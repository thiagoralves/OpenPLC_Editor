/**
 * MCP Tool: st_reference
 *
 * Provides IEC 61131-3 Structured Text language reference and code templates.
 * Designed to help LLMs generate correct PLC code by providing context
 * about the language, standard functions, and common patterns.
 */

import { z } from 'zod';

export const stReferenceToolName = 'st_reference';

export const stReferenceToolConfig = {
  title: 'Structured Text Reference',
  description: `Get IEC 61131-3 Structured Text language reference information.

Returns syntax examples, standard function signatures, data types,
and common patterns. Use this before generating ST code to ensure
correct syntax and idiomatic usage.

Topics: data_types, operators, control_flow, timers_counters,
        standard_functions, program_template, function_block_template`,
  inputSchema: {
    topic: z.enum([
      'data_types',
      'operators',
      'control_flow',
      'timers_counters',
      'standard_functions',
      'program_template',
      'function_block_template',
      'all',
    ]).describe('The reference topic to look up'),
  },
};

const REFERENCES: Record<string, string> = {
  data_types: `## IEC 61131-3 Data Types

### Boolean
  BOOL          (* TRUE or FALSE *)

### Integer Types
  SINT          (* -128 to 127, 8-bit signed *)
  INT           (* -32768 to 32767, 16-bit signed *)
  DINT          (* -2^31 to 2^31-1, 32-bit signed *)
  LINT          (* -2^63 to 2^63-1, 64-bit signed *)
  USINT         (* 0 to 255, 8-bit unsigned *)
  UINT          (* 0 to 65535, 16-bit unsigned *)
  UDINT         (* 0 to 2^32-1, 32-bit unsigned *)
  ULINT         (* 0 to 2^64-1, 64-bit unsigned *)

### Floating Point
  REAL          (* 32-bit IEEE 754 *)
  LREAL         (* 64-bit IEEE 754 *)

### Bit String
  BYTE          (* 8 bits *)
  WORD          (* 16 bits *)
  DWORD         (* 32 bits *)
  LWORD         (* 64 bits *)

### Time / Date
  TIME          (* Duration, e.g. T#5s, T#100ms *)
  DATE          (* Calendar date, e.g. D#2024-01-15 *)
  TIME_OF_DAY   (* TOD#14:30:00 *)
  DATE_AND_TIME (* DT#2024-01-15-14:30:00 *)

### String
  STRING        (* Variable-length, default max 254 chars *)
  STRING[80]    (* Max 80 chars *)

### Type Conversions
  INT_TO_REAL(x)    REAL_TO_INT(x)    BOOL_TO_INT(x)
  INT_TO_STRING(x)  STRING_TO_INT(x)  DINT_TO_REAL(x)`,

  operators: `## IEC 61131-3 Operators

### Arithmetic
  +    (* Addition *)
  -    (* Subtraction *)
  *    (* Multiplication *)
  /    (* Division *)
  MOD  (* Modulo *)

### Comparison (return BOOL)
  =    (* Equal *)
  <>   (* Not equal *)
  <    (* Less than *)
  >    (* Greater than *)
  <=   (* Less or equal *)
  >=   (* Greater or equal *)

### Logical (BOOL operands)
  AND  (* Logical AND *)
  OR   (* Logical OR *)
  XOR  (* Logical XOR *)
  NOT  (* Logical NOT *)

### Bitwise (integer operands)
  AND  (* Bitwise AND *)
  OR   (* Bitwise OR *)
  XOR  (* Bitwise XOR *)
  NOT  (* Bitwise NOT *)
  SHL(x, n)  (* Shift left *)
  SHR(x, n)  (* Shift right *)

### Assignment
  :=   (* Assign value *)`,

  control_flow: `## IEC 61131-3 Control Flow

### IF / ELSIF / ELSE
  IF condition THEN
    (* statements *)
  ELSIF other_condition THEN
    (* statements *)
  ELSE
    (* statements *)
  END_IF;

### CASE
  CASE selector OF
    1: (* statements for value 1 *);
    2, 3: (* statements for 2 or 3 *);
    4..10: (* statements for range 4-10 *);
  ELSE
    (* default statements *)
  END_CASE;

### FOR Loop
  FOR i := 0 TO 9 BY 1 DO
    (* statements, i goes 0,1,2,...,9 *)
  END_FOR;

### WHILE Loop
  WHILE condition DO
    (* statements *)
  END_WHILE;

### REPEAT Loop
  REPEAT
    (* statements *)
  UNTIL condition
  END_REPEAT;

### EXIT / RETURN
  EXIT;    (* Break out of FOR/WHILE/REPEAT *)
  RETURN;  (* Exit current POU *)`,

  timers_counters: `## IEC 61131-3 Standard Timers and Counters

### TON - Timer On Delay
  VAR
    myTimer : TON;
  END_VAR
  myTimer(IN := start_signal, PT := T#5s);
  IF myTimer.Q THEN
    (* Executes after 5 seconds of IN being TRUE *)
  END_IF;
  (* myTimer.ET = elapsed time *)

### TOF - Timer Off Delay
  VAR
    offTimer : TOF;
  END_VAR
  offTimer(IN := signal, PT := T#3s);
  (* offTimer.Q stays TRUE for 3s after IN goes FALSE *)

### TP - Pulse Timer
  VAR
    pulse : TP;
  END_VAR
  pulse(IN := trigger, PT := T#1s);
  (* pulse.Q is TRUE for exactly 1s after rising edge of IN *)

### CTU - Count Up
  VAR
    counter : CTU;
  END_VAR
  counter(CU := count_pulse, R := reset, PV := 100);
  IF counter.Q THEN
    (* counter.CV has reached PV (100) *)
  END_IF;

### CTD - Count Down
  VAR
    downCounter : CTD;
  END_VAR
  downCounter(CD := count_pulse, LD := load, PV := 50);
  (* downCounter.Q is TRUE when CV reaches 0 *)

### R_TRIG / F_TRIG - Edge Detection
  VAR
    risingEdge : R_TRIG;
    fallingEdge : F_TRIG;
  END_VAR
  risingEdge(CLK := input_signal);
  IF risingEdge.Q THEN
    (* TRUE for one scan on rising edge *)
  END_IF;`,

  standard_functions: `## IEC 61131-3 Standard Functions

### Math
  ABS(x)        (* Absolute value *)
  SQRT(x)       (* Square root *)
  LN(x)         (* Natural log *)
  LOG(x)        (* Log base 10 *)
  EXP(x)        (* e^x *)
  EXPT(x, y)    (* x^y *)
  SIN(x)        (* Sine, x in radians *)
  COS(x)        (* Cosine *)
  TAN(x)        (* Tangent *)
  ASIN(x)       (* Arc sine *)
  ACOS(x)       (* Arc cosine *)
  ATAN(x)       (* Arc tangent *)

### Selection
  SEL(G, IN0, IN1)     (* Select: if G then IN1 else IN0 *)
  MAX(IN0, IN1)        (* Maximum *)
  MIN(IN0, IN1)        (* Minimum *)
  LIMIT(MN, IN, MX)    (* Clamp IN between MN and MX *)
  MUX(K, IN0, IN1...)  (* Multiplexer: select INk *)

### String
  LEN(s)               (* String length *)
  LEFT(s, n)           (* Left n chars *)
  RIGHT(s, n)          (* Right n chars *)
  MID(s, n, p)         (* n chars starting at position p *)
  CONCAT(s1, s2)       (* Concatenate *)
  FIND(s1, s2)         (* Find s2 in s1, returns position *)
  INSERT(s1, s2, p)    (* Insert s2 into s1 at position p *)
  DELETE(s, n, p)       (* Delete n chars from s at position p *)
  REPLACE(s1, s2, n, p) (* Replace n chars in s1 at p with s2 *)`,

  program_template: `## Program Template

PROGRAM main
VAR
  (* Local variables *)
  counter : INT := 0;
  running : BOOL := TRUE;
  setpoint : REAL := 25.0;
END_VAR
VAR_INPUT
  (* Inputs from I/O or calling context *)
  start_button AT %IX0.0 : BOOL;
  sensor_value AT %IW0 : INT;
END_VAR
VAR_OUTPUT
  (* Outputs to I/O or calling context *)
  motor_on AT %QX0.0 : BOOL;
  speed_ref AT %QW0 : INT;
END_VAR

  (* Program body *)
  IF start_button AND running THEN
    counter := counter + 1;
    motor_on := TRUE;
    speed_ref := REAL_TO_INT(setpoint * 100.0);
  ELSE
    motor_on := FALSE;
    speed_ref := 0;
  END_IF;

END_PROGRAM`,

  function_block_template: `## Function Block Template

FUNCTION_BLOCK PID_Controller
VAR_INPUT
  setpoint : REAL;
  process_value : REAL;
  kp : REAL := 1.0;    (* Proportional gain *)
  ki : REAL := 0.1;    (* Integral gain *)
  kd : REAL := 0.01;   (* Derivative gain *)
  dt : REAL := 0.02;   (* Sample time in seconds *)
END_VAR
VAR_OUTPUT
  output : REAL;
END_VAR
VAR
  error : REAL;
  prev_error : REAL := 0.0;
  integral : REAL := 0.0;
  derivative : REAL;
END_VAR

  error := setpoint - process_value;
  integral := integral + (error * dt);
  derivative := (error - prev_error) / dt;

  output := (kp * error) + (ki * integral) + (kd * derivative);

  (* Clamp output 0-100% *)
  output := LIMIT(0.0, output, 100.0);

  prev_error := error;

END_FUNCTION_BLOCK`,
};

export async function stReferenceToolHandler({
  topic,
}: {
  topic: string;
}) {
  if (topic === 'all') {
    const allContent = Object.values(REFERENCES).join('\n\n---\n\n');
    return {
      content: [{
        type: 'text' as const,
        text: allContent,
      }],
    };
  }

  const content = REFERENCES[topic];
  if (!content) {
    return {
      content: [{
        type: 'text' as const,
        text: `Unknown topic: ${topic}. Available: ${Object.keys(REFERENCES).join(', ')}, all`,
      }],
    };
  }

  return {
    content: [{
      type: 'text' as const,
      text: content,
    }],
  };
}
