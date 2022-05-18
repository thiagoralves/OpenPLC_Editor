/**************************************************************************
*
* Copyright (C) 2004 Steve Karg <skarg@users.sourceforge.net>
* Copyright (C) 2017 Mario de Sousa <msousa@fe.up.pt>
*
* Permission is hereby granted, free of charge, to any person obtaining
* a copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so, subject to
* the following conditions:
*
* The above copyright notice and this permission notice shall be included
* in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*
*********************************************************************/


#ifndef CONFIG_BACNET_FOR_BEREMIZ_H
#define CONFIG_BACNET_FOR_BEREMIZ_H

#ifdef  CONFIG_H
#error  "config.h already processed! (config_bacnet_for_beremiz.h should be included before config.h)"
#endif

/* Compilaton options for BACnet library, configured for the BACnet sserver
 * running on Beremiz.
 */

/* declare a single physical layer using your compiler define.
 * see datalink.h for possible defines. 
 */
/* Use BACnet/IP */
#define BACDL_BIP

/* optional configuration for BACnet/IP datalink layers */
/* other BIP defines (define as 1 to enable):
    USE_INADDR - uses INADDR_BROADCAST for broadcast and binds using INADDR_ANY
    USE_CLASSADDR = uses IN_CLASSx_HOST where x=A,B,C or D for broadcast
*/
#define BBMD_ENABLED 1

/* name of file in which BDT table will be stored */
#define BBMD_BACKUP_FILE beremiz_BACnet_BDT_table

/* Enable the Gateway (Routing) functionality here, if desired. */
#define MAX_NUM_DEVICES 1       /* Just the one normal BACnet Device Object */


/* Define your processor architecture as
   Big Endian (PowerPC,68K,Sparc) or Little Endian (Intel,AVR)
   ARM and MIPS can be either - what is your setup? */

/* WARNING: The following files are being included:
 *              <stdib.h>  -->  <endian.h>  -->  <bits/endian.h>
 * 
 *          endian.h defines the following constants as:
 *            #define __LITTLE_ENDIAN  and LITTLE_ENDIAN  as 1234
 *            #define    __BIG_ENDIAN  and    BIG_ENDIAN  as 4321
 *            #define    __PDP_ENDIAN  and    PDP_ENDIAN  as 3412
 * 
 *          bits/endian.h defines the constant BYTE_ORDER as:
 *              #define __BYTE_ORDER as __LITTLE_ENDIAN
 * 
 *          endian.h then sets the following constants
 *          (if __USE_BSD is set, which seems to be true):
 *            # define LITTLE_ENDIAN    __LITTLE_ENDIAN
 *            # define BIG_ENDIAN       __BIG_ENDIAN
 *            # define PDP_ENDIAN       __PDP_ENDIAN
 *            # define BYTE_ORDER       __BYTE_ORDER
 * 
 *         CONCLUSION:
 *           The bacnet library uses the BIG_ENDIAN constant (set to 0, or anything <>0)
 *           to indicate whether we are compiling on a little or big endian platform.
 *           However, <stdlib.h> is defining this same constant as '4321' !!!
 *           The decision to use BIG_ENDIAN as the constant is a unfortunate 
 *           on the part of the bacnet coders, but we live with it for now...
 *           We simply start off by undefining the BIG_ENDIAN constant, and carry
 *           on from there! 
 */
#undef BIG_ENDIAN

#ifndef BIG_ENDIAN
#if defined(__GNUC__) 
  /* We have GCC, which should define __LITTLE_ENDIAN__ or __BIG_ENDIAN__ */ 
#  if   defined(__LITTLE_ENDIAN__)
/*#    warning "Using gcc to determine platform endianness."*/
#    define BIG_ENDIAN 0
#  elif defined(__BIG_ENDIAN__)
/*#    warning "Using gcc to determine platform endianness."*/
#    define BIG_ENDIAN 1
#  endif
#endif /* __GNUC__   */ 
#endif /* BIG_ENDIAN */


/* If we still don't know byte order, try to get it from <endian.h> */
#ifndef BIG_ENDIAN
#include <endian.h>
#  ifdef BYTE_ORDER
#    if BYTE_ORDER == LITTLE_ENDIAN
/*#      warning "Using <endian.h> to determine platform endianness."*/
#      undef  BIG_ENDIAN 
#      define BIG_ENDIAN 0
#    elif BYTE_ORDER == BIG_ENDIAN
/*#      warning "Using <endian.h> to determine platform endianness."*/
#      undef  BIG_ENDIAN 
#      define BIG_ENDIAN 1
#    else
#      undef  BIG_ENDIAN
#    endif
#  endif /* BYTE_ORDER */
#endif   /* BIG_ENDIAN */


#ifndef BIG_ENDIAN
#error   "Unable to determine platform's byte order. Aborting compilation."
#elif   BIG_ENDIAN
/*#warning "Compiling for BIG endian platform."*/
#else
/*#warning "Compiling for LITTLE endian platform."*/
#endif



/* Define your Vendor Identifier assigned by ASHRAE */
#define BACNET_VENDOR_ID %(BACnet_Vendor_ID)s
#define BACNET_VENDOR_NAME "%(BACnet_Vendor_Name)s"
#define BACNET_DEVICE_MODEL_NAME "%(BACnet_Model_Name)s"
#define BACNET_FIRMWARE_REVISION  "Beremiz BACnet Extension, BACnet Stack:" BACNET_VERSION_TEXT
#define BACNET_DEVICE_LOCATION    "%(BACnet_Device_Location)s"
#define BACNET_DEVICE_DESCRIPTION "%(BACnet_Device_Description)s"  
#define BACNET_DEVICE_APPSOFT_VER "%(BACnet_Device_AppSoft_Version)s"


/* Max number of bytes in an APDU. */
/* Typical sizes are 50, 128, 206, 480, 1024, and 1476 octets */
/* This is used in constructing messages and to tell others our limits */
/* 50 is the minimum; adjust to your memory and physical layer constraints */
/* Lon=206, MS/TP=480, ARCNET=480, Ethernet=1476, BACnet/IP=1476 */
#define MAX_APDU 1476
/* #define MAX_APDU 128 enable this IP for testing readrange so you get the More Follows flag set */


/* for confirmed messages, this is the number of transactions */
/* that we hold in a queue waiting for timeout. */
/* Configure to zero if you don't want any confirmed messages */
/* Configure from 1..255 for number of outstanding confirmed */
/* requests available. */
#define MAX_TSM_TRANSACTIONS 255

/* The address cache is used for binding to BACnet devices */
/* The number of entries corresponds to the number of */
/* devices that might respond to an I-Am on the network. */
/* If your device is a simple server and does not need to bind, */
/* then you don't need to use this. */
#define MAX_ADDRESS_CACHE 255

/* some modules have debugging enabled using PRINT_ENABLED */
#define PRINT_ENABLED 0


/* BACAPP decodes WriteProperty service requests
   Choose the datatypes that your application supports */
#if !(defined(BACAPP_ALL) || \
    defined(BACAPP_NULL) || \
    defined(BACAPP_BOOLEAN) || \
    defined(BACAPP_UNSIGNED) || \
    defined(BACAPP_SIGNED) || \
    defined(BACAPP_REAL) || \
    defined(BACAPP_DOUBLE) || \
    defined(BACAPP_OCTET_STRING) || \
    defined(BACAPP_CHARACTER_STRING) || \
    defined(BACAPP_BIT_STRING) || \
    defined(BACAPP_ENUMERATED) || \
    defined(BACAPP_DATE) || \
    defined(BACAPP_TIME) || \
    defined(BACAPP_OBJECT_ID) || \
    defined(BACAPP_DEVICE_OBJECT_PROP_REF))
#define BACAPP_ALL
#endif

#if defined (BACAPP_ALL)
#define BACAPP_NULL
#define BACAPP_BOOLEAN
#define BACAPP_UNSIGNED
#define BACAPP_SIGNED
#define BACAPP_REAL
#define BACAPP_DOUBLE
#define BACAPP_OCTET_STRING
#define BACAPP_CHARACTER_STRING
#define BACAPP_BIT_STRING
#define BACAPP_ENUMERATED
#define BACAPP_DATE
#define BACAPP_TIME
#define BACAPP_OBJECT_ID
#define BACAPP_DEVICE_OBJECT_PROP_REF
#endif

/*
** Set the maximum vector type sizes
*/
#define MAX_BITSTRING_BYTES        (15)
#define MAX_CHARACTER_STRING_BYTES (MAX_APDU-6)
#define MAX_OCTET_STRING_BYTES     (MAX_APDU-6)

/*
** Control the selection of services etc to enable code size reduction for those
** compiler suites which do not handle removing of unused functions in modules
** so well.
**
** We will start with the A type services code first as these are least likely
** to be required in embedded systems using the stack.
*/

/*
** Define the services that may be required.
**
**/

/* For the moment enable them all to avoid breaking things */
#define BACNET_SVC_I_HAVE_A    1   /* Do we send I_Have requests? */
#define BACNET_SVC_WP_A        1   /* Do we send WriteProperty requests? */
#define BACNET_SVC_RP_A        1   /* Do we send ReadProperty requests? */
#define BACNET_SVC_RPM_A       1   /* Do we send ReadPropertyMultiple requests? */
#define BACNET_SVC_DCC_A       1   /* Do we send DeviceCommunicationControl requests? */
#define BACNET_SVC_RD_A        1   /* Do we send ReinitialiseDevice requests? */
#define BACNET_SVC_TS_A        1
#define BACNET_SVC_SERVER      0   /* Are we a pure server type device? */
#define BACNET_USE_OCTETSTRING 1   /* Do we need any octet strings? */
#define BACNET_USE_DOUBLE      1   /* Do we need any doubles? */
#define BACNET_USE_SIGNED      1   /* Do we need any signed integers */

/* Do them one by one */
#ifndef BACNET_SVC_I_HAVE_A     /* Do we send I_Have requests? */
#define BACNET_SVC_I_HAVE_A 0
#endif

#ifndef BACNET_SVC_WP_A /* Do we send WriteProperty requests? */
#define BACNET_SVC_WP_A 0
#endif

#ifndef BACNET_SVC_RP_A /* Do we send ReadProperty requests? */
#define BACNET_SVC_RP_A 0
#endif

#ifndef BACNET_SVC_RPM_A        /* Do we send ReadPropertyMultiple requests? */
#define BACNET_SVC_RPM_A 0
#endif

#ifndef BACNET_SVC_DCC_A        /* Do we send DeviceCommunicationControl requests? */
#define BACNET_SVC_DCC_A 0
#endif

#ifndef BACNET_SVC_RD_A /* Do we send ReinitialiseDevice requests? */
#define BACNET_SVC_RD_A 0
#endif

#ifndef BACNET_SVC_SERVER       /* Are we a pure server type device? */
#define BACNET_SVC_SERVER 1
#endif

#ifndef BACNET_USE_OCTETSTRING  /* Do we need any octet strings? */
#define BACNET_USE_OCTETSTRING 0
#endif

#ifndef BACNET_USE_DOUBLE       /* Do we need any doubles? */
#define BACNET_USE_DOUBLE 0
#endif

#ifndef BACNET_USE_SIGNED       /* Do we need any signed integers */
#define BACNET_USE_SIGNED 0
#endif

#endif  /* CONFIG_BACNET_FOR_BEREMIZ_H */
