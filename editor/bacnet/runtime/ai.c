/**************************************************************************
*
* Copyright (C) 2006 Steve Karg <skarg@users.sourceforge.net>
* Copyright (C) 2011 Krzysztof Malorny <malornykrzysztof@gmail.com>
* Copyright (C) 2017 Mario de Sousa <msousa@fe.up.pt>
*
* Permission is hereby granted, free of charge, to any person obtaining
* a copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so, subject to
* the following conditions:
*
* The above copyright notice and this permission notice shall be included
* in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*
*********************************************************************/

/* Analog Input Objects - customize for your use */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>     /* NAN maro */

#include "config_bacnet_for_beremiz_%(locstr)s.h"     /* the custom configuration for beremiz plugin */
#include "bacdef.h"
#include "bacdcode.h"
#include "bacenum.h"
#include "bacapp.h"
#include "bactext.h"
#include "device_%(locstr)s.h"
#include "handlers.h"
#include "ai_%(locstr)s.h"



/* initial value for present_value property of each object */ 
#define AI_VALUE_INIT (0)

/* The IEC 61131-3 located variables mapped onto the Analog Input objects of BACnet protocol */
%(AI_lvars)s


/* The array where we keep all the state related to the Analog Input Objects */
#define MAX_ANALOG_INPUTS %(AI_count)s
static ANALOG_INPUT_DESCR AI_Descr[MAX_ANALOG_INPUTS] = {
%(AI_param)s
};



/* These three arrays are used by the ReadPropertyMultiple handler,
 * as well as to initialize the XXX_Property_List used by the 
 * Property List (PROP_PROPERTY_LIST) property.
 */
static const int Analog_Input_Properties_Required[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                              /*(1)(2)      */
    PROP_OBJECT_IDENTIFIER,   /* R  R ( 75) */
    PROP_OBJECT_NAME,         /* R  R ( 77) */
    PROP_OBJECT_TYPE,         /* R  R ( 79) */
    PROP_PRESENT_VALUE,       /* W  R ( 85) */
    PROP_STATUS_FLAGS,        /* R  R (111) */
    PROP_EVENT_STATE,         /* R  R ( 36) */
    PROP_OUT_OF_SERVICE,      /* W  R ( 81) */
    PROP_UNITS,               /* W  R (117) */
//  PROP_PROPERTY_LIST,       /* R  R (371) */
    -1
};

static const int Analog_Input_Properties_Optional[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                              /*(1)(2)      */
    PROP_DESCRIPTION,         /* R  O ( 28) */
    -1
};

static const int Analog_Input_Properties_Proprietary[] = {
    -1
};

/* This array stores the PROPERTY_LIST which may be read by clients.
 * End of list is marked by following the last element with the value '-1'
 * 
 * It is initialized by Analog_Inputs_Init() based off the values
 * stored in Analog_Input_Properties_Required 
 *           Analog_Input_Properties_Optional
 *           Analog_Input_Properties_Proprietary
 */
/* TODO: Allocate memory for this array with malloc() at startup */
static int Analog_Input_Properties_List[64];



/********************************************************/
/**                  Callback functions.               **/
/** Functions required by BACnet devie implementation. **/
/********************************************************/


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Analog_Input_Property_Lists(
    const int **pRequired,
    const int **pOptional,
    const int **pProprietary)
{
    if (pRequired)
        *pRequired = Analog_Input_Properties_Required;
    if (pOptional)
        *pOptional = Analog_Input_Properties_Optional;
    if (pProprietary)
        *pProprietary = Analog_Input_Properties_Proprietary;

    return;
}


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Analog_Input_Init(
    void)
{
    unsigned i, j;
    static bool initialized = false;

    if (!initialized) {
        initialized = true;

        /* initialize the Analog_Input_Properties_List array */
        int len = 0;
        len += BACnet_Init_Properties_List(Analog_Input_Properties_List + len,
                                           Analog_Input_Properties_Required);
        len += BACnet_Init_Properties_List(Analog_Input_Properties_List + len,
                                           Analog_Input_Properties_Optional);
        len += BACnet_Init_Properties_List(Analog_Input_Properties_List + len,
                                           Analog_Input_Properties_Proprietary);

        for (i = 0; i < MAX_ANALOG_INPUTS; i++) {
            // MJS: the following line in th original demo code was commented out so we do not
            //      overwrite the initial values configured by the user in beremiz IDE
            // memset(&AI_Descr[i], 0x00, sizeof(ANALOG_INPUT_DESCR));
            AI_Descr[i].Present_Value  = AI_VALUE_INIT;
            AI_Descr[i].Out_Of_Service = 0;
            AI_Descr[i].Event_State    = 0;
//          AI_Descr[i].Units = UNITS_NO_UNITS;
        }
    }
}




/* validate that the given instance exists */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Analog_Input_Valid_Instance(
    uint32_t object_instance)
{
    return (Analog_Input_Instance_To_Index(object_instance) < MAX_ANALOG_INPUTS);
}

/* the number of Analog Input Objects */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
unsigned Analog_Input_Count(void) {return MAX_ANALOG_INPUTS;}


/* returns the instance (i.e. Object Identifier) that correlates to the correct index */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
uint32_t Analog_Input_Index_To_Instance(unsigned index) {return AI_Descr[index].Object_Identifier;}



/* returns the index that correlates to the correct instance number (Object Identifier) */
unsigned Analog_Input_Instance_To_Index(
    uint32_t object_instance)
{
    unsigned index = 0;
  
    for (index = 0; index < MAX_ANALOG_INPUTS; index++)
        if (object_instance == AI_Descr[index].Object_Identifier)
            return index;

    /* error, this object ID is not in our list! */
    return MAX_ANALOG_INPUTS;
}




float Analog_Input_Present_Value(
    uint32_t object_instance)
{
    float value = AI_VALUE_INIT;
    unsigned index = 0;
    unsigned i = 0;

    index = Analog_Input_Instance_To_Index(object_instance);
    if (index < MAX_ANALOG_INPUTS)
        value = AI_Descr[index].Present_Value;

    return value;
}




/* note: the object name must be unique within this device */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Analog_Input_Object_Name(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    bool    status = false;
    unsigned index = Analog_Input_Instance_To_Index(object_instance);

    if (index < MAX_ANALOG_INPUTS)
        status = characterstring_init_ansi(object_name, AI_Descr[index].Object_Name);
    
    return status;
}



bool Analog_Input_Object_Description(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    bool    status = false;
    unsigned index = Analog_Input_Instance_To_Index(object_instance);

    if (index < MAX_ANALOG_INPUTS)
        status = characterstring_init_ansi(object_name, AI_Descr[index].Description);
    
    return status;    
}



/* return apdu len, or BACNET_STATUS_ERROR on error */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
int Analog_Input_Read_Property(
    BACNET_READ_PROPERTY_DATA * rpdata)
{
    int apdu_len = 0;   /* return value */
    BACNET_BIT_STRING bit_string;
    BACNET_CHARACTER_STRING char_string;
    float real_value = (float) 1.414;
    unsigned object_index = 0;
    bool state = false;
    uint8_t *apdu = NULL;

    if ((rpdata == NULL) || (rpdata->application_data == NULL) ||
        (rpdata->application_data_len == 0)) {
        return 0;
    }

    apdu = rpdata->application_data;

    object_index = Analog_Input_Instance_To_Index(rpdata->object_instance);
    if (object_index >= MAX_ANALOG_INPUTS) {
        rpdata->error_class = ERROR_CLASS_OBJECT;
        rpdata->error_code  = ERROR_CODE_UNKNOWN_OBJECT;
        return BACNET_STATUS_ERROR;
    }

    switch (rpdata->object_property) {
        case PROP_OBJECT_IDENTIFIER:
            apdu_len =
                encode_application_object_id(&apdu[0], OBJECT_ANALOG_INPUT,
                rpdata->object_instance);
            break;

        case PROP_OBJECT_NAME:
            Analog_Input_Object_Name(rpdata->object_instance, &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;

        case PROP_DESCRIPTION:
            Analog_Input_Object_Description(rpdata->object_instance, &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;

        case PROP_OBJECT_TYPE:
            apdu_len =
                encode_application_enumerated(&apdu[0], OBJECT_ANALOG_INPUT);
            break;

        case PROP_PRESENT_VALUE:
            real_value = Analog_Input_Present_Value(rpdata->object_instance);
            apdu_len = encode_application_real(&apdu[0], real_value);
            break;

        case PROP_STATUS_FLAGS:
            bitstring_init(&bit_string);
            bitstring_set_bit(&bit_string, STATUS_FLAG_IN_ALARM, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_FAULT, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OVERRIDDEN, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OUT_OF_SERVICE,
                AI_Descr[object_index].Out_Of_Service);

            apdu_len = encode_application_bitstring(&apdu[0], &bit_string);
            break;

        case PROP_EVENT_STATE:
            apdu_len =
                encode_application_enumerated(&apdu[0], EVENT_STATE_NORMAL);
            break;

        case PROP_OUT_OF_SERVICE:
            state = AI_Descr[object_index].Out_Of_Service;
            apdu_len = encode_application_boolean(&apdu[0], state);
            break;

        case PROP_UNITS:
            apdu_len =
                encode_application_enumerated(&apdu[0], AI_Descr[object_index].Units);
            break;

//      case PROP_PROPERTY_LIST:
//          BACnet_encode_array(Analog_Input_Properties_List,
//                              property_list_count(Analog_Input_Properties_List),
//                              retfalse, encode_application_enumerated);
//          break;
        default:
            rpdata->error_class = ERROR_CLASS_PROPERTY;
            rpdata->error_code = ERROR_CODE_UNKNOWN_PROPERTY;
            apdu_len = BACNET_STATUS_ERROR;
            break;
    }
    /*  only array properties can have array options */
    if ((apdu_len >= 0) &&
        (rpdata->object_property != PROP_EVENT_TIME_STAMPS) &&
//      (rpdata->object_property != PROP_PROPERTY_LIST) &&
        (rpdata->array_index != BACNET_ARRAY_ALL)) {
        rpdata->error_class = ERROR_CLASS_PROPERTY;
        rpdata->error_code = ERROR_CODE_PROPERTY_IS_NOT_AN_ARRAY;
        apdu_len = BACNET_STATUS_ERROR;
    }

    return apdu_len;
}




/* returns true if successful */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Analog_Input_Write_Property(
    BACNET_WRITE_PROPERTY_DATA * wp_data)
{
    bool status = false;        /* return value */
    unsigned int object_index = 0;
    int len = 0;
    BACNET_APPLICATION_DATA_VALUE value;
    ANALOG_INPUT_DESCR *CurrentAI;

    /* decode the some of the request */
    len =
        bacapp_decode_application_data(wp_data->application_data,
        wp_data->application_data_len, &value);
    /* FIXME: len < application_data_len: more data? */
    if (len < 0) {
        /* error while decoding - a value larger than we can handle */
        wp_data->error_class = ERROR_CLASS_PROPERTY;
        wp_data->error_code = ERROR_CODE_VALUE_OUT_OF_RANGE;
        return false;
    }
    if ((wp_data->object_property != PROP_EVENT_TIME_STAMPS) &&
        (wp_data->array_index != BACNET_ARRAY_ALL)) {
        /*  only array properties can have array options */
        wp_data->error_class = ERROR_CLASS_PROPERTY;
        wp_data->error_code = ERROR_CODE_PROPERTY_IS_NOT_AN_ARRAY;
        return false;
    }
    object_index = Analog_Input_Instance_To_Index(wp_data->object_instance);
    if (object_index < MAX_ANALOG_INPUTS)
        CurrentAI = &AI_Descr[object_index];
    else
        return false;

    switch (wp_data->object_property) {
        case PROP_PRESENT_VALUE:
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_REAL,
                &wp_data->error_class, &wp_data->error_code);
            if (!status) {
                wp_data->error_class = ERROR_CLASS_PROPERTY;
                wp_data->error_code  = ERROR_CODE_VALUE_OUT_OF_RANGE;
                status = false; // not really necessary here.
            } else {
                if (!AI_Descr[object_index].Out_Of_Service) {
                    /* input objects can only be written to when Out_Of_Service is true! */
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code  = ERROR_CODE_WRITE_ACCESS_DENIED;
                    status = false;
                } else {
                    AI_Descr[object_index].Present_Value = value.type.Real;
                    status = true;
                }
            }
            break;
      
        case PROP_OUT_OF_SERVICE:
        {
            bool Previous_Out_Of_Service = CurrentAI->Out_Of_Service;
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_BOOLEAN,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                CurrentAI->Out_Of_Service = value.type.Boolean;
                if (Previous_Out_Of_Service && !CurrentAI->Out_Of_Service)
                    /* We have just changed from Out_of_Service -> In Service */
                    /* We need to update the Present_Value to the value
                     * currently in the PLC...
                     */
                    CurrentAI->Present_Value = *(CurrentAI->Located_Var_ptr);
            }
            break;
        }

        case PROP_UNITS:
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_ENUMERATED,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                CurrentAI->Units = value.type.Enumerated;
            }
            break;

        case PROP_OBJECT_IDENTIFIER:
        case PROP_OBJECT_NAME:
        case PROP_OBJECT_TYPE:
        case PROP_STATUS_FLAGS:
        case PROP_EVENT_STATE:
        case PROP_DESCRIPTION:
//      case PROP_PROPERTY_LIST:
            wp_data->error_class = ERROR_CLASS_PROPERTY;
            wp_data->error_code = ERROR_CODE_WRITE_ACCESS_DENIED;
            break;
        default:
            wp_data->error_class = ERROR_CLASS_PROPERTY;
            wp_data->error_code = ERROR_CODE_UNKNOWN_PROPERTY;
            break;
    }

    return status;
}







/********************************************/
/** Functions required for Beremiz plugin  **/
/********************************************/

void  Analog_Input_Copy_Present_Value_to_Located_Var(void) {
    unsigned i;
    for (i = 0; i < MAX_ANALOG_INPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (AI_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        *(AI_Descr[i].Located_Var_ptr) = Analog_Input_Present_Value(AI_Descr[i].Object_Identifier);
    }
}



void  Analog_Input_Copy_Located_Var_to_Present_Value(void) {
    unsigned i;
    for (i = 0; i < MAX_ANALOG_INPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (AI_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        AI_Descr[i].Present_Value = *(AI_Descr[i].Located_Var_ptr);
    }
}

