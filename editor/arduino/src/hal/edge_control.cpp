#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

#include <Arduino_EdgeControl.h>

//OpenPLC HAL for Arduino Edge Control

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

void hardwareInit()
{
    EdgeControl.begin();
    //Enables Power
    Power.enable3V3();
    Power.enable5V();

    //Start IO expansion
    //Wire.begin();
    //Expander.begin();
    //while (!Expander) {delay(1);}
    //Input.begin();
    //Input.enable();
    //analogReadResolution(12);
    Relay.begin();

    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        pinMode(pinMask_DIN[i], INPUT);
    }
    
    //for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    //{
    //    pinMode(pinMask_AIN[i], INPUT);
    //}
    
    //for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    //{
    //    pinMode(pinMask_DOUT[i], OUTPUT);
    //}

    //for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    //{
    //    pinMode(pinMask_AOUT[i], OUTPUT);
    //}
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (bool_input[i/8][i%8] != NULL) 
            *bool_input[i/8][i%8] = digitalRead(pinMask_DIN[i]);
    }
    
    /*
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
            *int_input[i] = (Input.analogRead(pinMask_AIN[i]));
    }
    */
}

void updateOutputBuffers()
{
    
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        if (bool_output[i/8][i%8] != NULL)
        {
            if (*bool_output[i/8][i%8])
            {
                Relay.on(pinMask_DOUT[i]);
            }
            else
            {
                Relay.off(pinMask_DOUT[i]);
            }

        }
    }
    /*
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        if (int_output[i] != NULL) 
            analogWrite(pinMask_AOUT[i], (*int_output[i] / 256));
    }
    */
}
