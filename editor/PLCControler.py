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
from copy import deepcopy
import os
import re
import datetime
from time import localtime
from functools import reduce
from future.builtins import round

import util.paths as paths
from plcopen import *
from plcopen.types_enums import *
from plcopen.InstancesPathCollector import InstancesPathCollector
from plcopen.POUVariablesCollector import POUVariablesCollector
from plcopen.InstanceTagnameCollector import InstanceTagnameCollector
from plcopen.BlockInstanceCollector import BlockInstanceCollector
from plcopen.VariableInfoCollector import VariableInfoCollector
from graphics.GraphicCommons import *
from PLCGenerator import *

duration_model = re.compile(r"(?:([0-9]{1,2})h)?(?:([0-9]{1,2})m(?!s))?(?:([0-9]{1,2})s)?(?:([0-9]{1,3}(?:\.[0-9]*)?)ms)?")
VARIABLE_NAME_SUFFIX_MODEL = re.compile(r'(\d+)$')

ScriptDirectory = paths.AbsDir(__file__)

# Length of the buffer
UNDO_BUFFER_LENGTH = 20


class UndoBuffer(object):
    """
    Undo Buffer for PLCOpenEditor
    Class implementing a buffer of changes made on the current editing model
    """

    def __init__(self, currentstate, issaved=False):
        """
        Constructor initialising buffer
        """
        self.Buffer = []
        self.CurrentIndex = -1
        self.MinIndex = -1
        self.MaxIndex = -1
        # if current state is defined
        if currentstate:
            self.CurrentIndex = 0
            self.MinIndex = 0
            self.MaxIndex = 0
        # Initialising buffer with currentstate at the first place
        for i in xrange(UNDO_BUFFER_LENGTH):
            if i == 0:
                self.Buffer.append(currentstate)
            else:
                self.Buffer.append(None)
        # Initialising index of state saved
        if issaved:
            self.LastSave = 0
        else:
            self.LastSave = -1

    def Buffering(self, currentstate):
        """
        Add a new state in buffer
        """
        self.CurrentIndex = (self.CurrentIndex + 1) % UNDO_BUFFER_LENGTH
        self.Buffer[self.CurrentIndex] = currentstate
        # Actualising buffer limits
        self.MaxIndex = self.CurrentIndex
        if self.MinIndex == self.CurrentIndex:
            # If the removed state was the state saved, there is no state saved in the buffer
            if self.LastSave == self.MinIndex:
                self.LastSave = -1
            self.MinIndex = (self.MinIndex + 1) % UNDO_BUFFER_LENGTH
        self.MinIndex = max(self.MinIndex, 0)

    def Current(self):
        """
        Return current state of buffer
        """
        return self.Buffer[self.CurrentIndex]

    # Change current state to previous in buffer and return new current state
    def Previous(self):
        if self.CurrentIndex != self.MinIndex:
            self.CurrentIndex = (self.CurrentIndex - 1) % UNDO_BUFFER_LENGTH
            return self.Buffer[self.CurrentIndex]
        return None

    # Change current state to next in buffer and return new current state
    def Next(self):
        if self.CurrentIndex != self.MaxIndex:
            self.CurrentIndex = (self.CurrentIndex + 1) % UNDO_BUFFER_LENGTH
            return self.Buffer[self.CurrentIndex]
        return None

    # Return True if current state is the first in buffer
    def IsFirst(self):
        return self.CurrentIndex == self.MinIndex

    # Return True if current state is the last in buffer
    def IsLast(self):
        return self.CurrentIndex == self.MaxIndex

    # Note that current state is saved
    def CurrentSaved(self):
        self.LastSave = self.CurrentIndex

    # Return True if current state is saved
    def IsCurrentSaved(self):
        return self.LastSave == self.CurrentIndex


class PLCControler(object):
    """
    Controler for PLCOpenEditor
    Class which controls the operations made on the plcopen model and answers to view requests
    """

    # Create a new PLCControler
    def __init__(self):
        self.LastNewIndex = 0
        self.Reset()
        self.InstancesPathCollector = InstancesPathCollector(self)
        self.POUVariablesCollector = POUVariablesCollector(self)
        self.InstanceTagnameCollector = InstanceTagnameCollector(self)
        self.BlockInstanceCollector = BlockInstanceCollector(self)
        self.VariableInfoCollector = VariableInfoCollector(self)

    # Reset PLCControler internal variables
    def Reset(self):
        self.Project = None
        self.ProjectBufferEnabled = True
        self.ProjectBuffer = None
        self.ProjectSaved = True
        self.Buffering = False
        self.FilePath = ""
        self.FileName = ""
        self.ProgramChunks = []
        self.ProgramOffset = 0
        self.NextCompiledProject = None
        self.CurrentCompiledProject = None
        self.ConfNodeTypes = []
        self.TotalTypesDict = StdBlckDct.copy()
        self.TotalTypes = StdBlckLst[:]
        self.ProgramFilePath = ""

    def GetQualifierTypes(self):
        return QualifierList

    def GetProject(self, debug=False):
        if debug and self.CurrentCompiledProject is not None:
            return self.CurrentCompiledProject
        else:
            return self.Project

    # -------------------------------------------------------------------------------
    #                         Project management functions
    # -------------------------------------------------------------------------------

    # Return if a project is opened
    def HasOpenedProject(self):
        return self.Project is not None

    # Create a new project by replacing the current one
    def CreateNewProject(self, properties):
        # Create the project
        self.Project = PLCOpenParser.CreateRoot()
        properties["creationDateTime"] = datetime.datetime(*localtime()[:6])
        self.Project.setfileHeader(properties)
        self.Project.setcontentHeader(properties)
        self.SetFilePath("")

        # Initialize the project buffer
        self.CreateProjectBuffer(False)
        self.ProgramChunks = []
        self.ProgramOffset = 0
        self.NextCompiledProject = self.Copy(self.Project)
        self.CurrentCompiledProject = None
        self.Buffering = False

    # Return project data type names
    def GetProjectDataTypeNames(self, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return [datatype.getname() for datatype in project.getdataTypes()]
        return []

    # Return project pou names
    def GetProjectPouNames(self, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return [pou.getname() for pou in project.getpous()]
        return []

    # Return project pou names
    def GetProjectConfigNames(self, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return [config.getname() for config in project.getconfigurations()]
        return []

    # Return project pou variable names
    def GetProjectPouVariableNames(self, pou_name=None, debug=False):
        variables = []
        project = self.GetProject(debug)
        if project is not None:
            for pou in project.getpous():
                if pou_name is None or pou_name == pou.getname():
                    variables.extend([var.Name for var in self.GetPouInterfaceVars(pou, debug=debug)])
                    for transition in pou.gettransitionList():
                        variables.append(transition.getname())
                    for action in pou.getactionList():
                        variables.append(action.getname())
        return variables

    # Return file path if project is an open file
    def GetFilePath(self):
        return self.FilePath

    # Return file path if project is an open file
    def GetProgramFilePath(self):
        return self.ProgramFilePath

    # Return file name and point out if file is up to date
    def GetFilename(self):
        if self.Project is not None:
            if self.ProjectIsSaved():
                return self.FileName
            else:
                return "~%s~" % self.FileName
        return ""

    # Change file path and save file name or create a default one if file path not defined
    def SetFilePath(self, filepath):
        self.FilePath = filepath
        if filepath == "":
            self.LastNewIndex += 1
            self.FileName = _("Unnamed%d") % self.LastNewIndex
        else:
            self.FileName = os.path.splitext(os.path.basename(filepath))[0]

    # Change project properties
    def SetProjectProperties(self, name=None, properties=None, buffer=True):
        if self.Project is not None:
            if name is not None:
                self.Project.setname(name)
            if properties is not None:
                self.Project.setfileHeader(properties)
                self.Project.setcontentHeader(properties)
            if buffer and (name is not None or properties is not None):
                self.BufferProject()

    # Return project name
    def GetProjectName(self, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return project.getname()
        return None

    # Return project properties
    def GetProjectProperties(self, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            properties = project.getfileHeader()
            properties.update(project.getcontentHeader())
            return properties
        return None

    # Return project informations
    def GetProjectInfos(self, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            infos = {"name": project.getname(), "type": ITEM_PROJECT}
            datatypes = {"name": DATA_TYPES, "type": ITEM_DATATYPES, "values": []}
            for datatype in project.getdataTypes():
                datatypes["values"].append({
                    "name": datatype.getname(),
                    "type": ITEM_DATATYPE,
                    "tagname": ComputeDataTypeName(datatype.getname()),
                    "values": []})
            pou_types = {
                "function": {
                    "name":   FUNCTIONS,
                    "type":   ITEM_FUNCTION,
                    "values": []
                },
                "functionBlock": {
                    "name":   FUNCTION_BLOCKS,
                    "type":   ITEM_FUNCTIONBLOCK,
                    "values": []
                },
                "program": {
                    "name":   PROGRAMS,
                    "type":   ITEM_PROGRAM,
                    "values": []
                }
            }
            for pou in project.getpous():
                pou_type = pou.getpouType()
                pou_infos = {"name": pou.getname(), "type": ITEM_POU,
                             "tagname": ComputePouName(pou.getname())}
                pou_values = []
                if pou.getbodyType() == "SFC":
                    transitions = []
                    for transition in pou.gettransitionList():
                        transitions.append({
                            "name": transition.getname(),
                            "type": ITEM_TRANSITION,
                            "tagname": ComputePouTransitionName(pou.getname(), transition.getname()),
                            "values": []})
                    pou_values.append({"name": TRANSITIONS, "type": ITEM_TRANSITIONS, "values": transitions})
                    actions = []
                    for action in pou.getactionList():
                        actions.append({
                            "name": action.getname(),
                            "type": ITEM_ACTION,
                            "tagname": ComputePouActionName(pou.getname(), action.getname()),
                            "values": []})
                    pou_values.append({"name": ACTIONS, "type": ITEM_ACTIONS, "values": actions})
                if pou_type in pou_types:
                    pou_infos["values"] = pou_values
                    pou_types[pou_type]["values"].append(pou_infos)
            configurations = {"name": CONFIGURATIONS, "type": ITEM_CONFIGURATIONS, "values": []}
            for config in project.getconfigurations():
                config_name = config.getname()
                config_infos = {
                    "name": config_name,
                    "type": ITEM_CONFIGURATION,
                    "tagname": ComputeConfigurationName(config.getname()),
                    "values": []}
                resources = {"name": RESOURCES, "type": ITEM_RESOURCES, "values": []}
                for resource in config.getresource():
                    resource_name = resource.getname()
                    resource_infos = {
                        "name": resource_name,
                        "type": ITEM_RESOURCE,
                        "tagname": ComputeConfigurationResourceName(config.getname(), resource.getname()),
                        "values": []}
                    resources["values"].append(resource_infos)
                config_infos["values"] = [resources]
                configurations["values"].append(config_infos)
            infos["values"] = [datatypes, pou_types["function"], pou_types["functionBlock"],
                               pou_types["program"], configurations]
            return infos
        return None

    def GetPouVariables(self, tagname, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            obj = None
            words = tagname.split("::")
            if words[0] == "P":
                obj = self.GetPou(words[1], debug)
            elif words[0] != "D":
                obj = self.GetEditedElement(tagname, debug)
            if obj is not None:
                return self.POUVariablesCollector.Collect(obj, debug)

        return None

    def GetInstanceList(self, root, name, debug=False):
        return self.InstancesPathCollector.Collect(root, name, debug)

    def SearchPouInstances(self, tagname, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            words = tagname.split("::")
            if words[0] == "P":
                return self.GetInstanceList(project, words[1])
            elif words[0] == 'C':
                return [words[1]]
            elif words[0] == 'R':
                return ["%s.%s" % (words[1], words[2])]
            elif words[0] in ['T', 'A']:
                return ["%s.%s" % (instance, words[2])
                        for instance in self.SearchPouInstances(
                            ComputePouName(words[1]), debug)]
        return []

    def GetPouInstanceTagName(self, instance_path, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return self.InstanceTagnameCollector.Collect(project,
                                                         debug,
                                                         instance_path)

    def GetInstanceInfos(self, instance_path, debug=False):
        tagname = self.GetPouInstanceTagName(instance_path)
        if tagname is not None:
            infos = self.GetPouVariables(tagname, debug)
            infos.type = tagname
            return infos
        else:
            pou_path, var_name = instance_path.rsplit(".", 1)
            tagname = self.GetPouInstanceTagName(pou_path)
            if tagname is not None:
                pou_infos = self.GetPouVariables(tagname, debug)
                for var_infos in pou_infos.variables:
                    if var_infos.name == var_name:
                        return var_infos
        return None

    # Return if data type given by name is used by another data type or pou
    def DataTypeIsUsed(self, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return len(self.GetInstanceList(project, name, debug)) > 0
        return False

    # Return if pou given by name is used by another pou
    def PouIsUsed(self, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            return len(self.GetInstanceList(project, name, debug)) > 0
        return False

    # Return if pou given by name is directly or undirectly used by the reference pou
    def PouIsUsedBy(self, name, reference, debug=False):
        pou_infos = self.GetPou(reference, debug)
        if pou_infos is not None:
            return len(self.GetInstanceList(pou_infos, name, debug)) > 0
        return False

    def GenerateProgram(self, filepath=None):
        errors = []
        warnings = []
        if self.Project is not None:
            try:
                self.ProgramChunks = GenerateCurrentProgram(self, self.Project, errors, warnings)
                self.NextCompiledProject = self.Copy(self.Project)
                program_text = "".join([item[0] for item in self.ProgramChunks])
                if filepath is not None:
                    programfile = open(filepath, "w")
                    programfile.write(program_text.encode("utf-8"))
                    programfile.close()
                    self.ProgramFilePath = filepath
                return program_text, errors, warnings
            except PLCGenException as ex:
                errors.append(ex)
        else:
            errors.append("No project opened")
        return "", errors, warnings

    def DebugAvailable(self):
        return self.CurrentCompiledProject is not None

    def ProgramTransferred(self):
        if self.NextCompiledProject is None:
            self.CurrentCompiledProject = self.NextCompiledProject
        else:
            self.CurrentCompiledProject = self.Copy(self.Project)

    def GetChunkInfos(self, from_location, to_location):
        row = self.ProgramOffset + 1
        col = 1
        infos = []
        for chunk, chunk_infos in self.ProgramChunks:
            lines = chunk.split("\n")
            if len(lines) > 1:
                next_row = row + len(lines) - 1
                next_col = len(lines[-1]) + 1
            else:
                next_row = row
                next_col = col + len(chunk)
            if (next_row > from_location[0] or next_row == from_location[0] and next_col >= from_location[1]) and len(chunk_infos) > 0:
                infos.append((chunk_infos, (row, col)))
            if next_row == to_location[0] and next_col > to_location[1] or next_row > to_location[0]:
                return infos
            row, col = next_row, next_col
        return infos

    # -------------------------------------------------------------------------------
    #                        Project Pous management functions
    # -------------------------------------------------------------------------------

    # Add a Data Type to Project
    def ProjectAddDataType(self, datatype_name=None):
        if self.Project is not None:
            if datatype_name is None:
                datatype_name = self.GenerateNewName(None, None, "datatype%d")
            # Add the datatype to project
            self.Project.appenddataType(datatype_name)
            self.BufferProject()
            return ComputeDataTypeName(datatype_name)
        return None

    # Remove a Data Type from project
    def ProjectRemoveDataType(self, datatype_name):
        if self.Project is not None:
            self.Project.removedataType(datatype_name)
            self.BufferProject()

    # Add a Pou to Project
    def ProjectAddPou(self, pou_name, pou_type, body_type):
        if self.Project is not None:
            # Add the pou to project
            self.Project.appendpou(pou_name, pou_type, body_type)
            if pou_type == "function":
                self.SetPouInterfaceReturnType(pou_name, "BOOL")
            self.BufferProject()
            return ComputePouName(pou_name)
        return None

    def ProjectChangePouType(self, name, pou_type):
        if self.Project is not None:
            pou = self.Project.getpou(name)
            if pou is not None:
                pou.setpouType(pou_type)
                self.BufferProject()

    def GetPouXml(self, pou_name):
        if self.Project is not None:
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                return pou.tostring()
        return None

    def PastePou(self, pou_type, pou_xml):
        '''
        Adds the POU defined by 'pou_xml' to the current project with type 'pou_type'
        '''
        try:
            new_pou, error = LoadPou(pou_xml)
        except Exception:
            error = ""
        if error is not None:
            return _("Couldn't paste non-POU object.")

        name = new_pou.getname()

        idx = 0
        new_name = name
        while self.Project.getpou(new_name) is not None:
            # a POU with that name already exists.
            # make a new name and test if a POU with that name exists.
            # append an incrementing numeric suffix to the POU name.
            idx += 1
            new_name = "%s%d" % (name, idx)

        # we've found a name that does not already exist, use it
        new_pou.setname(new_name)

        if pou_type is not None:
            orig_type = new_pou.getpouType()

            # prevent violations of POU content restrictions:
            # function blocks cannot be pasted as functions,
            # programs cannot be pasted as functions or function blocks
            if orig_type == 'functionBlock' and pou_type == 'function' or \
               orig_type == 'program' and pou_type in ['function', 'functionBlock']:
                msg = _('''{a1} "{a2}" can't be pasted as a {a3}.''').format(a1=orig_type, a2=name, a3=pou_type)
                return msg

            new_pou.setpouType(pou_type)

        self.Project.insertpou(0, new_pou)
        self.BufferProject()

        return ComputePouName(new_name),

    # Remove a Pou from project
    def ProjectRemovePou(self, pou_name):
        if self.Project is not None:
            self.Project.removepou(pou_name)
            self.BufferProject()

    # Return the name of the configuration if only one exist
    def GetProjectMainConfigurationName(self):
        if self.Project is not None:
            # Found the configuration corresponding to old name and change its name to new name
            configurations = self.Project.getconfigurations()
            if len(configurations) == 1:
                return configurations[0].getname()
        return None

    # Add a configuration to Project
    def ProjectAddConfiguration(self, config_name=None):
        if self.Project is not None:
            if config_name is None:
                config_name = self.GenerateNewName(None, None, "configuration%d")
            self.Project.addconfiguration(config_name)
            self.BufferProject()
            return ComputeConfigurationName(config_name)
        return None

    # Remove a configuration from project
    def ProjectRemoveConfiguration(self, config_name):
        if self.Project is not None:
            self.Project.removeconfiguration(config_name)
            self.BufferProject()

    # Add a resource to a configuration of the Project
    def ProjectAddConfigurationResource(self, config_name, resource_name=None):
        if self.Project is not None:
            if resource_name is None:
                resource_name = self.GenerateNewName(None, None, "resource%d")
            self.Project.addconfigurationResource(config_name, resource_name)
            self.BufferProject()
            return ComputeConfigurationResourceName(config_name, resource_name)
        return None

    # Remove a resource from a configuration of the project
    def ProjectRemoveConfigurationResource(self, config_name, resource_name):
        if self.Project is not None:
            self.Project.removeconfigurationResource(config_name, resource_name)
            self.BufferProject()

    # Add a Transition to a Project Pou
    def ProjectAddPouTransition(self, pou_name, transition_name, transition_type):
        if self.Project is not None:
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                pou.addtransition(transition_name, transition_type)
                self.BufferProject()
                return ComputePouTransitionName(pou_name, transition_name)
        return None

    # Remove a Transition from a Project Pou
    def ProjectRemovePouTransition(self, pou_name, transition_name):
        # Search if the pou removed is currently opened
        if self.Project is not None:
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                pou.removetransition(transition_name)
                self.BufferProject()

    # Add an Action to a Project Pou
    def ProjectAddPouAction(self, pou_name, action_name, action_type):
        if self.Project is not None:
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                pou.addaction(action_name, action_type)
                self.BufferProject()
                return ComputePouActionName(pou_name, action_name)
        return None

    # Remove an Action from a Project Pou
    def ProjectRemovePouAction(self, pou_name, action_name):
        # Search if the pou removed is currently opened
        if self.Project is not None:
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                pou.removeaction(action_name)
                self.BufferProject()

    # Change the name of a pou
    def ChangeDataTypeName(self, old_name, new_name):
        if self.Project is not None:
            # Found the pou corresponding to old name and change its name to new name
            datatype = self.Project.getdataType(old_name)
            if datatype is not None:
                datatype.setname(new_name)
                self.Project.updateElementName(old_name, new_name)
                self.BufferProject()

    # Change the name of a pou
    def ChangePouName(self, old_name, new_name):
        if self.Project is not None:
            # Found the pou corresponding to old name and change its name to new name
            pou = self.Project.getpou(old_name)
            if pou is not None:
                pou.setname(new_name)
                self.Project.updateElementName(old_name, new_name)
                self.BufferProject()

    # Change the name of a pou transition
    def ChangePouTransitionName(self, pou_name, old_name, new_name):
        if self.Project is not None:
            # Found the pou transition corresponding to old name and change its name to new name
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                transition = pou.gettransition(old_name)
                if transition is not None:
                    transition.setname(new_name)
                    pou.updateElementName(old_name, new_name)
                    self.BufferProject()

    # Change the name of a pou action
    def ChangePouActionName(self, pou_name, old_name, new_name):
        if self.Project is not None:
            # Found the pou action corresponding to old name and change its name to new name
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                action = pou.getaction(old_name)
                if action is not None:
                    action.setname(new_name)
                    pou.updateElementName(old_name, new_name)
                    self.BufferProject()

    # Change the name of a pou variable
    def ChangePouVariableName(self, pou_name, old_name, new_name):
        if self.Project is not None:
            # Found the pou action corresponding to old name and change its name to new name
            pou = self.Project.getpou(pou_name)
            if pou is not None:
                for _type, varlist in pou.getvars():
                    for var in varlist.getvariable():
                        if var.getname() == old_name:
                            var.setname(new_name)
                self.BufferProject()

    # Change the name of a configuration
    def ChangeConfigurationName(self, old_name, new_name):
        if self.Project is not None:
            # Found the configuration corresponding to old name and change its name to new name
            configuration = self.Project.getconfiguration(old_name)
            if configuration is not None:
                configuration.setname(new_name)
                self.BufferProject()

    # Change the name of a configuration resource
    def ChangeConfigurationResourceName(self, config_name, old_name, new_name):
        if self.Project is not None:
            # Found the resource corresponding to old name and change its name to new name
            resource = self.Project.getconfigurationResource(config_name, old_name)
            if resource is not None:
                resource.setname(new_name)
                self.BufferProject()

    # Return the description of the pou given by its name
    def GetPouDescription(self, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its type
            pou = project.getpou(name)
            if pou is not None:
                return pou.getdescription()
        return ""

    # Return the description of the pou given by its name
    def SetPouDescription(self, name, description, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its type
            pou = project.getpou(name)
            if pou is not None:
                pou.setdescription(description)
                self.BufferProject()

    # Return the type of the pou given by its name
    def GetPouType(self, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its type
            pou = project.getpou(name)
            if pou is not None:
                return pou.getpouType()
        return None

    # Return pous with SFC language
    def GetSFCPous(self, debug=False):
        list = []
        project = self.GetProject(debug)
        if project is not None:
            for pou in project.getpous():
                if pou.getBodyType() == "SFC":
                    list.append(pou.getname())
        return list

    # Return the body language of the pou given by its name
    def GetPouBodyType(self, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its body language
            pou = project.getpou(name)
            if pou is not None:
                return pou.getbodyType()
        return None

    # Return the actions of a pou
    def GetPouTransitions(self, pou_name, debug=False):
        transitions = []
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its transitions if SFC
            pou = project.getpou(pou_name)
            if pou is not None and pou.getbodyType() == "SFC":
                for transition in pou.gettransitionList():
                    transitions.append(transition.getname())
        return transitions

    # Return the body language of the transition given by its name
    def GetTransitionBodyType(self, pou_name, pou_transition, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name
            pou = project.getpou(pou_name)
            if pou is not None:
                # Found the pou transition correponding to name and return its body language
                transition = pou.gettransition(pou_transition)
                if transition is not None:
                    return transition.getbodyType()
        return None

    # Return the actions of a pou
    def GetPouActions(self, pou_name, debug=False):
        actions = []
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its actions if SFC
            pou = project.getpou(pou_name)
            if pou.getbodyType() == "SFC":
                for action in pou.getactionList():
                    actions.append(action.getname())
        return actions

    # Return the body language of the pou given by its name
    def GetActionBodyType(self, pou_name, pou_action, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the pou correponding to name and return its body language
            pou = project.getpou(pou_name)
            if pou is not None:
                action = pou.getaction(pou_action)
                if action is not None:
                    return action.getbodyType()
        return None

    # Extract varlists from a list of vars
    def ExtractVarLists(self, vars):
        varlist_list = []
        current_varlist = None
        current_type = None
        for var in vars:
            next_type = (var.Class,
                         var.Option,
                         var.Location in ["", None] or
                         # When declaring globals, located
                         # and not located variables are
                         # in the same declaration block
                         var.Class == "Global")
            if current_type != next_type:
                current_type = next_type
                infos = VAR_CLASS_INFOS.get(var.Class, None)
                if infos is not None:
                    current_varlist = PLCOpenParser.CreateElement(infos[0], "interface")
                else:
                    current_varlist = PLCOpenParser.CreateElement("varList")
                varlist_list.append((var.Class, current_varlist))
                if var.Option == "Constant":
                    current_varlist.setconstant(True)
                elif var.Option == "Retain":
                    current_varlist.setretain(True)
                elif var.Option == "Non-Retain":
                    current_varlist.setnonretain(True)
            # Create variable and change its properties
            tempvar = PLCOpenParser.CreateElement("variable", "varListPlain")
            tempvar.setname(var.Name)

            var_type = PLCOpenParser.CreateElement("type", "variable")
            if isinstance(var.Type, tuple):
                if var.Type[0] == "array":
                    _array_type, base_type_name, dimensions = var.Type
                    array = PLCOpenParser.CreateElement("array", "dataType")
                    baseType = PLCOpenParser.CreateElement("baseType", "array")
                    array.setbaseType(baseType)
                    for i, dimension in enumerate(dimensions):
                        dimension_range = PLCOpenParser.CreateElement("dimension", "array")
                        if i == 0:
                            array.setdimension([dimension_range])
                        else:
                            array.appenddimension(dimension_range)
                        dimension_range.setlower(dimension[0])
                        dimension_range.setupper(dimension[1])
                    if base_type_name in self.GetBaseTypes():
                        baseType.setcontent(PLCOpenParser.CreateElement(
                            base_type_name.lower()
                            if base_type_name in ["STRING", "WSTRING"]
                            else base_type_name, "dataType"))
                    else:
                        derived_datatype = PLCOpenParser.CreateElement("derived", "dataType")
                        derived_datatype.setname(base_type_name)
                        baseType.setcontent(derived_datatype)
                    var_type.setcontent(array)
            elif var.Type in self.GetBaseTypes():
                var_type.setcontent(PLCOpenParser.CreateElement(
                    var.Type.lower()
                    if var.Type in ["STRING", "WSTRING"]
                    else var.Type, "dataType"))
            else:
                derived_type = PLCOpenParser.CreateElement("derived", "dataType")
                derived_type.setname(var.Type)
                var_type.setcontent(derived_type)
            tempvar.settype(var_type)

            if var.InitialValue != "":
                value = PLCOpenParser.CreateElement("initialValue", "variable")
                value.setvalue(var.InitialValue)
                tempvar.setinitialValue(value)
            if var.Location != "":
                tempvar.setaddress(var.Location)
            else:
                tempvar.setaddress(None)
            if var.Documentation != "":
                ft = PLCOpenParser.CreateElement("documentation", "variable")
                ft.setanyText(var.Documentation)
                tempvar.setdocumentation(ft)

            # Add variable to varList
            current_varlist.appendvariable(tempvar)
        return varlist_list

    def GetVariableDictionary(self, object_with_vars, tree=False, debug=False):
        variables = []
        self.VariableInfoCollector.Collect(object_with_vars,
                                           debug, variables, tree)
        return variables

    # Add a global var to configuration to configuration
    def AddConfigurationGlobalVar(self, config_name, var_type, var_name,
                                  location="", description=""):
        if self.Project is not None:
            # Found the configuration corresponding to name
            configuration = self.Project.getconfiguration(config_name)
            if configuration is not None:
                # Set configuration global vars
                configuration.addglobalVar(
                    self.GetVarTypeObject(var_type),
                    var_name, location, description)

    # Replace the configuration globalvars by those given
    def SetConfigurationGlobalVars(self, name, vars):
        if self.Project is not None:
            # Found the configuration corresponding to name
            configuration = self.Project.getconfiguration(name)
            if configuration is not None:
                # Set configuration global vars
                configuration.setglobalVars([
                    varlist for _vartype, varlist
                    in self.ExtractVarLists(vars)])

    # Return the configuration globalvars
    def GetConfigurationGlobalVars(self, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the configuration corresponding to name
            configuration = project.getconfiguration(name)
            if configuration is not None:
                # Extract variables defined in configuration
                return self.GetVariableDictionary(configuration, debug)

        return []

    # Return configuration variable names
    def GetConfigurationVariableNames(self, config_name=None, debug=False):
        variables = []
        project = self.GetProject(debug)
        if project is not None:
            for configuration in self.Project.getconfigurations():
                if config_name is None or config_name == configuration.getname():
                    variables.extend(
                        [var.getname() for var in reduce(
                            lambda x, y: x + y, [
                                varlist.getvariable()
                                for varlist in configuration.globalVars],
                            [])])
        return variables

    # Replace the resource globalvars by those given
    def SetConfigurationResourceGlobalVars(self, config_name, name, vars):
        if self.Project is not None:
            # Found the resource corresponding to name
            resource = self.Project.getconfigurationResource(config_name, name)
            # Set resource global vars
            if resource is not None:
                resource.setglobalVars([
                    varlist for _vartype, varlist
                    in self.ExtractVarLists(vars)])

    # Return the resource globalvars
    def GetConfigurationResourceGlobalVars(self, config_name, name, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            # Found the resource corresponding to name
            resource = project.getconfigurationResource(config_name, name)
            if resource is not None:
                # Extract variables defined in configuration
                return self.GetVariableDictionary(resource, debug)

        return []

    # Return resource variable names
    def GetConfigurationResourceVariableNames(
            self, config_name=None, resource_name=None, debug=False):
        variables = []
        project = self.GetProject(debug)
        if project is not None:
            for configuration in self.Project.getconfigurations():
                if config_name is None or config_name == configuration.getname():
                    for resource in configuration.getresource():
                        if resource_name is None or resource.getname() == resource_name:
                            variables.extend(
                                [var.getname() for var in reduce(
                                    lambda x, y: x + y, [
                                        varlist.getvariable()
                                        for varlist in resource.globalVars],
                                    [])])
        return variables

    # Return the interface for the given pou
    def GetPouInterfaceVars(self, pou, tree=False, debug=False):
        interface = pou.interface
        # Verify that the pou has an interface
        if interface is not None:
            # Extract variables defined in interface
            return self.GetVariableDictionary(interface, tree, debug)
        return []

    # Replace the Pou interface by the one given
    def SetPouInterfaceVars(self, name, vars):
        if self.Project is not None:
            # Found the pou corresponding to name and add interface if there isn't one yet
            pou = self.Project.getpou(name)
            if pou is not None:
                if pou.interface is None:
                    pou.interface = PLCOpenParser.CreateElement("interface", "pou")
                # Set Pou interface
                pou.setvars([varlist for _varlist_type, varlist in self.ExtractVarLists(vars)])

    # Replace the return type of the pou given by its name (only for functions)
    def SetPouInterfaceReturnType(self, name, return_type):
        if self.Project is not None:
            pou = self.Project.getpou(name)
            if pou is not None:
                if pou.interface is None:
                    pou.interface = PLCOpenParser.CreateElement("interface", "pou")
                # If there isn't any return type yet, add it
                return_type_obj = pou.interface.getreturnType()
                if return_type_obj is None:
                    return_type_obj = PLCOpenParser.CreateElement("returnType", "interface")
                    pou.interface.setreturnType(return_type_obj)
                # Change return type
                if return_type in self.GetBaseTypes():
                    return_type_obj.setcontent(PLCOpenParser.CreateElement(
                        return_type.lower()
                        if return_type in ["STRING", "WSTRING"]
                        else return_type, "dataType"))
                else:
                    derived_type = PLCOpenParser.CreateElement("derived", "dataType")
                    derived_type.setname(return_type)
                    return_type_obj.setcontent(derived_type)

    def UpdateProjectUsedPous(self, old_name, new_name):
        if self.Project is not None:
            self.Project.updateElementName(old_name, new_name)

    def UpdateEditedElementUsedVariable(self, tagname, old_name, new_name):
        pou = self.GetEditedElement(tagname)
        if pou is not None:
            pou.updateElementName(old_name, new_name)

    # Return the return type of the given pou
    def GetPouInterfaceReturnType(self, pou, tree=False, debug=False):
        # Verify that the pou has an interface
        if pou.interface is not None:
            # Return the return type if there is one
            return_type = pou.interface.getreturnType()
            if return_type is not None:
                factory = self.VariableInfoCollector.Collect(return_type,
                                                             debug, [], tree)
                if tree:
                    return [factory.GetType(), factory.GetTree()]
                return factory.GetType()

        if tree:
            return [None, ([], [])]
        return None

    # Function that add a new confnode to the confnode list
    def AddConfNodeTypesList(self, typeslist):
        self.ConfNodeTypes.extend(typeslist)
        addedcat = [{"name": _("%s POUs") % confnodetypes["name"],
                     "list": [pou.getblockInfos()
                              for pou in confnodetypes["types"].getpous()]}
                    for confnodetypes in typeslist]
        self.TotalTypes.extend(addedcat)
        for cat in addedcat:
            for desc in cat["list"]:
                BlkLst = self.TotalTypesDict.setdefault(desc["name"], [])
                BlkLst.append((section["name"], desc))

    # Function that clear the confnode list
    def ClearConfNodeTypes(self):
        self.ConfNodeTypes = []
        self.TotalTypesDict = StdBlckDct.copy()
        self.TotalTypes = StdBlckLst[:]

    def GetConfNodeDataTypes(self, exclude=None, only_locatables=False):
        return [{"name": _("%s Data Types") % confnodetypes["name"],
                 "list": [
                     datatype.getname()
                     for datatype in confnodetypes["types"].getdataTypes()
                     if not only_locatables or self.IsLocatableDataType(datatype)]}
                for confnodetypes in self.ConfNodeTypes]

    def GetVariableLocationTree(self):
        return []

    def GetConfNodeGlobalInstances(self):
        return []

    def GetConfigurationExtraVariables(self):
        global_vars = []
        for var_name, var_type, var_initial in self.GetConfNodeGlobalInstances():
            tempvar = PLCOpenParser.CreateElement("variable", "globalVars")
            tempvar.setname(var_name)

            tempvartype = PLCOpenParser.CreateElement("type", "variable")
            if var_type in self.GetBaseTypes():
                tempvartype.setcontent(PLCOpenParser.CreateElement(
                    var_type.lower()
                    if var_type in ["STRING", "WSTRING"]
                    else var_type, "dataType"))
            else:
                tempderivedtype = PLCOpenParser.CreateElement("derived", "dataType")
                tempderivedtype.setname(var_type)
                tempvartype.setcontent(tempderivedtype)
            tempvar.settype(tempvartype)

            if var_initial != "":
                value = PLCOpenParser.CreateElement("initialValue", "variable")
                value.setvalue(var_initial)
                tempvar.setinitialValue(value)

            global_vars.append(tempvar)
        return global_vars

    # Function that returns the block definition associated to the block type given
    def GetBlockType(self, typename, inputs=None, debug=False):
        result_blocktype = {}
        for _sectioname, blocktype in self.TotalTypesDict.get(typename, []):
            if inputs is not None and inputs != "undefined":
                block_inputs = tuple([var_type for _name, var_type, _modifier in blocktype["inputs"]])
                if reduce(lambda x, y: x and y, map(lambda x: x[0] == "ANY" or self.IsOfType(*x), zip(inputs, block_inputs)), True):
                    return blocktype
            else:
                if result_blocktype:
                    if inputs == "undefined":
                        return None
                    else:
                        result_blocktype["inputs"] = [(i[0], "ANY", i[2]) for i in result_blocktype["inputs"]]
                        result_blocktype["outputs"] = [(o[0], "ANY", o[2]) for o in result_blocktype["outputs"]]
                        return result_blocktype
                result_blocktype = blocktype.copy()
        if result_blocktype:
            return result_blocktype
        project = self.GetProject(debug)
        if project is not None:
            blocktype = project.getpou(typename)
            if blocktype is not None:
                blocktype_infos = blocktype.getblockInfos()
                if inputs in [None, "undefined"]:
                    return blocktype_infos

                if inputs == tuple([var_type
                                    for _name, var_type, _modifier in blocktype_infos["inputs"]]):
                    return blocktype_infos

        return None

    # Return Block types checking for recursion
    def GetBlockTypes(self, tagname="", debug=False):
        words = tagname.split("::")
        name = None
        project = self.GetProject(debug)
        if project is not None:
            pou_type = None
            if words[0] in ["P", "T", "A"]:
                name = words[1]
                pou_type = self.GetPouType(name, debug)
            filter = (["function"]
                      if pou_type == "function" or words[0] == "T"
                      else ["functionBlock", "function"])
            blocktypes = [
                {"name": category["name"],
                 "list": [block for block in category["list"]
                          if block["type"] in filter]}
                for category in self.TotalTypes]
            blocktypes.append({
                "name": USER_DEFINED_POUS,
                "list": [pou.getblockInfos()
                         for pou in project.getpous(name, filter)
                         if (name is None or
                             len(self.GetInstanceList(pou, name, debug)) == 0)]
            })
            return blocktypes
        return self.TotalTypes

    # Return Function Block types checking for recursion
    def GetFunctionBlockTypes(self, tagname="", debug=False):
        project = self.GetProject(debug)
        words = tagname.split("::")
        name = None
        if project is not None and words[0] in ["P", "T", "A"]:
            name = words[1]
        blocktypes = []
        for blocks in self.TotalTypesDict.itervalues():
            for _sectioname, block in blocks:
                if block["type"] == "functionBlock":
                    blocktypes.append(block["name"])
        if project is not None:
            blocktypes.extend([
                pou.getname()
                for pou in project.getpous(name, ["functionBlock"])
                if (name is None or
                    len(self.GetInstanceList(pou, name, debug)) == 0)])
        return blocktypes

    # Return Block types checking for recursion
    def GetBlockResource(self, debug=False):
        blocktypes = []
        for category in StdBlckLst[:-1]:
            for blocktype in category["list"]:
                if blocktype["type"] == "program":
                    blocktypes.append(blocktype["name"])
        project = self.GetProject(debug)
        if project is not None:
            blocktypes.extend(
                [pou.getname()
                 for pou in project.getpous(filter=["program"])])
        return blocktypes

    # Return Data Types checking for recursion
    def GetDataTypes(self, tagname="", basetypes=True, confnodetypes=True, only_locatables=False, debug=False):
        if basetypes:
            datatypes = self.GetBaseTypes()
        else:
            datatypes = []
        project = self.GetProject(debug)
        name = None
        if project is not None:
            words = tagname.split("::")
            if words[0] in ["D"]:
                name = words[1]
            datatypes.extend([
                datatype.getname()
                for datatype in project.getdataTypes(name)
                if ((not only_locatables or self.IsLocatableDataType(datatype, debug)) and
                    (name is None or len(self.GetInstanceList(datatype, name, debug)) == 0))])
        if confnodetypes:
            for category in self.GetConfNodeDataTypes(name, only_locatables):
                datatypes.extend(category["list"])
        return datatypes

    # Return Data Type Object
    def GetPou(self, typename, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            result = project.getpou(typename)
            if result is not None:
                return result
        for standardlibrary in StdBlckLibs.values():
            result = standardlibrary.getpou(typename)
            if result is not None:
                return result
        for confnodetype in self.ConfNodeTypes:
            result = confnodetype["types"].getpou(typename)
            if result is not None:
                return result
        return None

    # Return Data Type Object
    def GetDataType(self, typename, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            result = project.getdataType(typename)
            if result is not None:
                return result
        for confnodetype in self.ConfNodeTypes:
            result = confnodetype["types"].getdataType(typename)
            if result is not None:
                return result
        return None

    # Return Data Type Object Base Type
    def GetDataTypeBaseType(self, datatype):
        basetype_content = datatype.baseType.getcontent()
        basetype_content_type = basetype_content.getLocalTag()
        if basetype_content_type in ["array", "subrangeSigned", "subrangeUnsigned"]:
            basetype = basetype_content.baseType.getcontent()
            basetype_type = basetype.getLocalTag()
            return (basetype.getname() if basetype_type == "derived"
                    else basetype_type.upper())
        return (basetype_content.getname() if basetype_content_type == "derived"
                else basetype_content_type.upper())

    # Return Base Type of given possible derived type
    def GetBaseType(self, typename, debug=False):
        if typename in TypeHierarchy:
            return typename

        datatype = self.GetDataType(typename, debug)
        if datatype is not None:
            basetype = self.GetDataTypeBaseType(datatype)
            if basetype is not None:
                return self.GetBaseType(basetype, debug)
            return typename

        return None

    def GetBaseTypes(self):
        '''
        return the list of datatypes defined in IEC 61131-3.
        TypeHierarchy_list has a rough order to it (e.g. SINT, INT, DINT, ...),
        which makes it easy for a user to find a type in a menu.
        '''
        return [x for x, _y in TypeHierarchy_list if not x.startswith("ANY")]

    def IsOfType(self, typename, reference, debug=False):
        if reference is None or typename == reference:
            return True

        basetype = TypeHierarchy.get(typename)
        if basetype is not None:
            return self.IsOfType(basetype, reference)

        datatype = self.GetDataType(typename, debug)
        if datatype is not None:
            basetype = self.GetDataTypeBaseType(datatype)
            if basetype is not None:
                return self.IsOfType(basetype, reference, debug)

        return False

    def IsEndType(self, typename):
        if typename is not None:
            return not typename.startswith("ANY")
        return True

    def IsLocatableDataType(self, datatype, debug=False):
        basetype_content = datatype.baseType.getcontent()
        basetype_content_type = basetype_content.getLocalTag()
        if basetype_content_type in ["enum", "struct"]:
            return False
        elif basetype_content_type == "derived":
            return self.IsLocatableType(basetype_content.getname())
        elif basetype_content_type == "array":
            array_base_type = basetype_content.baseType.getcontent()
            if array_base_type.getLocalTag() == "derived":
                return self.IsLocatableType(array_base_type.getname(), debug)
        return True

    def IsLocatableType(self, typename, debug=False):
        if isinstance(typename, tuple) or self.GetBlockType(typename) is not None:
            return False

        # the size of these types is implementation dependend
        if typename in ["TIME", "DATE", "DT", "TOD"]:
            return False

        datatype = self.GetDataType(typename, debug)
        if datatype is not None:
            return self.IsLocatableDataType(datatype)
        return True

    def IsEnumeratedType(self, typename, debug=False):
        if isinstance(typename, tuple):
            typename = typename[1]
        datatype = self.GetDataType(typename, debug)
        if datatype is not None:
            basetype_content = datatype.baseType.getcontent()
            basetype_content_type = basetype_content.getLocalTag()
            if basetype_content_type == "derived":
                return self.IsEnumeratedType(basetype_content_type, debug)
            return basetype_content_type == "enum"
        return False

    def IsSubrangeType(self, typename, exclude=None, debug=False):
        if typename == exclude:
            return False
        if isinstance(typename, tuple):
            typename = typename[1]
        datatype = self.GetDataType(typename, debug)
        if datatype is not None:
            basetype_content = datatype.baseType.getcontent()
            basetype_content_type = basetype_content.getLocalTag()
            if basetype_content_type == "derived":
                return self.IsSubrangeType(basetype_content_type, exclude, debug)
            elif basetype_content_type in ["subrangeSigned", "subrangeUnsigned"]:
                return not self.IsOfType(
                    self.GetDataTypeBaseType(datatype), exclude)
        return False

    def IsNumType(self, typename, debug=False):
        return self.IsOfType(typename, "ANY_NUM", debug) or\
               self.IsOfType(typename, "ANY_BIT", debug)

    def GetDataTypeRange(self, typename, debug=False):
        range = DataTypeRange.get(typename)
        if range is not None:
            return range
        datatype = self.GetDataType(typename, debug)
        if datatype is not None:
            basetype_content = datatype.baseType.getcontent()
            basetype_content_type = basetype_content.getLocalTag()
            if basetype_content_type in ["subrangeSigned", "subrangeUnsigned"]:
                return (basetype_content.range.getlower(),
                        basetype_content.range.getupper())
            elif basetype_content_type == "derived":
                return self.GetDataTypeRange(basetype_content.getname(), debug)
        return None

    # Return Subrange types
    def GetSubrangeBaseTypes(self, exclude, debug=False):
        subrange_basetypes = DataTypeRange.keys()
        project = self.GetProject(debug)
        if project is not None:
            subrange_basetypes.extend(
                [datatype.getname() for datatype in project.getdataTypes()
                 if self.IsSubrangeType(datatype.getname(), exclude, debug)])
        for confnodetype in self.ConfNodeTypes:
            subrange_basetypes.extend(
                [datatype.getname() for datatype in confnodetype["types"].getdataTypes()
                 if self.IsSubrangeType(datatype.getname(), exclude, debug)])
        return subrange_basetypes

    # Return Enumerated Values
    def GetEnumeratedDataValues(self, typename=None, debug=False):
        values = []
        if typename is not None:
            datatype_obj = self.GetDataType(typename, debug)
            if datatype_obj is not None:
                basetype_content = datatype_obj.baseType.getcontent()
                basetype_content_type = basetype_content.getLocalTag()
                if basetype_content_type == "enum":
                    return [value.getname()
                            for value in basetype_content.xpath(
                                "ppx:values/ppx:value",
                                namespaces=PLCOpenParser.NSMAP)]
                elif basetype_content_type == "derived":
                    return self.GetEnumeratedDataValues(basetype_content.getname(), debug)
        else:
            project = self.GetProject(debug)
            if project is not None:
                values.extend(project.GetEnumeratedDataTypeValues())
            for confnodetype in self.ConfNodeTypes:
                values.extend(confnodetype["types"].GetEnumeratedDataTypeValues())
        return values

    # -------------------------------------------------------------------------------
    #                    Project opened Data types management functions
    # -------------------------------------------------------------------------------

    # Return the data type informations
    def GetDataTypeInfos(self, tagname, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            words = tagname.split("::")
            if words[0] == "D":
                infos = {}
                datatype = project.getdataType(words[1])
                if datatype is None:
                    return None
                basetype_content = datatype.baseType.getcontent()
                basetype_content_type = basetype_content.getLocalTag()
                if basetype_content_type in ["subrangeSigned", "subrangeUnsigned"]:
                    infos["type"] = "Subrange"
                    infos["min"] = basetype_content.range.getlower()
                    infos["max"] = basetype_content.range.getupper()
                    base_type = basetype_content.baseType.getcontent()
                    base_type_type = base_type.getLocalTag()
                    infos["base_type"] = (base_type.getname()
                                          if base_type_type == "derived"
                                          else base_type_type)
                elif basetype_content_type == "enum":
                    infos["type"] = "Enumerated"
                    infos["values"] = []
                    for value in basetype_content.xpath("ppx:values/ppx:value", namespaces=PLCOpenParser.NSMAP):
                        infos["values"].append(value.getname())
                elif basetype_content_type == "array":
                    infos["type"] = "Array"
                    infos["dimensions"] = []
                    for dimension in basetype_content.getdimension():
                        infos["dimensions"].append((dimension.getlower(), dimension.getupper()))
                    base_type = basetype_content.baseType.getcontent()
                    base_type_type = base_type.getLocalTag()
                    infos["base_type"] = (base_type.getname()
                                          if base_type_type == "derived"
                                          else base_type_type.upper())
                elif basetype_content_type == "struct":
                    infos["type"] = "Structure"
                    infos["elements"] = []
                    for element in basetype_content.getvariable():
                        element_infos = {}
                        element_infos["Name"] = element.getname()
                        element_type = element.type.getcontent()
                        element_type_type = element_type.getLocalTag()
                        if element_type_type == "array":
                            dimensions = []
                            for dimension in element_type.getdimension():
                                dimensions.append((dimension.getlower(), dimension.getupper()))
                            base_type = element_type.baseType.getcontent()
                            base_type_type = base_type.getLocalTag()
                            element_infos["Type"] = ("array",
                                                     base_type.getname()
                                                     if base_type_type == "derived"
                                                     else base_type_type.upper(),
                                                     dimensions)
                        elif element_type_type == "derived":
                            element_infos["Type"] = element_type.getname()
                        else:
                            element_infos["Type"] = element_type_type.upper()
                        if element.initialValue is not None:
                            element_infos["Initial Value"] = element.initialValue.getvalue()
                        else:
                            element_infos["Initial Value"] = ""
                        infos["elements"].append(element_infos)
                else:
                    infos["type"] = "Directly"
                    infos["base_type"] = (basetype_content.getname()
                                          if basetype_content_type == "derived"
                                          else basetype_content_type.upper())

                if datatype.initialValue is not None:
                    infos["initial"] = datatype.initialValue.getvalue()
                else:
                    infos["initial"] = ""
                return infos
        return None

    # Change the data type informations
    def SetDataTypeInfos(self, tagname, infos):
        words = tagname.split("::")
        if self.Project is not None and words[0] == "D":
            datatype = self.Project.getdataType(words[1])
            if infos["type"] == "Directly":
                if infos["base_type"] in self.GetBaseTypes():
                    datatype.baseType.setcontent(PLCOpenParser.CreateElement(
                        infos["base_type"].lower()
                        if infos["base_type"] in ["STRING", "WSTRING"]
                        else infos["base_type"], "dataType"))
                else:
                    derived_datatype = PLCOpenParser.CreateElement("derived", "dataType")
                    derived_datatype.setname(infos["base_type"])
                    datatype.baseType.setcontent(derived_datatype)
            elif infos["type"] == "Subrange":
                subrange = PLCOpenParser.CreateElement(
                    "subrangeUnsigned"
                    if infos["base_type"] in GetSubTypes("ANY_UINT")
                    else "subrangeSigned", "dataType")
                datatype.baseType.setcontent(subrange)
                subrange.range.setlower(infos["min"])
                subrange.range.setupper(infos["max"])
                if infos["base_type"] in self.GetBaseTypes():
                    subrange.baseType.setcontent(
                        PLCOpenParser.CreateElement(infos["base_type"], "dataType"))
                else:
                    derived_datatype = PLCOpenParser.CreateElement("derived", "dataType")
                    derived_datatype.setname(infos["base_type"])
                    subrange.baseType.setcontent(derived_datatype)
            elif infos["type"] == "Enumerated":
                enumerated = PLCOpenParser.CreateElement("enum", "dataType")
                datatype.baseType.setcontent(enumerated)
                values = PLCOpenParser.CreateElement("values", "enum")
                enumerated.setvalues(values)
                for i, enum_value in enumerate(infos["values"]):
                    value = PLCOpenParser.CreateElement("value", "values")
                    value.setname(enum_value)
                    if i == 0:
                        values.setvalue([value])
                    else:
                        values.appendvalue(value)
            elif infos["type"] == "Array":
                array = PLCOpenParser.CreateElement("array", "dataType")
                datatype.baseType.setcontent(array)
                for i, dimension in enumerate(infos["dimensions"]):
                    dimension_range = PLCOpenParser.CreateElement("dimension", "array")
                    dimension_range.setlower(dimension[0])
                    dimension_range.setupper(dimension[1])
                    if i == 0:
                        array.setdimension([dimension_range])
                    else:
                        array.appenddimension(dimension_range)
                if infos["base_type"] in self.GetBaseTypes():
                    array.baseType.setcontent(PLCOpenParser.CreateElement(
                        infos["base_type"].lower()
                        if infos["base_type"] in ["STRING", "WSTRING"]
                        else infos["base_type"], "dataType"))
                else:
                    derived_datatype = PLCOpenParser.CreateElement("derived", "dataType")
                    derived_datatype.setname(infos["base_type"])
                    array.baseType.setcontent(derived_datatype)
            elif infos["type"] == "Structure":
                struct = PLCOpenParser.CreateElement("struct", "dataType")
                datatype.baseType.setcontent(struct)
                for i, element_infos in enumerate(infos["elements"]):
                    element = PLCOpenParser.CreateElement("variable", "struct")
                    element.setname(element_infos["Name"])
                    element_type = PLCOpenParser.CreateElement("type", "variable")
                    if isinstance(element_infos["Type"], tuple):
                        if element_infos["Type"][0] == "array":
                            _array_type, base_type_name, dimensions = element_infos["Type"]
                            array = PLCOpenParser.CreateElement("array", "dataType")
                            baseType = PLCOpenParser.CreateElement("baseType", "array")
                            array.setbaseType(baseType)
                            element_type.setcontent(array)
                            for j, dimension in enumerate(dimensions):
                                dimension_range = PLCOpenParser.CreateElement("dimension", "array")
                                dimension_range.setlower(dimension[0])
                                dimension_range.setupper(dimension[1])
                                if j == 0:
                                    array.setdimension([dimension_range])
                                else:
                                    array.appenddimension(dimension_range)
                            if base_type_name in self.GetBaseTypes():
                                baseType.setcontent(PLCOpenParser.CreateElement(
                                    base_type_name.lower()
                                    if base_type_name in ["STRING", "WSTRING"]
                                    else base_type_name, "dataType"))
                            else:
                                derived_datatype = PLCOpenParser.CreateElement("derived", "dataType")
                                derived_datatype.setname(base_type_name)
                                array.baseType.setcontent(derived_datatype)
                    elif element_infos["Type"] in self.GetBaseTypes():
                        element_type.setcontent(
                            PLCOpenParser.CreateElement(
                                element_infos["Type"].lower()
                                if element_infos["Type"] in ["STRING", "WSTRING"]
                                else element_infos["Type"], "dataType"))
                    else:
                        derived_datatype = PLCOpenParser.CreateElement("derived", "dataType")
                        derived_datatype.setname(element_infos["Type"])
                        element_type.setcontent(derived_datatype)
                    element.settype(element_type)
                    if element_infos["Initial Value"] != "":
                        value = PLCOpenParser.CreateElement("initialValue", "variable")
                        value.setvalue(element_infos["Initial Value"])
                        element.setinitialValue(value)
                    if i == 0:
                        struct.setvariable([element])
                    else:
                        struct.appendvariable(element)
            if infos["initial"] != "":
                if datatype.initialValue is None:
                    datatype.initialValue = PLCOpenParser.CreateElement("initialValue", "dataType")
                datatype.initialValue.setvalue(infos["initial"])
            else:
                datatype.initialValue = None
            self.BufferProject()

    # -------------------------------------------------------------------------------
    #                       Project opened Pous management functions
    # -------------------------------------------------------------------------------

    # Return edited element
    def GetEditedElement(self, tagname, debug=False):
        project = self.GetProject(debug)
        if project is not None:
            words = tagname.split("::")
            if words[0] == "D":
                return project.getdataType(words[1])
            elif words[0] == "P":
                return project.getpou(words[1])
            elif words[0] in ['T', 'A']:
                pou = project.getpou(words[1])
                if pou is not None:
                    if words[0] == 'T':
                        return pou.gettransition(words[2])
                    elif words[0] == 'A':
                        return pou.getaction(words[2])
            elif words[0] == 'C':
                return project.getconfiguration(words[1])
            elif words[0] == 'R':
                return project.getconfigurationResource(words[1], words[2])
        return None

    # Return edited element name
    def GetEditedElementName(self, tagname):
        words = tagname.split("::")
        if words[0] in ["P", "C", "D"]:
            return words[1]
        else:
            return words[2]
        return None

    # Return edited element name and type
    def GetEditedElementType(self, tagname, debug=False):
        words = tagname.split("::")
        if words[0] in ["P", "T", "A"]:
            return words[1], self.GetPouType(words[1], debug)
        return None, None

    # Return language in which edited element is written
    def GetEditedElementBodyType(self, tagname, debug=False):
        words = tagname.split("::")
        if words[0] == "P":
            return self.GetPouBodyType(words[1], debug)
        elif words[0] == 'T':
            return self.GetTransitionBodyType(words[1], words[2], debug)
        elif words[0] == 'A':
            return self.GetActionBodyType(words[1], words[2], debug)
        return None

    # Return the edited element variables
    def GetEditedElementInterfaceVars(self, tagname, tree=False, debug=False):
        words = tagname.split("::")
        if words[0] in ["P", "T", "A"]:
            project = self.GetProject(debug)
            if project is not None:
                pou = project.getpou(words[1])
                if pou is not None:
                    return self.GetPouInterfaceVars(pou, tree, debug)
        return []

    # Return the edited element return type
    def GetEditedElementInterfaceReturnType(self, tagname, tree=False, debug=False):
        words = tagname.split("::")
        if words[0] == "P":
            project = self.GetProject(debug)
            if project is not None:
                pou = self.Project.getpou(words[1])
                if pou is not None:
                    return self.GetPouInterfaceReturnType(pou, tree, debug)
        elif words[0] == 'T':
            return ["BOOL", ([], [])]
        return None

    # Change the edited element text
    def SetEditedElementText(self, tagname, text):
        if self.Project is not None:
            element = self.GetEditedElement(tagname)
            if element is not None:
                element.settext(text)

    # Return the edited element text
    def GetEditedElementText(self, tagname, debug=False):
        element = self.GetEditedElement(tagname, debug)
        if element is not None:
            return element.gettext()
        return ""

    # Return the edited element transitions
    def GetEditedElementTransitions(self, tagname, debug=False):
        pou = self.GetEditedElement(tagname, debug)
        if pou is not None and pou.getbodyType() == "SFC":
            transitions = []
            for transition in pou.gettransitionList():
                transitions.append(transition.getname())
            return transitions
        return []

    # Return edited element transitions
    def GetEditedElementActions(self, tagname, debug=False):
        pou = self.GetEditedElement(tagname, debug)
        if pou is not None and pou.getbodyType() == "SFC":
            actions = []
            for action in pou.getactionList():
                actions.append(action.getname())
            return actions
        return []

    # Return the names of the pou elements
    def GetEditedElementVariables(self, tagname, debug=False):
        words = tagname.split("::")
        if words[0] in ["P", "T", "A"]:
            return self.GetProjectPouVariableNames(words[1], debug)
        elif words[0] in ["C", "R"]:
            names = self.GetConfigurationVariableNames(words[1], debug)
            if words[0] == "R":
                names.extend(self.GetConfigurationResourceVariableNames(
                    words[1], words[2], debug))
            return names
        return []

    def GetEditedElementCopy(self, tagname, debug=False):
        element = self.GetEditedElement(tagname, debug)
        if element is not None:
            return element.tostring()
        return ""

    def GetEditedElementInstancesCopy(self, tagname, blocks_id=None, wires=None, debug=False):
        element = self.GetEditedElement(tagname, debug)
        text = ""
        if element is not None:
            wires = dict([(wire, True)
                          for wire in wires
                          if wire[0] in blocks_id and wire[1] in blocks_id])
            copy_body = PLCOpenParser.CreateElement("body", "pou")
            element.append(copy_body)
            copy_body.setcontent(
                PLCOpenParser.CreateElement(element.getbodyType(), "body"))
            for id in blocks_id:
                instance = element.getinstance(id)
                if instance is not None:
                    copy_body.appendcontentInstance(self.Copy(instance))
                    instance_copy = copy_body.getcontentInstance(id)
                    instance_copy.filterConnections(wires)
                    text += instance_copy.tostring()
            element.remove(copy_body)
        return text

    def GenerateNewName(self, tagname, name, format, start_idx=0, exclude=None, debug=False):
        if name is not None:
            result = re.search(VARIABLE_NAME_SUFFIX_MODEL, name)
            if result is not None:
                format = name[:result.start(1)] + '%d'
                start_idx = int(result.group(1))
            else:
                format = name + '%d'

        names = {} if exclude is None else exclude.copy()
        if tagname is not None:
            names.update(dict([(varname.upper(), True)
                               for varname in self.GetEditedElementVariables(tagname, debug)]))
            words = tagname.split("::")
            if words[0] in ["P", "T", "A"]:
                element = self.GetEditedElement(tagname, debug)
                if element is not None and element.getbodyType() not in ["ST", "IL"]:
                    for instance in element.getinstances():
                        if isinstance(
                                instance,
                                (PLCOpenParser.GetElementClass("step",         "sfcObjects"),
                                 PLCOpenParser.GetElementClass("connector",    "commonObjects"),
                                 PLCOpenParser.GetElementClass("continuation", "commonObjects"))):
                            names[instance.getname().upper()] = True
            elif words[0] == 'R':
                element = self.GetEditedElement(tagname, debug)
                for task in element.gettask():
                    names[task.getname().upper()] = True
                    for instance in task.getpouInstance():
                        names[instance.getname().upper()] = True
                for instance in element.getpouInstance():
                    names[instance.getname().upper()] = True
        else:
            project = self.GetProject(debug)
            if project is not None:
                for datatype in project.getdataTypes():
                    names[datatype.getname().upper()] = True
                for pou in project.getpous():
                    names[pou.getname().upper()] = True
                    for var in self.GetPouInterfaceVars(pou, debug=debug):
                        names[var.Name.upper()] = True
                    for transition in pou.gettransitionList():
                        names[transition.getname().upper()] = True
                    for action in pou.getactionList():
                        names[action.getname().upper()] = True
                for config in project.getconfigurations():
                    names[config.getname().upper()] = True
                    for resource in config.getresource():
                        names[resource.getname().upper()] = True

        i = start_idx
        while name is None or names.get(name.upper(), False):
            name = (format % i)
            i += 1
        return name

    def PasteEditedElementInstances(self, tagname, text, new_pos, middle=False, debug=False):
        element = self.GetEditedElement(tagname, debug)
        _element_name, element_type = self.GetEditedElementType(tagname, debug)
        if element is not None:
            bodytype = element.getbodyType()

            # Get edited element type scaling
            scaling = None
            project = self.GetProject(debug)
            if project is not None:
                properties = project.getcontentHeader()
                scaling = properties["scaling"][bodytype]

            # Get ids already by all the instances in edited element
            used_id = dict([(instance.getlocalId(), True) for instance in element.getinstances()])
            new_id = {}

            try:
                instances, error = LoadPouInstances(text, bodytype)
            except Exception:
                instances, error = [], ""
            if error is not None or len(instances) == 0:
                return _("Invalid plcopen element(s)!!!")

            exclude = {}
            for instance in instances:
                element.addinstance(instance)
                instance_type = instance.getLocalTag()
                if instance_type == "block":
                    blocktype = instance.gettypeName()
                    blocktype_infos = self.GetBlockType(blocktype)
                    blockname = instance.getinstanceName()
                    if blocktype_infos["type"] != "function" and blockname is not None:
                        if element_type == "function":
                            return _("FunctionBlock \"%s\" can't be pasted in a Function!!!") % blocktype
                        blockname = self.GenerateNewName(tagname,
                                                         blockname,
                                                         "%s%%d" % blocktype,
                                                         debug=debug)
                        exclude[blockname] = True
                        instance.setinstanceName(blockname)
                        self.AddEditedElementPouVar(tagname, blocktype, blockname)
                elif instance_type == "step":
                    stepname = self.GenerateNewName(tagname,
                                                    instance.getname(),
                                                    "Step%d",
                                                    exclude=exclude,
                                                    debug=debug)
                    exclude[stepname] = True
                    instance.setname(stepname)
                localid = instance.getlocalId()
                if localid not in used_id:
                    new_id[localid] = True

            idx = 1
            translate_id = {}
            bbox = rect()
            for instance in instances:
                localId = instance.getlocalId()
                bbox.union(instance.getBoundingBox())
                if localId in used_id:
                    while (idx in used_id) or (idx in new_id):
                        idx += 1
                    new_id[idx] = True
                    instance.setlocalId(idx)
                    translate_id[localId] = idx

            x, y, width, height = bbox.bounding_box()
            if middle:
                new_pos[0] -= width // 2
                new_pos[1] -= height // 2
            else:
                new_pos = map(lambda x: x + 30, new_pos)
            if scaling[0] != 0 and scaling[1] != 0:
                min_pos = map(lambda x: 30 / x, scaling)
                minx = round(min_pos[0])
                if int(min_pos[0]) == round(min_pos[0]):
                    minx += 1
                miny = round(min_pos[1])
                if int(min_pos[1]) == round(min_pos[1]):
                    miny += 1
                minx *= scaling[0]
                miny *= scaling[1]
                new_pos = (max(minx, round(new_pos[0] / scaling[0]) * scaling[0]),
                           max(miny, round(new_pos[1] / scaling[1]) * scaling[1]))
            else:
                new_pos = (max(30, new_pos[0]), max(30, new_pos[1]))
            diff = (int(new_pos[0] - x), int(new_pos[1] - y))

            connections = {}
            for instance in instances:
                connections.update(instance.updateConnectionsId(translate_id))
                if getattr(instance, "setexecutionOrderId", None) is not None:
                    instance.setexecutionOrderId(0)
                instance.translate(*diff)

            return new_id, connections

    def GetEditedElementInstancesInfos(self, tagname, debug=False):
        element = self.GetEditedElement(tagname, debug)
        if element is not None:
            return self.BlockInstanceCollector.Collect(element, debug)
        return {}

    def ClearEditedElementExecutionOrder(self, tagname):
        element = self.GetEditedElement(tagname)
        if element is not None:
            element.resetexecutionOrder()

    def ResetEditedElementExecutionOrder(self, tagname):
        element = self.GetEditedElement(tagname)
        if element is not None:
            element.compileexecutionOrder()

    def SetConnectionWires(self, connection, connector):
        wires = connector.GetWires()
        idx = 0
        for wire, handle in wires:
            points = wire.GetPoints(handle != 0)
            if handle == 0:
                result = wire.GetConnectedInfos(-1)
            else:
                result = wire.GetConnectedInfos(0)
            if result is not None:
                refLocalId, formalParameter = result
                connections = connection.getconnections()
                if connections is None or len(connection.getconnections()) <= idx:
                    connection.addconnection()
                connection.setconnectionId(idx, refLocalId)
                connection.setconnectionPoints(idx, points)
                if formalParameter != "":
                    connection.setconnectionParameter(idx, formalParameter)
                else:
                    connection.setconnectionParameter(idx, None)
                idx += 1

    def GetVarTypeObject(self, var_type):
        var_type_obj = PLCOpenParser.CreateElement("type", "variable")
        if not var_type.startswith("ANY") and TypeHierarchy.get(var_type):
            var_type_obj.setcontent(PLCOpenParser.CreateElement(
                var_type.lower() if var_type in ["STRING", "WSTRING"]
                else var_type, "dataType"))
        else:
            derived_type = PLCOpenParser.CreateElement("derived", "dataType")
            derived_type.setname(var_type)
            var_type_obj.setcontent(derived_type)
        return var_type_obj

    def AddEditedElementPouVar(self, tagname, var_type, name, **args):
        if self.Project is not None:
            words = tagname.split("::")
            if words[0] in ['P', 'T', 'A']:
                pou = self.Project.getpou(words[1])
                if pou is not None:
                    pou.addpouLocalVar(
                        self.GetVarTypeObject(var_type),
                        name, **args)

    def AddEditedElementPouExternalVar(self, tagname, var_type, name):
        if self.Project is not None:
            words = tagname.split("::")
            if words[0] in ['P', 'T', 'A']:
                pou = self.Project.getpou(words[1])
                if pou is not None:
                    pou.addpouExternalVar(
                        self.GetVarTypeObject(var_type), name)

    def ChangeEditedElementPouVar(self, tagname, old_type, old_name, new_type, new_name):
        if self.Project is not None:
            words = tagname.split("::")
            if words[0] in ['P', 'T', 'A']:
                pou = self.Project.getpou(words[1])
                if pou is not None:
                    pou.changepouVar(old_type, old_name, new_type, new_name)

    def RemoveEditedElementPouVar(self, tagname, type, name):
        if self.Project is not None:
            words = tagname.split("::")
            if words[0] in ['P', 'T', 'A']:
                pou = self.Project.getpou(words[1])
                if pou is not None:
                    pou.removepouVar(type, name)

    def AddEditedElementBlock(self, tagname, id, blocktype, blockname=None):
        element = self.GetEditedElement(tagname)
        if element is not None:
            block = PLCOpenParser.CreateElement("block", "fbdObjects")
            block.setlocalId(id)
            block.settypeName(blocktype)
            blocktype_infos = self.GetBlockType(blocktype)
            if blocktype_infos["type"] != "function" and blockname is not None:
                block.setinstanceName(blockname)
                self.AddEditedElementPouVar(tagname, blocktype, blockname)
            element.addinstance(block)

    def SetEditedElementBlockInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            block = element.getinstance(id)
            if block is None:
                return
            old_name = block.getinstanceName()
            old_type = block.gettypeName()
            new_name = infos.get("name", old_name)
            new_type = infos.get("type", old_type)
            if new_type != old_type:
                old_typeinfos = self.GetBlockType(old_type)
                new_typeinfos = self.GetBlockType(new_type)
                if old_typeinfos is None or new_typeinfos is None:
                    self.ChangeEditedElementPouVar(tagname, old_type, old_name, new_type, new_name)
                elif new_typeinfos["type"] != old_typeinfos["type"]:
                    if new_typeinfos["type"] == "function":
                        self.RemoveEditedElementPouVar(tagname, old_type, old_name)
                    else:
                        self.AddEditedElementPouVar(tagname, new_type, new_name)
                elif new_typeinfos["type"] != "function":
                    self.ChangeEditedElementPouVar(tagname, old_type, old_name, new_type, new_name)
            elif new_name != old_name:
                self.ChangeEditedElementPouVar(tagname, old_type, old_name, new_type, new_name)
            for param, value in infos.items():
                if param == "name":
                    if value != "":
                        block.setinstanceName(value)
                    else:
                        block.attrib.pop("instanceName", None)
                elif param == "type":
                    block.settypeName(value)
                elif param == "executionOrder" and block.getexecutionOrderId() != value:
                    element.setelementExecutionOrder(block, value)
                elif param == "height":
                    block.setheight(value)
                elif param == "width":
                    block.setwidth(value)
                elif param == "x":
                    block.setx(value)
                elif param == "y":
                    block.sety(value)
                elif param == "connectors":
                    block.inputVariables.setvariable([])
                    block.outputVariables.setvariable([])
                    for connector in value["inputs"]:
                        variable = PLCOpenParser.CreateElement("variable", "inputVariables")
                        block.inputVariables.appendvariable(variable)
                        variable.setformalParameter(connector.GetName())
                        if connector.IsNegated():
                            variable.setnegated(True)
                        if connector.GetEdge() != "none":
                            variable.setedge(connector.GetEdge())
                        position = connector.GetRelPosition()
                        variable.connectionPointIn.setrelPositionXY(position.x, position.y)
                        self.SetConnectionWires(variable.connectionPointIn, connector)
                    for connector in value["outputs"]:
                        variable = PLCOpenParser.CreateElement("variable", "outputVariables")
                        block.outputVariables.appendvariable(variable)
                        variable.setformalParameter(connector.GetName())
                        if connector.IsNegated():
                            variable.setnegated(True)
                        if connector.GetEdge() != "none":
                            variable.setedge(connector.GetEdge())
                        position = connector.GetRelPosition()
                        variable.addconnectionPointOut()
                        variable.connectionPointOut.setrelPositionXY(position.x, position.y)
            block.tostring()

    def AddEditedElementVariable(self, tagname, id, var_type):
        element = self.GetEditedElement(tagname)
        if element is not None:
            variable = PLCOpenParser.CreateElement(
                {INPUT: "inVariable",
                 OUTPUT: "outVariable",
                 INOUT: "inOutVariable"}[var_type], "fbdObjects")
            variable.setlocalId(id)
            element.addinstance(variable)

    def SetEditedElementVariableInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            variable = element.getinstance(id)
            if variable is None:
                return
            for param, value in infos.items():
                if param == "name":
                    variable.setexpression(value)
                elif param == "executionOrder" and variable.getexecutionOrderId() != value:
                    element.setelementExecutionOrder(variable, value)
                elif param == "height":
                    variable.setheight(value)
                elif param == "width":
                    variable.setwidth(value)
                elif param == "x":
                    variable.setx(value)
                elif param == "y":
                    variable.sety(value)
                elif param == "connectors":
                    if len(value["outputs"]) > 0:
                        output = value["outputs"][0]
                        if len(value["inputs"]) > 0:
                            variable.setnegatedOut(output.IsNegated())
                            variable.setedgeOut(output.GetEdge())
                        else:
                            variable.setnegated(output.IsNegated())
                            variable.setedge(output.GetEdge())
                        position = output.GetRelPosition()
                        variable.addconnectionPointOut()
                        variable.connectionPointOut.setrelPositionXY(position.x, position.y)
                    if len(value["inputs"]) > 0:
                        input = value["inputs"][0]
                        if len(value["outputs"]) > 0:
                            variable.setnegatedIn(input.IsNegated())
                            variable.setedgeIn(input.GetEdge())
                        else:
                            variable.setnegated(input.IsNegated())
                            variable.setedge(input.GetEdge())
                        position = input.GetRelPosition()
                        variable.addconnectionPointIn()
                        variable.connectionPointIn.setrelPositionXY(position.x, position.y)
                        self.SetConnectionWires(variable.connectionPointIn, input)

    def AddEditedElementConnection(self, tagname, id, connection_type):
        element = self.GetEditedElement(tagname)
        if element is not None:
            connection = PLCOpenParser.CreateElement(
                {CONNECTOR: "connector",
                 CONTINUATION: "continuation"}[connection_type], "commonObjects")
            connection.setlocalId(id)
            element.addinstance(connection)

    def SetEditedElementConnectionInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            connection = element.getinstance(id)
            if connection is None:
                return
            for param, value in infos.items():
                if param == "name":
                    connection.setname(value)
                elif param == "height":
                    connection.setheight(value)
                elif param == "width":
                    connection.setwidth(value)
                elif param == "x":
                    connection.setx(value)
                elif param == "y":
                    connection.sety(value)
                elif param == "connector":
                    position = value.GetRelPosition()
                    if isinstance(connection, PLCOpenParser.GetElementClass("continuation", "commonObjects")):
                        connection.addconnectionPointOut()
                        connection.connectionPointOut.setrelPositionXY(position.x, position.y)
                    elif isinstance(connection, PLCOpenParser.GetElementClass("connector", "commonObjects")):
                        connection.addconnectionPointIn()
                        connection.connectionPointIn.setrelPositionXY(position.x, position.y)
                        self.SetConnectionWires(connection.connectionPointIn, value)

    def AddEditedElementComment(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            comment = PLCOpenParser.CreateElement("comment", "commonObjects")
            comment.setlocalId(id)
            element.addinstance(comment)

    def SetEditedElementCommentInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            comment = element.getinstance(id)
            for param, value in infos.items():
                if param == "content":
                    comment.setcontentText(value)
                elif param == "height":
                    comment.setheight(value)
                elif param == "width":
                    comment.setwidth(value)
                elif param == "x":
                    comment.setx(value)
                elif param == "y":
                    comment.sety(value)

    def AddEditedElementPowerRail(self, tagname, id, powerrail_type):
        element = self.GetEditedElement(tagname)
        if element is not None:
            powerrail = PLCOpenParser.CreateElement(
                {LEFTRAIL: "leftPowerRail",
                 RIGHTRAIL: "rightPowerRail"}[powerrail_type], "ldObjects")
            powerrail.setlocalId(id)
            element.addinstance(powerrail)

    def SetEditedElementPowerRailInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            powerrail = element.getinstance(id)
            if powerrail is None:
                return
            for param, value in infos.items():
                if param == "height":
                    powerrail.setheight(value)
                elif param == "width":
                    powerrail.setwidth(value)
                elif param == "x":
                    powerrail.setx(value)
                elif param == "y":
                    powerrail.sety(value)
                elif param == "connectors":
                    if isinstance(powerrail, PLCOpenParser.GetElementClass("leftPowerRail", "ldObjects")):
                        powerrail.setconnectionPointOut([])
                        for connector in value["outputs"]:
                            position = connector.GetRelPosition()
                            connection = PLCOpenParser.CreateElement("connectionPointOut", "leftPowerRail")
                            powerrail.appendconnectionPointOut(connection)
                            connection.setrelPositionXY(position.x, position.y)
                    elif isinstance(powerrail, PLCOpenParser.GetElementClass("rightPowerRail", "ldObjects")):
                        powerrail.setconnectionPointIn([])
                        for connector in value["inputs"]:
                            position = connector.GetRelPosition()
                            connection = PLCOpenParser.CreateElement("connectionPointIn", "rightPowerRail")
                            powerrail.appendconnectionPointIn(connection)
                            connection.setrelPositionXY(position.x, position.y)
                            self.SetConnectionWires(connection, connector)

    def AddEditedElementContact(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            contact = PLCOpenParser.CreateElement("contact", "ldObjects")
            contact.setlocalId(id)
            element.addinstance(contact)

    def SetEditedElementContactInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            contact = element.getinstance(id)
            if contact is None:
                return
            for param, value in infos.items():
                if param == "name":
                    contact.setvariable(value)
                elif param == "type":
                    negated, edge = {
                        CONTACT_NORMAL: (False, "none"),
                        CONTACT_REVERSE: (True, "none"),
                        CONTACT_RISING: (False, "rising"),
                        CONTACT_FALLING: (False, "falling")}[value]
                    contact.setnegated(negated)
                    contact.setedge(edge)
                elif param == "height":
                    contact.setheight(value)
                elif param == "width":
                    contact.setwidth(value)
                elif param == "x":
                    contact.setx(value)
                elif param == "y":
                    contact.sety(value)
                elif param == "connectors":
                    input_connector = value["inputs"][0]
                    position = input_connector.GetRelPosition()
                    contact.addconnectionPointIn()
                    contact.connectionPointIn.setrelPositionXY(position.x, position.y)
                    self.SetConnectionWires(contact.connectionPointIn, input_connector)
                    output_connector = value["outputs"][0]
                    position = output_connector.GetRelPosition()
                    contact.addconnectionPointOut()
                    contact.connectionPointOut.setrelPositionXY(position.x, position.y)

    def AddEditedElementCoil(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            coil = PLCOpenParser.CreateElement("coil", "ldObjects")
            coil.setlocalId(id)
            element.addinstance(coil)

    def SetEditedElementCoilInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            coil = element.getinstance(id)
            if coil is None:
                return
            for param, value in infos.items():
                if param == "name":
                    coil.setvariable(value)
                elif param == "type":
                    negated, storage, edge = {
                        COIL_NORMAL: (False, "none", "none"),
                        COIL_REVERSE: (True, "none", "none"),
                        COIL_SET: (False, "set", "none"),
                        COIL_RESET: (False, "reset", "none"),
                        COIL_RISING: (False, "none", "rising"),
                        COIL_FALLING: (False, "none", "falling")}[value]
                    coil.setnegated(negated)
                    coil.setstorage(storage)
                    coil.setedge(edge)
                elif param == "height":
                    coil.setheight(value)
                elif param == "width":
                    coil.setwidth(value)
                elif param == "x":
                    coil.setx(value)
                elif param == "y":
                    coil.sety(value)
                elif param == "connectors":
                    input_connector = value["inputs"][0]
                    position = input_connector.GetRelPosition()
                    coil.addconnectionPointIn()
                    coil.connectionPointIn.setrelPositionXY(position.x, position.y)
                    self.SetConnectionWires(coil.connectionPointIn, input_connector)
                    output_connector = value["outputs"][0]
                    position = output_connector.GetRelPosition()
                    coil.addconnectionPointOut()
                    coil.connectionPointOut.setrelPositionXY(position.x, position.y)

    def AddEditedElementStep(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            step = PLCOpenParser.CreateElement("step", "sfcObjects")
            step.setlocalId(id)
            element.addinstance(step)

    def SetEditedElementStepInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            step = element.getinstance(id)
            if step is None:
                return
            for param, value in infos.items():
                if param == "name":
                    step.setname(value)
                elif param == "initial":
                    step.setinitialStep(value)
                elif param == "height":
                    step.setheight(value)
                elif param == "width":
                    step.setwidth(value)
                elif param == "x":
                    step.setx(value)
                elif param == "y":
                    step.sety(value)
                elif param == "connectors":
                    if len(value["inputs"]) > 0:
                        input_connector = value["inputs"][0]
                        position = input_connector.GetRelPosition()
                        step.addconnectionPointIn()
                        step.connectionPointIn.setrelPositionXY(position.x, position.y)
                        self.SetConnectionWires(step.connectionPointIn, input_connector)
                    else:
                        step.deleteconnectionPointIn()
                    if len(value["outputs"]) > 0:
                        output_connector = value["outputs"][0]
                        position = output_connector.GetRelPosition()
                        step.addconnectionPointOut()
                        step.connectionPointOut.setrelPositionXY(position.x, position.y)
                    else:
                        step.deleteconnectionPointOut()
                elif param == "action":
                    if value:
                        position = value.GetRelPosition()
                        step.addconnectionPointOutAction()
                        step.connectionPointOutAction.setrelPositionXY(position.x, position.y)
                    else:
                        step.deleteconnectionPointOutAction()

    def AddEditedElementTransition(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            transition = PLCOpenParser.CreateElement("transition", "sfcObjects")
            transition.setlocalId(id)
            element.addinstance(transition)

    def SetEditedElementTransitionInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            transition = element.getinstance(id)
            if transition is None:
                return
            for param, value in infos.items():
                if param == "type" and value != "connection":
                    transition.setconditionContent(value, infos["condition"])
                elif param == "height":
                    transition.setheight(value)
                elif param == "width":
                    transition.setwidth(value)
                elif param == "x":
                    transition.setx(value)
                elif param == "y":
                    transition.sety(value)
                elif param == "priority":
                    if value != 0:
                        transition.setpriority(value)
                    else:
                        transition.setpriority(None)
                elif param == "connectors":
                    input_connector = value["inputs"][0]
                    position = input_connector.GetRelPosition()
                    transition.addconnectionPointIn()
                    transition.connectionPointIn.setrelPositionXY(position.x, position.y)
                    self.SetConnectionWires(transition.connectionPointIn, input_connector)
                    output_connector = value["outputs"][0]
                    position = output_connector.GetRelPosition()
                    transition.addconnectionPointOut()
                    transition.connectionPointOut.setrelPositionXY(position.x, position.y)
                elif infos.get("type", None) == "connection" and param == "connection" and value:
                    transition.setconditionContent("connection", None)
                    self.SetConnectionWires(transition.condition.content, value)

    def AddEditedElementDivergence(self, tagname, id, divergence_type):
        element = self.GetEditedElement(tagname)
        if element is not None:
            divergence = PLCOpenParser.CreateElement(
                {SELECTION_DIVERGENCE: "selectionDivergence",
                 SELECTION_CONVERGENCE: "selectionConvergence",
                 SIMULTANEOUS_DIVERGENCE: "simultaneousDivergence",
                 SIMULTANEOUS_CONVERGENCE: "simultaneousConvergence"}.get(
                     divergence_type), "sfcObjects")
            divergence.setlocalId(id)
            element.addinstance(divergence)

    DivergenceTypes = [
        (divergence_type,
         PLCOpenParser.GetElementClass(divergence_type, "sfcObjects"))
        for divergence_type in ["selectionDivergence", "simultaneousDivergence",
                                "selectionConvergence", "simultaneousConvergence"]]

    def GetDivergenceType(self, divergence):
        for divergence_type, divergence_class in self.DivergenceTypes:
            if isinstance(divergence, divergence_class):
                return divergence_type
        return None

    def SetEditedElementDivergenceInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            divergence = element.getinstance(id)
            if divergence is None:
                return
            for param, value in infos.items():
                if param == "height":
                    divergence.setheight(value)
                elif param == "width":
                    divergence.setwidth(value)
                elif param == "x":
                    divergence.setx(value)
                elif param == "y":
                    divergence.sety(value)
                elif param == "connectors":
                    input_connectors = value["inputs"]
                    divergence_type = self.GetDivergenceType(divergence)
                    if divergence_type in ["selectionDivergence", "simultaneousDivergence"]:
                        position = input_connectors[0].GetRelPosition()
                        divergence.addconnectionPointIn()
                        divergence.connectionPointIn.setrelPositionXY(position.x, position.y)
                        self.SetConnectionWires(divergence.connectionPointIn, input_connectors[0])
                    else:
                        divergence.setconnectionPointIn([])
                        for input_connector in input_connectors:
                            position = input_connector.GetRelPosition()
                            connection = PLCOpenParser.CreateElement("connectionPointIn", divergence_type)
                            divergence.appendconnectionPointIn(connection)
                            connection.setrelPositionXY(position.x, position.y)
                            self.SetConnectionWires(connection, input_connector)
                    output_connectors = value["outputs"]
                    if divergence_type in ["selectionConvergence", "simultaneousConvergence"]:
                        position = output_connectors[0].GetRelPosition()
                        divergence.addconnectionPointOut()
                        divergence.connectionPointOut.setrelPositionXY(position.x, position.y)
                    else:
                        divergence.setconnectionPointOut([])
                        for output_connector in output_connectors:
                            position = output_connector.GetRelPosition()
                            connection = PLCOpenParser.CreateElement("connectionPointOut", divergence_type)
                            divergence.appendconnectionPointOut(connection)
                            connection.setrelPositionXY(position.x, position.y)

    def AddEditedElementJump(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            jump = PLCOpenParser.CreateElement("jumpStep", "sfcObjects")
            jump.setlocalId(id)
            element.addinstance(jump)

    def SetEditedElementJumpInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            jump = element.getinstance(id)
            if jump is None:
                return
            for param, value in infos.items():
                if param == "target":
                    jump.settargetName(value)
                elif param == "height":
                    jump.setheight(value)
                elif param == "width":
                    jump.setwidth(value)
                elif param == "x":
                    jump.setx(value)
                elif param == "y":
                    jump.sety(value)
                elif param == "connector":
                    position = value.GetRelPosition()
                    jump.addconnectionPointIn()
                    jump.connectionPointIn.setrelPositionXY(position.x, position.y)
                    self.SetConnectionWires(jump.connectionPointIn, value)

    def AddEditedElementActionBlock(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            actionBlock = PLCOpenParser.CreateElement("actionBlock", "commonObjects")
            actionBlock.setlocalId(id)
            element.addinstance(actionBlock)

    def SetEditedElementActionBlockInfos(self, tagname, id, infos):
        element = self.GetEditedElement(tagname)
        if element is not None:
            actionBlock = element.getinstance(id)
            if actionBlock is None:
                return
            for param, value in infos.items():
                if param == "actions":
                    actionBlock.setactions(value)
                elif param == "height":
                    actionBlock.setheight(value)
                elif param == "width":
                    actionBlock.setwidth(value)
                elif param == "x":
                    actionBlock.setx(value)
                elif param == "y":
                    actionBlock.sety(value)
                elif param == "connector":
                    position = value.GetRelPosition()
                    actionBlock.addconnectionPointIn()
                    actionBlock.connectionPointIn.setrelPositionXY(position.x, position.y)
                    self.SetConnectionWires(actionBlock.connectionPointIn, value)

    def RemoveEditedElementInstance(self, tagname, id):
        element = self.GetEditedElement(tagname)
        if element is not None:
            instance = element.getinstance(id)
            if isinstance(instance, PLCOpenParser.GetElementClass("block", "fbdObjects")):
                self.RemoveEditedElementPouVar(tagname, instance.gettypeName(), instance.getinstanceName())
            element.removeinstance(id)

    def GetEditedResourceVariables(self, tagname, debug=False):
        varlist = []
        words = tagname.split("::")
        for var in self.GetConfigurationGlobalVars(words[1], debug):
            if var.Type == "BOOL":
                varlist.append(var.Name)
        for var in self.GetConfigurationResourceGlobalVars(words[1], words[2], debug):
            if var.Type == "BOOL":
                varlist.append(var.Name)
        return varlist

    def SetEditedResourceInfos(self, tagname, tasks, instances):
        resource = self.GetEditedElement(tagname)
        if resource is not None:
            resource.settask([])
            resource.setpouInstance([])
            task_list = {}
            for task in tasks:
                new_task = PLCOpenParser.CreateElement("task", "resource")
                resource.appendtask(new_task)
                new_task.setname(task["Name"])
                if task["Triggering"] == "Interrupt":
                    new_task.setsingle(task["Single"])
#                result = duration_model.match(task["Interval"]).groups()
#                if reduce(lambda x, y: x or y != None, result):
#                    values = []
#                    for value in result[:-1]:
#                        if value != None:
#                            values.append(int(value))
#                        else:
#                            values.append(0)
#                    if result[-1] is not None:
#                        values.append(int(float(result[-1]) * 1000))
#                    new_task.setinterval(datetime.time(*values))
                if task["Triggering"] == "Cyclic":
                    new_task.setinterval(task["Interval"])
                new_task.setpriority(int(task["Priority"]))
                if task["Name"] != "":
                    task_list[task["Name"]] = new_task
            for instance in instances:
                task = task_list.get(instance["Task"])
                if task is not None:
                    new_instance = PLCOpenParser.CreateElement("pouInstance", "task")
                    task.appendpouInstance(new_instance)
                else:
                    new_instance = PLCOpenParser.CreateElement("pouInstance", "resource")
                    resource.appendpouInstance(new_instance)
                new_instance.setname(instance["Name"])
                new_instance.settypeName(instance["Type"])

    def GetEditedResourceInfos(self, tagname, debug=False):
        resource = self.GetEditedElement(tagname, debug)
        if resource is not None:
            tasks = resource.gettask()
            instances = resource.getpouInstance()
            tasks_data = []
            instances_data = []
            for task in tasks:
                new_task = {}
                new_task["Name"] = task.getname()
                single = task.getsingle()
                if single is not None:
                    new_task["Single"] = single
                else:
                    new_task["Single"] = ""
                interval = task.getinterval()
                if interval is not None:
                    # text = ""
                    # if interval.hour != 0:
                    #     text += "%dh"%interval.hour
                    # if interval.minute != 0:
                    #     text += "%dm"%interval.minute
                    # if interval.second != 0:
                    #     text += "%ds"%interval.second
                    # if interval.microsecond != 0:
                    #     if interval.microsecond % 1000 != 0:
                    #         text += "%.3fms"%(float(interval.microsecond) / 1000)
                    #     else:
                    #         text += "%dms"%(interval.microsecond / 1000)
                    # new_task["Interval"] = text
                    new_task["Interval"] = interval
                else:
                    new_task["Interval"] = ""
                if single is not None and interval is None:
                    new_task["Triggering"] = "Interrupt"
                elif interval is not None and single is None:
                    new_task["Triggering"] = "Cyclic"
                else:
                    new_task["Triggering"] = ""
                new_task["Priority"] = str(task.getpriority())
                tasks_data.append(new_task)
                for instance in task.getpouInstance():
                    new_instance = {}
                    new_instance["Name"] = instance.getname()
                    new_instance["Type"] = instance.gettypeName()
                    new_instance["Task"] = task.getname()
                    instances_data.append(new_instance)
            for instance in instances:
                new_instance = {}
                new_instance["Name"] = instance.getname()
                new_instance["Type"] = instance.gettypeName()
                new_instance["Task"] = ""
                instances_data.append(new_instance)
            return tasks_data, instances_data

    def OpenXMLFile(self, filepath):
        self.Project, error = LoadProject(filepath)
        if self.Project is None:
            return _("Project file syntax error:\n\n") + error
        self.SetFilePath(filepath)
        self.CreateProjectBuffer(True)
        self.ProgramChunks = []
        self.ProgramOffset = 0
        self.NextCompiledProject = self.Copy(self.Project)
        self.CurrentCompiledProject = None
        self.Buffering = False
        self.CurrentElementEditing = None
        return error

    def SaveXMLFile(self, filepath=None):
        if not filepath and self.FilePath == "":
            return False
        else:
            contentheader = {"modificationDateTime": datetime.datetime(*localtime()[:6])}
            self.Project.setcontentHeader(contentheader)

            if filepath:
                SaveProject(self.Project, filepath)
            else:
                SaveProject(self.Project, self.FilePath)

            self.MarkProjectAsSaved()
            if filepath:
                self.SetFilePath(filepath)
            return True

    # -------------------------------------------------------------------------------
    #                       Search in Current Project Functions
    # -------------------------------------------------------------------------------

    def SearchInProject(self, criteria):
        project_matches = self.Project.Search(criteria)
        ctn_matches = self.CTNSearch(criteria)
        return project_matches + ctn_matches

    def SearchInPou(self, tagname, criteria, debug=False):
        pou = self.GetEditedElement(tagname, debug)
        if pou is not None:
            search_results = pou.Search(criteria, [tagname])
            if tagname.split("::")[0] in ['A', 'T']:
                parent_pou_tagname = "P::%s" % (tagname.split("::")[-2])
                parent_pou = self.GetEditedElement(parent_pou_tagname, debug)
                for infos, start, end, text in parent_pou.Search(criteria):
                    if infos[1] in ["var_local", "var_input", "var_output", "var_inout"]:
                        search_results.append((infos, start, end, text))
            return search_results
        return []

    # -------------------------------------------------------------------------------
    #                      Current Buffering Management Functions
    # -------------------------------------------------------------------------------

    def Copy(self, model):
        """Return a copy of the project"""
        return deepcopy(model)

    def CreateProjectBuffer(self, saved):
        if self.ProjectBufferEnabled:
            self.ProjectBuffer = UndoBuffer(PLCOpenParser.Dumps(self.Project), saved)
        else:
            self.ProjectBuffer = None
            self.ProjectSaved = saved

    def IsProjectBufferEnabled(self):
        return self.ProjectBufferEnabled

    def EnableProjectBuffer(self, enable):
        self.ProjectBufferEnabled = enable
        if self.Project is not None:
            if enable:
                current_saved = self.ProjectSaved
            else:
                current_saved = self.ProjectBuffer.IsCurrentSaved()
            self.CreateProjectBuffer(current_saved)

    def BufferProject(self):
        if self.ProjectBuffer is not None:
            self.ProjectBuffer.Buffering(PLCOpenParser.Dumps(self.Project))
        else:
            self.ProjectSaved = False

    def StartBuffering(self):
        if self.ProjectBuffer is not None:
            self.Buffering = True
        else:
            self.ProjectSaved = False

    def EndBuffering(self):
        if self.ProjectBuffer is not None and self.Buffering:
            self.ProjectBuffer.Buffering(PLCOpenParser.Dumps(self.Project))
            self.Buffering = False

    def MarkProjectAsSaved(self):
        self.EndBuffering()
        if self.ProjectBuffer is not None:
            self.ProjectBuffer.CurrentSaved()
        else:
            self.ProjectSaved = True

    # Return if project is saved
    def ProjectIsSaved(self):
        if self.ProjectBuffer is not None:
            return self.ProjectBuffer.IsCurrentSaved() and not self.Buffering
        else:
            return self.ProjectSaved

    def LoadPrevious(self):
        self.EndBuffering()
        if self.ProjectBuffer is not None:
            self.Project = PLCOpenParser.Loads(self.ProjectBuffer.Previous())

    def LoadNext(self):
        if self.ProjectBuffer is not None:
            self.Project = PLCOpenParser.Loads(self.ProjectBuffer.Next())

    def GetBufferState(self):
        if self.ProjectBuffer is not None:
            first = self.ProjectBuffer.IsFirst() and not self.Buffering
            last = self.ProjectBuffer.IsLast()
            return not first, not last
        return False, False
