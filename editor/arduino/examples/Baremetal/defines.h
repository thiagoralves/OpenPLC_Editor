//Comms configurations
#define MBSERIAL_IFACE Serial
#define MBSERIAL_BAUD 115200
#define MBSERIAL_SLAVE 0
#define MBTCP_MAC 0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD
#define MBTCP_IP 192,168,0,192
#define MBTCP_DNS 8,8,8,8
#define MBTCP_GATEWAY 192,168,0,1
#define MBTCP_SUBNET 255,255,255,0
#define MBTCP_SSID "Alves-Net"
#define MBTCP_PWD "palmdev1"
#define MBTCP
#define MODBUS_ENABLED
#define MBTCP_WIFI


//IO Config
#define PINMASK_DIN 2, 3, 4, 5, 6
#define PINMASK_AIN 15, 16, 17, 18, 19, 20, 21
#define PINMASK_DOUT 7, 8, 10, 11, 12, 13
#define PINMASK_AOUT 9, 14
#define NUM_DISCRETE_INPUT 5
#define NUM_ANALOG_INPUT 7
#define NUM_DISCRETE_OUTPUT 6
#define NUM_ANALOG_OUTPUT 2
#define BOARD_WIFININA


//Arduino Libraries
#define USE_MQTT_BLOCKS


//Pin Array Sizes
