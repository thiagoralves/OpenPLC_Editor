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

"""
Beremiz Project Controller
"""


from __future__ import absolute_import
import os
import traceback
import time
from time import localtime
import shutil
import re
import tempfile
from threading import Timer
from datetime import datetime
from weakref import WeakKeyDictionary
from functools import reduce
from distutils.dir_util import copy_tree
from six.moves import xrange

import wx

import features
import connectors
import util.paths as paths
from util.misc import CheckPathPerm, GetClassImporter
from util.MiniTextControler import MiniTextControler
from util.ProcessLogger import ProcessLogger
from util.BitmapLibrary import GetBitmap
from editors.FileManagementPanel import FileManagementPanel
from editors.ProjectNodeEditor import ProjectNodeEditor
from editors.IECCodeViewer import IECCodeViewer
from editors.DebugViewer import DebugViewer, REFRESH_PERIOD
from dialogs import UriEditor, IDManager
from PLCControler import PLCControler
from plcopen.structures import IEC_KEYWORDS
from plcopen.types_enums import ComputeConfigurationResourceName, ITEM_CONFNODE
import targets
from runtime.typemapping import DebugTypesSize, UnpackDebugBuffer
from runtime import PlcStatus
from ConfigTreeNode import ConfigTreeNode, XSDSchemaErrorMessage

base_folder = paths.AbsParentDir(__file__)

MATIEC_ERROR_MODEL = re.compile(
    r".*\.st:(\d+)-(\d+)\.\.(\d+)-(\d+): (?:error)|(?:warning) : (.*)$")


def ExtractChildrenTypesFromCatalog(catalog):
    children_types = []
    for n, d, _h, c in catalog:
        if isinstance(c, list):
            children_types.extend(ExtractChildrenTypesFromCatalog(c))
        else:
            children_types.append((n, GetClassImporter(c), d))
    return children_types


def ExtractMenuItemsFromCatalog(catalog):
    menu_items = []
    for n, d, h, c in catalog:
        if isinstance(c, list):
            children = ExtractMenuItemsFromCatalog(c)
        else:
            children = []
        menu_items.append((n, d, h, children))
    return menu_items


def GetAddMenuItems():
    return ExtractMenuItemsFromCatalog(features.catalog)


class Iec2CSettings(object):

    def __init__(self):
        self.iec2c = None
        self.iec2c_buildopts = None
        self.ieclib_path = self.findLibPath()
        self.ieclib_c_path = self.findLibCPath()

    def findObject(self, paths, test):
        path = None
        for p in paths:
            if test(p):
                path = p
                break
        return path

    def findCmd(self):
        cmd = "iec2c" + (".exe" if wx.Platform == '__WXMSW__' else "")
        paths = [
            os.path.join(base_folder, "matiec")
        ]
        path = self.findObject(
            paths, lambda p: os.path.isfile(os.path.join(p, cmd)))

        # otherwise use iec2c from PATH
        if path is not None:
            cmd = os.path.join(path, cmd)

        return cmd

    def findLibPath(self):
        paths = [
            os.path.join(base_folder, "matiec", "lib"),
            "/usr/lib/matiec"
        ]
        path = self.findObject(
            paths, lambda p: os.path.isfile(os.path.join(p, "ieclib.txt")))
        return path

    def findLibCPath(self):
        path = None
        if self.ieclib_path is not None:
            paths = [
                os.path.join(self.ieclib_path, "C"),
                self.ieclib_path]
            path = self.findObject(
                paths,
                lambda p: os.path.isfile(os.path.join(p, "iec_types.h")))
        return path

    def findSupportedOptions(self):
        buildcmd = "\"%s\" -h" % (self.getCmd())
        options = ["-f", "-l", "-p"]

        buildopt = ""
        try:
            # Invoke compiler.
            # Output files are listed to stdout, errors to stderr
            _status, result, _err_result = ProcessLogger(None, buildcmd,
                                                         no_stdout=True,
                                                         no_stderr=True).spin()
        except Exception:
            return buildopt

        for opt in options:
            if opt in result:
                buildopt = buildopt + " " + opt
        return buildopt

    def getCmd(self):
        if self.iec2c is None:
            self.iec2c = self.findCmd()
        return self.iec2c

    def getOptions(self):
        if self.iec2c_buildopts is None:
            self.iec2c_buildopts = self.findSupportedOptions()
        return self.iec2c_buildopts

    def getLibPath(self):
        return self.ieclib_path

    def getLibCPath(self):
        if self.ieclib_c_path is None:
            self.ieclib_c_path = self.findLibCPath()
        return self.ieclib_c_path


def GetProjectControllerXSD():
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="BeremizRoot">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="TargetType">
              <xsd:complexType>
                <xsd:choice minOccurs="0">
                """ + targets.GetTargetChoices() + """
                </xsd:choice>
              </xsd:complexType>
            </xsd:element>""" + (("""
            <xsd:element name="Libraries" minOccurs="0">
              <xsd:complexType>
              """ + "\n".join(['<xsd:attribute name=' +
                               '"Enable_' + libname + '_Library" ' +
                               'type="xsd:boolean" use="optional" default="' +
                               ('true' if default else 'false') + '"/>'
                               for libname, _lib, default in features.libraries]) + """
              </xsd:complexType>
            </xsd:element>""") if len(features.libraries) > 0 else '') + """
          </xsd:sequence>
          <xsd:attribute name="URI_location" type="xsd:string" use="optional" default=""/>
          <xsd:attribute name="Disable_Extensions" type="xsd:boolean" use="optional" default="false"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """
    return XSD


class ProjectController(ConfigTreeNode, PLCControler):

    """
    This class define Root object of the confnode tree.
    It is responsible of :
    - Managing project directory
    - Building project
    - Handling PLCOpenEditor controler and view
    - Loading user confnodes and instanciante them as children
    - ...

    """
    # For root object, available Children Types are modules of the confnode
    # packages.
    CTNChildrenTypes = ExtractChildrenTypesFromCatalog(features.catalog)
    XSD = GetProjectControllerXSD()
    EditorType = ProjectNodeEditor
    iec2c_cfg = None

    def __init__(self, frame, logger):
        PLCControler.__init__(self)
        ConfigTreeNode.__init__(self)

        if ProjectController.iec2c_cfg is None:
            ProjectController.iec2c_cfg = Iec2CSettings()

        self.MandatoryParams = None
        self._builder = None
        self._connector = None
        self.DispatchDebugValuesTimer = None
        self.DebugValuesBuffers = []
        self.DebugTicks = []
        self.SetAppFrame(frame, logger)

        # Setup debug information
        self.IECdebug_datas = {}

        self.DebugTimer = None
        self.ResetIECProgramsAndVariables()

        # In both new or load scenario, no need to save
        self.ChangesToSave = False
        # root have no parent
        self.CTNParent = None
        # Keep track of the confnode type name
        self.CTNType = "Beremiz"
        self.Children = {}
        self._View = None
        # After __init__ root confnode is not valid
        self.ProjectPath = None
        self._setBuildPath(None)
        self.debug_break = False
        self.previous_plcstate = None
        # copy StatusMethods so that it can be later customized
        self.StatusMethods = [dic.copy() for dic in self.StatusMethods]
        self.DebugToken = None
        self.debug_status = PlcStatus.Stopped

    def __del__(self):
        if self.DebugTimer:
            self.DebugTimer.cancel()
        self.KillDebugThread()

    def LoadLibraries(self):
        self.Libraries = []
        TypeStack = []
        for libname, clsname, lib_enabled in features.libraries:
            if self.BeremizRoot.Libraries is not None:
                enable_attr = getattr(self.BeremizRoot.Libraries,
                                      "Enable_" + libname + "_Library")
                if enable_attr is not None:
                    lib_enabled = enable_attr

            if lib_enabled:
                Lib = GetClassImporter(clsname)()(self, libname, TypeStack)
                TypeStack.append(Lib.GetTypes())
                self.Libraries.append(Lib)

    def SetAppFrame(self, frame, logger):
        self.AppFrame = frame
        self.logger = logger
        self.StatusTimer = None
        if self.DispatchDebugValuesTimer is not None:
            self.DispatchDebugValuesTimer.Stop()
        self.DispatchDebugValuesTimer = None

        if frame is not None:

            # Timer to pull PLC status
            self.StatusTimer = wx.Timer(self.AppFrame, -1)
            self.AppFrame.Bind(wx.EVT_TIMER,
                               self.PullPLCStatusProc,
                               self.StatusTimer)

            if self._connector is not None:
                frame.LogViewer.SetLogSource(self._connector)
                self.StatusTimer.Start(milliseconds=500, oneShot=False)

            # Timer to dispatch debug values to consumers
            self.DispatchDebugValuesTimer = wx.Timer(self.AppFrame, -1)
            self.AppFrame.Bind(wx.EVT_TIMER,
                               self.DispatchDebugValuesProc,
                               self.DispatchDebugValuesTimer)

            self.RefreshConfNodesBlockLists()

    def ResetAppFrame(self, logger):
        if self.AppFrame is not None:
            self.AppFrame.Unbind(wx.EVT_TIMER, self.StatusTimer)
            self.StatusTimer = None
            self.AppFrame = None
            self.KillDebugThread()
        self.logger = logger

    def CTNName(self):
        return "Project"

    def CTNTestModified(self):
        return self.ChangesToSave or not self.ProjectIsSaved()

    def CTNFullName(self):
        return ""

    def GetCTRoot(self):
        return self

    def GetIECLibPath(self):
        return self.iec2c_cfg.getLibCPath()

    def GetIEC2cPath(self):
        return self.iec2c_cfg.getCmd()

    def GetCurrentLocation(self):
        return ()

    def GetCurrentName(self):
        return ""

    def _GetCurrentName(self):
        return ""

    def GetProjectPath(self):
        return self.ProjectPath

    def GetProjectName(self):
        return os.path.split(self.ProjectPath)[1]

    def GetIconName(self):
        return "PROJECT"

    def GetDefaultTargetName(self):
        if wx.Platform == '__WXMSW__':
            return "Win32"
        else:
            return "Linux"

    def GetTarget(self):
        target = self.BeremizRoot.getTargetType()
        if target.getcontent() is None:
            temp_root = self.Parser.CreateRoot()
            target = self.Parser.CreateElement("TargetType", "BeremizRoot")
            temp_root.setTargetType(target)
            target_name = self.GetDefaultTargetName()
            target.setcontent(
                self.Parser.CreateElement(target_name, "TargetType"))
        return target

    def GetParamsAttributes(self, path=None):
        params = ConfigTreeNode.GetParamsAttributes(self, path)
        if params[0]["name"] == "BeremizRoot":
            for child in params[0]["children"]:
                if child["name"] == "TargetType" and child["value"] == '':
                    child.update(
                        self.GetTarget().getElementInfos("TargetType"))
        return params

    def SetParamsAttribute(self, path, value):
        if path.startswith("BeremizRoot.TargetType.") and self.BeremizRoot.getTargetType().getcontent() is None:
            self.BeremizRoot.setTargetType(self.GetTarget())
        res = ConfigTreeNode.SetParamsAttribute(self, path, value)
        if path.startswith("BeremizRoot.Libraries."):
            wx.CallAfter(self.RefreshConfNodesBlockLists)
        return res

    # helper func to check project path write permission
    def CheckProjectPathPerm(self, dosave=True):
        if CheckPathPerm(self.ProjectPath):
            return True
        if self.AppFrame is not None:
            dialog = wx.MessageDialog(
                self.AppFrame,
                _('You must have permission to work on the project\nWork on a project copy ?'),
                _('Error'),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            answer = dialog.ShowModal()
            dialog.Destroy()
            if answer == wx.ID_YES:
                if self.SaveProjectAs():
                    self.AppFrame.RefreshTitle()
                    self.AppFrame.RefreshFileMenu()
                    self.AppFrame.RefreshPageTitles()
                    return True
        return False

    def _getProjectFilesPath(self, project_path=None):
        if project_path is not None:
            return os.path.join(project_path, "project_files")
        projectfiles_path = os.path.join(
            self.GetProjectPath(), "project_files")
        if not os.path.exists(projectfiles_path):
            os.mkdir(projectfiles_path)
        return projectfiles_path

    def AddProjectDefaultConfiguration(self, config_name="Config0", res_name="Res0"):
        self.ProjectAddConfiguration(config_name)
        self.ProjectAddConfigurationResource(config_name, res_name)

    def SetProjectDefaultConfiguration(self):
        # Sets default task and instance for new project
        config = self.Project.getconfiguration(
            self.GetProjectMainConfigurationName())
        resource = config.getresource()[0].getname()
        config = config.getname()
        resource_tagname = ComputeConfigurationResourceName(config, resource)
        def_task = [
            {'Priority': '0', 'Single': '', 'Interval': 'T#20ms', 'Name': 'task0', 'Triggering': 'Cyclic'}]
        def_instance = [
            {'Task': def_task[0].get('Name'), 'Type': self.GetProjectPouNames()[0], 'Name': 'instance0'}]
        self.SetEditedResourceInfos(resource_tagname, def_task, def_instance)

    def NewProject(self, ProjectPath, BuildPath=None):
        """
        Create a new project in an empty folder
        @param ProjectPath: path of the folder where project have to be created
        @param PLCParams: properties of the PLCOpen program created
        """
        # Verify that chosen folder is empty
        if not os.path.isdir(ProjectPath) or len(os.listdir(ProjectPath)) > 0:
            return _("Chosen folder isn't empty. You can't use it for a new project!")

        # Create PLCOpen program
        self.CreateNewProject(
            {"projectName": _("Unnamed"),
             "productName": _("Unnamed"),
             "productVersion": "1",
             "companyName": _("Unknown"),
             "creationDateTime": datetime(*localtime()[:6])})
        self.AddProjectDefaultConfiguration()

        # Change XSD into class members
        self._AddParamsMembers()
        self.Children = {}
        # Keep track of the root confnode (i.e. project path)
        self.ProjectPath = ProjectPath
        self._setBuildPath(BuildPath)
        # get confnodes bloclist (is that usefull at project creation?)
        self.RefreshConfNodesBlockLists()
        # set default scaling properties
        PLCControler.SetProjectProperties(self, properties={"scaling": {'FBD': (10, 10)}})
        PLCControler.SetProjectProperties(self, properties={"scaling": {'LD': (10, 10)}})
        PLCControler.SetProjectProperties(self, properties={"scaling": {'SFC': (10, 10)}})
        # this will create files base XML files
        self.SaveProject()
        return None

    def LoadProject(self, ProjectPath, BuildPath=None):
        """
        Load a project contained in a folder
        @param ProjectPath: path of the project folder
        """
        if os.path.basename(ProjectPath) == "":
            ProjectPath = os.path.dirname(ProjectPath)
        # Verify that project contains a PLCOpen program
        plc_file = os.path.join(ProjectPath, "plc.xml")
        if not os.path.isfile(plc_file):
            return _("Chosen folder doesn't contain a program. It's not a valid project!"), True
        # Load PLCOpen file
        error = self.OpenXMLFile(plc_file)
        if error is not None:
            if self.Project is not None:
                (fname_err, lnum, src) = (("PLC",) + error)
                self.logger.write_warning(
                    XSDSchemaErrorMessage.format(a1=fname_err, a2=lnum, a3=src))
            else:
                return error, False
        if len(self.GetProjectConfigNames()) == 0:
            self.AddProjectDefaultConfiguration()
        # Change XSD into class members
        self._AddParamsMembers()
        self.Children = {}
        # Keep track of the root confnode (i.e. project path)
        self.ProjectPath = ProjectPath
        self._setBuildPath(BuildPath)
        # If dir have already be made, and file exist
        if os.path.isdir(self.CTNPath()) and os.path.isfile(self.ConfNodeXmlFilePath()):
            # Load the confnode.xml file into parameters members
            result = self.LoadXMLParams()
            if result:
                return result, False
            # Load and init all the children
            self.LoadChildren()
        self.RefreshConfNodesBlockLists()
        self.UpdateButtons()
        return None, False

    def RecursiveConfNodeInfos(self, confnode):
        values = []
        for CTNChild in confnode.IECSortedChildren():
            values.append(
                {"name": "%s: %s" % (CTNChild.GetFullIEC_Channel(),
                                     CTNChild.CTNName()),
                 "tagname": CTNChild.CTNFullName(),
                 "type": ITEM_CONFNODE,
                 "confnode": CTNChild,
                 "icon": CTNChild.GetIconName(),
                 "values": self.RecursiveConfNodeInfos(CTNChild)})
        return values

    def GetProjectInfos(self):
        infos = PLCControler.GetProjectInfos(self)
        configurations = infos["values"].pop(-1)
        resources = None
        for config_infos in configurations["values"]:
            if resources is None:
                resources = config_infos["values"][0]
            else:
                resources["values"].extend(config_infos["values"][0]["values"])
        if resources is not None:
            infos["values"].append(resources)
        infos["values"].extend(self.RecursiveConfNodeInfos(self))
        return infos

    def CloseProject(self):
        self.ClearChildren()
        self.ResetAppFrame(None)

    def CheckNewProjectPath(self, old_project_path, new_project_path):
        if old_project_path == new_project_path:
            message = (_("Save path is the same as path of a project! \n"))
            dialog = wx.MessageDialog(
                self.AppFrame, message, _("Error"), wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            return False
        else:
            if not CheckPathPerm(new_project_path):
                dialog = wx.MessageDialog(
                    self.AppFrame,
                    _('No write permissions in selected directory! \n'),
                    _("Error"), wx.OK | wx.ICON_ERROR)
                dialog.ShowModal()
                return False
            if not os.path.isdir(new_project_path) or len(os.listdir(new_project_path)) > 0:
                plc_file = os.path.join(new_project_path, "plc.xml")
                if os.path.isfile(plc_file):
                    message = _("Selected directory already contains another project. Overwrite? \n")
                else:
                    message = _("Selected directory isn't empty. Continue? \n")
                dialog = wx.MessageDialog(
                    self.AppFrame, message, _("Error"), wx.YES_NO | wx.ICON_ERROR)
                answer = dialog.ShowModal()
                return answer == wx.ID_YES
        return True

    def SaveProject(self, from_project_path=None):
        if self.CheckProjectPathPerm(False):
            if from_project_path is not None:
                old_projectfiles_path = self._getProjectFilesPath(
                    from_project_path)
                if os.path.isdir(old_projectfiles_path):
                    copy_tree(old_projectfiles_path,
                              self._getProjectFilesPath(self.ProjectPath))
            self.SaveXMLFile(os.path.join(self.ProjectPath, 'plc.xml'))
            result = self.CTNRequestSave(from_project_path)
            if result:
                self.logger.write_error(result)

    def SaveProjectAs(self):
        # Ask user to choose a path with write permissions
        if wx.Platform == '__WXMSW__':
            path = os.getenv("USERPROFILE")
        else:
            path = os.getenv("HOME")
        dirdialog = wx.DirDialog(
            self.AppFrame, _("Choose a directory to save project"), path, wx.DD_NEW_DIR_BUTTON)
        answer = dirdialog.ShowModal()
        dirdialog.Destroy()
        if answer == wx.ID_OK:
            newprojectpath = dirdialog.GetPath()
            if os.path.isdir(newprojectpath):
                if self.CheckNewProjectPath(self.ProjectPath, newprojectpath):
                    self.ProjectPath, old_project_path = newprojectpath, self.ProjectPath
                    self.SaveProject(old_project_path)
                    self._setBuildPath(self.BuildPath)
                return True
        return False

    def GetLibrariesTypes(self):
        self.LoadLibraries()
        return [lib.GetTypes() for lib in self.Libraries]

    def GetLibrariesSTCode(self):
        return "\n".join([lib.GetSTCode() for lib in self.Libraries])

    def GetLibrariesCCode(self, buildpath):
        if len(self.Libraries) == 0:
            return [], [], ()
        self.GetIECProgramsAndVariables()
        LibIECCflags = '"-I%s" -Wno-unused-function' % os.path.abspath(
            self.GetIECLibPath())
        LocatedCCodeAndFlags = []
        Extras = []
        for lib in self.Libraries:
            res = lib.Generate_C(buildpath, self._VariablesList, LibIECCflags)
            LocatedCCodeAndFlags.append(res[:2])
            if len(res) > 2:
                Extras.extend(res[2:])
        return map(list, zip(*LocatedCCodeAndFlags)) + [tuple(Extras)]

    # Update PLCOpenEditor ConfNode Block types from loaded confnodes
    def RefreshConfNodesBlockLists(self):
        if getattr(self, "Children", None) is not None:
            self.ClearConfNodeTypes()
            self.AddConfNodeTypesList(self.GetLibrariesTypes())
        if self.AppFrame is not None:
            self.AppFrame.RefreshLibraryPanel()
            self.AppFrame.RefreshEditor()

    # Update a PLCOpenEditor Pou variable location
    def UpdateProjectVariableLocation(self, old_leading, new_leading):
        self.Project.updateElementAddress(old_leading, new_leading)
        self.BufferProject()
        if self.AppFrame is not None:
            self.AppFrame.RefreshTitle()
            self.AppFrame.RefreshPouInstanceVariablesPanel()
            self.AppFrame.RefreshFileMenu()
            self.AppFrame.RefreshEditMenu()
            wx.CallAfter(self.AppFrame.RefreshEditor)

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
        return children

    def ConfNodePath(self):
        return paths.AbsDir(__file__)

    def CTNPath(self, CTNName=None):
        return self.ProjectPath

    def ConfNodeXmlFilePath(self, CTNName=None):
        return os.path.join(self.CTNPath(CTNName), "beremiz.xml")

    def ParentsTypesFactory(self):
        return self.ConfNodeTypesFactory()

    def _setBuildPath(self, buildpath):
        self.BuildPath = buildpath
        self.DefaultBuildPath = None
        if self._builder is not None:
            self._builder.SetBuildPath(self._getBuildPath())

    def _getBuildPath(self):
        # BuildPath is defined by user
        if self.BuildPath is not None:
            return self.BuildPath
        # BuildPath isn't defined by user but already created by default
        if self.DefaultBuildPath is not None:
            return self.DefaultBuildPath
        # Create a build path in project folder if user has permissions
        if CheckPathPerm(self.ProjectPath):
            self.DefaultBuildPath = os.path.join(self.ProjectPath, "build")
        # Create a build path in temp folder
        else:
            self.DefaultBuildPath = os.path.join(
                tempfile.mkdtemp(), os.path.basename(self.ProjectPath), "build")

        if not os.path.exists(self.DefaultBuildPath):
            os.makedirs(self.DefaultBuildPath)
        return self.DefaultBuildPath

    def _getExtraFilesPath(self):
        return os.path.join(self._getBuildPath(), "extra_files")

    def _getIECcodepath(self):
        # define name for IEC code file
        return os.path.join(self._getBuildPath(), "plc.st")

    def _getIECgeneratedcodepath(self):
        # define name for IEC generated code file
        return os.path.join(self._getBuildPath(), "generated_plc.st")

    def _getIECrawcodepath(self):
        # define name for IEC raw code file
        return os.path.join(self.CTNPath(), "raw_plc.st")

    def GetLocations(self):
        locations = []
        filepath = os.path.join(self._getBuildPath(), "LOCATED_VARIABLES.h")
        if os.path.isfile(filepath):
            # IEC2C compiler generate a list of located variables :
            # LOCATED_VARIABLES.h
            location_file = open(
                os.path.join(self._getBuildPath(), "LOCATED_VARIABLES.h"))
            # each line of LOCATED_VARIABLES.h declares a located variable
            lines = [line.strip() for line in location_file.readlines()]
            # This regular expression parses the lines genereated by IEC2C
            LOCATED_MODEL = re.compile(
                r"__LOCATED_VAR\((?P<IEC_TYPE>[A-Z]*),(?P<NAME>[_A-Za-z0-9]*),(?P<DIR>[QMI])(?:,(?P<SIZE>[XBWDL]))?,(?P<LOC>[,0-9]*)\)")
            for line in lines:
                # If line match RE,
                result = LOCATED_MODEL.match(line)
                if result:
                    # Get the resulting dict
                    resdict = result.groupdict()
                    # rewrite string for variadic location as a tuple of
                    # integers
                    resdict['LOC'] = tuple(map(int, resdict['LOC'].split(',')))
                    # set located size to 'X' if not given
                    if not resdict['SIZE']:
                        resdict['SIZE'] = 'X'
                    # finally store into located variable list
                    locations.append(resdict)
        return locations

    def GetConfNodeGlobalInstances(self):
        return self._GlobalInstances()

    def _Generate_SoftPLC(self):
        if self._Generate_PLC_ST():
            return self._Compile_ST_to_SoftPLC()
        return False

    def RemoveLocatedVariables(self, st_program):
        modified_program = ""
        for line in st_program.splitlines(True):
            if (line.find("AT %") > 0):
                a = line.split("AT %")
                b = a[1].split(":")
                modified_program += a[0] + ":" + b[1]
            else:
                modified_program += line

        return modified_program

    def _Generate_PLC_ST(self):
        """
        Generate SoftPLC ST/IL/SFC code out of PLCOpenEditor controller, and compile it with IEC2C
        @param buildpath: path where files should be created
        """

        # Update PLCOpenEditor ConfNode Block types before generate ST code
        self.RefreshConfNodesBlockLists()

        self.logger.write(
            _("Generating SoftPLC IEC-61131 ST/IL/SFC code...\n"))
        # ask PLCOpenEditor controller to write ST/IL/SFC code file
        _program, errors, warnings = self.GenerateProgram(
            self._getIECgeneratedcodepath())
        if len(warnings) > 0:
            self.logger.write_warning(
                _("Warnings in ST/IL/SFC code generator :\n"))
            for warning in warnings:
                self.logger.write_warning("%s\n" % warning)
        if len(errors) > 0:
            # Failed !
            self.logger.write_error(
                _("Error in ST/IL/SFC code generator :\n%s\n") % errors[0])
            return False
        plc_file = open(self._getIECcodepath(), "w")
        # Add ST Library from confnodes
        plc_file.write(self.GetLibrariesSTCode())
        if os.path.isfile(self._getIECrawcodepath()):
            plc_file.write(open(self._getIECrawcodepath(), "r").read())
            plc_file.write("\n")
        plc_file.close()
        plc_file = open(self._getIECcodepath(), "r")
        self.ProgramOffset = 0
        for dummy in plc_file.readlines():
            self.ProgramOffset += 1
        plc_file.close()
        plc_file = open(self._getIECcodepath(), "a")
        plc_file.write(self.RemoveLocatedVariables(open(self._getIECgeneratedcodepath(), "r").read()))
        plc_file.close()
        return True

    def _Compile_ST_to_SoftPLC(self):
        iec2c_libpath = self.iec2c_cfg.getLibPath()
        if iec2c_libpath is None:
            self.logger.write_error(_("matiec installation is not found\n"))
            return False

        self.logger.write(_("Compiling IEC Program into C code...\n"))
        buildpath = self._getBuildPath()
        buildcmd = "\"%s\" %s -I \"%s\" -T \"%s\" \"%s\"" % (
            self.iec2c_cfg.getCmd(),
            self.iec2c_cfg.getOptions(),
            iec2c_libpath,
            buildpath,
            self._getIECcodepath())

        try:
            # Invoke compiler.
            # Output files are listed to stdout, errors to stderr
            status, result, err_result = ProcessLogger(self.logger, buildcmd,
                                                       no_stdout=True,
                                                       no_stderr=True).spin()
        except Exception as e:
            self.logger.write_error(buildcmd + "\n")
            self.logger.write_error(repr(e) + "\n")
            return False

        if status:
            # Failed !

            # parse iec2c's error message. if it contains a line number,
            # then print those lines from the generated IEC file.
            for err_line in err_result.split('\n'):
                self.logger.write_warning(err_line + "\n")

                m_result = MATIEC_ERROR_MODEL.match(err_line)
                if m_result is not None:
                    first_line, _first_column, last_line, _last_column, _error = m_result.groups()
                    first_line, last_line = int(first_line), int(last_line)

                    last_section = None
                    f = open(self._getIECcodepath())

                    for i, line in enumerate(f.readlines()):
                        i = i + 1
                        if line[0] not in '\t \r\n':
                            last_section = line

                        if first_line <= i <= last_line:
                            if last_section is not None:
                                self.logger.write_warning(
                                    "In section: " + last_section)
                                last_section = None  # only write section once
                            self.logger.write_warning("%04d: %s" % (i, line))

                    f.close()

            self.logger.write_error(
                _("Error : IEC to C compiler returned %d\n") % status)
            return False

        # Now extract C files of stdout
        C_files = [fname for fname in result.splitlines() if fname[
            -2:] == ".c" or fname[-2:] == ".C"]
        # remove those that are not to be compiled because included by others
        C_files.remove("POUS.c")
        if not C_files:
            self.logger.write_error(
                _("Error : At least one configuration and one resource must be declared in PLC !\n"))
            return False
        # transform those base names to full names with path
        C_files = map(
            lambda filename: os.path.join(buildpath, filename), C_files)

        # prepend beremiz include to configuration header
        H_files = [fname for fname in result.splitlines() if fname[
            -2:] == ".h" or fname[-2:] == ".H"]
        H_files.remove("LOCATED_VARIABLES.h")
        H_files = map(
            lambda filename: os.path.join(buildpath, filename), H_files)
        for H_file in H_files:
            with open(H_file, 'r') as original:
                data = original.read()
            with open(H_file, 'w') as modified:
                modified.write('#include "beremiz.h"\n' + data)

        self.logger.write(_("Extracting Located Variables...\n"))
        # Keep track of generated located variables for later use by
        # self._Generate_C
        self.PLCGeneratedLocatedVars = self.GetLocations()
        # Keep track of generated C files for later use by self.CTNGenerate_C
        self.PLCGeneratedCFiles = C_files
        # compute CFLAGS for plc
        self.plcCFLAGS = '"-I%s" -Wno-unused-function' % self.iec2c_cfg.getLibCPath()
        return True

    def GetBuilder(self):
        """
        Return a Builder (compile C code into machine code)
        """
        # Get target, module and class name
        targetname = self.GetTarget().getcontent().getLocalTag()
        targetclass = targets.GetBuilder(targetname)

        # if target already
        if self._builder is None or not isinstance(self._builder, targetclass):
            # Get classname instance
            self._builder = targetclass(self)
        return self._builder

    #
    #
    #                C CODE GENERATION METHODS
    #
    #

    def CTNGenerate_C(self, buildpath, locations):
        """
        Return C code generated by iec2c compiler
        when _generate_softPLC have been called
        @param locations: ignored
        @return: [(C_file_name, CFLAGS),...] , LDFLAGS_TO_APPEND
        """

        return ([(C_file_name, self.plcCFLAGS)
                 for C_file_name in self.PLCGeneratedCFiles],
                "",  # no ldflags
                False)  # do not expose retreive/publish calls

    def ResetIECProgramsAndVariables(self):
        """
        Reset variable and program list that are parsed from
        CSV file generated by IEC2C compiler.
        """
        self._ProgramList = None
        self._VariablesList = None
        self._DbgVariablesList = None
        self._IECPathToIdx = {}
        self._Ticktime = 0
        self.TracedIECPath = []
        self.TracedIECTypes = []

    def GetIECProgramsAndVariables(self):
        """
        Parse CSV-like file  VARIABLES.csv resulting from IEC2C compiler.
        Each section is marked with a line staring with '//'
        list of all variables used in various POUs
        """
        if self._ProgramList is None or self._VariablesList is None:
            try:
                csvfile = os.path.join(self._getBuildPath(), "VARIABLES.csv")
                # describes CSV columns
                ProgramsListAttributeName = ["num", "C_path", "type"]
                VariablesListAttributeName = [
                    "num", "vartype", "IEC_path", "C_path", "type"]
                self._ProgramList = []
                self._VariablesList = []
                self._DbgVariablesList = []
                self._IECPathToIdx = {}

                # Separate sections
                ListGroup = []
                for line in open(csvfile, 'r').readlines():
                    strippedline = line.strip()
                    if strippedline.startswith("//"):
                        # Start new section
                        ListGroup.append([])
                    elif len(strippedline) > 0 and len(ListGroup) > 0:
                        # append to this section
                        ListGroup[-1].append(strippedline)

                # first section contains programs
                for line in ListGroup[0]:
                    # Split and Maps each field to dictionnary entries
                    attrs = dict(
                        zip(ProgramsListAttributeName, line.strip().split(';')))
                    # Truncate "C_path" to remove conf an resources names
                    attrs["C_path"] = '__'.join(
                        attrs["C_path"].split(".", 2)[1:])
                    # Push this dictionnary into result.
                    self._ProgramList.append(attrs)

                # second section contains all variables
                config_FBs = {}
                Idx = 0
                for line in ListGroup[1]:
                    # Split and Maps each field to dictionnary entries
                    attrs = dict(
                        zip(VariablesListAttributeName, line.strip().split(';')))
                    # Truncate "C_path" to remove conf an resources names
                    parts = attrs["C_path"].split(".", 2)
                    if len(parts) > 2:
                        config_FB = config_FBs.get(tuple(parts[:2]))
                        if config_FB:
                            parts = [config_FB] + parts[2:]
                            attrs["C_path"] = '.'.join(parts)
                        else:
                            attrs["C_path"] = '__'.join(parts[1:])
                    else:
                        attrs["C_path"] = '__'.join(parts)
                        if attrs["vartype"] == "FB":
                            config_FBs[tuple(parts)] = attrs["C_path"]
                    if attrs["vartype"] != "FB" and attrs["type"] in DebugTypesSize:
                        # Push this dictionnary into result.
                        self._DbgVariablesList.append(attrs)
                        # Fill in IEC<->C translation dicts
                        IEC_path = attrs["IEC_path"]
                        self._IECPathToIdx[IEC_path] = (Idx, attrs["type"])
                        # Ignores numbers given in CSV file
                        # Idx=int(attrs["num"])
                        # Count variables only, ignore FBs
                        Idx += 1
                    self._VariablesList.append(attrs)

                # third section contains ticktime
                if len(ListGroup) > 2:
                    self._Ticktime = int(ListGroup[2][0])

            except Exception:
                self.logger.write_error(
                    _("Cannot open/parse VARIABLES.csv!\n"))
                self.logger.write_error(traceback.format_exc())
                self.ResetIECProgramsAndVariables()
                return False

        return True

    def Generate_plc_debugger(self):
        """
        Generate trace/debug code out of PLC variable list
        """
        self.GetIECProgramsAndVariables()

        # prepare debug code
        variable_decl_array = []
        bofs = 0
        for v in self._DbgVariablesList:
            sz = DebugTypesSize.get(v["type"], 0)
            variable_decl_array += [
                "{&(%(C_path)s), " % v +
                {
                    "EXT": "%(type)s_P_ENUM",
                    "IN":  "%(type)s_P_ENUM",
                    "MEM": "%(type)s_O_ENUM",
                    "OUT": "%(type)s_O_ENUM",
                    "VAR": "%(type)s_ENUM"
                }[v["vartype"]] % v +
                "}"]
            bofs += sz
        debug_code = targets.GetCode("plc_debug.c") % {
            "buffer_size": bofs,
            "programs_declarations": "\n".join(["extern %(type)s %(C_path)s;" %
                                                p for p in self._ProgramList]),
            "extern_variables_declarations": "\n".join([
                {
                    "EXT": "extern __IEC_%(type)s_p %(C_path)s;",
                    "IN":  "extern __IEC_%(type)s_p %(C_path)s;",
                    "MEM": "extern __IEC_%(type)s_p %(C_path)s;",
                    "OUT": "extern __IEC_%(type)s_p %(C_path)s;",
                    "VAR": "extern __IEC_%(type)s_t %(C_path)s;",
                    "FB":  "extern       %(type)s   %(C_path)s;"
                }[v["vartype"]] % v
                for v in self._VariablesList if v["C_path"].find('.') < 0]),
            "variable_decl_array": ",\n".join(variable_decl_array)
        }

        return debug_code

    def Generate_plc_main(self):
        """
        Use confnodes layout given in LocationCFilesAndCFLAGS to
        generate glue code that dispatch calls to all confnodes
        """
        # filter location that are related to code that will be called
        # in retreive, publish, init, cleanup
        locstrs = map(lambda x: "_".join(map(str, x)),
                      [loc for loc, _Cfiles, DoCalls in
                       self.LocationCFilesAndCFLAGS if loc and DoCalls])

        # Generate main, based on template
        if not self.BeremizRoot.getDisable_Extensions():
            plc_main_code = targets.GetCode("plc_main_head.c") % {
                "calls_prototypes": "\n".join([(
                    "int __init_%(s)s(int argc,char **argv);\n" +
                    "void __cleanup_%(s)s(void);\n" +
                    "void __retrieve_%(s)s(void);\n" +
                    "void __publish_%(s)s(void);") % {'s': locstr} for locstr in locstrs]),
                "retrieve_calls": "\n    ".join([
                    "__retrieve_%s();" % locstr for locstr in locstrs]),
                "publish_calls": "\n    ".join([  # Call publish in reverse order
                    "__publish_%s();" % locstrs[i - 1] for i in xrange(len(locstrs), 0, -1)]),
                "init_calls": "\n    ".join([
                    "init_level=%d; " % (i + 1) +
                    "if((res = __init_%s(argc,argv))){" % locstr +
                    # "printf(\"%s\"); "%locstr + #for debug
                    "return res;}" for i, locstr in enumerate(locstrs)]),
                "cleanup_calls": "\n    ".join([
                    "if(init_level >= %d) " % i +
                    "__cleanup_%s();" % locstrs[i - 1] for i in xrange(len(locstrs), 0, -1)])
            }
        else:
            plc_main_code = targets.GetCode("plc_main_head.c") % {
                "calls_prototypes": "\n",
                "retrieve_calls":   "\n",
                "publish_calls":    "\n",
                "init_calls":       "\n",
                "cleanup_calls":    "\n"
            }
        plc_main_code += targets.GetTargetCode(
            self.GetTarget().getcontent().getLocalTag())
        plc_main_code += targets.GetCode("plc_main_tail.c")
        return plc_main_code

    def _Build(self):
        """
        Method called by user to (re)build SoftPLC and confnode tree
        """
        if self.AppFrame is not None:
            self.AppFrame.ClearErrors()
        self._CloseView(self._IECCodeView)

        buildpath = self._getBuildPath()

        # Eventually create build dir
        if not os.path.exists(buildpath):
            os.mkdir(buildpath)

        self.logger.flush()
        self.logger.write(_("Start build in %s\n") % buildpath)

        # Generate SoftPLC IEC code
        IECGenRes = self._Generate_SoftPLC()
        #self.UpdateButtons()

        # If IEC code gen fail, bail out.
        if not IECGenRes:
            self.logger.write_error(_("PLC code generation failed !\n"))
            return False

        # Reset variable and program list that are parsed from
        # CSV file generated by IEC2C compiler.
        self.ResetIECProgramsAndVariables()

        # Collect platform specific C code
        # Code and other files from extension
        if not self._Generate_runtime():
            return False

        # Get current or fresh builder
        builder = self.GetBuilder()
        if builder is None:
            self.logger.write_error(_("Fatal : cannot get builder.\n"))
            return False

        # Build
        try:
            if not builder.build():
                self.logger.write_error(_("C Build failed.\n"))
                return False
        except Exception:
            builder.ResetBinaryMD5()
            self.logger.write_error(_("C Build crashed !\n"))
            self.logger.write_error(traceback.format_exc())
            return False

        self.logger.write(_("Successfully built.\n"))
        # Update GUI status about need for transfer
        self.CompareLocalAndRemotePLC()

        return True

    def _Generate_runtime(self):
        buildpath = self._getBuildPath()

        # Generate C code and compilation params from confnode hierarchy
        try:
            CTNLocationCFilesAndCFLAGS, CTNLDFLAGS, CTNExtraFiles = self._Generate_C(
                buildpath,
                self.PLCGeneratedLocatedVars)
        except Exception:
            self.logger.write_error(
                _("Runtime IO extensions C code generation failed !\n"))
            self.logger.write_error(traceback.format_exc())
            return False

        # Generate C code and compilation params from liraries
        try:
            LibCFilesAndCFLAGS, LibLDFLAGS, LibExtraFiles = self.GetLibrariesCCode(
                buildpath)
        except Exception:
            self.logger.write_error(
                _("Runtime library extensions C code generation failed !\n"))
            self.logger.write_error(traceback.format_exc())
            return False

        self.LocationCFilesAndCFLAGS = LibCFilesAndCFLAGS + \
            CTNLocationCFilesAndCFLAGS
        self.LDFLAGS = CTNLDFLAGS + LibLDFLAGS
        ExtraFiles = CTNExtraFiles + LibExtraFiles

        # Get temporary directory path
        extrafilespath = self._getExtraFilesPath()
        # Remove old directory
        if os.path.exists(extrafilespath):
            shutil.rmtree(extrafilespath)
        # Recreate directory
        os.mkdir(extrafilespath)
        # Then write the files
        for fname, fobject in ExtraFiles:
            fpath = os.path.join(extrafilespath, fname)
            open(fpath, "wb").write(fobject.read())
        # Now we can forget ExtraFiles (will close files object)
        del ExtraFiles

        # Header file for extensions
        open(os.path.join(buildpath, "beremiz.h"), "w").write(
            targets.GetHeader())

        # Template based part of C code generation
        # files are stacked at the beginning, as files of confnode tree root
        c_source = [
            #  debugger code
            (self.Generate_plc_debugger, "plc_debugger.c", "Debugger"),
            # init/cleanup/retrieve/publish, run and align code
            (self.Generate_plc_main, "plc_main.c", "Common runtime")
        ]

        for generator, filename, name in c_source:
            try:
                # Do generate
                code = generator()
                if code is None:
                    raise Exception
                code_path = os.path.join(buildpath, filename)
                open(code_path, "w").write(code)
                # Insert this file as first file to be compiled at root
                # confnode
                self.LocationCFilesAndCFLAGS[0][1].insert(
                    0, (code_path, self.plcCFLAGS))
            except Exception:
                self.logger.write_error(name + _(" generation failed !\n"))
                self.logger.write_error(traceback.format_exc())
                return False
        self.logger.write(_("C code generated successfully.\n"))
        return True

    def ShowError(self, logger, from_location, to_location):
        chunk_infos = self.GetChunkInfos(from_location, to_location)
        for infos, (start_row, start_col) in chunk_infos:
            row = 1 if from_location[0] < start_row else (
                from_location[0] - start_row)
            col = 1 if (start_row != from_location[0]) else (
                from_location[1] - start_col)
            start = (row, col)

            row = 1 if to_location[0] < start_row else (
                to_location[0] - start_row)
            col = 1 if (start_row != to_location[0]) else (
                to_location[1] - start_col)
            end = (row, col)

            if self.AppFrame is not None:
                self.AppFrame.ShowError(infos, start, end)

    _IECCodeView = None

    def _showIDManager(self):
        dlg = IDManager(self.AppFrame, self)
        dlg.ShowModal()
        dlg.Destroy()

    def _showIECcode(self):
        self._OpenView("IEC code")

    _IECRawCodeView = None

    def _editIECrawcode(self):
        self._OpenView("IEC raw code")

    _ProjectFilesView = None

    def _OpenProjectFiles(self):
        self._OpenView("Project Files")

    _FileEditors = {}

    def _OpenFileEditor(self, filepath):
        self._OpenView(filepath)

    def _OpenView(self, name=None, onlyopened=False):
        if name == "IEC code":
            if self._IECCodeView is None:
                plc_file = self._getIECcodepath()

                self._IECCodeView = IECCodeViewer(
                    self.AppFrame.TabsOpened, "", self.AppFrame, None, instancepath=name)
                self._IECCodeView.SetTextSyntax("ALL")
                self._IECCodeView.SetKeywords(IEC_KEYWORDS)
                try:
                    text = open(plc_file).read()
                except Exception:
                    text = '(* No IEC code have been generated at that time ! *)'
                self._IECCodeView.SetText(text=text)
                self._IECCodeView.Editor.SetReadOnly(True)
                self._IECCodeView.SetIcon(GetBitmap("ST"))
                setattr(self._IECCodeView, "_OnClose", self.OnCloseEditor)

            if self._IECCodeView is not None:
                self.AppFrame.EditProjectElement(self._IECCodeView, name)

            return self._IECCodeView

        elif name == "IEC raw code":
            if self._IECRawCodeView is None:
                controler = MiniTextControler(self._getIECrawcodepath(), self)

                self._IECRawCodeView = IECCodeViewer(
                    self.AppFrame.TabsOpened, "", self.AppFrame, controler, instancepath=name)
                self._IECRawCodeView.SetTextSyntax("ALL")
                self._IECRawCodeView.SetKeywords(IEC_KEYWORDS)
                self._IECRawCodeView.RefreshView()
                self._IECRawCodeView.SetIcon(GetBitmap("ST"))
                setattr(self._IECRawCodeView, "_OnClose", self.OnCloseEditor)

            if self._IECRawCodeView is not None:
                self.AppFrame.EditProjectElement(self._IECRawCodeView, name)

            return self._IECRawCodeView

        elif name == "Project Files":
            if self._ProjectFilesView is None:
                self._ProjectFilesView = FileManagementPanel(
                    self.AppFrame.TabsOpened, self, name, self._getProjectFilesPath(), True)

                extensions = []
                for extension, _name, _editor in features.file_editors:
                    if extension not in extensions:
                        extensions.append(extension)
                self._ProjectFilesView.SetEditableFileExtensions(extensions)

            if self._ProjectFilesView is not None:
                self.AppFrame.EditProjectElement(self._ProjectFilesView, name)

            return self._ProjectFilesView

        elif name is not None and name.find("::") != -1:
            filepath, editor_name = name.split("::")
            if filepath not in self._FileEditors:
                if os.path.isfile(filepath):
                    file_extension = os.path.splitext(filepath)[1]

                    editors = dict([(edit_name, edit_class)
                                    for extension, edit_name, edit_class in features.file_editors
                                    if extension == file_extension])

                    if editor_name == "":
                        if len(editors) == 1:
                            editor_name = editors.keys()[0]
                        elif len(editors) > 0:
                            names = editors.keys()
                            dialog = wx.SingleChoiceDialog(
                                self.AppFrame,
                                _("Select an editor:"),
                                _("Editor selection"),
                                names,
                                wx.DEFAULT_DIALOG_STYLE | wx.OK | wx.CANCEL)
                            if dialog.ShowModal() == wx.ID_OK:
                                editor_name = names[dialog.GetSelection()]
                            dialog.Destroy()

                    if editor_name != "":
                        name = "::".join([filepath, editor_name])

                        editor = editors[editor_name]()
                        self._FileEditors[filepath] = editor(
                            self.AppFrame.TabsOpened, self, name, self.AppFrame)
                        self._FileEditors[filepath].SetIcon(GetBitmap("FILE"))
                        if isinstance(self._FileEditors[filepath], DebugViewer):
                            self._FileEditors[filepath].SetDataProducer(self)

            if filepath in self._FileEditors:
                editor = self._FileEditors[filepath]
                self.AppFrame.EditProjectElement(editor, editor.GetTagName())

            return self._FileEditors.get(filepath)
        else:
            return ConfigTreeNode._OpenView(self, self.CTNName(), onlyopened)

    def OnCloseEditor(self, view):
        ConfigTreeNode.OnCloseEditor(self, view)
        if self._IECCodeView == view:
            self._IECCodeView = None
        if self._IECRawCodeView == view:
            self._IECRawCodeView = None
        if self._ProjectFilesView == view:
            self._ProjectFilesView = None
        if view in self._FileEditors.values():
            self._FileEditors.pop(view.GetFilePath())

    def _Clean(self):
        self._CloseView(self._IECCodeView)
        if os.path.isdir(os.path.join(self._getBuildPath())):
            self.logger.write(_("Cleaning the build directory\n"))
            shutil.rmtree(os.path.join(self._getBuildPath()))
        else:
            self.logger.write_error(_("Build directory already clean\n"))
        # kill the builder
        self._builder = None
        self.CompareLocalAndRemotePLC()
        #self.UpdateButtons()

    def _UpdateButtons(self):
        #self.EnableMethod("_Clean", os.path.exists(self._getBuildPath()))
        #self.ShowMethod("_showIECcode", os.path.isfile(self._getIECcodepath()))
        if self.AppFrame is not None and not self.UpdateMethodsFromPLCStatus():
            self.AppFrame.RefreshStatusToolBar()

    def UpdateButtons(self):
        wx.CallAfter(self._UpdateButtons)

    def _BlockButtons(self):
        self.EnableMethod("_Run", False)
        if self.AppFrame is not None and not self.UpdateMethodsFromPLCStatus():
            self.AppFrame.RefreshStatusToolBar()

    def BlockButtons(self):
        wx.CallAfter(self._BlockButtons)

    def _UnblockButtons(self):
        self.EnableMethod("_Run", True)
        self.EnableMethod("_generateOpenPLC", True)
        if self.AppFrame is not None and not self.UpdateMethodsFromPLCStatus():
            self.AppFrame.RefreshStatusToolBar()

    def UnblockButtons(self):
        wx.CallAfter(self._UnblockButtons)

    def UpdatePLCLog(self, log_count):
        if log_count:
            if self.AppFrame is not None:
                self.AppFrame.LogViewer.SetLogCounters(log_count)

    DefaultMethods = {
        "_Run": True,
        "_Stop": False,
        "_Transfer": False,
        "_Connect": False,
        "_Disconnect": False,
        "_showIECcode": False,
        "_showIDManager": False,
        "_generateOpenPLC": True
    }

    MethodsFromStatus = {
        PlcStatus.Started:      {"_Stop": True,
                                 "_Run": False,
                                 "_Transfer": False,
                                 "_Connect": False,
                                 "_Disconnect": False,
                                 "_generateOpenPLC": True},
        PlcStatus.Stopped:      {"_Run": True,
                                 "_Stop": False,
                                 "_Transfer": False,
                                 "_Connect": False,
                                 "_Disconnect": False,
                                 "_generateOpenPLC": True},
        PlcStatus.Empty:        {"_Transfer": True,
                                 "_Connect": False,
                                 "_Disconnect": True},
        PlcStatus.Broken:       {"_Connect": False,
                                 "_Disconnect": True},
        PlcStatus.Disconnected: {},
    }

    def UpdateMethodsFromPLCStatus(self):
        updated = False
        status = None
        if self._connector is not None:
            PLCstatus = self._connector.GetPLCstatus()
            if PLCstatus is not None:
                status, log_count = PLCstatus
                self.UpdatePLCLog(log_count)
        if status is None:
            self._SetConnector(None, False)
            status = PlcStatus.Disconnected
        if self.previous_plcstate != status:
            allmethods = self.DefaultMethods.copy()
            allmethods.update(
                self.MethodsFromStatus.get(status, {}))
            for method, active in allmethods.items():
                self.ShowMethod(method, active)
            self.previous_plcstate = status
            if self.AppFrame is not None:
                updated = True
                self.AppFrame.RefreshStatusToolBar()
                if status == PlcStatus.Disconnected:
                    self.AppFrame.ConnectionStatusBar.SetStatusText(
                        _(status), 1)
                    self.AppFrame.ConnectionStatusBar.SetStatusText('', 2)
                else:
                    self.AppFrame.ConnectionStatusBar.SetStatusText(
                        _("Connected to URI: %s") % self.BeremizRoot.getURI_location().strip(), 1)
                    self.AppFrame.ConnectionStatusBar.SetStatusText(
                        _(status), 2)
        return updated

    def ShowPLCProgress(self, status="", progress=0):
        self.AppFrame.ProgressStatusBar.Show()
        self.AppFrame.ConnectionStatusBar.SetStatusText(
            _(status), 1)
        self.AppFrame.ProgressStatusBar.SetValue(progress)

    def HidePLCProgress(self):
        # clear previous_plcstate to restore status
        # in UpdateMethodsFromPLCStatus()
        self.previous_plcstate = ""
        self.AppFrame.ProgressStatusBar.Hide()
        self.UpdateMethodsFromPLCStatus()

    def PullPLCStatusProc(self, event):
        self.UpdateMethodsFromPLCStatus()

    def SnapshotAndResetDebugValuesBuffers(self):
        debug_status = PlcStatus.Disconnected
        if self._connector is not None and self.DebugToken is not None:
            debug_status, Traces = self._connector.GetTraceVariables(self.DebugToken)
            # print [dict.keys() for IECPath, (dict, log, status, fvalue) in
            # self.IECdebug_datas.items()]
            if debug_status == PlcStatus.Started:
                if len(Traces) > 0:
                    for debug_tick, debug_buff in Traces:
                        debug_vars = UnpackDebugBuffer(
                            debug_buff, self.TracedIECTypes)
                        if debug_vars is not None and len(debug_vars) == len(self.TracedIECPath):
                            for IECPath, values_buffer, value in zip(
                                    self.TracedIECPath,
                                    self.DebugValuesBuffers,
                                    debug_vars):
                                IECdebug_data = self.IECdebug_datas.get(
                                    IECPath, None)
                                if IECdebug_data is not None and value is not None:
                                    forced = (IECdebug_data[2] == "Forced") \
                                        and (value is not None) and \
                                        (IECdebug_data[3] is not None)

                                    if not IECdebug_data[4] and len(values_buffer) > 0:
                                        values_buffer[-1] = (value, forced)
                                    else:
                                        values_buffer.append((value, forced))
                            self.DebugTicks.append(debug_tick)

        buffers, self.DebugValuesBuffers = (self.DebugValuesBuffers,
                                            [list() for dummy in xrange(len(self.TracedIECPath))])

        ticks, self.DebugTicks = self.DebugTicks, []

        return debug_status, ticks, buffers

    def RegisterDebugVarToConnector(self):
        self.DebugTimer = None
        Idxs = []
        self.TracedIECPath = []
        self.TracedIECTypes = []
        if self._connector is not None and self.debug_status != PlcStatus.Broken:
            IECPathsToPop = []
            for IECPath, data_tuple in self.IECdebug_datas.iteritems():
                WeakCallableDict, _data_log, _status, fvalue, _buffer_list = data_tuple
                if len(WeakCallableDict) == 0:
                    # Callable Dict is empty.
                    # This variable is not needed anymore!
                    IECPathsToPop.append(IECPath)
                elif IECPath != "__tick__":
                    # Convert
                    Idx, IEC_Type = self._IECPathToIdx.get(
                        IECPath, (None, None))
                    if Idx is not None:
                        if IEC_Type in DebugTypesSize:
                            Idxs.append((Idx, IEC_Type, fvalue, IECPath))
                        else:
                            self.logger.write_warning(
                                _("Debug: Unsupported type to debug '%s'\n") % IEC_Type)
                    else:
                        self.logger.write_warning(
                            _("Debug: Unknown variable '%s'\n") % IECPath)
            for IECPathToPop in IECPathsToPop:
                self.IECdebug_datas.pop(IECPathToPop)

            if Idxs:
                Idxs.sort()
                IdxsT = zip(*Idxs)
                self.TracedIECPath = IdxsT[3]
                self.TracedIECTypes = IdxsT[1]
                self.DebugToken = self._connector.SetTraceVariablesList(zip(*IdxsT[0:3]))
            else:
                self.TracedIECPath = []
                self._connector.SetTraceVariablesList([])
                self.DebugToken = None
            self.debug_status, _debug_ticks, _buffers = self.SnapshotAndResetDebugValuesBuffers()

    def IsPLCStarted(self):
        return self.previous_plcstate == PlcStatus.Started

    def ReArmDebugRegisterTimer(self):
        if self.DebugTimer is not None:
            self.DebugTimer.cancel()

        # Prevent to call RegisterDebugVarToConnector when PLC is not started
        # If an output location var is forced it's leads to segmentation fault in runtime
        # Links between PLC located variables and real variables are not ready
        if self.IsPLCStarted():
            # Timer to prevent rapid-fire when registering many variables
            # use wx.CallAfter use keep using same thread. TODO : use wx.Timer
            # instead
            self.DebugTimer = Timer(
                0.5, wx.CallAfter, args=[self.RegisterDebugVarToConnector])
            # Rearm anti-rapid-fire timer
            self.DebugTimer.start()

    def GetDebugIECVariableType(self, IECPath):
        _Idx, IEC_Type = self._IECPathToIdx.get(IECPath, (None, None))
        return IEC_Type

    def SubscribeDebugIECVariable(self, IECPath, callableobj, buffer_list=False):
        """
        Dispatching use a dictionnary linking IEC variable paths
        to a WeakKeyDictionary linking
        weakly referenced callables
        """
        if IECPath != "__tick__" and IECPath not in self._IECPathToIdx:
            return None

        # If no entry exist, create a new one with a fresh WeakKeyDictionary
        IECdebug_data = self.IECdebug_datas.get(IECPath, None)
        if IECdebug_data is None:
            IECdebug_data = [
                WeakKeyDictionary(),  # Callables
                [],                   # Data storage [(tick, data),...]
                "Registered",         # Variable status
                None,
                buffer_list]                # Forced value
            self.IECdebug_datas[IECPath] = IECdebug_data
        else:
            IECdebug_data[4] |= buffer_list

        IECdebug_data[0][callableobj] = buffer_list

        self.ReArmDebugRegisterTimer()

        return IECdebug_data[1]

    def UnsubscribeDebugIECVariable(self, IECPath, callableobj):
        IECdebug_data = self.IECdebug_datas.get(IECPath, None)
        if IECdebug_data is not None:
            IECdebug_data[0].pop(callableobj, None)
            if len(IECdebug_data[0]) == 0:
                self.IECdebug_datas.pop(IECPath)
            else:
                IECdebug_data[4] = reduce(
                    lambda x, y: x | y,
                    IECdebug_data[0].itervalues(),
                    False)

        self.ReArmDebugRegisterTimer()

    def UnsubscribeAllDebugIECVariable(self):
        self.IECdebug_datas = {}

        self.ReArmDebugRegisterTimer()

    def ForceDebugIECVariable(self, IECPath, fvalue):
        if IECPath not in self.IECdebug_datas:
            return

        # If no entry exist, create a new one with a fresh WeakKeyDictionary
        IECdebug_data = self.IECdebug_datas.get(IECPath, None)
        IECdebug_data[2] = "Forced"
        IECdebug_data[3] = fvalue

        self.ReArmDebugRegisterTimer()

    def ReleaseDebugIECVariable(self, IECPath):
        if IECPath not in self.IECdebug_datas:
            return

        # If no entry exist, create a new one with a fresh WeakKeyDictionary
        IECdebug_data = self.IECdebug_datas.get(IECPath, None)
        IECdebug_data[2] = "Registered"
        IECdebug_data[3] = None

        self.ReArmDebugRegisterTimer()

    def CallWeakcallables(self, IECPath, function_name, *cargs):
        data_tuple = self.IECdebug_datas.get(IECPath, None)
        if data_tuple is not None:
            WeakCallableDict, _data_log, _status, _fvalue, buffer_list = data_tuple
            # data_log.append((debug_tick, value))
            for weakcallable, buffer_list in WeakCallableDict.iteritems():
                function = getattr(weakcallable, function_name, None)
                if function is not None:
                    if buffer_list:
                        function(*cargs)
                    else:
                        function(*tuple([lst[-1] for lst in cargs]))

    def GetTicktime(self):
        return self._Ticktime

    def RemoteExec(self, script, **kwargs):
        if self._connector is None:
            return -1, "No runtime connected!"
        return self._connector.RemoteExec(script, **kwargs)

    def DispatchDebugValuesProc(self, event):
        self.debug_status, debug_ticks, buffers = self.SnapshotAndResetDebugValuesBuffers()
        start_time = time.time()
        if len(self.TracedIECPath) == len(buffers):
            for IECPath, values in zip(self.TracedIECPath, buffers):
                if len(values) > 0:
                    self.CallWeakcallables(
                        IECPath, "NewValues", debug_ticks, values)
            if len(debug_ticks) > 0:
                self.CallWeakcallables(
                    "__tick__", "NewDataAvailable", debug_ticks)

        if self.debug_status == PlcStatus.Broken:
            self.logger.write_warning(
                _("Debug: token rejected - other debug took over - reconnect to recover\n"))
        else:
            delay = time.time() - start_time
            next_refresh = max(REFRESH_PERIOD - delay, 0.2 * delay)
            if self.DispatchDebugValuesTimer is not None:
                self.DispatchDebugValuesTimer.Start(
                    int(next_refresh * 1000), oneShot=True)
        event.Skip()

    def KillDebugThread(self):
        if self.DispatchDebugValuesTimer is not None:
            self.DispatchDebugValuesTimer.Stop()

    def _connect_debug(self):
        self.previous_plcstate = None
        if self.AppFrame:
            self.AppFrame.ResetGraphicViewers()

        self.debug_status = PlcStatus.Started

        self.RegisterDebugVarToConnector()
        if self.DispatchDebugValuesTimer is not None:
            self.DispatchDebugValuesTimer.Start(
                int(REFRESH_PERIOD * 1000), oneShot=True)

    def _Run(self):
        """
        Start PLC
        """
        self.BlockButtons()
        #Clean build folder
        self._Clean()

        #Build Project
        if (self._Build() is False):
            self.UnblockButtons()
            return

        #Connect to target
        if (self._Connect() is False):
            self.UnblockButtons()
            return

        #Transfer PLC program
        if (self._Transfer() is False):
            self.UnblockButtons()
            return

        #Run
        if self.GetIECProgramsAndVariables():
            self._connector.StartPLC()
            self.logger.write(_("Starting PLC\n"))
            self._connect_debug()
        else:
            self.logger.write_error(_("Couldn't start PLC !\n"))

        self.UnblockButtons()
        wx.CallAfter(self.UpdateMethodsFromPLCStatus)

    def _Stop(self):
        """
        Stop PLC
        """
        if self._connector is not None and not self._connector.StopPLC():
            self.logger.write_error(_("Couldn't stop PLC !\n"))

        self._Disconnect()

        # debugthread should die on his own
        # self.KillDebugThread()

        wx.CallAfter(self.UpdateMethodsFromPLCStatus)

    def _SetConnector(self, connector, update_status=True):
        self._connector = connector
        if self.AppFrame is not None:
            self.AppFrame.LogViewer.SetLogSource(connector)
        if connector is not None:
            if self.StatusTimer is not None:
                # Start the status Timer
                self.StatusTimer.Start(milliseconds=500, oneShot=False)
        else:
            if self.StatusTimer is not None:
                # Stop the status Timer
                self.StatusTimer.Stop()
            if update_status:
                wx.CallAfter(self.UpdateMethodsFromPLCStatus)

    def _Connect(self):
        # don't accept re-connetion if already connected
        if self._connector is not None:
            self.logger.write_error(
                _("Already connected. Please disconnect\n"))
            return True

        # Get connector uri
        uri = self.BeremizRoot.getURI_location().strip()

        # if uri is empty launch discovery dialog
        if uri == "":
            uri = "LOCAL://"
            self.BeremizRoot.setURI_location(uri)
            self.ChangesToSave = True
            if self._View is not None:
                self._View.RefreshView()
            if self.AppFrame is not None:
                self.AppFrame.RefreshTitle()
                self.AppFrame.RefreshFileMenu()
                self.AppFrame.RefreshEditMenu()
                self.AppFrame.RefreshPageTitles()
            """
            try:
                # Launch Service Discovery dialog
                dialog = UriEditor(self.AppFrame, self)
                answer = dialog.ShowModal()
                uri = str(dialog.GetURI())
                dialog.Destroy()
            except Exception:
                self.logger.write_error(_("Local service discovery failed!\n"))
                self.logger.write_error(traceback.format_exc())
                uri = None

            # Nothing choosed or cancel button
            if uri is None or answer == wx.ID_CANCEL:
                self.logger.write_error(_("Connection canceled!\n"))
                return
            else:
                self.BeremizRoot.setURI_location(uri)
                self.ChangesToSave = True
                if self._View is not None:
                    self._View.RefreshView()
                if self.AppFrame is not None:
                    self.AppFrame.RefreshTitle()
                    self.AppFrame.RefreshFileMenu()
                    self.AppFrame.RefreshEditMenu()
                    self.AppFrame.RefreshPageTitles()"""

        # Get connector from uri
        try:
            self._SetConnector(connectors.ConnectorFactory(uri, self))
        except Exception as e:
            self.logger.write_error(
                _("Exception while connecting to '{uri}': {ex}\n").format(
                    uri=uri, ex=e))

        # Did connection success ?
        if self._connector is None:
            # Oups.
            self.logger.write_error(_("Connection failed to %s!\n") % uri)
            return False
        else:
            self.CompareLocalAndRemotePLC()

            # Init with actual PLC status and print it
            #self.UpdateMethodsFromPLCStatus()
            if self.previous_plcstate in [PlcStatus.Started, PlcStatus.Stopped]:
                if self.DebugAvailable() and self.GetIECProgramsAndVariables():
                    self.logger.write(_("Debugger ready\n"))
                    self._connect_debug()
                else:
                    self.logger.write_warning(
                        _("Debug does not match PLC - stop/transfert/start to re-enable\n"))
            return True

    def CompareLocalAndRemotePLC(self):
        if self._connector is None:
            return
        builder = self.GetBuilder()
        if builder is None:
            return
        MD5 = builder.GetBinaryMD5()
        if MD5 is None:
            return
        # Check remote target PLC correspondance to that md5
        if self._connector.MatchMD5(MD5):
            self.logger.write(
                _("Latest build matches with connected target.\n"))
            self.ProgramTransferred()
        else:
            self.logger.write(
                _("Latest build does not match with connected target.\n"))

    def _Disconnect(self):
        self._SetConnector(None)

    def _Transfer(self):
        if self.IsPLCStarted():
            dialog = wx.MessageDialog(
                self.AppFrame,
                _("Cannot transfer while PLC is running. Stop it now?"),
                style=wx.YES_NO | wx.CENTRE)
            if dialog.ShowModal() == wx.ID_YES:
                self._Stop()
            else:
                return False

        builder = self.GetBuilder()
        if builder is None:
            self.logger.write_error(_("Fatal : cannot get builder.\n"))
            return False

        # recover md5 from last build
        MD5 = builder.GetBinaryMD5()

        # Check if md5 file is empty : ask user to build PLC
        if MD5 is None:
            self.logger.write_error(
                _("Failed : Must build before transfer.\n"))
            return False

        # Compare PLC project with PLC on target
        if self._connector.MatchMD5(MD5):
            self.logger.write(
                _("Latest build already matches current target. Transfering anyway...\n"))

        # purge any non-finished transfer
        # note: this would abord any runing transfer with error
        self._connector.PurgeBlobs()

        # transfer extra files
        extrafiles = []
        for extrafilespath in [self._getExtraFilesPath(),
                               self._getProjectFilesPath()]:

            for name in os.listdir(extrafilespath):
                extrafiles.append((
                    name,
                    self._connector.BlobFromFile(
                        # use file name as a seed to avoid collisions
                        # with files having same content
                        os.path.join(extrafilespath, name), name)))

        # Send PLC on target
        object_path = builder.GetBinaryPath()
        # arbitrarily use MD5 as a seed, could be any string
        object_blob = self._connector.BlobFromFile(object_path, MD5)

        self.HidePLCProgress()

        self.logger.write(_("PLC data transfered successfully.\n"))

        if self._connector.NewPLC(MD5, object_blob, extrafiles):
            if self.GetIECProgramsAndVariables():
                self.UnsubscribeAllDebugIECVariable()
                self.ProgramTransferred()
                self.AppFrame.CloseObsoleteDebugTabs()
                self.AppFrame.RefreshPouInstanceVariablesPanel()
                self.AppFrame.LogViewer.ResetLogCounters()
                self.logger.write(_("PLC installed successfully.\n"))
            else:
                self.logger.write_error(_("Missing debug data\n"))
                return False
        else:
            self.logger.write_error(_("PLC couldn't be installed\n"))
            return False
        return True

        #wx.CallAfter(self.UpdateMethodsFromPLCStatus)

    def _generateOpenPLC(self):
        self._Clean()
        if (self._Build() is True):
            f = open(self._getIECgeneratedcodepath(), "r")
            program = f.read()
            f.close()

            dlg = wx.FileDialog(self.AppFrame, "Save to file:", "", "", "OpenPLC Program(*.st)|*.st", wx.SAVE|wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    f = open(dlg.GetPath(), "w")
                    f.write(program)
                    f.close()
                    #wx.MessageBox('OpenPLC program generated successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
                    self.logger.write("OpenPLC program generated successfully\n")

                except:
                    self.logger.write_error('It was not possible to save the generated program\n')

    StatusMethods = [
        {
            "bitmap":    "Build",
            "name":    _("Build"),
            "tooltip": _("Build project into build folder"),
            "method":   "_Build",
            "shown":      False,
        },
        {
            "bitmap":    "Clean",
            "name":    _("Clean"),
            "tooltip": _("Clean project build folder"),
            "method":   "_Clean",
            "enabled":    False,
            "shown":      False,
        },
        {
            "bitmap":    "Run",
            "name":    _("Run"),
            "tooltip": _("Start PLC Simulation"),
            "method":   "_Run",
            "shown":      True,
        },
        {
            "bitmap":    "Stop",
            "name":    _("Stop"),
            "tooltip": _("Stop PLC Simulation"),
            "method":   "_Stop",
            "shown":      False,
        },
        {
            "bitmap":    "Connect",
            "name":    _("Connect"),
            "tooltip": _("Connect to the target PLC"),
            "method":   "_Connect",
            "shown":      False,
        },
        {
            "bitmap":    "Transfer",
            "name":    _("Transfer"),
            "tooltip": _("Transfer PLC"),
            "method":   "_Transfer",
            "shown":      False,
        },
        {
            "bitmap":    "Disconnect",
            "name":    _("Disconnect"),
            "tooltip": _("Disconnect from PLC"),
            "method":   "_Disconnect",
            "shown":      False,
        },
        {
            "bitmap":    "IDManager",
            "name":    _("ID Manager"),
            "tooltip": _("Manage secure connection identities"),
            "method":   "_showIDManager",
            "shown":      False,
        },
        {
            "bitmap":    "ShowIECcode",
            "name":    _("Show code"),
            "tooltip": _("Show IEC code generated by PLCGenerator"),
            "method":   "_showIECcode",
            "shown":      False,
        },
        {
            "bitmap":    "down",
            "name":    _("Generate Program"),
            "tooltip": _("Generate program for OpenPLC Runtime"),
            "method":   "_generateOpenPLC",
            "shown":      True,
        },
    ]

    ConfNodeMethods = [
        {
            "bitmap":    "editIECrawcode",
            "name":    _("Raw IEC code"),
            "tooltip": _("Edit raw IEC code added to code generated by PLCGenerator"),
            "method":   "_editIECrawcode"
        },
        {
            "bitmap":    "ManageFolder",
            "name":    _("Project Files"),
            "tooltip": _("Open a file explorer to manage project files"),
            "method":   "_OpenProjectFiles"
        },
    ]

    def EnableMethod(self, method, value):
        for d in self.StatusMethods:
            if d["method"] == method:
                d["enabled"] = value
                return True
        return False

    def ShowMethod(self, method, value):
        for d in self.StatusMethods:
            if d["method"] == method:
                d["shown"] = value
                return True
        return False

    def CallMethod(self, method):
        for d in self.StatusMethods:
            if d["method"] == method and d.get("enabled", True) and d.get("shown", True):
                getattr(self, method)()
