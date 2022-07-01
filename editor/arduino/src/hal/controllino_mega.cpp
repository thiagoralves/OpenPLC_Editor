#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for CONTROLLINO MEGA see https://www.controllino.com/wp-content/uploads/2021/03/CONTROLLINO-MEGA-Pinout.pdf

/************************PINOUT CONFIGURATION*************************
Digital In:  A5, A6, A7, A8, A9, A10, A11, A12          (%IX0.0 - %IX0.7)
             A13, A14, A15, I16, I17, I18, IN0, IN1     (%IX1.0 - %IX1.7)

Digital Out: D12, D13, D14, D15, D16, D17, D18, D19     (%QX0.0 - %QX0.7)
             R0, R1, R2, R3, R4, R5, R6, R7             (%QX1.0 - %QX1.7)
             R8, R9, R10, R11, R12, R13, R14, R15       (%QX2.0 - %QX2.7)

Analog In:   A0, A1, A2, A3, A4                         (%IW0 - %IW4)

Analog Out:  D0, D1, D2, D3, D4, D5, D6, D7             (%QW0 - %QW7)
             D8, D9, D10, D11                           (%QW8 - %QW11)
*********************************************************************/

//Define the number of inputs and outputs for this board (mapping for the Arduino Mega)
#define NUM_DISCRETE_INPUT         16
#define NUM_ANALOG_INPUT           5
#define NUM_DISCRETE_OUTPUT        24
#define NUM_ANALOG_OUTPUT          12

//Create the I/O pin masks
uint8_t pinMask_DIN[] =     { A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, 38, 39, 40, 18, 19 };
uint8_t pinMask_AIN[] =     { A0, A1, A2, A3, A4 };
uint8_t pinMask_DOUT[] =    { 42, 43, 44, 45, 46, 47, 48, 49, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37 };
uint8_t pinMask_AOUT[] =    { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };

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
