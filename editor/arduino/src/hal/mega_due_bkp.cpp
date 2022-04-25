#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for Arduino Mega and Arduino Due

/************************PINOUT CONFIGURATION*************************
Digital In: 62, 63, 64, 65, 66, 67, 68, 69        (%IX0.0 - %IX0.7)
            22, 24, 26, 28, 30, 32, 34, 36        (%IX1.0 - %IX1.7)
            38, 40, 42, 44, 46, 48, 50, 52        (%IX2.0 - %IX2.7)
			
Digital Out: 14, 15, 16, 17, 18, 19, 20, 21       (%QX0.0 - %QX0.7)
             23, 25, 27, 29, 31, 33, 35, 37       (%QX1.0 - %QX1.7)
             39, 41, 43, 45, 47, 49, 51, 53       (%QX2.0 - %QX2.7)
			 
Analog In: A0, A1, A2, A3, A4, A5, A6, A7         (%IW0 - %IW7)
		   
Analog Out: 2, 3, 4, 5, 6, 7, 8, 9                (%QW0 - %QW7)
            10, 11, 12, 13                        (%QW8 - %QW11)
			
*********************************************************************/

//Define the number of inputs and outputs for this board (mapping for the Arduino Mega)
#define NUM_DISCRETE_INPUT         24
#define NUM_ANALOG_INPUT           8
#define NUM_DISCRETE_OUTPUT        24
#define NUM_ANALOG_OUTPUT          12

//Create the I/O pin masks
//const PROGMEM uint8_t pinMask_DIN[] = {62, 63, 64, 65, 66, 67, 68, 69, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52};
const PROGMEM uint8_t pinMask_DIN[] = {62, 63, 64, 65, 66, 67, 68, 69, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52};
const PROGMEM uint8_t pinMask_AIN[] = {A0, A1, A2, A3, A4, A5, A6, A7};
const PROGMEM uint8_t pinMask_DOUT[] = {14, 15, 16, 17, 18, 19, 20, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53};
const PROGMEM uint8_t pinMask_AOUT[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13};

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
        uint8_t pin = pgm_read_byte(pinMask_DIN + i);
        pinMode(pin, INPUT);
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_AIN + i);
        pinMode(pin, INPUT);
    }
    
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_DOUT + i);
        pinMode(pin, OUTPUT);
    }

    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_AOUT + i);
        pinMode(pin, OUTPUT);
    }
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_DIN + i);
        if (checkPin(pin))
        {
            if (bool_input[i/8][i%8] != NULL) 
                *bool_input[i/8][i%8] = digitalRead(pin);
        }
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_AIN + i);
        if (checkPin(pin))
        {
            if (int_input[i] != NULL)
                *int_input[i] = (analogRead(pin) * 64);
        }
    }
}

void updateOutputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_DOUT + i);
        if (checkPin(pin))
        {
            if (bool_output[i/8][i%8] != NULL) 
                digitalWrite(pin, *bool_output[i/8][i%8]);
        }
    }
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
		uint8_t pin = pgm_read_byte(pinMask_AOUT + i);
        if (checkPin(pin))
        {
            if (int_output[i] != NULL) 
                analogWrite(pin, (*int_output[i] / 256));
        }
    }
}
