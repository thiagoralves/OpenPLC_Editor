(*
  Blink Example
  Toggles a digital output every 500ms.
  Classic "hello world" of PLC programming.
*)
PROGRAM blink
VAR
  timer : TON;
  blink_state : BOOL := FALSE;
END_VAR
VAR_OUTPUT
  led AT %QX0.0 : BOOL;
END_VAR

  timer(IN := NOT timer.Q, PT := T#500ms);

  IF timer.Q THEN
    blink_state := NOT blink_state;
  END_IF;

  led := blink_state;

END_PROGRAM
