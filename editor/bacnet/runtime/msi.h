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
#ifndef MULTISTATE_INPUT_H
#define MULTISTATE_INPUT_H

#include <stdbool.h>
#include <stdint.h>
#include "bacdef.h"
#include "bacerror.h"
#include "rp.h"
#include "wp.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */


/* MultiState Inputs are encoded in unsigned integer
 * (in BACnet => uint8_t), and can not be 0.
 * See ASHRAE 135-2016, section 12.20.4
 */
#define MULTISTATE_MAX_NUMBER_OF_STATES (255)


    typedef struct Multistate_Input_descr {
        /* pointer to IEC 61131-3 located variable that is mapped onto this BACnet object */
        uint8_t *Located_Var_ptr;
        uint32_t Object_Identifier;  /* called object 'Instance' in the source code! */
        char    *Object_Name;   
        char    *Description;
        uint8_t  Number_Of_States;

        /* stores the current value */
        uint8_t Present_Value;
        /* Writable out-of-service allows others to manipulate our Present Value */
        bool Out_Of_Service;
        char State_Text[MULTISTATE_MAX_NUMBER_OF_STATES][64];
    } MULTISTATE_INPUT_DESCR;


    void Multistate_Input_Property_Lists(
        const int **pRequired,
        const int **pOptional,
        const int **pProprietary);

    bool Multistate_Input_Valid_Instance(
        uint32_t object_instance);
    unsigned Multistate_Input_Count(
        void);
    uint32_t Multistate_Input_Index_To_Instance(
        unsigned index);
    unsigned Multistate_Input_Instance_To_Index(
        uint32_t instance);

    int Multistate_Input_Read_Property(
        BACNET_READ_PROPERTY_DATA * rpdata);

    bool Multistate_Input_Write_Property(
        BACNET_WRITE_PROPERTY_DATA * wp_data);

    /* optional API */
    bool Multistate_Input_Object_Name(
        uint32_t object_instance,
        BACNET_CHARACTER_STRING * object_name);

    uint32_t Multistate_Input_Present_Value(
        uint32_t object_instance);
    bool Multistate_Input_Present_Value_Set(
        uint32_t object_instance,
        uint32_t value);

    bool Multistate_Input_Out_Of_Service(
        uint32_t object_instance);
    void Multistate_Input_Out_Of_Service_Set(
        uint32_t object_instance,
        bool value);

    void Multistate_Input_Init(
        void);



#ifdef __cplusplus
}
#endif /* __cplusplus */
#endif
