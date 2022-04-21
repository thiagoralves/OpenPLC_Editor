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
#ifndef AI_H
#define AI_H

#include <stdbool.h>
#include <stdint.h>
#include "bacdef.h"
#include "bacerror.h"
#include "wp.h"
#include "rp.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

    typedef struct Analog_Input_descr {
        /* pointer to IEC 61131-3 located variable that is mapped onto this BACnet object */
        float   *Located_Var_ptr;
        uint32_t Object_Identifier;  /* called object 'Instance' in the source code! */
        char    *Object_Name;   
        char    *Description;
        uint16_t Units;
      
        /* stores the current value */
        /* one entry per priority value */
        float Present_Value;
        unsigned Event_State:3;
        bool Out_Of_Service;
    } ANALOG_INPUT_DESCR;


    void Analog_Input_Property_Lists(
        const int **pRequired,
        const int **pOptional,
        const int **pProprietary);
    bool Analog_Input_Valid_Instance(
        uint32_t object_instance);
    unsigned Analog_Input_Count(
        void);
    uint32_t Analog_Input_Index_To_Instance(
        unsigned index);
    unsigned Analog_Input_Instance_To_Index(
        uint32_t object_instance);

    bool Analog_Input_Object_Name(
        uint32_t object_instance,
        BACNET_CHARACTER_STRING * object_name);

    int Analog_Input_Read_Property(
        BACNET_READ_PROPERTY_DATA * rpdata);

    bool Analog_Input_Write_Property(
        BACNET_WRITE_PROPERTY_DATA * wp_data);

    float Analog_Input_Present_Value(
        uint32_t object_instance);

    char *Analog_Input_Description(
        uint32_t instance);

    uint16_t Analog_Input_Units(
        uint32_t instance);

    bool Analog_Input_Out_Of_Service(
        uint32_t instance);
    void Analog_Input_Out_Of_Service_Set(
        uint32_t instance,
        bool oos_flag);

    void Analog_Input_Init(
        void);


#ifdef __cplusplus
}
#endif /* __cplusplus */
#endif
