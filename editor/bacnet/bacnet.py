#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard.
# This files implements the bacnet plugin for Beremiz, adding BACnet server support.
#
# Copyright (c) 2017 Mario de Sousa (msousa@fe.up.pt)
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
from collections import Counter
from datetime import datetime
import pickle

import wx

from bacnet.BacnetSlaveEditor import *
from bacnet.BacnetSlaveEditor import ObjectProperties
from PLCControler import LOCATION_CONFNODE, LOCATION_VAR_MEMORY

base_folder = os.path.split(
    os.path.dirname(os.path.realpath(__file__)))[0]
base_folder = os.path.join(base_folder, "..")
BacnetPath = os.path.join(base_folder, "BACnet")
BacnetLibraryPath = os.path.join(BacnetPath, "lib")
BacnetIncludePath = os.path.join(BacnetPath, "include")
BacnetIncludePortPath = os.path.join(BacnetPath, "ports")
BacnetIncludePortPath = os.path.join(BacnetIncludePortPath, "linux")

# Parameters to be monkey patched in beremiz customizations
BACNET_VENDOR_ID = 9999
BACNET_VENDOR_NAME = "Beremiz.org"
BACNET_DEVICE_MODEL_NAME = "Beremiz PLC"

#
#
#
# S L A V E    D E V I C E              #
#
#
#

# NOTE: Objects of class _BacnetSlavePlug are never instantiated directly.
#       The objects are instead instantiated from class FinalCTNClass
#       FinalCTNClass inherits from: - ConfigTreeNode
#                                    - The tree node plug (in our case _BacnetSlavePlug)
# class _BacnetSlavePlug:


class RootClass(object):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="BACnetServerNode">
        <xsd:complexType>
          <xsd:attribute name="Network_Interface"      type="xsd:string"  use="optional" default="eth0"/>
          <xsd:attribute name="UDP_Port_Number"                           use="optional" default="47808">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="65535"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="BACnet_Communication_Control_Password"
                                                       type="xsd:string"  use="optional" default="Malba Tahan"/>
          <xsd:attribute name="BACnet_Device_ID"                          use="optional" default="0">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="0"/>
                    <xsd:maxInclusive value="4194302"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="BACnet_Device_Name"        type="xsd:string"  use="optional" default="Beremiz device 0"/>
          <xsd:attribute name="BACnet_Device_Location"    type="xsd:string"  use="optional" default=""/>
          <xsd:attribute name="BACnet_Device_Description" type="xsd:string"  use="optional" default="Beremiz device 0"/>
          <xsd:attribute name="BACnet_Device_Application_Software_Version" type="xsd:string"  use="optional" default="1.0"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    # NOTE: BACnet device (object) IDs are 22 bits long (not counting the 10 bits for the type ID)
    #       so the Device instance ID is limited from 0 to 22^2-1 = 4194303
    #       However, 4194303 is reserved for special use (similar to NULL pointer), so last
    #       valid ID becomes 4194302

    # The class/object that will render the graphical interface to edit the
    #    BacnetSlavePlug's configuration parameters. The object of class BacnetSlaveEditorPlug
    #    will be instantiated by the ConfigTreeNode class.
    #    This BacnetSlaveEditorPlug object can be accessed from _BacnetSlavePlug as
    #    'self._View'
    #    See the following note to understand how this is possible!
    #
    # NOTE: Objects of class _BacnetSlavePlug are never instantiated directly.
    #       The objects are instead instantiated from class FinalCTNClass
    #       FinalCTNClass inherits from: - ConfigTreeNode
    #                                    - The tree node plug (in our case _BacnetSlavePlug)
    #
    #       This means that objects of class _BacnetSlavePlug may safely access all the members
    #       of classes ConfigTreeNode as well as FinalCTNClass (since they are always instantiated
    #       as a FinalCTNClass)
    EditorType = BacnetSlaveEditorPlug

    # The following classes follow the model/viewer design pattern
    #
    # _BacnetSlavePlug       - contains the model (i.e. configuration parameters)
    # BacnetSlaveEditorPlug  - contains the viewer (and editor, so it includes the 'controller' part of the
    #                                    design pattern which in this case is not separated from the viewer)
    #
    # The _BacnetSlavePlug      object is 'permanent', i.e. it exists as long as the beremiz project is open
    # The BacnetSlaveEditorPlug object is 'transient', i.e. it exists only while the editor is visible/open
    #                                                         in the editing panel. It is destoryed whenever
    #                                                         the user closes the corresponding tab in the
    #                                                         editing panel, and a new object is created when
    #                                                         the editor is re-opened.
    #
    # _BacnetSlavePlug contains:  AV_ObjTable, ...
    #                             (these are the objects that actually store the config parameters or 'model'
    #                              and are therefore stored to a file)
    #
    # _BacnetSlavePlug contains:  AV_VarEditor, ...
    #                             (these are the objects that implement a grid table to edit/view the
    #                              corresponding mode parameters)
    #
    #  Logic:
    #    - The xx_VarEditor classes inherit from wx.grid.Grid
    #    - The xx_ObjTable  classes inherit from wx.grid.PyGridTableBase
    #  To be more precise, the inheritance tree is actually:
    #    xx_VarEditor -> ObjectGrid -> CustomGrid   -> wx.grid.Grid
    #    xx_ObjTable  -> ObjectTable -> CustomTable -> wx.grid.PyGridTableBase)
    #
    #  Note that wx.grid.Grid is prepared to work with wx.grid.PyGridTableBase as the container of
    #  data that is displayed and edited in the Grid.

    ConfNodeMethods = [
        {"bitmap": "ExportSlave",
         "name": _("Export slave"),
         "tooltip": _("Export BACnet slave to EDE file"),
         "method": "_ExportBacnetSlave"},
    ]

    def __init__(self):
        # Initialize the dictionary that stores the current configuration for the Analog/Digital/MultiValued Variables
        #   in this BACnet server.
        self.ObjTablesData = {}

        # Each list will contain an entry for each row in the xxxxVar grid!!
        #   Each entry/row will be a dictionary
        #     Each dictionary will contain all entries/data
        # for one row in the grid.

        self.ObjTablesData["AV_Obj"] = []
        self.ObjTablesData["AO_Obj"] = []
        self.ObjTablesData["AI_Obj"] = []
        self.ObjTablesData["BV_Obj"] = []
        self.ObjTablesData["BO_Obj"] = []
        self.ObjTablesData["BI_Obj"] = []
        self.ObjTablesData["MSV_Obj"] = []
        self.ObjTablesData["MSO_Obj"] = []
        self.ObjTablesData["MSI_Obj"] = []

        self.ObjTablesData["EDEfile_parm"] = {"next_EDE_file_version": 1}

        # EDE files inlcude extra parameters (ex. file version)
        # We would like to save the parameters the user configures
        # so they are available the next time the user opens the project.
        # Since this plugin is only storing the ObjTablesData[] dict
        # to file, we add that info to this dictionary too.
        # Yes, I know this is kind of a
        # hack.

        filepath = self.GetFileName()
        if os.path.isfile(filepath):
            self.LoadFromFile(filepath)

        self.ObjTables = {}
        self.ObjTables["AV_Obj"] = ObjectTable(
            self, self.ObjTablesData["AV_Obj"],  AVObject)
        self.ObjTables["AO_Obj"] = ObjectTable(
            self, self.ObjTablesData["AO_Obj"],  AOObject)
        self.ObjTables["AI_Obj"] = ObjectTable(
            self, self.ObjTablesData["AI_Obj"],  AIObject)
        self.ObjTables["BV_Obj"] = ObjectTable(
            self, self.ObjTablesData["BV_Obj"],  BVObject)
        self.ObjTables["BO_Obj"] = ObjectTable(
            self, self.ObjTablesData["BO_Obj"],  BOObject)
        self.ObjTables["BI_Obj"] = ObjectTable(
            self, self.ObjTablesData["BI_Obj"],  BIObject)
        self.ObjTables["MSV_Obj"] = ObjectTable(
            self, self.ObjTablesData["MSV_Obj"], MSVObject)
        self.ObjTables["MSO_Obj"] = ObjectTable(
            self, self.ObjTablesData["MSO_Obj"], MSOObject)
        self.ObjTables["MSI_Obj"] = ObjectTable(
            self, self.ObjTablesData["MSI_Obj"], MSIObject)

    #
    # Functions to be called by CTNClass #
    #
    # The following functions would be somewhat equvalent to virtual functions/methods in C++ classes
    # They will be called by the base class (CTNClass) from which this
    # _BacnetSlavePlug class derives.

    def GetCurrentNodeName(self):
        return self.CTNName()

    def GetFileName(self):
        return os.path.join(self.CTNPath(), 'bacnet_slave')

    def OnCTNSave(self, from_project_path=None):
        return self.SaveToFile(self.GetFileName())

    def CTNTestModified(self):
        # self.ChangesToSave: Check whether any of the parameters, defined in the XSD above, were changed.
        #                     This is handled by the ConfigTreeNode class
        #                     (Remember that no objects are ever instantiated from _BacnetSlavePlug.
        #                      Objects are instead created from FinalCTNClass, which derives from
        #                      _BacnetSlavePlug and ConfigTreeNode. This means that we can exceptionally
        # consider that all objects of type _BacnetSlavePlug will also be a
        # ConfigTreeNode).
        result = self.ChangesToSave \
            or self.ObjTables["AV_Obj"].ChangesToSave \
            or self.ObjTables["AO_Obj"].ChangesToSave \
            or self.ObjTables["AI_Obj"].ChangesToSave \
            or self.ObjTables["BV_Obj"].ChangesToSave \
            or self.ObjTables["BO_Obj"].ChangesToSave \
            or self.ObjTables["BI_Obj"].ChangesToSave \
            or self.ObjTables["MSV_Obj"].ChangesToSave \
            or self.ObjTables["MSO_Obj"].ChangesToSave \
            or self.ObjTables["MSI_Obj"].ChangesToSave
        return result

    # Currently not needed. Override _OpenView() in case we need to do some special stuff whenever the editor is opened!
    # def _OpenView(self, name=None, onlyopened=False):
        # print "_BacnetSlavePlug._OpenView() Called!!!"
        # ConfigTreeNode._OpenView(self, name, onlyopened)
        # print self._View
        # if self._View is not None:
        #     self._View.SetBusId(self.GetCurrentLocation())
        # return self._View

    def GetVariableLocationTree(self):
        current_location = self.GetCurrentLocation()
        # see comment in CTNGenerate_C regarding identical line of code!
        locstr = ".".join(map(str, current_location))

        # IDs used by BACnet to identify object types/class.
        #     OBJECT_ANALOG_INPUT       =  0,
        #     OBJECT_ANALOG_OUTPUT      =  1,
        #     OBJECT_ANALOG_VALUE       =  2,
        #     OBJECT_BINARY_INPUT       =  3,
        #     OBJECT_BINARY_OUTPUT      =  4,
        #     OBJECT_BINARY_VALUE       =  5,
        #     OBJECT_MULTI_STATE_INPUT  = 13,
        #     OBJECT_MULTI_STATE_OUTPUT = 14,
        #     OBJECT_MULTI_STATE_VALUE  = 19,
        #
        #  Since Binary Value, Analog Value, etc. objects may use the same
        # object ID (since they have distinct class IDs), we must also distinguish them in some way in
        # the %MX0.3.4 IEC 61131-3 syntax.
        #
        # For this reason we add the BACnet class identifier to the %MX0.5.3 location.
        # For example, for a BACnet plugin in location '0' of the Beremiz configuration tree,
        #  all      Binary Values will be mapped onto: %MX0.5.xxx    (xxx is object ID)
        #  all Multi State Values will be mapped onto: %MB0.19.xxx   (xxx is object ID)
        #  all      Analog Values will be mapped onto: %MD0.2.xxx    (xxx is object ID)
        #  etc..
        #
        #   Value objects will be mapped onto %M
        #   Input objects will be mapped onto %I
        #  Output objects will be mapped onto %Q

        BACnetEntries = []
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["AV_Obj"], 32, 'REAL', 'D', locstr + '.2', 'Analog Values'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["AO_Obj"], 32, 'REAL', 'D', locstr + '.1', 'Analog Outputs'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["AI_Obj"], 32, 'REAL', 'D', locstr + '.0', 'Analog Inputs'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["BV_Obj"],  1, 'BOOL', 'X', locstr + '.5', 'Binary Values'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["BO_Obj"],  1, 'BOOL', 'X', locstr + '.4', 'Binary Outputs'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["BI_Obj"],  1, 'BOOL', 'X', locstr + '.3', 'Binary Inputs'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["MSV_Obj"],  8, 'BYTE', 'B', locstr + '.19', 'Multi State Values'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["MSO_Obj"],  8, 'BYTE', 'B', locstr + '.14', 'Multi State Outputs'))
        BACnetEntries.append(self.GetSlaveLocationTree(
            self.ObjTablesData["MSI_Obj"],  8, 'BYTE', 'B', locstr + '.13', 'Multi State Inputs'))

        return {"name": self.BaseParams.getName(),
                "type": LOCATION_CONFNODE,
                "location": locstr + ".x",
                "children": BACnetEntries}

    #
    # Helper functions/methods #
    #
    # a helper function to GetVariableLocationTree()
    def GetSlaveLocationTree(self, ObjTablesData, size_in_bits, IECdatatype, location_size, location_str, name):
        BACnetObjectEntries = []
        for xx_ObjProp in ObjTablesData:
            BACnetObjectEntries.append({
                "name": str(xx_ObjProp["Object Identifier"]) + ': ' + xx_ObjProp["Object Name"],
                "type": LOCATION_VAR_MEMORY,  # LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT, or LOCATION_VAR_MEMORY
                "size": size_in_bits,  # 1 or 16
                "IEC_type": IECdatatype,  # 'BOOL', 'WORD', ...
                "var_name": "var_name",  # seems to be ignored??
                "location": location_size + location_str + "." + str(xx_ObjProp["Object Identifier"]),
                "description": "description",  # seems to be ignored?
                "children": []})

        return {"name": name,
                "type": LOCATION_CONFNODE,
                "location": location_str + ".x",
                "children": BACnetObjectEntries}

    # Returns a dictionary with:
    #      keys: names  of BACnet objects
    #     value: number of BACnet objects using this same name
    #            (values larger than 1 indicates an error as BACnet requires unique names)
    def GetObjectNamesCount(self):
        # The dictionary is built by first creating a list containing the names of _ALL_
        # BACnet objects currently configured by the user (using the GUI)
        ObjectNames = []
        ObjectNames.extend(
            self.ObjTables["AV_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["AO_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["AI_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["BV_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["BO_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["BI_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["MSV_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["MSO_Obj"].GetAllValuesByName("Object Name"))
        ObjectNames.extend(
            self.ObjTables["MSI_Obj"].GetAllValuesByName("Object Name"))
        # This list is then transformed into a collections.Counter class
        # Which is then transformed into a dictionary using dict()
        return dict(Counter(ObjectNames))

    # Check whether the current configuration contains BACnet objects configured
    # with the same identical object name  (returns True or False)
    def HasDuplicateObjectNames(self):
        ObjectNamesCount = self.GetObjectNamesCount()
        for ObjName in ObjectNamesCount:
            if ObjectNamesCount[ObjName] > 1:
                return True
        return False

    # Check whether any object ID is used more than once (not valid in BACnet)
    # (returns True or False)
    def HasDuplicateObjectIDs(self):
        res = self.ObjTables["AV_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["AO_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["AI_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["BV_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["BO_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["BI_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["MSV_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["MSO_Obj"].HasDuplicateObjectIDs()
        res = res or self.ObjTables["MSI_Obj"].HasDuplicateObjectIDs()
        return res

    #
    # Methods related to files (saving/loading/exporting) #
    #
    def SaveToFile(self, filepath):
        # Save node data in file
        # The configuration data declared in the XSD string will be saved by the ConfigTreeNode class,
        # so we only need to save the data that is stored in ObjTablesData objects
        # Note that we do not store the ObjTables objects. ObjTables is of a class that
        # contains more stuff we do not need to store. Actually it is a bad idea to store
        # this extra stuff (as we would make the files we generate dependent on the actual
        # version of the wx library we are using!!! Remember that ObjTables evetually
        # derives/inherits from wx.grid.PyGridTableBase). Another reason not to store the whole
        # object is because it is not pickable (i.e. pickle.dump() cannot handle it)!!
        try:
            fd = open(filepath,   "w")
            pickle.dump(self.ObjTablesData, fd)
            fd.close()
            # On successfull save, reset flags to indicate no more changes that
            # need saving
            self.ObjTables["AV_Obj"].ChangesToSave = False
            self.ObjTables["AO_Obj"].ChangesToSave = False
            self.ObjTables["AI_Obj"].ChangesToSave = False
            self.ObjTables["BV_Obj"].ChangesToSave = False
            self.ObjTables["BO_Obj"].ChangesToSave = False
            self.ObjTables["BI_Obj"].ChangesToSave = False
            self.ObjTables["MSV_Obj"].ChangesToSave = False
            self.ObjTables["MSO_Obj"].ChangesToSave = False
            self.ObjTables["MSI_Obj"].ChangesToSave = False
            return True
        except Exception:
            return _("Unable to save to file \"%s\"!") % filepath

    def LoadFromFile(self, filepath):
        # Load the data that is saved in SaveToFile()
        try:
            fd = open(filepath,   "r")
            self.ObjTablesData = pickle.load(fd)
            fd.close()
            return True
        except Exception:
            return _("Unable to load file \"%s\"!") % filepath

    def _ExportBacnetSlave(self):
        dialog = wx.FileDialog(self.GetCTRoot().AppFrame,
                               _("Choose a file"),
                               os.path.expanduser("~"),
                               "%s_EDE.csv" % self.CTNName(),
                               _("EDE files (*_EDE.csv)|*_EDE.csv|All files|*.*"),
                               wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            result = self.GenerateEDEFile(dialog.GetPath())
            result = False
            if result:
                self.GetCTRoot().logger.write_error(
                    _("Error: Export slave failed\n"))
        dialog.Destroy()

    def GenerateEDEFile(self, filename):
        template_file_dir = os.path.join(
            os.path.split(__file__)[0], "ede_files")

        # The BACnetServerNode attribute is added dynamically by ConfigTreeNode._AddParamsMembers()
        # It will be an XML parser object created by
        # GenerateParserFromXSDstring(self.XSD).CreateRoot()
        BACnet_Device_ID = self.BACnetServerNode.getBACnet_Device_ID()

        # The EDE file contains a header that includes general project data (name, author, ...)
        # Instead of asking the user for this data, we get it from the configuration
        # of the Beremiz project itself.
        # We ask the root Config Tree Node for the data...
        ProjProp = {}
        FileProp = {}

        # this should be an object of class ProjectController
        CTN_Root = self.GetCTRoot()

        # this should be an object capable of parsing
        # PLCopen XML files. The parser is created automatically
        # (i.e. using GenerateParserFromXSD() from xmlclass module)
        # using the PLCopen XSD file defining the format of the XML.
        # See the file plcopen/plcopen.py
        Project = CTN_Root.Project
        if Project is not None:
            # getcontentHeader() and getfileHeader() are functions that are conditionally defined in
            # plcopn/plcopen.py    We cannot rely on their existance
            if getattr(Project, "getcontentHeader", None) is not None:
                ProjProp = Project.getcontentHeader()
                # getcontentHeader() returns a dictionary. Available keys are:
                # "projectName", "projectVersion", "modificationDateTime",
                # "organization", "authorName", "language", "pageSize", "scaling"
            if getattr(Project, "getfileHeader", None) is not None:
                FileProp = Project.getfileHeader()
                # getfileHeader() returns a dictionary. Available keys are:
                # "companyName", "companyURL", "productName", "productVersion",
                # "productRelease", "creationDateTime", "contentDescription"

        ProjName = ""
        if "projectName" in ProjProp:
            ProjName = ProjProp["projectName"]
        ProjAuthor = ""
        if "companyName" in FileProp:
            ProjAuthor += "(" + FileProp["companyName"] + ")"
        if "authorName" in ProjProp:
            ProjAuthor = ProjProp["authorName"] + " " + ProjAuthor

        projdata_dict = {}
        projdata_dict["Project Name"] = ProjName
        projdata_dict["Project Author"] = ProjAuthor
        projdata_dict["Current Time"] = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        projdata_dict["EDE file version"] = self.ObjTablesData[
            "EDEfile_parm"]["next_EDE_file_version"]

        # Next time we generate an EDE file, use another version!
        self.ObjTablesData["EDEfile_parm"]["next_EDE_file_version"] += 1

        AX_params_format = "%(Object Name)s;" + str(BACnet_Device_ID) + \
            ";%(Object Name)s;%(BACnetObjTypeID)s;%(Object Identifier)s;%(Description)s;0;;;%(Settable)s;N;;;;%(Unit ID)s;"

        BX_params_format = "%(Object Name)s;" + str(BACnet_Device_ID) + \
            ";%(Object Name)s;%(BACnetObjTypeID)s;%(Object Identifier)s;%(Description)s;0;0;1;%(Settable)s;N;;;;;"

        MSX_params_format = "%(Object Name)s;" + str(BACnet_Device_ID) + \
            ";%(Object Name)s;%(BACnetObjTypeID)s;%(Object Identifier)s;%(Description)s;1;1;%(Number of States)s;%(Settable)s;N;;;;;"

        Objects_List = []
        for ObjType, params_format in [("AV",  AX_params_format),
                                       ("AO",  AX_params_format),
                                       ("AI",  AX_params_format),
                                       ("BV",  BX_params_format),
                                       ("BO",  BX_params_format),
                                       ("BI",  BX_params_format),
                                       ("MSV", MSX_params_format),
                                       ("MSO", MSX_params_format),
                                       ("MSI", MSX_params_format)]:
            self.ObjTables[ObjType + "_Obj"].UpdateAllVirtualProperties()
            for ObjProp in self.ObjTablesData[ObjType + "_Obj"]:
                Objects_List.append(params_format % ObjProp)

        # Normalize filename
        for extension in ["_EDE.csv", "_ObjTypes.csv", "_StateTexts.csv", "_Units.csv"]:
            if filename.lower().endswith(extension.lower()):
                filename = filename[:-len(extension)]

        # EDE_header
        generate_file_name = filename + "_EDE.csv"
        template_file_name = os.path.join(
            template_file_dir, "template_EDE.csv")
        generate_file_content = open(template_file_name).read() % projdata_dict
        generate_file_handle = open(generate_file_name, 'w')
        generate_file_handle  .write(generate_file_content)
        generate_file_handle  .write("\n".join(Objects_List))
        generate_file_handle  .close()

        # templates of remaining files do not need changes. They are simply
        # copied unchanged!
        for extension in ["_ObjTypes.csv", "_StateTexts.csv", "_Units.csv"]:
            generate_file_name = filename + extension
            template_file_name = os.path.join(
                template_file_dir, "template" + extension)
            generate_file_content = open(template_file_name).read()
            generate_file_handle = open(generate_file_name, 'w')
            generate_file_handle  .write(generate_file_content)
            generate_file_handle  .close()

    #
    # Generate the source files #
    #
    def CTNGenerate_C(self, buildpath, locations):
        # Determine the current location in Beremiz's project configuration
        # tree
        current_location = self.GetCurrentLocation()
        # The current location of this plugin in Beremiz's configuration tree, separated by underscores
        #  NOTE: Since BACnet plugin currently does not use sub-branches in the tree (in other words, this
        #        _BacnetSlavePlug class was actually renamed as the RootClass), the current_location_dots
        #        will actually be a single number (e.g.: 0 or 3 or 6, corresponding to the location
        #        in which the plugin was inserted in the Beremiz configuration tree on Beremiz's left panel).
        locstr = "_".join(map(str, current_location))

        # First check whether all the current parameters (inserted by user in
        # the GUI) are valid...
        if self.HasDuplicateObjectNames():
            self.GetCTRoot().logger.write_warning(
                _("Error: BACnet server '{a1}.x:{a2}' contains objects with duplicate object names.\n").
                format(a1=locstr, a2=self.CTNName()))
            raise Exception(False)
            # TODO: return an error code instead of raising an exception
            # (currently unsupported by Beremiz)

        if self.HasDuplicateObjectIDs():
            self.GetCTRoot().logger.write_warning(
                _("Error: BACnet server '{a1}.x: {a2}' contains objects with duplicate object identifiers.\n").
                format(a1=locstr, a2=self.CTNName()))
            raise Exception(False)
            # TODO: return an error code instead of raising an exception
            # (currently unsupported by Beremiz)

        # -------------------------------------------------------------------------------
        # Create and populate the loc_dict dictionary with all parameters needed to configure
        #  the generated source code (.c and .h files)
        # ----------------------------------------------------------------------

        # 1) Create the dictionary (loc_dict = {})
        loc_dict = {}
        loc_dict["locstr"] = locstr

        # The BACnetServerNode attribute is added dynamically by ConfigTreeNode._AddParamsMembers()
        # It will be an XML parser object created by
        # GenerateParserFromXSDstring(self.XSD).CreateRoot()
        loc_dict["network_interface"] = self.BACnetServerNode.getNetwork_Interface()
        loc_dict["port_number"] = self.BACnetServerNode.getUDP_Port_Number()
        loc_dict["BACnet_Device_ID"] = self.BACnetServerNode.getBACnet_Device_ID()
        loc_dict["BACnet_Device_Name"] = self.BACnetServerNode.getBACnet_Device_Name()
        loc_dict["BACnet_Comm_Control_Password"] = self.BACnetServerNode.getBACnet_Communication_Control_Password()
        loc_dict["BACnet_Device_Location"] = self.BACnetServerNode.getBACnet_Device_Location()
        loc_dict["BACnet_Device_Description"] = self.BACnetServerNode.getBACnet_Device_Description()
        loc_dict["BACnet_Device_AppSoft_Version"] = self.BACnetServerNode.getBACnet_Device_Application_Software_Version()
        loc_dict["BACnet_Vendor_ID"] = BACNET_VENDOR_ID
        loc_dict["BACnet_Vendor_Name"] = BACNET_VENDOR_NAME
        loc_dict["BACnet_Model_Name"] = BACNET_DEVICE_MODEL_NAME

        # 2) Add the data specific to each BACnet object type
        # For each BACnet object type, start off by creating some intermediate helpful lists
        #  a) parameters_list containing the strings that will
        #     be included in the C source code, and which will initialize the struct with the
        #     object (Analog Value, Binary Value, or Multi State Value) parameters
        #  b) locatedvar_list containing the strings that will
        #     declare the memory to store the located variables, as well as the
        #     pointers (required by matiec) that point to that memory.

        # format for delaring IEC 61131-3 variable (and pointer) onto which
        # BACnet object is mapped
        locvar_format = '%(Ctype)s ___%(loc)s_%(Object Identifier)s; ' + \
                        '%(Ctype)s *__%(loc)s_%(Object Identifier)s = &___%(loc)s_%(Object Identifier)s;'

        # format for initializing a ANALOG_VALUE_DESCR struct in C code
        #    also valid for ANALOG_INPUT and ANALOG_OUTPUT
        AX_params_format = '{&___%(loc)s_%(Object Identifier)s, ' + \
            '%(Object Identifier)s, "%(Object Name)s", "%(Description)s", %(Unit ID)d}'
        # format for initializing a BINARY_VALUE_DESCR struct in C code
        #    also valid for BINARY_INPUT and BINARY_OUTPUT
        BX_params_format = '{&___%(loc)s_%(Object Identifier)s, ' + \
            '%(Object Identifier)s, "%(Object Name)s", "%(Description)s"}'

        # format for initializing a MULTISTATE_VALUE_DESCR struct in C code
        #    also valid for MULTISTATE_INPUT and MULTISTATE_OUTPUT
        MSX_params_format = '{&___%(loc)s_%(Object Identifier)s, ' + \
            '%(Object Identifier)s, "%(Object Name)s", "%(Description)s", %(Number of States)s}'

        # see the comment in GetVariableLocationTree()
        AV_locstr = 'MD' + locstr + '_2'
        AO_locstr = 'QD' + locstr + '_1'
        AI_locstr = 'ID' + locstr + '_0'
        BV_locstr = 'MX' + locstr + '_5'
        BO_locstr = 'QX' + locstr + '_4'
        BI_locstr = 'IX' + locstr + '_3'
        MSV_locstr = 'MB' + locstr + '_19'
        MSO_locstr = 'QB' + locstr + '_14'
        MSI_locstr = 'IB' + locstr + '_13'

        for ObjType,  ObjLocStr,     params_format in [
                ("AV",  AV_locstr,  AX_params_format),
                ("AO",  AO_locstr,  AX_params_format),
                ("AI",  AI_locstr,  AX_params_format),
                ("BV",  BV_locstr,  BX_params_format),
                ("BO",  BO_locstr,  BX_params_format),
                ("BI",  BI_locstr,  BX_params_format),
                ("MSV", MSV_locstr, MSX_params_format),
                ("MSO", MSO_locstr, MSX_params_format),
                ("MSI", MSI_locstr, MSX_params_format)]:
            parameters_list = []
            locatedvar_list = []
            self.ObjTables[ObjType + "_Obj"].UpdateAllVirtualProperties()
            for ObjProp in self.ObjTablesData[ObjType + "_Obj"]:
                ObjProp["loc"] = ObjLocStr
                parameters_list.append(params_format % ObjProp)
                locatedvar_list.append(locvar_format % ObjProp)
            loc_dict[ObjType + "_count"] = len(parameters_list)
            loc_dict[ObjType + "_param"] = ",\n".join(parameters_list)
            loc_dict[ObjType + "_lvars"] = "\n".join(locatedvar_list)

        # ----------------------------------------------------------------------
        # Create the C source files that implement the BACnet server
        # ----------------------------------------------------------------------

        # Names of the .c files that will be generated, based on a template file with same name
        #   (names without '.c'  --> this will be added later)
        #   main server.c file is handled separately
        Generated_BACnet_c_mainfile = "server"
        Generated_BACnet_c_files = [
            "ai", "ao", "av", "bi", "bo", "bv", "msi", "mso", "msv", "device"]

        # Names of the .h files that will be generated, based on a template file with same name
        #   (names without '.h'  --> this will be added later)
        Generated_BACnet_h_files = [
            "server", "device", "config_bacnet_for_beremiz",
            "ai", "ao", "av", "bi", "bo", "bv", "msi", "mso", "msv"
        ]

        # Generate the files with the source code
        postfix = "_".join(map(str, current_location))
        template_file_dir = os.path.join(
            os.path.split(__file__)[0], "runtime")

        def generate_file(file_name, extension):
            generate_file_name = os.path.join(
                buildpath, "%s_%s.%s" % (file_name, postfix, extension))
            template_file_name = os.path.join(
                template_file_dir, "%s.%s" % (file_name, extension))
            generate_file_content = open(template_file_name).read() % loc_dict
            generate_file_handle = open(generate_file_name, 'w')
            generate_file_handle.write(generate_file_content)
            generate_file_handle.close()

        for file_name in Generated_BACnet_c_files:
            generate_file(file_name, "c")
        for file_name in Generated_BACnet_h_files:
            generate_file(file_name, "h")
        generate_file(Generated_BACnet_c_mainfile, "c")
        Generated_BACnet_c_mainfile_name = \
            os.path.join(buildpath, "%s_%s.%s" %
                         (Generated_BACnet_c_mainfile, postfix, "c"))

        # ----------------------------------------------------------------------
        # Finally, define the compilation and linking commands and flags
        # ----------------------------------------------------------------------

        LDFLAGS = []
        # when using dynamically linked library...
        # LDFLAGS.append(' -lbacnet')
        # LDFLAGS.append(' -L"'+BacnetLibraryPath+'"')
        # LDFLAGS.append(' "-Wl,-rpath,' + BacnetLibraryPath + '"')
        # when using static library:
        LDFLAGS.append(
            ' "' + os.path.join(BacnetLibraryPath, "libbacnet.a") + '"')

        CFLAGS = ' -I"' + BacnetIncludePath + '"'
        CFLAGS += ' -I"' + BacnetIncludePortPath + '"'

        return [(Generated_BACnet_c_mainfile_name, CFLAGS)], LDFLAGS, True
