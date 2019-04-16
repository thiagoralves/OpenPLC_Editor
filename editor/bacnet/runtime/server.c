/**************************************************************************
*
* Copyright (C) 2006 Steve Karg <skarg@users.sourceforge.net>
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
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <time.h>
#include <inttypes.h>  // uint32_t, ..., PRIu32, ...

#include "config_bacnet_for_beremiz_%(locstr)s.h"     /* the custom configuration for beremiz pluginh  */
#include "server_%(locstr)s.h"
#include "address.h"
#include "bacdef.h"
#include "handlers.h"
#include "client.h"
#include "dlenv.h"
#include "bacdcode.h"
#include "npdu.h"
#include "apdu.h"
#include "iam.h"
#include "tsm.h"
#include "datalink.h"
#include "dcc.h"
#include "getevent.h"
#include "net.h"
#include "txbuf.h"
#include "version.h"
#include "timesync.h"


/* A utility function used by most (all?) implementations of BACnet Objects */
/* Adds to Prop_List all entries in Prop_List_XX that are not
 * PROP_OBJECT_IDENTIFIER, PROP_OBJECT_NAME, PROP_OBJECT_TYPE, PROP_PROPERTY_LIST
 * and returns the number of elements that were added
 */
int BACnet_Init_Properties_List(
          int *Prop_List, 
    const int *Prop_List_XX) {
  
    unsigned int i = 0;
    unsigned int j = 0;
    
    for (j = 0; Prop_List_XX[j] >= 0; j++)
        // Add any propety, except for the following 4 which should not be included
        // in the Property_List property array.
        //  (see ASHRAE 135-2016, for example section 12.4.34)
        if ((Prop_List_XX[j] != PROP_OBJECT_IDENTIFIER) &&
            (Prop_List_XX[j] != PROP_OBJECT_NAME)       &&
            (Prop_List_XX[j] != PROP_OBJECT_TYPE)       &&
            (Prop_List_XX[j] != PROP_PROPERTY_LIST)) {
            Prop_List[i] = Prop_List_XX[j];
            i++;
        }
    Prop_List[i] = -1; // marks the end of the list!
    return i;
}






int BACnet_encode_character_string(uint8_t *apdu, const char *str) {
    BACNET_CHARACTER_STRING   char_string;
    characterstring_init_ansi(&char_string, str);
    /* FIXME: this might go beyond MAX_APDU length! */
    return encode_application_character_string(apdu, &char_string);
}

/* macro that always returns false.
 * To be used as the 'test_null' parameter to the BACnet_encode_array macro
 * in situations where we should never encode_null() values.
 */
#define retfalse(x) (false)

#define BACnet_encode_array(array, array_len, test_null, encode_function)                  \
{                                                                                           \
    uint8_t *apdu = NULL;                                                                   \
    apdu = rpdata->application_data;                                                        \
                                                                                            \
    switch (rpdata->array_index) {                                                          \
      case 0: /* Array element zero is the number of elements in the array */               \
        apdu_len = encode_application_unsigned(&apdu[0], array_len);                        \
        break;                                                                              \
      case BACNET_ARRAY_ALL: {                                                              \
        /* if no index was specified, then try to encode the entire list */                 \
        unsigned i = 0;                                                                     \
        apdu_len   = 0;                                                                     \
        for (i = 0; i < array_len; i++) {                                                   \
            /* FIXME: this might go beyond MAX_APDU length! */                              \
            if (!test_null(array[i]))                                                       \
                  apdu_len += encode_function        (&apdu[apdu_len], array[i]);           \
            else  apdu_len += encode_application_null(&apdu[apdu_len]);                     \
            /* return error if it does not fit in the APDU */                               \
            if (apdu_len >= MAX_APDU) {                                                     \
                rpdata->error_class = ERROR_CLASS_SERVICES;                                 \
                rpdata->error_code = ERROR_CODE_NO_SPACE_FOR_OBJECT;                        \
                apdu_len = BACNET_STATUS_ERROR;                                             \
                break; /* for(;;) */                                                        \
            }                                                                               \
        }                                                                                   \
        break;                                                                              \
      }                                                                                     \
      default:                                                                              \
        if (rpdata->array_index <= array_len) {                                             \
            if (!test_null(array[rpdata->array_index - 1]))                                 \
                  apdu_len += encode_function(&apdu[0], array[rpdata->array_index - 1]);    \
            else  apdu_len += encode_application_null(&apdu[0]);                            \
        } else {                                                                            \
            rpdata->error_class = ERROR_CLASS_PROPERTY;                                     \
            rpdata->error_code = ERROR_CODE_INVALID_ARRAY_INDEX;                            \
            apdu_len = BACNET_STATUS_ERROR;                                                 \
        }                                                                                   \
        break;                                                                              \
    } /* switch() */                                                                        \
}


/* include the device object */
#include "device_%(locstr)s.c"
#include "ai_%(locstr)s.c"
#include "ao_%(locstr)s.c"
#include "av_%(locstr)s.c"
#include "bi_%(locstr)s.c"
#include "bo_%(locstr)s.c"
#include "bv_%(locstr)s.c"
#include "msi_%(locstr)s.c"
#include "mso_%(locstr)s.c"
#include "msv_%(locstr)s.c"


/** Buffer used for receiving */
static uint8_t Rx_Buf[MAX_MPDU] = { 0 };




/*******************************************************/
/* BACnet Service Handlers taylored to Beremiz plugin  */ 
/*******************************************************/

static void BACNET_show_date_time(
    BACNET_DATE * bdate,
    BACNET_TIME * btime)
{
    /* show the date received */
    fprintf(stderr, "%%u", (unsigned) bdate->year);
    fprintf(stderr, "/%%u", (unsigned) bdate->month);
    fprintf(stderr, "/%%u", (unsigned) bdate->day);
    /* show the time received */
    fprintf(stderr, " %%02u", (unsigned) btime->hour);
    fprintf(stderr, ":%%02u", (unsigned) btime->min);
    fprintf(stderr, ":%%02u", (unsigned) btime->sec);
    fprintf(stderr, ".%%02u", (unsigned) btime->hundredths);
    fprintf(stderr, "\r\n");
}

static time_t __timegm(struct tm *new_time) {
    time_t     sec =  mktime(new_time);  /* assume new_time is in local time */
    
    /* sec will be an aproximation of the correct value. 
     * We must now fix this with the current difference
     * between UTC and localtime.
     * 
     * WARNING: The following algorithm to determine the current
     *          difference between local time and UTC will not 
     *          work if each value (lcl and utc) falls on a different
     *          side of a change to/from DST.
     *          For example, assume a change to DST is made at 12h00 
     *          of day X. The following algorithm does not work if:
     *            - lcl falls before 12h00 of day X
     *            - utc falls after  12h00 of day X
     */
    struct  tm lcl = *localtime(&sec); // lcl will be == new_time
    struct  tm utc = *gmtime   (&sec);
    
    if (lcl.tm_isdst == 1)  utc.tm_isdst = 1;
    
    time_t sec_lcl =  mktime(&lcl);
    time_t sec_utc =  mktime(&utc);

    /* difference in seconds between localtime and utc */
    time_t sec_dif = sec_lcl - sec_utc;
    return sec + sec_dif;
}


static void BACNET_set_date_time(
    BACNET_DATE * bdate,
    BACNET_TIME * btime,
    int utc /* set to > 0 if date & time in UTC */)
{
    struct tm       brokendown_time;
    time_t          seconds = 0;
    struct timespec ts;

    brokendown_time.tm_sec   = btime->sec;        /* seconds 0..60    */
    brokendown_time.tm_min   = btime->min;        /* minutes 0..59    */
    brokendown_time.tm_hour  = btime->hour;       /* hours   0..23    */
    brokendown_time.tm_mday  = bdate->day;        /* day of the month 1..31 */
    brokendown_time.tm_mon   = bdate->month-1;    /* month 0..11      */
    brokendown_time.tm_year  = bdate->year-1900;  /* years since 1900 */
//  brokendown_time.tm_wday  = ;                  /* day of the week  */
//  brokendown_time.tm_yday  = ;                  /* day in the year  */
    brokendown_time.tm_isdst = -1;                /* daylight saving time (-1 => unknown) */

    // Tranform time into format -> 'seconds since epoch'
    /* WARNING: timegm() is a non standard GNU extension.
     *          If you do not have it on your build system then consider
     *          finding the source code for timegm() (it is LGPL) from GNU
     *          C library and copying it here 
     *          (e.g. https://code.woboq.org/userspace/glibc/time/timegm.c.html)
     *          Another alternative is to use the fundion __timegm() above,
     *          which will mostly work but may have errors when the time being 
     *          converted is close to the time in the year when changing 
     *          to/from DST (daylight saving time)
     */
    if (utc > 0) seconds = timegm(&brokendown_time);    
    else         seconds = mktime(&brokendown_time);

    ts.tv_sec  = seconds;
    ts.tv_nsec = btime->hundredths*10*1000*1000;

//  fprintf(stderr, "clock_settime() s=%%ul,  ns=%%u\n", ts.tv_sec, ts.tv_nsec);
    clock_settime(CLOCK_REALTIME, &ts); 
//  clock_gettime(CLOCK_REALTIME, &ts); 
//  fprintf(stderr, "clock_gettime() s=%%ul,  ns=%%u\n", ts.tv_sec, ts.tv_nsec);
}



void BACnet_handler_timesync(
    uint8_t * service_request,
    uint16_t service_len,
    BACNET_ADDRESS * src)
{
    int len = 0;
    BACNET_DATE bdate;
    BACNET_TIME btime;

    (void) src;
    (void) service_len;
    len =
        timesync_decode_service_request(service_request, service_len, &bdate, &btime);
    if (len > 0) {
        fprintf(stderr, "BACnet plugin: Received TimeSyncronization Request -> ");
        BACNET_show_date_time(&bdate, &btime);
        /* set the time */
        BACNET_set_date_time(&bdate, &btime, 0 /* time in local time */);
    }

    return;
}

void BACnet_handler_timesync_utc(
    uint8_t * service_request,
    uint16_t service_len,
    BACNET_ADDRESS * src)
{
    int len = 0;
    BACNET_DATE bdate;
    BACNET_TIME btime;

    (void) src;
    (void) service_len;
    len =
        timesync_decode_service_request(service_request, service_len, &bdate, &btime);
    if (len > 0) {
        fprintf(stderr, "BACnet plugin: Received TimeSyncronizationUTC Request -> ");
        BACNET_show_date_time(&bdate, &btime);
        /* set the time */
        BACNET_set_date_time(&bdate, &btime, 1 /* time in UTC */);
    }

    return;
}



/**********************************************/
/** Initialize the handlers we will utilize. **/
/**********************************************/
/*
 * TLDR: The functions that will create the __Resp.__ messages.
 * 
 * The service handlers are the functions that will respond to BACnet requests this device receives.
 * In essence, the service handlers will create and send the Resp. (Response) messages
 * of the Req. -> Ind. -> Resp. -> Conf. service sequence defined in OSI
 * (Request, Indication, Response, Confirmation)
 * 
 */
static int Init_Service_Handlers(
    void)
{
    /* set the handler for all the services we don't implement */
    /* It is required to send the proper reject message... */
    apdu_set_unrecognized_service_handler_handler(handler_unrecognized_service);

    /* Set the handlers for any unconfirmed services that we support. */
    apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_WHO_IS,  // DM-DDB-B - Dynamic Device Binding B (Resp.)
                                   handler_who_is);           //            (see ASHRAE 135-2016, section K5.1 and K5.2)
//  apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_I_AM,    // DM-DDB-A - Dynamic Device Binding A (Resp.)
//                                 handler_i_am_bind);        //            Responding to I_AM requests is for clients (A)!
//                                                            //            (see ASHRAE 135-2016, section K5.1 and K5.2)
    apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_WHO_HAS, // DM-DOB-B - Dynamic Object Binding B (Resp.)
                                   handler_who_has);          //            (see ASHRAE 135-2016, section K5.3 and K5.4)
//  apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_I_HAVE,  // DM-DOB-A - Dynamic Object Binding A (Resp.)
//                                 handler_i_have);           //            Responding to I_HAVE requests is for clients (A)!
//                                                            //            (see ASHRAE 135-2016, section K5.3 and K5.4)
    apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_UTC_TIME_SYNCHRONIZATION, // DM-UTC-B -UTCTimeSynchronization-B (Resp.)
                                 BACnet_handler_timesync_utc);                 //            (see ASHRAE 135-2016, section K5.14)
    apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_TIME_SYNCHRONIZATION,     // DM-TS-B - TimeSynchronization-B (Resp.)
                                 BACnet_handler_timesync);                     //            (see ASHRAE 135-2016, section K5.12)

    /* Set the handlers for any confirmed services that we support. */
    apdu_set_confirmed_handler(SERVICE_CONFIRMED_READ_PROPERTY,      // DS-RP-B - Read Property B (Resp.)
                                 handler_read_property);             //            (see ASHRAE 135-2016, section K1.2)
//  apdu_set_confirmed_handler(SERVICE_CONFIRMED_READ_PROP_MULTIPLE, // DS-RPM-B -Read Property Multiple-B (Resp.)
//                               handler_read_property_multiple);    //            (see ASHRAE 135-2016, section K1.4)
    apdu_set_confirmed_handler(SERVICE_CONFIRMED_WRITE_PROPERTY,     // DS-WP-B - Write Property B (Resp.)
                                 handler_write_property);            //            (see ASHRAE 135-2016, section K1.8)
//  apdu_set_confirmed_handler(SERVICE_CONFIRMED_WRITE_PROP_MULTIPLE,// DS-WPM-B -Write Property Multiple B (Resp.)
//                               handler_write_property_multiple);   //            (see ASHRAE 135-2016, section K1.10)
//  apdu_set_confirmed_handler(SERVICE_CONFIRMED_READ_RANGE,
//                               handler_read_range);
//  apdu_set_confirmed_handler(SERVICE_CONFIRMED_REINITIALIZE_DEVICE,
//                               handler_reinitialize_device);
    
//  apdu_set_confirmed_handler(SERVICE_CONFIRMED_SUBSCRIBE_COV,
//                               handler_cov_subscribe);
//  apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_COV_NOTIFICATION,
//                               handler_ucov_notification);
    /* handle communication so we can shutup when asked */
    apdu_set_confirmed_handler(SERVICE_CONFIRMED_DEVICE_COMMUNICATION_CONTROL, // DM-DCC-B - Device Communication Control B
                                 handler_device_communication_control);        //            (see ASHRAE 135-2016, section K5.6)
//  /* handle the data coming back from private requests */
//  apdu_set_unconfirmed_handler(SERVICE_UNCONFIRMED_PRIVATE_TRANSFER,
//                               handler_unconfirmed_private_transfer);
    
    // success
    return 0;
}



static int Init_Network_Interface(
    const char *interface,    // for linux:   /dev/eth0, /dev/eth1, /dev/wlan0, ...
                              // for windows: 192.168.0.1 (IP addr. of interface)
                              // NULL => use default!
    const char *port,         // Port the server will listen on. (NULL => use default)
    const char *apdu_timeout, // (NULL => use default)
    const char *apdu_retries  // (NULL => use default)
   )
{
    char datalink_layer[4];

    strcpy(datalink_layer, "BIP"); // datalink_set() does not accpet const char *, so we copy it...
//  BIP_Debug = true;

    if (port != NULL) {
        bip_set_port(htons((uint16_t) strtol(port, NULL, 0)));
    } else {
            bip_set_port(htons(0xBAC0));
    }
    
    if (apdu_timeout != NULL) {
        apdu_timeout_set((uint16_t) strtol(apdu_timeout, NULL, 0));
    }

    if (apdu_retries != NULL) {
        apdu_retries_set((uint8_t) strtol(apdu_retries, NULL, 0));
    }

    // datalink_init is a pointer that will actually call bip_init()
    // datalink_init pointer is set by the call datalink_set("BIP")
    /* NOTE: current implementation of BACnet stack uses the interface
     *       only to determine the server's local IP address and broacast address.
     *       The local IP addr is later used to discard (broadcast) messages
     *       it receives that were sent by itself.
     *       The broadcast IP addr is used for broadcast messages.
     *       WARNING: The socket itself is created to listen on all 
     *       available interfaces (INADDR_ANY), so this setting may induce
     *       the user in error as we will accept messages arriving on other
     *       interfaces (if they exist)
     *       (see bip_init() in ports/linux/bip-init.c)
     *       (see bip_****() in src/bip.c)
     */
    char *tmp = (char *)malloc(strlen(interface) + 1);
    if (tmp == NULL) return -1;
    strncpy(tmp, interface, strlen(interface) + 1);
    if (!datalink_init(tmp)) {
        return -1;
    }
// #if (MAX_TSM_TRANSACTIONS)
//     pEnv = getenv("BACNET_INVOKE_ID");
//     if (pEnv) {
//         tsm_invokeID_set((uint8_t) strtol(pEnv, NULL, 0));
//     }
// #endif
    dlenv_register_as_foreign_device();
    
    // success
    return 0;
}


// This mutex blocks execution of __init_%(locstr)s() until initialization is done
static int init_done = 0;
static pthread_mutex_t init_done_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t init_done_cond = PTHREAD_COND_INITIALIZER;

/** Main function of server demo. **/
int bn_server_run(server_node_t *server_node) {
    int res = 0;
    BACNET_ADDRESS src = {0};  /* address where message came from */
    uint16_t pdu_len = 0;
    unsigned timeout = 1000;       /* milliseconds */
    time_t last_seconds = 0;
    time_t current_seconds = 0;
    uint32_t elapsed_seconds = 0;
    uint32_t elapsed_milliseconds = 0;
    uint32_t address_binding_tmr = 0;
    uint32_t recipient_scan_tmr = 0;

    /* allow the device ID to be set */
    Device_Set_Object_Instance_Number(server_node->device_id);
    /* load any static address bindings in our device bindings list */
    address_init();
    /* load any entries in the BDT table from backup file */
    bvlc_bdt_restore_local();
    /* Initiliaze the bacnet server 'device' */    
    Device_Init(server_node->device_name);

    pthread_mutex_lock(&init_done_lock);
    init_done = 1;
    pthread_cond_signal(&init_done_cond);
    pthread_mutex_unlock(&init_done_lock);

    /* Set the password (max 31 chars) for Device Communication Control request. */
    /* Default in the BACnet stack is hardcoded as "filister" */
    /* (char *) cast is to remove the cast. The function is incorrectly declared/defined in the BACnet stack! */
    /* BACnet stack needs to change demo/handler/h_dcc.c and include/handlers.h                               */
    handler_dcc_password_set((char *)server_node->comm_control_passwd);
    /* Set callbacks and configure network interface */
    res = Init_Service_Handlers();
    if (res < 0) exit(1);
    res = Init_Network_Interface(
            server_node->network_interface, // interface    (NULL => use default (eth0))
            server_node->port_number,       // Port number  (NULL => use default (0xBAC0))
            NULL,              // apdu_timeout (NULL => use default)
            NULL               // apdu_retries (NULL => use default)
           );
    if (res < 0) {
        fprintf(stderr, "BACnet plugin: error initializing bacnet server node %%s!\n", server_node->location);
        exit(1); // kill the server thread!
    }
    /* BACnet stack correcly configured. Give user some feedback! */
    struct in_addr my_addr, broadcast_addr;
    my_addr.       s_addr = bip_get_addr();
    broadcast_addr.s_addr = bip_get_broadcast_addr();
    printf("BACnet plugin:"
                         " Local IP addr: %%s" 
                        ", Broadcast IP addr: %%s" 
                        ", Port number: 0x%%04X [%%hu]" 
                        ", BACnet Device ID: %%d"
                        ", Max APDU: %%d"
                        ", BACnet Stack Version %%s\n",
                        inet_ntoa(my_addr),
                        inet_ntoa(broadcast_addr),
                        ntohs(bip_get_port()), ntohs(bip_get_port()),
                        Device_Object_Instance_Number(), 
                        MAX_APDU,
                        Device_Firmware_Revision()
                        );
    /* configure the timeout values */
    last_seconds = time(NULL);
    /* broadcast an I-Am on startup */
    Send_I_Am(&Handler_Transmit_Buffer[0]);
    /* loop forever */
    for (;;) {
        /* input */
        current_seconds = time(NULL);

        /* returns 0 bytes on timeout */
        pdu_len = datalink_receive(&src, &Rx_Buf[0], MAX_MPDU, timeout);

        /* process */
        if (pdu_len) {
            npdu_handler(&src, &Rx_Buf[0], pdu_len);
        }
        /* at least one second has passed */
        elapsed_seconds = (uint32_t) (current_seconds - last_seconds);
        if (elapsed_seconds) {
            last_seconds = current_seconds;
            dcc_timer_seconds(elapsed_seconds);
            //bvlc_maintenance_timer(elapsed_seconds); // already called by dlenv_maintenance_timer() => do _not_ call here!
            dlenv_maintenance_timer(elapsed_seconds);
            elapsed_milliseconds = elapsed_seconds * 1000;
            tsm_timer_milliseconds(elapsed_milliseconds);
        }
        handler_cov_task();
        /* scan cache address */
        address_binding_tmr += elapsed_seconds;
        if (address_binding_tmr >= 60) {
            address_cache_timer(address_binding_tmr);
            address_binding_tmr = 0;
        }
    }

    /* should never occur!! */
    return 0;
}





#include <pthread.h>

static void *__bn_server_thread(void *_server_node)  {
	server_node_t *server_node = _server_node;

	// Enable thread cancelation. Enabled is default, but set it anyway to be safe.
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);

	// bn_server_run() should never return!
	bn_server_run(server_node);
	fprintf(stderr, "BACnet plugin: bacnet server for node %%s died unexpectedly!\n", server_node->location); /* should never occur */
	return NULL;
}


int __cleanup_%(locstr)s ();

int __init_%(locstr)s (int argc, char **argv){
	int index;

    init_done = 0;
	/* init each local server */
	/* NOTE: All server_nodes[].init_state are initialised to 0 in the code 
	 *       generated by the BACnet plugin 
	 */
	/* create the BACnet server */
	server_node.init_state = 1; // we have created the node
	
	/* launch a thread to handle this server node */
	{
		int res = 0;
		pthread_attr_t attr;
		res |= pthread_attr_init(&attr);
		res |= pthread_create(&(server_node.thread_id), &attr, &__bn_server_thread, (void *)&(server_node));
		if (res !=  0) {
			fprintf(stderr, "BACnet plugin: Error starting bacnet server thread for node %%s\n", server_node.location);
			goto error_exit;
		}
	}

    pthread_mutex_lock(&init_done_lock);
    while (!init_done) {
        pthread_cond_wait(&init_done_cond, &init_done_lock);
    }
    pthread_mutex_unlock(&init_done_lock);

	server_node.init_state = 2; // we have created the node and thread

	return 0;
	
error_exit:
	__cleanup_%(locstr)s ();
	return -1;
}





void __publish_%(locstr)s (){
       Analog_Value_Copy_Located_Var_to_Present_Value();
       Analog_Input_Copy_Located_Var_to_Present_Value();
      Analog_Output_Copy_Located_Var_to_Present_Value();
       Binary_Value_Copy_Located_Var_to_Present_Value();
       Binary_Input_Copy_Located_Var_to_Present_Value();
      Binary_Output_Copy_Located_Var_to_Present_Value();
   Multistate_Value_Copy_Located_Var_to_Present_Value();
   Multistate_Input_Copy_Located_Var_to_Present_Value();
  Multistate_Output_Copy_Located_Var_to_Present_Value();
}





void __retrieve_%(locstr)s (){
       Analog_Value_Copy_Present_Value_to_Located_Var();
       Analog_Input_Copy_Present_Value_to_Located_Var();
      Analog_Output_Copy_Present_Value_to_Located_Var();
       Binary_Value_Copy_Present_Value_to_Located_Var();
       Binary_Input_Copy_Present_Value_to_Located_Var();
      Binary_Output_Copy_Present_Value_to_Located_Var();
   Multistate_Value_Copy_Present_Value_to_Located_Var();
   Multistate_Input_Copy_Present_Value_to_Located_Var();
  Multistate_Output_Copy_Present_Value_to_Located_Var();
}





int __cleanup_%(locstr)s (){
	int index, close;
	int res = 0;

	/* kill thread and close connections of each modbus server node */
	close = 0;
	if (server_node.init_state >= 2) {
		// thread was launched, so we try to cancel it!
		close  = pthread_cancel(server_node.thread_id);
		close |= pthread_join  (server_node.thread_id, NULL);
		if (close < 0)
			fprintf(stderr, "BACnet plugin: Error closing thread for bacnet server %%s\n", server_node.location);
	}
	res |= close;

	close = 0;
	if (server_node.init_state >= 1) {
		// bacnet server node was created, so we try to close it!
		// datalink_cleanup is a pointer that will actually call bip_cleanup()
		// datalink_cleanup pointer is set by the call datalink_set("BIP")
		datalink_cleanup();
	}
	res |= close;
	server_node.init_state = 0;

	/* bacnet library close */
	// Nothing to do ???

	return res;
}

