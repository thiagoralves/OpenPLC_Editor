/*

Template C code used to produce target Ethercat C CIA402 code

Copyright (C) 2011-2014: Laurent BESSARD, Edouard TISSERANT

Distributed under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

See COPYING file for copyrights details.

*/

#include "ecrt.h"

#include "beremiz.h"
#include "iec_types_all.h"

#include "accessor.h"
#include "POUS.h"

/* From CiA402, page 27

        Table 30 - State coding
    Statusword      |      PDS FSA state
xxxx xxxx x0xx 0000 | Not ready to switch on
xxxx xxxx x1xx 0000 | Switch on disabled
xxxx xxxx x01x 0001 | Ready to switch on
xxxx xxxx x01x 0011 | Switched on
xxxx xxxx x01x 0111 | Operation enabled
xxxx xxxx x00x 0111 | Quick stop active
xxxx xxxx x0xx 1111 | Fault reaction active
xxxx xxxx x0xx 1000 | Fault
*/
#define FSAFromStatusWord(SW) (SW & 0x006f)
#define NotReadyToSwitchOn  0b00000000 FSA_sep 0b00100000
#define SwitchOnDisabled    0b01000000 FSA_sep 0b01100000
#define ReadyToSwitchOn     0b00100001
#define SwitchedOn          0b00100011
#define OperationEnabled    0b00100111
#define QuickStopActive     0b00000111
#define FaultReactionActive 0b00001111 FSA_sep 0b00101111
#define Fault               0b00001000 FSA_sep 0b00101000

// SatusWord bits :
#define SW_ReadyToSwitchOn     0x0001
#define SW_SwitchedOn          0x0002
#define SW_OperationEnabled    0x0004
#define SW_Fault               0x0008
#define SW_VoltageEnabled      0x0010
#define SW_QuickStop           0x0020
#define SW_SwitchOnDisabled    0x0040
#define SW_Warning             0x0080
#define SW_Remote              0x0200
#define SW_TargetReached       0x0400
#define SW_InternalLimitActive 0x0800

// ControlWord bits :
#define SwitchOn        0x0001
#define EnableVoltage   0x0002
#define QuickStop       0x0004
#define EnableOperation 0x0008
#define FaultReset      0x0080
#define Halt            0x0100


IEC_INT beremiz__IW%(location_str)s = %(slave_pos)s;
IEC_INT *__IW%(location_str)s = &beremiz__IW%(location_str)s;
IEC_INT beremiz__IW%(location_str)s_402;
IEC_INT *__IW%(location_str)s_402 = &beremiz__IW%(location_str)s_402;

%(MCL_headers)s

static IEC_BOOL __FirstTick = 1;

typedef enum {
    mc_mode_none, // No motion mode
    mc_mode_csp,  // Continuous Synchronous Positionning mode
    mc_mode_csv,  // Continuous Synchronous Velocity mode
    mc_mode_cst,  // Continuous Synchronous Torque mode
} mc_axismotionmode_enum;

typedef struct {
   IEC_BOOL Power;
   IEC_BOOL CommunicationReady;
   IEC_UINT NetworkPosition;
   IEC_BOOL ReadyForPowerOn;
   IEC_BOOL PowerFeedback;
   IEC_DINT ActualRawPosition;
   IEC_DINT ActualRawVelocity;
   IEC_DINT ActualRawTorque;
   IEC_DINT RawPositionSetPoint;
   IEC_DINT RawVelocitySetPoint;
   IEC_DINT RawTorqueSetPoint;
   mc_axismotionmode_enum AxisMotionMode;
   IEC_LREAL ActualVelocity;
   IEC_LREAL ActualPosition;
   IEC_LREAL ActualTorque;
}axis_s;

typedef struct {
%(entry_variables)s
    axis_s* axis;
} __CIA402Node;

#define AxsPub __CIA402Node_%(location_str)s

static __CIA402Node AxsPub;

%(extern_located_variables_declaration)s

%(fieldbus_interface_declaration)s

int __init_%(location_str)s()
{
    __FirstTick = 1;
%(init_entry_variables)s
	*(AxsPub.ModesOfOperation) = 0x08;
    return 0;
}

void __cleanup_%(location_str)s()
{
}

void __retrieve_%(location_str)s()
{
	if (__FirstTick) {
		*__IW%(location_str)s_402 = __MK_Alloc_AXIS_REF();
		AxsPub.axis = 
            __MK_GetPublic_AXIS_REF(*__IW%(location_str)s_402);
		AxsPub.axis->NetworkPosition = beremiz__IW%(location_str)s;
%(init_axis_params)s
%(fieldbus_interface_definition)s
		__FirstTick = 0;
	}

	// Default variables retrieve
	AxsPub.axis->CommunicationReady = 
        *(AxsPub.StatusWord) != 0;
#define FSA_sep || FSA ==
    {
        uint16_t FSA = FSAFromStatusWord(*(AxsPub.StatusWord));
        AxsPub.axis->ReadyForPowerOn = FSA == ReadyToSwitchOn;
        AxsPub.axis->PowerFeedback = FSA == OperationEnabled;
    }
#undef FSA_sep 
	AxsPub.axis->ActualRawPosition = *(AxsPub.ActualPosition);
	AxsPub.axis->ActualRawVelocity = *(AxsPub.ActualVelocity);
	AxsPub.axis->ActualRawTorque = *(AxsPub.ActualTorque);

	// Extra variables retrieve
%(extra_variables_retrieve)s
}

void __publish_%(location_str)s()
{
	IEC_BOOL power = 
        ((*(AxsPub.StatusWord) & SW_VoltageEnabled) != 0) 
        && AxsPub.axis->Power;
    uint16_t CW = *(AxsPub.ControlWord);

#define FSA_sep : case
	// CIA402 node state transition computation
	switch (FSAFromStatusWord(*(AxsPub.StatusWord))) {
	    case SwitchOnDisabled :
            CW &= ~(SwitchOn | FaultReset);
            CW |= EnableVoltage | QuickStop;
	    	break;
	    case ReadyToSwitchOn :
	    case OperationEnabled :
	    	if (!power) {
                CW &= ~(FaultReset | EnableOperation);
                CW |= SwitchOn | EnableVoltage | QuickStop;
	    		break;
	    	}
	    case SwitchedOn :
	    	if (power) {
                CW &= ~(FaultReset);
                CW |= SwitchOn | EnableVoltage | QuickStop | EnableOperation;
	    	}
	    	break;
	    case Fault :
            /* TODO reset fault only when MC_Reset */
            CW &= ~(SwitchOn | EnableVoltage | QuickStop | EnableOperation);
            CW |= FaultReset;
	    	break;
	    default:
	    	break;
	}
#undef FSA_sep 
    *(AxsPub.ControlWord) = CW;

	// CIA402 node modes of operation computation according to axis motion mode
	switch (AxsPub.axis->AxisMotionMode) {
		case mc_mode_cst:
			*(AxsPub.ModesOfOperation) = 0x0a;
			break;
		case mc_mode_csv:
			*(AxsPub.ModesOfOperation) = 0x09;
			break;
		default:
			*(AxsPub.ModesOfOperation) = 0x08;
			break;
	}

	// Default variables publish
	*(AxsPub.TargetPosition) = 
            AxsPub.axis->RawPositionSetPoint;
	*(AxsPub.TargetVelocity) = 
            AxsPub.axis->RawVelocitySetPoint;
	*(AxsPub.TargetTorque) = 
            AxsPub.axis->RawTorqueSetPoint;

	// Extra variables publish
%(extra_variables_publish)s
}
