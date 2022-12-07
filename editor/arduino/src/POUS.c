#include "POUS.h"

void PROGRAM0_init__(PROGRAM0 *data__, BOOL retain) {
  TON_init__(&data__->TON0,retain);
  __INIT_LOCATED(BOOL,__QX0_0,data__->BLINKY,retain)
  __INIT_LOCATED_VALUE(data__->BLINKY,__BOOL_LITERAL(FALSE))
  TOF_init__(&data__->TOF0,retain);
  P1AM_INIT_init__(&data__->P1AM_INIT0,retain);
  __INIT_LOCATED(INT,__QW0,data__->INIT_MODULES,retain)
  __INIT_LOCATED_VALUE(data__->INIT_MODULES,0)
  P1_16TR_init__(&data__->P1_16TR0,retain);
  P1_08N_init__(&data__->P1_08N0,retain);
  __INIT_VAR(data__->SINT_TO_INT11_OUT,0,retain)
}

// Code part
void PROGRAM0_body__(PROGRAM0 *data__) {
  // Initialise TEMP variables

  __SET_VAR(data__->P1AM_INIT0.,INIT,,__BOOL_LITERAL(TRUE));
  P1AM_INIT_body__(&data__->P1AM_INIT0);
  __SET_VAR(data__->,SINT_TO_INT11_OUT,,SINT_TO_INT(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (SINT)__GET_VAR(data__->P1AM_INIT0.SUCCESS,)));
  __SET_LOCATED(data__->,INIT_MODULES,,__GET_VAR(data__->SINT_TO_INT11_OUT,));
  __SET_VAR(data__->TON0.,IN,,!(__GET_LOCATED(data__->BLINKY,)));
  __SET_VAR(data__->TON0.,PT,,__time_to_timespec(1, 0, 2, 0, 0, 0));
  TON_body__(&data__->TON0);
  __SET_VAR(data__->TOF0.,IN,,__GET_VAR(data__->TON0.Q,));
  __SET_VAR(data__->TOF0.,PT,,__time_to_timespec(1, 0, 2, 0, 0, 0));
  TOF_body__(&data__->TOF0);
  __SET_LOCATED(data__->,BLINKY,,__GET_VAR(data__->TOF0.Q,));
  __SET_VAR(data__->P1_08N0.,SLOT,,1);
  P1_08N_body__(&data__->P1_08N0);
  __SET_VAR(data__->P1_16TR0.,SLOT,,1);
  __SET_VAR(data__->P1_16TR0.,O2,,__GET_LOCATED(data__->BLINKY,));
  __SET_VAR(data__->P1_16TR0.,O4,,__GET_VAR(data__->P1_08N0.I1,));
  __SET_VAR(data__->P1_16TR0.,O7,,__GET_VAR(data__->P1_08N0.I4,));
  __SET_VAR(data__->P1_16TR0.,O9,,__GET_VAR(data__->P1_08N0.I6,));
  __SET_VAR(data__->P1_16TR0.,O13,,__GET_LOCATED(data__->BLINKY,));
  P1_16TR_body__(&data__->P1_16TR0);

  goto __end;

__end:
  return;
} // PROGRAM0_body__() 





