#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

// OpenPLC HAL for FX3U-14 Clone / WS3U-14Mx
// 2024 by Dieter Lambrecht
// based on fx3u-14.cpp
/******************PINOUT CONFIGURATION******************************************
Digital In:  PB13, PB14, PB11, PB12, PE15, PB10, PE13, PE14     (%IX0.0 - %IX0.7)
Digital Out: PC9, PC8, PA8, PA0, PB3, PD12                      (%QX0.0 - %QX0.5)
Analog In:   PA1, PA3, PC4, PC5, PC0, PC1, PC2, PC3             (%IW0 - %IW7)
Analog Out:  PA4, PA5                                           (%QW0 - %QW1)
*********************************************************************************/

#define RUN_LED                     PD10                            // RUN LED is inverse logic: HIGH for off, LOW for on
#define RUN_PIN                     PB2                             // RUN Switch is inverse logic: LOW is STOP Mode, HIGH is RUN Mode

#ifndef MBSERIAL_TXPIN                                              // if the TXPIN is not defined - set it to PA14 - otherwise RS485/ModBusRTU did not work !
    #define MBSERIAL_TXPIN PA14
#endif

#ifndef MBSERIAL_IFACE
    #define MBSERIAL_IFACE Serial3
#endif

#ifndef MBSERIAL_BAUD
    #define MBSERIAL_BAUD 57600
#endif

#ifndef MBSERIAL_SLAVE
    #define MBSERIAL_SLAVE 1
#endif

HardwareSerial Serial3(PC11_ALT1, PC_10_ALT1);                      //needed to use Serial3 for RS485 - also define PA14 as TxPin

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {PINMASK_DIN};
uint8_t pinMask_AIN[] = {PINMASK_AIN};
uint8_t pinMask_DOUT[] = {PINMASK_DOUT};
uint8_t pinMask_AOUT[] = {PINMASK_AOUT};


void hardwareInit()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        pinMode(pinMask_DIN[i], INPUT);
    }

    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        pinMode(pinMask_AIN[i], INPUT);
    }

    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        pinMode(pinMask_DOUT[i], OUTPUT);
    }

    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        pinMode(pinMask_AOUT[i], OUTPUT);
    }
    

    pinMode(RUN_PIN, INPUT);                                        // set the RUN PIN to input - this is the RUN Switch
    pinMode(RUN_LED, OUTPUT);                                       // set the RUN LED to output, this is the RUN LED

    Serial.begin(MBSERIAL_BAUD);                                    // Fix - without this Serial did not work
    Serial.setRx(PA10);                                             // Fix - without this Serial did not work
    Serial.setTx(PA9);                                              // Fix - without this Serial did not work
    Serial2.begin(MBSERIAL_BAUD);                                   // Fix - without this Serial did not work - don't know why

}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (bool_input[i / 8][i % 8] != NULL)
            *bool_input[i / 8][i % 8] = !digitalRead(pinMask_DIN[i]); //inverted
    }

    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
            *int_input[i] = (analogRead(pinMask_AIN[i]) * 16);
    }
}

void updateOutputBuffers()
{
    if (!digitalRead(RUN_PIN))  //inverted
    {
        //PLC is in STOP mode
        digitalWrite(RUN_LED, HIGH);
        /*                                                             // do nothing in STOP Mode !
        for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
        {
            if (bool_output[i / 8][i % 8] != NULL)
                digitalWrite(pinMask_DOUT[i], 0);
        }
        for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
        {
            if (int_output[i] != NULL)
                analogWrite(pinMask_AOUT[i], 0);
        }
        */
    }
    else
    {
        //PLC is in RUN mode
        digitalWrite(RUN_LED, LOW);
        for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
        {
            if (bool_output[i / 8][i % 8] != NULL)
                digitalWrite(pinMask_DOUT[i], *bool_output[i / 8][i % 8]);
        }
        for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
        {
            if (int_output[i] != NULL)
                analogWrite(pinMask_AOUT[i], (*int_output[i] / 256));
        }
    }
}
