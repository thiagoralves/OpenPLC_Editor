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
#ifndef BI_H
#define BI_H

#include <stdbool.h>
#include <stdint.h>
#include "bacdef.h"
#include "bacerror.h"
#include "rp.h"
#include "wp.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

    typedef struct Binary_Input_descr {
        /* pointer to IEC 61131-3 located variable that is mapped onto this BACnet object */
        uint8_t *Located_Var_ptr;
        uint32_t Object_Identifier;  /* called object 'Instance' in the source code! */
        char    *Object_Name;   
        char    *Description;
        /* stores the current value */
        BACNET_BINARY_PV Present_Value;
        /* Writable out-of-service allows others to play with our Present Value */
        /* without changing the physical output */
        bool             Out_Of_Service;
        BACNET_POLARITY  Polarity;
    } BINARY_INPUT_DESCR;


    void Binary_Input_Property_Lists(
        const int **pRequired,
        const int **pOptional,
        const int **pProprietary);
    bool Binary_Input_Valid_Instance(
        uint32_t object_instance);
    unsigned Binary_Input_Count(
        void);
    uint32_t Binary_Input_Index_To_Instance(
        unsigned index);
    unsigned Binary_Input_Instance_To_Index(
        uint32_t object_instance);

    bool Binary_Input_Object_Name(
        uint32_t object_instance,
        BACNET_CHARACTER_STRING * object_name);

    char *Binary_Input_Description(
        uint32_t instance);

    BACNET_BINARY_PV Binary_Input_Present_Value(
        uint32_t instance);
    bool Binary_Input_Present_Value_Set(
        uint32_t instance,
        BACNET_BINARY_PV value);

    bool Binary_Input_Out_Of_Service(
        uint32_t instance);
    void Binary_Input_Out_Of_Service_Set(
        uint32_t instance,
        bool value);

    char *Binary_Input_Description(
        uint32_t instance);

    int Binary_Input_Read_Property(
        BACNET_READ_PROPERTY_DATA * rpdata);

    bool Binary_Input_Write_Property(
        BACNET_WRITE_PROPERTY_DATA * wp_data);

    void Binary_Input_Init(
        void);



#ifdef __cplusplus
}
#endif /* __cplusplus */
#endif
