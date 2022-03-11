#include "Arduino_OpenPLC.h"
#include "defines.h"

#ifdef MODBUS_ENABLED
#include "Modbus.h"
#include "ModbusSerial.h"
#endif

unsigned long __tick = 0;

unsigned long scan_cycle;
unsigned long timer_ms = 0;

#include "arduino_libs.h"


#ifdef MODBUS_ENABLED
//Modbus Object
ModbusSerial modbus;
#endif

/*
extern "C" int availableMemory(char *);

int availableMemory(char *msg) 
{
  int size = 8192; // Use 2048 with ATmega328
  byte *buf;

  while ((buf = (byte *) malloc(--size)) == NULL);

  free(buf);
  Serial.print(msg);
  Serial.println(size);
}
*/

void setupCycleDelay(unsigned long long cycle_time)
{
    scan_cycle = (uint32_t)(cycle_time/1000000);
    timer_ms = millis() + scan_cycle;
}

void cycleDelay()
{
    //just wait until it is time to start a new cycle
    while(timer_ms > millis())
    {
        #ifdef MODBUS_ENABLED
        //Only run Modbus task if we have at least 1ms gap until the next cycle
        if (timer_ms - millis() >= 1)
        {
            syncModbusBuffers();
        }
        #endif
	}
    //noInterrupts();
    timer_ms += scan_cycle; //set timer for the next scan cycle
    //interrupts();
}

void setup() 
{   
    hardwareInit();
    config_init__();
    glueVars();
	#ifdef MODBUS_ENABLED
    
    #ifdef MBSERIAL
	//Config Modbus Serial (port, speed, rs485 tx pin)
	modbus.config(&MBSERIAL_IFACE, MBSERIAL_BAUD, -1);
	
	//Set the Slave ID
	modbus.setSlaveId(0); 
    #endif
    
    #ifdef MBTCP
    byte mac[] = { MBTCP_MAC };
    byte ip[] = { MBTCP_IP };
    byte dns[] = { MBTCP_DNS };
    byte gateway[] = { MBTCP_GATEWAY };
    byte subnet[] = { MBTCP_SUBNET };
    
    if (sizeof(ip)/sizeof(byte) < 4)
        modbus.config(mac);
    else if (sizeof(dns)/sizeof(byte) < 4)
        modbus.config(mac, ip);
    else if (sizeof(gateway)/sizeof(byte) < 4)
        modbus.config(mac, ip, dns);
    else if (sizeof(subnet)/sizeof(byte) < 4)
        modbus.config(mac, ip, dns, gateway);
    else
        modbus.config(mac, ip, dns, gateway, subnet);
    #endif
	
	//Add all modbus registers
	for (int i = 0; i < MAX_DIGITAL_INPUT; ++i) 
	{
		modbus.addIsts(i);
	}
	for (int i = 0; i < MAX_ANALOG_INPUT; ++i) 
	{
		modbus.addIreg(i);
	}
	for (int i = 0; i < MAX_DIGITAL_OUTPUT; ++i) 
	{
		modbus.addCoil(i);
	}
	for (int i = 0; i < MAX_ANALOG_OUTPUT; ++i) 
	{
		modbus.addHreg(i);
	}
	#endif

    setupCycleDelay(common_ticktime__);
}

#ifdef MODBUS_ENABLED
void syncModbusBuffers()
{
    //Sync OpenPLC Buffers with Modbus Buffers	
    for (int i = 0; i < MAX_DIGITAL_OUTPUT; i++)
    {
        if (bool_output[i/8][i%8] != NULL)
        {
			modbus.Coil(i, (bool)*bool_output[i/8][i%8]);
        }
    }
    for (int i = 0; i < MAX_ANALOG_OUTPUT; i++)
    {
        if (int_output[i] != NULL)
        {
			modbus.Hreg(i, *int_output[i]);
        }
    }
    for (int i = 0; i < MAX_DIGITAL_INPUT; i++)
    {
        if (bool_input[i/8][i%8] != NULL)
        {
			modbus.Ists(i, (bool)*bool_input[i/8][i%8]);
        }
    }
    for (int i = 0; i < MAX_ANALOG_INPUT; i++)
    {
        if (int_input[i] != NULL)
        {
			modbus.Ireg(i, *int_input[i]);
        }
    }
    
    //Read changes from clients
    modbus.task();
    
    //Write changes back to OpenPLC Buffers
    for (int i = 0; i < MAX_DIGITAL_OUTPUT; i++)
    {
        if (bool_output[i/8][i%8] != NULL)
        {
            *bool_output[i/8][i%8] = (uint8_t)modbus.Coil(i);
        }
    }
    for (int i = 0; i < MAX_ANALOG_OUTPUT; i++)
    {
        if (int_output[i] != NULL)
        {
            *int_output[i] = (uint16_t)modbus.Hreg(i);
        }
    }
}
#endif

void loop() 
{
    updateInputBuffers();
	
	#ifdef MODBUS_ENABLED
	syncModbusBuffers();
	#endif
	
    config_run__(__tick++);
    updateOutputBuffers();
    updateTime();

    //sleep until next scan cycle
    cycleDelay();
}