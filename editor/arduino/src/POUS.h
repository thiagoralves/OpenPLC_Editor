#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"
#include "iec_std_lib.h"

// PROGRAM PROGRAM0
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  TON TON0;
  __DECLARE_LOCATED(BOOL,BLINKY)
  TOF TOF0;
  P1AM_INIT P1AM_INIT0;
  __DECLARE_LOCATED(INT,INIT_MODULES)
  P1_16TR P1_16TR0;
  P1_08N P1_08N0;
  __DECLARE_VAR(INT,SINT_TO_INT11_OUT)

} PROGRAM0;

void PROGRAM0_init__(PROGRAM0 *data__, BOOL retain);
// Code part
void PROGRAM0_body__(PROGRAM0 *data__);
#endif //__POUS_H