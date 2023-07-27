//Comms configurations
#define MBSERIAL_IFACE Serial2
#define MBSERIAL_BAUD 57600
#define MBSERIAL_SLAVE 4
#define MBTCP_MAC 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD
#define MBTCP_IP 192,168,4,1
#define MBTCP_DNS 
#define MBTCP_GATEWAY 
#define MBTCP_SUBNET 255,255,255,0
#define MBTCP_SSID ""
#define MBTCP_PWD ""
#define MBSERIAL
#define MODBUS_ENABLED
#define MBSERIAL_TXPIN 17


//IO Config
#define PINMASK_DIN 18, 19, 21, 22
#define PINMASK_AIN 34, 35, 36
#define PINMASK_DOUT 04, 05, 14
#define PINMASK_AOUT 
#define NUM_DISCRETE_INPUT 4
#define NUM_ANALOG_INPUT 3
#define NUM_DISCRETE_OUTPUT 3
#define NUM_ANALOG_OUTPUT 1
#define BOARD_ESP32


//Arduino Libraries


//Pin Array Sizes
