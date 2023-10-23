/*
ModbusSlave.h - Header for Modbus Slave Library
Copyright (C) 2022 OpenPLC - Thiago Alves
*/

#ifndef MODBUSSLAVE_H
#define MODBUSSLAVE_H

#include <Arduino.h>
#include "defines.h"

#define bitRead(value, bit) (((value) >> (bit)) & 0x01)
//#define bitSet(value, bit) ((value) |= (1UL << (bit)))
//#define bitClear(value, bit) ((value) &= ~(1UL << (bit)))
#define bitWrite(value, bit, bitvalue) (bitvalue ? bitSet(value, bit) : bitClear(value, bit))
#define COILS           0
#define INPUTSTATUS     1
#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__) || defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega16U4__)
    #define MAX_MB_FRAME 128
#else
    #define MAX_MB_FRAME 256
#endif
#define MAX_SRV_CLIENTS 3 //how many clients should be able to connect to TCP server at the same time
#define MBAP_SIZE       6

//Platform specific defines and includes
#ifdef MBTCP_ETHERNET
#include <SPI.h>
#include <Ethernet.h>
#endif

#ifdef MBTCP_WIFI
#if defined(BOARD_ESP8266)
#include <ESP8266WiFi.h>
#elif defined(BOARD_ESP32)
#include <WiFi.h>
#elif defined(BOARD_WIFININA)
#include <WiFiNINA.h>
#else
#include <SPI.h>
#include <WiFi.h>
#endif
#endif

#if defined(CONTROLLINO_MAXI) || defined(CONTROLLINO_MEGA)
#include "Controllino.h"
#endif

// Debugger functions
extern "C" uint16_t get_var_count(void);
extern "C" size_t get_var_size(size_t);// {return 0;}
extern "C" void *get_var_addr(size_t);// {return 0;}
extern "C" void force_var(size_t, bool, void *);// {}
extern "C" void set_trace(size_t, bool, void *);// {}
extern "C" void trace_reset(void);// {}
extern uint32_t __tick;

#define MB_DEBUG_SUCCESS                 0x7E
#define MB_DEBUG_ERROR_OUT_OF_BOUNDS     0x81
#define MB_DEBUG_ERROR_OUT_OF_MEMORY     0x82

//Modbus registers struct
struct MBinfo {
    uint8_t slaveid;
    uint16_t *holding;
    uint8_t holding_size;
    uint8_t *coils;
    uint8_t coils_size;
    uint16_t *input_regs;
    uint8_t input_regs_size;
    uint8_t *input_status;
    uint8_t input_status_size;
};

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
    MB_FC_DEBUG_INFO       = 0x41, // Request debug variables count
    MB_FC_DEBUG_SET        = 0x42, // Debug set trace (force variable)
    MB_FC_DEBUG_GET        = 0x43, // Debug get trace (read variables)
    MB_FC_DEBUG_GET_LIST   = 0x44, // Debug get trace list (read list of variables)
    MB_FC_DEBUG_GET_MD5    = 0x45, // Debug get current program MD5
};

//Exception Codes
enum {
    MB_EX_ILLEGAL_FUNCTION = 0x01, // Function Code not Supported
    MB_EX_ILLEGAL_ADDRESS  = 0x02, // Output Address not exists
    MB_EX_ILLEGAL_VALUE    = 0x03, // Output Value not in Range
    MB_EX_SLAVE_FAILURE    = 0x04, // Slave Device Fails to process request
};

//Global Modbus vars
extern struct MBinfo modbus;
extern uint8_t mb_frame[MAX_MB_FRAME];
extern uint16_t mb_frame_len;
extern Stream* mb_serialport;
extern int8_t mb_txpin;
extern uint16_t mb_t15; // inter character time out
extern uint16_t mb_t35; // frame delay
#ifdef MBTCP_ETHERNET
    extern EthernetServer mb_server;
    extern uint8_t mb_mbap[MBAP_SIZE];
#ifdef BOARD_PORTENTA
    extern EthernetClient mb_serverClients[MAX_SRV_CLIENTS];
#endif
#endif

#ifdef MBTCP_WIFI
    extern WiFiServer mb_server;
    extern uint8_t mb_mbap[MBAP_SIZE];
#if defined(BOARD_ESP8266) || defined(BOARD_ESP32) || defined(BOARD_PORTENTA)
    extern WiFiClient mb_serverClients[MAX_SRV_CLIENTS];
#endif
#endif

bool init_mbregs(uint8_t size_holding, uint8_t size_coils, uint8_t input_regs, uint8_t input_status);
bool get_discrete(uint16_t addr, bool regtype);
void write_discrete(uint16_t addr, bool regtype, bool value);
void mbconfig_serial_iface(HardwareSerial* port, long baud, int txPin);
#ifdef MBTCP
void mbconfig_ethernet_iface(uint8_t *mac, uint8_t *ip, uint8_t *dns, uint8_t *gateway, uint8_t *subnet);
#endif
void mbtask();
#ifdef MBTCP
void handle_tcp();
#endif
#ifdef MBSERIAL
void handle_serial();
#endif
void process_mbpacket();
uint16_t calcCrc();

//Modbus handling functions
void readRegisters(uint16_t startreg, uint16_t numregs);
void writeSingleRegister(uint16_t reg, uint16_t value);
void writeMultipleRegisters(uint16_t startreg, uint16_t numoutputs, uint8_t bytecount);
void exceptionResponse(uint16_t fcode, uint16_t excode);
void readCoils(uint16_t startreg, uint16_t numregs);
void readInputStatus(uint16_t startreg, uint16_t numregs);
void readInputRegisters(uint16_t startreg, uint16_t numregs);
void writeSingleCoil(uint16_t reg, uint16_t status);
void writeMultipleCoils(uint16_t startreg, uint16_t numoutputs, uint16_t bytecount);
void debugInfo(void);
void debugSetTrace(uint16_t varidx, uint8_t flag, uint16_t len, void *value);
void debugGetTrace(uint16_t startidx, uint16_t endidx);
void debugGetTraceList(uint16_t numIndexes, uint8_t *indexArray);
void debugGetMd5(void);


/* Table of CRC values for high-order byte */
const byte _auchCRCHi[] = {
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
  0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
  0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
  0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
  0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81,
  0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
  0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
  0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
  0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
  0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
  0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
  0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
  0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
  0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
  0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
  0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
  0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
  0x40};

/* Table of CRC values for low-order byte */
const byte _auchCRCLo[] = {
    0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7, 0x05, 0xC5, 0xC4,
  0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09,
  0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD,
  0x1D, 0x1C, 0xDC, 0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
  0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32, 0x36, 0xF6, 0xF7,
  0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A,
  0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38, 0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE,
  0x2E, 0x2F, 0xEF, 0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
  0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1, 0x63, 0xA3, 0xA2,
  0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4, 0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F,
  0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB,
  0x7B, 0x7A, 0xBA, 0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
  0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0, 0x50, 0x90, 0x91,
  0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C,
  0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88,
  0x48, 0x49, 0x89, 0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
  0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83, 0x41, 0x81, 0x80,
  0x40};


#endif
