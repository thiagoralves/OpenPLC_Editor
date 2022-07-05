#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for CONTROLLINO MINI see https://www.controllino.com/wp-content/uploads/2021/03/CONTROLLINO-MINI-Pinout.pdf

/************************PINOUT CONFIGURATION*************************
Digital In:  A2, A3, A6, A7, IN0, IN1                   (%IX0.0 - %IX0.5)

Digital Out: D0, D3, D4, D5, D6, D7                     (%QX0.0 - %QX0.5)

Analog In:   A0, A1                                     (%IW0 - %IW1)

Analog Out:  D1, D2                                     (%QW0 - %QW1)
*********************************************************************/

//Define the number of inputs and outputs for this board (mapping for the Arduino Mega)
#define NUM_DISCRETE_INPUT         6
#define NUM_ANALOG_INPUT           2
#define NUM_DISCRETE_OUTPUT        6
#define NUM_ANALOG_OUTPUT          2

//Create the I/O pin masks
uint8_t pinMask_DIN[] =     { A2, A3, A6, A7, 2, 3 };
uint8_t pinMask_AIN[] =     { A0, A1 };
uint8_t pinMask_DOUT[] =    { 4, 7, 8, 9, A4, A5 };
uint8_t pinMask_AOUT[] =    { 5, 6 };

void hardwareInit()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
		uint8_t pin = pinMask_DIN[i];
        pinMode(pin, INPUT);
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
		uint8_t pin = pinMask_AIN[i];
        pinMode(pin, INPUT);
    }
    
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
		uint8_t pin = pinMask_DOUT[i];
        pinMode(pin, OUTPUT);
    }

    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
		uint8_t pin = pinMask_AOUT[i];
        pinMode(pin, OUTPUT);
    }
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
		uint8_t pin = pinMask_DIN[i];
        if (bool_input[i/8][i%8] != NULL) 
            *bool_input[i/8][i%8] = digitalRead(pin);
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
		uint8_t pin = pinMask_AIN[i];
        if (int_input[i] != NULL)
            *int_input[i] = (analogRead(pin) * 64);
    }
}

void updateOutputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
		uint8_t pin = pinMask_DOUT[i];
        if (bool_output[i/8][i%8] != NULL) 
            digitalWrite(pin, *bool_output[i/8][i%8]);
    }
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
		uint8_t pin = pinMask_AOUT[i];
        if (int_output[i] != NULL) 
            analogWrite(pin, (*int_output[i] / 256));
    }
}
