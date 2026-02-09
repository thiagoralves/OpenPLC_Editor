(*
  Motor Control with Start/Stop and Overload Protection
  Demonstrates typical industrial control patterns:
  - Latching start/stop logic
  - Timer-based star-delta starting
  - Overload fault with manual reset
*)
PROGRAM motor_control
VAR_INPUT
  start_button AT %IX0.0 : BOOL;     (* Momentary start push-button *)
  stop_button AT %IX0.1 : BOOL;      (* Momentary stop push-button, NC *)
  overload_relay AT %IX0.2 : BOOL;   (* Thermal overload relay contact *)
  reset_button AT %IX0.3 : BOOL;     (* Fault reset push-button *)
END_VAR
VAR_OUTPUT
  main_contactor AT %QX0.0 : BOOL;   (* Main contactor output *)
  star_contactor AT %QX0.1 : BOOL;   (* Star contactor for starting *)
  delta_contactor AT %QX0.2 : BOOL;  (* Delta contactor for running *)
  fault_lamp AT %QX0.3 : BOOL;       (* Fault indicator lamp *)
  running_lamp AT %QX0.4 : BOOL;     (* Running indicator lamp *)
END_VAR
VAR
  motor_running : BOOL := FALSE;
  fault_active : BOOL := FALSE;
  star_delta_timer : TON;
  star_delta_done : BOOL := FALSE;
END_VAR

  (* Overload fault detection and latching *)
  IF overload_relay THEN
    fault_active := TRUE;
    motor_running := FALSE;
  END_IF;

  (* Fault reset *)
  IF reset_button AND NOT overload_relay THEN
    fault_active := FALSE;
  END_IF;

  (* Start/stop logic with latching *)
  IF start_button AND stop_button AND NOT fault_active THEN
    motor_running := TRUE;
    star_delta_done := FALSE;
  END_IF;

  IF NOT stop_button THEN
    motor_running := FALSE;
  END_IF;

  (* Star-delta starting timer *)
  star_delta_timer(IN := motor_running AND NOT star_delta_done, PT := T#3s);
  IF star_delta_timer.Q THEN
    star_delta_done := TRUE;
  END_IF;

  (* Contactor outputs *)
  main_contactor := motor_running;
  star_contactor := motor_running AND NOT star_delta_done;
  delta_contactor := motor_running AND star_delta_done;

  (* Indicator lamps *)
  fault_lamp := fault_active;
  running_lamp := motor_running;

END_PROGRAM
