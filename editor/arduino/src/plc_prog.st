PROGRAM MQTT_Example
  VAR
    blink_led : BOOL;
    TON0 : TON;
    TOF0 : TOF;
    MQTT_CONNECT0 : MQTT_CONNECT;
    MQTT_SEND0 : MQTT_SEND;
    mqtt_connected : BOOL := 0;
  END_VAR

  TON0(EN := TRUE, IN := NOT(blink_led), PT := T#500ms);
  TOF0(EN := TON0.ENO, IN := TON0.Q, PT := T#500ms);
  blink_led := TOF0.Q;
  MQTT_CONNECT0(CONNECT := NOT(mqtt_connected), BROKER := 'test.mosquitto.org', PORT := 1883);
  mqtt_connected := MQTT_CONNECT0.SUCCESS;
  MQTT_SEND0(SEND := blink_led AND mqtt_connected, TOPIC := 'openplc-test-topic', MESSAGE := 'Hello from OpenPLC!');
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : MQTT_Example;
  END_RESOURCE
END_CONFIGURATION
