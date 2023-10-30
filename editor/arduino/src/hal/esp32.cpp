#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

#if defined(__SAM3X8E__) || defined(__SAMD21G18A__)
    #include "SAMD_PWM.h"
#elif defined(ESP32) || defined(__ESP32__)
    #include "ESP32_FastPWM.h"
#else
    #include "AVR_PWM.h"
#endif

//OpenPLC HAL for ESP32 boards

/******************PINOUT CONFIGURATION**************************
Digital In:  17, 18, 19, 21, 22, 23, 27, 32 (%IX0.0 - %IX0.7)
             33                             (%IX1.0 - %IX1.0)
Digital Out: 01, 02, 03, 04, 05, 12, 13, 14 (%QX0.0 - %QX0.7)
             15, 16                         (%QX1.0 - %QX1.1)
Analog In:   34, 35, 36, 39                 (%IW0 - %IW2)
Analog Out:  25, 26                         (%QW0 - %QW1)
*****************************************************************/

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
#elif defined(ESP32) || defined(__ESP32__)
    #define NUM_OF_PWM_PINS       2
    #define PWM_CHANNEL_0_PIN     32
    #define PWM_CHANNEL_1_PIN     33
	
#else
    #define NUM_OF_PWM_PINS       3
    #define PWM_CHANNEL_2_PIN     11
#endif


#if defined(__SAM3X8E__) || defined(__SAMD21G18A__)
    SAMD_PWM *PWM_Instance[NUM_OF_PWM_PINS];
#elif defined(ESP32) || defined(__ESP32__)
    ESP32_FAST_PWM *PWM_Instance[NUM_OF_PWM_PINS];
#else
    AVR_PWM *PWM_Instance[NUM_OF_PWM_PINS];
#endif


    #ifdef __AVR_ATmega32U4__
        const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN};
	#elif defined(ESP32) || defined(__ESP32__)		
	    const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN};	
    #else
	const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN, PWM_CHANNEL_2_PIN};
    #endif

extern "C" uint8_t set_hardware_pwm(uint8_t, float, float); //this call is required for the C-based PWM block on the Editor

bool pwm_initialized = false;

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

void init_pwm()
{
    // If PWM_CONTROLLER block is being used, disable pins from regular analogWrite

    
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
	#elif defined(__AVR_ATmega32U4__)
        PWM_Instance[0] = new AVR_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[1] = new AVR_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
	#elif defined(ESP32) || defined(__ESP32__)
		PWM_Instance[0] = new ESP32_FAST_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0, 0); //ESP32_FAST_PWM needs different "Timer Groups" for different frequencys. see ESP32_FAST_PWM docu.
		PWM_Instance[1] = new ESP32_FAST_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0, 2); //ESP32_FAST_PWM needs different "Timer Groups" for different frequencys. see ESP32_FAST_PWM docu.
	#else
		PWM_Instance[0] = new AVR_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
		PWM_Instance[1] = new AVR_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
		PWM_Instance[2] = new AVR_PWM(PWM_CHANNEL_2_PIN, PWM_DEFAULT_FREQ, 0);
	#endif
}

uint8_t set_hardware_pwm(uint8_t ch, float freq, float duty)
{
	
	     Serial.println(ch); 
         Serial.println(freq); 
         Serial.println(duty);

	
    if (pwm_initialized == false)
    {
        init_pwm();
        pwm_initialized = true;
    }


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
        if (bool_input[i/8][i%8] != NULL) 
            *bool_input[i/8][i%8] = digitalRead(pinMask_DIN[i]);
    }
    
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
            *int_input[i] = (analogRead(pinMask_AIN[i]) * 16);
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
            dacWrite(pinMask_AOUT[i], (*int_output[i] / 256));
    }
}
