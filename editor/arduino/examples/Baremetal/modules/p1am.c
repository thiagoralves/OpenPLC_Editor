#include <P1AM.h>
extern "C" uint8_t p1am_init();
extern "C" void p1am_writeDiscrete(uint32_t, uint8_t, uint8_t);
extern "C" uint32_t p1am_readDiscrete(uint8_t, uint8_t);
extern "C" uint16_t p1am_readAnalog(uint8_t, uint8_t);

uint8_t modules_initialized = 0;

uint8_t p1am_init()
{
    if (modules_initialized == 0)
    {
        modules_initialized = P1.init();
        //P1.init takes a while, so we need to reset scan cycle timer
        timer_ms = millis() + scan_cycle;
    }
    
    return modules_initialized;
}

void p1am_writeDiscrete(uint32_t data, uint8_t slot, uint8_t channel)
{
    P1.writeDiscrete(data, slot, channel);
}

uint32_t p1am_readDiscrete(uint8_t slot, uint8_t channel)
{
    return P1.readDiscrete(slot, channel);
}

uint16_t p1am_readAnalog(uint8_t slot, uint8_t channel)
{
    return (uint16_t)P1.readAnalog(slot, channel);
}