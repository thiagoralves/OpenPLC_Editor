PROGRAM program0
  VAR
    LED_PIN AT %QX0.3 : BOOL;
  END_VAR
  VAR
    TON0 : TON;
    TOF0 : TOF;
  END_VAR

  TON0(IN := NOT(LED_PIN), PT := T#500ms);
  TOF0(IN := TON0.Q, PT := T#500ms);
  LED_PIN := TOF0.Q;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : program0;
  END_RESOURCE
END_CONFIGURATION
