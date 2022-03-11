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

/************************************************************************
 *                     END OF ARDUINO LIB BLOCKS                        *
************************************************************************/