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

#ifndef SERVER_H_
#define SERVER_H_


#include <stddef.h>
#include <stdint.h>




typedef struct{
	    char location              [%(BACnet_Param_String_Size)d];
	    char network_interface     [%(BACnet_Param_String_Size)d];
	    char port_number           [%(BACnet_Param_String_Size)d];
	    char device_name           [%(BACnet_Param_String_Size)d];
	    char device_location       [%(BACnet_Param_String_Size)d];        
	    char device_description    [%(BACnet_Param_String_Size)d];
	    char device_appsoftware_ver[%(BACnet_Param_String_Size)d];        
	    char comm_control_passwd   [%(BACnet_Param_String_Size)d];
// 	    int         override_local_config;  // bool flag => 
// 	                                        //   true : use these parameter values
// 	                                        //   false: use values stored on local file in PLC
	    uint32_t	device_id; // device ID is 22 bits long! uint16_t is not enough!
	    int		init_state; // store how far along the server's initialization has progressed
	    pthread_t	thread_id;  // thread handling this server
	} server_node_t;



/*initialization following all parameters given by user in application*/
static server_node_t server_node = {
  "%(locstr)s",
  "%(network_interface)s",              // interface    (NULL => use default (eth0))
  "%(port_number)s",                    // Port number  (NULL => use default)
  "%(BACnet_Device_Name)s",             // BACnet server's device (object) Name
  "%(BACnet_Device_Location)s",         // BACnet server's device (object) Location
  "%(BACnet_Device_Description)s",      // BACnet server's device (object) Description
  "%(BACnet_Device_AppSoft_Version)s",  // BACnet server's device (object) App. Software Ver.
  "%(BACnet_Comm_Control_Password)s",   // BACnet server's device (object) Password
//  (Override_Parameters_Saved_on_PLC)d, // override locally saved parameters (bool flag)
  %(BACnet_Device_ID)s                  // BACnet server's device (object) ID
};


#endif /* SERVER_H_ */
