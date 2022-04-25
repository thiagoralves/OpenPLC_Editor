/*
    Modbus.h - Header for Modbus Base Library
    Copyright (C) 2014 Andre Sarmento Barbosa

  Fixed by Kocil, 2022
  - define uint16_t IEC_UINT
  - Change word to IEC_UINT 
*/
#include <Arduino.h>

#ifndef MODBUS_H
#define MODBUS_H

#define MAX_REGS     32
#define MAX_FRAME   128
//#define USE_HOLDING_REGISTERS_ONLY

typedef uint16_t   IEC_UINT;

//Function Codes
enum {
    MB_FC_READ_COILS       = 0x01, // Read Coils (Output) Status 0xxxx
    MB_FC_READ_INPUT_STAT  = 0x02, // Read Input Status (Discrete Inputs) 1xxxx
    MB_FC_READ_REGS        = 0x03, // Read Holding Registers 4xxxx
    MB_FC_READ_INPUT_REGS  = 0x04, // Read Input Registers 3xxxx
    MB_FC_WRITE_COIL       = 0x05, // Write Single Coil (Output) 0xxxx
    MB_FC_WRITE_REG        = 0x06, // Preset Single Register 4xxxx
    MB_FC_WRITE_COILS      = 0x0F, // Write Multiple Coils (Outputs) 0xxxx
    MB_FC_WRITE_REGS       = 0x10, // Write block of contiguous registers 4xxxx
};

//Exception Codes
enum {
    MB_EX_ILLEGAL_FUNCTION = 0x01, // Function Code not Supported
    MB_EX_ILLEGAL_ADDRESS  = 0x02, // Output Address not exists
    MB_EX_ILLEGAL_VALUE    = 0x03, // Output Value not in Range
    MB_EX_SLAVE_FAILURE    = 0x04, // Slave Device Fails to process request
};

//Reply Types
enum {
    MB_REPLY_OFF    = 0x01,
    MB_REPLY_ECHO   = 0x02,
    MB_REPLY_NORMAL = 0x03,
};

typedef struct TRegister {
    IEC_UINT address;
    IEC_UINT value;
    struct TRegister* next;
} TRegister;

class Modbus {
    private:
        TRegister *_regs_head;
        TRegister *_regs_last;

        void readRegisters(IEC_UINT startreg, IEC_UINT numregs);
        void writeSingleRegister(IEC_UINT reg, IEC_UINT value);
        void writeMultipleRegisters(byte* frame,IEC_UINT startreg, IEC_UINT numoutputs, byte bytecount);
        void exceptionResponse(byte fcode, byte excode);
        #ifndef USE_HOLDING_REGISTERS_ONLY
            void readCoils(IEC_UINT startreg, IEC_UINT numregs);
            void readInputStatus(IEC_UINT startreg, IEC_UINT numregs);
            void readInputRegisters(IEC_UINT startreg, IEC_UINT numregs);
            void writeSingleCoil(IEC_UINT reg, IEC_UINT status);
            void writeMultipleCoils(byte* frame,IEC_UINT startreg, IEC_UINT numoutputs, byte bytecount);
        #endif

        TRegister* searchRegister(IEC_UINT addr);

        void addReg(IEC_UINT address, IEC_UINT value = 0);
        bool Reg(IEC_UINT address, IEC_UINT value);
        IEC_UINT Reg(IEC_UINT address);

    protected:
        byte *_frame;
        byte  _len;
        byte  _reply;
        void receivePDU(byte* frame);

    public:
        Modbus();

        void addHreg(IEC_UINT offset, IEC_UINT value = 0);
        bool Hreg(IEC_UINT offset, IEC_UINT value);
        IEC_UINT Hreg(IEC_UINT offset);

        #ifndef USE_HOLDING_REGISTERS_ONLY
            void addCoil(IEC_UINT offset, bool value = false);
            void addIsts(IEC_UINT offset, bool value = false);
            void addIreg(IEC_UINT offset, IEC_UINT value = 0);

            bool Coil(IEC_UINT offset, bool value);
            bool Ists(IEC_UINT offset, bool value);
            bool Ireg(IEC_UINT offset, IEC_UINT value);

            bool Coil(IEC_UINT offset);
            bool Ists(IEC_UINT offset);
            IEC_UINT Ireg(IEC_UINT offset);
        #endif
};

#endif //MODBUS_H