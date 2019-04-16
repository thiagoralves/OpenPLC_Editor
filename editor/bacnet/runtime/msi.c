/**************************************************************************
*
* Copyright (C) 2012 Steve Karg <skarg@users.sourceforge.net>
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

/* Multi-state Input Objects */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "config_bacnet_for_beremiz_%(locstr)s.h"     /* the custom configuration for beremiz pluginh  */
#include "bacdef.h"
#include "bacdcode.h"
#include "bacenum.h"
#include "bacapp.h"
#include "rp.h"
#include "wp.h"
#include "msi_%(locstr)s.h"
#include "handlers.h"


/* initial value for present_value property of each object */ 
#define MSI_VALUE_INIT (1)

/* The IEC 61131-3 located variables mapped onto the Multi-state Input objects of BACnet protocol */
%(MSI_lvars)s


/* The array where we keep all the state related to the Multi-state Input Objects */
#define MAX_MULTISTATE_INPUTS %(MSI_count)s
static MULTISTATE_INPUT_DESCR MSI_Descr[MAX_MULTISTATE_INPUTS] = {
%(MSI_param)s
};



/* These three arrays are used by the ReadPropertyMultiple handler,
 * as well as to initialize the XXX_Property_List used by the 
 * Property List (PROP_PROPERTY_LIST) property.
 */
static const int Multistate_Input_Properties_Required[] = {
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
    PROP_NUMBER_OF_STATES,    /* R  R ( 74) */
//  PROP_PROPERTY_LIST,       /* R  R (371) */
    -1
};

static const int Multistate_Input_Properties_Optional[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                              /*(1)(2)      */
    PROP_DESCRIPTION,         /* R  O ( 28) */
    PROP_STATE_TEXT,          /* R  O (110) */
    -1
};

static const int Multistate_Input_Properties_Proprietary[] = {
    -1
};


/* This array stores the PROPERTY_LIST which may be read by clients.
 * End of list is marked by following the last element with the value '-1'
 * 
 * It is initialized by Multistate_Input_Init() based off the values
 * stored in Multistate_Input_Properties_Required 
 *           Multistate_Input_Properties_Optional
 *           Multistate_Input_Properties_Proprietary
 */
/* TODO: Allocate memory for this array with malloc() at startup */
static int Multistate_Input_Properties_List[64];





/********************************************************/
/**                  Callback functions.               **/
/** Functions required by BACnet devie implementation. **/
/********************************************************/


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Multistate_Input_Property_Lists(
    const int **pRequired,
    const int **pOptional,
    const int **pProprietary)
{
    if (pRequired)
        *pRequired = Multistate_Input_Properties_Required;
    if (pOptional)
        *pOptional = Multistate_Input_Properties_Optional;
    if (pProprietary)
        *pProprietary = Multistate_Input_Properties_Proprietary;

    return;
}



/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Multistate_Input_Init(
    void)
{
    unsigned int i, j;

    /* initialize the Multistate_Input_Properties_List array */
    int len = 0;
    len += BACnet_Init_Properties_List(Multistate_Input_Properties_List + len,
                                       Multistate_Input_Properties_Required);
    len += BACnet_Init_Properties_List(Multistate_Input_Properties_List + len,
                                       Multistate_Input_Properties_Optional);
    len += BACnet_Init_Properties_List(Multistate_Input_Properties_List + len,
                                       Multistate_Input_Properties_Proprietary);

    /* initialize all the analog output priority arrays to NULL */
    for (i = 0; i < MAX_MULTISTATE_INPUTS; i++) {
        MSI_Descr[i].Present_Value = MSI_VALUE_INIT;
        for (j = 0; j < MSI_Descr[i].Number_Of_States; j++) {
            sprintf(MSI_Descr[i].State_Text[j], "State %%d", j+1);
        }
    }
    return;
}



/* validate that the given instance exists */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Multistate_Input_Valid_Instance(
    uint32_t object_instance)
{
    // fprintf(stderr, "BACnet plugin: Multistate_Input_Valid_Instance(obj_ID=%%u) called!\n", object _instance);
    return (Multistate_Input_Instance_To_Index(object_instance) < MAX_MULTISTATE_INPUTS);
}


/* the number of Multistate Value Objects */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
unsigned Multistate_Input_Count(void) {return MAX_MULTISTATE_INPUTS;}


/* returns the instance (i.e. Object Identifier) that correlates to the correct index */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
uint32_t Multistate_Input_Index_To_Instance(unsigned index) {return MSI_Descr[index].Object_Identifier;}






/* returns the index that correlates to the correct instance number (Object Identifier) */
unsigned Multistate_Input_Instance_To_Index(
    uint32_t object_instance)
{
    unsigned index = 0;
  
    for (index = 0; index < MAX_MULTISTATE_INPUTS; index++)
        if (object_instance == MSI_Descr[index].Object_Identifier)
            return index;

    /* error, this object ID is not in our list! */
    return MAX_MULTISTATE_INPUTS;
}





uint32_t Multistate_Input_Present_Value(
    uint32_t object_instance)
{
    uint32_t value = MSI_VALUE_INIT;
    unsigned index = 0; /* offset from instance lookup */

    index = Multistate_Input_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_INPUTS)
        value = MSI_Descr[index].Present_Value;

    return value;
}



bool Multistate_Input_Present_Value_Set(
    uint32_t object_instance,
    uint32_t value)
{
    unsigned index = 0; /* offset from instance lookup */

    index = Multistate_Input_Instance_To_Index(object_instance);
    if (index >= MAX_MULTISTATE_INPUTS)
      return false;

    if ((value == 0) || (value > MSI_Descr[index].Number_Of_States))
      return false;
      
    MSI_Descr[index].Present_Value = (uint8_t) value;
    return true;
}




bool Multistate_Input_Out_Of_Service(
    uint32_t object_instance)
{
    bool value = false;
    unsigned index = 0;

    index = Multistate_Input_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_INPUTS) {
        value = MSI_Descr[index].Out_Of_Service;
    }

    return value;
}



void Multistate_Input_Out_Of_Service_Set(
    uint32_t object_instance,
    bool value)
{
    unsigned index = 0;

    index = Multistate_Input_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_INPUTS) {
        MSI_Descr[index].Out_Of_Service = value;
    }

    return;
}



static char *Multistate_Input_Description(
    uint32_t object_instance)
{
    unsigned index = 0; /* offset from instance lookup */
    char *pName = NULL; /* return value */

    index = Multistate_Input_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_INPUTS) {
        pName = MSI_Descr[index].Description;
    }

    return pName;
}



/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Multistate_Input_Object_Name(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    unsigned index = 0; /* offset from instance lookup */
    bool status = false;

    index = Multistate_Input_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_INPUTS) {
        status = characterstring_init_ansi(object_name, MSI_Descr[index].Object_Name);
    }

    return status;
}



/* return apdu len, or BACNET_STATUS_ERROR on error */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
int Multistate_Input_Read_Property(
    BACNET_READ_PROPERTY_DATA * rpdata)
{
    int len = 0;
    int apdu_len = 0;   /* return value */
    BACNET_BIT_STRING bit_string;
    BACNET_CHARACTER_STRING char_string;
    uint32_t present_value = 0;
    unsigned object_index = 0;
    unsigned i = 0;
    bool state = false;
    uint8_t *apdu = NULL;

    if ((rpdata == NULL) || (rpdata->application_data == NULL) ||
        (rpdata->application_data_len == 0)) {
        return 0;
    }

    object_index = Multistate_Input_Instance_To_Index(rpdata->object_instance);
    if (object_index >= MAX_MULTISTATE_INPUTS) {
        rpdata->error_class = ERROR_CLASS_OBJECT;
        rpdata->error_code  = ERROR_CODE_UNKNOWN_OBJECT;
        return BACNET_STATUS_ERROR;
    }

    apdu = rpdata->application_data;
    switch (rpdata->object_property) {
        case PROP_OBJECT_IDENTIFIER:
            apdu_len =
                encode_application_object_id(&apdu[0],
                OBJECT_MULTI_STATE_INPUT, rpdata->object_instance);
            break;
        case PROP_OBJECT_NAME:
            Multistate_Input_Object_Name(rpdata->object_instance,
                &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;
        case PROP_DESCRIPTION:
            characterstring_init_ansi(&char_string,
                Multistate_Input_Description(rpdata->object_instance));
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;
        case PROP_OBJECT_TYPE:
            apdu_len =
                encode_application_enumerated(&apdu[0],
                OBJECT_MULTI_STATE_INPUT);
            break;
        case PROP_PRESENT_VALUE:
            present_value =
                Multistate_Input_Present_Value(rpdata->object_instance);
            apdu_len = encode_application_unsigned(&apdu[0], present_value);
            break;
        case PROP_STATUS_FLAGS:
            /* note: see the details in the standard on how to use these */
            bitstring_init(&bit_string);
            bitstring_set_bit(&bit_string, STATUS_FLAG_IN_ALARM, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_FAULT, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OVERRIDDEN, false);
            if (Multistate_Input_Out_Of_Service(rpdata->object_instance)) {
                bitstring_set_bit(&bit_string, STATUS_FLAG_OUT_OF_SERVICE,
                    true);
            } else {
                bitstring_set_bit(&bit_string, STATUS_FLAG_OUT_OF_SERVICE,
                    false);
            }
            apdu_len = encode_application_bitstring(&apdu[0], &bit_string);
            break;
        case PROP_EVENT_STATE:
            /* note: see the details in the standard on how to use this */
            apdu_len =
                encode_application_enumerated(&apdu[0], EVENT_STATE_NORMAL);
            break;
        case PROP_OUT_OF_SERVICE:
            state = MSI_Descr[object_index].Out_Of_Service;
            apdu_len = encode_application_boolean(&apdu[0], state);
            break;
        case PROP_NUMBER_OF_STATES:
            apdu_len =
                encode_application_unsigned(&apdu[apdu_len],
                MSI_Descr[object_index].Number_Of_States);
            break;
        case PROP_STATE_TEXT:
            BACnet_encode_array(MSI_Descr[object_index].State_Text,
                                MSI_Descr[object_index].Number_Of_States,
                                retfalse, BACnet_encode_character_string);
            break;
//      case PROP_PROPERTY_LIST:
//          BACnet_encode_array(Multistate_Input_Properties_List,
//                              property_list_count(Multistate_Input_Properties_List),
//                              retfalse, encode_application_enumerated);
//          break;
        default:
            rpdata->error_class = ERROR_CLASS_PROPERTY;
            rpdata->error_code = ERROR_CODE_UNKNOWN_PROPERTY;
            apdu_len = BACNET_STATUS_ERROR;
            break;
    }
    /*  only array properties can have array options */
    if ((apdu_len >= 0) && (rpdata->object_property != PROP_STATE_TEXT) &&
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
bool Multistate_Input_Write_Property(
    BACNET_WRITE_PROPERTY_DATA * wp_data)
{
    bool status = false;        /* return value */
    int len = 0;
    unsigned object_index = 0;
    BACNET_APPLICATION_DATA_VALUE value;

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
    if ((wp_data->object_property != PROP_STATE_TEXT) &&
        (wp_data->array_index != BACNET_ARRAY_ALL)) {
        /*  only array properties can have array options */
        wp_data->error_class = ERROR_CLASS_PROPERTY;
        wp_data->error_code = ERROR_CODE_PROPERTY_IS_NOT_AN_ARRAY;
        return false;
    }
    /* No need to check whether object_index is within bounds.
     * Has already been checked before Multistate_Input_Write_Property() is called
     */
    object_index = Multistate_Input_Instance_To_Index(wp_data->object_instance);

    switch (wp_data->object_property) {
        case PROP_PRESENT_VALUE:
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_UNSIGNED_INT,
                &wp_data->error_class, &wp_data->error_code);
            if (!status) {
                wp_data->error_class = ERROR_CLASS_PROPERTY;
                wp_data->error_code  = ERROR_CODE_INVALID_DATA_TYPE;
                status = false; // not really necessary here.
            } else {
                if (!MSI_Descr[object_index].Out_Of_Service) {
                    /* input objects can only be written to when Out_Of_Service is true! */
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code  = ERROR_CODE_WRITE_ACCESS_DENIED;
                    status = false;
                } else {
                    status =
                        Multistate_Input_Present_Value_Set
                        (wp_data->object_instance, value.type.Unsigned_Int);
                    if (!status) {
                        wp_data->error_class = ERROR_CLASS_PROPERTY;
                        wp_data->error_code  = ERROR_CODE_VALUE_OUT_OF_RANGE;
                        status = false; // not really necessary here.
                    }
                }
            }
            break;
        case PROP_OUT_OF_SERVICE:
        {
            bool Previous_Out_Of_Service = MSI_Descr[object_index].Out_Of_Service;
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_BOOLEAN,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                MSI_Descr[object_index].Out_Of_Service = value.type.Boolean;
                if (Previous_Out_Of_Service && !MSI_Descr[object_index].Out_Of_Service)
                    /* We have just changed from Out_of_Service -> In Service */
                    /* We need to update the Present_Value to the value
                     * currently in the PLC...
                     */
                    MSI_Descr[object_index].Present_Value =
                                           *(MSI_Descr[object_index].Located_Var_ptr);
            }
            break;
        }
        case PROP_OBJECT_IDENTIFIER:
        case PROP_OBJECT_NAME:
        case PROP_OBJECT_TYPE:
        case PROP_STATUS_FLAGS:
        case PROP_EVENT_STATE:
        case PROP_NUMBER_OF_STATES:
        case PROP_DESCRIPTION:
        case PROP_STATE_TEXT:
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



void  Multistate_Input_Copy_Present_Value_to_Located_Var(void) {
    unsigned i;
    for (i = 0; i < MAX_MULTISTATE_INPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (MSI_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        *(MSI_Descr[i].Located_Var_ptr) = Multistate_Input_Present_Value(MSI_Descr[i].Object_Identifier);
    }
}



void  Multistate_Input_Copy_Located_Var_to_Present_Value(void) {
    unsigned i;
    for (i = 0; i < MAX_MULTISTATE_INPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (MSI_Descr[i].Out_Of_Service)
            continue;

        // Make sure local device does not set Present_Value to 0, nor higher than Number_Of_States
        if ((*(MSI_Descr[i].Located_Var_ptr) >  MSI_Descr[i].Number_Of_States) ||
            (*(MSI_Descr[i].Located_Var_ptr) == 0))
            continue;

        // Everything seems to be OK. Copy the value
        MSI_Descr[i].Present_Value = *(MSI_Descr[i].Located_Var_ptr);
    }
}



