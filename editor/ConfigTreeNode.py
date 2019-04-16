#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
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

"""
Config Tree Node base class.

- A Beremiz project is organized in a tree each node derivate from ConfigTreeNode
- Project tree organization match filesystem organization of project directory.
- Each node of the tree have its own xml configuration, whose grammar is defined for each node type, as XSD
- ... TODO : document
"""

from __future__ import absolute_import
import os
import traceback
import types
import shutil
from operator import add
from functools import reduce
from builtins import str as text
from past.builtins import execfile

from lxml import etree

from xmlclass import GenerateParserFromXSDstring
from PLCControler import LOCATION_CONFNODE
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor

_BaseParamsParser = GenerateParserFromXSDstring("""<?xml version="1.0" encoding="ISO-8859-1" ?>
        <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
          <xsd:element name="BaseParams">
            <xsd:complexType>
              <xsd:attribute name="Name" type="xsd:string" use="optional" default="__unnamed__"/>
              <xsd:attribute name="IEC_Channel" type="xsd:integer" use="required"/>
              <xsd:attribute name="Enabled" type="xsd:boolean" use="optional" default="true"/>
            </xsd:complexType>
          </xsd:element>
        </xsd:schema>""")

NameTypeSeparator = '@'
XSDSchemaErrorMessage = _("{a1} XML file doesn't follow XSD schema at line {a2}:\n{a3}")


class ConfigTreeNode(object):
    """
    This class is the one that define confnodes.
    """

    XSD = None
    CTNChildrenTypes = []
    CTNMaxCount = None
    ConfNodeMethods = []
    LibraryControler = None
    EditorType = ConfTreeNodeEditor
    IconPath = None

    def _AddParamsMembers(self):
        self.CTNParams = None
        if self.XSD:
            self.Parser = GenerateParserFromXSDstring(self.XSD)
            obj = self.Parser.CreateRoot()
            name = obj.getLocalTag()
            self.CTNParams = (name, obj)
            setattr(self, name, obj)

    def __init__(self):
        # Create BaseParam
        self.BaseParams = _BaseParamsParser.CreateRoot()
        self.MandatoryParams = ("BaseParams", self.BaseParams)
        self._AddParamsMembers()
        self.Children = {}
        self._View = None
        # copy ConfNodeMethods so that it can be later customized
        self.ConfNodeMethods = [dic.copy() for dic in self.ConfNodeMethods]

    def ConfNodeBaseXmlFilePath(self, CTNName=None):
        return os.path.join(self.CTNPath(CTNName), "baseconfnode.xml")

    def ConfNodeXmlFilePath(self, CTNName=None):
        return os.path.join(self.CTNPath(CTNName), "confnode.xml")

    def ConfNodePath(self):
        return os.path.join(self.CTNParent.ConfNodePath(), self.CTNType)

    def CTNPath(self, CTNName=None, project_path=None):
        if not CTNName:
            CTNName = self.CTNName()
        if not project_path:
            project_path = self.CTNParent.CTNPath()
        return os.path.join(project_path,
                            CTNName + NameTypeSeparator + self.CTNType)

    def CTNName(self):
        return self.BaseParams.getName()

    def CTNEnabled(self):
        return self.BaseParams.getEnabled()

    def CTNFullName(self):
        parent = self.CTNParent.CTNFullName()
        if parent != "":
            return parent + "." + self.CTNName()
        return self.BaseParams.getName()

    def CTNSearch(self, criteria):
        # TODO match config's fields name and fields contents
        return reduce(add, [
            CTNChild.CTNSearch(criteria)
            for CTNChild in self.IterChildren()], [])

    def GetIconName(self):
        return None

    def CTNTestModified(self):
        return self.ChangesToSave

    def ProjectTestModified(self):
        """
        recursively check modified status
        """
        if self.CTNTestModified():
            return True

        for CTNChild in self.IterChildren():
            if CTNChild.ProjectTestModified():
                return True

        return False

    def RemoteExec(self, script, **kwargs):
        return self.CTNParent.RemoteExec(script, **kwargs)

    def OnCTNSave(self, from_project_path=None):
        """Default, do nothing and return success"""
        return True

    def GetParamsAttributes(self, path=None):
        if path:
            parts = path.split(".", 1)
            if self.MandatoryParams and parts[0] == self.MandatoryParams[0]:
                return self.MandatoryParams[1].getElementInfos(parts[0], parts[1])
            elif self.CTNParams and parts[0] == self.CTNParams[0]:
                return self.CTNParams[1].getElementInfos(parts[0], parts[1])
        else:
            params = []
            if self.CTNParams:
                params.append(self.CTNParams[1].getElementInfos(self.CTNParams[0]))
            return params

    def SetParamsAttribute(self, path, value):
        self.ChangesToSave = True
        # Filter IEC_Channel and Name, that have specific behavior
        if path == "BaseParams.IEC_Channel":
            old_leading = ".".join(map(str, self.GetCurrentLocation()))
            new_value = self.FindNewIEC_Channel(value)
            if new_value != value:
                new_leading = ".".join(map(str, self.CTNParent.GetCurrentLocation() + (new_value,)))
                self.GetCTRoot().UpdateProjectVariableLocation(old_leading, new_leading)
            return new_value, True
        elif path == "BaseParams.Name":
            res = self.FindNewName(value)
            self.CTNRequestSave()
            return res, True

        parts = path.split(".", 1)
        if self.MandatoryParams and parts[0] == self.MandatoryParams[0]:
            self.MandatoryParams[1].setElementValue(parts[1], value)
            value = self.MandatoryParams[1].getElementInfos(parts[0], parts[1])["value"]
        elif self.CTNParams and parts[0] == self.CTNParams[0]:
            self.CTNParams[1].setElementValue(parts[1], value)
            value = self.CTNParams[1].getElementInfos(parts[0], parts[1])["value"]
        return value, False

    def CTNMakeDir(self):
        os.mkdir(self.CTNPath())

    def CTNRequestSave(self, from_project_path=None):
        if self.GetCTRoot().CheckProjectPathPerm(False):
            # If confnode do not have corresponding directory
            ctnpath = self.CTNPath()
            if not os.path.isdir(ctnpath):
                # Create it
                os.mkdir(ctnpath)

            # generate XML for base XML parameters controller of the confnode
            if self.MandatoryParams:
                BaseXMLFile = open(self.ConfNodeBaseXmlFilePath(), 'w')
                BaseXMLFile.write(etree.tostring(
                    self.MandatoryParams[1],
                    pretty_print=True,
                    xml_declaration=True,
                    encoding='utf-8'))
                BaseXMLFile.close()

            # generate XML for XML parameters controller of the confnode
            if self.CTNParams:
                XMLFile = open(self.ConfNodeXmlFilePath(), 'w')
                XMLFile.write(etree.tostring(
                    self.CTNParams[1],
                    pretty_print=True,
                    xml_declaration=True,
                    encoding='utf-8'))
                XMLFile.close()

            # Call the confnode specific OnCTNSave method
            result = self.OnCTNSave(from_project_path)
            if not result:
                return _("Error while saving \"%s\"\n") % self.CTNPath()

            # mark confnode as saved
            self.ChangesToSave = False
            # go through all children and do the same
            for CTNChild in self.IterChildren():
                CTNChildPath = None
                if from_project_path is not None:
                    CTNChildPath = CTNChild.CTNPath(project_path=from_project_path)
                result = CTNChild.CTNRequestSave(CTNChildPath)
                if result:
                    return result
        return None

    def CTNImport(self, src_CTNPath):
        shutil.copytree(src_CTNPath, self.CTNPath)
        return True

    def CTNGlobalInstances(self):
        """
        @return: [(instance_name, instance_type),...]
        """
        return []

    def _GlobalInstances(self):
        instances = self.CTNGlobalInstances()
        for CTNChild in self.IECSortedChildren():
            instances.extend(CTNChild._GlobalInstances())
        return instances

    def CTNGenerate_C(self, buildpath, locations):
        """
        Generate C code
        @param locations: List of complete variables locations \
            [{"IEC_TYPE" : the IEC type (i.e. "INT", "STRING", ...)
            "NAME" : name of the variable (generally "__IW0_1_2" style)
            "DIR" : direction "Q","I" or "M"
            "SIZE" : size "X", "B", "W", "D", "L"
            "LOC" : tuple of interger for IEC location (0,1,2,...)
            }, ...]
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """
        self.GetCTRoot().logger.write_warning(".".join(map(str, self.GetCurrentLocation())) + " -> Nothing to do\n")
        return [], "", False

    def _Generate_C(self, buildpath, locations):
        # Generate confnodes [(Cfiles, CFLAGS)], LDFLAGS, DoCalls, extra_files
        # extra_files = [(fname,fobject), ...]
        gen_result = self.CTNGenerate_C(buildpath, locations)
        CTNCFilesAndCFLAGS, CTNLDFLAGS, DoCalls = gen_result[:3]
        extra_files = gen_result[3:]
        # if some files have been generated put them in the list with their location
        if CTNCFilesAndCFLAGS:
            LocationCFilesAndCFLAGS = [(self.GetCurrentLocation(), CTNCFilesAndCFLAGS, DoCalls)]
        else:
            LocationCFilesAndCFLAGS = []

        # confnode asks for some LDFLAGS
        LDFLAGS = []
        if CTNLDFLAGS is not None:
            # LDFLAGS can be either string
            if isinstance(CTNLDFLAGS, (str, text)):
                LDFLAGS += [CTNLDFLAGS]
            # or list of strings
            elif isinstance(CTNLDFLAGS, list):
                LDFLAGS += CTNLDFLAGS

        # recurse through all children, and stack their results
        for CTNChild in self.IECSortedChildren():
            new_location = CTNChild.GetCurrentLocation()
            # How deep are we in the tree ?
            depth = len(new_location)
            _LocationCFilesAndCFLAGS, _LDFLAGS, _extra_files = \
                CTNChild._Generate_C(
                    # keep the same path
                    buildpath,
                    # filter locations that start with current IEC location
                    [loc for loc in locations if loc["LOC"][0:depth] == new_location])
            # stack the result
            LocationCFilesAndCFLAGS += _LocationCFilesAndCFLAGS
            LDFLAGS += _LDFLAGS
            extra_files += _extra_files

        return LocationCFilesAndCFLAGS, LDFLAGS, extra_files

    def IterChildren(self):
        for _CTNType, Children in self.Children.items():
            for CTNInstance in Children:
                yield CTNInstance

    def IECSortedChildren(self):
        # reorder children by IEC_channels
        ordered = [(chld.BaseParams.getIEC_Channel(), chld) for chld in self.IterChildren()]
        if ordered:
            ordered.sort()
            return zip(*ordered)[1]
        else:
            return []

    def _GetChildBySomething(self, something, toks):
        for CTNInstance in self.IterChildren():
            # if match component of the name
            if getattr(CTNInstance.BaseParams, something) == toks[0]:
                # if Name have other components
                if len(toks) >= 2:
                    # Recurse in order to find the latest object
                    return CTNInstance._GetChildBySomething(something, toks[1:])
                # No sub name -> found
                return CTNInstance
        # Not found
        return None

    def GetChildByName(self, Name):
        if Name:
            toks = Name.split('.')
            return self._GetChildBySomething("Name", toks)
        else:
            return self

    def GetChildByIECLocation(self, Location):
        if Location:
            return self._GetChildBySomething("IEC_Channel", Location)
        else:
            return self

    def GetCurrentLocation(self):
        """
        @return:  Tupple containing confnode IEC location of current confnode : %I0.0.4.5 => (0,0,4,5)
        """
        return self.CTNParent.GetCurrentLocation() + (self.BaseParams.getIEC_Channel(),)

    def GetCurrentName(self):
        """
        @return:  String "ParentParentName.ParentName.Name"
        """
        return self.CTNParent._GetCurrentName() + self.BaseParams.getName()

    def _GetCurrentName(self):
        """
        @return:  String "ParentParentName.ParentName.Name."
        """
        return self.CTNParent._GetCurrentName() + self.BaseParams.getName() + "."

    def GetCTRoot(self):
        return self.CTNParent.GetCTRoot()

    def GetFullIEC_Channel(self):
        return ".".join([str(i) for i in self.GetCurrentLocation()]) + ".x"

    def GetLocations(self):
        location = self.GetCurrentLocation()
        return [loc for loc in self.CTNParent.GetLocations() if loc["LOC"][0:len(location)] == location]

    def GetVariableLocationTree(self):
        '''
        This function is meant to be overridden by confnodes.

        It should returns an list of dictionaries

        - IEC_type is an IEC type like BOOL/BYTE/SINT/...
        - location is a string of this variable's location, like "%IX0.0.0"
        '''
        children = []
        for child in self.IECSortedChildren():
            children.append(child.GetVariableLocationTree())
        return {"name": self.BaseParams.getName(),
                "type": LOCATION_CONFNODE,
                "location": self.GetFullIEC_Channel(),
                "children": children}

    def FindNewName(self, DesiredName):
        """
        Changes Name to DesiredName if available, Name-N if not.
        @param DesiredName: The desired Name (string)
        """

        # Build a list of used Name out of parent's Children
        AllNames = []
        for CTNInstance in self.CTNParent.IterChildren():
            if CTNInstance != self:
                AllNames.append(CTNInstance.BaseParams.getName())

        # Find a free name, eventually appending digit
        res = DesiredName
        if DesiredName.endswith("_0"):
            BaseDesiredName = DesiredName[:-2]
        else:
            BaseDesiredName = DesiredName
        suffix = 1
        while res in AllNames:
            res = "%s_%d" % (BaseDesiredName, suffix)
            suffix += 1

        # Check previous confnode existance
        dontexist = self.BaseParams.getName() == "__unnamed__"
        if not dontexist:
            # Get old path
            oldpath = self.CTNPath()
        # Set the new name
        self.BaseParams.setName(res)
        # Rename confnode dir if exist
        if not dontexist:
            shutil.move(oldpath, self.CTNPath())
        # warn user he has two left hands
        if DesiredName != res:
            msg = _("A child named \"{a1}\" already exists -> \"{a2}\"\n").format(a1=DesiredName, a2=res)
            self.GetCTRoot().logger.write_warning(msg)
        return res

    def GetAllChannels(self):
        AllChannels = []
        for CTNInstance in self.CTNParent.IterChildren():
            if CTNInstance != self:
                AllChannels.append(CTNInstance.BaseParams.getIEC_Channel())
        AllChannels.sort()
        return AllChannels

    def FindNewIEC_Channel(self, DesiredChannel):
        """
        Changes IEC Channel number to DesiredChannel if available, nearest available if not.
        @param DesiredChannel: The desired IEC channel (int)
        """
        # Get Current IEC channel
        CurrentChannel = self.BaseParams.getIEC_Channel()
        # Do nothing if no change
        # if CurrentChannel == DesiredChannel: return CurrentChannel
        # Build a list of used Channels out of parent's Children
        AllChannels = self.GetAllChannels()

        # Now, try to guess the nearest available channel
        res = DesiredChannel
        while res in AllChannels:  # While channel not free
            if res < CurrentChannel:  # Want to go down ?
                res -= 1  # Test for n-1
                if res < 0:
                    self.GetCTRoot().logger.write_warning(_("Cannot find lower free IEC channel than %d\n") % CurrentChannel)
                    return CurrentChannel  # Can't go bellow 0, do nothing
            else:  # Want to go up ?
                res += 1  # Test for n-1
        # Finally set IEC Channel
        self.BaseParams.setIEC_Channel(res)
        return res

    def GetContextualMenuItems(self):
        return None

    def GetView(self):
        if self._View is None and self.EditorType is not None:
            app_frame = self.GetCTRoot().AppFrame
            self._View = self.EditorType(app_frame.TabsOpened, self, app_frame)

        return self._View

    def _OpenView(self, name=None, onlyopened=False):
        view = self.GetView()

        if view is not None:
            if name is None:
                name = self.CTNFullName()
            app_frame = self.GetCTRoot().AppFrame
            app_frame.EditProjectElement(view, name)

        return view

    def _CloseView(self, view):
        app_frame = self.GetCTRoot().AppFrame
        if app_frame is not None:
            app_frame.DeletePage(view)

    def OnCloseEditor(self, view):
        if self._View == view:
            self._View = None

    def OnCTNClose(self):
        if self._View is not None:
            self._CloseView(self._View)
            self._View = None
        return True

    def _doRemoveChild(self, CTNInstance):
        # Remove all children of child
        for SubCTNInstance in CTNInstance.IterChildren():
            CTNInstance._doRemoveChild(SubCTNInstance)
        # Call the OnCloseMethod
        CTNInstance.OnCTNClose()
        # Delete confnode dir
        try:
            shutil.rmtree(CTNInstance.CTNPath())
        except Exception:
            pass
        # Remove child of Children
        self.Children[CTNInstance.CTNType].remove(CTNInstance)
        if len(self.Children[CTNInstance.CTNType]) == 0:
            self.Children.pop(CTNInstance.CTNType)
        # Forget it... (View have to refresh)

    def CTNRemove(self):
        # Fetch the confnode
        # CTNInstance = self.GetChildByName(CTNName)
        # Ask to his parent to remove it
        self.CTNParent._doRemoveChild(self)

    def CTNAddChild(self, CTNName, CTNType, IEC_Channel=0):
        """
        Create the confnodes that may be added as child to this node self
        @param CTNType: string desining the confnode class name (get name from CTNChildrenTypes)
        @param CTNName: string for the name of the confnode instance
        """
        # reorganize self.CTNChildrenTypes tuples from (name, CTNClass, Help)
        # to ( name, (CTNClass, Help)), an make a dict
        transpose = zip(*self.CTNChildrenTypes)
        CTNChildrenTypes = dict(zip(transpose[0], zip(transpose[1], transpose[2])))
        # Check that adding this confnode is allowed
        try:
            CTNClass, CTNHelp = CTNChildrenTypes[CTNType]
        except KeyError:
            raise Exception(_("Cannot create child {a1} of type {a2} ").
                            format(a1=CTNName, a2=CTNType))

        # if CTNClass is a class factory, call it. (prevent unneeded imports)
        if isinstance(CTNClass, types.FunctionType):
            CTNClass = CTNClass()

        # Eventualy Initialize child instance list for this class of confnode
        ChildrenWithSameClass = self.Children.setdefault(CTNType, list())
        # Check count
        if getattr(CTNClass, "CTNMaxCount", None) and len(ChildrenWithSameClass) >= CTNClass.CTNMaxCount:
            raise Exception(
                _("Max count ({a1}) reached for this confnode of type {a2} ").
                format(a1=CTNClass.CTNMaxCount, a2=CTNType))

        # create the final class, derived of provided confnode and template
        class FinalCTNClass(CTNClass, ConfigTreeNode):
            """
            ConfNode class is derivated into FinalCTNClass before being instanciated
            This way __init__ is overloaded to ensure ConfigTreeNode.__init__ is called
            before CTNClass.__init__, and to do the file related stuff.
            """
            def __init__(self, parent):
                self.CTNParent = parent
                # Keep track of the confnode type name
                self.CTNType = CTNType
                # remind the help string, for more fancy display
                self.CTNHelp = CTNHelp
                # Call the base confnode template init - change XSD into class members
                ConfigTreeNode.__init__(self)
                # check name is unique
                NewCTNName = self.FindNewName(CTNName)
                # If dir have already be made, and file exist
                if os.path.isdir(self.CTNPath(NewCTNName)):  # and os.path.isfile(self.ConfNodeXmlFilePath(CTNName)):
                    # Load the confnode.xml file into parameters members
                    self.LoadXMLParams(NewCTNName)
                    # Basic check. Better to fail immediately.
                    if self.BaseParams.getName() != NewCTNName:
                        raise Exception(
                            _("Project tree layout do not match confnode.xml {a1}!={a2} ").
                            format(a1=NewCTNName, a2=self.BaseParams.getName()))

                    # Now, self.CTNPath() should be OK

                    # Check that IEC_Channel is not already in use.
                    self.FindNewIEC_Channel(self.BaseParams.getIEC_Channel())
                    # Call the confnode real __init__
                    if getattr(CTNClass, "__init__", None):
                        CTNClass.__init__(self)
                    # Load and init all the children
                    self.LoadChildren()
                    # just loaded, nothing to saved
                    self.ChangesToSave = False
                else:
                    # If confnode do not have corresponding file/dirs - they will be created on Save
                    self.CTNMakeDir()
                    # Find an IEC number
                    self.FindNewIEC_Channel(IEC_Channel)
                    # Call the confnode real __init__
                    if getattr(CTNClass, "__init__", None):
                        CTNClass.__init__(self)
                    self.CTNRequestSave()
                    # just created, must be saved
                    self.ChangesToSave = True

            def _getBuildPath(self):
                return self.CTNParent._getBuildPath()

        # Create the object out of the resulting class
        newConfNodeOpj = FinalCTNClass(self)
        # Store it in CTNgedChils
        ChildrenWithSameClass.append(newConfNodeOpj)

        return newConfNodeOpj

    def ClearChildren(self):
        for child in self.IterChildren():
            child.ClearChildren()
        self.Children = {}

    def LoadXMLParams(self, CTNName=None):
        methode_name = os.path.join(self.CTNPath(CTNName), "methods.py")
        if os.path.isfile(methode_name):
            execfile(methode_name)

        ConfNodeName = CTNName if CTNName is not None else self.CTNName()

        # Get the base xml tree
        if self.MandatoryParams:
            try:
                basexmlfile = open(self.ConfNodeBaseXmlFilePath(CTNName), 'r')
                self.BaseParams, error = _BaseParamsParser.LoadXMLString(basexmlfile.read())
                if error is not None:
                    (fname, lnum, src) = ((ConfNodeName + " BaseParams",) + error)
                    self.GetCTRoot().logger.write_warning(XSDSchemaErrorMessage.format(a1=fname, a2=lnum, a3=src))
                self.MandatoryParams = ("BaseParams", self.BaseParams)
                basexmlfile.close()
            except Exception as exc:
                msg = _("Couldn't load confnode base parameters {a1} :\n {a2}").format(a1=ConfNodeName, a2=text(exc))
                self.GetCTRoot().logger.write_error(msg)
                self.GetCTRoot().logger.write_error(traceback.format_exc())

        # Get the xml tree
        if self.CTNParams:
            try:
                xmlfile = open(self.ConfNodeXmlFilePath(CTNName), 'r')
                obj, error = self.Parser.LoadXMLString(xmlfile.read())
                if error is not None:
                    (fname, lnum, src) = ((ConfNodeName,) + error)
                    self.GetCTRoot().logger.write_warning(XSDSchemaErrorMessage.format(a1=fname, a2=lnum, a3=src))
                name = obj.getLocalTag()
                setattr(self, name, obj)
                self.CTNParams = (name, obj)
                xmlfile.close()
            except Exception as exc:
                msg = _("Couldn't load confnode parameters {a1} :\n {a2}").format(a1=ConfNodeName, a2=text(exc))
                self.GetCTRoot().logger.write_error(msg)
                self.GetCTRoot().logger.write_error(traceback.format_exc())

    def LoadChildren(self):
        # Iterate over all CTNName@CTNType in confnode directory, and try to open them
        for CTNDir in os.listdir(self.CTNPath()):
            if os.path.isdir(os.path.join(self.CTNPath(), CTNDir)) and \
               CTNDir.count(NameTypeSeparator) == 1:
                pname, ptype = CTNDir.split(NameTypeSeparator)
                try:
                    self.CTNAddChild(pname, ptype)
                except Exception as exc:
                    msg = _("Could not add child \"{a1}\", type {a2} :\n{a3}\n").format(a1=pname, a2=ptype, a3=text(exc))
                    self.GetCTRoot().logger.write_error(msg)
                    self.GetCTRoot().logger.write_error(traceback.format_exc())
