PROGRAM program0
  VAR
    RUN_BUTTON AT %IX0.1 : BOOL;
    STOP_BUTTON AT %IX0.2 : BOOL;
    heat AT %IX0.3 : BOOL;
    cooling AT %IX0.4 : BOOL;
  END_VAR
  VAR
    stop_status : BOOL;
  END_VAR
  VAR
    system_out AT %QX0.3 : BOOL;
    heat_out AT %QX0.4 : BOOL;
    cooling_out AT %QX0.7 : BOOL;
  END_VAR
  VAR
    RUN_STATUS : BOOL;
  END_VAR
  VAR
    ET_IN AT %IW0 : INT;
    BT_IN AT %IW1 : INT;
    AT_IN AT %IW2 : INT;
  END_VAR
  VAR
    TON0 : TON;
    ARTISAN_BT : INT;
    R_TRIG1 : R_TRIG;
    _TMP_MOVE35_ENO : BOOL;
    _TMP_MOVE35_OUT : INT;
  END_VAR

  stop_status := STOP_BUTTON;
  RUN_STATUS := NOT(stop_status) AND (RUN_BUTTON OR RUN_STATUS);
  TON0(IN := RUN_STATUS, PT := t#2000ms);
  system_out := TON0.Q;
  R_TRIG1(CLK := STOP_BUTTON);
  IF R_TRIG1.Q THEN
    RUN_STATUS := FALSE; (*reset*)
  END_IF;
  cooling_out := cooling AND RUN_STATUS;
  heat_out := heat AND RUN_STATUS;
  _TMP_MOVE35_OUT := MOVE(EN := RUN_STATUS, IN := BT_IN, ENO => _TMP_MOVE35_ENO);
  IF _TMP_MOVE35_ENO THEN
      ARTISAN_BT := _TMP_MOVE35_OUT;
  END_IF;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : program0;
  END_RESOURCE
END_CONFIGURATION
