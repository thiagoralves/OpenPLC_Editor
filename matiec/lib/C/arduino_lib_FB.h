/************************************************************************
 *               DECLARATION OF ARDUINO LIB BLOCKS                      *
************************************************************************/

// READ_DS18B20
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT)

  // FB private variables - TEMP, private and located variables

} DS18B20;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)

  // FB private variables - TEMP, private and located variables

} DS18B20_2_OUT;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  __DECLARE_VAR(REAL,OUT_2)

  // FB private variables - TEMP, private and located variables

} DS18B20_3_OUT;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  __DECLARE_VAR(REAL,OUT_2)
  __DECLARE_VAR(REAL,OUT_3)

  // FB private variables - TEMP, private and located variables

} DS18B20_4_OUT;
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,PIN)
  __DECLARE_VAR(REAL,OUT_0)
  __DECLARE_VAR(REAL,OUT_1)
  __DECLARE_VAR(REAL,OUT_2)
  __DECLARE_VAR(REAL,OUT_3)
  __DECLARE_VAR(REAL,OUT_4)

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
  __DECLARE_VAR(DINT,DINT_VAR)
  __DECLARE_VAR(BOOL,SUCCESS)

  // FB private variables - TEMP, private and located variables

} CLOUD_ADD_DINT;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(STRING,VAR_NAME)
  __DECLARE_VAR(REAL,REAL_VAR)
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

// ARDUINOCAN

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(SINT,EN_PIN)
  __DECLARE_VAR(LINT,BR)
  __DECLARE_VAR(BOOL,DONE) 
  // FB private variables - TEMP, private and located variables
} ARDUINOCAN_CONF;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(DWORD,ID)
  __DECLARE_VAR(USINT,D0)
  __DECLARE_VAR(USINT,D1)
  __DECLARE_VAR(USINT,D2)
  __DECLARE_VAR(USINT,D3)
  __DECLARE_VAR(USINT,D4)
  __DECLARE_VAR(USINT,D5)
  __DECLARE_VAR(USINT,D6)
  __DECLARE_VAR(USINT,D7)
  __DECLARE_VAR(BOOL,DONE) 
  // FB private variables - TEMP, private and located variables
} ARDUINOCAN_WRITE;

typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(DWORD,ID)
  __DECLARE_VAR(LWORD,DATA)
  __DECLARE_VAR(BOOL,DONE) 
  // FB private variables - TEMP, private and located variables
} ARDUINOCAN_WRITE_WORD;


typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,SETUP_BLOCK)
  __DECLARE_VAR(LWORD,DATA)
 
  // FB private variables - TEMP, private and located variables
} ARDUINOCAN_READ;

/************************************************************************
 *                     END OF ARDUINO LIB BLOCKS                        *
************************************************************************/

/************************************************************************
 *               DECLARATION OF ARDUINO LIB BLOCKS                      *
************************************************************************/

static void DS18B20_init__(DS18B20 *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
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
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,OUT,,0);

  goto __end;

__end:
  return;
} // READ_DS18B20_body__()

static void DS18B20_2_OUT_init__(DS18B20_2_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
}

// Code part
static void DS18B20_2_OUT_body__(DS18B20_2_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,OUT_0,,0);
  __SET_VAR(data__->,OUT_1,,0);

  goto __end;

__end:
  return;
} // READ_DS18B20_body__()

static void DS18B20_3_OUT_init__(DS18B20_3_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
  __INIT_VAR(data__->OUT_2,0.0,retain)
}

// Code part
static void DS18B20_3_OUT_body__(DS18B20_3_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,OUT_0,,0);
  __SET_VAR(data__->,OUT_1,,0);
  __SET_VAR(data__->,OUT_2,,0);

  goto __end;

__end:
  return;
} // READ_DS18B20_body__()

static void DS18B20_4_OUT_init__(DS18B20_4_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
  __INIT_VAR(data__->OUT_2,0.0,retain)
  __INIT_VAR(data__->OUT_3,0.0,retain)
}

// Code part
static void DS18B20_4_OUT_body__(DS18B20_4_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,OUT_0,,0);
  __SET_VAR(data__->,OUT_1,,0);
  __SET_VAR(data__->,OUT_2,,0);
  __SET_VAR(data__->,OUT_3,,0);

  goto __end;

__end:
  return;
} // READ_DS18B20_body__()

static void DS18B20_5_OUT_init__(DS18B20_5_OUT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->PIN,0,retain)
  __INIT_VAR(data__->OUT_0,0.0,retain)
  __INIT_VAR(data__->OUT_1,0.0,retain)
  __INIT_VAR(data__->OUT_2,0.0,retain)
  __INIT_VAR(data__->OUT_3,0.0,retain)
  __INIT_VAR(data__->OUT_4,0.0,retain)
}

// Code part
static void DS18B20_5_OUT_body__(DS18B20_5_OUT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,OUT_0,,0);
  __SET_VAR(data__->,OUT_1,,0);
  __SET_VAR(data__->,OUT_2,,0);
  __SET_VAR(data__->,OUT_3,,0);
  __SET_VAR(data__->,OUT_4,,0);

  goto __end;

__end:
  return;
} // READ_DS18B20_body__()

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
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,SUCCESS,,0);
  
  goto __end;

__end:
  return;
} // CLOUD_ADD_BOOL_body__()

static void CLOUD_ADD_DINT_init__(CLOUD_ADD_DINT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->VAR_NAME,__STRING_LITERAL(1,"\0"),retain)
  __INIT_VAR(data__->DINT_VAR,0,retain)
  __INIT_VAR(data__->SUCCESS,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void CLOUD_ADD_DINT_body__(CLOUD_ADD_DINT *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,SUCCESS,,0);
  
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
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,SUCCESS,,0);
  
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
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,SUCCESS,,0);
  
  goto __end;

__end:
  return;
} // CLOUD_BEGIN_body__()


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


//Init 
//definition of blocks
static void ARDUINOCAN_CONF_init__(ARDUINOCAN_CONF *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->EN_PIN,0,retain)
  __INIT_VAR(data__->BR,250000,retain)
  __INIT_VAR(data__->DONE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void ARDUINOCAN_CONF_body__(ARDUINOCAN_CONF *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // // Initialise TEMP variables
  if (!__GET_VAR(data__->SETUP_BLOCK)) {
      __SET_VAR(data__->,SETUP_BLOCK,,__BOOL_LITERAL(FALSE));
      __SET_VAR(data__->,DONE,,__BOOL_LITERAL(FALSE));
  }
  goto __end;

__end:
  return;
  }

// write single byte
//definition of blocks
static void ARDUINOCAN_WRITE_init__(ARDUINOCAN_WRITE *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
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
static void ARDUINOCAN_WRITE_body__(ARDUINOCAN_WRITE *data__) {
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


// write paylod in word
//definition of blocks
static void ARDUINOCAN_WRITE_WORD_init__(ARDUINOCAN_WRITE_WORD *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ID,0,retain)
  __INIT_VAR(data__->DATA,0,retain)
  __INIT_VAR(data__->DONE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
static void ARDUINOCAN_WRITE_WORD_body__(ARDUINOCAN_WRITE_WORD *data__) {
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
static void ARDUINOCAN_READ_init__(ARDUINOCAN_READ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SETUP_BLOCK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->DATA,0,retain)
}
// Code part
static void ARDUINOCAN_READ_body__(ARDUINOCAN_READ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }

  __SET_VAR(data__->,DATA,,__BOOL_LITERAL(FALSE));


  goto __end;

__end:
  return;
 }
/************************************************************************
 *                     END OF ARDUINO LIB BLOCKS                        *
************************************************************************/
