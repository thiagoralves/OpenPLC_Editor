#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for ESP8266 boards

/******************PINOUT CONFIGURATION***********************
Digital In:  4, 5, 6, 7                     (%IX0.0 - %IX0.3)
Digital Out: 0, 1, 2, 3                     (%QX0.0 - %QX0.3)
Analog In: A0                               (%IW0)
Analog Out: 8                               (%QW0)
**************************************************************/

//Define the number of inputs and outputs for this board (mapping for the NodeMCU 1.0)
#define NUM_DISCRETE_INPUT          4
#define NUM_ANALOG_INPUT            1
#define NUM_DISCRETE_OUTPUT         4
#define NUM_ANALOG_OUTPUT           1

#define NODE_PIN_D0		16
#define NODE_PIN_D1		5
#define NODE_PIN_D2		4
#define NODE_PIN_D3		0
#define NODE_PIN_D4		2
#define NODE_PIN_D5		14
#define NODE_PIN_D6		12
#define NODE_PIN_D7		13
#define NODE_PIN_D8		15

uint8_t pinMask_DIN[] = { NODE_PIN_D4, NODE_PIN_D5, NODE_PIN_D6, NODE_PIN_D7 };
uint8_t pinMask_DOUT[] = { NODE_PIN_D0, NODE_PIN_D1, NODE_PIN_D2, NODE_PIN_D3 };
uint8_t pinMask_AIN[] = { A0 };
uint8_t pinMask_AOUT[] = { NODE_PIN_D8 };

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
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (bool_input[i/8][i%8] != NULL) 
            *bool_input[i/8][i%8] = digitalRead(pinMask_DIN[i]);
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
            *int_input[i] = (analogRead(pinMask_AIN[i]) * 64);
    }
}

void updateOutputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        if (bool_output[i/8][i%8] != NULL) 
            digitalWrite(pinMask_DOUT[i], *bool_output[i/8][i%8]);
    }
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        if (int_output[i] != NULL) 
            analogWrite(pinMask_AOUT[i], (*int_output[i] / 64));
    }
}
