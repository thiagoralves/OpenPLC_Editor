#include <stdlib.h>
extern "C" {
#include "openplc.h"
}
#include "Arduino.h"
#include "../examples/Baremetal/defines.h"

#include <SPI.h>
#include <Ethernet.h>
#include "RP2040_PWM.h"

//Sketch defines
#define ADC_CS 9
#define DIO_CS 3
#define ADC_SPI SPI1
#define DIO_SPI SPI1
#define SD_SPI SPI
#define SD_CS SDCARD_SS_PIN
#define WIZNET_CS 17
#define WIZNET_RST 21

// SPI Settings
SPISettings adc_spi_settings(500000, MSBFIRST, SPI_MODE2); //CPOL=1, CPHA=0
SPISettings dio_spi_settings(1000000, MSBFIRST, SPI_MODE3); //CPOL=1, CPHA=1

// Shift register driven outputs
const uint8_t pwm_led_bit_1 = 0;
const uint8_t pwm_led_bit_2 = 1;
const uint8_t pwm_led_bit_3 = 2;
const uint8_t pwm_led_bit_4 = 3;
const uint8_t pwm_enable_bit = 4;
const uint8_t relay_enable_bit = 5;
const uint8_t rs485_enable_bit = 6;
const uint8_t wiz_reset_bit = 7;

// Shift register buffers
uint8_t sdo[2];
uint8_t sdi[2];

// PWM settings
RP2040_PWM *PWM[4]; 
#define PWM_1_2_FREQ 20000.0f
#define PWM_3_4_FREQ 50000.0f
#define ENC_A 2
#define ENC_B 15
#define ENC_Z 28
#define PWM1_PIN  6
#define PWM2_PIN  7 
#define PWM3_PIN  27
#define PWM4_PIN  26
extern "C" uint8_t set_hardware_pwm(uint8_t, float, float); //this call is required for the C-based PWM block on the Editor

//ADC Settings
#define BIPOLAR_10V 0x00
#define UNIPOLAR_10V 0x05
#define BIPOLAR_5V 0x01
#define UNIPOLAR_5V 0x06
uint8_t current_ch_range[4] = {BIPOLAR_10V};


//OpenPLC HAL for Project Jaguar

/******************PINOUT CONFIGURATION***********************
Digital In:  2, 3, 4, 5, 6, 7               (%IX0.0 - %IX0.5)
Digital Out: 8, 9, 10, 11, 12, 13           (%QX0.0 - %QX0.5)
Analog In: A1, A2, A3                       (%IW0 - %IW2)
Analog Out: 14                              (%QW0 - %QW0)
**************************************************************/

//Create the I/O pin masks
int8_t pinMask_DIN[] = {PINMASK_DIN};
int8_t pinMask_AIN[] = {PINMASK_AIN}; //Apparently Arduino mbedOS crashes when we use A4 onward. They need to fix this...
int8_t pinMask_DOUT[] = {PINMASK_DOUT};
int8_t pinMask_AOUT[] = {PINMASK_AOUT};

#define NUM_JAGUAR_RELAY_OUTPUTS    8
#define NUM_JAGUAR_DIGITAL_INPUTS   12
#define NUM_JAGUAR_ANALOG_INPUTS    4

#define bitRead(value, bit) (((value) >> (bit)) & 0x01)
#define bitWrite(value, bit, bitvalue) (bitvalue ? bitSet(value, bit) : bitClear(value, bit))


void Adc_RangeSelReg(unsigned char ainChNum, unsigned char voltRange)
{   
    if (ainChNum > 3)
    {
        return; 
    }

    current_ch_range[ainChNum] = voltRange;
    // uint8_t spiMsb = 0x0B + 2 * ainChNum;

    uint8_t spiMsb = ((0x05 + ainChNum) << 1) | 0x01;
    uint8_t spiLsb = voltRange;

    ADC_SPI.beginTransaction(adc_spi_settings);
    digitalWrite(ADC_CS, 0); // ADC chip select low
    ADC_SPI.transfer(spiMsb);
    ADC_SPI.transfer(spiLsb);
    ADC_SPI.transfer(0xFF); // need 24 SCLKs
    delayMicroseconds(5);
    digitalWrite(ADC_CS, 1); // ADC chip select high
}

// AD8688 init
void ADC_init()
{
    Adc_RangeSelReg(0, BIPOLAR_10V);
    Adc_RangeSelReg(1, UNIPOLAR_10V);
    Adc_RangeSelReg(2, BIPOLAR_5V);
    Adc_RangeSelReg(3, UNIPOLAR_5V);
}

void ADC_Write_CmdReg(uint8_t spiMsb)
{
    const uint8_t send_zero = 0x00;

    ADC_SPI.beginTransaction(adc_spi_settings);
    digitalWrite(ADC_CS, 0); // ADC chip select low
    ADC_SPI.transfer(spiMsb);
    ADC_SPI.transfer(send_zero);
    delayMicroseconds(5);
    digitalWrite(ADC_CS, 1); // ADC chip select high
}

void update_spi_io()
{
    DIO_SPI.beginTransaction(dio_spi_settings);
    digitalWrite(DIO_CS, LOW);
    for (unsigned int i = 0; i < sizeof(sdi); i++) 
    {
        sdi[i] = DIO_SPI.transfer(sdo[i]);
    }
    digitalWrite(DIO_CS, HIGH);
    DIO_SPI.endTransaction();
}

void write_relay_bits(uint8_t bits)
{
    sdo[1] = ~bits;
    update_spi_io();
}

uint16_t read_di_bits()
{
    uint16_t val = 0;

    update_spi_io();

    // Input order is incorrect on board, so swap data here
    val |= (~sdi[0]) & 0xF; // First 4 channels
    val |= (~sdi[1] << 4) & 0xFF0; // Next 8 channels

    return val;
}

// Returns 16 bit counts based on reading, channel is 0 indexed
uint16_t ADC_read_channel(uint8_t ch)
{
    // Select ADC channel
    if(ch > 3)
        return 0;

    ADC_Write_CmdReg(0xC0 + 4*ch);

    // Get ADC reading
    const uint8_t send_zero = 0x00;
    const uint8_t send_dummy = 0xFF;
    uint8_t msb, lsb; 

    ADC_SPI.beginTransaction(adc_spi_settings);
    digitalWrite(ADC_CS, 0); // ADC chip select low 
    ADC_SPI.transfer(send_zero);
    ADC_SPI.transfer(send_zero);
    msb = ADC_SPI.transfer(send_dummy);
    lsb = ADC_SPI.transfer(send_dummy); // store off in conversion array
    ADC_SPI.transfer(send_dummy);
    delayMicroseconds(5);
    digitalWrite(ADC_CS, 1); // ADC chip select high
    
    return (msb << 8) | lsb;
}

void write_pwm_led(uint8_t ch, bool state)
{
    if(!state)
    { // LEDs on == low
        sdo[0] |= 1 << (ch - 1);
    }
    else
    {
        sdo[0]  &= ~(1 << (ch - 1));
    }
    update_spi_io();
}

uint8_t set_hardware_pwm(uint8_t ch, float freq, float duty)
{
    const uint8_t pins[] = {PWM1_PIN, PWM2_PIN, PWM3_PIN, PWM4_PIN};

    //Serial.print("ch: ");
    //Serial.println(ch);
    //Serial.print("freq: ");
    //Serial.println(freq);
    //Serial.print("duty: ");
    //Serial.println(duty);

    if (ch > 3)
    {
        return 0;
    }

    if (PWM[ch]->setPWM(pins[ch], freq, duty))
    {
        write_pwm_led(ch, duty != 0); // Set status LED state
        return 1;
    }

    return 0;
}

void hardwareInit()
{
    //Serial.begin(115200);
    //delay(2000);
    //Serial.println("Initializing hardware...");

    Ethernet.init(WIZNET_CS);

    //Serial.println("Started Wiznet");

    pinMode(5, INPUT); //What is this exactly?

    pinMode(WIZNET_CS, OUTPUT);
    pinMode(WIZNET_RST, OUTPUT);
    pinMode(SD_CS, OUTPUT);
    pinMode(ADC_CS, OUTPUT);
    pinMode(DIO_CS, OUTPUT);
    digitalWrite(ADC_CS, HIGH);
    digitalWrite(DIO_CS, HIGH);
    digitalWrite(WIZNET_CS, HIGH);
    digitalWrite(SD_CS, HIGH);

    //Serial.println("Started other things");

    digitalWrite(WIZNET_RST, LOW); //Do we really need to reset Wiznet?
    delay(100);
    digitalWrite(WIZNET_RST, HIGH);
    delay(100);

    SPI.begin();
    SPI1.begin();

    pinMode(12, OUTPUT); //What are these for?
    pinMode(13, INPUT);

    //Enable relays and PWM
    sdo[0] |= 1 << relay_enable_bit;
    update_spi_io();
    sdo[0]  &= ~(1 << pwm_enable_bit);
    update_spi_io();
    PWM[0] = new RP2040_PWM(PWM1_PIN, PWM_1_2_FREQ, 0); 
    PWM[1] = new RP2040_PWM(PWM2_PIN, PWM_1_2_FREQ, 0); // 7 is on the same PWM block and must use same frequency
    PWM[2] = new RP2040_PWM(PWM3_PIN, PWM_3_4_FREQ, 0); 
    PWM[3] = new RP2040_PWM(PWM4_PIN, PWM_3_4_FREQ, 0); // 26 is on the same PWM block and must use same frequency

    pinMode(PWM1_PIN, OUTPUT);
    pinMode(PWM2_PIN, OUTPUT);
    pinMode(PWM3_PIN, OUTPUT);
    pinMode(PWM4_PIN, OUTPUT);
    pinMode(ENC_A, INPUT);
    pinMode(ENC_B, INPUT);
    pinMode(ENC_Z, INPUT);

    //Disable all relay outputs
    write_relay_bits(0);

    //Serial.println("Finished initialization");

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
    //Serial.println("Running input buffers");
    uint16_t digital_inputs = read_di_bits();

    for (int i = 0; i < NUM_JAGUAR_DIGITAL_INPUTS; i++)
    {
        if (bool_input[i/8][i%8] != NULL) 
            *bool_input[i/8][i%8] = bitRead(digital_inputs, i);
    }

    for (int i = 0; i < NUM_JAGUAR_ANALOG_INPUTS; i++)
    {
        if (int_input[i] != NULL)
        {
            *int_input[i] = ADC_read_channel(i);
        }
    }
}

void updateOutputBuffers()
{
    //Serial.println("Running output buffers");
    uint8_t relay_outputs = 0;
    for (int i = 0; i < NUM_JAGUAR_RELAY_OUTPUTS; i++)
    {
        if (bool_output[i/8][i%8] != NULL)
            bitWrite(relay_outputs, i, *bool_output[i/8][i%8]);
    }
    write_relay_bits(relay_outputs);

    //for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    //{
    //    if (int_output[i] != NULL) 
    //        analogWrite(pinMask_AOUT[i], (*int_output[i] / 256));
    //}
}
