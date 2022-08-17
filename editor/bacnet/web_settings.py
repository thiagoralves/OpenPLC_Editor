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


import json
import os
import ctypes

from formless import annotate, webform

import runtime.NevowServer as NS


# Will contain references to the C functions 
# (implemented in beremiz/bacnet/runtime/server.c)
# used to get/set the BACnet specific configuration paramters
BacnetGetParamFuncs = {}
BacnetSetParamFuncs = {}


# Upon PLC load, this Dictionary is initialised with the BACnet configuration
# hardcoded in the C file
# (i.e. the configuration inserted in Beremiz IDE when project was compiled)
_BacnetDefaultConfiguration = None


# Dictionary that contains the BACnet configuration currently being shown
# on the web interface
# This configuration will almost always be identical to the current
# configuration in the PLC (i.e., the current state stored in the 
# C variables in the .so file).
# The configuration viewed on the web will only be different to the current 
# configuration when the user edits the configuration, and when
# the user asks to save the edited configuration but it contains an error.
_BacnetWebviewConfiguration = None


# Dictionary that stores the BACnet configuration currently stored in a file
# Currently only used to decide whether or not to show the "Delete" button on the
# web interface (only shown if _BacnetSavedConfiguration is not None)
_BacnetSavedConfiguration = None


# File to which the new BACnet configuration gets stored on the PLC
# Note that the stored configuration is likely different to the
# configuration hardcoded in C generated code (.so file), so
# this file should be persistent across PLC reboots so we can
# re-configure the PLC (change values of variables in .so file)
# before it gets a chance to start running
#
#_BACnetConfFilename = None
_BACnetConfFilename = os.path.join(WorkingDir, "bacnetconf.json")



class BN_StrippedString(annotate.String):
    def __init__(self, *args, **kwargs):
        annotate.String.__init__(self, strip = True, *args, **kwargs)



BACnet_parameters = [
    #    param. name             label                                            ctype type      annotate type
    # (C code var name)         (used on web interface)                          (C data type)    (web data type)
    #                                                                                             (annotate.String,
    #                                                                                              annotate.Integer, ...)
    ("network_interface"      , _("Network Interface")                         , ctypes.c_char_p, BN_StrippedString),
    ("port_number"            , _("UDP Port Number")                           , ctypes.c_char_p, BN_StrippedString),
    ("comm_control_passwd"    , _("BACnet Communication Control Password")     , ctypes.c_char_p, annotate.String),
    ("device_id"              , _("BACnet Device ID")                          , ctypes.c_int,    annotate.Integer),
    ("device_name"            , _("BACnet Device Name")                        , ctypes.c_char_p, annotate.String),
    ("device_location"        , _("BACnet Device Location")                    , ctypes.c_char_p, annotate.String),
    ("device_description"     , _("BACnet Device Description")                 , ctypes.c_char_p, annotate.String),
    ("device_appsoftware_ver" , _("BACnet Device Application Software Version"), ctypes.c_char_p, annotate.String)
    ]






def _CheckBacnetPortnumber(port_number):
    """ check validity of the port number """
    try:
        portnum = int(port_number)
        if (portnum < 0) or (portnum > 65535):
           raise Exception
    except Exception:    
        return False
        
    return True    
    


def _CheckBacnetDeviceID(device_id):
    """ 
    # check validity of the Device ID 
    # NOTE: BACnet device (object) IDs are 22 bits long (not counting the 10 bits for the type ID)
    #       so the Device instance ID is limited from 0 to 22^2-1 = 4194303
    #       However, 4194303 is reserved for special use (similar to NULL pointer), so last
    #       valid ID becomes 4194302
    """
    try:
        devid = int(device_id)
        if (devid < 0) or (devid > 4194302):
            raise Exception
    except Exception:    
        return False
        
    return True    





def _CheckBacnetConfiguration(BACnetConfig):
    res = True    
    res = res and _CheckBacnetPortnumber(BACnetConfig["port_number"])
    res = res and _CheckBacnetDeviceID  (BACnetConfig["device_id"])
    return res



def _CheckBacnetWebConfiguration(BACnetConfig):
    res = True
    
    # check the port number
    if not _CheckBacnetPortnumber(BACnetConfig["port_number"]):
        raise annotate.ValidateError(
            {"port_number": "Invalid port number: " + str(BACnetConfig["port_number"])},
            _("BACnet configuration error:"))
        res = False
    
    if not _CheckBacnetDeviceID(BACnetConfig["device_id"]):
        raise annotate.ValidateError(
            {"device_id": "Invalid device ID: " + str(BACnetConfig["device_id"])},
            _("BACnet configuration error:"))
        res = False
        
    return res






def _SetBacnetSavedConfiguration(BACnetConfig):
    """ Stores in a file a dictionary containing the BACnet parameter configuration """
    global _BacnetSavedConfiguration

    if BACnetConfig == _BacnetDefaultConfiguration :
        _DelBacnetSavedConfiguration()
        _BacnetSavedConfiguration = None
    else :
        with open(os.path.realpath(_BACnetConfFilename), 'w') as f:
            json.dump(BACnetConfig, f, sort_keys=True, indent=4)
        _BacnetSavedConfiguration = BACnetConfig


def _DelBacnetSavedConfiguration():
    """ Deletes the file cotaining the persistent BACnet configuration """
    if os.path.exists(_BACnetConfFilename):
        os.remove(_BACnetConfFilename)


def _GetBacnetSavedConfiguration():
    """
    # Returns a dictionary containing the BACnet parameter configuration
    # that was last saved to file. If no file exists, then return None
    """
    try:
        #if os.path.isfile(_BACnetConfFilename):
        saved_config = json.load(open(_BACnetConfFilename))
    except Exception:    
        return None

    if _CheckBacnetConfiguration(saved_config):
        return saved_config
    else:
        return None


def _GetBacnetPLCConfiguration():
    """
    # Returns a dictionary containing the current BACnet parameter configuration
    # stored in the C variables in the loaded PLC (.so file)
    """
    current_config = {}
    for par_name, x1, x2, x3 in BACnet_parameters:
        value = BacnetGetParamFuncs[par_name]()
        if value is not None:
            current_config[par_name] = value
    
    return current_config


def _SetBacnetPLCConfiguration(BACnetConfig):
    """
    # Stores the BACnet parameter configuration into the
    # the C variables in the loaded PLC (.so file)
    """
    for par_name in BACnetConfig:
        value = BACnetConfig[par_name]
        #PLCObject.LogMessage("BACnet web server extension::_SetBacnetPLCConfiguration()  Setting "
        #                       + par_name + " to " + str(value) )
        if value is not None:
            BacnetSetParamFuncs[par_name](value)
    # update the configuration shown on the web interface
    global _BacnetWebviewConfiguration 
    _BacnetWebviewConfiguration = _GetBacnetPLCConfiguration()



def _GetBacnetWebviewConfigurationValue(ctx, argument):
    """
    # Callback function, called by the web interface (NevowServer.py)
    # to fill in the default value of each parameter
    """
    try:
        return _BacnetWebviewConfiguration[argument.name]
    except Exception:
        return ""


# The configuration of the web form used to see/edit the BACnet parameters
webFormInterface = [(name, web_dtype (label=web_label, default=_GetBacnetWebviewConfigurationValue)) 
                    for name, web_label, c_dtype, web_dtype in BACnet_parameters]


def OnBacnetButtonSave(**kwargs):
    """
    # Function called when user clicks 'Save' button in web interface
    # The function will configure the BACnet plugin in the PLC with the values
    # specified in the web interface. However, values must be validated first!
    """

    #PLCObject.LogMessage("BACnet web server extension::OnBacnetButtonSave()  Called")
    
    newConfig = {}
    for par_name, x1, x2, x3 in BACnet_parameters:
        value = kwargs.get(par_name, None)
        if value is not None:
            newConfig[par_name] = value

    
    # First check if configuration is OK.
    if not _CheckBacnetWebConfiguration(newConfig):
        return

    # store to file the new configuration so that 
    # we can recoup the configuration the next time the PLC
    # has a cold start (i.e. when Beremiz_service.py is retarted)
    _SetBacnetSavedConfiguration(newConfig)

    # Configure PLC with the current BACnet parameters
    _SetBacnetPLCConfiguration(newConfig)



def OnBacnetButtonReset(**kwargs):
    """
    # Function called when user clicks 'Delete' button in web interface
    # The function will delete the file containing the persistent
    # BACnet configution
    """

    # Delete the file
    _DelBacnetSavedConfiguration()
    # Set the current configuration to the default (hardcoded in C)
    _SetBacnetPLCConfiguration(_BacnetDefaultConfiguration)
    # Reset global variable
    global _BacnetSavedConfiguration
    _BacnetSavedConfiguration = None



# location_str is replaced by extension's value in CTNGenerateC call
def _runtime_%(location_str)s_bacnet_websettings_init():
    """
    # Callback function, called (by PLCObject.py) when a new PLC program
    # (i.e. XXX.so file) is transfered to the PLC runtime
    # and oaded into memory
    """

    #PLCObject.LogMessage("BACnet web server extension::OnLoadPLC() Called...")

    if PLCObject.PLClibraryHandle is None:
        # PLC was loaded but we don't have access to the library of compiled code (.so lib)?
        # Hmm... This shold never occur!! 
        return  

    # Map the get/set functions (written in C code) we will be using to get/set the configuration parameters
    for name, web_label, c_dtype, web_dtype in BACnet_parameters:
        # location_str is replaced by extension's value in CTNGenerateC call
        GetParamFuncName = "__bacnet_%(location_str)s_get_ConfigParam_" + name
        SetParamFuncName = "__bacnet_%(location_str)s_set_ConfigParam_" + name
        
        # XXX TODO : stop reading from PLC .so file. This code is template code
        #            that can use modbus extension build data
        BacnetGetParamFuncs[name]          = getattr(PLCObject.PLClibraryHandle, GetParamFuncName)
        BacnetGetParamFuncs[name].restype  = c_dtype
        BacnetGetParamFuncs[name].argtypes = None
        
        BacnetSetParamFuncs[name]          = getattr(PLCObject.PLClibraryHandle, SetParamFuncName)
        BacnetSetParamFuncs[name].restype  = None
        BacnetSetParamFuncs[name].argtypes = [c_dtype]

    # Default configuration is the configuration done in Beremiz IDE
    # whose parameters get hardcoded into C, and compiled into the .so file
    # We read the default configuration from the .so file before the values
    # get changed by the user using the web server, or by the call (further on)
    # to _SetBacnetPLCConfiguration(BacnetSavedConfiguration)
    global _BacnetDefaultConfiguration 
    _BacnetDefaultConfiguration = _GetBacnetPLCConfiguration()
    
    # Show the current PLC configuration on the web interface        
    global _BacnetWebviewConfiguration
    _BacnetWebviewConfiguration = _GetBacnetPLCConfiguration()
 
    # Read from file the last used configuration, which is likely
    # different to the hardcoded configuration.
    # We Reset the current configuration (i.e., the config stored in the 
    # variables of .so file) to this saved configuration
    # so the PLC will start off with this saved configuration instead
    # of the hardcoded (in Beremiz C generated code) configuration values.
    #
    # Note that _SetBacnetPLCConfiguration() will also update 
    # _BacnetWebviewConfiguration , if necessary.
    global _BacnetSavedConfiguration
    _BacnetSavedConfiguration  = _GetBacnetSavedConfiguration()
    if _BacnetSavedConfiguration is not None:
        if _CheckBacnetConfiguration(_BacnetSavedConfiguration):
            _SetBacnetPLCConfiguration(_BacnetSavedConfiguration)
            
    WebSettings = NS.newExtensionSetting("BACnet extension", "bacnet_token")

    # Configure the web interface to include the BACnet config parameters
    WebSettings.addSettings(
        "BACnetConfigParm",                # name
        _("BACnet Configuration"),         # description
        webFormInterface,                  # fields
        _("Apply"),  # button label
        OnBacnetButtonSave)                      # callback    

    # Add the Delete button to the web interface
    WebSettings.addSettings(
        "BACnetConfigDelSaved",                   # name
        _("BACnet Configuration"),                # description
        [ ("status",
           annotate.String(label=_("Current state"),
                           immutable=True,
                           default=lambda *k:getBacnetConfigStatus())),
        ],                                       # fields  (empty, no parameters required!)
        _("Reset"), # button label
        OnBacnetButtonReset) 



def getBacnetConfigStatus():
    if _BacnetWebviewConfiguration == _BacnetDefaultConfiguration :
        return "Unchanged"
    return "Modified"


# location_str is replaced by extension's value in CTNGenerateC call
def _runtime_%(location_str)s_bacnet_websettings_cleanup():
    """
    # Callback function, called (by PLCObject.py) when a PLC program is unloaded from memory
    """

    #PLCObject.LogMessage("BACnet web server extension::OnUnLoadPLC() Called...")
    
    NS.removeExtensionSetting("bacnet_token")
    
    BacnetGetParamFuncs = {}
    BacnetSetParamFuncs = {}
    _BacnetWebviewConfiguration = None
    _BacnetSavedConfiguration   = None




