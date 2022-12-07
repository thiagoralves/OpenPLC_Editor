//disable pins
//uint8_t disabled_pins[11] = {1, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255}; //10 pins max. First array position is used as index
extern uint8_t pinMask_DIN[];
extern uint8_t pinMask_AIN[];
extern uint8_t pinMask_DOUT[];
extern uint8_t pinMask_AOUT[];

#ifdef USE_DS18B20_BLOCK
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
#endif

#ifdef USE_P1AM_BLOCKS
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
#endif

#ifdef USE_CLOUD_BLOCKS
    #include <ArduinoIoTCloud.h>
    #include <Arduino_ConnectionHandler.h>
    
    extern "C" void cloud_begin(char *, char *, char *);
    extern "C" void cloud_add_bool(char *, int *);
    extern "C" void cloud_add_int(char *, int *);
    extern "C" void cloud_add_float(char *, float *);
    extern "C" void cloud_update();
    
    bool first_update = true;
    
    WiFiConnectionHandler *ArduinoIoTPreferredConnection;
    
    void cloud_begin(char *thing_id, char *str_ssid, char *str_pass)
    {
        Serial.begin(9600);
        ArduinoIoTPreferredConnection = new WiFiConnectionHandler(str_ssid, str_pass);
        ArduinoCloud.setThingId(thing_id);
    }
    
    void cloud_update()
    {
        if (first_update)
        {
            first_update = false;
            ArduinoCloud.begin(*ArduinoIoTPreferredConnection);
        
            //Temporary
            setDebugMessageLevel(4);
            ArduinoCloud.printDebugInfo();
        }
        ArduinoCloud.update();
    }
    
    void cloud_add_bool(char *var_name, int *bool_var)
    {
        ArduinoCloud.addPropertyReal(*bool_var, String(var_name));
    }
    
    void cloud_add_int(char *var_name, int *int_var)
    {
        ArduinoCloud.addPropertyReal(*int_var, String(var_name));
    }
    
    void cloud_add_float(char *var_name, float *float_var)
    {
        ArduinoCloud.addPropertyReal(*float_var, String(var_name));
    }
    
#endif
