#include "POUS.h"

void BLINK_init__(BLINK *data__, BOOL retain) {
  __INIT_LOCATED(BOOL,__QX0_0,data__->BLINK_LED,retain)
  __INIT_LOCATED_VALUE(data__->BLINK_LED,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__IX0_0,data__->BUTTON,retain)
  __INIT_LOCATED_VALUE(data__->BUTTON,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__QX0_1,data__->COUNTER_MAX,retain)
  __INIT_LOCATED_VALUE(data__->COUNTER_MAX,__BOOL_LITERAL(FALSE))
  __INIT_VAR(data__->COUNTER_VALUE,0,retain)
  TON_init__(&data__->TON0,retain);
  TOF_init__(&data__->TOF0,retain);
  CTU_init__(&data__->CTU0,retain);
  R_TRIG_init__(&data__->R_TRIG1,retain);
}

// Code part
void BLINK_body__(BLINK *data__) {
  // Initialise TEMP variables

  __SET_VAR(data__->TON0.,EN,,__BOOL_LITERAL(TRUE));
  __SET_VAR(data__->TON0.,IN,,!(__GET_LOCATED(data__->BLINK_LED,)));
  __SET_VAR(data__->TON0.,PT,,__time_to_timespec(1, 500, 0, 0, 0, 0));
  TON_body__(&data__->TON0);
  __SET_VAR(data__->TOF0.,EN,,__GET_VAR(data__->TON0.ENO,));
  __SET_VAR(data__->TOF0.,IN,,__GET_VAR(data__->TON0.Q,));
  __SET_VAR(data__->TOF0.,PT,,__time_to_timespec(1, 500, 0, 0, 0, 0));
  TOF_body__(&data__->TOF0);
  __SET_LOCATED(data__->,BLINK_LED,,__GET_VAR(data__->TOF0.Q,));
  __SET_VAR(data__->R_TRIG1.,CLK,,__GET_LOCATED(data__->BUTTON,));
  R_TRIG_body__(&data__->R_TRIG1);
  __SET_VAR(data__->CTU0.,CU,,__GET_VAR(data__->R_TRIG1.Q,));
  __SET_VAR(data__->CTU0.,PV,,10);
  CTU_body__(&data__->CTU0);
  __SET_LOCATED(data__->,COUNTER_MAX,,__GET_VAR(data__->CTU0.Q,));
  __SET_VAR(data__->,COUNTER_VALUE,,__GET_VAR(data__->CTU0.CV,));

  goto __end;

__end:
  return;
} // BLINK_body__() 





