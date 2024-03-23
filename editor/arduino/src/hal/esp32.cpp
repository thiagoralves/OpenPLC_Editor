#include <stdlib.h>
extern "C" {
 #include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"
#include "driver/ledc.h"

// OpenPLC HAL for ESP32 boards
// NOTE: PWM channel == pin number

// Create the I/O pin masks (defined within editor GUI when compiling for board)
uint8_t pinMask_DIN[] = {PINMASK_DIN};
uint8_t pinMask_AIN[] = {PINMASK_AIN};
uint8_t pinMask_DOUT[] = {PINMASK_DOUT};
uint8_t pinMask_AOUT[] = {PINMASK_AOUT};

#define PWM_ANALOG_FREQ       4000 // Frequency to use when emulating analog on boards without a DAC
#define PWM_RESOLUTION        12 // 12-bit should allow up to 10kHz
#define PWM_MAX               0xFFF // 12-bit max

extern "C" uint8_t set_hardware_pwm(uint8_t, float, float); //this call is required for the C-based PWM block on the Editor

bool pwm_initialized[64] = {false}; // Store which PWM channels have been initialised

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
        #if !SOC_DAC_SUPPORTED
        ledcAttach(pinMask_AOUT[i], PWM_ANALOG_FREQ, PWM_RESOLUTION);
        #endif
    }
}

uint8_t set_hardware_pwm(uint8_t ch, float freq, float duty)
{
    if (!pwm_initialized[ch])
    {
        if (!ledcAttach(ch, (uint32_t)freq, PWM_RESOLUTION))
        {
            return 0;
        }
        pwm_initialized[ch] = true;
    }

    ledcWrite(ch, (uint32_t)(duty / 100 * PWM_MAX));
    return ledcChangeFrequency(ch, (uint32_t)freq, PWM_RESOLUTION);
}

void updateInputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        *bool_input[i/8][i%8] = digitalRead(pinMask_DIN[i]);
    }

    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        *int_input[i] = (analogRead(pinMask_AIN[i]) * 16);
    }
}

void updateOutputBuffers()
{
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        digitalWrite(pinMask_DOUT[i], *bool_output[i/8][i%8]);
    }

    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        #if SOC_DAC_SUPPORTED
        dacWrite(pinMask_AOUT[i], (*int_output[i] / 256));
        #else
        ledcWrite(pinMask_AOUT[i], (*int_output[i] / 16));
        #endif
    }
}
