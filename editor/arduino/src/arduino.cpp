#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for AutomationDirect P1AM PLC

/******************PINOUT CONFIGURATION***********************
Digital In:  0, 1, 2, 3, 4, 5               (%IX0.0 - %IX0.5)
Digital Out: 7, 8, 9, 10, 11, 12            (%QX0.0 - %QX0.5)
Analog In: A1, A2, A3, A4, A5, A6           (%IW0 - %IW5)
Analog Out: 6, 15                           (%QW0 - %QW1)
**************************************************************/

//Define the number of inputs and outputs for this board (mapping for the Arduino UNO)
#define NUM_DISCRETE_INPUT          0
#define NUM_ANALOG_INPUT            0
#define NUM_DISCRETE_OUTPUT         0
#define NUM_ANALOG_OUTPUT           0

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {0, 1, 2, 3, 4, 5};
uint8_t pinMask_AIN[] = {A1, A2, A3, A4, A5, A6};
uint8_t pinMask_DOUT[] = {7, 8, 9, 10, 11, 12};
uint8_t pinMask_AOUT[] = {6, 15};

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
