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
    system_out AT %QX0.0 : BOOL;
    heat_out AT %QX0.1 : BOOL;
    cooling_out AT %QX0.2 : BOOL;
  END_VAR
  VAR
    RUN_STATUS : BOOL;
  END_VAR
  VAR
    ET_IN AT %IW0 : INT;
    BT_IN AT %IW1 : INT;
    AT_IN AT %IW2 : INT;
    CH4_in AT %IW3 : INT;
  END_VAR
  VAR
    TON0 : TON;
  END_VAR

  stop_status := STOP_BUTTON;
  RUN_STATUS := NOT(stop_status) AND RUN_STATUS;
  TON0(IN := RUN_STATUS, PT := t#2000ms);
  system_out := TON0.Q;
  cooling_out := cooling AND RUN_STATUS;
  heat_out := heat AND RUN_STATUS;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : program0;
  END_RESOURCE
END_CONFIGURATION
