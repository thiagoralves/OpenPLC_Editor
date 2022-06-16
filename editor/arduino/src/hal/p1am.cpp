#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for AutomationDirect P1AM PLC

/******************PINOUT CONFIGURATION***********************
Digital In:  31, 0, 1, 2, 3, 4              (%IX0.0 - %IX0.5)
Digital Out: 32, 6, 7, 11, 12, 13, 14       (%QX0.0 - %QX0.6)
Analog In: A1, A2, A5, A6                   (%IW0 - %IW3)
Analog Out: A0                              (%QW0 - %QW0)

Notes:
P1AM Toggle Switch (digital pin 31) mapped to %IX0.0
P1AM LED (digital pin 32) mapped to %QX0.0
**************************************************************/

//Define the number of inputs and outputs for this board (mapping for the Arduino UNO)
#define NUM_DISCRETE_INPUT          6
#define NUM_ANALOG_INPUT            7
#define NUM_DISCRETE_OUTPUT         4
#define NUM_ANALOG_OUTPUT           1

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {31, 0, 1, 2, 3, 4};
uint8_t pinMask_AIN[] = {A1, A2, A5, A6};
uint8_t pinMask_DOUT[] = {32, 6, 7, 11, 12, 13, 14};
uint8_t pinMask_AOUT[] = {A0};

extern uint8_t disabled_pins[11];

bool checkPin(uint8_t pin)
{
    for (int i = 1; i < disabled_pins[0]; i++)
    {
        if (pin == disabled_pins[i])
        {
            return false;
        }
    }
    return true;
}

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
            analogWrite(pinMask_AOUT[i], (*int_output[i] / 256));
    }
}
