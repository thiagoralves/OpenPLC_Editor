#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

#if defined(__AVR__)
    #include "AVR_PWM.h"
#else
    #include "SAMDUE_PWM.h"
#endif

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

//Create the I/O pin masks
uint8_t pinMask_DIN[] = {PINMASK_DIN};
uint8_t pinMask_AIN[] = {PINMASK_AIN};
uint8_t pinMask_DOUT[] = {PINMASK_DOUT};
uint8_t pinMask_AOUT[] = {PINMASK_AOUT};

#define NUM_OF_PWM_PINS       12
#define PWM_DEFAULT_FREQ      490

#if defined(__AVR__)
    #define PWM_CHANNEL_0_PIN     2
    #define PWM_CHANNEL_1_PIN     3
    #define PWM_CHANNEL_2_PIN     255 // disable pin 4 as it uses TIMER0
    #define PWM_CHANNEL_3_PIN     5
    #define PWM_CHANNEL_4_PIN     6
    #define PWM_CHANNEL_5_PIN     7
    #define PWM_CHANNEL_6_PIN     8
    #define PWM_CHANNEL_7_PIN     9
    #define PWM_CHANNEL_8_PIN     10
    #define PWM_CHANNEL_9_PIN     11
    #define PWM_CHANNEL_10_PIN    12
    #define PWM_CHANNEL_11_PIN    255 // disable pin 13 as it uses TIMER0
#else
    #define PWM_CHANNEL_0_PIN     2
    #define PWM_CHANNEL_1_PIN     3
    #define PWM_CHANNEL_2_PIN     4
    #define PWM_CHANNEL_3_PIN     5
    #define PWM_CHANNEL_4_PIN     6
    #define PWM_CHANNEL_5_PIN     7
    #define PWM_CHANNEL_6_PIN     8
    #define PWM_CHANNEL_7_PIN     9
    #define PWM_CHANNEL_8_PIN     10
    #define PWM_CHANNEL_9_PIN     11
    #define PWM_CHANNEL_10_PIN    12
    #define PWM_CHANNEL_11_PIN    13
#endif


#if defined(__AVR__)
    AVR_PWM *PWM_Instance[NUM_OF_PWM_PINS];
#else
    SAMDUE_PWM *PWM_Instance[NUM_OF_PWM_PINS];
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
    const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN, PWM_CHANNEL_2_PIN, PWM_CHANNEL_3_PIN, PWM_CHANNEL_4_PIN, PWM_CHANNEL_5_PIN,
                            PWM_CHANNEL_6_PIN, PWM_CHANNEL_7_PIN, PWM_CHANNEL_8_PIN, PWM_CHANNEL_9_PIN, PWM_CHANNEL_10_PIN, PWM_CHANNEL_11_PIN};
    
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
    #if defined(__AVR__)
        PWM_Instance[0] = new AVR_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[1] = new AVR_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[2] = new AVR_PWM(PWM_CHANNEL_2_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[3] = new AVR_PWM(PWM_CHANNEL_3_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[4] = new AVR_PWM(PWM_CHANNEL_4_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[5] = new AVR_PWM(PWM_CHANNEL_5_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[6] = new AVR_PWM(PWM_CHANNEL_6_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[7] = new AVR_PWM(PWM_CHANNEL_7_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[8] = new AVR_PWM(PWM_CHANNEL_8_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[9] = new AVR_PWM(PWM_CHANNEL_9_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[10] = new AVR_PWM(PWM_CHANNEL_10_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[11] = new AVR_PWM(PWM_CHANNEL_11_PIN, PWM_DEFAULT_FREQ, 0);
    #else
        PWM_Instance[0] = new SAMDUE_PWM(PWM_CHANNEL_0_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[1] = new SAMDUE_PWM(PWM_CHANNEL_1_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[2] = new SAMDUE_PWM(PWM_CHANNEL_2_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[3] = new SAMDUE_PWM(PWM_CHANNEL_3_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[4] = new SAMDUE_PWM(PWM_CHANNEL_4_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[5] = new SAMDUE_PWM(PWM_CHANNEL_5_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[6] = new SAMDUE_PWM(PWM_CHANNEL_6_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[7] = new SAMDUE_PWM(PWM_CHANNEL_7_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[8] = new SAMDUE_PWM(PWM_CHANNEL_8_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[9] = new SAMDUE_PWM(PWM_CHANNEL_9_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[10] = new SAMDUE_PWM(PWM_CHANNEL_10_PIN, PWM_DEFAULT_FREQ, 0);
        PWM_Instance[11] = new SAMDUE_PWM(PWM_CHANNEL_11_PIN, PWM_DEFAULT_FREQ, 0);
    #endif
}

uint8_t set_hardware_pwm(uint8_t ch, float freq, float duty)
{
    if (pwm_initialized == false)
    {
        init_pwm();
        pwm_initialized = true;
    }

    const uint8_t pins[] = {PWM_CHANNEL_0_PIN, PWM_CHANNEL_1_PIN, PWM_CHANNEL_2_PIN, PWM_CHANNEL_3_PIN, PWM_CHANNEL_4_PIN, PWM_CHANNEL_5_PIN,
                            PWM_CHANNEL_6_PIN, PWM_CHANNEL_7_PIN, PWM_CHANNEL_8_PIN, PWM_CHANNEL_9_PIN, PWM_CHANNEL_10_PIN, PWM_CHANNEL_11_PIN};

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
