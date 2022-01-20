/************************************************************************
 *               DECLARATION OF ARDUINO LIB BLOCKS                      *
************************************************************************/

// READ_DS18B20
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT)
  void *class_pointer;

  // FB private variables - TEMP, private and located variables

} DS18B20;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  void *class_pointer;

  // FB private variables - TEMP, private and located variables

} DS18B20_2_OUT;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  __DECLARE_VAR(REAL,OUT_2)
  void *class_pointer;

  // FB private variables - TEMP, private and located variables

} DS18B20_3_OUT;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  __DECLARE_VAR(REAL,OUT_2)
  __DECLARE_VAR(REAL,OUT_3)
  void *class_pointer;

  // FB private variables - TEMP, private and located variables

} DS18B20_4_OUT;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  __DECLARE_VAR(REAL,OUT_2)
  __DECLARE_VAR(REAL,OUT_3)
  __DECLARE_VAR(REAL,OUT_4)
  void *class_pointer;

  // FB private variables - TEMP, private and located variables

} DS18B20_5_OUT;

// ARDUINO_CLOUD_ADD_BOOL
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,VAR_NAME)
  __DECLARE_VAR(BOOL,BOOL_VAR)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables

} CLOUD_ADD_BOOL;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,VAR_NAME)
  __DECLARE_VAR(BOOL,INT_VAR)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables

} CLOUD_ADD_INT;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,VAR_NAME)
  __DECLARE_VAR(BOOL,REAL_VAR)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables

} CLOUD_ADD_REAL;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,THING_ID)
  __DECLARE_VAR(STRING,SSID)
  __DECLARE_VAR(STRING,PASS)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables

} CLOUD_BEGIN;

/************************************************************************
 *                     END OF ARDUINO LIB BLOCKS                        *
************************************************************************/

/************************************************************************
 *               DECLARATION OF ARDUINO LIB BLOCKS                      *
************************************************************************/
/************************************************************************
 *                            DS18B20                                   *
************************************************************************/
//definition of external functions
void *init_ds18b20(uint8_t);
float read_ds18b20(void *, uint8_t);
void request_ds18b20_temperatures(void *);

//definition of blocks
static void DS18B20_init__(DS18B20 *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT,0.0,retain)
}

// Code part
static void DS18B20_body__(DS18B20 *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables
  if (!__GET_VAR(data__->SETUP_BLOCK)) {
      (*data__).class_pointer = init_ds18b20((uint8_t)__GET_VAR(data__->PIN));
      __SET_VAR(data__->,SETUP_BLOCK,,__BOOL_LITERAL(TRUE));
  }
  request_ds18b20_temperatures((*data__).class_pointer);
  __SET_VAR(data__->,OUT,,read_ds18b20((*data__).class_pointer, 0));

  goto __end;

__end:
  return;
} // READ_DS18B20_body__() 
static void DS18B20_2_OUT_init__(DS18B20_2_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
}
static void DS18B20_2_OUT_body__(DS18B20_2_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables
  if (!__GET_VAR(data__->SETUP_BLOCK)) {
      (*data__).class_pointer = init_ds18b20((uint8_t)__GET_VAR(data__->PIN));
      __SET_VAR(data__->,SETUP_BLOCK,,__BOOL_LITERAL(TRUE));
  }
  request_ds18b20_temperatures((*data__).class_pointer);
  __SET_VAR(data__->,OUT_0,,read_ds18b20((*data__).class_pointer, 0));
  __SET_VAR(data__->,OUT_1,,read_ds18b20((*data__).class_pointer, 1));

  goto __end;

__end:
  return;
} // READ_DS18B20_body__() 
static void DS18B20_3_OUT_init__(DS18B20_3_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
  __INIT_VAR(data__->OUT_2,0.0,retain)
}
static void DS18B20_3_OUT_body__(DS18B20_3_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables
  if (!__GET_VAR(data__->SETUP_BLOCK)) {
      (*data__).class_pointer = init_ds18b20((uint8_t)__GET_VAR(data__->PIN));
      __SET_VAR(data__->,SETUP_BLOCK,,__BOOL_LITERAL(TRUE));
  }
  request_ds18b20_temperatures((*data__).class_pointer);
  __SET_VAR(data__->,OUT_0,,read_ds18b20((*data__).class_pointer, 0));
  __SET_VAR(data__->,OUT_1,,read_ds18b20((*data__).class_pointer, 1));
  __SET_VAR(data__->,OUT_2,,read_ds18b20((*data__).class_pointer, 2));

  goto __end;

__end:
  return;
} // READ_DS18B20_body__() 
static void DS18B20_4_OUT_init__(DS18B20_4_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
  __INIT_VAR(data__->OUT_2,0.0,retain)
  __INIT_VAR(data__->OUT_3,0.0,retain)
}
static void DS18B20_4_OUT_body__(DS18B20_4_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables
  if (!__GET_VAR(data__->SETUP_BLOCK)) {
      (*data__).class_pointer = init_ds18b20((uint8_t)__GET_VAR(data__->PIN));
      __SET_VAR(data__->,SETUP_BLOCK,,__BOOL_LITERAL(TRUE));
  }
  request_ds18b20_temperatures((*data__).class_pointer);
  __SET_VAR(data__->,OUT_0,,read_ds18b20((*data__).class_pointer, 0));
  __SET_VAR(data__->,OUT_1,,read_ds18b20((*data__).class_pointer, 1));
  __SET_VAR(data__->,OUT_2,,read_ds18b20((*data__).class_pointer, 2));
  __SET_VAR(data__->,OUT_3,,read_ds18b20((*data__).class_pointer, 3));

  goto __end;

__end:
  return;
} // READ_DS18B20_body__() 
static void DS18B20_5_OUT_init__(DS18B20_5_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
  __INIT_VAR(data__->OUT_2,0.0,retain)
  __INIT_VAR(data__->OUT_3,0.0,retain)
  __INIT_VAR(data__->OUT_4,0.0,retain)
}
static void DS18B20_5_OUT_body__(DS18B20_5_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables
  if (!__GET_VAR(data__->SETUP_BLOCK)) {
      (*data__).class_pointer = init_ds18b20((uint8_t)__GET_VAR(data__->PIN));
      __SET_VAR(data__->,SETUP_BLOCK,,__BOOL_LITERAL(TRUE));
  }
  request_ds18b20_temperatures((*data__).class_pointer);
  __SET_VAR(data__->,OUT_0,,read_ds18b20((*data__).class_pointer, 0));
  __SET_VAR(data__->,OUT_1,,read_ds18b20((*data__).class_pointer, 1));
  __SET_VAR(data__->,OUT_2,,read_ds18b20((*data__).class_pointer, 2));
  __SET_VAR(data__->,OUT_3,,read_ds18b20((*data__).class_pointer, 3));
  __SET_VAR(data__->,OUT_4,,read_ds18b20((*data__).class_pointer, 4));

  goto __end;

__end:
  return;
} // READ_DS18B20_body__() 

/************************************************************************
 *                         ARDUINO_CLOUD                                *
************************************************************************/
//definition of external functions
void cloud_begin(char *, char *, char *);
void cloud_add_bool(char *, char *);
void cloud_add_int(char *, int *);
void cloud_add_float(char *, float *);

static void CLOUD_ADD_BOOL_init__(CLOUD_ADD_BOOL *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->VAR_NAME,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->BOOL_VAR,0,retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void CLOUD_ADD_BOOL_body__(CLOUD_ADD_BOOL *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  
  if (!__GET_VAR(data__->SUCCESS))
  {
    cloud_add_bool(__GET_VAR(data__->VAR_NAME).body, &__GET_VAR(data__->BOOL_VAR));
    __SET_VAR(data__->,SUCCESS,,1);
  }
  
  goto __end;

__end:
  return;
} // CLOUD_ADD_BOOL_body__()

static void CLOUD_ADD_INT_init__(CLOUD_ADD_INT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->VAR_NAME,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->INT_VAR,0,retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void CLOUD_ADD_INT_body__(CLOUD_ADD_INT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  
  if (!__GET_VAR(data__->SUCCESS))
  {
    cloud_add_int(__GET_VAR(data__->VAR_NAME).body, &__GET_VAR(data__->INT_VAR));
    __SET_VAR(data__->,SUCCESS,,1);
  }
  
  goto __end;

__end:
  return;
} // CLOUD_ADD_INT_body__()

static void CLOUD_ADD_REAL_init__(CLOUD_ADD_REAL *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->VAR_NAME,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->REAL_VAR,0.0,retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void CLOUD_ADD_REAL_body__(CLOUD_ADD_REAL *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  
  if (!__GET_VAR(data__->SUCCESS))
  {
    cloud_add_float(__GET_VAR(data__->VAR_NAME).body, &__GET_VAR(data__->REAL_VAR));
    __SET_VAR(data__->,SUCCESS,,1);
  }
  
  goto __end;

__end:
  return;
} // CLOUD_ADD_REAL_body__()

static void CLOUD_BEGIN_init__(CLOUD_BEGIN *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->THING_ID,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->SSID,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->PASS,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void CLOUD_BEGIN_body__(CLOUD_BEGIN *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  
  if (!__GET_VAR(data__->SUCCESS))
  {
    cloud_begin(__GET_VAR(data__->THING_ID).body, __GET_VAR(data__->SSID).body, __GET_VAR(data__->PASS).body);
    __SET_VAR(data__->,SUCCESS,,1);
  }
  
  goto __end;

__end:
  return;
} // CLOUD_BEGIN_body__()

/************************************************************************
 *                     END OF ARDUINO LIB BLOCKS                        *
************************************************************************/