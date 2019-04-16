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

/* Multi-state Output Objects */

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
#include "mso_%(locstr)s.h"
#include "handlers.h"

/* we choose to have a NULL level in our system represented by */
/* a particular value.  When the priorities are not in use, they */
/* will be relinquished (i.e. set to the NULL level). */
/* Since multi state value objects can never take the value 0, we 
 * use 0 as our NULL value.
 * See ASHRAE 135-2016, section 12.20.4
 */
#define MSO_VALUE_NULL (0)
#define MSO_VALUE_IS_NULL(x)  ((x) == MSO_VALUE_NULL)
/* When all the priorities are level null, the present value returns */
/* the Relinquish Default value */
#define MSO_VALUE_RELINQUISH_DEFAULT 1



/* The IEC 61131-3 located variables mapped onto the Multi-state Output objects of BACnet protocol */
%(MSO_lvars)s


/* The array where we keep all the state related to the Multi-state Output Objects */
#define MAX_MULTISTATE_OUTPUTS %(MSO_count)s
static MULTISTATE_OUTPUT_DESCR MSO_Descr[MAX_MULTISTATE_OUTPUTS] = {
%(MSO_param)s
};



/* These three arrays are used by the ReadPropertyMultiple handler,
 * as well as to initialize the XXX_Property_List used by the 
 * Property List (PROP_PROPERTY_LIST) property.
 */
static const int Multistate_Output_Properties_Required[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                                  /*(1)(2)      */
    PROP_OBJECT_IDENTIFIER,       /* R  R ( 75) */
    PROP_OBJECT_NAME,             /* R  R ( 77) */
    PROP_OBJECT_TYPE,             /* R  R ( 79) */
    PROP_PRESENT_VALUE,           /* W  W ( 85) */
    PROP_STATUS_FLAGS,            /* R  R (111) */
    PROP_EVENT_STATE,             /* R  R ( 36) */
    PROP_OUT_OF_SERVICE,          /* W  R ( 81) */
    PROP_NUMBER_OF_STATES,        /* R  R ( 74) */
    PROP_PRIORITY_ARRAY,          /* R  R ( 87) */
    PROP_RELINQUISH_DEFAULT,      /* R  R (104) */
//  PROP_PROPERTY_LIST,           /* R  R (371) */
//  PROP_CURRENT_COMMAND_PRIORITY,/* R  R (431) */   
    -1
};

static const int Multistate_Output_Properties_Optional[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                                  /*(1)(2)      */
    PROP_DESCRIPTION,             /* R  O ( 28) */
    PROP_STATE_TEXT,              /* R  O (110) */
    -1
};

static const int Multistate_Output_Properties_Proprietary[] = {
    -1
};


/* This array stores the PROPERTY_LIST which may be read by clients.
 * End of list is marked by following the last element with the value '-1'
 * 
 * It is initialized by Multistate_Output_Init() based off the values
 * stored in Multistate_Output_Properties_Required 
 *           Multistate_Output_Properties_Optional
 *           Multistate_Output_Properties_Proprietary
 */
/* TODO: Allocate memory for this array with malloc() at startup */
static int Multistate_Output_Properties_List[64];





/********************************************************/
/**                  Callback functions.               **/
/** Functions required by BACnet devie implementation. **/
/********************************************************/


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Multistate_Output_Property_Lists(
    const int **pRequired,
    const int **pOptional,
    const int **pProprietary)
{
    if (pRequired)
        *pRequired = Multistate_Output_Properties_Required;
    if (pOptional)
        *pOptional = Multistate_Output_Properties_Optional;
    if (pProprietary)
        *pProprietary = Multistate_Output_Properties_Proprietary;

    return;
}



/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Multistate_Output_Init(
    void)
{
    unsigned int i, j;

    /* initialize the Multistate_Output_Properties_List array */
    int len = 0;
    len += BACnet_Init_Properties_List(Multistate_Output_Properties_List + len,
                                       Multistate_Output_Properties_Required);
    len += BACnet_Init_Properties_List(Multistate_Output_Properties_List + len,
                                       Multistate_Output_Properties_Optional);
    len += BACnet_Init_Properties_List(Multistate_Output_Properties_List + len,
                                       Multistate_Output_Properties_Proprietary);

    /* initialize all the analog output priority arrays to NULL */
    for (i = 0; i < MAX_MULTISTATE_OUTPUTS; i++) {
        for (j = 0; j < BACNET_MAX_PRIORITY; j++) {
            MSO_Descr[i].Present_Value[j] = MSO_VALUE_NULL;
        }
        for (j = 0; j < MSO_Descr[i].Number_Of_States; j++) {
            sprintf(MSO_Descr[i].State_Text[j], "State %%d", j+1);
        }
    }
    return;
}



/* validate that the given instance exists */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Multistate_Output_Valid_Instance(
    uint32_t object_instance)
{
    // fprintf(stderr, "BACnet plugin: Multistate_Output_Valid_Instance(obj_ID=%%u) called!\n", object _instance);
    return (Multistate_Output_Instance_To_Index(object_instance) < MAX_MULTISTATE_OUTPUTS);
}


/* the number of Multistate Value Objects */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
unsigned Multistate_Output_Count(void) {return MAX_MULTISTATE_OUTPUTS;}


/* returns the instance (i.e. Object Identifier) that correlates to the correct index */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
uint32_t Multistate_Output_Index_To_Instance(unsigned index) {return MSO_Descr[index].Object_Identifier;}






/* returns the index that correlates to the correct instance number (Object Identifier) */
unsigned Multistate_Output_Instance_To_Index(
    uint32_t object_instance)
{
    unsigned index = 0;
  
    for (index = 0; index < MAX_MULTISTATE_OUTPUTS; index++)
        if (object_instance == MSO_Descr[index].Object_Identifier)
            return index;

    /* error, this object ID is not in our list! */
    return MAX_MULTISTATE_OUTPUTS;
}





uint32_t Multistate_Output_Present_Value(
    uint32_t object_instance)
{
    uint32_t value = MSO_VALUE_RELINQUISH_DEFAULT;
    unsigned index = 0; /* offset from instance lookup */
    unsigned i = 0;

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_OUTPUTS) {
        for (i = 0; i < BACNET_MAX_PRIORITY; i++) {
            if (!MSO_VALUE_IS_NULL(MSO_Descr[index].Present_Value[i])) {
                value = MSO_Descr[index].Present_Value[i];
                break;
            }
        }
    }

    return value;
}



bool Multistate_Output_Present_Value_Set(
    uint32_t object_instance,
    uint32_t value,
    uint8_t  priority)
{
    unsigned index = 0; /* offset from instance lookup */

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index >= MAX_MULTISTATE_OUTPUTS)
      return false;

    if ((priority == 0) || (priority > BACNET_MAX_PRIORITY) ||
        (priority == 6 /* reserved, ASHRAE 135-2016, section 19.2.2 */))
      return false;
    
    if ((value == 0) || (value > MSO_Descr[index].Number_Of_States))
      return false;
      
    priority--;
    MSO_Descr[index].Present_Value[priority] = (uint8_t) value;

    return true;
}



/* returns command priority (1..16), or 0 if all priority values are at NULL */
int Multistate_Output_Current_Command_Priority(
    uint32_t object_instance)
{
    unsigned index = 0;
    unsigned i = 0;

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_OUTPUTS) {
        for (i = 0; i < BACNET_MAX_PRIORITY; i++) {
            if (!MSO_VALUE_IS_NULL(MSO_Descr[index].Present_Value[i])) {
                return i+1; // +1 since priority is 1..16, and not 0..15
            }
        }
    }
    // command values in all priorities are set to NULL
    return 0;
}




bool Multistate_Output_Present_Value_Relinquish(
    uint32_t object_instance,
    uint8_t  priority)
{
    unsigned index = 0; /* offset from instance lookup */

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index >= MAX_MULTISTATE_OUTPUTS)
      return false;
    
    if ((priority == 0) || (priority > BACNET_MAX_PRIORITY) ||
        (priority == 6 /* reserved, ASHRAE 135-2016, section 19.2.2 */))
      return false;
    
    priority--;
    MSO_Descr[index].Present_Value[priority] = MSO_VALUE_NULL;

    return true;
}



bool Multistate_Output_Out_Of_Service(
    uint32_t object_instance)
{
    bool value = false;
    unsigned index = 0;

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_OUTPUTS) {
        value = MSO_Descr[index].Out_Of_Service;
    }

    return value;
}



void Multistate_Output_Out_Of_Service_Set(
    uint32_t object_instance,
    bool value)
{
    unsigned index = 0;

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_OUTPUTS) {
        MSO_Descr[index].Out_Of_Service = value;
    }

    return;
}



static char *Multistate_Output_Description(
    uint32_t object_instance)
{
    unsigned index = 0; /* offset from instance lookup */
    char *pName = NULL; /* return value */

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_OUTPUTS) {
        pName = MSO_Descr[index].Description;
    }

    return pName;
}



/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Multistate_Output_Object_Name(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    unsigned index = 0; /* offset from instance lookup */
    bool status = false;

    index = Multistate_Output_Instance_To_Index(object_instance);
    if (index < MAX_MULTISTATE_OUTPUTS) {
        status = characterstring_init_ansi(object_name, MSO_Descr[index].Object_Name);
    }

    return status;
}



/* return apdu len, or BACNET_STATUS_ERROR on error */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
int Multistate_Output_Read_Property(
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

    object_index = Multistate_Output_Instance_To_Index(rpdata->object_instance);
    if (object_index >= MAX_MULTISTATE_OUTPUTS) {
        rpdata->error_class = ERROR_CLASS_OBJECT;
        rpdata->error_code  = ERROR_CODE_UNKNOWN_OBJECT;
        return BACNET_STATUS_ERROR;
    }

    apdu = rpdata->application_data;
    switch (rpdata->object_property) {
        case PROP_OBJECT_IDENTIFIER:
            apdu_len =
                encode_application_object_id(&apdu[0],
                OBJECT_MULTI_STATE_OUTPUT, rpdata->object_instance);
            break;
        case PROP_OBJECT_NAME:
            Multistate_Output_Object_Name(rpdata->object_instance,
                &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;
        case PROP_DESCRIPTION:
            characterstring_init_ansi(&char_string,
                Multistate_Output_Description(rpdata->object_instance));
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;
        case PROP_OBJECT_TYPE:
            apdu_len =
                encode_application_enumerated(&apdu[0],
                OBJECT_MULTI_STATE_OUTPUT);
            break;
        case PROP_PRESENT_VALUE:
            present_value =
                Multistate_Output_Present_Value(rpdata->object_instance);
            apdu_len = encode_application_unsigned(&apdu[0], present_value);
            break;
        case PROP_STATUS_FLAGS:
            /* note: see the details in the standard on how to use these */
            bitstring_init(&bit_string);
            bitstring_set_bit(&bit_string, STATUS_FLAG_IN_ALARM, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_FAULT, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OVERRIDDEN, false);
            if (Multistate_Output_Out_Of_Service(rpdata->object_instance)) {
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
            state = MSO_Descr[object_index].Out_Of_Service;
            apdu_len = encode_application_boolean(&apdu[0], state);
            break;
        case PROP_PRIORITY_ARRAY:
            BACnet_encode_array(MSO_Descr[object_index].Present_Value,
                                BACNET_MAX_PRIORITY,
                                MSO_VALUE_IS_NULL,
                                encode_application_unsigned);
            break;
//      case PROP_CURRENT_COMMAND_PRIORITY: {
//          unsigned i = Multistate_Output_Current_Command_Priority(rpdata->object_instance);
//          if (i == 0)  apdu_len = encode_application_null    (&apdu[0]);
//          else         apdu_len = encode_application_unsigned(&apdu[0], i);
//          break;
//      }

        case PROP_RELINQUISH_DEFAULT:
            present_value = MSO_VALUE_RELINQUISH_DEFAULT;
            apdu_len = encode_application_unsigned(&apdu[0], present_value);
            break;
        case PROP_NUMBER_OF_STATES:
            apdu_len =
                encode_application_unsigned(&apdu[apdu_len],
                MSO_Descr[object_index].Number_Of_States);
            break;
        case PROP_STATE_TEXT:
            BACnet_encode_array(MSO_Descr[object_index].State_Text,
                                MSO_Descr[object_index].Number_Of_States,
                                retfalse, BACnet_encode_character_string);
            break;
//      case PROP_PROPERTY_LIST:
//          BACnet_encode_array(Multistate_Output_Properties_List,
//                              property_list_count(Multistate_Output_Properties_List),
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
        (rpdata->object_property != PROP_PRIORITY_ARRAY) &&
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
bool Multistate_Output_Write_Property(
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
        (wp_data->object_property != PROP_PRIORITY_ARRAY) &&
        (wp_data->array_index != BACNET_ARRAY_ALL)) {
        /*  only array properties can have array options */
        wp_data->error_class = ERROR_CLASS_PROPERTY;
        wp_data->error_code = ERROR_CODE_PROPERTY_IS_NOT_AN_ARRAY;
        return false;
    }
    /* No need to check whether object_index is within bounds.
     * Has already been checked before Multistate_Output_Write_Property() is called
     */
    object_index = Multistate_Output_Instance_To_Index(wp_data->object_instance);

    switch (wp_data->object_property) {
        case PROP_PRESENT_VALUE:
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_UNSIGNED_INT,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                status =
                    Multistate_Output_Present_Value_Set
                    (wp_data->object_instance, value.type.Unsigned_Int, wp_data->priority);
                if (!status) {
                    if (wp_data->priority == 6) {
                        /* Command priority 6 is reserved for use by Minimum On/Off
                           algorithm and may not be used for other purposes in any
                           object. */
                        wp_data->error_class = ERROR_CLASS_PROPERTY;
                        wp_data->error_code = ERROR_CODE_WRITE_ACCESS_DENIED;
                    } else {
                        wp_data->error_class = ERROR_CLASS_PROPERTY;
                        wp_data->error_code = ERROR_CODE_VALUE_OUT_OF_RANGE;
                    }
                }
            } else {
                status =
                    WPValidateArgType(&value, BACNET_APPLICATION_TAG_NULL,
                    &wp_data->error_class, &wp_data->error_code);
                if (status) {
                    status =
                        Multistate_Output_Present_Value_Relinquish
                        (wp_data->object_instance, wp_data->priority);
                }
                if (!status) {
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code = ERROR_CODE_INVALID_DATA_TYPE;
                }
            }
            break;
        case PROP_OUT_OF_SERVICE:
        {
            bool Previous_Out_Of_Service = MSO_Descr[object_index].Out_Of_Service;
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_BOOLEAN,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                MSO_Descr[object_index].Out_Of_Service = value.type.Boolean;
                if (Previous_Out_Of_Service && !MSO_Descr[object_index].Out_Of_Service)
                    /* We have just changed from Out_of_Service -> In Service */
                    /* We need to update the Present_Value to the value
                     * currently in the PLC...
                     */
                    MSO_Descr[object_index].Present_Value[BACNET_MAX_PRIORITY-1] =
                                           *(MSO_Descr[object_index].Located_Var_ptr);
            }
            break;
        }
        case PROP_OBJECT_IDENTIFIER:
        case PROP_OBJECT_NAME:
        case PROP_OBJECT_TYPE:
        case PROP_STATUS_FLAGS:
        case PROP_EVENT_STATE:
        case PROP_NUMBER_OF_STATES:
        case PROP_PRIORITY_ARRAY:
//      case PROP_CURRENT_COMMAND_PRIORITY:
        case PROP_RELINQUISH_DEFAULT:
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



void  Multistate_Output_Copy_Present_Value_to_Located_Var(void) {
    unsigned i;
    for (i = 0; i < MAX_MULTISTATE_OUTPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (MSO_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        *(MSO_Descr[i].Located_Var_ptr) = Multistate_Output_Present_Value(MSO_Descr[i].Object_Identifier);
    }
}



void  Multistate_Output_Copy_Located_Var_to_Present_Value(void) {
    unsigned i;
    for (i = 0; i < MAX_MULTISTATE_OUTPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (MSO_Descr[i].Out_Of_Service)
            continue;

        // Make sure local device does not set Present_Value to a value higher than Number_Of_States
        /* NOTE: The following comparison (Present_Value > Number_Of_States) is OK as the
         *       MSO_VALUE_NULL is currently set to 0. This means that the local controller
         *       can safely relinquish control by setting the Present_Value to 0.
         *       The comparison would not be safe if for some reason we later change
         *       MSO_VALUE_NULL to a value that may be higher than Number_Of_States.
         */
        #if MSO_VALUE_NULL != 0
        #error Implementation assumes that MSO_VALUE_NULL is set to 0, which is currently not the case.
        #endif
        if (*(MSO_Descr[i].Located_Var_ptr) > MSO_Descr[i].Number_Of_States)
            continue;

        // Everything seems to be OK. Copy the value
        MSO_Descr[i].Present_Value[BACNET_MAX_PRIORITY-1] = *(MSO_Descr[i].Located_Var_ptr);
    }
}



