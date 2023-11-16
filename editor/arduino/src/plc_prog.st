FUNCTION_BLOCK PT2
  VAR_INPUT
    IN1 : BOOL;
    IN3 : BOOL := 1;
    IN2 : BOOL;
    IN_TIME : TIME;
  END_VAR
  VAR_OUTPUT
    OUT1 : BOOL;
    OUT2 : BOOL;
    OUT3 : BOOL;
    ERROR : BOOL;
  END_VAR
  VAR
    started_timer_1 : BOOL := 0;
    timer_1_input : BOOL := 0;
    started_timer_2 : BOOL := 0;
    timer_2_input : BOOL := 0;
    TOF1 : TOF;
    TOF2 : TOF;
  END_VAR

  (* Declare timers *)
  TOF1(IN := timer_1_input, PT := T#5s);
  TOF2(IN := timer_2_input, PT := T#5s);


  (* Validate user time input *)
  if LE(IN_TIME, T#0s) or GT(IN_TIME, T#300s) then
      (* Invalid input *)
      ERROR := TRUE;
  else
      ERROR := FALSE;
  end_if;

  (* Logic to activate timer 1 *)
  if IN1 = TRUE and started_timer_1 = FALSE then
      (* Rising edge on IN1 - starting timer *)
      started_timer_1 := TRUE;
      timer_1_input := TRUE;

  elsif started_timer_1 = TRUE and TOF1.Q = TRUE then
      (* Timer has started and is running, lets make sure TOF1 input remains false *)
      timer_1_input := FALSE;
      
      
  elsif started_timer_1 = TRUE and TOF1.Q = FALSE and IN1 = FALSE then
      (* Timer has expired, IN1 is false, lets reset *)
      started_timer_1 := FALSE;
      timer_1_input := FALSE;
  end_if;

  (* Logic to activate timer 2 *)
  if IN2 = TRUE and started_timer_2 = FALSE then
      (* Rising edge on IN2 - starting timer *)
      started_timer_2 := TRUE;
      timer_2_input := TRUE;

  elsif started_timer_2 = TRUE and TOF2.Q = TRUE then
      (* Timer has started and is running, lets make sure TOF2 input remains false *)
      timer_2_input := FALSE;
      
      
  elsif started_timer_2 = TRUE and TOF2.Q = FALSE and IN2 = FALSE then
      (* Timer has expired, IN1 is false, lets reset *)
      started_timer_2 := FALSE;
      timer_2_input := FALSE;
  end_if;

  (* Set outputs *)
  OUT1 := TOF1.Q;
  OUT2 := TOF2.Q;
  OUT3 := IN3;



END_FUNCTION_BLOCK

PROGRAM program0
  VAR
    button : BOOL;
  END_VAR
  VAR
    timer_out AT %QX0.0 : BOOL;
  END_VAR
  VAR
    counter_value : INT;
    PT20 : PT2;
  END_VAR

  PT20(IN1 := button);
  timer_out := PT20.OUT1;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 0);
    PROGRAM instance0 WITH task0 : program0;
  END_RESOURCE
END_CONFIGURATION
