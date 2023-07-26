#include <OneWire.h>
#include <DallasTemperature.h>

extern "C" void *init_ds18b20(uint8_t);
extern "C" void request_ds18b20_temperatures(void *);
extern "C" float read_ds18b20(void *, uint8_t);

void *init_ds18b20(uint8_t pin)
{
    //Disable pin
    //disabled_pins[disabled_pins[0]] = pin;
    //if (disabled_pins[0] < 10) disabled_pins[0]++;
    
    for (int i = 0; i < NUM_DISCRETE_INPUT; i++)
    {
        if (pinMask_DIN[i] == pin)
            pinMask_DIN[i] = 255;
    }
    for (int i = 0; i < NUM_ANALOG_INPUT; i++)
    {
        if (pinMask_AIN[i] == pin)
            pinMask_AIN[i] = 255;
    }
    for (int i = 0; i < NUM_DISCRETE_OUTPUT; i++)
    {
        if (pinMask_DOUT[i] == pin)
            pinMask_DOUT[i] = 255;
    }
    for (int i = 0; i < NUM_ANALOG_OUTPUT; i++)
    {
        if (pinMask_AOUT[i] == pin)
            pinMask_AOUT[i] = 255;
    }
    
    OneWire *oneWire;
    DallasTemperature *sensors;
    oneWire = new OneWire(pin);
    sensors = new DallasTemperature(oneWire);
    sensors->begin();
    return sensors;
}
void request_ds18b20_temperatures(void *class_pointer)
{
    DallasTemperature *sensors = (DallasTemperature *)class_pointer;
    sensors->requestTemperatures();
}
float read_ds18b20(void *class_pointer, uint8_t index)
{
    DallasTemperature *sensors = (DallasTemperature *)class_pointer;
    return sensors->getTempCByIndex(index);
}