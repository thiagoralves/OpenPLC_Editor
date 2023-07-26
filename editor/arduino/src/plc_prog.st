PROGRAM Blink
  VAR
    blink_led : BOOL;
    TON0 : TON;
    TOF0 : TOF;
  END_VAR

  TON0(EN := TRUE, IN := NOT(blink_led), PT := T#500ms);
  TOF0(EN := TON0.ENO, IN := TON0.Q, PT := T#500ms);
  blink_led := TOF0.Q;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : Blink;
  END_RESOURCE
END_CONFIGURATION
