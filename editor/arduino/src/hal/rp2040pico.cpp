#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"

//OpenPLC HAL for Raspberry Pi Pico/Pico W with the RP2040

/******************PINOUT CONFIGURATION***********************
Digital In:  6, 7 ,8, 9, 10, 11, 12, 13      (%IX0.0 - %IX0.7)
Digital Out: 14, 15, 16, 17, 18, 19, 20, 21  (%QX0.0 - %QX0.7)
Analog In: A1, A2, A3 (26,27,28)             (%IW0 - %IW2)
Analog Out: 4,5                              (%QW0 - %QW1)
**************************************************************/

//Define the number of inputs and outputs for this board
#define NUM_DISCRETE_INPUT          8
#define NUM_ANALOG_INPUT            3
#define NUM_DISCRETE_OUTPUT         8
#define NUM_ANALOG_OUTPUT           2
/*
    Refer to Pico-OpenPLC-A4-Pinout.pdf & -PicoPLC schem.pdf for details
    on using the Pico/Pico W as a plc
    An additional 2 analogue outputs can be used with GPIO2 & 3 if the      
    SPI functionality is not required (adding extra code to the .ino file)     
*/
//Create the I/O pin masks
uint8_t pinMask_DIN[] = {6, 7, 8, 9, 10, 11, 12, 13};
uint8_t pinMask_AIN[] = {26, 27, 28}; 
uint8_t pinMask_DOUT[] = {14, 15, 16, 17, 18, 19, 20, 21};
uint8_t pinMask_AOUT[] = {4,5}; //2,3 can be used if SPI not required

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
        /*
            Changed to work with the Raspberry Pi Pico/Pico W
            Nano connect uses the A0-A3 from the RP2040
            and A4-A7 from the Nina-W102
        */		
//            *int_input[i] = (analogRead(pinMask_AIN[i]) * 64);
            *int_input[i] = analogRead(pinMask_AIN[i]);
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
