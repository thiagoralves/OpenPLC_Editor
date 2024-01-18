#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

//OpenPLC HAL for Arduino Opta

/******************PINOUT CONFIGURATION***********************
Digital In:  IRQ_CH1, IRQ_CH2, IRQ_CH3, IRQ_CH4, IRQ_CH5, IRQ_CH6                  (%IX0.0 - %IX0.5)
Digital Out: RELAY_CH01, RELAY_CH02, RELAY_CH03, RELAY_CH04                        (%QX0.0 - %QX0.3)
Analog In: INPUT_420mA_CH01, INPUT_420mA_CH02, INPUT_420mA_CH03, INPUT_420mA_CH04  (%IW0 - %IW3)
           INPUT_05V_CH01, INPUT_05V_CH02, INPUT_05V_CH03, INPUT_05V_CH04          (%IW4 - %IW7)
           INPUT_05V_CH05, INPUT_05V_CH06, INPUT_05V_CH07, INPUT_05V_CH08          (%IW8 - %IW11)  
Analog Out:
**************************************************************/

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {PINMASK_DIN};
uint8_t pinMask_AIN[] = {PINMASK_AIN};
uint8_t pinMask_DOUT[] = {PINMASK_DOUT};
uint8_t pinMask_AOUT[] = {PINMASK_AOUT};

uint8_t analogInputMask[8] = {0, 0, 0, 0, 0, 0, 0, 0};
uint8_t digitalInputMask[8] = {1, 1, 1, 1, 1, 1, 1, 1};
uint8_t ledMask[4] = {LED_D0, LED_D1, LED_D2, LED_D3};

void hardwareInit()
{
    //Setup Opta LEDs
    pinMode(LED_D0, OUTPUT);
    pinMode(LED_D1, OUTPUT);
    pinMode(LED_D2, OUTPUT);
    pinMode(LED_D3, OUTPUT);

    //Opta inputs can be used either as digital or analog inputs. Therefore, to get
    //a proper sense of how each input is being used in the current program we must
    //validate each input on the respective buffer. If the buffer is NULL then that
    //particular input is not being used in the program
    analogReadResolution(16);
    for (int i = 0; i < 8; i++)
    {
        if (int_input[i] != NULL) //this input is being used as analog
        {
            analogInputMask[i] = 1;
            digitalInputMask[i] = 0;
        }
    }

    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (digitalInputMask[i])
            pinMode(pinMask_DIN[i], INPUT);
    }
    
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        pinMode(pinMask_DOUT[i], OUTPUT);
    }
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (bool_input[i/8][i%8] != NULL)
        {
            if (digitalInputMask[i])
            {
                *bool_input[i/8][i%8] = digitalRead(pinMask_DIN[i]);
            }
            else
            {
                *bool_input[i/8][i%8] = 0;
            }
        }
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
        {
            if (analogInputMask[i])
            {
                *int_input[i] = (analogRead(pinMask_AIN[i]));
            }
            else
            {
                *int_input[i] = 0;
            }
        }
    }
}

void updateOutputBuffers()
{
    
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        if (bool_output[i/8][i%8] != NULL)
        {
            digitalWrite(ledMask[i], *bool_output[i/8][i%8]);
            digitalWrite(pinMask_DOUT[i], *bool_output[i/8][i%8]);
        }
    }
}
