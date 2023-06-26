#include "POUS.h"

void MQTT_EXAMPLE_init__(MQTT_EXAMPLE *data__, BOOL retain) {
  __INIT_VAR(data__->BLINK_LED,__BOOL_LITERAL(FALSE),retain)
  TON_init__(&data__->TON0,retain);
  TOF_init__(&data__->TOF0,retain);
  MQTT_CONNECT_init__(&data__->MQTT_CONNECT0,retain);
  MQTT_SEND_init__(&data__->MQTT_SEND0,retain);
  __INIT_VAR(data__->MQTT_CONNECTED,0,retain)
}

// Code part
void MQTT_EXAMPLE_body__(MQTT_EXAMPLE *data__) {
  // Initialise TEMP variables

  __SET_VAR(data__->TON0.,EN,,__BOOL_LITERAL(TRUE));
  __SET_VAR(data__->TON0.,IN,,!(__GET_VAR(data__->BLINK_LED,)));
  __SET_VAR(data__->TON0.,PT,,__time_to_timespec(1, 500, 0, 0, 0, 0));
  TON_body__(&data__->TON0);
  __SET_VAR(data__->TOF0.,EN,,__GET_VAR(data__->TON0.ENO,));
  __SET_VAR(data__->TOF0.,IN,,__GET_VAR(data__->TON0.Q,));
  __SET_VAR(data__->TOF0.,PT,,__time_to_timespec(1, 500, 0, 0, 0, 0));
  TOF_body__(&data__->TOF0);
  __SET_VAR(data__->,BLINK_LED,,__GET_VAR(data__->TOF0.Q,));
  __SET_VAR(data__->MQTT_CONNECT0.,CONNECT,,!(__GET_VAR(data__->MQTT_CONNECTED,)));
  __SET_VAR(data__->MQTT_CONNECT0.,BROKER,,__STRING_LITERAL(18,"test.mosquitto.org"));
  __SET_VAR(data__->MQTT_CONNECT0.,PORT,,1883);
  MQTT_CONNECT_body__(&data__->MQTT_CONNECT0);
  __SET_VAR(data__->,MQTT_CONNECTED,,__GET_VAR(data__->MQTT_CONNECT0.SUCCESS,));
  __SET_VAR(data__->MQTT_SEND0.,SEND,,(__GET_VAR(data__->BLINK_LED,) && __GET_VAR(data__->MQTT_CONNECTED,)));
  __SET_VAR(data__->MQTT_SEND0.,TOPIC,,__STRING_LITERAL(18,"openplc-test-topic"));
  __SET_VAR(data__->MQTT_SEND0.,MESSAGE,,__STRING_LITERAL(19,"Hello from OpenPLC!"));
  MQTT_SEND_body__(&data__->MQTT_SEND0);

  goto __end;

__end:
  return;
} // MQTT_EXAMPLE_body__() 





