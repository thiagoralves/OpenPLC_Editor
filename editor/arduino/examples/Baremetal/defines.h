//Comms configurations
#define MBSERIAL_IFACE Serial
#define MBSERIAL_BAUD 115200
#define MBSERIAL_SLAVE 0
#define MBTCP_MAC 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD
#define MBTCP_IP 
#define MBTCP_DNS 
#define MBTCP_GATEWAY 
#define MBTCP_SUBNET 255,255,255,0
#define MBTCP_SSID ""
#define MBTCP_PWD ""


//IO Config
#define PINMASK_DIN 17, 18, 19, 21, 22, 23, 27, 32, 33
#define PINMASK_AIN 34, 35, 36, 39
#define PINMASK_DOUT 01, 02, 03, 04, 05, 12, 13, 14, 15, 16
#define PINMASK_AOUT 25, 26
#define NUM_DISCRETE_INPUT 9
#define NUM_ANALOG_INPUT 4
#define NUM_DISCRETE_OUTPUT 10
#define NUM_ANALOG_OUTPUT 2
#define BOARD_ESP32


//Arduino Libraries
