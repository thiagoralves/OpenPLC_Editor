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

static void STM32CAN_CONF_init__(STM32CAN_CONF *data__, BOOL retain);

static void STM32CAN_CONF_body__(STM32CAN_CONF *data__);

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

static void STM32CAN_WRITE_init__(STM32CAN_WRITE *data__, BOOL retain);

static void STM32CAN_WRITE_body__(STM32CAN_WRITE *data__);

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


uint8_t init_stm32can(int);
uint8_t write_stm32can(uint8_t,uint32_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t);
uint8_t read_stm32can(uint32_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*, uint8_t*);


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
  
  if(__GET_VAR(data__->CONF)){
  
  __SET_VAR(data__->,DONE,,init_stm32can(__GET_VAR(data__->BR)));
  
  }
  
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
  uint8_t write_done = 0;
  if (__GET_VAR(data__->EN_PIN)){
	  
	write_done = write_stm32can(__GET_VAR(data__->CH),__GET_VAR(data__->ID),__GET_VAR(data__->D0),
		__GET_VAR(data__->D1), __GET_VAR(data__->D2),__GET_VAR(data__->D3),
			__GET_VAR(data__->D4), __GET_VAR(data__->D5),__GET_VAR(data__->D6),
				__GET_VAR(data__->D7));		
				
  }
  __SET_VAR(data__->,DONE,,write_done);
  
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
  
  uint32_t id = 0;
  uint8_t d0 = 0;
  uint8_t d1 = 0;
  uint8_t d2 = 0;
  uint8_t d3 = 0;
  uint8_t d4 = 0;
  uint8_t d5 = 0;
  uint8_t d6 = 0;
  uint8_t d7 = 0;
  uint8_t read_done = 0;
  
  if (__GET_VAR(data__->EN_PIN)){
	  read_done = read_stm32can(&id,&d0,&d1,&d2,&d3,&d4,&d5,&d6,&d7);
	  
  }
  __SET_VAR(data__->,ID,,id);
  __SET_VAR(data__->,D0,,d0);
  __SET_VAR(data__->,D1,,d1);
  __SET_VAR(data__->,D2,,d2);
  __SET_VAR(data__->,D3,,d3);
  __SET_VAR(data__->,D4,,d4);
  __SET_VAR(data__->,D5,,d5);
  __SET_VAR(data__->,D6,,d6);
  __SET_VAR(data__->,D7,,d7);
  __SET_VAR(data__->,DONE,,read_done);
  goto __end;

__end:
  return;
 }