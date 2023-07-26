PROGRAM Blink
  VAR
    acceso AT %IX0.0 : BOOL;
    led1 AT %QX0.0 : BOOL;
    led2 AT %QX0.4 : BOOL;
  END_VAR
  VAR CONSTANT
    valore : WORD := 30000;
  END_VAR
  VAR
    Analogica AT %IW0 : WORD;
  END_VAR
  VAR
    _TMP_GT12_OUT : BOOL;
  END_VAR

  led1 := acceso;
  _TMP_GT12_OUT := GT(Analogica, valore);
  led2 := _TMP_GT12_OUT;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : Blink;
  END_RESOURCE
END_CONFIGURATION
