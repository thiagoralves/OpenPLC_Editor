#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz runtime.
#
# Copyright (C) 2020: Mario de Sousa
#
# See COPYING.Runtime file for copyrights details.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA




##############################################################################################
# This file implements an extension to the web server embedded in the Beremiz_service.py     #
# runtime manager (webserver is in runtime/NevowServer.py).                                  #
#                                                                                            #
# The extension implemented in this file allows for runtime configuration                    #
# of Modbus plugin parameters                                                                #
##############################################################################################



import json
import os
import ctypes
import string
import hashlib

from formless import annotate, webform

import runtime.NevowServer as NS

# Directory in which to store the persistent configurations
# Should be a directory that does not get wiped on reboot!
_ModbusConfFiledir = WorkingDir

# List of all Web Extension Setting nodes we are handling.
# One WebNode each for:
#   - Modbus TCP client 
#   - Modbus TCP server
#   - Modbus RTU client
#   - Modbus RTU slave
# configured in the loaded PLC (i.e. the .so file loaded into memory)
# Each entry will be a dictionary. See _AddWebNode() for the details
# of the data structure in each entry.
_WebNodeList = []




class MB_StrippedString(annotate.String):
    def __init__(self, *args, **kwargs):
        annotate.String.__init__(self, strip = True, *args, **kwargs)


class MB_StopBits(annotate.Choice):
    _choices = [0, 1, 2]

    def coerce(self, val, configurable):
        return int(val)
    def __init__(self, *args, **kwargs):
        annotate.Choice.__init__(self, choices = self._choices, *args, **kwargs)


class MB_Baud(annotate.Choice):
    _choices = [110, 300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

    def coerce(self, val, configurable):
        return int(val)
    def __init__(self, *args, **kwargs):
        annotate.Choice.__init__(self, choices = self._choices, *args, **kwargs)


class MB_Parity(annotate.Choice):
    # For more info on what this class really does, have a look at the code in
    # file twisted/nevow/annotate.py
    # grab this code from $git clone https://github.com/twisted/nevow/
    # 
    # Warning: do _not_ name this variable choice[] without underscore, as that name is
    # already used for another similar variable by the underlying class annotate.Choice
    _choices = [  0,      1,      2  ]
    _label   = ["none", "odd", "even"]
    
    def choice_to_label(self, key):
        #PLCObject.LogMessage("Modbus web server extension::choice_to_label()  " + str(key))
        return self._label[key]
    
    def coerce(self, val, configurable):
        """Coerce a value with the help of an object, which is the object
        we are configuring.
        """
        # Basically, make sure the value the user introduced is valid, and transform
        # into something that is valid if necessary or mark it as an error 
        # (by raising an exception ??).
        #
        # We are simply using this functions to transform the input value (a string)
        # into an integer. Note that although the available options are all
        # integers (0, 1 or 2), even though what is shown on the user interface
        # are actually strings, i.e. the labels), these parameters are for some 
        # reason being parsed as strings, so we need to map them back to an
        # integer.
        #
        #PLCObject.LogMessage("Modbus web server extension::coerce  " + val )
        return int(val)

    def __init__(self, *args, **kwargs):
        annotate.Choice.__init__(self, 
                                 choices   = self._choices,
                                 stringify = self.choice_to_label,
                                 *args, **kwargs)



# Parameters we will need to get from the C code, but that will not be shown
# on the web interface. Common to all modbus entry types (client/server, tcp/rtu/ascii)
#
# The annotate type entry is basically useless and is completely ignored.
# We kee that entry so that this list can later be correctly merged with the
# following lists...
General_parameters = [
    #    param. name       label                        ctype type         annotate type
    # (C code var name)   (used on web interface)      (C data type)       (web data type)
    #                                                                      (annotate.String,
    #                                                                       annotate.Integer, ...)
    ("config_name"      , _("")                      , ctypes.c_char_p,    annotate.String),
    ("addr_type"        , _("")                      , ctypes.c_char_p,    annotate.String)
    ]                                                                      
                                                                           
# Parameters we will need to get from the C code, and that _will_ be shown
# on the web interface.
TCPclient_parameters = [                                                   
    #    param. name       label                        ctype type         annotate type
    # (C code var name)   (used on web interface)      (C data type)       (web data type)
    #                                                                      (annotate.String,
    #                                                                       annotate.Integer, ...)
    ("host"             , _("Remote IP Address")     , ctypes.c_char_p,    MB_StrippedString),
    ("port"             , _("Remote Port Number")    , ctypes.c_char_p,    MB_StrippedString),
    ("comm_period"      , _("Invocation Rate (ms)")  , ctypes.c_ulonglong, annotate.Integer )
    ]

RTUclient_parameters = [                                                   
    #    param. name       label                        ctype type         annotate type
    # (C code var name)   (used on web interface)      (C data type)       (web data type)
    #                                                                      (annotate.String,
    #                                                                       annotate.Integer, ...)
    ("device"           , _("Serial Port")           , ctypes.c_char_p,    MB_StrippedString),
    ("baud"             , _("Baud Rate")             , ctypes.c_int,       MB_Baud         ),
    ("parity"           , _("Parity")                , ctypes.c_int,       MB_Parity       ),
    ("stop_bits"        , _("Stop Bits")             , ctypes.c_int,       MB_StopBits     ),
    ("comm_period"      , _("Invocation Rate (ms)")  , ctypes.c_ulonglong, annotate.Integer)
    ]

TCPserver_parameters = [                                                   
    #    param. name       label                        ctype type         annotate type
    # (C code var name)   (used on web interface)      (C data type)       (web data type)
    #                                                                      (annotate.String,
    #                                                                       annotate.Integer, ...)
    ("host"             , _("Local IP Address")      , ctypes.c_char_p,    MB_StrippedString),
    ("port"             , _("Local Port Number")     , ctypes.c_char_p,    MB_StrippedString),
    ("slave_id"         , _("Slave ID")              , ctypes.c_ubyte,     annotate.Integer )
    ]

RTUslave_parameters = [                                                   
    #    param. name       label                        ctype type         annotate type
    # (C code var name)   (used on web interface)      (C data type)       (web data type)
    #                                                                      (annotate.String,
    #                                                                       annotate.Integer, ...)
    ("device"           , _("Serial Port")           , ctypes.c_char_p,    MB_StrippedString),
    ("baud"             , _("Baud Rate")             , ctypes.c_int,       MB_Baud         ),
    ("parity"           , _("Parity")                , ctypes.c_int,       MB_Parity       ),
    ("stop_bits"        , _("Stop Bits")             , ctypes.c_int,       MB_StopBits     ),
    ("slave_id"         , _("Slave ID")              , ctypes.c_ubyte,     annotate.Integer)
    ]




# Dictionary containing List of Web viewable parameters
# Note: the dictionary key must be the same as the string returned by the 
# __modbus_get_ClientNode_addr_type()
# __modbus_get_ServerNode_addr_type()
# functions implemented in C (see modbus/mb_runtime.c)
_client_WebParamListDict = {}
_client_WebParamListDict["tcp"  ] = TCPclient_parameters
_client_WebParamListDict["rtu"  ] = RTUclient_parameters
_client_WebParamListDict["ascii"] = []  # (Note: ascii not yet implemented in Beremiz modbus plugin)

_server_WebParamListDict = {}
_server_WebParamListDict["tcp"  ] = TCPserver_parameters
_server_WebParamListDict["rtu"  ] = RTUslave_parameters
_server_WebParamListDict["ascii"] = []  # (Note: ascii not yet implemented in Beremiz modbus plugin)

WebParamListDictDict = {}
WebParamListDictDict['client'] = _client_WebParamListDict
WebParamListDictDict['server'] = _server_WebParamListDict






def _SetModbusSavedConfiguration(WebNode_id, newConfig):
    """ Stores a dictionary in a persistant file containing the Modbus parameter configuration """
    WebNode_entry = _WebNodeList[WebNode_id]

    if WebNode_entry["DefaultConfiguration"] == newConfig:

        _DelModbusSavedConfiguration(WebNode_id)
        WebNode_entry["ModbusSavedConfiguration"] = None

    else:

        # Add the addr_type and node_type to the data that will be saved to file
        # This allows us to confirm the saved data contains the correct addr_type
        # when loading from file
        save_info = {}
        save_info["addr_type"] = WebNode_entry["addr_type"]
        save_info["node_type"] = WebNode_entry["node_type"]
        save_info["config"   ] = newConfig
        
        filename = WebNode_entry["filename"]

        with open(os.path.realpath(filename), 'w') as f:
            json.dump(save_info, f, sort_keys=True, indent=4)
            
        WebNode_entry["ModbusSavedConfiguration"] = newConfig




def _DelModbusSavedConfiguration(WebNode_id):
    """ Deletes the file cotaining the persistent Modbus configuration """
    filename = _WebNodeList[WebNode_id]["filename"]
    
    if os.path.exists(filename):
        os.remove(filename)




def _GetModbusSavedConfiguration(WebNode_id):
    """
    Returns a dictionary containing the Modbus parameter configuration
    that was last saved to file. If no file exists, or file contains 
    wrong addr_type (i.e. 'tcp', 'rtu' or 'ascii' -> does not match the
    addr_type of the WebNode_id), then return None
    """
    filename = _WebNodeList[WebNode_id]["filename"]
    try:
        #if os.path.isfile(filename):
        save_info = json.load(open(os.path.realpath(filename)))
    except Exception:    
        return None

    if save_info["addr_type"] != _WebNodeList[WebNode_id]["addr_type"]:
        return None
    if save_info["node_type"] != _WebNodeList[WebNode_id]["node_type"]:
        return None
    if "config" not in save_info:
        return None
    
    saved_config = save_info["config"]
    
    #if _CheckConfiguration(saved_config):
    #    return saved_config
    #else:
    #    return None

    return saved_config



def _GetModbusPLCConfiguration(WebNode_id):
    """
    Returns a dictionary containing the current Modbus parameter configuration
    stored in the C variables in the loaded PLC (.so file)
    """
    current_config = {}
    C_node_id      = _WebNodeList[WebNode_id]["C_node_id"]
    WebParamList   = _WebNodeList[WebNode_id]["WebParamList"]
    GetParamFuncs  = _WebNodeList[WebNode_id]["GetParamFuncs"]

    for par_name, x1, x2, x3 in WebParamList:
        value = GetParamFuncs[par_name](C_node_id)
        if value is not None:
            current_config[par_name] = value
    
    return current_config



def _SetModbusPLCConfiguration(WebNode_id, newconfig):
    """
    Stores the Modbus parameter configuration into the
    the C variables in the loaded PLC (.so file)
    """
    C_node_id      = _WebNodeList[WebNode_id]["C_node_id"]
    SetParamFuncs  = _WebNodeList[WebNode_id]["SetParamFuncs"]

    for par_name in newconfig:
        value = newconfig[par_name]
        if value is not None:
            SetParamFuncs[par_name](C_node_id, value)
            



def _GetModbusWebviewConfigurationValue(ctx, WebNode_id, argument):
    """
    Callback function, called by the web interface (NevowServer.py)
    to fill in the default value of each parameter of the web form
    
    Note that the real callback function is a dynamically created function that
    will simply call this function to do the work. It will also pass the WebNode_id 
    as a parameter.
    """    
    try:
        return _WebNodeList[WebNode_id]["WebviewConfiguration"][argument.name]
    except Exception:
        return ""



def OnModbusButtonSave(**kwargs):
    """
    Function called when user clicks 'Save' button in web interface
    The function will configure the Modbus plugin in the PLC with the values
    specified in the web interface. However, values must be validated first!
    
    Note that this function does not get called directly. The real callback
    function is the dynamic __OnButtonSave() function, which will add the 
    "WebNode_id" argument, and call this function to do the work.
    """

    #PLCObject.LogMessage("Modbus web server extension::OnModbusButtonSave()  Called")
    
    newConfig    = {}
    WebNode_id   =  kwargs.get("WebNode_id", None)
    WebParamList = _WebNodeList[WebNode_id]["WebParamList"]
    
    for par_name, x1, x2, x3 in WebParamList:
        value = kwargs.get(par_name, None)
        if value is not None:
            newConfig[par_name] = value

    # First check if configuration is OK.
    # Note that this is not currently required, as we use drop down choice menus
    # for baud, parity and sop bits, so the values should always be correct!
    #if not _CheckWebConfiguration(newConfig):
    #    return
    
    # store to file the new configuration so that 
    # we can recoup the configuration the next time the PLC
    # has a cold start (i.e. when Beremiz_service.py is retarted)
    _SetModbusSavedConfiguration(WebNode_id, newConfig)

    # Configure PLC with the current Modbus parameters
    _SetModbusPLCConfiguration(WebNode_id, newConfig)

    # Update the viewable configuration
    # The PLC may have coerced the values on calling _SetModbusPLCConfiguration()
    # so we do not set it directly to newConfig
    _WebNodeList[WebNode_id]["WebviewConfiguration"] = _GetModbusPLCConfiguration(WebNode_id)



def OnModbusButtonReset(**kwargs):
    """
    Function called when user clicks 'Delete' button in web interface
    The function will delete the file containing the persistent
    Modbus configution
    """

    WebNode_id = kwargs.get("WebNode_id", None)
    
    # Delete the file
    _DelModbusSavedConfiguration(WebNode_id)

    # Set the current configuration to the default (hardcoded in C)
    new_config = _WebNodeList[WebNode_id]["DefaultConfiguration"]
    _SetModbusPLCConfiguration(WebNode_id, new_config)
    
    #Update the webviewconfiguration
    _WebNodeList[WebNode_id]["WebviewConfiguration"] = new_config
    
    # Reset ModbusSavedConfiguration
    _WebNodeList[WebNode_id]["ModbusSavedConfiguration"] = None
    




def _AddWebNode(C_node_id, node_type, GetParamFuncs, SetParamFuncs):
    """
    Load from the compiled code (.so file, aloready loaded into memmory)
    the configuration parameters of a specific Modbus plugin node.
    This function works with both client and server nodes, depending on the
    Get/SetParamFunc dictionaries passed to it (either the client or the server
    node versions of the Get/Set functions)
    """
    WebNode_entry = {}

    # Get the config_name from the C code...
    config_name = GetParamFuncs["config_name"](C_node_id)
    # Get the addr_type from the C code...
    # addr_type will be one of "tcp", "rtu" or "ascii"
    addr_type   = GetParamFuncs["addr_type"  ](C_node_id)   
    # For some operations we cannot use the config name (e.g. filename to store config)
    # because the user may be using characters that are invalid for that purpose ('/' for
    # example), so we create a hash of the config_name, and use that instead.
    config_hash = hashlib.md5(config_name).hexdigest()
    
    #PLCObject.LogMessage("Modbus web server extension::_AddWebNode("+str(C_node_id)+") config_name="+config_name)

    # Add the new entry to the global list
    # Note: it is OK, and actually necessary, to do this _before_ seting all the parameters in WebNode_entry
    #       WebNode_entry will be stored as a reference, so we can later insert parameters at will.
    global _WebNodeList
    _WebNodeList.append(WebNode_entry)
    WebNode_id = len(_WebNodeList) - 1

    # store all WebNode relevant data for future reference
    #
    # Note that "WebParamList" will reference one of:
    #  - TCPclient_parameters, TCPserver_parameters, RTUclient_parameters, RTUslave_parameters
    WebNode_entry["C_node_id"    ] = C_node_id
    WebNode_entry["config_name"  ] = config_name 
    WebNode_entry["config_hash"  ] = config_hash
    WebNode_entry["filename"     ] = os.path.join(_ModbusConfFiledir, "Modbus_config_" + config_hash + ".json")
    WebNode_entry["GetParamFuncs"] = GetParamFuncs
    WebNode_entry["SetParamFuncs"] = SetParamFuncs
    WebNode_entry["WebParamList" ] = WebParamListDictDict[node_type][addr_type] 
    WebNode_entry["addr_type"    ] = addr_type  # 'tcp', 'rtu', or 'ascii' (as returned by C function)
    WebNode_entry["node_type"    ] = node_type  # 'client', 'server'
        
    
    # Dictionary that contains the Modbus configuration currently being shown
    # on the web interface
    # This configuration will almost always be identical to the current
    # configuration in the PLC (i.e., the current state stored in the 
    # C variables in the .so file).
    # The configuration viewed on the web will only be different to the current 
    # configuration when the user edits the configuration, and when
    # the user asks to save an edited configuration that contains an error.
    WebNode_entry["WebviewConfiguration"] = None

    # Upon PLC load, this Dictionary is initialised with the Modbus configuration
    # hardcoded in the C file
    # (i.e. the configuration inserted in Beremiz IDE when project was compiled)
    WebNode_entry["DefaultConfiguration"] = _GetModbusPLCConfiguration(WebNode_id)
    WebNode_entry["WebviewConfiguration"] = WebNode_entry["DefaultConfiguration"]
    
    # Dictionary that stores the Modbus configuration currently stored in a file
    # Currently only used to decide whether or not to show the "Delete" button on the
    # web interface (only shown if "ModbusSavedConfiguration" is not None)
    SavedConfig = _GetModbusSavedConfiguration(WebNode_id)
    WebNode_entry["ModbusSavedConfiguration"] = SavedConfig
    
    if SavedConfig is not None:
        _SetModbusPLCConfiguration(WebNode_id, SavedConfig)
        WebNode_entry["WebviewConfiguration"] = SavedConfig
        
    # Define the format for the web form used to show/change the current parameters
    # We first declare a dynamic function to work as callback to obtain the default values for each parameter
    # Note: We transform every parameter into a string
    #       This is not strictly required for parameters of type annotate.Integer that will correctly
    #           accept the default value as an Integer python object
    #       This is obviously also not required for parameters of type annotate.String, that are
    #           always handled as strings.
    #       However, the annotate.Choice parameters (and all parameters that derive from it,
    #           sucn as Parity, Baud, etc.) require the default value as a string
    #           even though we store it as an integer, which is the data type expected
    #           by the set_***() C functions in mb_runtime.c
    def __GetWebviewConfigurationValue(ctx, argument):
        return str(_GetModbusWebviewConfigurationValue(ctx, WebNode_id, argument))
    
    webFormInterface = [(name, web_dtype (label=web_label, default=__GetWebviewConfigurationValue)) 
                    for name, web_label, c_dtype, web_dtype in WebNode_entry["WebParamList"]]

    # Configure the web interface to include the Modbus config parameters
    def __OnButtonSave(**kwargs):
        OnModbusButtonSave(WebNode_id=WebNode_id, **kwargs)

    WebSettings = NS.newExtensionSetting("Modbus #"+ str(WebNode_id), config_hash)

    WebSettings.addSettings(
        "ModbusConfigParm"          + config_hash,     # name (internal, may not contain spaces, ...)
        _("Modbus Configuration: ") + config_name,     # description (user visible label)
        webFormInterface,                              # fields
        _("Apply"), # button label
        __OnButtonSave)                                # callback   
    
    def __OnButtonReset(**kwargs):
        return OnModbusButtonReset(WebNode_id = WebNode_id, **kwargs)
            
    def getModbusConfigStatus():
        if WebNode_entry["WebviewConfiguration"] == WebNode_entry["DefaultConfiguration"]:
            return "Unchanged"
        return "Modified"

    WebSettings.addSettings(
        "ModbusConfigDelSaved"      + config_hash,  # name (internal, may not contain spaces, ...)
        _("Modbus Configuration: ") + config_name,  # description (user visible label)
        [ ("status",
           annotate.String(label=_("Current state"),
                           immutable=True,
                           default=lambda *k:getModbusConfigStatus())),
        ],                                       # fields  (empty, no parameters required!)
        _("Reset"), # button label
        __OnButtonReset)




def _runtime_%(location_str)s_modbus_websettings_init():
    """
    Callback function, called (by PLCObject.py) when a new PLC program
    (i.e. XXX.so file) is transfered to the PLC runtime
    and loaded into memory
    """

    #PLCObject.LogMessage("Modbus web server extension::OnLoadPLC() Called...")

    if PLCObject.PLClibraryHandle is None:
        # PLC was loaded but we don't have access to the library of compiled code (.so lib)?
        # Hmm... This shold never occur!! 
        return  
    
    # Get the number of Modbus Client and Servers (Modbus plugin)
    # configured in the currently loaded PLC project (i.e., the .so file)
    # If the "__modbus_plugin_client_node_count" 
    # or the "__modbus_plugin_server_node_count" C variables 
    # are not present in the .so file we conclude that the currently loaded 
    # PLC does not have the Modbus plugin included (situation (2b) described above init())
    try:
        # XXX TODO : stop reading from PLC .so file. This code is template code
        #            that can use modbus extension build data, such as client node count.
        client_count = ctypes.c_int.in_dll(PLCObject.PLClibraryHandle, "__modbus_plugin_client_node_count").value
        server_count = ctypes.c_int.in_dll(PLCObject.PLClibraryHandle, "__modbus_plugin_server_node_count").value
    except Exception:
        # Loaded PLC does not have the Modbus plugin => nothing to do
        #   (i.e. do _not_ configure and make available the Modbus web interface)
        return

    if client_count < 0: client_count = 0
    if server_count < 0: server_count = 0
    
    if (client_count == 0) and (server_count == 0):
        # The Modbus plugin in the loaded PLC does not have any client and servers configured
        #  => nothing to do (i.e. do _not_ configure and make available the Modbus web interface)
        return
    
    # Map the get/set functions (written in C code) we will be using to get/set the configuration parameters
    # Will contain references to the C functions (implemented in beremiz/modbus/mb_runtime.c)
    GetClientParamFuncs = {}
    SetClientParamFuncs = {}
    GetServerParamFuncs = {}
    SetServerParamFuncs = {}

    # XXX TODO : stop reading from PLC .so file. This code is template code
    #            that can use modbus extension build data
    for name, web_label, c_dtype, web_dtype in TCPclient_parameters + RTUclient_parameters + General_parameters:
        ParamFuncName                      = "__modbus_get_ClientNode_" + name        
        GetClientParamFuncs[name]          = getattr(PLCObject.PLClibraryHandle, ParamFuncName)
        GetClientParamFuncs[name].restype  = c_dtype
        GetClientParamFuncs[name].argtypes = [ctypes.c_int]
        
    for name, web_label, c_dtype, web_dtype in TCPclient_parameters + RTUclient_parameters:
        ParamFuncName                      = "__modbus_set_ClientNode_" + name
        SetClientParamFuncs[name]          = getattr(PLCObject.PLClibraryHandle, ParamFuncName)
        SetClientParamFuncs[name].restype  = None
        SetClientParamFuncs[name].argtypes = [ctypes.c_int, c_dtype]

    # XXX TODO : stop reading from PLC .so file. This code is template code
    #            that can use modbus extension build data
    for name, web_label, c_dtype, web_dtype in TCPserver_parameters + RTUslave_parameters + General_parameters:
        ParamFuncName                      = "__modbus_get_ServerNode_" + name        
        GetServerParamFuncs[name]          = getattr(PLCObject.PLClibraryHandle, ParamFuncName)
        GetServerParamFuncs[name].restype  = c_dtype
        GetServerParamFuncs[name].argtypes = [ctypes.c_int]
        
    for name, web_label, c_dtype, web_dtype in TCPserver_parameters + RTUslave_parameters:
        ParamFuncName                      = "__modbus_set_ServerNode_" + name
        SetServerParamFuncs[name]          = getattr(PLCObject.PLClibraryHandle, ParamFuncName)
        SetServerParamFuncs[name].restype  = None
        SetServerParamFuncs[name].argtypes = [ctypes.c_int, c_dtype]

    for node_id in range(client_count):
        _AddWebNode(node_id, "client" ,GetClientParamFuncs, SetClientParamFuncs)

    for node_id in range(server_count):
        _AddWebNode(node_id, "server", GetServerParamFuncs, SetServerParamFuncs)





def _runtime_%(location_str)s_modbus_websettings_cleanup():
    """
    Callback function, called (by PLCObject.py) when a PLC program is unloaded from memory
    """

    #PLCObject.LogMessage("Modbus web server extension::OnUnLoadPLC() Called...")
    
    # Delete the Modbus specific web interface extensions
    # (Safe to ask to delete, even if it has not been added!)
    global _WebNodeList
    for index, WebNode_entry in enumerate(_WebNodeList):
        config_hash = WebNode_entry["config_hash"]
        NS.removeExtensionSetting(config_hash)
        
    # Dele all entries...
    _WebNodeList = []

