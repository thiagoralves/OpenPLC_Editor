#ifndef __POUS_H
#define __POUS_H

#include "accessor.h"
#include "iec_std_lib.h"

// PROGRAM BLINK
// Data part
typedef struct {
  // PROGRAM Interface - IN, OUT, IN_OUT variables

  // PROGRAM private variables - TEMP, private and located variables
  __DECLARE_LOCATED(BOOL,ACCESO)
  __DECLARE_LOCATED(BOOL,LED1)
  __DECLARE_LOCATED(BOOL,LED2)
  __DECLARE_VAR(WORD,VALORE)
  __DECLARE_LOCATED(WORD,ANALOGICA)
  __DECLARE_VAR(BOOL,_TMP_GT12_OUT)

} BLINK;

void BLINK_init__(BLINK *data__, BOOL retain);
// Code part
void BLINK_body__(BLINK *data__);
#endif //__POUS_H
