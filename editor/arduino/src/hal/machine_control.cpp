#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include <Arduino_MachineControl.h>
#include "Wire.h"
#include "../examples/Baremetal/defines.h"

using namespace machinecontrol;

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {PINMASK_DIN};
uint8_t pinMask_AIN[] = {PINMASK_AIN};
uint8_t pinMask_DOUT[] = {PINMASK_DOUT};
uint8_t pinMask_AOUT[] = {PINMASK_AOUT};

void hardwareInit()
{
    //Setup Digital Inputs
    Wire.begin();
    digital_inputs.init();
    
    //Setup Analog Inputs
    analogReadResolution(16);
    analog_in.set0_10V();
    
    //Setup Digital Outputs
    digital_outputs.setLatch(); //Set digital outputs in retry mode during overcurrent
    digital_outputs.setAll(0); //At startup set all channels to OPEN
    
    //Setup Analog Outputs
    analog_out.period_ms(0, 4);
    analog_out.period_ms(1, 4);
    analog_out.period_ms(2, 4);
    analog_out.period_ms(3, 4);
    
    /*
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
    */
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (bool_input[i/8][i%8] != NULL) 
            *bool_input[i/8][i%8] = digital_inputs.read(pinMask_DIN[i]);
    }
	
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
            *int_input[i] = analog_in.read(pinMask_AIN[i]);
    }
    
}

void updateOutputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        if (bool_output[i/8][i%8] != NULL)
            digital_outputs.set(pinMask_DOUT[i], *bool_output[i/8][i%8]);
    }
	
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        if (int_output[i] != NULL)
            analogWrite(pinMask_AOUT[i], ((float)*int_output[i] / 1000.0));
    }
}
