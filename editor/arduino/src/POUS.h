#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"
#include "iec_std_lib.h"

// PROGRAM BLINK
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  __DECLARE_LOCATED(BOOL,BLINK_LED)
  __DECLARE_LOCATED(BOOL,BUTTON)
  __DECLARE_LOCATED(BOOL,COUNTER_MAX)
  __DECLARE_VAR(INT,COUNTER_VALUE)
  TON TON0;
  TOF TOF0;
  CTU CTU0;
  R_TRIG R_TRIG1;

} BLINK;

void BLINK_init__(BLINK *data__, BOOL retain);
// Code part
void BLINK_body__(BLINK *data__);
#endif //__POUS_H
