#include "POUS.h"

void BLINK_init__(BLINK *data__, BOOL retain) {
  __INIT_LOCATED(BOOL,__IX0_0,data__->ACCESO,retain)
  __INIT_LOCATED_VALUE(data__->ACCESO,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__QX0_0,data__->LED1,retain)
  __INIT_LOCATED_VALUE(data__->LED1,__BOOL_LITERAL(FALSE))
  __INIT_LOCATED(BOOL,__QX0_4,data__->LED2,retain)
  __INIT_LOCATED_VALUE(data__->LED2,__BOOL_LITERAL(FALSE))
  __INIT_VAR(data__->VALORE,30000,retain)
  __INIT_LOCATED(WORD,__IW0,data__->ANALOGICA,retain)
  __INIT_LOCATED_VALUE(data__->ANALOGICA,0)
  __INIT_VAR(data__->_TMP_GT12_OUT,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void BLINK_body__(BLINK *data__) {
  // Initialise TEMP variables

  __SET_LOCATED(data__->,LED1,,__GET_LOCATED(data__->ACCESO,));
  __SET_VAR(data__->,_TMP_GT12_OUT,,GT__BOOL__WORD(
    (BOOL)__BOOL_LITERAL(TRUE),
    NULL,
    (UINT)2,
    (WORD)__GET_LOCATED(data__->ANALOGICA,),
    (WORD)__GET_VAR(data__->VALORE,)));
  __SET_LOCATED(data__->,LED2,,__GET_VAR(data__->_TMP_GT12_OUT,));

  goto __end;

__end:
  return;
} // BLINK_body__() 





