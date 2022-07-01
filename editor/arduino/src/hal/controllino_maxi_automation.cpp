#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for CONTROLLINO MAXI Automation see https://www.controllino.com/wp-content/uploads/2021/03/CONTROLLINO-MAXI-Automation-Pinout.pdf

/************************PINOUT CONFIGURATION*************************
Digital In:  AI2, AI3, AI4, AI5, AI6, AI7, AI8, AI9     (%IX0.0 - %IX0.7)
             AI10, AI11, DI0, DI1, DI2, DI3, IN0, IN1   (%IX1.0 - %IX1.7)

Digital Out: DO0, DO1, DO2, DO3, DO4, DO5, DO6, DO7     (%QX0.0 - %QX0.7)
             R0, R1, R2, R3, R4, R5, R6, R7             (%QX1.0 - %QX1.7)
             R8, R9                                     (%QX2.0 - %QX2.1)

Analog In:   AI0, AI1, AI13, AI13                       (%IW0 - %IW3)

Analog Out:  AO0, AO1                                   (%QW0 - %QW1)
*********************************************************************/

//Define the number of inputs and outputs for this board (mapping for the Arduino Mega)
#define NUM_DISCRETE_INPUT         16
#define NUM_ANALOG_INPUT           4
#define NUM_DISCRETE_OUTPUT        18
#define NUM_ANALOG_OUTPUT          2

//Create the I/O pin masks
uint8_t pinMask_DIN[] =     { A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, 10, 11, 18, 19 };
uint8_t pinMask_AIN[] =     { A0, A1, A14, A15 };
uint8_t pinMask_DOUT[] =    { 2, 3, 4, 5, 6, 7, 8, 9, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31 };
uint8_t pinMask_AOUT[] =    { 12, 13 };

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
