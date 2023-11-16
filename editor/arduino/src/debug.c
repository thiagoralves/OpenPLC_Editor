/*
 * This file is part of OpenPLC Runtime
 *
 * Copyright (C) 2023 Autonomy, GP Orcullo
 * Based on the work by GP Orcullo on Beremiz for uC
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include <stdbool.h>

#include "iec_types_all.h"
#include "POUS.h"

#define SAME_ENDIANNESS      0
#define REVERSE_ENDIANNESS   1

uint8_t endianness;


extern PROGRAM0 RES0__INSTANCE0;

static const struct {
    void *ptr;
    __IEC_types_enum type;
} debug_vars[] = {
    {&(RES0__INSTANCE0.BUTTON), BOOL_ENUM},
    {&(RES0__INSTANCE0.TIMER_OUT), BOOL_O_ENUM},
    {&(RES0__INSTANCE0.COUNTER_VALUE), INT_ENUM},
    {&(RES0__INSTANCE0.PT20.EN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.ENO), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.IN1), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.IN3), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.IN2), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.IN_TIME), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.OUT1), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.OUT2), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.OUT3), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.ERROR), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.STARTED_TIMER_1), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TIMER_1_INPUT), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.STARTED_TIMER_2), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TIMER_2_INPUT), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.EN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.ENO), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.IN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.PT), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.Q), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.ET), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.STATE), SINT_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.PREV_IN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.CURRENT_TIME), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF1.START_TIME), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.EN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.ENO), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.IN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.PT), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.Q), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.ET), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.STATE), SINT_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.PREV_IN), BOOL_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.CURRENT_TIME), TIME_ENUM},
    {&(RES0__INSTANCE0.PT20.TOF2.START_TIME), TIME_ENUM},
};

#define VAR_COUNT               37

uint16_t get_var_count(void)
{
    return VAR_COUNT;
}

size_t get_var_size(size_t idx)
{
    switch (debug_vars[idx].type) {
    case BOOL_ENUM:
    case BOOL_O_ENUM:
        return sizeof(BOOL);
    case TIME_ENUM:
        return sizeof(TIME);
    case INT_ENUM:
        return sizeof(INT);
    case SINT_ENUM:
        return sizeof(SINT);
    default:
        return 0;
    }
}

void *get_var_addr(size_t idx)
{
    void *ptr = debug_vars[idx].ptr;

    switch (debug_vars[idx].type) {
    case BOOL_ENUM:
        return (void *)&((__IEC_BOOL_t *) ptr)->value;
    case BOOL_O_ENUM:
        return (void *)((((__IEC_BOOL_p *) ptr)->flags & __IEC_FORCE_FLAG) 
                        ? &(((__IEC_BOOL_p *) ptr)->fvalue) 
                        : ((__IEC_BOOL_p *) ptr)->value);
    case TIME_ENUM:
        return (void *)&((__IEC_TIME_t *) ptr)->value;
    case INT_ENUM:
        return (void *)&((__IEC_INT_t *) ptr)->value;
    case SINT_ENUM:
        return (void *)&((__IEC_SINT_t *) ptr)->value;
    default:
        return 0;
    }
}

void force_var(size_t idx, bool forced, void *val)
{
    void *ptr = debug_vars[idx].ptr;

    if (forced) {
        size_t var_size = get_var_size(idx);
        switch (debug_vars[idx].type) {
        case BOOL_ENUM: {
            memcpy(&((__IEC_BOOL_t *) ptr)->value, val, var_size);
            //((__IEC_BOOL_t *) ptr)->value = *((BOOL *) val);
            ((__IEC_BOOL_t *) ptr)->flags |= __IEC_FORCE_FLAG;
            break;
        }
        case BOOL_O_ENUM: {
            memcpy((((__IEC_BOOL_p *) ptr)->value), val, var_size);
            //*(((__IEC_BOOL_p *) ptr)->value) = *((BOOL *) val);
            ((__IEC_BOOL_p *) ptr)->flags |= __IEC_FORCE_FLAG;
            break;
        }
        case TIME_ENUM: {
            memcpy(&((__IEC_TIME_t *) ptr)->value, val, var_size);
            //((__IEC_TIME_t *) ptr)->value = *((TIME *) val);
            ((__IEC_TIME_t *) ptr)->flags |= __IEC_FORCE_FLAG;
            break;
        }
        case INT_ENUM: {
            memcpy(&((__IEC_INT_t *) ptr)->value, val, var_size);
            //((__IEC_INT_t *) ptr)->value = *((INT *) val);
            ((__IEC_INT_t *) ptr)->flags |= __IEC_FORCE_FLAG;
            break;
        }
        case SINT_ENUM: {
            memcpy(&((__IEC_SINT_t *) ptr)->value, val, var_size);
            //((__IEC_SINT_t *) ptr)->value = *((SINT *) val);
            ((__IEC_SINT_t *) ptr)->flags |= __IEC_FORCE_FLAG;
            break;
        }
        default:
            break;
        }
    } else {
        switch (debug_vars[idx].type) {
        case BOOL_ENUM:
            ((__IEC_BOOL_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;
            break;
        case BOOL_O_ENUM:
            ((__IEC_BOOL_p *) ptr)->flags &= ~__IEC_FORCE_FLAG;
            break;
        case TIME_ENUM:
            ((__IEC_TIME_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;
            break;
        case INT_ENUM:
            ((__IEC_INT_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;
            break;
        case SINT_ENUM:
            ((__IEC_SINT_t *) ptr)->flags &= ~__IEC_FORCE_FLAG;
            break;
        default:
            break;
        }
    }
}

void swap_bytes(void *ptr, size_t size) 
{
    uint8_t *bytePtr = (uint8_t *)ptr;
    size_t i;
    for (i = 0; i < size / 2; ++i) 
    {
        uint8_t temp = bytePtr[i];
        bytePtr[i] = bytePtr[size - 1 - i];
        bytePtr[size - 1 - i] = temp;
    }
}

void trace_reset(void)
{
    for (size_t i=0; i < VAR_COUNT; i++) 
    {
        force_var(i, false, 0);
    }
}

void set_trace(size_t idx, bool forced, void *val)
{
    if (idx >= 0 && idx < VAR_COUNT) 
    {
        if (endianness == REVERSE_ENDIANNESS)
        {
            // Aaaaarghhhh... Stupid AVR is Big Endian.
            swap_bytes(val, get_var_size(idx));
        }

        force_var(idx, forced, val);
    }
}

void set_endianness(uint8_t value)
{
    if (value == SAME_ENDIANNESS || value == REVERSE_ENDIANNESS)
    {
        endianness = value;
    }
}
