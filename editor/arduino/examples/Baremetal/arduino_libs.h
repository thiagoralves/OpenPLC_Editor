//disable pins
//uint8_t disabled_pins[11] = {1, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255}; //10 pins max. First array position is used as index
extern uint8_t pinMask_DIN[];
extern uint8_t pinMask_AIN[];
extern uint8_t pinMask_DOUT[];
extern uint8_t pinMask_AOUT[];

#ifdef USE_DS18B20_BLOCK
    #include "modules/ds18b20.c"
#endif

#ifdef USE_P1AM_BLOCKS
    #include "modules/p1am.c"
#endif

#ifdef USE_CLOUD_BLOCKS
    #include "modules/arduino_cloud.c"
#endif

#ifdef USE_MQTT_BLOCKS
    #include "modules/mqtt.c"
#endif

#ifdef USE_SM_BLOCKS
	#include "modules/sm_cards.c"
#endif

#ifdef USE_ARDUINOCAN_BLOCK
	#include "modules/arduinocan.c"
#endif