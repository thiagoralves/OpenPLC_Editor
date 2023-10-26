#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

#if defined(__SAM3X8E__) || defined(__SAMD21G18A__)
    #include "SAMD_PWM.h"
#else
    #include "AVR_PWM.h"
#endif

//OpenPLC HAL for Arduino Uno and Arduino Nano (old) form factor (Uno, Leonardo, Nano, Micro and Zero)

/******************PINOUT CONFIGURATION*******************
Digital In: 2, 3, 4, 5, 6           (%IX0.0 - %IX0.4)
Digital Out: 7, 8, 12, 13           (%QX0.0 - %QX0.3)
Analog In: A0, A1, A2, A3, A4, A5   (%IW0 - %IW5)
Analog Out: 9, 10, 11               (%QW0 - %QW2)
**********************************************************/

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {PINMASK_DIN};
uint8_t pinMask_AIN[] = {PINMASK_AIN};
uint8_t pinMask_DOUT[] = {PINMASK_DOUT};
uint8_t pinMask_AOUT[] = {PINMASK_AOUT};

#define PWM_DEFAULT_FREQ      490
#define PWM_CHANNEL_0_PIN     9
#define PWM_CHANNEL_1_PIN     10

#ifdef __AVR_ATmega32U4__
    #define NUM_OF_PWM_PINS       2
#else
    #define NUM_OF_PWM_PINS       3
    #define PWM_CHANNEL_2_PIN     11
#endif


#if defined(__SAM3X8E__) || defined(__SAMD21G18A__)
    SAMD_PWM *PWM_Instance[NUM_OF_PWM_PINS];
#else
    AVR_PWM *PWM_Instance[NUM_OF_PWM_PINS];
#endif

extern "C" uint8_t set_hardware_pwm(uint8_t, float, float); //this call is required for the C-based PWM block on the Editor

bool pwm_initialized = false;

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

void init_pwm()
{
    // If PWM_CONTROLLER block is being used, disable pins from regular analogWrite
    #ifdef __AVR_ATmega32U4__
        const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN};
    #else
	const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN, PWM_CHANNEL_2_PIN};
    #endif
    
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        for (int j = 0; j < NUM_OF_PWM_PINS; j++)
        {
            if (pinMask_AOUT[i] == pins[j])
            {
                pinMask_AOUT[i] = 255; //disable pin
            }
        }
    }

    // Initialize PWM pins
    #if defined(__SAM3X8E__) || defined(__SAMD21G18A__)
        PWM_Instance[0] = new SAMD_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[1] = new SAMD_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
	PWM_Instance[2] = new SAMD_PWM(PWM_CHANNEL_2_PIN, PWM_DEFAULT_FREQ, 0);
    #else
	#ifdef __AVR_ATmega32U4__
            PWM_Instance[0] = new AVR_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
            PWM_Instance[1] = new AVR_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
	#else
	    PWM_Instance[0] = new AVR_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
            PWM_Instance[1] = new AVR_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
	    PWM_Instance[2] = new AVR_PWM(PWM_CHANNEL_2_PIN, PWM_DEFAULT_FREQ, 0);
	#endif
    #endif
}

uint8_t set_hardware_pwm(uint8_t ch, float freq, float duty)
{
    if (pwm_initialized == false)
    {
        init_pwm();
        pwm_initialized = true;
    }

    #ifdef __AVR_ATmega32U4__
        const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN};
    #else
	const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN, PWM_CHANNEL_2_PIN};
    #endif

    if (ch >= NUM_OF_PWM_PINS)
    {
        return 0;
    }

    if (PWM_Instance[ch]->setPWM(pins[ch], freq, duty))
    {
        return 1;
    }

    return 0;
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
