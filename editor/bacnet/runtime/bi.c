/**************************************************************************
*
* Copyright (C) 2006 Steve Karg <skarg@users.sourceforge.net>
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

/* Binary Input Objects - customize for your use */

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "config_bacnet_for_beremiz_%(locstr)s.h"     /* the custom configuration for beremiz plugin */
#include "bacdef.h"
#include "bacdcode.h"
#include "bacenum.h"
#include "bacapp.h"
#include "wp.h"
#include "rp.h"
#include "bi_%(locstr)s.h"
#include "handlers.h"



/* initial value for present_value property of each object */ 
#define BI_VALUE_INIT (0)


/* The IEC 61131-3 located variables mapped onto the Binary Input objects of BACnet protocol */
%(BI_lvars)s


/* The array where we keep all the state related to the Binary Input Objects */
#define MAX_BINARY_INPUTS %(BI_count)s
static BINARY_INPUT_DESCR BI_Descr[MAX_BINARY_INPUTS] = {
%(BI_param)s
};




/* These three arrays are used by the ReadPropertyMultiple handler,
 * as well as to initialize the XXX_Property_List used by the 
 * Property List (PROP_PROPERTY_LIST) property.
 */
static const int Binary_Input_Properties_Required[] = {
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
    PROP_POLARITY,            /* R  R ( 84) */
//  PROP_PROPERTY_LIST,       /* R  R (371) */
    -1
};

static const int Binary_Input_Properties_Optional[] = {
 /* (1) Currently Supported                  */
 /* (2) Required by standard ASHRAE 135-2016 */
                              /*(1)(2)      */
    PROP_DESCRIPTION,         /* R  O ( 28) */
    -1
};

static const int Binary_Input_Properties_Proprietary[] = {
    -1
};


/* This array stores the PROPERTY_LIST which may be read by clients.
 * End of list is marked by following the last element with the value '-1'
 * 
 * It is initialized by Binary_Input_Init() based off the values
 * stored in Binary_Input_Properties_Required 
 *           Binary_Input_Properties_Optional
 *           Binary_Input_Properties_Proprietary
 */
/* TODO: Allocate memory for this array with malloc() at startup */
static int Binary_Input_Properties_List[64];





/********************************************************/
/**                  Callback functions.               **/
/** Functions required by BACnet devie implementation. **/
/********************************************************/


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Binary_Input_Property_Lists(
    const int **pRequired,
    const int **pOptional,
    const int **pProprietary)
{
    if (pRequired)
        *pRequired = Binary_Input_Properties_Required;
    if (pOptional)
        *pOptional = Binary_Input_Properties_Optional;
    if (pProprietary)
        *pProprietary = Binary_Input_Properties_Proprietary;

    return;
}


/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
void Binary_Input_Init(
    void)
{
    unsigned i, j;
    static bool initialized = false;

    // fprintf(stderr, "BACnet plugin: Binary_Input_Init() called!\n");
    
    if (!initialized) {
        initialized = true;

        /* initialize the Binary_Input_Properties_List array */
        int len = 0;
        len += BACnet_Init_Properties_List(Binary_Input_Properties_List + len,
                                           Binary_Input_Properties_Required);
        len += BACnet_Init_Properties_List(Binary_Input_Properties_List + len,
                                           Binary_Input_Properties_Optional);
        len += BACnet_Init_Properties_List(Binary_Input_Properties_List + len,
                                           Binary_Input_Properties_Proprietary);

        /* initialize all the binary values priority arrays to NULL */
        for (i = 0; i < MAX_BINARY_INPUTS; i++) {
            BI_Descr[i].Present_Value = BI_VALUE_INIT;
            BI_Descr[i].Polarity      = POLARITY_NORMAL;
        }
    }

    return;
}



/* validate that the given instance (Object ID) exists */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Binary_Input_Valid_Instance(
    uint32_t object_instance)
{
    // fprintf(stderr, "BACnet plugin: Binary_Input_Valid_Instance(obj_ID=%%u) called!\n", object _instance);
    return (Binary_Input_Instance_To_Index(object_instance) < MAX_BINARY_INPUTS);
}


/* the number of Binary Input Objects */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
unsigned Binary_Input_Count(void)   {return MAX_BINARY_INPUTS;}


/* returns the instance (i.e. Object Identifier) that correlates to the correct index */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
uint32_t Binary_Input_Index_To_Instance(unsigned index) {return BI_Descr[index].Object_Identifier;}


/* returns the index that correlates to the correct instance number (Object Identifier) */
unsigned Binary_Input_Instance_To_Index(
    uint32_t object_instance)
{
    unsigned index = 0;
  
    for (index = 0; index < MAX_BINARY_INPUTS; index++)
        if (object_instance == BI_Descr[index].Object_Identifier)
            return index;

    /* error, this object ID is not in our list! */
    return MAX_BINARY_INPUTS;
}



BACNET_BINARY_PV Binary_Input_Present_Value(
    uint32_t object_instance)
{
    BACNET_BINARY_PV value = BI_VALUE_INIT;
    unsigned index = 0;
    unsigned i = 0;

    // fprintf(stderr, "BACnet plugin: Binary_Input_Present_Value(obj_ID=%%u) called!\n", object_instance);

    index = Binary_Input_Instance_To_Index(object_instance);
    if (index < MAX_BINARY_INPUTS)
        value = BI_Descr[index].Present_Value;

    return value;
}



/* note: the object name must be unique within this device */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
bool Binary_Input_Object_Name(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    bool    status = false;
    unsigned index = Binary_Input_Instance_To_Index(object_instance);

    if (index < MAX_BINARY_INPUTS)
        status = characterstring_init_ansi(object_name, BI_Descr[index].Object_Name);
    
    return status;
}



bool Binary_Input_Object_Description(
    uint32_t object_instance,
    BACNET_CHARACTER_STRING * object_name)
{
    bool    status = false;
    unsigned index = Binary_Input_Instance_To_Index(object_instance);

    if (index < MAX_BINARY_INPUTS)
        status = characterstring_init_ansi(object_name, BI_Descr[index].Description);
    
    return status;    
}



/* return apdu len, or BACNET_STATUS_ERROR on error */
/* This is a callback function. Callback set in My_Object_Table[] array declared in device.c,  */
int Binary_Input_Read_Property(
    BACNET_READ_PROPERTY_DATA * rpdata)
{
    int len = 0;
    int apdu_len = 0;   /* return value */
    BACNET_BIT_STRING bit_string;
    BACNET_CHARACTER_STRING char_string;
    BACNET_BINARY_PV present_value = BINARY_INACTIVE;
    unsigned object_index = 0;
    unsigned i = 0;
    bool state = false;
    uint8_t *apdu = NULL;

    // fprintf(stderr, "BACnet plugin: Binary_Input_Read_Property() called!\n");

    if ((rpdata == NULL) || (rpdata->application_data == NULL) ||
        (rpdata->application_data_len == 0)) {
        return 0;
    }
    
    object_index = Binary_Input_Instance_To_Index(rpdata->object_instance);
    if (object_index >= MAX_BINARY_INPUTS) {
        rpdata->error_class = ERROR_CLASS_OBJECT;
        rpdata->error_code  = ERROR_CODE_UNKNOWN_OBJECT;
        return BACNET_STATUS_ERROR;
    }
    
    apdu = rpdata->application_data;
    switch (rpdata->object_property) {
        case PROP_OBJECT_IDENTIFIER:
            apdu_len =
                encode_application_object_id(&apdu[0], OBJECT_BINARY_INPUT,
                rpdata->object_instance);
            break;
        case PROP_OBJECT_NAME:
            Binary_Input_Object_Name(rpdata->object_instance, &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;
        case PROP_DESCRIPTION:
            Binary_Input_Object_Description(rpdata->object_instance, &char_string);
            apdu_len =
                encode_application_character_string(&apdu[0], &char_string);
            break;
        case PROP_OBJECT_TYPE:
            apdu_len =
                encode_application_enumerated(&apdu[0], OBJECT_BINARY_INPUT);
            break;
        case PROP_PRESENT_VALUE:
            present_value =
                Binary_Input_Present_Value(rpdata->object_instance);
            apdu_len = encode_application_enumerated(&apdu[0], present_value);
            break;
        case PROP_STATUS_FLAGS:
            /* note: see the details in the standard on how to use these */
            bitstring_init(&bit_string);
            bitstring_set_bit(&bit_string, STATUS_FLAG_IN_ALARM, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_FAULT, false);
            bitstring_set_bit(&bit_string, STATUS_FLAG_OVERRIDDEN, false);
            state = BI_Descr[object_index].Out_Of_Service;
            bitstring_set_bit(&bit_string, STATUS_FLAG_OUT_OF_SERVICE, state);
            apdu_len = encode_application_bitstring(&apdu[0], &bit_string);
            break;
        case PROP_EVENT_STATE:
            /* note: see the details in the standard on how to use this */
            apdu_len =
                encode_application_enumerated(&apdu[0], EVENT_STATE_NORMAL);
            break;
        case PROP_OUT_OF_SERVICE:
            state = BI_Descr[object_index].Out_Of_Service;
            apdu_len = encode_application_boolean(&apdu[0], state);
            break;
        case PROP_POLARITY:
            apdu_len = encode_application_enumerated(&apdu[0],
                                BI_Descr[object_index].Polarity);
            break;
//      case PROP_PROPERTY_LIST:
//          BACnet_encode_array(Binary_Input_Properties_List,
//                              property_list_count(Binary_Input_Properties_List),
//                              retfalse, encode_application_enumerated);
//          break;
        default:
            rpdata->error_class = ERROR_CLASS_PROPERTY;
            rpdata->error_code  = ERROR_CODE_UNKNOWN_PROPERTY;
            apdu_len = BACNET_STATUS_ERROR;
            break;
    }
    /*  only array properties can have array options */
    if ((apdu_len >= 0) &&
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
bool Binary_Input_Write_Property(
    BACNET_WRITE_PROPERTY_DATA * wp_data)
{
    bool status = false;        /* return value */
    unsigned int object_index = 0;
    unsigned int priority = 0;
    BACNET_BINARY_PV level = BINARY_NULL;
    int len = 0;
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
    /*  only array properties can have array options */
    if (wp_data->array_index != BACNET_ARRAY_ALL) {
        wp_data->error_class = ERROR_CLASS_PROPERTY;
        wp_data->error_code = ERROR_CODE_PROPERTY_IS_NOT_AN_ARRAY;
        return false;
    }
    /* No need to check whether object_index is within bounds.
     * Has already been checked before Binary_Input_Write_Property() is called
     */
    object_index = Binary_Input_Instance_To_Index(wp_data->object_instance);
    
    switch (wp_data->object_property) {
        case PROP_PRESENT_VALUE:
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_ENUMERATED,
                &wp_data->error_class, &wp_data->error_code);
            if (!status) {
                wp_data->error_class = ERROR_CLASS_PROPERTY;
                wp_data->error_code  = ERROR_CODE_VALUE_OUT_OF_RANGE;
            } else {
                if (!BI_Descr[object_index].Out_Of_Service) {
                    /* input objects can only be written to when Out_Of_Service is true! */
                    wp_data->error_class = ERROR_CLASS_PROPERTY;
                    wp_data->error_code  = ERROR_CODE_WRITE_ACCESS_DENIED;
                    status = false; // not really necessary here.
                } else {
                    if (!(value.type.Enumerated <= MAX_BINARY_PV)) {
                        wp_data->error_class = ERROR_CLASS_PROPERTY;
                        wp_data->error_code  = ERROR_CODE_VALUE_OUT_OF_RANGE;
                        status = false;
                    } else {
                        level = (BACNET_BINARY_PV) value.type.Enumerated;
                        BI_Descr[object_index].Present_Value = level;
                        status = true;
                    }
                }
            }
            break;
        case PROP_OUT_OF_SERVICE:
        {
            bool Previous_Out_Of_Service = BI_Descr[object_index].Out_Of_Service;
            status =
                WPValidateArgType(&value, BACNET_APPLICATION_TAG_BOOLEAN,
                &wp_data->error_class, &wp_data->error_code);
            if (status) {
                BI_Descr[object_index].Out_Of_Service = value.type.Boolean;
                if (Previous_Out_Of_Service && !BI_Descr[object_index].Out_Of_Service)
                    /* We have just changed from Out_of_Service -> In Service */
                    /* We need to update the Present_Value to the value
                     * currently in the PLC...
                     */
                    BI_Descr[object_index].Present_Value =
                                           *(BI_Descr[object_index].Located_Var_ptr);
            }
            break;
        }
        case PROP_OBJECT_IDENTIFIER:
        case PROP_OBJECT_NAME:
        case PROP_DESCRIPTION:
        case PROP_OBJECT_TYPE:
        case PROP_STATUS_FLAGS:
        case PROP_EVENT_STATE:
        case PROP_POLARITY:
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



void  Binary_Input_Copy_Present_Value_to_Located_Var(void) {
    unsigned i;
    for (i = 0; i < MAX_BINARY_INPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (BI_Descr[i].Out_Of_Service)
            continue;

        // copy the value
        *(BI_Descr[i].Located_Var_ptr) = Binary_Input_Present_Value(BI_Descr[i].Object_Identifier);
    }
}
  
void  Binary_Input_Copy_Located_Var_to_Present_Value(void) {
    unsigned i;
    for (i = 0; i < MAX_BINARY_INPUTS; i++) {
        // decouple PLC's Located Variable from Bacnet Object's Present Value if Out_Of_Service is true
        if (BI_Descr[i].Out_Of_Service)
            continue;

        // copy the value (0 is false, all other values are true)
        if (*(BI_Descr[i].Located_Var_ptr))
            BI_Descr[i].Present_Value = BINARY_ACTIVE;
        else
            BI_Descr[i].Present_Value = BINARY_INACTIVE;
    }
}


