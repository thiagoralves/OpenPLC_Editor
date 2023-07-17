
// FUNCTION_BLOCK PWM_CONTROLLER
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,CHANNEL)
  __DECLARE_VAR(REAL,FREQ)
  __DECLARE_VAR(REAL,DUTY)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,INTERNAL_CH)
  __DECLARE_VAR(REAL,INTERNAL_FREQ)
  __DECLARE_VAR(REAL,INTERNAL_DUTY)

} PWM_CONTROLLER;

static void PWM_CONTROLLER_init__(PWM_CONTROLLER *data__, BOOL retain);
// Code part
static void PWM_CONTROLLER_body__(PWM_CONTROLLER *data__);
static void PWM_CONTROLLER_init__(PWM_CONTROLLER *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CHANNEL,0,retain)
  __INIT_VAR(data__->FREQ,0,retain)
  __INIT_VAR(data__->DUTY,0,retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->INTERNAL_CH,0,retain)
  __INIT_VAR(data__->INTERNAL_FREQ,0,retain)
  __INIT_VAR(data__->INTERNAL_DUTY,0,retain)
}

// Code part
static void PWM_CONTROLLER_body__(PWM_CONTROLLER *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_VAR(data__->CHANNEL,) < 1)) {
    __SET_VAR(data__->,SUCCESS,,__BOOL_LITERAL(FALSE));
    goto __end;
  };
  if ((((__GET_VAR(data__->CHANNEL,) != __GET_VAR(data__->INTERNAL_CH,)) || (__GET_VAR(data__->FREQ,) != __GET_VAR(data__->INTERNAL_FREQ,))) || (__GET_VAR(data__->DUTY,) != __GET_VAR(data__->INTERNAL_DUTY,)))) {
    __SET_VAR(data__->,SUCCESS,,__BOOL_LITERAL(TRUE));
  };

  goto __end;

__end:
  return;
} // PWM_CONTROLLER_body__() 





