/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

#ifndef YY_YY_IEC_BISON_HH_INCLUDED
# define YY_YY_IEC_BISON_HH_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif
/* "%code requires" blocks.  */
#line 255 "iec_bison.yy"

/* define a new data type to store the locations, so we can also store
 * the filename in which the token is expressed.
 */
/* NOTE: since this code will be placed in the iec_bison.hh header file,
 * as well as the iec.cc file that also includes the iec_bison.hh header file,
 * declaring the typedef struct yyltype__local here would result in a 
 * compilation error when compiling iec.cc, as this struct would be
 * declared twice.
 * We therefore use the #if !defined YYLTYPE ...
 * to make sure only the first declaration is parsed by the C++ compiler.
 */
#if ! defined YYLTYPE && ! defined YYLTYPE_IS_DECLARED
typedef struct YYLTYPE {
    int         first_line;
    int         first_column;
    const char *first_file;
    long int    first_order;
    int         last_line;
    int         last_column;
    const char *last_file;
    long int    last_order;
} YYLTYPE;
#define YYLTYPE_IS_DECLARED 1
#define YYLTYPE_IS_TRIVIAL 0
#endif


#line 78 "iec_bison.hh"

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    END_OF_INPUT = 0,              /* END_OF_INPUT  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    BOGUS_TOKEN_ID = 258,          /* BOGUS_TOKEN_ID  */
    prev_declared_variable_name_token = 259, /* prev_declared_variable_name_token  */
    prev_declared_direct_variable_token = 260, /* prev_declared_direct_variable_token  */
    prev_declared_fb_name_token = 261, /* prev_declared_fb_name_token  */
    prev_declared_simple_type_name_token = 262, /* prev_declared_simple_type_name_token  */
    prev_declared_subrange_type_name_token = 263, /* prev_declared_subrange_type_name_token  */
    prev_declared_enumerated_type_name_token = 264, /* prev_declared_enumerated_type_name_token  */
    prev_declared_array_type_name_token = 265, /* prev_declared_array_type_name_token  */
    prev_declared_structure_type_name_token = 266, /* prev_declared_structure_type_name_token  */
    prev_declared_string_type_name_token = 267, /* prev_declared_string_type_name_token  */
    prev_declared_ref_type_name_token = 268, /* prev_declared_ref_type_name_token  */
    prev_declared_derived_function_name_token = 269, /* prev_declared_derived_function_name_token  */
    prev_declared_derived_function_block_name_token = 270, /* prev_declared_derived_function_block_name_token  */
    prev_declared_program_type_name_token = 271, /* prev_declared_program_type_name_token  */
    start_ST_body_token = 272,     /* start_ST_body_token  */
    start_IL_body_token = 273,     /* start_IL_body_token  */
    disable_code_generation_pragma_token = 274, /* disable_code_generation_pragma_token  */
    enable_code_generation_pragma_token = 275, /* enable_code_generation_pragma_token  */
    pragma_token = 276,            /* pragma_token  */
    EN = 277,                      /* EN  */
    ENO = 278,                     /* ENO  */
    REF = 279,                     /* REF  */
    DREF = 280,                    /* DREF  */
    REF_TO = 281,                  /* REF_TO  */
    NULL_token = 282,              /* NULL_token  */
    identifier_token = 283,        /* identifier_token  */
    integer_token = 284,           /* integer_token  */
    binary_integer_token = 285,    /* binary_integer_token  */
    octal_integer_token = 286,     /* octal_integer_token  */
    hex_integer_token = 287,       /* hex_integer_token  */
    real_token = 288,              /* real_token  */
    safeboolean_true_literal_token = 289, /* safeboolean_true_literal_token  */
    safeboolean_false_literal_token = 290, /* safeboolean_false_literal_token  */
    boolean_true_literal_token = 291, /* boolean_true_literal_token  */
    boolean_false_literal_token = 292, /* boolean_false_literal_token  */
    FALSE = 293,                   /* FALSE  */
    TRUE = 294,                    /* TRUE  */
    single_byte_character_string_token = 295, /* single_byte_character_string_token  */
    double_byte_character_string_token = 296, /* double_byte_character_string_token  */
    fixed_point_token = 297,       /* fixed_point_token  */
    fixed_point_d_token = 298,     /* fixed_point_d_token  */
    integer_d_token = 299,         /* integer_d_token  */
    fixed_point_h_token = 300,     /* fixed_point_h_token  */
    integer_h_token = 301,         /* integer_h_token  */
    fixed_point_m_token = 302,     /* fixed_point_m_token  */
    integer_m_token = 303,         /* integer_m_token  */
    fixed_point_s_token = 304,     /* fixed_point_s_token  */
    integer_s_token = 305,         /* integer_s_token  */
    fixed_point_ms_token = 306,    /* fixed_point_ms_token  */
    integer_ms_token = 307,        /* integer_ms_token  */
    end_interval_token = 308,      /* end_interval_token  */
    erroneous_interval_token = 309, /* erroneous_interval_token  */
    T_SHARP = 310,                 /* T_SHARP  */
    D_SHARP = 311,                 /* D_SHARP  */
    BYTE = 312,                    /* BYTE  */
    WORD = 313,                    /* WORD  */
    DWORD = 314,                   /* DWORD  */
    LWORD = 315,                   /* LWORD  */
    LREAL = 316,                   /* LREAL  */
    REAL = 317,                    /* REAL  */
    SINT = 318,                    /* SINT  */
    INT = 319,                     /* INT  */
    DINT = 320,                    /* DINT  */
    LINT = 321,                    /* LINT  */
    USINT = 322,                   /* USINT  */
    UINT = 323,                    /* UINT  */
    UDINT = 324,                   /* UDINT  */
    ULINT = 325,                   /* ULINT  */
    WSTRING = 326,                 /* WSTRING  */
    STRING = 327,                  /* STRING  */
    BOOL = 328,                    /* BOOL  */
    TIME = 329,                    /* TIME  */
    DATE = 330,                    /* DATE  */
    DATE_AND_TIME = 331,           /* DATE_AND_TIME  */
    DT = 332,                      /* DT  */
    TIME_OF_DAY = 333,             /* TIME_OF_DAY  */
    TOD = 334,                     /* TOD  */
    VOID = 335,                    /* VOID  */
    SAFEBYTE = 336,                /* SAFEBYTE  */
    SAFEWORD = 337,                /* SAFEWORD  */
    SAFEDWORD = 338,               /* SAFEDWORD  */
    SAFELWORD = 339,               /* SAFELWORD  */
    SAFELREAL = 340,               /* SAFELREAL  */
    SAFEREAL = 341,                /* SAFEREAL  */
    SAFESINT = 342,                /* SAFESINT  */
    SAFEINT = 343,                 /* SAFEINT  */
    SAFEDINT = 344,                /* SAFEDINT  */
    SAFELINT = 345,                /* SAFELINT  */
    SAFEUSINT = 346,               /* SAFEUSINT  */
    SAFEUINT = 347,                /* SAFEUINT  */
    SAFEUDINT = 348,               /* SAFEUDINT  */
    SAFEULINT = 349,               /* SAFEULINT  */
    SAFEWSTRING = 350,             /* SAFEWSTRING  */
    SAFESTRING = 351,              /* SAFESTRING  */
    SAFEBOOL = 352,                /* SAFEBOOL  */
    SAFETIME = 353,                /* SAFETIME  */
    SAFEDATE = 354,                /* SAFEDATE  */
    SAFEDATE_AND_TIME = 355,       /* SAFEDATE_AND_TIME  */
    SAFEDT = 356,                  /* SAFEDT  */
    SAFETIME_OF_DAY = 357,         /* SAFETIME_OF_DAY  */
    SAFETOD = 358,                 /* SAFETOD  */
    ANY = 359,                     /* ANY  */
    ANY_DERIVED = 360,             /* ANY_DERIVED  */
    ANY_ELEMENTARY = 361,          /* ANY_ELEMENTARY  */
    ANY_MAGNITUDE = 362,           /* ANY_MAGNITUDE  */
    ANY_NUM = 363,                 /* ANY_NUM  */
    ANY_REAL = 364,                /* ANY_REAL  */
    ANY_INT = 365,                 /* ANY_INT  */
    ANY_BIT = 366,                 /* ANY_BIT  */
    ANY_STRING = 367,              /* ANY_STRING  */
    ANY_DATE = 368,                /* ANY_DATE  */
    ASSIGN = 369,                  /* ASSIGN  */
    DOTDOT = 370,                  /* DOTDOT  */
    TYPE = 371,                    /* TYPE  */
    END_TYPE = 372,                /* END_TYPE  */
    ARRAY = 373,                   /* ARRAY  */
    OF = 374,                      /* OF  */
    STRUCT = 375,                  /* STRUCT  */
    END_STRUCT = 376,              /* END_STRUCT  */
    direct_variable_token = 377,   /* direct_variable_token  */
    incompl_location_token = 378,  /* incompl_location_token  */
    VAR_INPUT = 379,               /* VAR_INPUT  */
    VAR_OUTPUT = 380,              /* VAR_OUTPUT  */
    VAR_IN_OUT = 381,              /* VAR_IN_OUT  */
    VAR_EXTERNAL = 382,            /* VAR_EXTERNAL  */
    VAR_GLOBAL = 383,              /* VAR_GLOBAL  */
    END_VAR = 384,                 /* END_VAR  */
    RETAIN = 385,                  /* RETAIN  */
    NON_RETAIN = 386,              /* NON_RETAIN  */
    R_EDGE = 387,                  /* R_EDGE  */
    F_EDGE = 388,                  /* F_EDGE  */
    AT = 389,                      /* AT  */
    standard_function_name_token = 390, /* standard_function_name_token  */
    FUNCTION = 391,                /* FUNCTION  */
    END_FUNCTION = 392,            /* END_FUNCTION  */
    CONSTANT = 393,                /* CONSTANT  */
    standard_function_block_name_token = 394, /* standard_function_block_name_token  */
    FUNCTION_BLOCK = 395,          /* FUNCTION_BLOCK  */
    END_FUNCTION_BLOCK = 396,      /* END_FUNCTION_BLOCK  */
    VAR_TEMP = 397,                /* VAR_TEMP  */
    VAR = 398,                     /* VAR  */
    PROGRAM = 399,                 /* PROGRAM  */
    END_PROGRAM = 400,             /* END_PROGRAM  */
    ACTION = 401,                  /* ACTION  */
    END_ACTION = 402,              /* END_ACTION  */
    TRANSITION = 403,              /* TRANSITION  */
    END_TRANSITION = 404,          /* END_TRANSITION  */
    FROM = 405,                    /* FROM  */
    TO = 406,                      /* TO  */
    PRIORITY = 407,                /* PRIORITY  */
    INITIAL_STEP = 408,            /* INITIAL_STEP  */
    STEP = 409,                    /* STEP  */
    END_STEP = 410,                /* END_STEP  */
    L = 411,                       /* L  */
    D = 412,                       /* D  */
    SD = 413,                      /* SD  */
    DS = 414,                      /* DS  */
    SL = 415,                      /* SL  */
    N = 416,                       /* N  */
    P = 417,                       /* P  */
    P0 = 418,                      /* P0  */
    P1 = 419,                      /* P1  */
    prev_declared_global_var_name_token = 420, /* prev_declared_global_var_name_token  */
    prev_declared_program_name_token = 421, /* prev_declared_program_name_token  */
    prev_declared_resource_name_token = 422, /* prev_declared_resource_name_token  */
    prev_declared_configuration_name_token = 423, /* prev_declared_configuration_name_token  */
    CONFIGURATION = 424,           /* CONFIGURATION  */
    END_CONFIGURATION = 425,       /* END_CONFIGURATION  */
    TASK = 426,                    /* TASK  */
    RESOURCE = 427,                /* RESOURCE  */
    ON = 428,                      /* ON  */
    END_RESOURCE = 429,            /* END_RESOURCE  */
    VAR_CONFIG = 430,              /* VAR_CONFIG  */
    VAR_ACCESS = 431,              /* VAR_ACCESS  */
    WITH = 432,                    /* WITH  */
    SINGLE = 433,                  /* SINGLE  */
    INTERVAL = 434,                /* INTERVAL  */
    READ_WRITE = 435,              /* READ_WRITE  */
    READ_ONLY = 436,               /* READ_ONLY  */
    EOL = 437,                     /* EOL  */
    sendto_identifier_token = 438, /* sendto_identifier_token  */
    LD = 439,                      /* LD  */
    LDN = 440,                     /* LDN  */
    ST = 441,                      /* ST  */
    STN = 442,                     /* STN  */
    NOT = 443,                     /* NOT  */
    S = 444,                       /* S  */
    R = 445,                       /* R  */
    S1 = 446,                      /* S1  */
    R1 = 447,                      /* R1  */
    CLK = 448,                     /* CLK  */
    CU = 449,                      /* CU  */
    CD = 450,                      /* CD  */
    PV = 451,                      /* PV  */
    IN = 452,                      /* IN  */
    PT = 453,                      /* PT  */
    AND = 454,                     /* AND  */
    AND2 = 455,                    /* AND2  */
    OR = 456,                      /* OR  */
    XOR = 457,                     /* XOR  */
    ANDN = 458,                    /* ANDN  */
    ANDN2 = 459,                   /* ANDN2  */
    ORN = 460,                     /* ORN  */
    XORN = 461,                    /* XORN  */
    ADD = 462,                     /* ADD  */
    SUB = 463,                     /* SUB  */
    MUL = 464,                     /* MUL  */
    DIV = 465,                     /* DIV  */
    MOD = 466,                     /* MOD  */
    GT = 467,                      /* GT  */
    GE = 468,                      /* GE  */
    EQ = 469,                      /* EQ  */
    LT = 470,                      /* LT  */
    LE = 471,                      /* LE  */
    NE = 472,                      /* NE  */
    CAL = 473,                     /* CAL  */
    CALC = 474,                    /* CALC  */
    CALCN = 475,                   /* CALCN  */
    RET = 476,                     /* RET  */
    RETC = 477,                    /* RETC  */
    RETCN = 478,                   /* RETCN  */
    JMP = 479,                     /* JMP  */
    JMPC = 480,                    /* JMPC  */
    JMPCN = 481,                   /* JMPCN  */
    SENDTO = 482,                  /* SENDTO  */
    OPER_NE = 483,                 /* OPER_NE  */
    OPER_GE = 484,                 /* OPER_GE  */
    OPER_LE = 485,                 /* OPER_LE  */
    OPER_EXP = 486,                /* OPER_EXP  */
    RETURN = 487,                  /* RETURN  */
    IF = 488,                      /* IF  */
    THEN = 489,                    /* THEN  */
    ELSIF = 490,                   /* ELSIF  */
    ELSE = 491,                    /* ELSE  */
    END_IF = 492,                  /* END_IF  */
    CASE = 493,                    /* CASE  */
    END_CASE = 494,                /* END_CASE  */
    FOR = 495,                     /* FOR  */
    BY = 496,                      /* BY  */
    DO = 497,                      /* DO  */
    END_FOR = 498,                 /* END_FOR  */
    WHILE = 499,                   /* WHILE  */
    END_WHILE = 500,               /* END_WHILE  */
    REPEAT = 501,                  /* REPEAT  */
    UNTIL = 502,                   /* UNTIL  */
    END_REPEAT = 503,              /* END_REPEAT  */
    EXIT = 504                     /* EXIT  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif
/* Token kinds.  */
#define YYEMPTY -2
#define END_OF_INPUT 0
#define YYerror 256
#define YYUNDEF 257
#define BOGUS_TOKEN_ID 258
#define prev_declared_variable_name_token 259
#define prev_declared_direct_variable_token 260
#define prev_declared_fb_name_token 261
#define prev_declared_simple_type_name_token 262
#define prev_declared_subrange_type_name_token 263
#define prev_declared_enumerated_type_name_token 264
#define prev_declared_array_type_name_token 265
#define prev_declared_structure_type_name_token 266
#define prev_declared_string_type_name_token 267
#define prev_declared_ref_type_name_token 268
#define prev_declared_derived_function_name_token 269
#define prev_declared_derived_function_block_name_token 270
#define prev_declared_program_type_name_token 271
#define start_ST_body_token 272
#define start_IL_body_token 273
#define disable_code_generation_pragma_token 274
#define enable_code_generation_pragma_token 275
#define pragma_token 276
#define EN 277
#define ENO 278
#define REF 279
#define DREF 280
#define REF_TO 281
#define NULL_token 282
#define identifier_token 283
#define integer_token 284
#define binary_integer_token 285
#define octal_integer_token 286
#define hex_integer_token 287
#define real_token 288
#define safeboolean_true_literal_token 289
#define safeboolean_false_literal_token 290
#define boolean_true_literal_token 291
#define boolean_false_literal_token 292
#define FALSE 293
#define TRUE 294
#define single_byte_character_string_token 295
#define double_byte_character_string_token 296
#define fixed_point_token 297
#define fixed_point_d_token 298
#define integer_d_token 299
#define fixed_point_h_token 300
#define integer_h_token 301
#define fixed_point_m_token 302
#define integer_m_token 303
#define fixed_point_s_token 304
#define integer_s_token 305
#define fixed_point_ms_token 306
#define integer_ms_token 307
#define end_interval_token 308
#define erroneous_interval_token 309
#define T_SHARP 310
#define D_SHARP 311
#define BYTE 312
#define WORD 313
#define DWORD 314
#define LWORD 315
#define LREAL 316
#define REAL 317
#define SINT 318
#define INT 319
#define DINT 320
#define LINT 321
#define USINT 322
#define UINT 323
#define UDINT 324
#define ULINT 325
#define WSTRING 326
#define STRING 327
#define BOOL 328
#define TIME 329
#define DATE 330
#define DATE_AND_TIME 331
#define DT 332
#define TIME_OF_DAY 333
#define TOD 334
#define VOID 335
#define SAFEBYTE 336
#define SAFEWORD 337
#define SAFEDWORD 338
#define SAFELWORD 339
#define SAFELREAL 340
#define SAFEREAL 341
#define SAFESINT 342
#define SAFEINT 343
#define SAFEDINT 344
#define SAFELINT 345
#define SAFEUSINT 346
#define SAFEUINT 347
#define SAFEUDINT 348
#define SAFEULINT 349
#define SAFEWSTRING 350
#define SAFESTRING 351
#define SAFEBOOL 352
#define SAFETIME 353
#define SAFEDATE 354
#define SAFEDATE_AND_TIME 355
#define SAFEDT 356
#define SAFETIME_OF_DAY 357
#define SAFETOD 358
#define ANY 359
#define ANY_DERIVED 360
#define ANY_ELEMENTARY 361
#define ANY_MAGNITUDE 362
#define ANY_NUM 363
#define ANY_REAL 364
#define ANY_INT 365
#define ANY_BIT 366
#define ANY_STRING 367
#define ANY_DATE 368
#define ASSIGN 369
#define DOTDOT 370
#define TYPE 371
#define END_TYPE 372
#define ARRAY 373
#define OF 374
#define STRUCT 375
#define END_STRUCT 376
#define direct_variable_token 377
#define incompl_location_token 378
#define VAR_INPUT 379
#define VAR_OUTPUT 380
#define VAR_IN_OUT 381
#define VAR_EXTERNAL 382
#define VAR_GLOBAL 383
#define END_VAR 384
#define RETAIN 385
#define NON_RETAIN 386
#define R_EDGE 387
#define F_EDGE 388
#define AT 389
#define standard_function_name_token 390
#define FUNCTION 391
#define END_FUNCTION 392
#define CONSTANT 393
#define standard_function_block_name_token 394
#define FUNCTION_BLOCK 395
#define END_FUNCTION_BLOCK 396
#define VAR_TEMP 397
#define VAR 398
#define PROGRAM 399
#define END_PROGRAM 400
#define ACTION 401
#define END_ACTION 402
#define TRANSITION 403
#define END_TRANSITION 404
#define FROM 405
#define TO 406
#define PRIORITY 407
#define INITIAL_STEP 408
#define STEP 409
#define END_STEP 410
#define L 411
#define D 412
#define SD 413
#define DS 414
#define SL 415
#define N 416
#define P 417
#define P0 418
#define P1 419
#define prev_declared_global_var_name_token 420
#define prev_declared_program_name_token 421
#define prev_declared_resource_name_token 422
#define prev_declared_configuration_name_token 423
#define CONFIGURATION 424
#define END_CONFIGURATION 425
#define TASK 426
#define RESOURCE 427
#define ON 428
#define END_RESOURCE 429
#define VAR_CONFIG 430
#define VAR_ACCESS 431
#define WITH 432
#define SINGLE 433
#define INTERVAL 434
#define READ_WRITE 435
#define READ_ONLY 436
#define EOL 437
#define sendto_identifier_token 438
#define LD 439
#define LDN 440
#define ST 441
#define STN 442
#define NOT 443
#define S 444
#define R 445
#define S1 446
#define R1 447
#define CLK 448
#define CU 449
#define CD 450
#define PV 451
#define IN 452
#define PT 453
#define AND 454
#define AND2 455
#define OR 456
#define XOR 457
#define ANDN 458
#define ANDN2 459
#define ORN 460
#define XORN 461
#define ADD 462
#define SUB 463
#define MUL 464
#define DIV 465
#define MOD 466
#define GT 467
#define GE 468
#define EQ 469
#define LT 470
#define LE 471
#define NE 472
#define CAL 473
#define CALC 474
#define CALCN 475
#define RET 476
#define RETC 477
#define RETCN 478
#define JMP 479
#define JMPC 480
#define JMPCN 481
#define SENDTO 482
#define OPER_NE 483
#define OPER_GE 484
#define OPER_LE 485
#define OPER_EXP 486
#define RETURN 487
#define IF 488
#define THEN 489
#define ELSIF 490
#define ELSE 491
#define END_IF 492
#define CASE 493
#define END_CASE 494
#define FOR 495
#define BY 496
#define DO 497
#define END_FOR 498
#define WHILE 499
#define END_WHILE 500
#define REPEAT 501
#define UNTIL 502
#define END_REPEAT 503
#define EXIT 504

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 286 "iec_bison.yy"

    symbol_c 	*leaf;
    list_c	*list;
    char 	*ID;	/* token value */

#line 602 "iec_bison.hh"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif

/* Location type.  */
#if ! defined YYLTYPE && ! defined YYLTYPE_IS_DECLARED
typedef struct YYLTYPE YYLTYPE;
struct YYLTYPE
{
  int first_line;
  int first_column;
  int last_line;
  int last_column;
};
# define YYLTYPE_IS_DECLARED 1
# define YYLTYPE_IS_TRIVIAL 1
#endif


extern YYSTYPE yylval;
extern YYLTYPE yylloc;

int yyparse (void);


#endif /* !YY_YY_IEC_BISON_HH_INCLUDED  */
