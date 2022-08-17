#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
#
# Copyright (C) 2011-2014: Laurent BESSARD, Edouard TISSERANT
#                          RTES Lab : CRKim, JBLee, youcu
#                          Higen Motor : Donggu Kang
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
import os
from copy import deepcopy
from functools import reduce
from lxml import etree

import wx

from xmlclass import *

from PLCControler import UndoBuffer, LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT
from ConfigTreeNode import ConfigTreeNode
from dialogs import BrowseValuesLibraryDialog
from IDEFrame import TITLE, FILEMENU, PROJECTTREE
from POULibrary import POULibrary

from etherlab.ConfigEditor import MasterEditor
from etherlab.EthercatCFileGenerator import _EthercatCFileGenerator
from etherlab.EthercatSlave import \
    _EthercatSlaveCTN, \
    ExtractHexDecValue, \
    GenerateHexDecValue, \
    TYPECONVERSION, \
    VARCLASSCONVERSION, \
    _CommonSlave

try:
    from etherlab.EthercatCIA402Slave import _EthercatCIA402SlaveCTN
    HAS_MCL = True
except Exception:
    HAS_MCL = False

# --------------------------------------------------
#         Remote Exec Etherlab Commands
# --------------------------------------------------

SCAN_COMMAND = """
import commands
result = commands.getoutput("ethercat slaves")
slaves = []
for slave_line in result.splitlines():
    chunks = slave_line.split()
    idx, pos, state, flag = chunks[:4]
    name = " ".join(chunks[4:])
    alias, position = pos.split(":")
    slave = {"idx": int(idx),
             "alias": int(alias),
             "position": int(position),
             "name": name}
    details = commands.getoutput("ethercat slaves -p %d -v" % slave["idx"])
    for details_line in details.splitlines():
        details_line = details_line.strip()
        for header, param in [("Vendor Id:", "vendor_id"),
                              ("Product code:", "product_code"),
                              ("Revision number:", "revision_number")]:
            if details_line.startswith(header):
                slave[param] = details_line.split()[-1]
                break
    slaves.append(slave)
returnVal = slaves
"""

# --------------------------------------------------
#      Etherlab Specific Blocks Library
# --------------------------------------------------


def GetLocalPath(filename):
    return os.path.join(os.path.split(__file__)[0], filename)


class EtherlabLibrary(POULibrary):
    def GetLibraryPath(self):
        return GetLocalPath("pous.xml")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):
        etherlab_ext_file = open(GetLocalPath("etherlab_ext.c"), 'r')
        etherlab_ext_code = etherlab_ext_file.read()
        etherlab_ext_file.close()

        Gen_etherlabfile_path = os.path.join(buildpath, "etherlab_ext.c")
        ethelabfile = open(Gen_etherlabfile_path, 'w')
        ethelabfile.write(etherlab_ext_code)
        ethelabfile.close()

        return ((["etherlab_ext"], [(Gen_etherlabfile_path, IECCFLAGS)], True), "",
                ("runtime_etherlab.py", open(GetLocalPath("runtime_etherlab.py"))))

                # TODO : rename to match runtime_{location}_extname.py format

# --------------------------------------------------
#                 Ethercat MASTER
# --------------------------------------------------


EtherCATConfigParser = GenerateParserFromXSD(os.path.join(os.path.dirname(__file__), "EtherCATConfig.xsd"))


def sort_commands(x, y):
    if x["Index"] == y["Index"]:
        return cmp(x["Subindex"], y["Subindex"])
    return cmp(x["Index"], y["Index"])


cls = EtherCATConfigParser.GetElementClass("Slave", "Config")
if cls:

    def getType(self):
        slave_info = self.getInfo()
        return {"device_type": slave_info.getName(),
                "vendor": GenerateHexDecValue(slave_info.getVendorId()),
                "product_code": GenerateHexDecValue(slave_info.getProductCode(), 16),
                "revision_number": GenerateHexDecValue(slave_info.getRevisionNo(), 16)}
    setattr(cls, "getType", getType)

    def setType(self, type_infos):
        slave_info = self.getInfo()
        slave_info.setName(type_infos["device_type"])
        slave_info.setVendorId(ExtractHexDecValue(type_infos["vendor"]))
        slave_info.setProductCode(ExtractHexDecValue(type_infos["product_code"]))
        slave_info.setRevisionNo(ExtractHexDecValue(type_infos["revision_number"]))
    setattr(cls, "setType", setType)

    def getInitCmds(self, create_default=False):
        Mailbox = self.getMailbox()
        if Mailbox is None:
            if create_default:
                self.addMailbox()
                Mailbox = self.getMailbox()
            else:
                return None
        CoE = Mailbox.getCoE()
        if CoE is None:
            if create_default:
                Mailbox.addCoE()
                CoE = Mailbox.getCoE()
            else:
                return None
        InitCmds = CoE.getInitCmds()
        if InitCmds is None and create_default:
            CoE.addInitCmds()
            InitCmds = CoE.getInitCmds()
        return InitCmds
    setattr(cls, "getInitCmds", getInitCmds)

    def getStartupCommands(self):
        pos = self.getInfo().getPhysAddr()
        InitCmds = self.getInitCmds()
        if InitCmds is None:
            return []
        commands = []
        for idx, InitCmd in enumerate(InitCmds.getInitCmd()):
            comment = InitCmd.getComment()
            if comment is None:
                comment = ""
            commands.append({
                "command_idx": idx,
                "Position": pos,
                "Index": InitCmd.getIndex(),
                "Subindex": InitCmd.getSubIndex(),
                "Value": InitCmd.getData(),
                "Description": comment})
        commands.sort(sort_commands)
        return commands
    setattr(cls, "getStartupCommands", getStartupCommands)

    def appendStartupCommand(self, command_infos):
        InitCmds = self.getInitCmds(True)
        command = EtherCATConfigParser.CreateElement("InitCmd", "InitCmds", 1)
        InitCmds.appendInitCmd(command)
        command.setIndex(command_infos["Index"])
        command.setSubIndex(command_infos["Subindex"])
        command.setData(command_infos["Value"])
        command.setComment(command_infos["Description"])
        return len(InitCmds.getInitCmd()) - 1
    setattr(cls, "appendStartupCommand", appendStartupCommand)

    def setStartupCommand(self, command_infos):
        InitCmds = self.getInitCmds()
        if InitCmds is not None:
            commands = InitCmds.getInitCmd()
            if command_infos["command_idx"] < len(commands):
                command = commands[command_infos["command_idx"]]
                command.setIndex(command_infos["Index"])
                command.setSubIndex(command_infos["Subindex"])
                command.setData(command_infos["Value"])
                command.setComment(command_infos["Description"])
    setattr(cls, "setStartupCommand", setStartupCommand)

    def removeStartupCommand(self, command_idx):
        InitCmds = self.getInitCmds()
        if InitCmds is not None:
            if command_idx < len(InitCmds.getInitCmd()):
                InitCmds.removeInitCmd(command_idx)
    setattr(cls, "removeStartupCommand", removeStartupCommand)

ProcessVariablesXSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="ProcessVariables">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="variable" minOccurs="0" maxOccurs="unbounded">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="ReadFrom" type="LocationDesc" minOccurs="0"/>
                  <xsd:element name="WriteTo" type="LocationDesc" minOccurs="0"/>
                </xsd:sequence>
                <xsd:attribute name="Name" type="xsd:string" use="required"/>
                <xsd:attribute name="Comment" type="xsd:string" use="required"/>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:complexType name="LocationDesc">
        <xsd:attribute name="Position" type="xsd:integer" use="required"/>
        <xsd:attribute name="Index" type="xsd:integer" use="required"/>
        <xsd:attribute name="SubIndex" type="xsd:integer" use="required"/>
      </xsd:complexType>
    </xsd:schema>
"""

ProcessVariablesParser = GenerateParserFromXSDstring(ProcessVariablesXSD)


class _EthercatCTN(object):

    CTNChildrenTypes = [("EthercatSlave", _EthercatSlaveCTN, "Ethercat Slave")]
    if HAS_MCL:
        CTNChildrenTypes.append(("EthercatCIA402Slave", _EthercatCIA402SlaveCTN, "Ethercat CIA402 Slave"))
    EditorType = MasterEditor

    def __init__(self):
        config_filepath = self.ConfigFileName()
        config_is_saved = False
        self.Config = None
        # if os.path.isfile(config_filepath):
        #     config_xmlfile = open(config_filepath, 'r')
        #     try:
        #         self.Config, error = \
        #             EtherCATConfigParser.LoadXMLString(config_xmlfile.read())
        #         if error is None:
        #             config_is_saved = True
        #     except Exception as e:
        #         error = str(e)
        #     config_xmlfile.close()

        #     if error is not None:
        #         self.GetCTRoot().logger.write_error(
        #             _("Couldn't load %s network configuration file.") % self.CTNName())

        if self.Config is None:
            self.Config = EtherCATConfigParser.CreateElement("EtherCATConfig")

        process_filepath = self.ProcessVariablesFileName()
        process_is_saved = False
        self.ProcessVariables = None
        if os.path.isfile(process_filepath):
            process_xmlfile = open(process_filepath, 'r')
            try:
                self.ProcessVariables, error = \
                    ProcessVariablesParser.LoadXMLString(process_xmlfile.read())
                if error is None:
                    process_is_saved = True
            except Exception as e:
                error = str(e)
            process_xmlfile.close()

            if error is not None:
                self.GetCTRoot().logger.write_error(
                    _("Couldn't load %s network process variables file.") % self.CTNName())

        if self.ProcessVariables is None:
            self.ProcessVariables = ProcessVariablesParser.CreateElement("ProcessVariables")

        #if config_is_saved and process_is_saved:
        if process_is_saved:
            self.CreateBuffer(True)
        else:
            self.CreateBuffer(False)
            self.OnCTNSave()

        if os.path.isfile(config_filepath):
            config_xmlfile = open(config_filepath, 'r')
            try:
                self.Config, error = \
                    EtherCATConfigParser.LoadXMLString(config_xmlfile.read())
                if error is None:
                    config_is_saved = True
            except Exception, e:
                error = e.message
            config_xmlfile.close()
            
            if error is not None:
                self.GetCTRoot().logger.write_error(
                    _("Couldn't load %s network configuration file.") % CTNName)

        # ----------- call ethercat mng. function --------------
        self.CommonMethod = _CommonSlave(self)

    def GetIconName(self):
        return "Ethercat"

    def GetContextualMenuItems(self):
        return [(_("Add Ethercat Slave"), _("Add Ethercat Slave to Master"), self.OnAddEthercatSlave)]

    def OnAddEthercatSlave(self, event):
        app_frame = self.GetCTRoot().AppFrame
        dialog = BrowseValuesLibraryDialog(app_frame,
                                           _("Ethercat Slave Type"),
                                           self.GetSlaveTypesLibrary())
        if dialog.ShowModal() == wx.ID_OK:
            type_infos = dialog.GetValueInfos()
            device, _module_extra_params = self.GetModuleInfos(type_infos)
            if device is not None:
                if HAS_MCL and str(_EthercatCIA402SlaveCTN.NODE_PROFILE) in device.GetProfileNumbers():
                    ConfNodeType = "EthercatCIA402Slave"
                else:
                    ConfNodeType = "EthercatSlave"
                new_child = self.CTNAddChild("%s_0" % ConfNodeType, ConfNodeType)
                new_child.SetParamsAttribute("SlaveParams.Type", type_infos)
                self.CTNRequestSave()
                new_child._OpenView()
                app_frame._Refresh(TITLE, FILEMENU, PROJECTTREE)
        dialog.Destroy()

    def ExtractHexDecValue(self, value):
        return ExtractHexDecValue(value)

    def GetSizeOfType(self, type):
        return TYPECONVERSION.get(self.GetCTRoot().GetBaseType(type), None)

    def ConfigFileName(self):
        return os.path.join(self.CTNPath(), "config.xml")

    def ProcessVariablesFileName(self):
        return os.path.join(self.CTNPath(), "process_variables.xml")

    def FilterSlave(self, slave, vendor=None, slave_pos=None, slave_profile=None):
        if slave_pos is not None and slave.getInfo().getPhysAddr() != slave_pos:
            return False
        type_infos = slave.getType()
        if vendor is not None and ExtractHexDecValue(type_infos["vendor"]) != vendor:
            return False
        device, _module_extra_params = self.GetModuleInfos(type_infos)
        if slave_profile is not None and slave_profile not in device.GetProfileNumbers():
            return False
        return True

    def GetSlaveName(self, slave_pos):
        CTNChild = self.GetChildByIECLocation((slave_pos,))
        if CTNChild is not None:
            return CTNChild.CTNName()
        return self.CTNName()

    def GetSlaves(self, vendor=None, slave_pos=None, slave_profile=None):
        slaves = []
        for slave in self.Config.getConfig().getSlave():
            if self.FilterSlave(slave, vendor, slave_pos, slave_profile):
                slaves.append(slave.getInfo().getPhysAddr())
        slaves.sort()
        return slaves

    def GetSlave(self, slave_pos):
        for slave in self.Config.getConfig().getSlave():
            slave_info = slave.getInfo()
            if slave_info.getPhysAddr() == slave_pos:
                return slave
        return None

    def GetStartupCommands(self, vendor=None, slave_pos=None, slave_profile=None):
        commands = []
        for slave in self.Config.getConfig().getSlave():
            if self.FilterSlave(slave, vendor, slave_pos, slave_profile):
                commands.append((slave.getInfo().getPhysAddr(), slave.getStartupCommands()))
        commands.sort()
        return reduce(lambda x, y: x + y[1], commands, [])

    def AppendStartupCommand(self, command_infos):
        slave = self.GetSlave(command_infos["Position"])
        if slave is not None:
            command_idx = slave.appendStartupCommand(command_infos)
            self.BufferModel()
            return command_idx
        return None

    def SetStartupCommandInfos(self, command_infos):
        slave = self.GetSlave(command_infos["Position"])
        if slave is not None:
            slave.setStartupCommand(command_infos)
            self.BufferModel()

    def RemoveStartupCommand(self, slave_pos, command_idx, buffer=True):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            slave.removeStartupCommand(command_idx)
            if buffer:
                self.BufferModel()

    def SetProcessVariables(self, variables):
        vars = []
        for var in variables:
            variable = ProcessVariablesParser.CreateElement("variable", "ProcessVariables")
            variable.setName(var["Name"])
            variable.setComment(var["Description"])
            if var["ReadFrom"] != "":
                position, index, subindex = var["ReadFrom"]
                if variable.getReadFrom() is None:
                    variable.addReadFrom()
                read_from = variable.getReadFrom()
                read_from.setPosition(position)
                read_from.setIndex(index)
                read_from.setSubIndex(subindex)
            elif variable.getReadFrom() is not None:
                variable.deleteReadFrom()
            if var["WriteTo"] != "":
                position, index, subindex = var["WriteTo"]
                if variable.getWriteTo() is None:
                    variable.addWriteTo()
                write_to = variable.getWriteTo()
                write_to.setPosition(position)
                write_to.setIndex(index)
                write_to.setSubIndex(subindex)
            elif variable.getWriteTo() is not None:
                variable.deleteWriteTo()
            vars.append(variable)
        self.ProcessVariables.setvariable(vars)
        self.BufferModel()

    def GetProcessVariables(self):
        variables = []
        idx = 0
        for variable in self.ProcessVariables.getvariable():
            var = {"Name": variable.getName(),
                   "Number": idx,
                   "Description": variable.getComment()}
            read_from = variable.getReadFrom()
            if read_from is not None:
                var["ReadFrom"] = (read_from.getPosition(),
                                   read_from.getIndex(),
                                   read_from.getSubIndex())
            else:
                var["ReadFrom"] = ""
            write_to = variable.getWriteTo()
            if write_to is not None:
                var["WriteTo"] = (write_to.getPosition(),
                                  write_to.getIndex(),
                                  write_to.getSubIndex())
            else:
                var["WriteTo"] = ""
            variables.append(var)
            idx += 1
        return variables

    def _ScanNetwork(self):
        app_frame = self.GetCTRoot().AppFrame

        execute = True
        if len(self.Children) > 0:
            dialog = wx.MessageDialog(
                app_frame,
                _("The current network configuration will be deleted.\nDo you want to continue?"),
                _("Scan Network"),
                wx.YES_NO | wx.ICON_QUESTION)
            execute = dialog.ShowModal() == wx.ID_YES
            dialog.Destroy()

        if execute:
            error, returnVal = self.RemoteExec(SCAN_COMMAND, returnVal=None)
            if error != 0:
                dialog = wx.MessageDialog(app_frame, returnVal, _("Error"), wx.OK | wx.ICON_ERROR)
                dialog.ShowModal()
                dialog.Destroy()
            elif returnVal is not None:
                for child in self.IECSortedChildren():
                    self._doRemoveChild(child)

                for slave in returnVal:
                    type_infos = {
                        "vendor": slave["vendor_id"],
                        "product_code": slave["product_code"],
                        "revision_number": slave["revision_number"],
                    }
                    device, _module_extra_params = self.GetModuleInfos(type_infos)
                    if device is not None:
                        if HAS_MCL and _EthercatCIA402SlaveCTN.NODE_PROFILE in device.GetProfileNumbers():
                            CTNType = "EthercatCIA402Slave"
                        else:
                            CTNType = "EthercatSlave"
                        self.CTNAddChild("slave%s" % slave["idx"], CTNType, slave["idx"])
                        self.SetSlaveAlias(slave["idx"], slave["alias"])
                        type_infos["device_type"] = device.getType().getcontent()
                        self.SetSlaveType(slave["idx"], type_infos)

                if app_frame:
                    app_frame.RefreshProjectTree()

    def CTNAddChild(self, CTNName, CTNType, IEC_Channel=0):
        """
        Create the confnodes that may be added as child to this node self
        @param CTNType: string desining the confnode class name (get name from CTNChildrenTypes)
        @param CTNName: string for the name of the confnode instance
        """
        newConfNodeOpj = ConfigTreeNode.CTNAddChild(self, CTNName, CTNType, IEC_Channel)

        slave = self.GetSlave(newConfNodeOpj.BaseParams.getIEC_Channel())
        if slave is None:
            slave = EtherCATConfigParser.CreateElement("Slave", "Config")
            self.Config.getConfig().appendSlave(slave)
            slave_infos = slave.getInfo()
            slave_infos.setName("undefined")
            slave_infos.setPhysAddr(newConfNodeOpj.BaseParams.getIEC_Channel())
            slave_infos.setAutoIncAddr(0)
            self.BufferModel()
            self.OnCTNSave()

        return newConfNodeOpj

    def _doRemoveChild(self, CTNInstance):
        slave_pos = CTNInstance.GetSlavePos()
        config = self.Config.getConfig()
        for idx, slave in enumerate(config.getSlave()):
            slave_infos = slave.getInfo()
            if slave_infos.getPhysAddr() == slave_pos:
                config.removeSlave(idx)
                self.BufferModel()
                self.OnCTNSave()
        ConfigTreeNode._doRemoveChild(self, CTNInstance)

    def SetSlavePosition(self, slave_pos, new_pos):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            slave_info = slave.getInfo()
            slave_info.setPhysAddr(new_pos)
            for variable in self.ProcessVariables.getvariable():
                read_from = variable.getReadFrom()
                if read_from is not None and read_from.getPosition() == slave_pos:
                    read_from.setPosition(new_pos)
                write_to = variable.getWriteTo()
                if write_to is not None and write_to.getPosition() == slave_pos:
                    write_to.setPosition(new_pos)
            self.CreateBuffer(True)
            self.CTNRequestSave()
            if self._View is not None:
                self._View.RefreshView()
                self._View.RefreshBuffer()

    def GetSlaveAlias(self, slave_pos):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            slave_info = slave.getInfo()
            return slave_info.getAutoIncAddr()
        return None

    def SetSlaveAlias(self, slave_pos, alias):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            slave_info = slave.getInfo()
            slave_info.setAutoIncAddr(alias)
            self.BufferModel()

    def GetSlaveType(self, slave_pos):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            return slave.getType()
        return None

    def SetSlaveType(self, slave_pos, type_infos):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            slave.setType(type_infos)
            self.BufferModel()

    def GetSlaveInfos(self, slave_pos):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            type_infos = slave.getType()
            device, _module_extra_params = self.GetModuleInfos(type_infos)
            if device is not None:
                infos = type_infos.copy()
                infos.update({"physics": device.getPhysics(),
                              "sync_managers": device.GetSyncManagers(),
                              "entries": self.GetSlaveVariables(device)})
                return infos
        return None

    def GetSlaveVariables(self, slave_pos=None, limits=None, device=None, module=None):
        # add jblee
        files = os.listdir(self.CTNPath())
        moduleNames = []
        modulePos = 1
        for file in files:
            filepath = os.path.join(self.CTNPath(), file)
            if os.path.isdir(filepath):
                MDPFilePath = os.path.join(filepath, "DataForMDP.txt")
                CheckConfNodePath = os.path.join(filepath, "baseconfnode.xml")

                try :
                    moduleDataFile = open(MDPFilePath, 'r')
                    confNodeFile = open(CheckConfNodePath, 'r')

                    lines = moduleDataFile.readlines()
                    checklines = confNodeFile.readlines()

                    moduleDataFile.close()
                    confNodeFile.close()

                    module_info = self.GetModuleEntryList()
                    # checklines(ex) : <BaseParams xmlns:xsd="http://www.w3.org/2001/XMLSchema" IEC_Channel="0" Name="EthercatSlave_0"/>
                    # checklines[1].split() : [<BaseParams, xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    #                           IEC_Channel="0", Name="EthercatSlave_0"/>]
                    # checklines[1].split()[2] : IEC_Channel="0"
                    # checklines[1].split()[2].split("\"") = [IEC_Channel=, 0, ]
                    pos_check = int(checklines[1].split()[2].split("\"")[1])

                    if slave_pos != pos_check:
                        continue

                    for line in lines:
                        if line == "\n":
                            continue
                        # module_name : ST-1214, ST-2314, ...
                        # if user add module => ST-1214 3EA, ST-2314 3EA
                        # each result_module_name : 
                        #    (ST-1214, Module 1), (ST-1214, Module 2), (ST-1214, Module 3)
                        #    (ST-2314, Module 4), (ST-2314, Module 5), (ST-2314, Module 6)  
                        module_name = line.split()[0]
                        result_module_name = module_name + ", Module %d" % modulePos
                        moduleNames.append(result_module_name)
                        modulePos += 1
                except :
                    pass

        if device is None and slave_pos is not None:
            slave = self.GetSlave(slave_pos)
            if slave is not None:
                type_infos = slave.getType()
                device, _module_extra_params = self.GetModuleInfos(type_infos)
        if device is not None:
            # Test OD
            entries = device.GetEntriesList(limits)
            #entries = self.CTNParent.GetEntriesList()
            entries_list = entries.items()
            entries_list.sort()
            entries = []
            current_index = None
            current_entry = {}
            for (index, _subindex), entry in entries_list:
                entry["children"] = []
                if slave_pos is not None:
                    entry["Position"] = str(slave_pos)
                if index != current_index:
                    current_index = index
                    current_entry = entry
                    entries.append(entry)
                elif current_entry:
                    current_entry["children"].append(entry)
                else:
                    entries.append(entry)

            increment = self.CTNParent.GetModuleIncrement()[0]
            count = 1
            #print module_info
            # moduleNameAndPos : (ST-1214, Module 1), (ST-1214, Module 2), ... ,
            # moduleNameAndPos.split(",") : ["ST-1214", " Module 1"]
            # moduleNameAndPos.split(",")[0] : "ST-1214"
            for moduleNameAndPos in moduleNames:
                moduleName = moduleNameAndPos.split(",")[0]
                modulePosName = moduleNameAndPos.split(",")[1]
                idx_increment = int(increment) * count
                
                for MDP_entry in module_info.get(moduleName):
                    LocalMDPEntry = []
                    #print MDP_entry
                    local_idx = MDP_entry["Index"]
                    if ExtractHexDecValue(local_idx) == 0: #and local_idx[0] == "#":
                        temp_index = ExtractHexDecValue(local_idx)
                    else :
                        temp_index = ExtractHexDecValue(MDP_entry["Index"]) + idx_increment
                    #temp_index = ExtractHexDecValue(MDP_entry["Index"]) + idx_increment
                    entry_index = hex(temp_index)
                    entry_subidx = MDP_entry["SubIndex"]
                    entry_name = MDP_entry["Name"] + ", " + " " + \
                                 moduleName + " - " + modulePosName
                    entry_type = MDP_entry["Type"]
                    entry_bitsize = MDP_entry["BitSize"]
                    entry_access = MDP_entry["Access"]
                    mapping_type = MDP_entry["PDOMapping"]

                    LocalMDPEntry.append({
                        "Index": entry_index,
                        "SubIndex": entry_subidx,
                        "Name": entry_name,
                        "Type": entry_type,
                        "BitSize": entry_bitsize,
                        "Access": entry_access, 
                        "PDOMapping": mapping_type,
                        "children": ""})
                    entries.append(LocalMDPEntry[0])
                count += 1
            
            #print entries
            return entries
        return []

    def GetSlaveVariableDataType(self, slave_pos, index, subindex):
        slave = self.GetSlave(slave_pos)
        if slave is not None:
            device, _module_extra_params = self.GetModuleInfos(slave.getType())
            if device is not None:
                entries = device.GetEntriesList()
                entry_infos = entries.get((index, subindex))
                if entry_infos is not None:
                    return entry_infos["Type"]
        return None

    def GetNodesVariables(self, vendor=None, slave_pos=None, slave_profile=None, limits=None):
        entries = []
        for slave_position in self.GetSlaves():
            if slave_pos is not None and slave_position != slave_pos:
                continue
            slave = self.GetSlave(slave_position)
            type_infos = slave.getType()
            if vendor is not None and ExtractHexDecValue(type_infos["vendor"]) != vendor:
                continue
            device, _module_extra_params = self.GetModuleInfos(type_infos)
            if slave_profile is not None and slave_profile not in device.GetProfileNumbers():
                continue
            entries.extend(self.GetSlaveVariables(slave_position, limits, device))
        return entries

    def GetModuleInfos(self, type_infos):
        return self.CTNParent.GetModuleInfos(type_infos)

    # add jblee
    def GetModuleEntryList(self):
        return self.CTNParent.GetModuleEntryList()
    
    def GetSlaveTypesLibrary(self, profile_filter=None):
        return self.CTNParent.GetModulesLibrary(profile_filter)

    def GetLibraryVendors(self):
        return self.CTNParent.GetVendors()

    def GetDeviceLocationTree(self, slave_pos, current_location, device_name):
        slave = self.GetSlave(slave_pos)
        vars = []

        # add jblee
        files = os.listdir(self.CTNPath())
        moduleNames = []
        modulePos = 1
        for file in files:
            filepath = os.path.join(self.CTNPath(), file)
            if os.path.isdir(filepath):
                MDPFilePath = os.path.join(filepath, "DataForMDP.txt")
                CheckConfNodePath = os.path.join(filepath, "baseconfnode.xml")

                try :
                    moduleDataFile = open(MDPFilePath, 'r')
                    confNodeFile = open(CheckConfNodePath, 'r')

                    lines = moduleDataFile.readlines()
                    checklines = confNodeFile.readlines()

                    moduleDataFile.close()
                    confNodeFile.close()

                    module_info = self.GetModuleEntryList()
                    # checklines(ex) : <BaseParams xmlns:xsd="http://www.w3.org/2001/XMLSchema" IEC_Channel="0" Name="EthercatSlave_0"/>
                    # checklines[1].split() : [<BaseParams, xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    #                           IEC_Channel="0", Name="EthercatSlave_0"/>]
                    # checklines[1].split()[2] : IEC_Channel="0"
                    # checklines[1].split()[2].split("\"") = [IEC_Channel=, 0, ]
                    pos_check = int(checklines[1].split()[2].split("\"")[1])

                    if slave_pos != pos_check:
                        continue

                    for line in lines:
                        if line == "\n":
                            continue
                        # module_name : ST-1214, ST-2314, ...
                        # if user add module => ST-1214 3EA, ST-2314 3EA
                        # each result_module_name : 
                        #    (ST-1214, Module 1), (ST-1214, Module 2), (ST-1214, Module 3)
                        #    (ST-2314, Module 4), (ST-2314, Module 5), (ST-2314, Module 6)  
                        module_name = line.split()[0]
                        result_module_name = module_name + ", Module %d" % modulePos
                        moduleNames.append(result_module_name)
                        modulePos += 1
                except :
                    pass

        if slave is not None:
            type_infos = slave.getType()

            device, _module_extra_params = self.GetModuleInfos(type_infos)
            if device is not None:
                sync_managers = []
                for sync_manager in device.getSm():
                    sync_manager_control_byte = ExtractHexDecValue(sync_manager.getControlByte())
                    sync_manager_direction = sync_manager_control_byte & 0x0c
                    if sync_manager_direction:
                        sync_managers.append(LOCATION_VAR_OUTPUT)
                    else:
                        sync_managers.append(LOCATION_VAR_INPUT)

                entries = device.GetEntriesList().items()
                entries.sort()
                for (index, subindex), entry in entries:
                    var_size = self.GetSizeOfType(entry["Type"])
                    if var_size is not None:
                        var_class = VARCLASSCONVERSION.get(entry["PDOMapping"], None)
                        if var_class is not None:
                            if var_class == LOCATION_VAR_INPUT:
                                var_dir = "%I"
                            else:
                                var_dir = "%Q"

                            vars.append({
                                "name": "0x%4.4x-0x%2.2x: %s" % (index, subindex, entry["Name"]),
                                "type": var_class,
                                "size": var_size,
                                "IEC_type": entry["Type"],
                                "var_name": "%s_%4.4x_%2.2x" % ("_".join(device_name.split()), index, subindex),
                                "location": "%s%s%s" % (var_dir, var_size, ".".join(map(str, current_location +
                                                                                        (index, subindex)))),
                                "description": "",
                                "children": [],
                            })

                # add jblee for MDP
                if not entries :
                    increment = self.CTNParent.GetModuleIncrement()[0]
                    count = 1
                    for moduleNameAndPos in moduleNames:
                        moduleName = moduleNameAndPos.split(",")[0]
                        idx_increment = int(increment) * count
                        for MDP_entry in module_info.get(moduleName):
                            local_idx = MDP_entry["Index"]
                            if ExtractHexDecValue(local_idx) != 0 and local_idx[0] == "#":
                                index = ExtractHexDecValue(local_idx) + idx_increment
                            else :
                                index = ExtractHexDecValue(MDP_entry["Index"])
                            subindex = int(MDP_entry["SubIndex"])
                            var_class = VARCLASSCONVERSION.get(MDP_entry["PDOMapping"], None)
                            if var_class is not None:
                                if var_class == LOCATION_VAR_INPUT:
                                    var_dir = "%I"
                                else:
                                    var_dir = "%Q"
                            var_size = self.GetSizeOfType(MDP_entry["Type"])
                            result_name = MDP_entry["Name"] + ", " + moduleNameAndPos
                            vars.append({"name": "0x%4.4x-0x%2.2x: %s" % (index, subindex, result_name),
                                         "type": var_class,
                                         "size": var_size,
                                         "IEC_type": MDP_entry["Type"],
                                         "var_name": "%s_%4.4x_%2.2x" % ("_".join(moduleName.split()), index, subindex),
                                         "location": "%s%s%s"%(var_dir, var_size, ".".join(map(str, current_location + 
                                                                                                    (index, subindex)))),
                                         "description": "",
                                         "children": []})
                        count += 1

        return vars

    def CTNTestModified(self):
        return self.ChangesToSave or not self.ModelIsSaved()

    def OnCTNSave(self, from_project_path=None):
        config_filepath = self.ConfigFileName()
        config_xmlfile = open(config_filepath, "w")
        config_xmlfile.write(etree.tostring(
            self.Config,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'))
        config_xmlfile.close()

        process_filepath = self.ProcessVariablesFileName()

        process_xmlfile = open(process_filepath, "w")
        process_xmlfile.write(etree.tostring(
            self.ProcessVariables,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'))
        process_xmlfile.close()

        self.Buffer.CurrentSaved()
        return True

    def GetProcessVariableName(self, location, var_type):
        return "__M%s_%s" % (self.GetSizeOfType(var_type), "_".join(map(str, location)))

    def _Generate_C(self, buildpath, locations):
        current_location = self.GetCurrentLocation()
        # define a unique name for the generated C file
        location_str = "_".join(map(str, current_location))

        Gen_Ethercatfile_path = os.path.join(buildpath, "ethercat_%s.c" % location_str)

        self.FileGenerator = _EthercatCFileGenerator(self)

        LocationCFilesAndCFLAGS, LDFLAGS, extra_files = ConfigTreeNode._Generate_C(self, buildpath, locations)

        for idx, variable in enumerate(self.ProcessVariables.getvariable()):
            name = None
            var_type = None
            read_from = variable.getReadFrom()
            write_to = variable.getWriteTo()
            if read_from is not None:
                pos = read_from.getPosition()
                index = read_from.getIndex()
                subindex = read_from.getSubIndex()
                location = current_location + (idx, )
                var_type = self.GetSlaveVariableDataType(pos, index, subindex)
                name = self.FileGenerator.DeclareVariable(pos, index, subindex,
                                                          var_type, "I",
                                                          self.GetProcessVariableName(location, var_type))
            if write_to is not None:
                pos = write_to.getPosition()
                index = write_to.getIndex()
                subindex = write_to.getSubIndex()
                if name is None:
                    location = current_location + (idx, )
                    var_type = self.GetSlaveVariableDataType(pos, index, subindex)
                    name = self.GetProcessVariableName(location, var_type)
                self.FileGenerator.DeclareVariable(pos, index, subindex, var_type, "Q", name, True)

        self.FileGenerator.GenerateCFile(Gen_Ethercatfile_path, location_str, self.BaseParams.getIEC_Channel())

        LocationCFilesAndCFLAGS.insert(
            0,
            (current_location,
             [(Gen_Ethercatfile_path, '"-I%s"' % os.path.abspath(self.GetCTRoot().GetIECLibPath()))],
             True))
        LDFLAGS.append("-lethercat_rtdm -lrtdm")

        return LocationCFilesAndCFLAGS, LDFLAGS, extra_files

    ConfNodeMethods = [
        {
            "bitmap": "ScanNetwork",
            "name": _("Scan Network"),
            "tooltip": _("Scan Network"),
            "method": "_ScanNetwork",
        },
    ]

    def CTNGenerate_C(self, buildpath, locations):
        current_location = self.GetCurrentLocation()

        slaves = self.GetSlaves()
        for slave_pos in slaves:
            slave = self.GetSlave(slave_pos)
            if slave is not None:
                self.FileGenerator.DeclareSlave(slave_pos, slave)

        for location in locations:
            loc = location["LOC"][len(current_location):]
            slave_pos = loc[0]
            if slave_pos in slaves and len(loc) == 3 and location["DIR"] != "M":
                self.FileGenerator.DeclareVariable(
                    slave_pos, loc[1], loc[2], location["IEC_TYPE"], location["DIR"], location["NAME"])

        return [], "", False

# -------------------------------------------------------------------------------
#                      Current Buffering Management Functions
# -------------------------------------------------------------------------------

    def Copy(self, model):
        """Return a copy of the config"""
        return deepcopy(model)

    def CreateBuffer(self, saved):
        self.Buffer = UndoBuffer(
            (EtherCATConfigParser.Dumps(self.Config),
             ProcessVariablesParser.Dumps(self.ProcessVariables)),
            saved)

    def BufferModel(self):
        self.Buffer.Buffering(
            (EtherCATConfigParser.Dumps(self.Config),
             ProcessVariablesParser.Dumps(self.ProcessVariables)))

    def ModelIsSaved(self):
        if self.Buffer is not None:
            return self.Buffer.IsCurrentSaved()
        else:
            return True

    def LoadPrevious(self):
        config, process_variables = self.Buffer.Previous()
        self.Config = EtherCATConfigParser.Loads(config)
        self.ProcessVariables = ProcessVariablesParser.Loads(process_variables)

    def LoadNext(self):
        config, process_variables = self.Buffer.Next()
        self.Config = EtherCATConfigParser.Loads(config)
        self.ProcessVariables = ProcessVariablesParser.Loads(process_variables)

    def GetBufferState(self):
        first = self.Buffer.IsFirst()
        last = self.Buffer.IsLast()
        return not first, not last
