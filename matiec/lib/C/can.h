//my_custom_library.h – this file contains the C code for the TEST block defined in the “My Custom Library”

// STM32CAN

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,CONF)
  __DECLARE_VAR(LINT,BR)
  __DECLARE_VAR(BOOL,DONE) 
  // FB private variables - TEMP, private and located variables
} STM32CAN_CONF;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,EN_PIN)
  __DECLARE_VAR(USINT,CH)
  __DECLARE_VAR(DWORD,ID)
  __DECLARE_VAR(BYTE,D0)
  __DECLARE_VAR(BYTE,D1)
  __DECLARE_VAR(BYTE,D2)
  __DECLARE_VAR(BYTE,D3)
  __DECLARE_VAR(BYTE,D4)
  __DECLARE_VAR(BYTE,D5)
  __DECLARE_VAR(BYTE,D6)
  __DECLARE_VAR(BYTE,D7)
  __DECLARE_VAR(BOOL,DONE) 
  // FB private variables - TEMP, private and located variables
} STM32CAN_WRITE;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,EN_PIN)
  __DECLARE_VAR(DWORD,ID)
  __DECLARE_VAR(BYTE,D0)
  __DECLARE_VAR(BYTE,D1)
  __DECLARE_VAR(BYTE,D2)
  __DECLARE_VAR(BYTE,D3)
  __DECLARE_VAR(BYTE,D4)
  __DECLARE_VAR(BYTE,D5)
  __DECLARE_VAR(BYTE,D6)
  __DECLARE_VAR(BYTE,D7)
  __DECLARE_VAR(BOOL,DONE) 
 
  // FB private variables - TEMP, private and located variables
} STM32CAN_READ;


//definition of blocks
static void STM32CAN_CONF_init__(STM32CAN_CONF *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CONF,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->BR,250000,retain)
  __INIT_VAR(data__->DONE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void STM32CAN_CONF_body__(STM32CAN_CONF *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }

  __SET_VAR(data__->,DONE,,__BOOL_LITERAL(TRUE));

  goto __end;

__end:
  return;
  }

// write single byte
//definition of blocks
static void STM32CAN_WRITE_init__(STM32CAN_WRITE *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->EN_PIN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CH,0,retain)
  __INIT_VAR(data__->ID,0,retain)
  __INIT_VAR(data__->D0,0,retain)
  __INIT_VAR(data__->D1,0,retain)
  __INIT_VAR(data__->D2,0,retain)
  __INIT_VAR(data__->D3,0,retain)
  __INIT_VAR(data__->D4,0,retain)
  __INIT_VAR(data__->D5,0,retain)
  __INIT_VAR(data__->D6,0,retain)
  __INIT_VAR(data__->D7,0,retain)
  __INIT_VAR(data__->DONE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void STM32CAN_WRITE_body__(STM32CAN_WRITE *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }

  __SET_VAR(data__->,DONE,,__BOOL_LITERAL(FALSE));
  goto __end;

__end:
  return;
  }

// read
//definition of blocks
static void STM32CAN_READ_init__(STM32CAN_READ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->EN_PIN,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->ID,0,retain)
  __INIT_VAR(data__->D0,0,retain)
  __INIT_VAR(data__->D1,0,retain)
  __INIT_VAR(data__->D2,0,retain)
  __INIT_VAR(data__->D3,0,retain)
  __INIT_VAR(data__->D4,0,retain)
  __INIT_VAR(data__->D5,0,retain)
  __INIT_VAR(data__->D6,0,retain)
  __INIT_VAR(data__->D7,0,retain)
  __INIT_VAR(data__->DONE,__BOOL_LITERAL(FALSE),retain)
}
// Code part
static void STM32CAN_READ_body__(STM32CAN_READ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }

  __SET_VAR(data__->,DONE,,__BOOL_LITERAL(FALSE));
  

  goto __end;

__end:
  return;
 }
