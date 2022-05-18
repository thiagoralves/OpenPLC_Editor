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

/* Analog Value Objects - customize for your use */

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
#include "av_%(locstr)s.h"

/* we choose to have a NULL level in our system represented by */
/* a particular value.  When the priorities are not in use, they */
/* will be relinquished (i.e. set to the NULL level). */
/* Since the values are floats, we use NAN (Not A Number) as our NULL value. */
/* WARNING: Never use comparisons like 'if (value == AO_LEVEL_NULL)'
 *           as it will always return false, even if both values are NAN.
 *          Use instead the negated version 'if (value != AO_LEVEL_NULL)'
 *           and add an 'else' to the 'if' condition if necessary.
 *         However, some compilers may screw this up if they do not
 *         implement IEEE 754 properly. It is probably best to stick with
 *         the isnan() macro if available.
 */
#define AV_VALUE_NULL NAN
#define AV_VALUE_IS_NULL(x)  (isnan(x))
/* When all the priorities are level null, the present value returns */
/* the Relinquish Default value */
#define AV_VALUE_RELINQUISH_DEFAULT (0.0)


/* The IEC 61131-3 located variables mapped onto the Analog Value objects of BACnet protocol */
%(AV_lvars)s


/* The array where we keep all the state related to the Analog Value Objects */
#define MAX_ANALOG_VALUES %(AV_count)s
static ANALOG_VALUE_DESCR AV_Descr[MAX_ANALOG_VALUES] = {
%(AV_param)s
};


/* These three arrays are used by the ReadPropertyMultiple handler,
 * as well as to initialize the XXX_Property_List used by the 
 * Property List (PROP_PROPERTY_LIST) property.
 */
static const int Analog_Value_Properties_Required[] = {
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

static const int Analog_Value_Properties_Optional[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                                  /*(1)(2)      */
    PROP_DESCRIPTION,             /* R  O ( 28) */
    /* required if Present_Value is writable (which is true in our case!) */
    PROP_PRIORITY_ARRAY,          /* R  O ( 87) */
    PROP_RELINQUISH_DEFAULT,      /* R  O (104) */
//  PROP_CURRENT_COMMAND_PRIORITY,/* R  O (431) */   
    -1
};

static const int Analog_Value_Properties_Proprietary[] = {
    -1
};

/* This array stores the PROPERTY_LIST which may be read by clients.
 * End of list is marked by following the last element with the value '-1'
 * 
 * It is initialized by Analog_Values_Init() based off the values
 * stored in Analog_Value_Properties_Required 
 *           Analog_Value_Properties_Optional
 *           Analog_Value_Properties_Proprietary
 */
/* TODO: Allocate memory for this array with malloc() at startup */
static int Analog_Value_Properties_List[64];



/********************************************************/
/**                  Callback functions.               **/
/** Functions required by BACnet devie implementation. **/
/********************************************************/


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Analog_Value_Property_Lists(
    const int **pRequired,
    const int **pOptional,
    const int **pProprietary)
{
    if (pRequired)
        *pRequired = Analog_Value_Properties_Required;
    if (pOptional)
        *pOptional = Analog_Value_Properties_Optional;
    if (pProprietary)
        *pProprietary = Analog_Value_Properties_Proprietary;

    return;
}


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Analog_Value_Init(
    void)
{
    unsigned i, j;
    static bool initialized = false;

    if (!initialized) {
        initialized = true;

        /* initialize the Analog_Value_Properties_List array */
        int len = 0;
        len += BACnet_Init_Properties_List(Analog_Value_Properties_List + len,
                                           Analog_Value_Properties_Required);
        len += BACnet_Init_Properties_List(Analog_Value_Properties_List + len,
                                           Analog_Value_Properties_Optional);
        len += BACnet_Init_Properties_List(Analog_Value_Properties_List + len,
                                           Analog_Value_Properties_Proprietary);

        for (i = 0; i < MAX_ANALOG_VALUES; i++) {
            // MJS: the following line in th original demo code was commented out so we do not
            //      overwrite the initial values configured by the user in beremiz IDE
            // memset(&AV_Descr[i], 0x00, sizeof(ANALOG_VALUE_DESCR));
            for (j = 0; j < BACNET_MAX_PRIORITY; j++) {
                AV_Descr[i].Present_Value[j]  = AV_VALUE_NULL;
            }
            AV_Descr[i].Out_Of_Service = 0;
            AV_Descr[i].Event_State    = 0;
//          AV_Descr[i].Units = UNITS_NO_UNITS;
        }
    }
}




/* validate that the given instance exists */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Analog_Value_Valid_Instance(
    uint32_t object_instance)
{
    return (Analog_Value_Instance_To_Index(object_instance) < MAX_ANALOG_VALUES);
}

/* the number of Analog Value Objects */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
unsigned Analog_Value_Count(void) {return MAX_ANALOG_VALUES;}


/* returns the instance (i.e. Object Identifier) that correlates to the correct index */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
uint32_t Analog_Value_Index_To_Instance(unsigned index) {return AV_Descr[index].Object_Identifier;}



/* returns the index that correlates to the correct instance number (Object Identifier) */
unsigned Analog_Value_Instance_To_Index(
    uint32_t object_instance)
{
    unsigned index = 0;
  
    for (index = 0; index < MAX_ANALOG_VALUES; index++)
        if (object_instance == AV_Descr[index].Object_Identifier)
            return index;

    /* error, this object ID is not in our list! */
    return MAX_ANALOG_VALUES;
}




float Analog_Value_Present_Value(
    uint32_t object_instance)
{
    float value = AV_VALUE_RELINQUISH_DEFAULT;
    unsigned index = 0;
    unsigned i = 0;

    index = Analog_Value_Instance_To_Index(object_instance);
    if (index < MAX_ANALOG_VALUES) {
        for (i = 0; i < BACNET_MAX_PRIORITY; i++) {
            if (!AV_VALUE_IS_NULL(AV_Descr[index].Present_Value[i])) {
                value = AV_Descr[index].Present_Value[i];
                break;
            }
        }
    }

    return value;
}



/* returns command priority (1..16), or 0 if all priority values are at NULL */
int Analog_Value_Current_Command_Priority(
    uint32_t object_instance)
{
    unsigned index = 0;
    unsigned i = 0;

    index = Analog_Value_Instance_To_Index(object_instance);
    if (index < MAX_ANALOG_VALUES) {
        for (i = 0; i < BACNET_MAX_PRIORITY; i++) {
            if (!AV_VALUE_IS_NULL(AV_Descr[index].Present_Value[i])) {
                return i+1; // +1 since priority is 1..16, and not 0..15
            }
        }
    }
    // command values in all priorities are set to NULL
    return 0;
}



/* For a given object instance-number, sets the present-value at a given
 * priority 1..16 (except 6, see ASHRAE 135-2016, section 19.2.2)
 */
bool Analog_Value_Present_Value_Set(
    uint32_t object_instance,
    float value,
    uint8_t priority)
{
    unsigned index = 0;

    index = Analog_Value_Instance_To_Index(object_instance);
    if (index >= MAX_ANALOG_VALUES) 
      return false;
    if ((priority == 0) || (priority > BACNET_MAX_PRIORITY) ||
        (priority == 6 /* reserved, ASHRAE 135-2016, section 19.2.2 */))
      return false;
    
    priority--;
    AV_Descr[index].Present_Value[priority] = value;
    return true;
}



bool Analog_Value_Present_Value_Relinquish(
    uint32_t object_instance,
    unsigned priority)
{
    unsigned index = 0;

    index = Analog_Value_Instance_To_Index(object_instance);
    if (index >= MAX_ANALOG_VALUES)
      return false;

    if ((priority == 0) || (priority > BACNET_MAX_PRIORITY) ||
        (priority == 6 /* reserved, ASHRAE 135-2016, section 19.2.2 */))
      return false;
 
    priority--;
    AV_Descr[index].Present_Value[priority] = AV_VALUE_NULL;
    return true;
}



/* note: the object name must be unique within this device */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Analog_Value_Object_Name(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    bool    status = false;
    unsigned index = Analog_Value_Instance_To_Index(object_instance);

    if (index < MAX_ANALOG_VALUES)
        status = characterstring_init_ansi(object_name, AV_Descr[index].Object_Name);
    
    return status;
}



bool Analog_Value_Object_Description(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    bool    status = false;
    unsigned index = Analog_Value_Instance_To_Index(object_instance);

    if (index < MAX_ANALOG_VALUES)
        status = characterstring_init_ansi(object_name, AV_Descr[index].Description);
    
    return status;    
}



/* return apdu len, or BACNET_STATUS_ERROR on error */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
int Analog_Value_Read_Property(
    BACNET_READ_PROPERTY_DATA * rpdata)
{
    int apdu_len = 0;   /* return value */
    BACNET_BIT_STRING bit_string;
    BACNET_CHARACTER_STRING char_string;
    float real_value = (float) 1.414;
    unsigned object_index = 0;
    bool state = false;
    uint8_t *apdu = NULL;
    ANALOG_VALUE_DESCR *CurrentAV;

    if ((rpdata == NULL) || (rpdata->application_data == NULL) ||
        (rpdata->application_data_len == 0)) {
        return 0;
    }

    apdu = rpdata->application_data;

    object_index = Analog_Value_Instance_To_Index(rpdata->object_instance);
    if (object_index >= MAX_ANALOG_VALUES) {
        rpdata->error_class = ERROR_CLASS_OBJECT;
        rpdata->error_code  = ERROR_CODE_UNKNOWN_OBJECT;
        return BACNET_STATUS_ERROR;
    }

    switch (rpdata->object_property) {
        case PROP_OBJECT_IDENTIFIER:
            apdu_len =
                encode_application_object_id(&apdu[0], OBJECT_ANALOG_VALUE,
                rpdata->object_instance);
            break;

        case PROP_OBJECT_NAME:
            Analog_Value_Object_Name(rpdata->object_instance, &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;

        case PROP_DESCRIPTION:
            Analog_Value_Object_Description(rpdata->object_instance, &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;

        case PROP_OBJECT_TYPE:
            apdu_len =
                encode_application_enumerated(&apdu[0], OBJECT_ANALOG_VALUE);
            break;

        case PROP_PRESENT_VALUE:
            real_value = Analog_Value_Present_Value(rpdata->object_instance);
            apdu_len = encode_application_real(&apdu[0], real_value);
            break;

        case PROP_STATUS_FLAGS:
            bitstring_init(&bit_string);
            bitstring_set_bit(&bit_string, STATUS_FLAG_IN_ALARM, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_FAULT, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OVERRIDDEN, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OUT_OF_SERVICE,
                AV_Descr[object_index].Out_Of_Service);

            apdu_len = encode_application_bitstring(&apdu[0], &bit_string);
            break;

        case PROP_EVENT_STATE:
            apdu_len =
                encode_application_enumerated(&apdu[0], EVENT_STATE_NORMAL);
            break;

        case PROP_OUT_OF_SERVICE:
            state = AV_Descr[object_index].Out_Of_Service;
            apdu_len = encode_application_boolean(&apdu[0], state);
            break;

        case PROP_PRIORITY_ARRAY:
            BACnet_encode_array(AV_Descr[object_index].Present_Value,
                                BACNET_MAX_PRIORITY,
                                AV_VALUE_IS_NULL,
                                encode_application_real)
            break;

//      case PROP_CURRENT_COMMAND_PRIORITY: {
//          unsigned i = Analog_Value_Current_Command_Priority(rpdata->object_instance);
//          if (i == 0)  apdu_len = encode_application_null    (&apdu[0]);
//          else         apdu_len = encode_application_unsigned(&apdu[0], i);
//          break;
//      }

        case PROP_RELINQUISH_DEFAULT:
            real_value = AV_VALUE_RELINQUISH_DEFAULT;
            apdu_len = encode_application_real(&apdu[0], real_value);
            break;

        case PROP_UNITS:
            apdu_len =
                encode_application_enumerated(&apdu[0], AV_Descr[object_index].Units);
            break;

//      case PROP_PROPERTY_LIST:
//          BACnet_encode_array(Analog_Value_Properties_List,
//                              property_list_count(Analog_Value_Properties_List),
//                              retfalse, encode_application_enumerated);
//          break;
        default:
            rpdata->error_class = ERROR_CLASS_PROPERTY;
            rpdata->error_code = ERROR_CODE_UNKNOWN_PROPERTY;
            apdu_len = BACNET_STATUS_ERROR;
            break;
    }
    /*  only array properties can have array options */
    if ((apdu_len >= 0) && (rpdata->object_property != PROP_PRIORITY_ARRAY) &&
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
bool Analog_Value_Write_Property(
    BACNET_WRITE_PROPERTY_DATA * wp_data)
{
    bool status = false;        /* return value */
    unsigned int object_index = 0;
    int len = 0;
    BACNET_APPLICATION_DATA_VALUE value;
    ANALOG_VALUE_DESCR *CurrentAV;

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
    if ((wp_data->object_property != PROP_PRIORITY_ARRAY) &&
        (wp_data->object_property != PROP_EVENT_TIME_STAMPS) &&
        (wp_data->array_index != BACNET_ARRAY_ALL)) {
        /*  only array properties can have array options */
        wp_data->error_class = ERROR_CLASS_PROPERTY;
        wp_data->error_code = ERROR_CODE_PROPERTY_IS_NOT_AN_ARRAY;
        return false;
    }
    object_index = Analog_Value_Instance_To_Index(wp_data->object_instance);
    if (object_index < MAX_ANALOG_VALUES)
        CurrentAV = &AV_Descr[object_index];
    else
        return false;

    switch (wp_data->object_property) {
        case PROP_PRESENT_VALUE:
            if (value.tag == BACNET_APPLICATION_TAG_REAL) {
                if (Analog_Value_Present_Value_Set(wp_data->object_instance,
                        value.type.Real, wp_data->priority)) {
                    status = true;
                } else if (wp_data->priority == 6) {
                    /* Command priority 6 is reserved for use by Minimum On/Off
                       algorithm and may not be used for other purposes in any
                       object. */
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code = ERROR_CODE_WRITE_ACCESS_DENIED;
                } else {
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code = ERROR_CODE_VALUE_OUT_OF_RANGE;
                }
            } else {
                status =
                    WPValidateArgType(&value, BACNET_APPLICATION_TAG_NULL,
                    &wp_data->error_class, &wp_data->error_code);
                if (status) {
                    status =
                        Analog_Value_Present_Value_Relinquish
                        (wp_data->object_instance, wp_data->priority);
                }
                if (!status) {
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code = ERROR_CODE_VALUE_OUT_OF_RANGE;
                }
            }
            break;

        case PROP_OUT_OF_SERVICE:
        {
            bool Previous_Out_Of_Service = CurrentAV->Out_Of_Service;
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_BOOLEAN,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                CurrentAV->Out_Of_Service = value.type.Boolean;
                if (Previous_Out_Of_Service && !CurrentAV->Out_Of_Service)
                    /* We have just changed from Out_of_Service -> In Service */
                    /* We need to update the Present_Value to the value
                     * currently in the PLC...
                     */
                    CurrentAV->Present_Value[BACNET_MAX_PRIORITY-1] =
                                             *(CurrentAV->Located_Var_ptr);
            }
            break;
        }

        case PROP_UNITS:
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_ENUMERATED,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                CurrentAV->Units = value.type.Enumerated;
            }
            break;

        case PROP_OBJECT_IDENTIFIER:
        case PROP_OBJECT_NAME:
        case PROP_OBJECT_TYPE:
        case PROP_STATUS_FLAGS:
        case PROP_EVENT_STATE:
        case PROP_DESCRIPTION:
        case PROP_RELINQUISH_DEFAULT:
        case PROP_PRIORITY_ARRAY:
//      case PROP_PROPERTY_LIST:
//      case PROP_CURRENT_COMMAND_PRIORITY:
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

void  Analog_Value_Copy_Present_Value_to_Located_Var(void) {
    unsigned i;
    for (i = 0; i < MAX_ANALOG_VALUES; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (AV_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        *(AV_Descr[i].Located_Var_ptr) = Analog_Value_Present_Value(AV_Descr[i].Object_Identifier);
    }
}



void  Analog_Value_Copy_Located_Var_to_Present_Value(void) {
    unsigned i;
    for (i = 0; i < MAX_ANALOG_VALUES; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (AV_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        AV_Descr[i].Present_Value[BACNET_MAX_PRIORITY-1] = *(AV_Descr[i].Located_Var_ptr);
    }
}

