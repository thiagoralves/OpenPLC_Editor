#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (c) 2016 Mario de Sousa (msousa@fe.up.pt)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This code is made available on the understanding that it will not be
# used in safety-critical situations without a full and competent review.


from __future__ import absolute_import
import os
from six.moves import xrange

from modbus.mb_utils import *
from ConfigTreeNode import ConfigTreeNode
from PLCControler import LOCATION_CONFNODE, LOCATION_VAR_MEMORY
import util.paths as paths

ModbusPath = paths.ThirdPartyPath("Modbus")


#
#
#
# C L I E N T    R E Q U E S T            #
#
#
#


class _RequestPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ModbusRequest">
        <xsd:complexType>
          <xsd:attribute name="Function" type="xsd:string" use="optional" default="01 - Read Coils"/>
          <xsd:attribute name="SlaveID" use="optional" default="1">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="255"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Nr_of_Channels" use="optional" default="1">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="2000"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Start_Address" use="optional" default="0">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="65535"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Timeout_in_ms" use="optional" default="10">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="100000"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Write_on_change" type="xsd:boolean" use="optional" default="false"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """

    def GetParamsAttributes(self, path=None):
        infos = ConfigTreeNode.GetParamsAttributes(self, path=path)
        for element in infos:
            if element["name"] == "ModbusRequest":
                for child in element["children"]:
                    if child["name"] == "Function":
                        list = modbus_function_dict.keys()
                        list.sort()
                        child["type"] = list
        return infos

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        name = self.BaseParams.getName()
        address = self.GetParamsAttributes()[0]["children"][3]["value"]
        count = self.GetParamsAttributes()[0]["children"][2]["value"]
        function = self.GetParamsAttributes()[0]["children"][0]["value"]
        # 'BOOL' or 'WORD'
        datatype = modbus_function_dict[function][3]
        # 1 or 16
        datasize = modbus_function_dict[function][4]
        # 'Q' for coils and holding registers, 'I' for input discretes and input registers
        # datazone = modbus_function_dict[function][5]
        # 'X' for bits, 'W' for words
        datatacc = modbus_function_dict[function][6]
        # 'Coil', 'Holding Register', 'Input Discrete' or 'Input Register'
        dataname = modbus_function_dict[function][7]
        # start off with a boolean entry
        # This is a flag used to allow the user program to control when to 
        # execute the Modbus request.
        # NOTE: If the Modbus request has a 'current_location' of
        #          %QX1.2.3
        #       then the execution control flag will be
        #          %QX1.2.3.0.0
        #       and all the Modbus registers/coils will be
        #          %QX1.2.3.0
        #          %QX1.2.3.1
        #          %QX1.2.3.2
        #            ..
        #          %QX1.2.3.n
        entries = []
        entries.append({
            "name": "Execute request flag",
            "type": LOCATION_VAR_MEMORY,
            "size": 1,           # BOOL flag
            "IEC_type": "BOOL",  # BOOL flag
            "var_name": "var_name",
            "location": "X" + ".".join([str(i) for i in current_location]) + ".0.0",
            "description": "Modbus request execution control flag",
            "children": []})        
        entries.append({
            "name": "Modbus Request Status flag",
            "type": LOCATION_VAR_MEMORY,
            "size": 8,           # BYTE flag
            "IEC_type": "BYTE",  # BYTE flag
            "var_name": "var_name",
            "location": "B" + ".".join([str(i) for i in current_location]) + ".0.1",
            "description": "Modbus request status flag (0 -> OK, 1 -> Network error, 2 -> Received invalid frame, 3 -> Timeout, 4 -> Received error frame)",
            "children": []})        
        entries.append({
            "name": "Modbus Error Code",
            "type": LOCATION_VAR_MEMORY,
            "size": 8,           # BYTE flag
            "IEC_type": "BYTE",  # BYTE flag
            "var_name": "var_name",
            "location": "B" + ".".join([str(i) for i in current_location]) + ".0.2",
            "description": "Modbus Error Code received in Modbus error frame",
            "children": []})        
        for offset in range(address, address + count):
            entries.append({
                "name": dataname + " " + str(offset),
                "type": LOCATION_VAR_MEMORY,
                "size": datasize,
                "IEC_type": datatype,
                "var_name": "MB_" + "".join([w[0] for w in dataname.split()]) + "_" + str(offset),
                "location": datatacc + ".".join([str(i) for i in current_location]) + "." + str(offset),
                "description": "description",
                "children": []})
        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": ".".join([str(i) for i in current_location]) + ".x",
                "children": entries}

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing plugin IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        return [], "", False



#
#
#
# S E R V E R    M E M O R Y    A R E A       #
#
#
#

# dictionary implementing:
# key - string with the description we want in the request plugin GUI
# list - (modbus function number, request type, max count value)
modbus_memtype_dict = {
    "01 - Coils":            ('1', 'rw_bits',  65536, "BOOL", 1, "Q", "X", "Coil"),
    "02 - Input Discretes":  ('2', 'ro_bits',  65536, "BOOL", 1, "I", "X", "Input Discrete"),
    "03 - Holding Registers": ('3', 'rw_words', 65536, "WORD", 16, "Q", "W", "Holding Register"),
    "04 - Input Registers":  ('4', 'ro_words', 65536, "WORD", 16, "I", "W", "Input Register"),
}


class _MemoryAreaPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="MemoryArea">
        <xsd:complexType>
          <xsd:attribute name="MemoryAreaType" type="xsd:string" use="optional" default="01 - Coils"/>
          <xsd:attribute name="Nr_of_Channels" use="optional" default="1">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="65536"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Start_Address" use="optional" default="0">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="65535"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """

    def GetParamsAttributes(self, path=None):
        infos = ConfigTreeNode.GetParamsAttributes(self, path=path)
        for element in infos:
            if element["name"] == "MemoryArea":
                for child in element["children"]:
                    if child["name"] == "MemoryAreaType":
                        list = modbus_memtype_dict.keys()
                        list.sort()
                        child["type"] = list
        return infos

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        name = self.BaseParams.getName()
        address = self.GetParamsAttributes()[0]["children"][2]["value"]
        count = self.GetParamsAttributes()[0]["children"][1]["value"]
        function = self.GetParamsAttributes()[0]["children"][0]["value"]
        # 'BOOL' or 'WORD'
        datatype = modbus_memtype_dict[function][3]
        # 1 or 16
        datasize = modbus_memtype_dict[function][4]
        # 'Q' for coils and holding registers, 'I' for input discretes and input registers
        # datazone = modbus_memtype_dict[function][5]
        # 'X' for bits, 'W' for words
        datatacc = modbus_memtype_dict[function][6]
        # 'Coil', 'Holding Register', 'Input Discrete' or 'Input Register'
        dataname = modbus_memtype_dict[function][7]
        entries = []
        for offset in range(address, address + count):
            entries.append({
                "name": dataname + " " + str(offset),
                "type": LOCATION_VAR_MEMORY,
                "size": datasize,
                "IEC_type": datatype,
                "var_name": "MB_" + "".join([w[0] for w in dataname.split()]) + "_" + str(offset),
                "location": datatacc + ".".join([str(i) for i in current_location]) + "." + str(offset),
                "description": "description",
                "children": []})
        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": ".".join([str(i) for i in current_location]) + ".x",
                "children": entries}

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing plugin IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        return [], "", False


#
#
#
# T C P    C L I E N T                 #
#
#
#

# XXX TODO "Configuration_Name" should disapear in favor of CTN Name, which is already unique

class _ModbusTCPclientPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ModbusTCPclient">
        <xsd:complexType>
          <xsd:attribute name="Configuration_Name" type="xsd:string" use="optional" default=""/>
          <xsd:attribute name="Remote_IP_Address" type="xsd:string" use="optional" default="localhost"/>
          <xsd:attribute name="Remote_Port_Number" type="xsd:string" use="optional" default="502"/>
          <xsd:attribute name="Invocation_Rate_in_ms" use="optional" default="100">
            <xsd:simpleType>
                <xsd:restriction base="xsd:unsignedLong">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="2147483647"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    # NOTE: Max value of 2147483647 (i32_max) for Invocation_Rate_in_ms
    # corresponds to aprox 25 days.
    CTNChildrenTypes = [("ModbusRequest", _RequestPlug, "Request")]
    # TODO: Replace with CTNType !!!
    PlugType = "ModbusTCPclient"


    def __init__(self):
        # NOTE:
        # The ModbusTCPclient attribute is added dynamically by ConfigTreeNode._AddParamsMembers()
        # It will be an XML parser object created by
        # GenerateParserFromXSDstring(self.XSD).CreateRoot()
        
        # Set the default value for the "Configuration_Name" parameter
        # The default value will need to be different for each instance of the 
        # _ModbusTCPclientPlug class, so we cannot hardcode the default value in the XSD above
        # This value will be used by the web interface 
        #   (i.e. the extension to the web server used to configure the Modbus parameters).
        #   (The web server is run/activated/started by Beremiz_service.py)
        #   (The web server code is found in runtime/NevowServer.py)
        #   (The Modbus extension to the web server is found in runtime/Modbus_config.py)
        loc_str = ".".join(map(str, self.GetCurrentLocation()))
        self.ModbusTCPclient.setConfiguration_Name("Modbus TCP Client " + loc_str)
        
    # Return the number of (modbus library) nodes this specific TCP client will need
    #   return type: (tcp nodes, rtu nodes, ascii nodes)
    def GetNodeCount(self):
        return (1, 0, 0)

    def GetConfigName(self):
        """ Return the node's Configuration_Name """
        return self.ModbusTCPclient.getConfiguration_Name()

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing plugin IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        return [], "", False


#
#
#
# T C P    S E R V E R                 #
#
#
#

# XXX TODO "Configuration_Name" should disapear in favor of CTN Name, which is already unique

class _ModbusTCPserverPlug(object):
    # NOTE: the Port number is a 'string' and not an 'integer'!
    # This is because the underlying modbus library accepts strings
    # (e.g.: well known port names!)
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ModbusServerNode">
        <xsd:complexType>
          <xsd:attribute name="Configuration_Name" type="xsd:string" use="optional" default=""/>
          <xsd:attribute name="Local_IP_Address" type="xsd:string" use="optional"  default="#ANY#"/>
          <xsd:attribute name="Local_Port_Number" type="xsd:string" use="optional" default="502"/>
          <xsd:attribute name="SlaveID" use="optional" default="0">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="255"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    CTNChildrenTypes = [("MemoryArea", _MemoryAreaPlug, "Memory Area")]
    # TODO: Replace with CTNType !!!
    PlugType = "ModbusTCPserver"

    def __init__(self):
        # NOTE:
        # The ModbusServerNode attribute is added dynamically by ConfigTreeNode._AddParamsMembers()
        # It will be an XML parser object created by
        # GenerateParserFromXSDstring(self.XSD).CreateRoot()
        
        # Set the default value for the "Configuration_Name" parameter
        # The default value will need to be different for each instance of the 
        # _ModbusTCPclientPlug class, so we cannot hardcode the default value in the XSD above
        # This value will be used by the web interface 
        #   (i.e. the extension to the web server used to configure the Modbus parameters).
        #   (The web server is run/activated/started by Beremiz_service.py)
        #   (The web server code is found in runtime/NevowServer.py)
        #   (The Modbus extension to the web server is found in runtime/Modbus_config.py)
        loc_str = ".".join(map(str, self.GetCurrentLocation()))
        self.ModbusServerNode.setConfiguration_Name("Modbus TCP Server " + loc_str)
        
    # Return the number of (modbus library) nodes this specific TCP server will need
    #   return type: (tcp nodes, rtu nodes, ascii nodes)
    def GetNodeCount(self):
        return (1, 0, 0)

    # Return a list with a single tuple conatining the (location, IP address, port number)
    #     location   : location of this node in the configuration tree
    #     port number: IP port used by this Modbus/IP server
    #     IP address : IP address of the network interface on which the server will be listening
    #                  ("", "*", or "#ANY#" => listening on all interfaces!)
    def GetIPServerPortNumbers(self):
        port = self.ModbusServerNode.getLocal_Port_Number()
        addr = self.ModbusServerNode.getLocal_IP_Address()
        return [(self.GetCurrentLocation(), addr, port)]

    def GetConfigName(self):
        """ Return the node's Configuration_Name """
        return self.ModbusServerNode.getConfiguration_Name()

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        name             = self.BaseParams.getName()
        # start off with flags that count the number of Modbus requests/transactions
        # handled by this Modbus server/slave.
        # These flags are mapped onto located variables and therefore available to the user programs
        # May be used to detect communication errors.
        # execute the Modbus request.
        # NOTE: If the Modbus slave has a 'current_location' of
        #          %QX1.2
        #       then the "Modbus Read Request Counter"  will be %MD1.2.0
        #       then the "Modbus Write Request Counter" will be %MD1.2.1
        #       then the "Modbus Read Request Flag"     will be %MD1.2.2
        #       then the "Modbus Write Request Flag"    will be %MD1.2.3
        #
        # Note that any MemoryArea contained under this server/slave
        # will ocupy the locations of type
        #          %MX or %MW
        # which will never clash with the %MD used here.
        # Additionaly, any MemoryArea contained under this server/slave
        # will ocupy locations with
        #           %M1.2.a.b (with a and b being numbers in range 0, 1, ...)
        # and therefore never ocupy the locations
        #           %M1.2.0
        #           %M1.2.1
        #           %M1.2.2
        #           %M1.2.3
        # used by the following flags/counters.
        entries = []
        entries.append({
            "name": "Modbus Read Request Counter",
            "type": LOCATION_VAR_MEMORY,
            "size": 32,           # UDINT flag
            "IEC_type": "UDINT",  # UDINT flag
            "var_name": "var_name",
            "location": "D" + ".".join([str(i) for i in current_location]) + ".0",
            "description": "Modbus read request counter",
            "children": []})        
        entries.append({
            "name": "Modbus Write Request Counter",
            "type": LOCATION_VAR_MEMORY,
            "size": 32,           # UDINT flag
            "IEC_type": "UDINT",  # UDINT flag
            "var_name": "var_name",
            "location": "D" + ".".join([str(i) for i in current_location]) + ".1",
            "description": "Modbus write request counter",
            "children": []})        
        entries.append({
            "name": "Modbus Read Request Flag",
            "type": LOCATION_VAR_MEMORY,
            "size": 1,            # BOOL flag
            "IEC_type": "BOOL",   # BOOL flag
            "var_name": "var_name",
            "location": "X" + ".".join([str(i) for i in current_location]) + ".2",
            "description": "Modbus read request flag",
            "children": []})        
        entries.append({
            "name": "Modbus write Request Flag",
            "type": LOCATION_VAR_MEMORY,
            "size": 1,            # BOOL flag
            "IEC_type": "BOOL",   # BOOL flag
            "var_name": "var_name",
            "location": "X" + ".".join([str(i) for i in current_location]) + ".3",
            "description": "Modbus write request flag",
            "children": []})        
        # recursively call all the Memory Areas under this Modbus server/save
        # i.e., all the children objects which will be of class _MemoryAreaPlug
        for child in self.IECSortedChildren():
            entries.append(child.GetVariableLocationTree())

        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": ".".join([str(i) for i in current_location]) + ".x",
                "children": entries}


    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing plugin IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        return [], "", False


#
#
#
# R T U    C L I E N T                 #
#
#
#

# XXX TODO "Configuration_Name" should disapear in favor of CTN Name, which is already unique

class _ModbusRTUclientPlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ModbusRTUclient">
        <xsd:complexType>
          <xsd:attribute name="Configuration_Name" type="xsd:string" use="optional" default=""/>
          <xsd:attribute name="Serial_Port" type="xsd:string"  use="optional" default="/dev/ttyS0"/>
          <xsd:attribute name="Baud_Rate"   type="xsd:string"  use="optional" default="9600"/>
          <xsd:attribute name="Parity"      type="xsd:string"  use="optional" default="even"/>
          <xsd:attribute name="Stop_Bits"   type="xsd:string"  use="optional" default="1"/>
          <xsd:attribute name="Invocation_Rate_in_ms" use="optional" default="100">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="2147483647"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    # NOTE: Max value of 2147483647 (i32_max) for Invocation_Rate_in_ms
    # corresponds to aprox 25 days.
    CTNChildrenTypes = [("ModbusRequest", _RequestPlug, "Request")]
    # TODO: Replace with CTNType !!!
    PlugType = "ModbusRTUclient"

    def __init__(self):
        # NOTE:
        # The ModbusRTUclient attribute is added dynamically by ConfigTreeNode._AddParamsMembers()
        # It will be an XML parser object created by
        # GenerateParserFromXSDstring(self.XSD).CreateRoot()
        
        # Set the default value for the "Configuration_Name" parameter
        # The default value will need to be different for each instance of the 
        # _ModbusTCPclientPlug class, so we cannot hardcode the default value in the XSD above
        # This value will be used by the web interface 
        #   (i.e. the extension to the web server used to configure the Modbus parameters).
        #   (The web server is run/activated/started by Beremiz_service.py)
        #   (The web server code is found in runtime/NevowServer.py)
        #   (The Modbus extension to the web server is found in runtime/Modbus_config.py)
        loc_str = ".".join(map(str, self.GetCurrentLocation()))
        self.ModbusRTUclient.setConfiguration_Name("Modbus RTU Client " + loc_str)
        
    def GetParamsAttributes(self, path=None):
        infos = ConfigTreeNode.GetParamsAttributes(self, path=path)
        for element in infos:
            if element["name"] == "ModbusRTUclient":
                for child in element["children"]:
                    if child["name"] == "Baud_Rate":
                        child["type"] = modbus_serial_baudrate_list
                    if child["name"] == "Stop_Bits":
                        child["type"] = modbus_serial_stopbits_list
                    if child["name"] == "Parity":
                        child["type"] = modbus_serial_parity_dict.keys()
        return infos

    # Return the number of (modbus library) nodes this specific RTU client will need
    #   return type: (tcp nodes, rtu nodes, ascii nodes)
    def GetNodeCount(self):
        return (0, 1, 0)

    def GetConfigName(self):
        """ Return the node's Configuration_Name """
        return self.ModbusRTUclient.getConfiguration_Name()

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing plugin IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        return [], "", False


#
#
#
# R T U    S L A V E                   #
#
#
#

# XXX TODO "Configuration_Name" should disapear in favor of CTN Name, which is already unique

class _ModbusRTUslavePlug(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ModbusRTUslave">
        <xsd:complexType>
          <xsd:attribute name="Configuration_Name" type="xsd:string" use="optional" default=""/>
          <xsd:attribute name="Serial_Port" type="xsd:string"  use="optional" default="/dev/ttyS0"/>
          <xsd:attribute name="Baud_Rate"   type="xsd:string"  use="optional" default="9600"/>
          <xsd:attribute name="Parity"      type="xsd:string"  use="optional" default="even"/>
          <xsd:attribute name="Stop_Bits"   type="xsd:string"  use="optional" default="1"/>
          <xsd:attribute name="SlaveID" use="optional" default="1">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="255"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    CTNChildrenTypes = [("MemoryArea", _MemoryAreaPlug, "Memory Area")]
    # TODO: Replace with CTNType !!!
    PlugType = "ModbusRTUslave"

    def __init__(self):
        # NOTE:
        # The ModbusRTUslave attribute is added dynamically by ConfigTreeNode._AddParamsMembers()
        # It will be an XML parser object created by
        # GenerateParserFromXSDstring(self.XSD).CreateRoot()
        
        # Set the default value for the "Configuration_Name" parameter
        # The default value will need to be different for each instance of the 
        # _ModbusTCPclientPlug class, so we cannot hardcode the default value in the XSD above
        # This value will be used by the web interface 
        #   (i.e. the extension to the web server used to configure the Modbus parameters).
        #   (The web server is run/activated/started by Beremiz_service.py)
        #   (The web server code is found in runtime/NevowServer.py)
        #   (The Modbus extension to the web server is found in runtime/Modbus_config.py)
        loc_str = ".".join(map(str, self.GetCurrentLocation()))
        self.ModbusRTUslave.setConfiguration_Name("Modbus RTU Slave " + loc_str)
        
    def GetParamsAttributes(self, path=None):
        infos = ConfigTreeNode.GetParamsAttributes(self, path=path)
        for element in infos:
            if element["name"] == "ModbusRTUslave":
                for child in element["children"]:
                    if child["name"] == "Baud_Rate":
                        child["type"] = modbus_serial_baudrate_list
                    if child["name"] == "Stop_Bits":
                        child["type"] = modbus_serial_stopbits_list
                    if child["name"] == "Parity":
                        child["type"] = modbus_serial_parity_dict.keys()
        return infos

    # Return the number of (modbus library) nodes this specific RTU slave will need
    #   return type: (tcp nodes, rtu nodes, ascii nodes)
    def GetNodeCount(self):
        return (0, 1, 0)

    def GetConfigName(self):
        """ Return the node's Configuration_Name """
        return self.ModbusRTUslave.getConfiguration_Name()

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        name             = self.BaseParams.getName()
        # start off with flags that count the number of Modbus requests/transactions
        # handled by this Modbus server/slave.
        # These flags are mapped onto located variables and therefore available to the user programs
        # May be used to detect communication errors.
        # execute the Modbus request.
        # NOTE: If the Modbus slave has a 'current_location' of
        #          %QX1.2
        #       then the "Modbus Read Request Counter"  will be %MD1.2.0
        #       then the "Modbus Write Request Counter" will be %MD1.2.1
        #       then the "Modbus Read Request Flag"     will be %MD1.2.2
        #       then the "Modbus Write Request Flag"    will be %MD1.2.3
        #
        # Note that any MemoryArea contained under this server/slave
        # will ocupy the locations of type
        #          %MX or %MW
        # which will never clash with the %MD used here.
        # Additionaly, any MemoryArea contained under this server/slave
        # will ocupy locations with
        #           %M1.2.a.b (with a and b being numbers in range 0, 1, ...)
        # and therefore never ocupy the locations
        #           %M1.2.0
        #           %M1.2.1
        #           %M1.2.2
        #           %M1.2.3
        # used by the following flags/counters.
        entries = []
        entries.append({
            "name": "Modbus Read Request Counter",
            "type": LOCATION_VAR_MEMORY,
            "size": 32,           # UDINT flag
            "IEC_type": "UDINT",  # UDINT flag
            "var_name": "var_name",
            "location": "D" + ".".join([str(i) for i in current_location]) + ".0",
            "description": "Modbus read request counter",
            "children": []})        
        entries.append({
            "name": "Modbus Write Request Counter",
            "type": LOCATION_VAR_MEMORY,
            "size": 32,           # UDINT flag
            "IEC_type": "UDINT",  # UDINT flag
            "var_name": "var_name",
            "location": "D" + ".".join([str(i) for i in current_location]) + ".1",
            "description": "Modbus write request counter",
            "children": []})        
        entries.append({
            "name": "Modbus Read Request Flag",
            "type": LOCATION_VAR_MEMORY,
            "size": 1,            # BOOL flag
            "IEC_type": "BOOL",   # BOOL flag
            "var_name": "var_name",
            "location": "X" + ".".join([str(i) for i in current_location]) + ".2",
            "description": "Modbus read request flag",
            "children": []})        
        entries.append({
            "name": "Modbus write Request Flag",
            "type": LOCATION_VAR_MEMORY,
            "size": 1,            # BOOL flag
            "IEC_type": "BOOL",   # BOOL flag
            "var_name": "var_name",
            "location": "X" + ".".join([str(i) for i in current_location]) + ".3",
            "description": "Modbus write request flag",
            "children": []})        
        # recursively call all the Memory Areas under this Modbus server/save
        # i.e., all the children objects which will be of class _MemoryAreaPlug
        for child in self.IECSortedChildren():
            entries.append(child.GetVariableLocationTree())

        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": ".".join([str(i) for i in current_location]) + ".x",
                "children": entries}


    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing plugin IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        return [], "", False


def _lt_to_str(loctuple):
    return '.'.join(map(str, loctuple))


#
#
#
# R O O T    C L A S S                #
#
#
#
class RootClass(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ModbusRoot">
        <xsd:complexType>
          <xsd:attribute name="MaxRemoteTCPclients" use="optional" default="10">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="65535"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    CTNChildrenTypes = [("ModbusTCPclient", _ModbusTCPclientPlug, "Modbus TCP Client"),
                        ("ModbusTCPserver", _ModbusTCPserverPlug, "Modbus TCP Server"),
                        ("ModbusRTUclient", _ModbusRTUclientPlug, "Modbus RTU Client"),
                        ("ModbusRTUslave", _ModbusRTUslavePlug,  "Modbus RTU Slave")]

    # Return the number of (modbus library) nodes this specific instance of the modbus plugin will need
    #   return type: (tcp nodes, rtu nodes, ascii nodes)
    def GetNodeCount(self):
        max_remote_tcpclient = self.GetParamsAttributes()[
            0]["children"][0]["value"]
        total_node_count = (max_remote_tcpclient, 0, 0)
        for child in self.IECSortedChildren():
            # ask each child how many nodes it needs, and add them all up.
            total_node_count = tuple(
                x1 + x2 for x1, x2 in zip(total_node_count, child.GetNodeCount()))
        return total_node_count

    # Return a list with tuples of the (location, port numbers) used by all the Modbus/IP servers
    def GetIPServerPortNumbers(self):
        IPServer_port_numbers = []
        for child in self.IECSortedChildren():
            if child.CTNType == "ModbusTCPserver":
                IPServer_port_numbers.extend(child.GetIPServerPortNumbers())
        return IPServer_port_numbers

    # Return a list with tuples of the (location, configuration_name) used by all the Modbus nodes (tcp/rtu, clients/servers)
    def GetConfigNames(self):
        Node_Configuration_Names = []
        for child in self.IECSortedChildren():
            Node_Configuration_Names.extend([(child.GetCurrentLocation(), child.GetConfigName())])
        return Node_Configuration_Names

    def CTNGenerate_C(self, buildpath, locations):
        # print "#############"
        # print self.__class__
        # print type(self)
        # print "self.CTNType >>>"
        # print self.CTNType
        # print "type(self.CTNType) >>>"
        # print type(self.CTNType)
        # print "#############"

        loc_dict = {"locstr": "_".join(map(str, self.GetCurrentLocation()))}

        # Determine the number of (modbus library) nodes ALL instances of the modbus plugin will need
        #   total_node_count: (tcp nodes, rtu nodes, ascii nodes)
        #
        # Also get a list with tuples of (location, IP address, port number) used by all the Modbus/IP server nodes
        #   This list is later used to search for duplicates in port numbers!
        #   IPServer_port_numbers = [(location, IP address, port number), ...]
        #       location            : tuple similar to (0, 3, 1) representing the location in the configuration tree "0.3.1.x"
        #       IPserver_port_number: a number (i.e. port number used by the Modbus/IP server)
        #       IP address          : IP address of the network interface on which the server will be listening
        #                             ("", "*", or "#ANY#" => listening on all interfaces!)
        #
        # Also get a list with tuples of (location, Configuration_Name) used by all the Modbus nodes
        #   This list is later used to search for duplicates in Configuration Names!
        #   Node_Configuration_Names = [(location, Configuration_Name), ...]
        #       location          : tuple similar to (0, 3, 1) representing the location in the configuration tree "0.3.1.x"
        #       Configuration_Name: the "Configuration_Name" string
        total_node_count = (0, 0, 0)
        IPServer_port_numbers    = []
        Node_Configuration_Names = []
        for CTNInstance in self.GetCTRoot().IterChildren():
            if CTNInstance.CTNType == "modbus":
                # ask each modbus plugin instance how many nodes it needs, and add them all up.
                total_node_count = tuple(x1 + x2 for x1, x2 in zip(total_node_count, CTNInstance.GetNodeCount()))
                IPServer_port_numbers.   extend(CTNInstance.GetIPServerPortNumbers())
                Node_Configuration_Names.extend(CTNInstance.GetConfigNames        ())

        # Search for use of duplicate Configuration_Names by Modbus nodes
        # Configuration Names are used by the web server running on the PLC
        # (more precisely, run by Beremiz_service.py) to identify and allow 
        # changing the Modbus parameters after the program has been downloaded 
        # to the PLC (but before it is started)
        # With clashes in the configuration names, the Modbus nodes will not be
        # distinguasheble on the web interface!
        for i in range(0, len(Node_Configuration_Names) - 1):
            for j in range(i + 1, len(Node_Configuration_Names)):
                if Node_Configuration_Names[i][1] == Node_Configuration_Names[j][1]:
                    error_message = _("Error: Modbus plugin nodes %{a1}.x and %{a2}.x use the same Configuration_Name \"{a3}\".\n").format(
                                        a1=_lt_to_str(Node_Configuration_Names[i][0]),
                                        a2=_lt_to_str(Node_Configuration_Names[j][0]),
                                        a3=Node_Configuration_Names[j][1])
                    self.FatalError(error_message)

        # Search for use of duplicate port numbers by Modbus/IP servers
        # Note: We only consider duplicate port numbers if using the same network interface!
        i = 0
        for loc1, addr1, port1 in IPServer_port_numbers[:-1]:
            i = i + 1
            for loc2, addr2, port2 in IPServer_port_numbers[i:]:
                if (port1 == port2) and (
                          (addr1 == addr2)   # on the same network interface
                       or (addr1 == "") or (addr1 == "*") or (addr1 == "#ANY#") # or one (or both) of the servers
                       or (addr2 == "") or (addr2 == "*") or (addr2 == "#ANY#") # use all available network interfaces
                   ):
                    error_message = _("Error: Modbus plugin nodes %{a1}.x and %{a2}.x use same port number \"{a3}\" " + 
                                      "on the same (or overlapping) network interfaces \"{a4}\" and \"{a5}\".\n").format(
                                        a1=_lt_to_str(loc1), a2=_lt_to_str(loc2), a3=port1, a4=addr1, a5=addr2)
                    self.FatalError(error_message)

        # Determine the current location in Beremiz's project configuration
        # tree
        current_location = self.GetCurrentLocation()

        # define a unique name for the generated C and h files
        prefix = "_".join(map(str, current_location))
        Gen_MB_c_path = os.path.join(buildpath, "MB_%s.c" % prefix)
        Gen_MB_h_path = os.path.join(buildpath, "MB_%s.h" % prefix)
        c_filename = os.path.join(os.path.split(__file__)[0], "mb_runtime.c")
        h_filename = os.path.join(os.path.split(__file__)[0], "mb_runtime.h")

        tcpclient_reqs_count = 0
        rtuclient_reqs_count = 0
        ascclient_reqs_count = 0
        tcpclient_node_count = 0
        rtuclient_node_count = 0
        ascclient_node_count = 0
        tcpserver_node_count = 0
        rtuserver_node_count = 0
        ascserver_node_count = 0
        nodeid = 0
        client_nodeid = 0
        client_requestid = 0
        server_id = 0

        server_node_list = []
        client_node_list = []
        client_request_list = []
        server_memarea_list = []
        loc_vars = []
        loc_vars_list = []  # list of variables already declared in C code!
        for child in self.IECSortedChildren():
            # print "<<<<<<<<<<<<<"
            # print "child (self.IECSortedChildren())----->"
            # print child.__class__
            # print ">>>>>>>>>>>>>"
            #
            if child.PlugType == "ModbusTCPserver":
                tcpserver_node_count += 1
                new_node = GetTCPServerNodePrinted(self, child)
                if new_node is None:
                    return [], "", False
                server_node_list.append(new_node)                
                #        We currently add 4 flags/counters to each Modbus server/slave
                #
                #        We add the Modbus read/write counter/flag to each Modbus slave/server
                #        to allow the user program to determine if the slave is being actively
                #        read from or written by by a remote Modbus client.
                for iecvar in child.GetLocations():
                    #print "child" + repr(iecvar)
                    if (len(iecvar["LOC"]) == 3) and (str(iecvar["NAME"]) not in loc_vars_list):
                        # Add if it is a "Modbus Read Request Counter" (mapped onto %MDa.b.0), so last number is a '0'
                        if iecvar["LOC"][2] == 0:
                            loc_vars.append("u32 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_read_req_counter;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                        # Add if it is a "Modbus Write Request Counter" (mapped onto %MDa.b.1), so last number is a '1'
                        if iecvar["LOC"][2] == 1:
                            loc_vars.append("u32 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_write_req_counter;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                        # Add if it is a "Modbus Read Request Flag" (mapped onto %MDa.b.2), so last number is a '2'
                        if iecvar["LOC"][2] == 2:
                            loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_read_req_flag;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                        # Add if it is a "Modbus Write Request Counter" (mapped onto %MDa.b.3), so last number is a '3'
                        if iecvar["LOC"][2] == 3:
                            loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_write_req_flag;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                
                for subchild in child.IECSortedChildren():
                    new_memarea = GetTCPServerMemAreaPrinted(self, subchild, nodeid)
                    if new_memarea is None:
                        return [], "", False
                    server_memarea_list.append(new_memarea)
                    function = subchild.GetParamsAttributes()[0]["children"][0]["value"]
                    # 'ro_bits', 'rw_bits', 'ro_words' or 'rw_words'
                    memarea = modbus_memtype_dict[function][1]
                    for iecvar in subchild.GetLocations():
                        if len(iecvar["LOC"]) == 4:
                            #print "subchild" + repr(iecvar)
                            absloute_address = iecvar["LOC"][3]
                            start_address = int(GetCTVal(subchild, 2))
                            relative_addr = absloute_address - start_address
                            # test if relative address in request specified range
                            if relative_addr in xrange(int(GetCTVal(subchild, 1))):
                                if str(iecvar["NAME"]) not in loc_vars_list:
                                    loc_vars.append("u16 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.%s[%d];" % (
                                        server_id, memarea, absloute_address))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                server_id += 1
            #
            if child.PlugType == "ModbusRTUslave":
                rtuserver_node_count += 1
                new_node = GetRTUSlaveNodePrinted(self, child)
                if new_node is None:
                    return [], "", False
                server_node_list.append(new_node)
                #        We currently add 4 flags/counters to each Modbus server/slave
                #
                #        We add the Modbus read/write counter/flag to each Modbus slave/server
                #        to allow the user program to determine if the slave is being actively
                #        read from or written by by a remote Modbus client.
                for iecvar in child.GetLocations():
                    #print "child" + repr(iecvar)
                    if (len(iecvar["LOC"]) == 3) and (str(iecvar["NAME"]) not in loc_vars_list):
                        # Add if it is a "Modbus Read Request Counter" (mapped onto %MDa.b.0), so last number is a '0'
                        if iecvar["LOC"][2] == 0:
                            loc_vars.append("u32 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_read_req_counter;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                        # Add if it is a "Modbus Write Request Counter" (mapped onto %MDa.b.1), so last number is a '1'
                        if iecvar["LOC"][2] == 1:
                            loc_vars.append("u32 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_write_req_counter;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                        # Add if it is a "Modbus Read Request Flag" (mapped onto %MDa.b.2), so last number is a '2'
                        if iecvar["LOC"][2] == 2:
                            loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_read_req_flag;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))
                        # Add if it is a "Modbus Write Request Counter" (mapped onto %MDa.b.3), so last number is a '3'
                        if iecvar["LOC"][2] == 3:
                            loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.flag_write_req_flag;" % (server_id))
                            loc_vars_list.append(str(iecvar["NAME"]))

                for subchild in child.IECSortedChildren():
                    new_memarea = GetTCPServerMemAreaPrinted(
                        self, subchild, nodeid)
                    if new_memarea is None:
                        return [], "", False
                    server_memarea_list.append(new_memarea)
                    function = subchild.GetParamsAttributes()[0]["children"][0]["value"]
                    # 'ro_bits', 'rw_bits', 'ro_words' or 'rw_words'
                    memarea = modbus_memtype_dict[function][1]
                    for iecvar in subchild.GetLocations():
                        if len(iecvar["LOC"]) == 4:
                            # print repr(iecvar)
                            absloute_address = iecvar["LOC"][3]
                            start_address = int(GetCTVal(subchild, 2))
                            relative_addr = absloute_address - start_address
                            # test if relative address in request specified range
                            if relative_addr in xrange(int(GetCTVal(subchild, 1))):
                                if str(iecvar["NAME"]) not in loc_vars_list:
                                    loc_vars.append("u16 *" + str(iecvar["NAME"]) + " = &server_nodes[%d].mem_area.%s[%d];" % (
                                        server_id, memarea, absloute_address))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                server_id += 1
            #
            if child.PlugType == "ModbusTCPclient":
                tcpclient_reqs_count += len(child.IECSortedChildren())
                new_node = GetTCPClientNodePrinted(self, child)
                if new_node is None:
                    return [], "", False
                client_node_list.append(new_node)
                for subchild in child.IECSortedChildren():
                    new_req = GetClientRequestPrinted(
                        self, subchild, client_nodeid)
                    if new_req is None:
                        return [], "", False
                    client_request_list.append(new_req)
                    for iecvar in subchild.GetLocations():
                        # absloute address - start address
                        relative_addr = iecvar["LOC"][3] - int(GetCTVal(subchild, 3))
                        # test if the located variable 
                        #    (a) has relative address in request specified range
                        #  AND is NOT
                        #    (b) is a flag added by this modbus plugin.
                        #        We currently add 3 flags: An execution control flag
                        #        and another two status flags.
                        #        We add the "Execution Control Flag" to each client request (one flag per request)
                        #        to allow the user program to control when to execute the request (if not executed periodically)
                        #        While all Modbus registers/coils are mapped onto a location
                        #        with 4 numbers (e.g. %QX0.1.2.55), this control flag is mapped
                        #        onto a location with 4 numbers (e.g. %QX0.1.2.0.0), where the last
                        #        two numbers are always '0.0', and the first two identify the request.
                        #        In the following if, we check for this condition by checking
                        #        if there are at least 4 or more number in the location's address.
                        if (        relative_addr in xrange(int(GetCTVal(subchild, 2)))  # condition (a) explained above
                            and len(iecvar["LOC"]) < 5):                                  # condition (b) explained above
                            if str(iecvar["NAME"]) not in loc_vars_list:
                                loc_vars.append("u16 *" + str(iecvar["NAME"]) + " = &client_requests[%d].plcv_buffer[%d];" % (client_requestid, relative_addr))
                                loc_vars_list.append(str(iecvar["NAME"]))
                        # Now add the located variable in case it is a flag (condition (b) above
                        if  len(iecvar["LOC"]) >= 5:       # condition (b) explained above
                            if str(iecvar["NAME"]) not in loc_vars_list:
                                # Add if it is a Execution Request Flag (mapped onto %QXa.b.c.0.0), so last number is a '0'
                                if iecvar["LOC"][4] == 0:
                                    loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &client_requests[%d].flag_exec_req;" % (client_requestid))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                                # Add if it is a "Modbus Request Status flag" (mapped onto %QWa.b.c.0.1), so last number is a '1'
                                #    -> will store the result of the last executed MB transaction
                                #         1 -> error accessing IP network, or serial interface
                                #         2 -> reply received from server was an invalid frame
                                #         3 -> server did not reply before timeout expired
                                #         4 -> server returned a valid Modbus error frame
                                #    -> will be reset (set to 0) once this MB transaction has completed sucesfully 
                                if iecvar["LOC"][4] == 1:
                                    loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &client_requests[%d].flag_tn_error_code;" % (client_requestid))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                                # Add if it is a "Modbus Error code" (mapped onto %QWa.b.c.0.2), so last number is a '2'
                                #    -> if "Modbus Request Status flag" is 4, this flag will store the MB error code returned by the MB server in a MB error frame
                                #    -> will be reset (set to 0) once this MB transaction has completed succesfully                                
                                if iecvar["LOC"][4] == 2:
                                    loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &client_requests[%d].flag_mb_error_code;" % (client_requestid))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                    client_requestid += 1
                tcpclient_node_count += 1
                client_nodeid += 1
            #
            if child.PlugType == "ModbusRTUclient":
                rtuclient_reqs_count += len(child.IECSortedChildren())
                new_node = GetRTUClientNodePrinted(self, child)
                if new_node is None:
                    return [], "", False
                client_node_list.append(new_node)
                for subchild in child.IECSortedChildren():
                    new_req = GetClientRequestPrinted(
                        self, subchild, client_nodeid)
                    if new_req is None:
                        return [], "", False
                    client_request_list.append(new_req)
                    for iecvar in subchild.GetLocations():
                        # absloute address - start address
                        relative_addr = iecvar["LOC"][3] - int(GetCTVal(subchild, 3))
                        # test if the located variable 
                        #    (a) has relative address in request specified range
                        #  AND is NOT
                        #    (b) is a flag added by this modbus plugin.
                        #        We currently add 3 flags: An execution control flag
                        #        and another two status flags.
                        #        We add the "Execution Control Flag" to each client request (one flag per request)
                        #        to allow the user program to control when to execute the request (if not executed periodically)
                        #        While all Modbus registers/coils are mapped onto a location
                        #        with 4 numbers (e.g. %QX0.1.2.55), this control flag is mapped
                        #        onto a location with 4 numbers (e.g. %QX0.1.2.0.0), where the last
                        #        two numbers are always '0.0', and the first two identify the request.
                        #        In the following if, we check for this condition by checking
                        #        if there are at least 4 or more number in the location's address.
                        if (        relative_addr in xrange(int(GetCTVal(subchild, 2)))  # condition (a) explained above
                            and len(iecvar["LOC"]) < 5):                                  # condition (b) explained above
                            if str(iecvar["NAME"]) not in loc_vars_list:
                                loc_vars.append(
                                    "u16 *" + str(iecvar["NAME"]) + " = &client_requests[%d].plcv_buffer[%d];" % (client_requestid, relative_addr))
                                loc_vars_list.append(str(iecvar["NAME"]))
                        # Now add the located variable in case it is a flag (condition (b) above
                        if  len(iecvar["LOC"]) >= 5:       # condition (b) explained above
                            if str(iecvar["NAME"]) not in loc_vars_list:
                                # Add if it is a Execution Request Flag (mapped onto %QXa.b.c.0.0), so last number is a '0'
                                if iecvar["LOC"][4] == 0:
                                    loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &client_requests[%d].flag_exec_req;" % (client_requestid))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                                # Add if it is a "Modbus Request Status flag" (mapped onto %QWa.b.c.0.1), so last number is a '1'
                                #    -> will store the result of the last executed MB transaction
                                #         1 -> error accessing IP network, or serial interface
                                #         2 -> reply received from server was an invalid frame
                                #         3 -> server did not reply before timeout expired
                                #         4 -> server returned a valid Modbus error frame
                                #    -> will be reset (set to 0) once this MB transaction has completed sucesfully 
                                if iecvar["LOC"][4] == 1:
                                    loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &client_requests[%d].flag_tn_error_code;" % (client_requestid))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                                # Add if it is a "Modbus Error code" (mapped onto %QWa.b.c.0.2), so last number is a '2'
                                #    -> if "Modbus Request Status flag" is 4, this flag will store the MB error code returned by the MB server in a MB error frame
                                #    -> will be reset (set to 0) once this MB transaction has completed succesfully                                
                                if iecvar["LOC"][4] == 2:
                                    loc_vars.append("u8 *" + str(iecvar["NAME"]) + " = &client_requests[%d].flag_mb_error_code;" % (client_requestid))
                                    loc_vars_list.append(str(iecvar["NAME"]))
                    client_requestid += 1
                rtuclient_node_count += 1
                client_nodeid += 1
            nodeid += 1

        loc_dict["loc_vars"] = "\n".join(loc_vars)
        loc_dict["server_nodes_params"] = ",\n\n".join(server_node_list)
        loc_dict["client_nodes_params"] = ",\n\n".join(client_node_list)
        loc_dict["client_req_params"] = ",\n\n".join(client_request_list)
        loc_dict["tcpclient_reqs_count"] = str(tcpclient_reqs_count)
        loc_dict["tcpclient_node_count"] = str(tcpclient_node_count)
        loc_dict["tcpserver_node_count"] = str(tcpserver_node_count)
        loc_dict["rtuclient_reqs_count"] = str(rtuclient_reqs_count)
        loc_dict["rtuclient_node_count"] = str(rtuclient_node_count)
        loc_dict["rtuserver_node_count"] = str(rtuserver_node_count)
        loc_dict["ascclient_reqs_count"] = str(ascclient_reqs_count)
        loc_dict["ascclient_node_count"] = str(ascclient_node_count)
        loc_dict["ascserver_node_count"] = str(ascserver_node_count)
        loc_dict["total_tcpnode_count"] = str(total_node_count[0])
        loc_dict["total_rtunode_count"] = str(total_node_count[1])
        loc_dict["total_ascnode_count"] = str(total_node_count[2])
        loc_dict["max_remote_tcpclient"] = int(
            self.GetParamsAttributes()[0]["children"][0]["value"])

        # get template file content into a string, format it with dict
        # and write it to proper .h file
        mb_main = open(h_filename).read() % loc_dict
        f = open(Gen_MB_h_path, 'w')
        f.write(mb_main)
        f.close()
        # same thing as above, but now to .c file
        mb_main = open(c_filename).read() % loc_dict
        f = open(Gen_MB_c_path, 'w')
        f.write(mb_main)
        f.close()

        LDFLAGS = []
        LDFLAGS.append(" \"-L" + ModbusPath + "\"")
        LDFLAGS.append(" \"" + os.path.join(ModbusPath, "libmb.a") + "\"")
        LDFLAGS.append(" \"-Wl,-rpath," + ModbusPath + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "mb_slave_and_master.o") + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "mb_slave.o") + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "mb_master.o") + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "mb_tcp.o")    + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "mb_rtu.o")    + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "mb_ascii.o")    + "\"")
        # LDFLAGS.append("\"" + os.path.join(ModbusPath, "sin_util.o")  + "\"")
        # Target is ARM with linux and not win on x86 so winsock2 (ws2_32) library is useless !!!
        # if os.name == 'nt':   # other possible values: 'posix' 'os2' 'ce' 'java' 'riscos'
        # LDFLAGS.append(" -lws2_32 ")  # on windows we need to load winsock
        # library!

        websettingfile = open(paths.AbsNeighbourFile(__file__, "web_settings.py"), 'r')
        websettingcode = websettingfile.read()
        websettingfile.close()

        location_str = "_".join(map(str, self.GetCurrentLocation()))
        websettingcode = websettingcode % locals()

        runtimefile_path = os.path.join(buildpath, "runtime_modbus_websettings.py")
        runtimefile = open(runtimefile_path, 'w')
        runtimefile.write(websettingcode)
        runtimefile.close()

        return ([(Gen_MB_c_path, ' -I"' + ModbusPath + '"')], LDFLAGS, True,
                ("runtime_%s_modbus_websettings.py" % location_str, open(runtimefile_path, "rb")),
        )
