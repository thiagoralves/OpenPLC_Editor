#include "POUS.h"

void PT2_init__(PT2 *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->IN1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->IN3,1,retain)
  __INIT_VAR(data__->IN2,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->IN_TIME,__time_to_timespec(1, 0, 0, 0, 0, 0),retain)
  __INIT_VAR(data__->OUT1,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OUT2,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OUT3,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ERROR,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->STARTED_TIMER_1,0,retain)
  __INIT_VAR(data__->TIMER_1_INPUT,0,retain)
  __INIT_VAR(data__->STARTED_TIMER_2,0,retain)
  __INIT_VAR(data__->TIMER_2_INPUT,0,retain)
  TOF_init__(&data__->TOF1,retain);
  TOF_init__(&data__->TOF2,retain);
}

// Code part
void PT2_body__(PT2 *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->TOF1.,IN,,__GET_VAR(data__->TIMER_1_INPUT,));
  __SET_VAR(data__->TOF1.,PT,,__time_to_timespec(1, 0, 5, 0, 0, 0));
  TOF_body__(&data__->TOF1);
  __SET_VAR(data__->TOF2.,IN,,__GET_VAR(data__->TIMER_2_INPUT,));
  __SET_VAR(data__->TOF2.,PT,,__time_to_timespec(1, 0, 5, 0, 0, 0));
  TOF_body__(&data__->TOF2);
  if ((LE__BOOL__TIME(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (TIME)__GET_VAR(data__->IN_TIME,),
    (TIME)__time_to_timespec(1, 0, 0, 0, 0, 0)) || GT__BOOL__TIME(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (TIME)__GET_VAR(data__->IN_TIME,),
    (TIME)__time_to_timespec(1, 0, 300, 0, 0, 0)))) {
    __SET_VAR(data__->,ERROR,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,ERROR,,__BOOL_LITERAL(FALSE));
  };
  if (((__GET_VAR(data__->IN1,) == __BOOL_LITERAL(TRUE)) && (__GET_VAR(data__->STARTED_TIMER_1,) == __BOOL_LITERAL(FALSE)))) {
    __SET_VAR(data__->,STARTED_TIMER_1,,__BOOL_LITERAL(TRUE));
    __SET_VAR(data__->,TIMER_1_INPUT,,__BOOL_LITERAL(TRUE));
  } else if (((__GET_VAR(data__->STARTED_TIMER_1,) == __BOOL_LITERAL(TRUE)) && (__GET_VAR(data__->TOF1.Q,) == __BOOL_LITERAL(TRUE)))) {
    __SET_VAR(data__->,TIMER_1_INPUT,,__BOOL_LITERAL(FALSE));
  } else if ((((__GET_VAR(data__->STARTED_TIMER_1,) == __BOOL_LITERAL(TRUE)) && (__GET_VAR(data__->TOF1.Q,) == __BOOL_LITERAL(FALSE))) && (__GET_VAR(data__->IN1,) == __BOOL_LITERAL(FALSE)))) {
    __SET_VAR(data__->,STARTED_TIMER_1,,__BOOL_LITERAL(FALSE));
    __SET_VAR(data__->,TIMER_1_INPUT,,__BOOL_LITERAL(FALSE));
  };
  if (((__GET_VAR(data__->IN2,) == __BOOL_LITERAL(TRUE)) && (__GET_VAR(data__->STARTED_TIMER_2,) == __BOOL_LITERAL(FALSE)))) {
    __SET_VAR(data__->,STARTED_TIMER_2,,__BOOL_LITERAL(TRUE));
    __SET_VAR(data__->,TIMER_2_INPUT,,__BOOL_LITERAL(TRUE));
  } else if (((__GET_VAR(data__->STARTED_TIMER_2,) == __BOOL_LITERAL(TRUE)) && (__GET_VAR(data__->TOF2.Q,) == __BOOL_LITERAL(TRUE)))) {
    __SET_VAR(data__->,TIMER_2_INPUT,,__BOOL_LITERAL(FALSE));
  } else if ((((__GET_VAR(data__->STARTED_TIMER_2,) == __BOOL_LITERAL(TRUE)) && (__GET_VAR(data__->TOF2.Q,) == __BOOL_LITERAL(FALSE))) && (__GET_VAR(data__->IN2,) == __BOOL_LITERAL(FALSE)))) {
    __SET_VAR(data__->,STARTED_TIMER_2,,__BOOL_LITERAL(FALSE));
    __SET_VAR(data__->,TIMER_2_INPUT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,OUT1,,__GET_VAR(data__->TOF1.Q,));
  __SET_VAR(data__->,OUT2,,__GET_VAR(data__->TOF2.Q,));
  __SET_VAR(data__->,OUT3,,__GET_VAR(data__->IN3,));

  goto __end;

__end:
  return;
} // PT2_body__() 





void PROGRAM0_init__(PROGRAM0 *data__, BOOL retain) {
  __INIT_VAR(data__->BUTTON,__BOOL_LITERAL(FALSE),retain)
  __INIT_LOCATED(BOOL,__QX0_0,data__->TIMER_OUT,retain)
  __INIT_LOCATED_VALUE(data__->TIMER_OUT,__BOOL_LITERAL(FALSE))
  __INIT_VAR(data__->COUNTER_VALUE,0,retain)
  PT2_init__(&data__->PT20,retain);
}

// Code part
void PROGRAM0_body__(PROGRAM0 *data__) {
  // Initialise TEMP variables

  __SET_VAR(data__->PT20.,IN1,,__GET_VAR(data__->BUTTON,));
  PT2_body__(&data__->PT20);
  __SET_LOCATED(data__->,TIMER_OUT,,__GET_VAR(data__->PT20.OUT1,));

  goto __end;

__end:
  return;
} // PROGRAM0_body__() 





