#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import
from __future__ import division
import os
import sys
import shutil
import wx
from gnosis.xml.pickle import *  # pylint: disable=import-error
from gnosis.xml.pickle.util import setParanoia  # pylint: disable=import-error

import util.paths as paths
from util.TranslationCatalogs import AddCatalog
from ConfigTreeNode import ConfigTreeNode
from PLCControler import \
    LOCATION_CONFNODE, \
    LOCATION_VAR_MEMORY

base_folder = paths.AbsParentDir(__file__, 2)  # noqa
CanFestivalPath = os.path.join(base_folder, "CanFestival-3")  # noqa
sys.path.append(os.path.join(CanFestivalPath, "objdictgen"))  # noqa

# pylint: disable=wrong-import-position
from nodelist import NodeList
from nodemanager import NodeManager
import gen_cfile
import eds_utils
import canfestival_config as local_canfestival_config  # pylint: disable=import-error
from commondialogs import CreateNodeDialog
from subindextable import IECTypeConversion, SizeConversion
from canfestival import config_utils
from canfestival.SlaveEditor import SlaveEditor, MasterViewer
from canfestival.NetworkEditor import NetworkEditor


AddCatalog(os.path.join(CanFestivalPath, "objdictgen", "locale"))
setParanoia(0)


# --------------------------------------------------
#              Location Tree Helper
# --------------------------------------------------


def GetSlaveLocationTree(slave_node, current_location, name):
    entries = []
    for index, subindex, size, entry_name in slave_node.GetMapVariableList():
        subentry_infos = slave_node.GetSubentryInfos(index, subindex)
        typeinfos = slave_node.GetEntryInfos(subentry_infos["type"])
        if typeinfos:
            entries.append({
                "name": "0x%4.4x-0x%2.2x: %s" % (index, subindex, entry_name),
                "type": LOCATION_VAR_MEMORY,
                "size": size,
                "IEC_type": IECTypeConversion.get(typeinfos["name"]),
                "var_name": "%s_%4.4x_%2.2x" % ("_".join(name.split()), index, subindex),
                "location": "%s%s" % (SizeConversion[size], ".".join(map(str, current_location +
                                                                         (index, subindex)))),
                "description": "",
                "children": []})
    return {"name": name,
            "type": LOCATION_CONFNODE,
            "location": ".".join([str(i) for i in current_location]) + ".x",
            "children": entries}

# --------------------------------------------------
#                    SLAVE
# --------------------------------------------------


class _SlaveCTN(NodeManager):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="CanFestivalSlaveNode">
        <xsd:complexType>
          <xsd:attribute name="CAN_Device" type="xsd:string" use="optional"/>
          <xsd:attribute name="CAN_Baudrate" type="xsd:string" use="optional"/>
          <xsd:attribute name="NodeId" type="xsd:integer" use="optional" default="2"/>
          <xsd:attribute name="Sync_Align" type="xsd:integer" use="optional" default="0"/>
          <xsd:attribute name="Sync_Align_Ratio" use="optional" default="50">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="99"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """

    EditorType = SlaveEditor
    IconPath = os.path.join(CanFestivalPath, "objdictgen", "networkedit.png")

    def __init__(self):
        # TODO change netname when name change
        NodeManager.__init__(self)
        odfilepath = self.GetSlaveODPath()
        if os.path.isfile(odfilepath):
            self.OpenFileInCurrent(odfilepath)
        else:
            self.FilePath = ""
            dialog = CreateNodeDialog(None, wx.OK)
            dialog.Type.Enable(False)
            dialog.GenSYNC.Enable(False)
            if dialog.ShowModal() == wx.ID_OK:
                name, id, _nodetype, description = dialog.GetValues()
                profile, filepath = dialog.GetProfile()
                NMT = dialog.GetNMTManagement()
                options = dialog.GetOptions()
                self.CreateNewNode(name,         # Name - will be changed at build time
                                   id,           # NodeID - will be changed at build time
                                   "slave",      # Type
                                   description,  # description
                                   profile,      # profile
                                   filepath,     # prfile filepath
                                   NMT,          # NMT
                                   options)      # options
            else:
                self.CreateNewNode("SlaveNode",  # Name - will be changed at build time
                                   0x00,         # NodeID - will be changed at build time
                                   "slave",      # Type
                                   "",           # description
                                   "None",       # profile
                                   "",           # prfile filepath
                                   "heartbeat",  # NMT
                                   [])           # options
            dialog.Destroy()
            self.OnCTNSave()

    def GetCurrentNodeName(self):
        return self.CTNName()

    def GetSlaveODPath(self):
        return os.path.join(self.CTNPath(), 'slave.od')

    def GetCanDevice(self):
        return self.CanFestivalSlaveNode.getCAN_Device()

    def _OpenView(self, name=None, onlyopened=False):
        ConfigTreeNode._OpenView(self, name, onlyopened)
        if self._View is not None:
            self._View.SetBusId(self.GetCurrentLocation())
        return self._View

    def _ExportSlave(self):
        dialog = wx.FileDialog(self.GetCTRoot().AppFrame,
                               _("Choose a file"),
                               os.path.expanduser("~"),
                               "%s.eds" % self.CTNName(),
                               _("EDS files (*.eds)|*.eds|All files|*.*"),
                               wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            result = eds_utils.GenerateEDSFile(dialog.GetPath(), self.GetCurrentNodeCopy())
            if result:
                self.GetCTRoot().logger.write_error(_("Error: Export slave failed\n"))
        dialog.Destroy()

    ConfNodeMethods = [
        {
            "bitmap":    "ExportSlave",
            "name":    _("Export slave"),
            "tooltip": _("Export CanOpen slave to EDS file"),
            "method":   "_ExportSlave"
        },
    ]

    def CTNTestModified(self):
        return self.ChangesToSave or self.OneFileHasChanged()

    def OnCTNSave(self, from_project_path=None):
        return self.SaveCurrentInFile(self.GetSlaveODPath())

    def SetParamsAttribute(self, path, value):
        result = ConfigTreeNode.SetParamsAttribute(self, path, value)

        # Filter IEC_Channel and Name, that have specific behavior
        if path == "BaseParams.IEC_Channel" and self._View is not None:
            self._View.SetBusId(self.GetCurrentLocation())

        return result

    def GetVariableLocationTree(self):
        return GetSlaveLocationTree(self.CurrentNode,
                                    self.GetCurrentLocation(),
                                    self.BaseParams.getName())

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing confnode IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        current_location = self.GetCurrentLocation()
        # define a unique name for the generated C file
        prefix = "_".join(map(str, current_location))
        Gen_OD_path = os.path.join(buildpath, "OD_%s.c" % prefix)
        # Create a new copy of the model
        slave = self.GetCurrentNodeCopy()
        slave.SetNodeName("OD_%s" % prefix)
        # allow access to local OD from Slave PLC
        pointers = config_utils.LocalODPointers(locations, current_location, slave)
        res = gen_cfile.GenerateFile(Gen_OD_path, slave, pointers)
        if res:
            raise Exception(res)
        res = eds_utils.GenerateEDSFile(os.path.join(buildpath, "Slave_%s.eds" % prefix), slave)
        if res:
            raise Exception(res)
        return [(Gen_OD_path, local_canfestival_config.getCFLAGS(CanFestivalPath))], "", False

    def LoadPrevious(self):
        self.LoadCurrentPrevious()

    def LoadNext(self):
        self.LoadCurrentNext()

    def GetBufferState(self):
        return self.GetCurrentBufferState()

# --------------------------------------------------
#                    MASTER
# --------------------------------------------------


class MiniNodeManager(NodeManager):

    def __init__(self, parent, filepath, fullname):
        NodeManager.__init__(self)

        self.OpenFileInCurrent(filepath)

        self.Parent = parent
        self.Fullname = fullname

    def GetIconName(self):
        return None

    def OnCloseEditor(self, view):
        self.Parent.OnCloseEditor(view)

    def CTNFullName(self):
        return self.Fullname

    def CTNTestModified(self):
        return False

    def GetBufferState(self):
        return self.GetCurrentBufferState()

    ConfNodeMethods = []


class _NodeManager(NodeManager):

    def __init__(self, parent, *args, **kwargs):
        NodeManager.__init__(self, *args, **kwargs)
        self.Parent = parent

    def __del__(self):
        self.Parent = None

    def GetCurrentNodeName(self):
        return self.Parent.CTNName()

    def GetCurrentNodeID(self):
        return self.Parent.CanFestivalNode.getNodeId()


class _NodeListCTN(NodeList):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="CanFestivalNode">
        <xsd:complexType>
          <xsd:attribute name="CAN_Device" type="xsd:string" use="optional"/>
          <xsd:attribute name="CAN_Baudrate" type="xsd:string" use="optional"/>
          <xsd:attribute name="NodeId" type="xsd:integer" use="optional" default="1"/>
          <xsd:attribute name="Sync_TPDOs" type="xsd:boolean" use="optional" default="true"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """

    EditorType = NetworkEditor
    IconPath = os.path.join(CanFestivalPath, "objdictgen", "networkedit.png")

    def __init__(self):
        manager = _NodeManager(self)
        NodeList.__init__(self, manager)
        self.LoadProject(self.CTNPath())
        self.SetNetworkName(self.BaseParams.getName())

    def GetCanDevice(self):
        return self.CanFestivalNode.getCAN_Device()

    def SetParamsAttribute(self, path, value):
        if path == "CanFestivalNode.NodeId":
            nodeid = self.CanFestivalNode.getNodeId()
            if value != nodeid:
                slaves = self.GetSlaveIDs()
                dir = (value - nodeid) // abs(value - nodeid)
                while value in slaves and value >= 0:
                    value += dir
                if value < 0:
                    value = nodeid

        value, refresh = ConfigTreeNode.SetParamsAttribute(self, path, value)
        refresh_network = False

        # Filter IEC_Channel and Name, that have specific behavior
        if path == "BaseParams.IEC_Channel" and self._View is not None:
            self._View.SetBusId(self.GetCurrentLocation())
        elif path == "BaseParams.Name":
            self.SetNetworkName(value)
            refresh_network = True
        elif path == "CanFestivalNode.NodeId":
            refresh_network = True

        if refresh_network and self._View is not None:
            wx.CallAfter(self._View.RefreshBufferState)
        return value, refresh

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        nodeindexes = self.SlaveNodes.keys()
        nodeindexes.sort()
        children = []
        children += [GetSlaveLocationTree(self.Manager.GetCurrentNodeCopy(),
                                          current_location,
                                          _("Local entries"))]
        children += [GetSlaveLocationTree(self.SlaveNodes[nodeid]["Node"],
                                          current_location + (nodeid,),
                                          self.SlaveNodes[nodeid]["Name"]) for nodeid in nodeindexes]

        return {
            "name":     self.BaseParams.getName(),
            "type":     LOCATION_CONFNODE,
            "location": self.GetFullIEC_Channel(),
            "children": children
        }

    _GeneratedMasterView = None

    def _ShowGeneratedMaster(self):
        self._OpenView("Generated master")

    def _OpenView(self, name=None, onlyopened=False):
        if name == "Generated master":
            app_frame = self.GetCTRoot().AppFrame
            if self._GeneratedMasterView is None:
                buildpath = self._getBuildPath()
                # Eventually create build dir
                if not os.path.exists(buildpath):
                    self.GetCTRoot().logger.write_error(_("Error: No PLC built\n"))
                    return

                masterpath = os.path.join(buildpath, "MasterGenerated.od")
                if not os.path.exists(masterpath):
                    self.GetCTRoot().logger.write_error(_("Error: No Master generated\n"))
                    return

                manager = MiniNodeManager(self, masterpath, self.CTNFullName())
                self._GeneratedMasterView = MasterViewer(app_frame.TabsOpened, manager, app_frame, name)

            if self._GeneratedMasterView is not None:
                app_frame.EditProjectElement(self._GeneratedMasterView, self._GeneratedMasterView.GetInstancePath())

            return self._GeneratedMasterView
        else:
            ConfigTreeNode._OpenView(self, name, onlyopened)
            if self._View is not None:
                self._View.SetBusId(self.GetCurrentLocation())
            return self._View

    ConfNodeMethods = [
        {
            "bitmap":    "ShowMaster",
            "name":    _("Show Master"),
            "tooltip": _("Show Master generated by config_utils"),
            "method":   "_ShowGeneratedMaster"
        }
    ]

    def OnCloseEditor(self, view):
        ConfigTreeNode.OnCloseEditor(self, view)
        if self._GeneratedMasterView == view:
            self._GeneratedMasterView = None

    def OnCTNClose(self):
        ConfigTreeNode.OnCTNClose(self)
        self._CloseView(self._GeneratedMasterView)
        return True

    def CTNTestModified(self):
        return self.ChangesToSave or self.HasChanged()

    def OnCTNSave(self, from_project_path=None):
        self.SetRoot(self.CTNPath())
        if from_project_path is not None:
            shutil.copytree(self.GetEDSFolder(from_project_path),
                            self.GetEDSFolder())
        return self.SaveProject() is None

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param current_location: Tupple containing confnode IEC location : %I0.0.4.5 => (0,0,4,5)
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        self._CloseView(self._GeneratedMasterView)
        current_location = self.GetCurrentLocation()
        # define a unique name for the generated C file
        prefix = "_".join(map(str, current_location))
        Gen_OD_path = os.path.join(buildpath, "OD_%s.c" % prefix)
        # Create a new copy of the model with DCF loaded with PDO mappings for desired location
        try:
            master, pointers = config_utils.GenerateConciseDCF(locations, current_location, self, self.CanFestivalNode.getSync_TPDOs(), "OD_%s" % prefix)
        except config_utils.PDOmappingException as e:
            raise Exception(e.message)
        # Do generate C file.
        res = gen_cfile.GenerateFile(Gen_OD_path, master, pointers)
        if res:
            raise Exception(res)

        file = open(os.path.join(buildpath, "MasterGenerated.od"), "w")
        # linter disabled here, undefined variable happens
        # here because gnosis isn't impored while linting
        dump(master, file)  # pylint: disable=undefined-variable
        file.close()

        return [(Gen_OD_path, local_canfestival_config.getCFLAGS(CanFestivalPath))], "", False

    def LoadPrevious(self):
        self.Manager.LoadCurrentPrevious()

    def LoadNext(self):
        self.Manager.LoadCurrentNext()

    def GetBufferState(self):
        return self.Manager.GetCurrentBufferState()


class RootClass(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="CanFestivalInstance">
        <xsd:complexType>
          <xsd:attribute name="CAN_Driver" type="xsd:string" use="optional"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """

    CTNChildrenTypes = [("CanOpenNode",  _NodeListCTN, "CanOpen Master"),
                        ("CanOpenSlave", _SlaveCTN,    "CanOpen Slave")]

    def GetParamsAttributes(self, path=None):
        infos = ConfigTreeNode.GetParamsAttributes(self, path=path)
        for element in infos:
            if element["name"] == "CanFestivalInstance":
                for child in element["children"]:
                    if child["name"] == "CAN_Driver":
                        child["type"] = local_canfestival_config.DLL_LIST
        return infos

    def GetCanDriver(self):
        res = self.CanFestivalInstance.getCAN_Driver()
        if not res:
            return ""
        return res

    def CTNGenerate_C(self, buildpath, locations):
        can_driver = self.GetCanDriver()
        if can_driver is not None:
            can_drivers = local_canfestival_config.DLL_LIST
            if can_driver not in can_drivers:
                can_driver = can_drivers[0]
            can_drv_ext = self.GetCTRoot().GetBuilder().extension
            can_drv_prefix = self.GetCTRoot().GetBuilder().dlopen_prefix
            can_driver_name = can_drv_prefix + "libcanfestival_" + can_driver + can_drv_ext
        else:
            can_driver_name = ""

        format_dict = {
            "locstr": "_".join(map(str, self.GetCurrentLocation())),
            "candriver": can_driver_name,
            "nodes_includes": "",
            "board_decls": "",
            "nodes_init": "",
            "nodes_open": "",
            "nodes_stop": "",
            "nodes_close": "",
            "nodes_send_sync": "",
            "nodes_proceed_sync": "",
            "slavebootups": "",
            "slavebootup_register": "",
            "post_sync": "",
            "post_sync_register": "",
            "pre_op": "",
            "pre_op_register": "",
        }
        for child in self.IECSortedChildren():
            childlocstr = "_".join(map(str, child.GetCurrentLocation()))
            nodename = "OD_%s" % childlocstr

            # Try to get Slave Node
            child_data = getattr(child, "CanFestivalSlaveNode", None)
            if child_data is None:
                # Not a slave -> master
                child_data = getattr(child, "CanFestivalNode")
                # Apply sync setting
                format_dict["nodes_init"] += 'NODE_MASTER_INIT(%s, %s)\n    ' % (
                    nodename,
                    child_data.getNodeId())
                if child_data.getSync_TPDOs():
                    format_dict["nodes_send_sync"] += 'NODE_SEND_SYNC(%s)\n    ' % (nodename)
                    format_dict["nodes_proceed_sync"] += 'NODE_PROCEED_SYNC(%s)\n    ' % (nodename)

                # initialize and declare node boot status variables for post_SlaveBootup lookup
                SlaveIDs = child.GetSlaveIDs()
                if len(SlaveIDs) == 0:
                    # define post_SlaveBootup lookup functions
                    format_dict["slavebootups"] += (
                        "static void %s_post_SlaveBootup(CO_Data* d, UNS8 nodeId){}\n" % (nodename))
                else:
                    format_dict["slavebootups"] += (
                        "static void %s_post_SlaveBootup(CO_Data* d, UNS8 nodeId){\n" % (nodename) +
                        "    check_and_start_node(d, nodeId);\n" +
                        "}\n")
                # register previously declared func as post_SlaveBootup callback for that node
                format_dict["slavebootup_register"] += (
                    "%s_Data.post_SlaveBootup = %s_post_SlaveBootup;\n" % (nodename, nodename))
                format_dict["pre_op"] += (
                    "static void %s_preOperational(CO_Data* d){\n    " % (nodename) +
                    "".join(["    masterSendNMTstateChange(d, %d, NMT_Reset_Comunication);\n" % NdId for NdId in SlaveIDs]) +
                    "}\n")
                format_dict["pre_op_register"] += (
                    "%s_Data.preOperational = %s_preOperational;\n" % (nodename, nodename))
            else:
                # Slave node
                align = child_data.getSync_Align()
                align_ratio = child_data.getSync_Align_Ratio()
                if align > 0:
                    format_dict["post_sync"] += (
                        "static int %s_CalCount = 0;\n" % (nodename) +
                        "static void %s_post_sync(CO_Data* d){\n" % (nodename) +
                        "    if(%s_CalCount < %d){\n" % (nodename, align) +
                        "        %s_CalCount++;\n" % (nodename) +
                        "        align_tick(-1);\n" +
                        "    }else{\n" +
                        "        align_tick(%d);\n" % (align_ratio) +
                        "    }\n" +
                        "}\n")
                    format_dict["post_sync_register"] += (
                        "%s_Data.post_sync = %s_post_sync;\n" % (nodename, nodename))
                format_dict["nodes_init"] += 'NODE_SLAVE_INIT(%s, %s)\n    ' % (
                    nodename,
                    child_data.getNodeId())

            # Include generated OD headers
            format_dict["nodes_includes"] += '#include "%s.h"\n' % (nodename)
            # Declare CAN channels according user filled config
            format_dict["board_decls"] += 'BOARD_DECL(%s, "%s", "%s")\n' % (
                nodename,
                child.GetCanDevice(),
                child_data.getCAN_Baudrate())
            format_dict["nodes_open"] += 'NODE_OPEN(%s)\n    ' % (nodename)
            format_dict["nodes_close"] += 'NODE_CLOSE(%s)\n    ' % (nodename)
            format_dict["nodes_stop"] += 'NODE_STOP(%s)\n    ' % (nodename)

        filename = paths.AbsNeighbourFile(__file__, "cf_runtime.c")
        cf_main = open(filename).read() % format_dict
        cf_main_path = os.path.join(buildpath, "CF_%(locstr)s.c" % format_dict)
        f = open(cf_main_path, 'w')
        f.write(cf_main)
        f.close()

        res = [(cf_main_path, local_canfestival_config.getCFLAGS(CanFestivalPath))], local_canfestival_config.getLDFLAGS(CanFestivalPath), True

        if can_driver is not None:
            can_driver_path = os.path.join(CanFestivalPath, "drivers", can_driver, can_driver_name)
            if os.path.exists(can_driver_path):
                res += ((can_driver_name, open(can_driver_path, "rb")),)

        return res
