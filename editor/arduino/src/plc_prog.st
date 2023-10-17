PROGRAM Blink
  VAR
    blink_led AT %QX0.0 : BOOL;
    button AT %IX0.0 : BOOL;
    counter_max AT %QX0.1 : BOOL;
  END_VAR
  VAR
    counter_value : INT;
    TON0 : TON;
    TOF0 : TOF;
    CTU0 : CTU;
    R_TRIG1 : R_TRIG;
  END_VAR

  TON0(EN := TRUE, IN := NOT(blink_led), PT := T#500ms);
  TOF0(EN := TON0.ENO, IN := TON0.Q, PT := T#500ms);
  blink_led := TOF0.Q;
  R_TRIG1(CLK := button);
  CTU0(CU := R_TRIG1.Q, PV := 10);
  counter_max := CTU0.Q;
  counter_value := CTU0.CV;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : Blink;
  END_RESOURCE
END_CONFIGURATION
