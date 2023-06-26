#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"
#include "iec_std_lib.h"

// PROGRAM MQTT_EXAMPLE
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,BLINK_LED)
  TON TON0;
  TOF TOF0;
  MQTT_CONNECT MQTT_CONNECT0;
  MQTT_SEND MQTT_SEND0;
  __DECLARE_VAR(BOOL,MQTT_CONNECTED)

} MQTT_EXAMPLE;

void MQTT_EXAMPLE_init__(MQTT_EXAMPLE *data__, BOOL retain);
// Code part
void MQTT_EXAMPLE_body__(MQTT_EXAMPLE *data__);
#endif //__POUS_H
