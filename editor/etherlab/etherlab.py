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
import shutil
import csv
from builtins import str as text

from lxml import etree
import wx

from xmlclass import *

from ConfigTreeNode import XSDSchemaErrorMessage

from etherlab.EthercatSlave import ExtractHexDecValue, ExtractName
from etherlab.EthercatMaster import _EthercatCTN
from etherlab.ConfigEditor import LibraryEditor, ETHERCAT_VENDOR, ETHERCAT_GROUP, ETHERCAT_DEVICE

ScriptDirectory = os.path.split(os.path.realpath(__file__))[0]

# --------------------------------------------------
#                 Ethercat ConfNode
# --------------------------------------------------

EtherCATInfoParser = GenerateParserFromXSD(os.path.join(os.path.dirname(__file__), "EtherCATInfo.xsd"))


def EtherCATInfo_XPath(xpath):
    return etree.XPath(xpath)


EtherCATBaseParser = GenerateParserFromXSD(os.path.join(os.path.dirname(__file__), "EtherCATBase.xsd"))


def EtherCATBase_XPath(xpath):
    return etree.XPath(xpath)


def HexDecValue(context, *args):
    return str(ExtractHexDecValue(args[0][0]))


def EntryName(context, *args):
    return ExtractName(args[0], args[1][0] if len(args) > 1 else None)


ENTRY_INFOS_KEYS = [
    ("Index", lambda x: "#x%4.4X" % int(x), "#x0000"),
    ("SubIndex", str, "0"),
    ("Name", str, ""),
    ("Type", str, ""),
    ("BitSize", int, 0),
    ("Access", str, ""),
    ("PDOMapping", str, ""),
    ("PDO index", str, ""),
    ("PDO name", str, ""),
    ("PDO type", str, "")]

# Read DefaultValue from ESI file
# Add by jblee 151229
ENTRY_INFOS_KEYS_FOR_DV = [
    ("Index", lambda x: "#x%4.4X" % int(x), "#x0000"),
    ("SubIndex", str, "0"),
    ("Name", str, ""),
    ("Type", str, ""),
    ("BitSize", int, 0),
    ("Access", str, ""),
    ("PDOMapping", str, ""),
    ("DefaultValue", str, ""),
    ("Sub_entry_flag", str, "0")]

class EntryListFactory(object):

    def __init__(self, entries):
        self.Entries = entries

    def AddEntry(self, context, *args):
        index, subindex = map(lambda x: int(x[0]), args[:2])
        if len(args) > 9:
		    new_entry_infos = {
            key: translate(arg[0]) if len(arg) > 0 else default
            for (key, translate, default), arg
            in zip(ENTRY_INFOS_KEYS, args)}
        else:
            new_entry_infos = {
            key: translate(arg[0]) if len(arg) > 0 else default
            for (key, translate, default), arg
            in zip(ENTRY_INFOS_KEYS_FOR_DV, args)}			
			
        if (index, subindex) != (0, 0):
            entry_infos = self.Entries.get((index, subindex))
            if entry_infos is not None:
                for param in ["PDO index", "PDO name", "PDO type"]:
                    value = new_entry_infos.get(param)
                    if value is not None:
                        entry_infos[param] = value
            else:
                self.Entries[(index, subindex)] = new_entry_infos


entries_list_xslt = etree.parse(
    os.path.join(ScriptDirectory, "entries_list.xslt"))

cls = EtherCATInfoParser.GetElementClass("DeviceType")
if cls:
    cls.DataTypes = None
    
    profile_numbers_xpath = EtherCATInfo_XPath("Profile/ProfileNo")

    def GetProfileNumbers(self):
        return [number.text for number in profile_numbers_xpath(self)]
    setattr(cls, "GetProfileNumbers", GetProfileNumbers)

    def getCoE(self):
        mailbox = self.getMailbox()
        if mailbox is not None:
            return mailbox.getCoE()
        return None
    setattr(cls, "getCoE", getCoE)

    # Modify by jblee
    def ExtractDataTypes(self):
        #self.DataTypes = {}
        #self.DT = {}
        DT = {}
        objects = []

        # get Profile Field
        for profile in self.getProfile():
            # get each (ProfileNo, Dictionary) Field as child
            for child in profile.getchildren():
                # child.text is not None -> ProfileNo, is None -> Dictionary
                if child.text is None:
                    # get each (DataTypes, Objects) Field 
                    dataTypes = child.getDataTypes()
                    objects = child.getObjects()
                                
                    for dataType in dataTypes.getDataType():
                        #if dataType.getName() is not None:
                        #    print dataType.getName(), dataType
                        DT[dataType.getName()] = dataType

        return DT, objects
    setattr(cls, "ExtractDataTypes", ExtractDataTypes)

    def GetEntriesList(self, limits=None):
        DataTypes, objects = self.ExtractDataTypes()

        entries = {}

        # get each Object Field
        for object in objects:
            # Object Field mendatory : Index, Name, Type, BitSize
            # Frequently Use : Info, Flags
            # Info Field -> DefaultData, SubItem
            # Flags Field -> Access, Category, PdoMapping
            object_index = object.getIndex().getcontent()
            index = ExtractHexDecValue(object_index)
            if limits is None or limits[0] <= index <= limits[1]:
                object_type = object.getType()
                object_name = ExtractName(object.getName())
                object_size = object.getBitSize()
                defaultData = ""
                object_access = ""
                object_PDOMapping_data = ""

                object_type_infos = DataTypes.get(object_type, None)
                subItem_infos = object_type_infos.getchildren()
                countSubIndex = 0
                if len(subItem_infos) > 2:
                    for subItem_info in subItem_infos:
                        if subItem_info.tag == "SubItem" : 
                            subItemName = subItem_info.getName()
                            subIdx = subItem_info.getSubIdx()
                            if subIdx is not None:
                                object_subidx = ExtractHexDecValue(subIdx)
                            else:
                                object_subidx = ExtractHexDecValue(countSubIndex)
                            subType = subItem_info.getType()
                            subBitSize = subItem_info.getBitSize()
                            subFlags = subItem_info.getFlags()
                            subAccess = ""
                            subPDOMapping_data = ""
                            if subFlags is not None:
                                subAccess = subFlags.getAccess().getcontent()
                                subPDOMapping = subFlags.getPdoMapping()                                                        
                                if subPDOMapping is not None:
                                    subPDOMapping_data = subFlags.getPdoMapping().upper()

                            entries[(index, object_subidx)] = {
                                "Index": object_index,
                                "SubIndex": subIdx,
                                "Name": "%s - %s" % 
                                    (object_name.decode("utf-8"),
                                     subItemName.decode("utf-8")),
                                "Type": subType,
                                "BitSize": subBitSize,
                                "Access": subAccess, 
                                "PDOMapping": subPDOMapping_data}

                            countSubIndex += 1

                    info = object.getInfo()
                    # subItemTest : check subItem 
                    countSubIndex = 0
                    if info is not None:
                        subItems = info.getchildren()
                        if len(subItems) > 1:
                            for subItem in subItems:
                                defaultdata_subidx = ExtractHexDecValue(countSubIndex)
                                defaultData = subItem.getchildren()[1].findtext("DefaultData")
                                entry = entries.get((index, defaultdata_subidx), None)
                                if entry is not None:
                                    entry["DefaultData"] = defaultData
                                countSubIndex += 1

                else :
                    info = object.getInfo()
                    if info is not None:
                        subItems = info.getchildren()
                        if len(subItems) <= 1:
                            defaultData = subItems[0].text
                                
                    object_flag = object.getFlags()
                    object_access = object_flag.getAccess().getcontent()
                    object_PDOMapping = object_flag.getPdoMapping()
                    if object_PDOMapping is not None:
                        object_PDOMapping_data = object_flag.getPdoMapping().upper()
                    entries[(index, 0)] = {
                        "Index": object_index,
                        "SubIndex": "0",
                        "Name": object_name,                                                               
                        "Type": object_type,
                        "BitSize": object_size,
                        "DefaultData" : defaultData,
                        "Access": object_access, 
                        "PDOMapping": object_PDOMapping_data}

        for TxPdo in self.getTxPdo():
            ExtractPdoInfos(TxPdo, "Transmit", entries, limits)
        for RxPdo in self.getRxPdo():
            ExtractPdoInfos(RxPdo, "Receive", entries, limits)
        
        return entries
    setattr(cls, "GetEntriesList", GetEntriesList)

#    def GetEntriesList(self, limits=None):
#        entries = {}
        
#        factory = EntryListFactory(entries)
        
#        entries_list_xslt_tree = etree.XSLT(
#            entries_list_xslt, extensions = {
#                ("entries_list_ns", "AddEntry"): factory.AddEntry,
#                ("entries_list_ns", "HexDecValue"): HexDecValue,
#                ("entries_list_ns", "EntryName"): EntryName})
#        entries_list_xslt_tree(self, **dict(zip(
#            ["min_index", "max_index"], 
#            map(lambda x: etree.XSLT.strparam(str(x)),
#                limits if limits is not None else [0x0000, 0xFFFF])
#            )))
#        
#        return entries
#    setattr(cls, "GetEntriesList", GetEntriesList)

    def GetSyncManagers(self):
        sync_managers = []
        for sync_manager in self.getSm():
            sync_manager_infos = {}
            for name, value in [("Name", sync_manager.getcontent()),
                                ("Start Address", sync_manager.getStartAddress()),
                                ("Default Size", sync_manager.getDefaultSize()),
                                ("Control Byte", sync_manager.getControlByte()),
                                ("Enable", sync_manager.getEnable())]:
                if value is None:
                    value = ""
                sync_manager_infos[name] = value
            sync_managers.append(sync_manager_infos)
        return sync_managers
    setattr(cls, "GetSyncManagers", GetSyncManagers)


def GroupItemCompare(x, y):
    if x["type"] == y["type"]:
        if x["type"] == ETHERCAT_GROUP:
            return cmp(x["order"], y["order"])
        else:
            return cmp(x["name"], y["name"])
    elif x["type"] == ETHERCAT_GROUP:
        return -1
    return 1


def SortGroupItems(group):
    for item in group["children"]:
        if item["type"] == ETHERCAT_GROUP:
            SortGroupItems(item)
    group["children"].sort(GroupItemCompare)

def ExtractPdoInfos(pdo, pdo_type, entries, limits=None):
    pdo_index = pdo.getIndex().getcontent()
    pdo_name = ExtractName(pdo.getName())
    exclude = pdo.getExclude()
    for pdo_entry in pdo.getEntry():
        entry_index = pdo_entry.getIndex().getcontent()
        entry_subindex = pdo_entry.getSubIndex()
        index = ExtractHexDecValue(entry_index)
        subindex = ExtractHexDecValue(entry_subindex)
        object_size = pdo_entry.getBitLen()

        if limits is None or limits[0] <= index <= limits[1]:
            entry = entries.get((index, subindex), None)
            if entry is not None:
                entry["PDO index"] = pdo_index
                entry["PDO name"] = pdo_name
                entry["PDO type"] = pdo_type
            else:
                entry_type = pdo_entry.getDataType()
                if entry_type is not None:
                    if pdo_type == "Transmit":
                        access = "ro"
                        pdomapping = "T"
                    else:
                        access = "wo"
                        pdomapping = "R"
                    entries[(index, subindex)] = {
                        "Index": entry_index,
                        "SubIndex": entry_subindex,
                        "Name": ExtractName(pdo_entry.getName()),
                        "Type": entry_type.getcontent(),
                        "BitSize": object_size,
                        "Access": access,
                        "PDOMapping": pdomapping}

class ModulesLibrary(object):

    MODULES_EXTRA_PARAMS = [
        (
            "pdo_alignment",
            {
                "column_label": _("PDO alignment"),
                "column_size": 150,
                "default": 8,
                "description": _("Minimal size in bits between 2 pdo entries")
            }
        ),
        (
            "max_pdo_size",
            {
                "column_label": _("Max entries by PDO"),
                "column_size": 150,
                "default": 255,
                "description": _("""Maximal number of entries mapped in a PDO
including empty entries used for PDO alignment""")
            }
        ),
        (
            "add_pdo",
            {
                "column_label": _("Creating new PDO"),
                "column_size": 150,
                "default": 0,
                "description": _("""Adding a PDO not defined in default configuration
for mapping needed location variables
(1 if possible)""")
            }
        )
    ]

    def __init__(self, path, parent_library=None):
        self.Path = path
        if not os.path.exists(self.Path):
            os.makedirs(self.Path)
        self.ParentLibrary = parent_library

        if parent_library is not None:
            self.LoadModules()
        else:
            self.Library = None
        self.LoadModulesExtraParams()

    def GetPath(self):
        return self.Path

    def GetModulesExtraParamsFilePath(self):
        return os.path.join(self.Path, "modules_extra_params.cfg")

    groups_xpath = EtherCATInfo_XPath("Descriptions/Groups/Group")
    devices_xpath = EtherCATInfo_XPath("Descriptions/Devices/Device")
    module_xpath = EtherCATBase_XPath("Descriptions/Modules/Module")

    def LoadModules(self):
        self.Library = {}
        # add by jblee for Modular Device Profile
        self.MDPList = []
        self.ModuleList = []
        self.MDPEntryList = {}
        dtDic = {}
        self.idxIncrement = 0
        self.slotIncrement = 0
        # add by jblee for PDO Mapping
        self.DataTypes = {}
        self.ObjectDictionary = {}
        
        files = os.listdir(self.Path)
        for file in files:
            filepath = os.path.join(self.Path, file)
            if os.path.isfile(filepath) and os.path.splitext(filepath)[-1] == ".xml":
                self.modules_infos = None

                xmlfile = open(filepath, 'r')
                try:
                    self.modules_infos, error = EtherCATInfoParser.LoadXMLString(xmlfile.read())
                    # if error is not None:
                    #     self.GetCTRoot().logger.write_warning(
                    #         XSDSchemaErrorMessage % (filepath + error))
                except Exception as exc:
                    self.modules_infos, error = None, text(exc)
                xmlfile.close()

                if self.modules_infos is not None:
                    vendor = self.modules_infos.getVendor()

                    vendor_category = self.Library.setdefault(
                        ExtractHexDecValue(vendor.getId()),
                        {"name": ExtractName(vendor.getName(), _("Miscellaneous")),
                         "groups": {}})

                    for group in self.groups_xpath(self.modules_infos):
                        group_type = group.getType()
                        # add for XmlToEeprom Func by jblee.
                        self.LcId_data = group.getchildren()[1]
                        self.Image16x14_data = group.getchildren()[2]

                        vendor_category["groups"].setdefault(
                            group_type,
                            {
                                "name": ExtractName(group.getName(), group_type),
                                "parent": group.getParentGroup(),
                                "order": group.getSortOrder(),
                                "devices": [],
                                # add jblee for support Moduler Device Profile (MDP)
                                "modules": []})
                            })

                    for device in self.devices_xpath(self.modules_infos):
                        device_group = device.getGroupType()
                        if device_group not in vendor_category["groups"]:
                            raise ValueError("Not such group \"%s\"" % device_group)
                        vendor_category["groups"][device_group]["devices"].append(
                            (device.getType().getcontent(), device))

                        # ------------------ Test Section --------------------#
                        slots = device.getSlots()
                        if slots is not None:
                            for slot in slots.getSlot():
                                self.idxIncrement = slot.getSlotIndexIncrement()
                                self.slotIncrement = slot.getSlotPdoIncrement()
                                for child in slot.getchildren():
                                    if child.tag == "ModuleClass":
                                        child_class = child.getClass()
                                        child_name = child.getName()

                    # -------------------- Test Section ----------------------------------# 
                        LocalMDPList = []
                        for module in self.module_xpath(self.modules_infos):
                            module_type = module.getType().getModuleClass()
                            module_name = module.getName()
                            LocalMDPData = ExtractName(module_name) + " (" + module_type + ")"
                            
                            self.ModuleList.append(module)
                            try :
                                module_pdos = module.getTxPdo()
                                module_pdos += module.getRxPdo()
                                for module_pdo in module_pdos:
                                    device_name = ExtractName(module_name)
                                    pdo_index = module_pdo.getIndex().getcontent()
                                    pdo_name = ExtractName(module_pdo.getName())
                                    pdo_entry = module_pdo.getEntry()
                                    if module_pdo.tag == "TxPdo":
                                        mapping_type = "T"
                                    else :
                                        mapping_type = "R"

                                    LocalMDPEntry = []
                                    for entry in pdo_entry:
                                        entry_index = entry.getIndex().getcontent()
                                        entry_subidx = entry.getSubIndex()
                                        entry_name = ExtractName(entry.getName())
                                        entry_bitsize = entry.getBitLen()
                                        try :
                                           entry_type = entry.getDataType().getcontent()
                                        except :
                                           entry_type = ""

                                        LocalMDPEntry.append({
                                            "Index": entry_index,
                                            "SubIndex": entry_subidx,
                                            "Name": "%s - %s" % (pdo_name, entry_name),
                                            "Type": entry_type,
                                            "BitSize": entry_bitsize,
                                            "Access": "", 
                                            "PDOMapping": mapping_type})
                                
                                    self.MDPEntryList[device_name] = LocalMDPEntry

                                LocalMDPList.append([LocalMDPData, module, LocalMDPEntry])
                            except :
                                LocalMDPList.append([LocalMDPData, module, []])
                           
                        if LocalMDPList:
                            vendor_category["groups"][device_group]["modules"].append(
                                (device.getType().getcontent(), LocalMDPList, self.idxIncrement, self.slotIncrement))
                            #self.MDPList.append([device.getType().getcontent(), LocalMDPList,
                            #                     self.idxIncrement, self.slotIncrement])

                    # --------------------------------------------------------------------- #

                # else:
                #     self.GetCTRoot().logger.write_error(
                #         _("Couldn't load {a1} XML file:\n{a2}").format(a1=filepath, a2=error))

        return self.Library

    # add jblee
    def GetMDPList(self):
        return self.MDPList

    # add jblee
    def GetSelectModule(self, idx):
        return self.ModuleList[idx]

    # add jblee
    def GetModuleEntryList(self):
        return self.MDPEntryList

    # add jblee
    def GetModuleIncrement(self):
        return (self.idxIncrement, self.slotIncrement)

    # add jblee
    #def GetEntriesList(self):
    #    return self.ObjectDictionary
    
    def GetModulesLibrary(self, profile_filter=None):
        if self.Library is None:
            self.LoadModules()
        library = []
        for vendor_id, vendor in self.Library.iteritems():
            groups = []
            children_dict = {}
            for group_type, group in vendor["groups"].iteritems():
                group_infos = {"name": group["name"],
                               "order": group["order"],
                               "type": ETHERCAT_GROUP,
                               "infos": None,
                               "children": children_dict.setdefault(group_type, [])}
                device_dict = {}
                for device_type, device in group["devices"]:
                    if profile_filter is None or profile_filter in device.GetProfileNumbers():
                        product_code = device.getType().getProductCode()
                        revision_number = device.getType().getRevisionNo()
                        module_infos = {"device_type": device_type,
                                        "vendor": vendor_id,
                                        "product_code": product_code,
                                        "revision_number": revision_number}
                        module_infos.update(self.GetModuleExtraParams(vendor_id, product_code, revision_number))
                        device_infos = {"name": ExtractName(device.getName()),
                                        "type": ETHERCAT_DEVICE,
                                        "infos": module_infos,
                                        "children": []}
                        group_infos["children"].append(device_infos)
                        device_type_occurrences = device_dict.setdefault(device_type, [])
                        device_type_occurrences.append(device_infos)
                for device_type_occurrences in device_dict.itervalues():
                    if len(device_type_occurrences) > 1:
                        for occurrence in device_type_occurrences:
                            occurrence["name"] += _(" (rev. %s)") % occurrence["infos"]["revision_number"]
                if len(group_infos["children"]) > 0:
                    if group["parent"] is not None:
                        parent_children = children_dict.setdefault(group["parent"], [])
                        parent_children.append(group_infos)
                    else:
                        groups.append(group_infos)
            if len(groups) > 0:
                library.append({"name": vendor["name"],
                                "type": ETHERCAT_VENDOR,
                                "infos": None,
                                "children": groups})
        library.sort(lambda x, y: cmp(x["name"], y["name"]))
        return library

    def GetVendors(self):
        return [(vendor_id, vendor["name"]) for vendor_id, vendor in self.Library.items()]

    def GetModuleInfos(self, module_infos):
        vendor = ExtractHexDecValue(module_infos["vendor"])
        vendor_infos = self.Library.get(vendor)
        if vendor_infos is not None:
            for _group_name, group_infos in vendor_infos["groups"].iteritems():
                for device_type, device_infos in group_infos["devices"]:
                    product_code = ExtractHexDecValue(device_infos.getType().getProductCode())
                    revision_number = ExtractHexDecValue(device_infos.getType().getRevisionNo())
                    if product_code == ExtractHexDecValue(module_infos["product_code"]) and \
                       revision_number == ExtractHexDecValue(module_infos["revision_number"]):
                        self.cntdevice = device_infos
                        self.cntdeviceType = device_type
                        return device_infos, self.GetModuleExtraParams(vendor, product_code, revision_number)
        return None, None

    # add jblee for MDP
    def GetMDPInfos(self, module_infos):
        vendor = ExtractHexDecValue(module_infos["vendor"])
        vendor_infos = self.Library.get(vendor)
        if vendor_infos is not None:
            for group_name, group_infos in vendor_infos["groups"].iteritems():
                return group_infos["modules"]
                #for device_type, module_list, idx_inc, slot_inc in group_infos["modules"]:
                #    return module_list, idx_inc, slot_inc

        #return None, None, None
    
    def ImportModuleLibrary(self, filepath):
        if os.path.isfile(filepath):
            shutil.copy(filepath, self.Path)
            self.LoadModules()
            return True
        return False

    def LoadModulesExtraParams(self):
        self.ModulesExtraParams = {}

        csvfile_path = self.GetModulesExtraParamsFilePath()
        if os.path.exists(csvfile_path):
            csvfile = open(csvfile_path, "rb")
            sample = csvfile.read(1024)
            csvfile.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            has_header = csv.Sniffer().has_header(sample)
            reader = csv.reader(csvfile, dialect)
            for row in reader:
                if has_header:
                    has_header = False
                else:
                    params_values = {}
                    for (param, _param_infos), value in zip(
                            self.MODULES_EXTRA_PARAMS, row[3:]):
                        if value != "":
                            params_values[param] = int(value)
                    self.ModulesExtraParams[
                        tuple(map(int, row[:3]))] = params_values
            csvfile.close()

    def SaveModulesExtraParams(self):
        csvfile = open(self.GetModulesExtraParamsFilePath(), "wb")
        extra_params = [param for param, _params_infos in self.MODULES_EXTRA_PARAMS]
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['Vendor', 'product_code', 'revision_number'] + extra_params)
        for (vendor, product_code, revision_number), module_extra_params in self.ModulesExtraParams.iteritems():
            writer.writerow([vendor, product_code, revision_number] +
                            [module_extra_params.get(param, '')
                             for param in extra_params])
        csvfile.close()

    def SetModuleExtraParam(self, vendor, product_code, revision_number, param, value):
        vendor = ExtractHexDecValue(vendor)
        product_code = ExtractHexDecValue(product_code)
        revision_number = ExtractHexDecValue(revision_number)

        module_infos = (vendor, product_code, revision_number)
        self.ModulesExtraParams.setdefault(module_infos, {})
        self.ModulesExtraParams[module_infos][param] = value

        self.SaveModulesExtraParams()

    def GetModuleExtraParams(self, vendor, product_code, revision_number):
        vendor = ExtractHexDecValue(vendor)
        product_code = ExtractHexDecValue(product_code)
        revision_number = ExtractHexDecValue(revision_number)

        if self.ParentLibrary is not None:
            extra_params = self.ParentLibrary.GetModuleExtraParams(vendor, product_code, revision_number)
        else:
            extra_params = {}

        extra_params.update(self.ModulesExtraParams.get((vendor, product_code, revision_number), {}))

        for param, param_infos in self.MODULES_EXTRA_PARAMS:
            extra_params.setdefault(param, param_infos["default"])

        return extra_params


USERDATA_DIR = wx.StandardPaths.Get().GetUserDataDir()
if wx.Platform != '__WXMSW__':
    USERDATA_DIR += '_files'

ModulesDatabase = ModulesLibrary(
    os.path.join(USERDATA_DIR, "ethercat_modules"))


class RootClass(object):

    CTNChildrenTypes = [("EthercatNode", _EthercatCTN, "Ethercat Master")]
    EditorType = LibraryEditor

    def __init__(self):
        self.ModulesLibrary = None
        self.LoadModulesLibrary()

    def GetIconName(self):
        return "Ethercat"

    def GetModulesLibraryPath(self, project_path=None):
        if project_path is None:
            project_path = self.CTNPath()
        return os.path.join(project_path, "modules")

    def OnCTNSave(self, from_project_path=None):
        if from_project_path is not None:
            shutil.copytree(self.GetModulesLibraryPath(from_project_path),
                            self.GetModulesLibraryPath())
        return True

    def CTNGenerate_C(self, buildpath, locations):
        return [], "", False

    def LoadModulesLibrary(self):
        if self.ModulesLibrary is None:
            self.ModulesLibrary = ModulesLibrary(self.GetModulesLibraryPath(), ModulesDatabase)
        else:
            self.ModulesLibrary.LoadModulesLibrary()

    def GetModulesDatabaseInstance(self):
        return ModulesDatabase

    def GetModulesLibraryInstance(self):
        return self.ModulesLibrary

    def GetModulesLibrary(self, profile_filter=None):
        return self.ModulesLibrary.GetModulesLibrary(profile_filter)

    # add jblee
    def GetMDPList(self):
        return self.ModulesLibrary.GetMDPList()

    # add jblee
    def GetSelectModule(self, idx):
        return self.ModulesLibrary.GetSelectModule(idx)

    # add jblee
    def GetModuleEntryList(self):
        return self.ModulesLibrary.GetModuleEntryList()

    # add jblee
    def GetModuleIncrement(self):
        return self.ModulesLibrary.GetModuleIncrement()

    # add jblee
    #def GetEntriesList(self, limits = None):
    #    return self.ModulesLibrary.GetEntriesList()

    def GetVendors(self):
        return self.ModulesLibrary.GetVendors()

    def GetModuleInfos(self, module_infos):
        return self.ModulesLibrary.GetModuleInfos(module_infos)

    def GetMDPInfos(self, module_infos):
        return self.ModulesLibrary.GetMDPInfos(module_infos)
