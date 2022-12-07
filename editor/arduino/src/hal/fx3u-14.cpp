#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for STM32F411CE boards (blackpill)
/******************PINOUT CONFIGURATION**************************
Digital In:  29, 30, 27, 28, 79, 26, 77, 78     (%IX0.0 - %IX0.7)
Digital Out: 41, 40, 8, 0, 19, 60               (%QX0.0 - %QX0.5)
Analog In:   -                 	    (%IW0 - %IW0)
Analog Out:  -                      (%QW0 - %QW0)
*****************************************************************/

//Define the number of inputs and outputs for this board
#define NUM_DISCRETE_INPUT          8
#define NUM_ANALOG_INPUT            0
#define NUM_DISCRETE_OUTPUT         6
#define NUM_ANALOG_OUTPUT           0

#define RUN_LED                     58
#define RUN_PIN                     PB2

uint8_t pinMask_DIN[] = { 29, 30, 27, 28, 79, 26, 77, 78 };
uint8_t pinMask_DOUT[] = { 41, 40, 8, 0, 19, 60 };
uint8_t pinMask_AIN[] = { };
uint8_t pinMask_AOUT[] = { };


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
    
    //Extra
    pinMode(RUN_PIN, INPUT);
    pinMode(RUN_LED, OUTPUT);
    
    //Fix Serial
    Serial.setRx(PA10);
    Serial.setTx(PA9);
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (bool_input[i / 8][i % 8] != NULL)
            *bool_input[i / 8][i % 8] = digitalRead(pinMask_DIN[i]);
    }

    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
            *int_input[i] = (analogRead(pinMask_AIN[i]) * 16);
    }
}

void updateOutputBuffers()
{
    if (digitalRead(RUN_PIN))
    {
        //PLC is in STOP mode
        digitalWrite(RUN_LED, HIGH);
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
