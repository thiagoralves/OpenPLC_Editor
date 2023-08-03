
// FUNCTION_BLOCK ADC_CONFIG
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,ADC_CH)
  __DECLARE_VAR(SINT,ADC_TYPE)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,ADC_CH_LOCAL)
  __DECLARE_VAR(SINT,ADC_TYPE_LOCAL)

} ADC_CONFIG;

static void ADC_CONFIG_init__(ADC_CONFIG *data__, BOOL retain);
// Code part
static void ADC_CONFIG_body__(ADC_CONFIG *data__);
static void ADC_CONFIG_init__(ADC_CONFIG *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ADC_CH,0,retain)
  __INIT_VAR(data__->ADC_TYPE,0,retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ADC_CH_LOCAL,0,retain)
  __INIT_VAR(data__->ADC_TYPE_LOCAL,0,retain)
}

// External C Functions
uint8_t ADC_configure_channel(uint8_t adc_ch, uint8_t adc_type);

// Code part
static void ADC_CONFIG_body__(ADC_CONFIG *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if (((__GET_VAR(data__->ADC_CH,) != __GET_VAR(data__->ADC_CH_LOCAL,)) || (__GET_VAR(data__->ADC_TYPE,) != __GET_VAR(data__->ADC_TYPE_LOCAL,)))) {
    __SET_VAR(data__->,ADC_CH_LOCAL,,__GET_VAR(data__->ADC_CH,));
    __SET_VAR(data__->,ADC_TYPE_LOCAL,,__GET_VAR(data__->ADC_TYPE,));
    uint8_t adc_ret = ADC_configure_channel(__GET_VAR(data__->ADC_CH,), __GET_VAR(data__->ADC_TYPE,));
    if (adc_ret == 0)
    {
      __SET_VAR(data__->,SUCCESS,,__BOOL_LITERAL(FALSE));
    }
    else
    {
      __SET_VAR(data__->,SUCCESS,,__BOOL_LITERAL(TRUE));
    }
  }

  goto __end;

__end:
  return;
} // ADC_CONFIG_body__() 





