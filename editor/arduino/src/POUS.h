#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"
#include "iec_std_lib.h"

// FUNCTION_BLOCK PT2
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,IN1)
  __DECLARE_VAR(BOOL,IN3)
  __DECLARE_VAR(BOOL,IN2)
  __DECLARE_VAR(TIME,IN_TIME)
  __DECLARE_VAR(BOOL,OUT1)
  __DECLARE_VAR(BOOL,OUT2)
  __DECLARE_VAR(BOOL,OUT3)
  __DECLARE_VAR(BOOL,ERROR)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,STARTED_TIMER_1)
  __DECLARE_VAR(BOOL,TIMER_1_INPUT)
  __DECLARE_VAR(BOOL,STARTED_TIMER_2)
  __DECLARE_VAR(BOOL,TIMER_2_INPUT)
  TOF TOF1;
  TOF TOF2;

} PT2;

void PT2_init__(PT2 *data__, BOOL retain);
// Code part
void PT2_body__(PT2 *data__);
// PROGRAM PROGRAM0
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  __DECLARE_VAR(BOOL,BUTTON)
  __DECLARE_LOCATED(BOOL,TIMER_OUT)
  __DECLARE_VAR(INT,COUNTER_VALUE)
  PT2 PT20;

} PROGRAM0;

void PROGRAM0_init__(PROGRAM0 *data__, BOOL retain);
// Code part
void PROGRAM0_body__(PROGRAM0 *data__);
#endif //__POUS_H
