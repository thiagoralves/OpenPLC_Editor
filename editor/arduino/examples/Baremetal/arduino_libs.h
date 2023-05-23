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

#ifdef USE_MQTT_BLOCKS
    /*
    #include <ArduinoMqttClient.h>
    
    WiFiClient wifiClient;
    MqttClient mqttClient(wifiClient);

    extern "C" uint8_t connect_mqtt(char *broker, uint16_t port);
    extern "C" uint8_t mqtt_send(char *topic, char *message);

    uint8_t connect_mqtt(char *broker, uint16_t port)
    {
        return mqttClient.connect(broker, port);
    }

    uint8_t mqtt_send(char *topic, char *message)
    {
        mqttClient.beginMessage(topic);
        mqttClient.print(message);
        mqttClient.endMessage();

        return 1;
    }
    */

    #include <PubSubClient.h>
    //Reference: https://www.hivemq.com/blog/mqtt-client-library-encyclopedia-arduino-pubsubclient/

    #ifdef MBTCP_ETHERNET
        EthernetClient wifiClient;
    #else
        WiFiClient wifiClient;
    #endif
    PubSubClient mqttClient(wifiClient);

    extern "C" uint8_t connect_mqtt(char *broker, uint16_t port);
    extern "C" uint8_t mqtt_send(char *topic, char *message);

    uint8_t connect_mqtt(char *broker, uint16_t port)
    {
        mqttClient.setServer(broker, port);
        return mqttClient.connect("openplc-client");
    }

    uint8_t mqtt_send(char *topic, char *message)
    {
        /*
        mqttClient.beginMessage(topic);
        mqttClient.print(message);
        mqttClient.endMessage();

        return 1;
        */

        return mqttClient.publish(topic, message);
    }

#endif

//#ifdef USE_SM_BLOCKS
#include <stdlib.h>
#include "Arduino.h"
#include "Wire.h"

#define OK 0
#define ERROR -1

extern "C" int relay8Init(int);
extern "C" int relays8Set(uint8_t, uint8_t);

int i2cMemRead(uint8_t hwAddr, uint8_t memAddr, uint8_t* buff, uint8_t size)
{
	if(buff == NULL)
	{
		return ERROR;
	}
	Wire.begin();
	Wire.beginTransmission(hwAddr);
	Wire.write(memAddr);
	if (Wire.endTransmission() != 0)
	{
		return ERROR;
	}

		Wire.requestFrom(hwAddr, (uint8_t)size);
		while (Wire.available())
		{
			*buff = Wire.read();
			buff++;
		}

	return OK;
}

int i2cMemWrite(uint8_t hwAddr, uint8_t memAddr, uint8_t* buff, uint8_t size)
{
	uint8_t byteCount = 0;

	if(buff == NULL)
	{
		return ERROR;
	}
	Wire.begin();
	Wire.beginTransmission(hwAddr);
	Wire.write(memAddr);
	while(byteCount < size)
	{
		Wire.write(*buff);
		buff ++;
		byteCount++;
	}
	return Wire.endTransmission();
}

#define RELAY8_HW_I2C_BASE_ADD 0x20
#define RELAY8_INPORT_REG_ADD	0x00
#define RELAY8_OUTPORT_REG_ADD	0x01
#define RELAY8_POLINV_REG_ADD	0x02
#define RELAY8_CFG_REG_ADD		0x03
#define RELAY8_REG_COUNT 0x04
#define STACK_LEVELS 8
uint8_t relay8_presence = 0;

const uint8_t relay8MaskRemap[8] = {0x01, 0x04, 0x40, 0x10, 0x20, 0x80, 0x08,
	0x02};

uint8_t relay8ToIO(uint8_t relay)
{
	uint8_t i;
	uint8_t val = 0;
	for (i = 0; i < 8; i++)
	{
		if ( (relay & (1 << i)) != 0)
			val += relay8MaskRemap[i];
	}
	return val;
}

int relay8CardCheck(int stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		return ERROR;
	}
	add = (stack + RELAY8_HW_I2C_BASE_ADD) ^ 0x07;
	return add;
}

int relay8Init(int stack)
{
	int dev = -1;
	uint8_t add = 0;
	uint8_t buff[2];

	dev = relay8CardCheck(stack);
	if (dev <= 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, RELAY8_CFG_REG_ADD, buff, 1))
	{
		return ERROR;
	}
	if (OK == i2cMemRead(dev, RELAY8_REG_COUNT, buff, 1)) //16 bits I/O expander found
	{
		return ERROR;
	}
	if (buff[0] != 0) //non initialized I/O Expander
	{
		// make all I/O pins output
		buff[0] = 0;
		if (OK > i2cMemWrite(dev, RELAY8_CFG_REG_ADD, buff, 1))
		{
			return ERROR;
		}
		// put all pins in 0-logic state
		buff[0] = 0;
		if (OK > i2cMemWrite(dev, RELAY8_OUTPORT_REG_ADD, buff, 1))
		{
			return ERROR;
		}
	}
	relay8_presence |= 1 << stack;
	return OK;
}

int relays8Set(uint8_t stack, uint8_t val)
{
	uint8_t buff[2];
	int dev = -1;
	static uint8_t relaysOldVal[STACK_LEVELS] = {0, 0, 0, 0, 0, 0, 0, 0};

	if (stack >= 8)
	{
		return ERROR;
	}

	if (relaysOldVal[stack] == val)
	{
		return OK;
	}
	dev = relay8CardCheck(stack);
	if (dev <= 0)
	{
		return ERROR;
	}

	buff[0] = relay8ToIO(val);

	if (OK != i2cMemWrite(dev, RELAY8_OUTPORT_REG_ADD, buff, 1))
	{
		return ERROR;
	}
	relaysOldVal[stack] = val;
	return OK;
}

// --------------------- 16RELAYS --------------------------------------

extern "C" int relay16Init(int);
extern "C" int relay16Set(uint8_t, uint16_t);

#define RELAY16_CHANNELS 16
#define RELAY16_HW_I2C_BASE_ADD	0x20
#define RELAY16_INPORT_REG_ADD	0x00
#define RELAY16_OUTPORT_REG_ADD	0x02
#define RELAY16_POLINV_REG_ADD	0x04
#define RELAY16_CFG_REG_ADD		0x06

#define RELAY16_X_PLC_OFFSET 64
#define RELAY16_STACK_MIN 0
#define RELAY16_STACK_LEVELS 4

const uint16_t relayMaskRemap16[RELAY16_CHANNELS] = {0x8000, 0x4000, 0x2000,
	0x1000, 0x800, 0x400, 0x200, 0x100, 0x80, 0x40, 0x20, 0x10, 0x8, 0x4, 0x2,
	0x1};

uint16_t relayToIO16(uint16_t relay)
{
	uint8_t i;
	uint16_t val = 0;
	for (i = 0; i < 16; i++)
	{
		if ( (relay & (1 << i)) != 0)
			val += relayMaskRemap16[i];
	}
	return val;
}

uint16_t IOToRelay16(uint16_t io)
{
	uint8_t i;
	uint16_t val = 0;
	for (i = 0; i < 16; i++)
	{
		if ( (io & relayMaskRemap16[i]) != 0)
		{
			val += 1 << i;
		}
	}
	return val;
}

int relay16CardCheck(uint8_t stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		return ERROR;
	}
	add = (stack + RELAY16_HW_I2C_BASE_ADD) ^ 0x07;
	return add;
}

int relay16Init(int stack)
{
	int dev = -1;
	uint8_t add = 0;
	uint8_t buff[2];
	uint16_t val = 0;

	dev = relay16CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, RELAY16_CFG_REG_ADD, buff, 2)) // 16 bits IO expander found
	{
		return ERROR;
	}
	memcpy(&val, buff, 2);
	if (val != 0) //non initialized I/O Expander
	{
		// make all I/O pins output
		val = 0;
		memcpy(buff, &val, 2);
		if (OK > i2cMemWrite(dev, RELAY16_CFG_REG_ADD, buff, 2))
		{
			return ERROR;
		}
		// put all pins in 0-logic state
		if (OK > i2cMemWrite(dev, RELAY16_OUTPORT_REG_ADD, buff, 2))
		{
			return ERROR;
		}
	}
	return OK;
}

int relay16Set(uint8_t stack, uint16_t val)
{
	static uint16_t relaysOldVal[STACK_LEVELS] = {0, 0, 0, 0, 0, 0, 0, 0};
	uint8_t buff[2];
	uint16_t rVal = 0;
	int dev = -1;

	if (stack >= STACK_LEVELS)
	{
		return ERROR;
	}
	if (relaysOldVal[stack] == val)
	{
		return OK;
	}
	dev = relay16CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	rVal = relayToIO16(val);
	memcpy(buff, &rVal, 2);

	if (OK == i2cMemWrite(dev, RELAY16_OUTPORT_REG_ADD, buff, 2))
	{
		relaysOldVal[stack] = val;
		return OK;
	}
	return ERROR;
}


//-----------------------------------------------------------------------------
// Eight High Voltage Digital Inputs 8-Layer Stackable HAT for Raspberry Pi
//-----------------------------------------------------------------------------

extern "C" int digIn8Get(uint8_t, uint8_t*);
extern "C" int digIn8Init(int );

#define DIG_IN8_CHANNELS 8
#define DIG_IN8_HW_I2C_BASE_ADD	0x20
#define DIG_IN8_INPORT_REG_ADD	0x00
#define DIG_IN8_OUTPORT_REG_ADD	0x01
#define DIG_IN8_POLINV_REG_ADD	0x02
#define DIG_IN8_CFG_REG_ADD		0x03

const uint8_t inputsMaskRemap8[DIG_IN8_CHANNELS] ={0x08, 0x04, 0x02, 0x01, 0x10, 0x20, 0x40, 0x80};

int digIn8CardCheck(uint8_t stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		//printf("Invalid stack level [0..7]!");
		return ERROR;
	}
	add = (stack + DIG_IN8_HW_I2C_BASE_ADD) ^ 0x07;
	return add;
}

int digIn8Init(int stack)
{
	int dev = -1;
	uint8_t add = 0;
	uint8_t buff[2];
	uint8_t val = 0;

	dev = digIn8CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, DIG_IN8_CFG_REG_ADD, buff, 1))
	{
		return ERROR;
	}
	
	if (buff[0] != 0xff) //non initialized I/O Expander
	{
		// make all I/O pins inputs
		buff[0] = 0xff;
		if (OK != i2cMemWrite(dev, RELAY8_CFG_REG_ADD, buff, 1))
		{
			return ERROR;
		}
	}
	return OK;
}

int digIn8Get(uint8_t stack, uint8_t *val)
{
	int dev = -1;
	uint8_t buff[2];
	uint8_t raw = 0;
	uint8_t i = 0;

	if (stack >= STACK_LEVELS || val == NULL)
	{
		return ERROR;
	}
	dev = digIn8CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (OK != i2cMemRead(dev, DIG_IN8_INPORT_REG_ADD, buff, 1))
	{
		return ERROR;
	}
	raw = 0xff & (~buff[0]);
	*val = 0;
	for (i = 0; i < 8; i++)
	{
		if (raw & inputsMaskRemap8[i])
		{
			*val += 1 << i;
		}
	}
	return OK;
}



//------------------------------------------------------------------------------
// Sixteen Digital Inputs 8-Layer Stackable HAT for Raspberry Pi
//------------------------------------------------------------------------------

extern "C" int digIn16Get(uint8_t, uint16_t*);
extern "C" int digIn16Init(int );

#define DIG_IN16_CHANNELS 16
#define DIG_IN16_HW_I2C_BASE_ADD	0x20
#define DIG_IN16_INPORT_REG_ADD	0x00
#define DIG_IN16_OUTPORT_REG_ADD	0x02
#define DIG_IN16_POLINV_REG_ADD	0x04
#define DIG_IN16_CFG_REG_ADD		0x06

#define DIG_IN16_X_PLC_OFFSET 0

#define DIG_IN16_STACK_MIN 4
#define DIG_IN16_STACK_LEVELS 4

const uint16_t inputsMaskRemap16[DIG_IN16_CHANNELS] = {0x8000, 0x4000, 0x2000,
	0x1000, 0x800, 0x400, 0x200, 0x100, 0x80, 0x40, 0x20, 0x10, 0x8, 0x4, 0x2,
	0x1};

int digIn16CardCheck(uint8_t stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		//printf("Invalid stack level [0..7]!");
		return ERROR;
	}
	add = (stack + DIG_IN16_HW_I2C_BASE_ADD) ^ 0x07;
	return add;
}

int digIn16Init(int stack)
{
	int dev = -1;
	uint8_t add = 0;
	uint8_t buff[2];
	uint16_t val = 0;

	dev = digIn16CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, DIG_IN16_CFG_REG_ADD, buff, 2))
	{
		return ERROR;
	}
	memcpy(&val, buff, 2);
	if (val != 0xffff) //non initialized I/O Expander
	{
		// make all I/O pins inputs
		val = 0xffff;
		memcpy(buff, &val, 2);
		if (OK != i2cMemWrite(dev, RELAY16_CFG_REG_ADD, buff, 2))
		{
			return ERROR;
		}
	}
	return OK;
}

int digIn16Get(uint8_t stack, uint16_t *val)
{
	int dev = -1;
	uint8_t buff[2];
	uint16_t raw = 0;
	uint8_t i = 0;

	if (stack >= STACK_LEVELS || val == NULL)
	{
		return ERROR;
	}
	dev = digIn16CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (OK != i2cMemRead(dev, DIG_IN16_INPORT_REG_ADD, buff, 2))
	{
		return ERROR;
	}
	raw = (0xff & (~buff[0])) + ( (0xff & (~buff[1])) << 8);
	*val = 0;
	for (i = 0; i < 16; i++)
	{
		if (raw & inputsMaskRemap16[i])
		{
			*val += 1 << i;
		}
	}
	return OK;
}


//------------------------------------------------------------------------------
// Four Relays four HV Inputs 8-Layer Stackable HAT for Raspberry Pi
//-------------------------------------------------------------------------------

extern "C" int r4i4SetRelays(uint8_t, uint8_t);
extern "C" int r4i4GetOptoInputs(uint8_t, uint8_t*);
extern "C" int r4i4GetACInputs(uint8_t, uint8_t*);
extern "C" int r4i4GetButton(uint8_t, uint8_t*);
extern "C" int r4i4GetPWMInFill(uint8_t, uint8_t, uint16_t*);
extern "C" int r4i4GetPWMInFreq(uint8_t, uint8_t, uint16_t*);

#define I2C_REL4_IN4_ADDRESS_BASE 0x0e

#define R4I4_I2C_MEM_RELAY_VAL  0//reserved 4 bits for open-drain and 4 bits for leds
#define R4I4_I2C_MEM_DIG_IN 3
#define R4I4_I2C_MEM_AC_IN 4
#define R4I4_I2C_MEM_PWM_IN_FILL 45
#define R4I4_I2C_MEM_IN_FREQENCY  53
#define R4I4_I2C_MEM_BUTTON 71
#define R4I4_I2C_MEM_REVISION_MAJOR_ADD 120

#define R4I4_CHANNEL_NR_MIN		1

#define R4I4_OPTO_CH_NR_MAX		4
#define R4I4_REL_CH_NR_MAX			4

#define R4I4_REL_PLC_OFFSET_BITS 0
#define R4I4_OPTO_IN_PLC_OFFSET_BITS 0
#define R4I4_AC_IN_PLC_OFFSET_BITS 4
#define R4I4_PWM_IN_FILL_PLC_OFFSET 0
#define R4I4_PWM_IN_FREQ_PLC_OFFSET 4
#define R4I4_BUTTON_PLC_OFFSET 9

int r4i4CardCheck(uint8_t stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		return ERROR;
	}
	add = stack + I2C_REL4_IN4_ADDRESS_BASE;
	return add;
}

int r4i4Init(int stack)
{
	int dev = -1;
	uint8_t buff[2];
	uint16_t val = 0;

	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, R4I4_I2C_MEM_REVISION_MAJOR_ADD, buff, 2))
	{
		return ERROR;
	}

	return OK;
}

int r4i4SetRelays(uint8_t stack, uint8_t value)
{
	static uint8_t prevRelays[STACK_LEVELS] = {0, 0, 0, 0, 0, 0, 0, 0};
	int dev = -1;

	if (stack >= STACK_LEVELS)
	{
		return ERROR;
	}
	if (prevRelays[stack] == value)
	{
		return OK; // prevent usless transactions on I2C bus
	}
	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemWrite(dev, R4I4_I2C_MEM_RELAY_VAL, &value, 1))
	{
		return ERROR;
	}
	prevRelays[stack] = value;
	return OK;
}

int r4i4GetOptoInputs(uint8_t stack, uint8_t *val)
{
	int dev = -1;

	if (val == NULL)
	{
		return ERROR;
	}
	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	return i2cMemRead(dev, R4I4_I2C_MEM_DIG_IN, val, 1);
}

int r4i4GetACInputs(uint8_t stack, uint8_t *val)
{
	int dev = -1;

	if (val == NULL)
	{
		return ERROR;
	}
	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	return i2cMemRead(dev, R4I4_I2C_MEM_AC_IN, val, 1);
}

int r4i4GetButton(uint8_t stack, uint8_t *button)
{
	int dev = -1;
	uint8_t val;

	if (button == NULL)
	{
		return ERROR;
	}
	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	if (OK != i2cMemRead(dev, R4I4_I2C_MEM_BUTTON, &val, 1))
	{
		return ERROR;
	}
	*button = 0x01 & val;
	return OK;
}

int r4i4GetPWMInFill(uint8_t stack, uint8_t channel, uint16_t *value)
{
	int dev = -1;
	uint8_t buff[2];

	if (channel >= R4I4_OPTO_CH_NR_MAX || value == NULL)
	{
		return ERROR;
	}

	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	if (OK != i2cMemRead(dev, R4I4_I2C_MEM_PWM_IN_FILL + 2 * channel, buff, 2))
	{
		return ERROR;
	}
	memcpy(value, buff, 2);
	return OK;
}

int r4i4GetPWMInFreq(uint8_t stack, uint8_t channel, uint16_t *value)
{
	int dev = -1;
	uint8_t buff[2];

	if (channel >= R4I4_OPTO_CH_NR_MAX || value == NULL)
	{
		return ERROR;
	}

	dev = r4i4CardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	if (OK != i2cMemRead(dev, R4I4_I2C_MEM_IN_FREQENCY + 2 * channel, buff, 2))
	{
		return ERROR;
	}
	memcpy(value, buff, 2);
	return OK;
}

//------------------------------------------------------------------------------
// RTD Data Acquisition 8-Layer Stackable HAT for Raspberry Pi
//------------------------------------------------------------------------------

extern "C" int rtdGetTemp(uint8_t, uint8_t, float*);

#define I2C_RTD_ADDRESS_BASE 0x40

#define RTD_I2C_VAL1_ADD  0//reserved 4 bits for open-drain and 4 bits for leds
#define RTD_I2C_MEM_REVISION_MAJOR_ADD 57

#define RTD_CHANNEL_NR_MIN		1
#define RTD_CH_NR_MAX		8

#define RTD_TEMP_SIZE 4

#define RTD_TEMP_PLC_SCALE_FACTOR ((float)10)
#define RTD_TEMP_PLC_OFFSET ((float)200)

#define RTD_TEMP_IW_ADDR_OFFSET  0
#define RTD_IW_PER_CARD 12

int rtdCardCheck(uint8_t stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		return ERROR;
	}
	add = stack + I2C_RTD_ADDRESS_BASE;
	return add;
}

int rtdInit(int stack)
{
	int dev = -1;
	uint8_t add = 0;
	uint8_t buff[2];
	uint16_t val = 0;

	dev = rtdCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, RTD_I2C_MEM_REVISION_MAJOR_ADD, buff, 2))
	{
		return ERROR;
	}

	return OK;
}

int rtdGetTemp(uint8_t stack, uint8_t channel, float *value)
{
	int dev = -1;
	uint8_t buff[4];

	if (channel >= RTD_CH_NR_MAX || value == NULL)
	{
		return ERROR;
	}

	dev = rtdCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	if (OK != i2cMemRead(dev, RTD_I2C_VAL1_ADD + 4 * channel, buff, 4))
	{
		return ERROR;
	}
	memcpy(value, buff, 4);
	return OK;
}


//------------------------------------------------------------------------------
// Industrial Automation 8-Layer Stackable HAT for Raspberry Pi
//------------------------------------------------------------------------------

extern "C" int indSetLeds(uint8_t, uint8_t);
extern "C" int indGetOptoInputs(uint8_t, uint8_t*);
extern "C" int indGet0_10Vin(uint8_t, uint8_t, float*);
extern "C" int indGet4_20mAin(uint8_t, uint8_t, float*);
extern "C" int indGet1WbTemp(uint8_t, uint8_t, float*);
extern "C" int indSet0_10Vout(uint8_t, uint8_t, float);
extern "C" int indSet4_20mAout(uint8_t, uint8_t, float);
extern "C" int indSetPWMout(uint8_t, uint8_t, float);

#define I2C_IND_ADDRESS_BASE 0x50

#define IND_I2C_MEM_RELAY_VAL 0//reserved 4 bits for open-drain and 4 bits for leds
#define IND_I2C_MEM_OPTO_IN_VAL 3
#define IND_I2C_MEM_U0_10_OUT_VAL 4
#define IND_I2C_MEM_I4_20_OUT_VAL 12
#define IND_I2C_MEM_OD_PWM 20
#define IND_I2C_MEM_U0_10_IN_VAL 28
#define IND_I2C_MEM_U_PM_10_IN_VAL 36
#define IND_I2C_MEM_I4_20_IN_VAL 44
#define IND_I2C_MEM_REVISION_MAJOR  0x78
#define IND_I2C_MEM_1WB_START_SEARCH 173
#define IND_I2C_MEM_1WB_T1 174

#define CHANNEL_NR_MIN		1

#define IND_OPTO_CH_NR_MAX		4
#define IND_OD_CH_NR_MAX			4
#define IND_I_OUT_CH_NR_MAX		4
#define IND_U_OUT_CH_NR_MAX		4
#define IND_U_IN_CH_NR_MAX		4
#define IND_I_IN_CH_NR_MAX		4
#define IND_LED_CH_NR_MAX 4
#define IND_OWB_CH_MAX 4 // (4/16) limit PLC variable alocation

#define IND_0_10V_RAW_MAX 10000
#define IND_4_20MA_RAW_MIN 4000
#define IND_4_20MA_RAW_MAX 20000
#define IND_OD_PWM_VAL_MAX	10000

#define IND_LED_PLC_OFFSET_BITS 0
#define IND_OPTO_IN_PLC_OFFSET_BITS 0
#define IND_U_IN_PLC_OFFSET 0
#define IND_I_IN_PLC_OFFSET 4
#define IND_T_PLC_OFFSET 8
#define IND_U_OUT_PLC_OFFSET 0
#define IND_I_OUT_PLC_OFFSET 4
#define IND_PWM_OUT_PLC_OFFSET 8

#define VOLT_TO_MILIVOLT ((float)1000)
#define MILI_TO_MICRO ((float)1000)
#define OWB_TEMP_SCALE ((float)100)
#define PWM_SCALE ((float)100)

int indCardCheck(uint8_t stack)
{
	uint8_t add = 0;

	if ( (stack < 0) || (stack > 7))
	{
		return ERROR;
	}
	add = stack + I2C_IND_ADDRESS_BASE;
	return add;
}

int indInit(int stack)
{
	int dev = -1;
	uint8_t add = 0;
	uint8_t buff[2];
	uint16_t val = 0;

	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (ERROR == i2cMemRead(dev, IND_I2C_MEM_REVISION_MAJOR, buff, 2))
	{
		return ERROR;
	}

	return OK;
}

int indSetLeds(uint8_t stack, uint8_t value)
{
	static uint8_t prevLeds[STACK_LEVELS] = {0, 0, 0, 0, 0, 0, 0, 0};
	int dev = -1;
	uint8_t buff[2];
	if (stack >= STACK_LEVELS)
	{
		return ERROR;
	}
	if (prevLeds[stack] == value)
	{
		return OK; // prevent usless transactions on I2C bus
	}
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	buff[0] = 0xf0 & (value << 4);
	if (ERROR == i2cMemWrite(dev, IND_I2C_MEM_RELAY_VAL, buff, 1))
	{
		return ERROR;
	}
	prevLeds[stack] = value;
	return OK;
}

int indGetOptoInputs(uint8_t stack, uint8_t *val)
{
	int dev = -1;

	if (val == NULL)
	{
		return ERROR;
	}
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	return i2cMemRead(dev, IND_I2C_MEM_OPTO_IN_VAL, val, 1);
}

int indGet0_10Vin(uint8_t stack, uint8_t channel, float *val)
{
	uint8_t buff[2];
	int dev = -1;
	uint16_t aux16 = 0;

	if (channel > IND_U_IN_CH_NR_MAX || NULL == val)
	{
		return ERROR;
	}
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (OK != i2cMemRead(dev, IND_I2C_MEM_U0_10_IN_VAL + 2 * channel, buff, 2))
	{
		return ERROR;
	}
	memcpy(&aux16, buff, 2);
	*val = (float)aux16 / VOLT_TO_MILIVOLT;
	return OK;
}

int indGet4_20mAin(uint8_t stack, uint8_t channel, float *val)
{
	uint8_t buff[2];
	int dev = -1;
    uint16_t aux16 = 0;

	if (channel > IND_I_IN_CH_NR_MAX || NULL == val)
	{
		return ERROR;
	}
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}

	if (OK != i2cMemRead(dev, IND_I2C_MEM_I4_20_IN_VAL + 2 * channel, buff, 2))
	{
		return ERROR;
	}
	memcpy(&aux16, buff, 2);
	*val = (float)aux16 / MILI_TO_MICRO;
	return OK;
}

int indGet1WbTemp(uint8_t stack, uint8_t channel, float *val)
{
	uint8_t buff[2];
	int dev = -1;
	int16_t aux16 = 0;

	if (channel > IND_OWB_CH_MAX || NULL == val)
	{
		return ERROR;
	}
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	if (OK != i2cMemRead(dev, IND_I2C_MEM_1WB_T1 + 2 * channel, buff, 2))
	{
		return ERROR;
	}
	memcpy(&aux16, buff, 2);
	*val = (float)aux16 / OWB_TEMP_SCALE;
	return OK;
}

int indSet0_10Vout(uint8_t stack, uint8_t channel, float val)
{
	//static uint16_t prevVout[IND_U_OUT_CH_NR_MAX] = {0, 0, 0, 0};
	uint8_t buff[2];
	int dev = -1;
	uint16_t aux16 = 0;

	if (channel > IND_U_OUT_CH_NR_MAX || val > IND_0_10V_RAW_MAX)
	{
		return ERROR;
	}
	aux16 = (uint16_t)(val * VOLT_TO_MILIVOLT);
	//if(aux16 == )
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	memcpy(buff, &aux16, 2);
	if (OK
		!= i2cMemWrite(dev, IND_I2C_MEM_U0_10_OUT_VAL + 2 * channel, buff, 2))
	{
		return ERROR;
	}

	return OK;
}

int indSet4_20mAout(uint8_t stack, uint8_t channel, float val)
{
	uint8_t buff[2];
	int dev = -1;
	uint16_t aux16 = 0;

	val *= MILI_TO_MICRO;
	if (channel > IND_I_OUT_CH_NR_MAX || val > IND_4_20MA_RAW_MAX
		|| val < IND_4_20MA_RAW_MIN)
	{
		return ERROR;
		//return ERROR;
	}
	aux16 = (uint16_t)val;
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	memcpy(buff, &aux16, 2);
	if (OK
		!= i2cMemWrite(dev, IND_I2C_MEM_I4_20_OUT_VAL + 2 * channel, buff, 2))
	{
		return ERROR;
	}

	return OK;
}

int indSetPWMout(uint8_t stack, uint8_t channel, float val)
{
	uint8_t buff[2];
	int dev = -1;
	uint16_t aux16 = 0;


	if (channel > IND_OD_CH_NR_MAX || val > 100 || val < 0)
	{
		return ERROR;
	}
	aux16 = (uint16_t)(val * PWM_SCALE);
	dev = indCardCheck(stack);
	if (dev < 0)
	{
		return ERROR;
	}
	memcpy(buff, &aux16, 2);
	if (OK != i2cMemWrite(dev, IND_I2C_MEM_OD_PWM + 2 * channel, buff, 2))
	{
		return ERROR;
	}

	return OK;
}
//#endif
