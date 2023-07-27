#include "POUS.h"

static inline INT __PROGRAM0_MOVE__INT__INT1(BOOL EN,
  INT IN,
  PROGRAM0 *data__)
{
  INT __res;
  BOOL __TMP_ENO = __GET_VAR(data__->_TMP_MOVE35_ENO,);
  __res = MOVE__INT__INT(EN,
    &__TMP_ENO,
    IN);
  __SET_VAR(,data__->_TMP_MOVE35_ENO,,__TMP_ENO);
  return __res;
}

void PROGRAM0_init__(PROGRAM0 *data__, BOOL retain) {
  __INIT_LOCATED(BOOL,__IX0_1,data__->RUN_BUTTON,retain)
  __INIT_LOCATED_VALUE(data__->RUN_BUTTON,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__IX0_2,data__->STOP_BUTTON,retain)
  __INIT_LOCATED_VALUE(data__->STOP_BUTTON,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__IX0_3,data__->HEAT,retain)
  __INIT_LOCATED_VALUE(data__->HEAT,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__IX0_4,data__->COOLING,retain)
  __INIT_LOCATED_VALUE(data__->COOLING,__BOOL_LITERAL(FALSE))
  __INIT_VAR(data__->STOP_STATUS,__BOOL_LITERAL(FALSE),retain)
  __INIT_LOCATED(BOOL,__QX0_3,data__->SYSTEM_OUT,retain)
  __INIT_LOCATED_VALUE(data__->SYSTEM_OUT,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__QX0_4,data__->HEAT_OUT,retain)
  __INIT_LOCATED_VALUE(data__->HEAT_OUT,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__QX0_7,data__->COOLING_OUT,retain)
  __INIT_LOCATED_VALUE(data__->COOLING_OUT,__BOOL_LITERAL(FALSE))
  __INIT_VAR(data__->RUN_STATUS,__BOOL_LITERAL(FALSE),retain)
  __INIT_LOCATED(INT,__IW0,data__->ET_IN,retain)
  __INIT_LOCATED_VALUE(data__->ET_IN,0)
  __INIT_LOCATED(INT,__IW1,data__->BT_IN,retain)
  __INIT_LOCATED_VALUE(data__->BT_IN,0)
  __INIT_LOCATED(INT,__IW2,data__->AT_IN,retain)
  __INIT_LOCATED_VALUE(data__->AT_IN,0)
  TON_init__(&data__->TON0,retain);
  __INIT_VAR(data__->ARTISAN_BT,0,retain)
  R_TRIG_init__(&data__->R_TRIG1,retain);
  __INIT_VAR(data__->_TMP_MOVE35_ENO,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->_TMP_MOVE35_OUT,0,retain)
}

// Code part
void PROGRAM0_body__(PROGRAM0 *data__) {
  // Initialise TEMP variables

  __SET_VAR(data__->,STOP_STATUS,,__GET_LOCATED(data__->STOP_BUTTON,));
  __SET_VAR(data__->,RUN_STATUS,,(!(__GET_VAR(data__->STOP_STATUS,)) && (__GET_LOCATED(data__->RUN_BUTTON,) || __GET_VAR(data__->RUN_STATUS,))));
  __SET_VAR(data__->TON0.,IN,,__GET_VAR(data__->RUN_STATUS,));
  __SET_VAR(data__->TON0.,PT,,__time_to_timespec(1, 2000, 0, 0, 0, 0));
  TON_body__(&data__->TON0);
  __SET_LOCATED(data__->,SYSTEM_OUT,,__GET_VAR(data__->TON0.Q,));
  __SET_VAR(data__->R_TRIG1.,CLK,,__GET_LOCATED(data__->STOP_BUTTON,));
  R_TRIG_body__(&data__->R_TRIG1);
  if (__GET_VAR(data__->R_TRIG1.Q,)) {
    __SET_VAR(data__->,RUN_STATUS,,__BOOL_LITERAL(FALSE));
  };
  __SET_LOCATED(data__->,COOLING_OUT,,(__GET_LOCATED(data__->COOLING,) && __GET_VAR(data__->RUN_STATUS,)));
  __SET_LOCATED(data__->,HEAT_OUT,,(__GET_LOCATED(data__->HEAT,) && __GET_VAR(data__->RUN_STATUS,)));
  __SET_VAR(data__->,_TMP_MOVE35_OUT,,__PROGRAM0_MOVE__INT__INT1(
    (BOOL)__GET_VAR(data__->RUN_STATUS,),
    (INT)__GET_LOCATED(data__->BT_IN,),
    data__));
  if (__GET_VAR(data__->_TMP_MOVE35_ENO,)) {
    __SET_VAR(data__->,ARTISAN_BT,,__GET_VAR(data__->_TMP_MOVE35_OUT,));
  };

  goto __end;

__end:
  return;
} // PROGRAM0_body__() 





