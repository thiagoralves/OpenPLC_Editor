/************************************************************************
 *                  DECLARATION OF P1AM LIB BLOCKS                      *
************************************************************************/
// P1AM_INIT
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(BOOL,INIT)
  __DECLARE_VAR(SINT,SUCCESS)

  // FB private variables - TEMP, private and located variables

} P1AM_INIT;

// P1_16CDR
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,SLOT)
  __DECLARE_VAR(BOOL,O1)
  __DECLARE_VAR(BOOL,O2)
  __DECLARE_VAR(BOOL,O3)
  __DECLARE_VAR(BOOL,O4)
  __DECLARE_VAR(BOOL,O5)
  __DECLARE_VAR(BOOL,O6)
  __DECLARE_VAR(BOOL,O7)
  __DECLARE_VAR(BOOL,O8)
  __DECLARE_VAR(BOOL,I1)
  __DECLARE_VAR(BOOL,I2)
  __DECLARE_VAR(BOOL,I3)
  __DECLARE_VAR(BOOL,I4)
  __DECLARE_VAR(BOOL,I5)
  __DECLARE_VAR(BOOL,I6)
  __DECLARE_VAR(BOOL,I7)
  __DECLARE_VAR(BOOL,I8)

  // FB private variables - TEMP, private and located variables

} P1_16CDR;

// P1_08N
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,SLOT)
  __DECLARE_VAR(BOOL,I1)
  __DECLARE_VAR(BOOL,I2)
  __DECLARE_VAR(BOOL,I3)
  __DECLARE_VAR(BOOL,I4)
  __DECLARE_VAR(BOOL,I5)
  __DECLARE_VAR(BOOL,I6)
  __DECLARE_VAR(BOOL,I7)
  __DECLARE_VAR(BOOL,I8)

  // FB private variables - TEMP, private and located variables

} P1_08N;

// P1_16N
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,SLOT)
  __DECLARE_VAR(BOOL,I1)
  __DECLARE_VAR(BOOL,I2)
  __DECLARE_VAR(BOOL,I3)
  __DECLARE_VAR(BOOL,I4)
  __DECLARE_VAR(BOOL,I5)
  __DECLARE_VAR(BOOL,I6)
  __DECLARE_VAR(BOOL,I7)
  __DECLARE_VAR(BOOL,I8)
  __DECLARE_VAR(BOOL,I9)
  __DECLARE_VAR(BOOL,I10)
  __DECLARE_VAR(BOOL,I11)
  __DECLARE_VAR(BOOL,I12)
  __DECLARE_VAR(BOOL,I13)
  __DECLARE_VAR(BOOL,I14)
  __DECLARE_VAR(BOOL,I15)
  __DECLARE_VAR(BOOL,I16)

  // FB private variables - TEMP, private and located variables

} P1_16N;

// P1_08T
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,SLOT)
  __DECLARE_VAR(BOOL,O1)
  __DECLARE_VAR(BOOL,O2)
  __DECLARE_VAR(BOOL,O3)
  __DECLARE_VAR(BOOL,O4)
  __DECLARE_VAR(BOOL,O5)
  __DECLARE_VAR(BOOL,O6)
  __DECLARE_VAR(BOOL,O7)
  __DECLARE_VAR(BOOL,O8)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,DUMMY)

} P1_08T;

// P1_16TR
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,SLOT)
  __DECLARE_VAR(BOOL,O1)
  __DECLARE_VAR(BOOL,O2)
  __DECLARE_VAR(BOOL,O3)
  __DECLARE_VAR(BOOL,O4)
  __DECLARE_VAR(BOOL,O5)
  __DECLARE_VAR(BOOL,O6)
  __DECLARE_VAR(BOOL,O7)
  __DECLARE_VAR(BOOL,O8)
  __DECLARE_VAR(BOOL,O9)
  __DECLARE_VAR(BOOL,O10)
  __DECLARE_VAR(BOOL,O11)
  __DECLARE_VAR(BOOL,O12)
  __DECLARE_VAR(BOOL,O13)
  __DECLARE_VAR(BOOL,O14)
  __DECLARE_VAR(BOOL,O15)
  __DECLARE_VAR(BOOL,O16)

  // FB private variables - TEMP, private and located variables
  __DECLARE_VAR(SINT,DUMMY)

} P1_16TR;

// P1_04AD
// Data part
typedef struct {
  // FB Interface - IN, OUT, IN_OUT variables
  __DECLARE_VAR(BOOL,EN)
  __DECLARE_VAR(BOOL,ENO)
  __DECLARE_VAR(SINT,SLOT)
  __DECLARE_VAR(UINT,I1)
  __DECLARE_VAR(UINT,I2)
  __DECLARE_VAR(UINT,I3)
  __DECLARE_VAR(UINT,I4)

  // FB private variables - TEMP, private and located variables

} P1_04AD;
/************************************************************************
 *                      END OF P1AM LIB BLOCKS                          *
************************************************************************/

/************************************************************************
 *                  DECLARATION OF P1AM LIB BLOCKS                      *
************************************************************************/
static void P1AM_INIT_init__(P1AM_INIT *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->INIT,0,retain)
  __INIT_VAR(data__->SUCCESS,0,retain)
}

// Code part
static void P1AM_INIT_body__(P1AM_INIT *data__) {
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
} // P1AM_INIT_body__()

static void P1_16CDR_init__(P1_16CDR *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SLOT,0,retain)
  __INIT_VAR(data__->O1,0,retain)
  __INIT_VAR(data__->O2,0,retain)
  __INIT_VAR(data__->O3,0,retain)
  __INIT_VAR(data__->O4,0,retain)
  __INIT_VAR(data__->O5,0,retain)
  __INIT_VAR(data__->O6,0,retain)
  __INIT_VAR(data__->O7,0,retain)
  __INIT_VAR(data__->O8,0,retain)
  __INIT_VAR(data__->I1,0,retain)
  __INIT_VAR(data__->I2,0,retain)
  __INIT_VAR(data__->I3,0,retain)
  __INIT_VAR(data__->I4,0,retain)
  __INIT_VAR(data__->I5,0,retain)
  __INIT_VAR(data__->I6,0,retain)
  __INIT_VAR(data__->I7,0,retain)
  __INIT_VAR(data__->I8,0,retain)
}

// Code part
static void P1_16CDR_body__(P1_16CDR *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,I1,,0);

  goto __end;

__end:
  return;
} // P1_16CDR_body__()


static void P1_08N_init__(P1_08N *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SLOT,0,retain)
  __INIT_VAR(data__->I1,0,retain)
  __INIT_VAR(data__->I2,0,retain)
  __INIT_VAR(data__->I3,0,retain)
  __INIT_VAR(data__->I4,0,retain)
  __INIT_VAR(data__->I5,0,retain)
  __INIT_VAR(data__->I6,0,retain)
  __INIT_VAR(data__->I7,0,retain)
  __INIT_VAR(data__->I8,0,retain)
}

// Code part
static void P1_08N_body__(P1_08N *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside p1am_FB.h file on arduino folder
  __SET_VAR(data__->,I1,,0);

  goto __end;

__end:
  return;
} // P1_08N_body__()


static void P1_16N_init__(P1_16N *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SLOT,0,retain)
  __INIT_VAR(data__->I1,0,retain)
  __INIT_VAR(data__->I2,0,retain)
  __INIT_VAR(data__->I3,0,retain)
  __INIT_VAR(data__->I4,0,retain)
  __INIT_VAR(data__->I5,0,retain)
  __INIT_VAR(data__->I6,0,retain)
  __INIT_VAR(data__->I7,0,retain)
  __INIT_VAR(data__->I8,0,retain)
  __INIT_VAR(data__->I9,0,retain)
  __INIT_VAR(data__->I10,0,retain)
  __INIT_VAR(data__->I11,0,retain)
  __INIT_VAR(data__->I12,0,retain)
  __INIT_VAR(data__->I13,0,retain)
  __INIT_VAR(data__->I14,0,retain)
  __INIT_VAR(data__->I15,0,retain)
  __INIT_VAR(data__->I16,0,retain)
}

// Code part
static void P1_16N_body__(P1_16N *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside p1am_FB.h file on arduino folder
  __SET_VAR(data__->,I1,,0);

  goto __end;

__end:
  return;
} // P1_16N_body__()


static void P1_08T_init__(P1_08T *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SLOT,0,retain)
  __INIT_VAR(data__->DUMMY,0,retain)
  __INIT_VAR(data__->O1,0,retain)
  __INIT_VAR(data__->O2,0,retain)
  __INIT_VAR(data__->O3,0,retain)
  __INIT_VAR(data__->O4,0,retain)
  __INIT_VAR(data__->O5,0,retain)
  __INIT_VAR(data__->O6,0,retain)
  __INIT_VAR(data__->O7,0,retain)
  __INIT_VAR(data__->O8,0,retain)
}

// Code part
static void P1_08T_body__(P1_08T *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,DUMMY,,0);

  goto __end;

__end:
  return;
} // P1_08T_body__()


static void P1_16TR_init__(P1_16TR *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SLOT,0,retain)
  __INIT_VAR(data__->DUMMY,0,retain)
  __INIT_VAR(data__->O1,0,retain)
  __INIT_VAR(data__->O2,0,retain)
  __INIT_VAR(data__->O3,0,retain)
  __INIT_VAR(data__->O4,0,retain)
  __INIT_VAR(data__->O5,0,retain)
  __INIT_VAR(data__->O6,0,retain)
  __INIT_VAR(data__->O7,0,retain)
  __INIT_VAR(data__->O8,0,retain)
  __INIT_VAR(data__->O9,0,retain)
  __INIT_VAR(data__->O10,0,retain)
  __INIT_VAR(data__->O11,0,retain)
  __INIT_VAR(data__->O12,0,retain)
  __INIT_VAR(data__->O13,0,retain)
  __INIT_VAR(data__->O14,0,retain)
  __INIT_VAR(data__->O15,0,retain)
  __INIT_VAR(data__->O16,0,retain)
}

// Code part
static void P1_16TR_body__(P1_16TR *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside iec_std_FB.h file on arduino folder
  __SET_VAR(data__->,DUMMY,,0);

  goto __end;

__end:
  return;
} // P1_16TR_body__()


static void P1_04AD_init__(P1_04AD *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->SLOT,0,retain)
  __INIT_VAR(data__->I1,0,retain)
  __INIT_VAR(data__->I2,0,retain)
  __INIT_VAR(data__->I3,0,retain)
  __INIT_VAR(data__->I4,0,retain)
}

// Code part
static void P1_04AD_body__(P1_04AD *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Dummy code - just for editor simulation. Real code is inside p1am_FB.h file on arduino folder
  __SET_VAR(data__->,I1,,0);

  goto __end;

__end:
  return;
} // P1_08N_body__()
/************************************************************************
 *                      END OF P1AM LIB BLOCKS                          *
************************************************************************/
