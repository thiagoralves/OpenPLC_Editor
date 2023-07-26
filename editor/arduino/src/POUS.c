#include "POUS.h"

void BLINK_init__(BLINK *data__, BOOL retain) {
  __INIT_LOCATED(BOOL,__QX0_0,data__->BLINK_LED,retain)
  __INIT_LOCATED_VALUE(data__->BLINK_LED,__BOOL_LITERAL(FALSE))
  TON_init__(&data__->TON0,retain);
  TOF_init__(&data__->TOF0,retain);
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

  goto __end;

__end:
  return;
} // BLINK_body__() 





