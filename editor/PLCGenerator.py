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


from __future__ import absolute_import
import re
from functools import reduce
from six.moves import xrange

from plcopen import PLCOpenParser
from plcopen.structures import *
from plcopen.types_enums import *


# Dictionary associating PLCOpen variable categories to the corresponding
# IEC 61131-3 variable categories
varTypeNames = {"localVars": "VAR", "tempVars": "VAR_TEMP", "inputVars": "VAR_INPUT",
                "outputVars": "VAR_OUTPUT", "inOutVars": "VAR_IN_OUT", "externalVars": "VAR_EXTERNAL",
                "globalVars": "VAR_GLOBAL", "accessVars": "VAR_ACCESS"}


# Dictionary associating PLCOpen POU categories to the corresponding
# IEC 61131-3 POU categories
pouTypeNames = {"function": "FUNCTION", "functionBlock": "FUNCTION_BLOCK", "program": "PROGRAM"}


errorVarTypes = {
    "VAR_INPUT": "var_input",
    "VAR_OUTPUT": "var_output",
    "VAR_INOUT": "var_inout",
}


def ReIndentText(text, nb_spaces):
    """ Helper function for reindenting text """
    compute = ""
    lines = text.splitlines()
    if len(lines) > 0:
        line_num = 0
        while line_num < len(lines) and len(lines[line_num].strip()) == 0:
            line_num += 1
        if line_num < len(lines):
            spaces = 0
            while lines[line_num][spaces] == " ":
                spaces += 1
            indent = ""
            for dummy in xrange(spaces, nb_spaces):
                indent += " "
            for line in lines:
                if line != "":
                    compute += "%s%s\n" % (indent, line)
                else:
                    compute += "\n"
    return compute


def SortInstances(a, b):
    ax, ay = int(a.getx()), int(a.gety())
    bx, by = int(b.getx()), int(b.gety())
    if abs(ay - by) < 10:
        return cmp(ax, bx)
    else:
        return cmp(ay, by)


def JoinList(separator, mylist):
    """ Helper for emulate join on element list """
    if len(mylist) > 0:
        return reduce(lambda x, y: x + separator + y, mylist)
    else:
        return mylist

# -------------------------------------------------------------------------------
#                  Specific exception for PLC generating errors
# -------------------------------------------------------------------------------


class PLCGenException(Exception):
    pass


# -------------------------------------------------------------------------------
#                           Generator of PLC program
# -------------------------------------------------------------------------------


class ProgramGenerator(object):

    # Create a new PCL program generator
    def __init__(self, controler, project, errors, warnings):
        # Keep reference of the controler and project
        self.Controler = controler
        self.Project = project
        # Reset the internal variables used to generate PLC programs
        self.Program = []
        self.DatatypeComputed = {}
        self.PouComputed = {}
        self.Errors = errors
        self.Warnings = warnings

    # Compute value according to type given
    def ComputeValue(self, value, var_type):
        base_type = self.Controler.GetBaseType(var_type)
        if base_type == "STRING" and not value.startswith("'") and not value.endswith("'"):
            return "'%s'" % value
        elif base_type == "WSTRING" and not value.startswith('"') and not value.endswith('"'):
            return "\"%s\"" % value
        return value

    # Generate a data type from its name
    def GenerateDataType(self, datatype_name):
        # Verify that data type hasn't been generated yet
        if not self.DatatypeComputed.get(datatype_name, True):
            # If not mark data type as computed
            self.DatatypeComputed[datatype_name] = True

            # Getting datatype model from project
            datatype = self.Project.getdataType(datatype_name)
            tagname = ComputeDataTypeName(datatype.getname())
            datatype_def = [("  ", ()),
                            (datatype.getname(), (tagname, "name")),
                            (" : ", ())]
            basetype_content = datatype.baseType.getcontent()
            basetype_content_type = basetype_content.getLocalTag()
            # Data type derived directly from a user defined type
            if basetype_content_type == "derived":
                basetype_name = basetype_content.getname()
                self.GenerateDataType(basetype_name)
                datatype_def += [(basetype_name, (tagname, "base"))]
            # Data type is a subrange
            elif basetype_content_type in ["subrangeSigned", "subrangeUnsigned"]:
                base_type = basetype_content.baseType.getcontent()
                base_type_type = base_type.getLocalTag()
                # Subrange derived directly from a user defined type
                if base_type_type == "derived":
                    basetype_name = base_type_type.getname()
                    self.GenerateDataType(basetype_name)
                # Subrange derived directly from an elementary type
                else:
                    basetype_name = base_type_type
                min_value = basetype_content.range.getlower()
                max_value = basetype_content.range.getupper()
                datatype_def += [(basetype_name, (tagname, "base")),
                                 (" (", ()),
                                 ("%s" % min_value, (tagname, "lower")),
                                 ("..", ()),
                                 ("%s" % max_value, (tagname, "upper")),
                                 (")", ())]
            # Data type is an enumerated type
            elif basetype_content_type == "enum":
                values = [[(value.getname(), (tagname, "value", i))]
                          for i, value in enumerate(
                              basetype_content.xpath("ppx:values/ppx:value",
                                                     namespaces=PLCOpenParser.NSMAP))]
                datatype_def += [("(", ())]
                datatype_def += JoinList([(", ", ())], values)
                datatype_def += [(")", ())]
            # Data type is an array
            elif basetype_content_type == "array":
                base_type = basetype_content.baseType.getcontent()
                base_type_type = base_type.getLocalTag()
                # Array derived directly from a user defined type
                if base_type_type == "derived":
                    basetype_name = base_type.getname()
                    self.GenerateDataType(basetype_name)
                # Array derived directly from an elementary type
                else:
                    basetype_name = base_type_type.upper()
                dimensions = [[("%s" % dimension.getlower(), (tagname, "range", i, "lower")),
                               ("..", ()),
                               ("%s" % dimension.getupper(), (tagname, "range", i, "upper"))]
                              for i, dimension in enumerate(basetype_content.getdimension())]
                datatype_def += [("ARRAY [", ())]
                datatype_def += JoinList([(",", ())], dimensions)
                datatype_def += [("] OF ", ()),
                                 (basetype_name, (tagname, "base"))]
            # Data type is a structure
            elif basetype_content_type == "struct":
                elements = []
                for i, element in enumerate(basetype_content.getvariable()):
                    element_type = element.type.getcontent()
                    element_type_type = element_type.getLocalTag()
                    # Structure element derived directly from a user defined type
                    if element_type_type == "derived":
                        elementtype_name = element_type.getname()
                        self.GenerateDataType(elementtype_name)
                    elif element_type_type == "array":
                        base_type = element_type.baseType.getcontent()
                        base_type_type = base_type.getLocalTag()
                        # Array derived directly from a user defined type
                        if base_type_type == "derived":
                            basetype_name = base_type.getname()
                            self.GenerateDataType(basetype_name)
                        # Array derived directly from an elementary type
                        else:
                            basetype_name = base_type_type.upper()
                        dimensions = ["%s..%s" % (dimension.getlower(), dimension.getupper())
                                      for dimension in element_type.getdimension()]
                        elementtype_name = "ARRAY [%s] OF %s" % (",".join(dimensions), basetype_name)
                    # Structure element derived directly from an elementary type
                    else:
                        elementtype_name = element_type_type.upper()
                    element_text = [("\n    ", ()),
                                    (element.getname(), (tagname, "struct", i, "name")),
                                    (" : ", ()),
                                    (elementtype_name, (tagname, "struct", i, "type"))]
                    if element.initialValue is not None:
                        element_text.extend([(" := ", ()),
                                             (self.ComputeValue(element.initialValue.getvalue(), elementtype_name), (tagname, "struct", i, "initial value"))])
                    element_text.append((";", ()))
                    elements.append(element_text)
                datatype_def += [("STRUCT", ())]
                datatype_def += JoinList([("", ())], elements)
                datatype_def += [("\n  END_STRUCT", ())]
            # Data type derived directly from a elementary type
            else:
                datatype_def += [(basetype_content_type.upper(), (tagname, "base"))]
            # Data type has an initial value
            if datatype.initialValue is not None:
                datatype_def += [(" := ", ()),
                                 (self.ComputeValue(datatype.initialValue.getvalue(), datatype_name), (tagname, "initial value"))]
            datatype_def += [(";\n", ())]
            self.Program += datatype_def

    # Generate a POU from its name
    def GeneratePouProgram(self, pou_name):
        # Verify that POU hasn't been generated yet
        if not self.PouComputed.get(pou_name, True):
            # If not mark POU as computed
            self.PouComputed[pou_name] = True

            # Getting POU model from project
            pou = self.Project.getpou(pou_name)
            pou_type = pou.getpouType()
            # Verify that POU type exists
            if pou_type in pouTypeNames:
                # Create a POU program generator
                pou_program = PouProgramGenerator(self, pou.getname(), pouTypeNames[pou_type], self.Errors, self.Warnings)
                program = pou_program.GenerateProgram(pou)
                self.Program += program
            else:
                raise PLCGenException(_("Undefined pou type \"%s\"") % pou_type)

    # Generate a POU defined and used in text
    def GeneratePouProgramInText(self, text):
        for pou_name in self.PouComputed.keys():
            model = re.compile("(?:^|[^0-9^A-Z])%s(?:$|[^0-9^A-Z])" % pou_name.upper())
            if model.search(text) is not None:
                self.GeneratePouProgram(pou_name)

    # Generate a configuration from its model
    def GenerateConfiguration(self, configuration):
        tagname = ComputeConfigurationName(configuration.getname())
        config = [("\nCONFIGURATION ", ()),
                  (configuration.getname(), (tagname, "name")),
                  ("\n", ())]
        var_number = 0

        varlists = [(varlist, varlist.getvariable()[:]) for varlist in configuration.getglobalVars()]

        extra_variables = self.Controler.GetConfigurationExtraVariables()
        extra_global_vars = None
        if len(extra_variables) > 0 and len(varlists) == 0:
            extra_global_vars = PLCOpenParser.CreateElement("globalVars", "interface")
            configuration.setglobalVars([extra_global_vars])
            varlists = [(extra_global_vars, [])]

        for variable in extra_variables:
            varlists[-1][0].appendvariable(variable)
            varlists[-1][1].append(variable)

        # Generate any global variable in configuration
        for varlist, varlist_variables in varlists:
            variable_type = errorVarTypes.get("VAR_GLOBAL", "var_local")
            # Generate variable block with modifier
            config += [("  VAR_GLOBAL", ())]
            if varlist.getconstant():
                config += [(" CONSTANT", (tagname, variable_type, (var_number, var_number + len(varlist.getvariable())), "constant"))]
            elif varlist.getretain():
                config += [(" RETAIN", (tagname, variable_type, (var_number, var_number + len(varlist.getvariable())), "retain"))]
            elif varlist.getnonretain():
                config += [(" NON_RETAIN", (tagname, variable_type, (var_number, var_number + len(varlist.getvariable())), "non_retain"))]
            config += [("\n", ())]
            # Generate any variable of this block
            for var in varlist_variables:
                vartype_content = var.gettype().getcontent()
                if vartype_content.getLocalTag() == "derived":
                    var_type = vartype_content.getname()
                    self.GenerateDataType(var_type)
                else:
                    var_type = var.gettypeAsText()

                config += [("    ", ()),
                           (var.getname(), (tagname, variable_type, var_number, "name")),
                           (" ", ())]
                # Generate variable address if exists
                address = var.getaddress()
                if address:
                    config += [("AT ", ()),
                               (address, (tagname, variable_type, var_number, "location")),
                               (" ", ())]
                config += [(": ", ()),
                           (var.gettypeAsText(), (tagname, variable_type, var_number, "type"))]
                # Generate variable initial value if exists
                initial = var.getinitialValue()
                if initial is not None:
                    config += [(" := ", ()),
                               (self.ComputeValue(initial.getvalue(), var_type), (tagname, variable_type, var_number, "initial value"))]
                config += [(";\n", ())]
                var_number += 1
            config += [("  END_VAR\n", ())]

        if extra_global_vars is not None:
            configuration.remove(extra_global_vars)
        else:
            for variable in extra_variables:
                varlists[-1][0].remove(variable)

        # Generate any resource in the configuration
        for resource in configuration.getresource():
            config += self.GenerateResource(resource, configuration.getname())
        config += [("END_CONFIGURATION\n", ())]
        return config

    # Generate a resource from its model
    def GenerateResource(self, resource, config_name):
        tagname = ComputeConfigurationResourceName(config_name, resource.getname())
        resrce = [("\n  RESOURCE ", ()),
                  (resource.getname(), (tagname, "name")),
                  (" ON PLC\n", ())]
        var_number = 0
        # Generate any global variable in configuration
        for varlist in resource.getglobalVars():
            variable_type = errorVarTypes.get("VAR_GLOBAL", "var_local")
            # Generate variable block with modifier
            resrce += [("    VAR_GLOBAL", ())]
            if varlist.getconstant():
                resrce += [(" CONSTANT", (tagname, variable_type, (var_number, var_number + len(varlist.getvariable())), "constant"))]
            elif varlist.getretain():
                resrce += [(" RETAIN", (tagname, variable_type, (var_number, var_number + len(varlist.getvariable())), "retain"))]
            elif varlist.getnonretain():
                resrce += [(" NON_RETAIN", (tagname, variable_type, (var_number, var_number + len(varlist.getvariable())), "non_retain"))]
            resrce += [("\n", ())]
            # Generate any variable of this block
            for var in varlist.getvariable():
                vartype_content = var.gettype().getcontent()
                if vartype_content.getLocalTag() == "derived":
                    var_type = vartype_content.getname()
                    self.GenerateDataType(var_type)
                else:
                    var_type = var.gettypeAsText()

                resrce += [("      ", ()),
                           (var.getname(), (tagname, variable_type, var_number, "name")),
                           (" ", ())]
                address = var.getaddress()
                # Generate variable address if exists
                if address:
                    resrce += [("AT ", ()),
                               (address, (tagname, variable_type, var_number, "location")),
                               (" ", ())]
                resrce += [(": ", ()),
                           (var.gettypeAsText(), (tagname, variable_type, var_number, "type"))]
                # Generate variable initial value if exists
                initial = var.getinitialValue()
                if initial is not None:
                    resrce += [(" := ", ()),
                               (self.ComputeValue(initial.getvalue(), var_type), (tagname, variable_type, var_number, "initial value"))]
                resrce += [(";\n", ())]
                var_number += 1
            resrce += [("    END_VAR\n", ())]
        # Generate any task in the resource
        tasks = resource.gettask()
        task_number = 0
        for task in tasks:
            # Task declaration
            resrce += [("    TASK ", ()),
                       (task.getname(), (tagname, "task", task_number, "name")),
                       ("(", ())]
            single = task.getsingle()
            # Single argument if exists
            if single is not None:
                if len(single) == 0:
                    raise PLCGenException(
                        _("Source signal has to be defined for single task '{a1}' in resource '{a2}.{a3}'.").
                        format(a1=task.getname(), a2=config_name, a3=resource.getname()))

                if single[0] == '[' and single[-1] == ']':
                    SNGLKW = "MULTI"
                else:
                    SNGLKW = "SINGLE"
                resrce += [(SNGLKW + " := ", ()),
                           (single, (tagname, "task", task_number, "single")),
                           (",", ())]
            # Interval argument if exists
            interval = task.getinterval()
            if interval is not None:
                resrce += [("INTERVAL := ", ()),
                           (interval, (tagname, "task", task_number, "interval")),
                           (",", ())]
#                resrce += [("INTERVAL := t#", ())]
#                if interval.hour != 0:
#                    resrce += [("%dh"%interval.hour, (tagname, "task", task_number, "interval", "hour"))]
#                if interval.minute != 0:
#                    resrce += [("%dm"%interval.minute, (tagname, "task", task_number, "interval", "minute"))]
#                if interval.second != 0:
#                    resrce += [("%ds"%interval.second, (tagname, "task", task_number, "interval", "second"))]
#                if interval.microsecond != 0:
#                    resrce += [("%dms"%(interval.microsecond / 1000), (tagname, "task", task_number, "interval", "millisecond"))]
#                resrce += [(",", ())]
            # Priority argument
            resrce += [("PRIORITY := ", ()),
                       ("%d" % task.getpriority(), (tagname, "task", task_number, "priority")),
                       (");\n", ())]
            task_number += 1
        instance_number = 0
        # Generate any program assign to each task
        for task in tasks:
            for instance in task.getpouInstance():
                resrce += [("    PROGRAM ", ()),
                           (instance.getname(), (tagname, "instance", instance_number, "name")),
                           (" WITH ", ()),
                           (task.getname(), (tagname, "instance", instance_number, "task")),
                           (" : ", ()),
                           (instance.gettypeName(), (tagname, "instance", instance_number, "type")),
                           (";\n", ())]
                instance_number += 1
        # Generate any program assign to no task
        for instance in resource.getpouInstance():
            resrce += [("    PROGRAM ", ()),
                       (instance.getname(),     (tagname, "instance", instance_number, "name")),
                       (" : ", ()),
                       (instance.gettypeName(), (tagname, "instance", instance_number, "type")),
                       (";\n", ())]
            instance_number += 1
        resrce += [("  END_RESOURCE\n", ())]
        return resrce

    # Generate the entire program for current project
    def GenerateProgram(self, log):
        log("Collecting data types")
        # Find all data types defined
        for datatype in self.Project.getdataTypes():
            self.DatatypeComputed[datatype.getname()] = False
        log("Collecting POUs")
        # Find all data types defined
        for pou in self.Project.getpous():
            self.PouComputed[pou.getname()] = False
        # Generate data type declaration structure if there is at least one data
        # type defined
        if len(self.DatatypeComputed) > 0:
            self.Program += [("TYPE\n", ())]
            # Generate every data types defined
            for datatype_name in self.DatatypeComputed.keys():
                log("Generate Data Type %s"%datatype_name)
                self.GenerateDataType(datatype_name)
            self.Program += [("END_TYPE\n\n", ())]
        # Generate every POUs defined
        for pou_name in self.PouComputed.keys():
            log("Generate POU %s"%pou_name)
            self.GeneratePouProgram(pou_name)
        # Generate every configurations defined
        log("Generate Config(s)")
        for config in self.Project.getconfigurations():
            self.Program += self.GenerateConfiguration(config)

    # Return generated program
    def GetGeneratedProgram(self):
        return self.Program


# -------------------------------------------------------------------------------
#                           Generator of POU programs
# -------------------------------------------------------------------------------

[ConnectorClass, ContinuationClass, ActionBlockClass] = [
    PLCOpenParser.GetElementClass(instance_name, "commonObjects")
    for instance_name in ["connector", "continuation", "actionBlock"]]
[InVariableClass, InOutVariableClass, OutVariableClass, BlockClass] = [
    PLCOpenParser.GetElementClass(instance_name, "fbdObjects")
    for instance_name in ["inVariable", "inOutVariable", "outVariable", "block"]]
[ContactClass, CoilClass, LeftPowerRailClass, RightPowerRailClass] = [
    PLCOpenParser.GetElementClass(instance_name, "ldObjects")
    for instance_name in ["contact", "coil", "leftPowerRail", "rightPowerRail"]]
[StepClass, TransitionClass, JumpStepClass,
 SelectionConvergenceClass, SelectionDivergenceClass,
 SimultaneousConvergenceClass, SimultaneousDivergenceClass] = [
     PLCOpenParser.GetElementClass(instance_name, "sfcObjects")
     for instance_name in ["step",
                           "transition",
                           "jumpStep",
                           "selectionConvergence",
                           "selectionDivergence",
                           "simultaneousConvergence",
                           "simultaneousDivergence"]]
TransitionObjClass = PLCOpenParser.GetElementClass("transition", "transitions")
ActionObjClass = PLCOpenParser.GetElementClass("action", "actions")


class PouProgramGenerator(object):

    # Create a new POU program generator
    def __init__(self, parent, name, type, errors, warnings):
        # Keep Reference to the parent generator
        self.ParentGenerator = parent
        self.Name = name
        self.Type = type
        self.TagName = ComputePouName(name)
        self.CurrentIndent = "  "
        self.ReturnType = None
        self.Interface = []
        self.InitialSteps = []
        self.ComputedBlocks = {}
        self.ComputedConnectors = {}
        self.ConnectionTypes = {}
        self.RelatedConnections = []
        self.SFCNetworks = {"Steps": {}, "Transitions": {}, "Actions": {}}
        self.SFCComputedBlocks = []
        self.ActionNumber = 0
        self.Program = []
        self.Errors = errors
        self.Warnings = warnings

    def GetBlockType(self, type, inputs=None):
        return self.ParentGenerator.Controler.GetBlockType(type, inputs)

    def IndentLeft(self):
        if len(self.CurrentIndent) >= 2:
            self.CurrentIndent = self.CurrentIndent[:-2]

    def IndentRight(self):
        self.CurrentIndent += "  "

    # Generator of unique ID for inline actions
    def GetActionNumber(self):
        self.ActionNumber += 1
        return self.ActionNumber

    # Test if a variable has already been defined
    def IsAlreadyDefined(self, name):
        for _list_type, _option, _located, vars in self.Interface:
            for _var_type, var_name, _var_address, _var_initial in vars:
                if name == var_name:
                    return True
        return False

    # Return the type of a variable defined in interface
    def GetVariableType(self, name):
        parts = name.split('.')
        current_type = None
        if len(parts) > 0:
            name = parts.pop(0)
            for _list_type, _option, _located, vars in self.Interface:
                for var_type, var_name, _var_address, _var_initial in vars:
                    if name == var_name:
                        current_type = var_type
                        break
            while current_type is not None and len(parts) > 0:
                blocktype = self.ParentGenerator.Controler.GetBlockType(current_type)
                if blocktype is not None:
                    name = parts.pop(0)
                    current_type = None
                    for var_name, var_type, _var_modifier in blocktype["inputs"] + blocktype["outputs"]:
                        if var_name == name:
                            current_type = var_type
                            break
                else:
                    tagname = ComputeDataTypeName(current_type)
                    infos = self.ParentGenerator.Controler.GetDataTypeInfos(tagname)
                    if infos is not None and infos["type"] == "Structure":
                        name = parts.pop(0)
                        current_type = None
                        for element in infos["elements"]:
                            if element["Name"] == name:
                                current_type = element["Type"]
                                break
        return current_type

    # Return connectors linked by a connection to the given connector
    def GetConnectedConnector(self, connector, body):
        links = connector.getconnections()
        if links is not None and len(links) == 1:
            return self.GetLinkedConnector(links[0], body)
        return None

    def GetLinkedConnector(self, link, body):
        parameter = link.getformalParameter()
        instance = body.getcontentInstance(link.getrefLocalId())
        if isinstance(instance, (InVariableClass, InOutVariableClass,
                                 ContinuationClass, ContactClass, CoilClass)):
            return instance.connectionPointOut
        elif isinstance(instance, BlockClass):
            outputvariables = instance.outputVariables.getvariable()
            if len(outputvariables) == 1:
                return outputvariables[0].connectionPointOut
            elif parameter:
                for variable in outputvariables:
                    if variable.getformalParameter() == parameter:
                        return variable.connectionPointOut
            else:
                point = link.getposition()[-1]
                for variable in outputvariables:
                    relposition = variable.connectionPointOut.getrelPositionXY()
                    blockposition = instance.getposition()
                    if point.x == blockposition.x + relposition[0] and point.y == blockposition.y + relposition[1]:
                        return variable.connectionPointOut
        elif isinstance(instance, LeftPowerRailClass):
            outputconnections = instance.getconnectionPointOut()
            if len(outputconnections) == 1:
                return outputconnections[0]
            else:
                point = link.getposition()[-1]
                for outputconnection in outputconnections:
                    relposition = outputconnection.getrelPositionXY()
                    powerrailposition = instance.getposition()
                    if point.x == powerrailposition.x + relposition[0] and point.y == powerrailposition.y + relposition[1]:
                        return outputconnection
        return None

    def ExtractRelatedConnections(self, connection):
        for i, related in enumerate(self.RelatedConnections):
            if connection in related:
                return self.RelatedConnections.pop(i)
        return [connection]

    def ComputeInterface(self, pou):
        interface = pou.getinterface()
        if interface is not None:
            if self.Type == "FUNCTION":
                returntype_content = interface.getreturnType()[0]
                returntype_content_type = returntype_content.getLocalTag()
                if returntype_content_type == "derived":
                    self.ReturnType = returntype_content.getname()
                else:
                    self.ReturnType = returntype_content_type.upper()
            for varlist in interface.getcontent():
                variables = []
                located = []
                varlist_type = varlist.getLocalTag()
                for var in varlist.getvariable():
                    vartype_content = var.gettype().getcontent()
                    if vartype_content.getLocalTag() == "derived":
                        var_type = vartype_content.getname()
                        blocktype = self.GetBlockType(var_type)
                        if blocktype is not None:
                            self.ParentGenerator.GeneratePouProgram(var_type)
                            variables.append((var_type, var.getname(), None, None))
                        else:
                            self.ParentGenerator.GenerateDataType(var_type)
                            initial = var.getinitialValue()
                            if initial is not None:
                                initial_value = initial.getvalue()
                            else:
                                initial_value = None
                            address = var.getaddress()
                            if address is not None:
                                located.append((vartype_content.getname(), var.getname(), address, initial_value))
                            else:
                                variables.append((vartype_content.getname(), var.getname(), None, initial_value))
                    else:
                        var_type = var.gettypeAsText()
                        initial = var.getinitialValue()
                        if initial is not None:
                            initial_value = initial.getvalue()
                        else:
                            initial_value = None
                        address = var.getaddress()
                        if address is not None:
                            located.append((var_type, var.getname(), address, initial_value))
                        else:
                            variables.append((var_type, var.getname(), None, initial_value))
                if varlist.getconstant():
                    option = "CONSTANT"
                elif varlist.getretain():
                    option = "RETAIN"
                elif varlist.getnonretain():
                    option = "NON_RETAIN"
                else:
                    option = None
                if len(variables) > 0:
                    self.Interface.append((varTypeNames[varlist_type], option, False, variables))
                if len(located) > 0:
                    self.Interface.append((varTypeNames[varlist_type], option, True, located))

    LITERAL_TYPES = {
        "T":   "TIME",
        "D":   "DATE",
        "TOD": "TIME_OF_DAY",
        "DT":  "DATE_AND_TIME",
        "2":    None,
        "8":    None,
        "16":   None,
    }

    def ComputeConnectionTypes(self, pou):
        body = pou.getbody()
        if isinstance(body, list):
            body = body[0]
        body_content = body.getcontent()
        body_type = body_content.getLocalTag()
        if body_type in ["FBD", "LD", "SFC"]:
            undefined_blocks = []
            for instance in body.getcontentInstances():
                if isinstance(instance, (InVariableClass, OutVariableClass,
                                         InOutVariableClass)):
                    expression = instance.getexpression()
                    var_type = self.GetVariableType(expression)
                    if isinstance(pou, TransitionObjClass) and expression == pou.getname():
                        var_type = "BOOL"
                    elif (not isinstance(pou, (TransitionObjClass, ActionObjClass)) and
                          pou.getpouType() == "function" and expression == pou.getname()):
                        returntype_content = pou.interface.getreturnType().getcontent()
                        returntype_content_type = returntype_content.getLocalTag()
                        if returntype_content_type == "derived":
                            var_type = returntype_content.getname()
                        else:
                            var_type = returntype_content_type.upper()
                    elif var_type is None:
                        parts = expression.split("#")
                        if len(parts) > 1:
                            literal_prefix = parts[0].upper()
                            var_type = self.LITERAL_TYPES.get(literal_prefix,
                                                              literal_prefix)
                        elif expression.startswith("'"):
                            var_type = "STRING"
                        elif expression.startswith('"'):
                            var_type = "WSTRING"
                    if var_type is not None:
                        if isinstance(instance, (InVariableClass, InOutVariableClass)):
                            for connection in self.ExtractRelatedConnections(instance.connectionPointOut):
                                self.ConnectionTypes[connection] = var_type
                        if isinstance(instance, (OutVariableClass, InOutVariableClass)):
                            self.ConnectionTypes[instance.connectionPointIn] = var_type
                            connected = self.GetConnectedConnector(instance.connectionPointIn, body)
                            if connected is not None and connected not in self.ConnectionTypes:
                                for related in self.ExtractRelatedConnections(connected):
                                    self.ConnectionTypes[related] = var_type
                elif isinstance(instance, (ContactClass, CoilClass)):
                    for connection in self.ExtractRelatedConnections(instance.connectionPointOut):
                        self.ConnectionTypes[connection] = "BOOL"
                    self.ConnectionTypes[instance.connectionPointIn] = "BOOL"
                    for link in instance.connectionPointIn.getconnections():
                        connected = self.GetLinkedConnector(link, body)
                        if connected is not None and connected not in self.ConnectionTypes:
                            for related in self.ExtractRelatedConnections(connected):
                                self.ConnectionTypes[related] = "BOOL"
                elif isinstance(instance, LeftPowerRailClass):
                    for connection in instance.getconnectionPointOut():
                        for related in self.ExtractRelatedConnections(connection):
                            self.ConnectionTypes[related] = "BOOL"
                elif isinstance(instance, RightPowerRailClass):
                    for connection in instance.getconnectionPointIn():
                        self.ConnectionTypes[connection] = "BOOL"
                        for link in connection.getconnections():
                            connected = self.GetLinkedConnector(link, body)
                            if connected is not None and connected not in self.ConnectionTypes:
                                for related in self.ExtractRelatedConnections(connected):
                                    self.ConnectionTypes[related] = "BOOL"
                elif isinstance(instance, TransitionClass):
                    content = instance.getconditionContent()
                    if content["type"] == "connection":
                        self.ConnectionTypes[content["value"]] = "BOOL"
                        connections = content["value"].getconnections()
                        if not connections:
                            raise PLCGenException(
                                _("SFC transition in POU \"%s\" must be connected.") % self.Name)

                        for link in connections:
                            connected = self.GetLinkedConnector(link, body)
                            if connected is not None and connected not in self.ConnectionTypes:
                                for related in self.ExtractRelatedConnections(connected):
                                    self.ConnectionTypes[related] = "BOOL"
                elif isinstance(instance, ContinuationClass):
                    name = instance.getname()
                    connector = None
                    var_type = "ANY"
                    for element in body.getcontentInstances():
                        if isinstance(element, ConnectorClass) and element.getname() == name:
                            if connector is not None:
                                raise PLCGenException(
                                    _("More than one connector found corresponding to \"{a1}\" continuation in \"{a2}\" POU").
                                    format(a1=name, a2=self.Name))
                            connector = element
                    if connector is not None:
                        undefined = [instance.connectionPointOut, connector.connectionPointIn]
                        connected = self.GetConnectedConnector(connector.connectionPointIn, body)
                        if connected is not None:
                            undefined.append(connected)
                        related = []
                        for connection in undefined:
                            if connection in self.ConnectionTypes:
                                var_type = self.ConnectionTypes[connection]
                            else:
                                related.extend(self.ExtractRelatedConnections(connection))
                        if var_type.startswith("ANY") and len(related) > 0:
                            self.RelatedConnections.append(related)
                        else:
                            for connection in related:
                                self.ConnectionTypes[connection] = var_type
                    else:
                        raise PLCGenException(
                            _("No connector found corresponding to \"{a1}\" continuation in \"{a2}\" POU").
                            format(a1=name, a2=self.Name))

                elif isinstance(instance, BlockClass):
                    block_infos = self.GetBlockType(instance.gettypeName(), "undefined")
                    if block_infos is not None:
                        self.ComputeBlockInputTypes(instance, block_infos, body)
                    else:
                        for variable in instance.inputVariables.getvariable():
                            connected = self.GetConnectedConnector(variable.connectionPointIn, body)
                            if connected is not None:
                                var_type = self.ConnectionTypes.get(connected, None)
                                if var_type is not None:
                                    self.ConnectionTypes[variable.connectionPointIn] = var_type
                                else:
                                    related = self.ExtractRelatedConnections(connected)
                                    related.append(variable.connectionPointIn)
                                    self.RelatedConnections.append(related)
                        undefined_blocks.append(instance)
            for instance in undefined_blocks:
                block_infos = self.GetBlockType(instance.gettypeName(), tuple([self.ConnectionTypes.get(variable.connectionPointIn, "ANY") for variable in instance.inputVariables.getvariable() if variable.getformalParameter() != "EN"]))
                if block_infos is not None:
                    self.ComputeBlockInputTypes(instance, block_infos, body)
                else:
                    raise PLCGenException(
                        _("No informations found for \"%s\" block") % (instance.gettypeName()))
            if body_type == "SFC":
                previous_tagname = self.TagName
                for action in pou.getactionList():
                    self.TagName = ComputePouActionName(self.Name, action.getname())
                    self.ComputeConnectionTypes(action)
                for transition in pou.gettransitionList():
                    self.TagName = ComputePouTransitionName(self.Name, transition.getname())
                    self.ComputeConnectionTypes(transition)
                self.TagName = previous_tagname

    def ComputeBlockInputTypes(self, instance, block_infos, body):
        undefined = {}
        for variable in instance.outputVariables.getvariable():
            output_name = variable.getformalParameter()
            if output_name == "ENO":
                for connection in self.ExtractRelatedConnections(variable.connectionPointOut):
                    self.ConnectionTypes[connection] = "BOOL"
            else:
                for oname, otype, _oqualifier in block_infos["outputs"]:
                    if output_name == oname:
                        if otype.startswith("ANY"):
                            if otype not in undefined:
                                undefined[otype] = []
                            undefined[otype].append(variable.connectionPointOut)
                        elif variable.connectionPointOut not in self.ConnectionTypes:
                            for connection in self.ExtractRelatedConnections(variable.connectionPointOut):
                                self.ConnectionTypes[connection] = otype
        for variable in instance.inputVariables.getvariable():
            input_name = variable.getformalParameter()
            if input_name == "EN":
                for connection in self.ExtractRelatedConnections(variable.connectionPointIn):
                    self.ConnectionTypes[connection] = "BOOL"
            else:
                for iname, itype, _iqualifier in block_infos["inputs"]:
                    if input_name == iname:
                        connected = self.GetConnectedConnector(variable.connectionPointIn, body)
                        if itype.startswith("ANY"):
                            if itype not in undefined:
                                undefined[itype] = []
                            undefined[itype].append(variable.connectionPointIn)
                            if connected is not None:
                                undefined[itype].append(connected)
                        else:
                            self.ConnectionTypes[variable.connectionPointIn] = itype
                            if connected is not None and connected not in self.ConnectionTypes:
                                for connection in self.ExtractRelatedConnections(connected):
                                    self.ConnectionTypes[connection] = itype
        for var_type, connections in undefined.items():
            related = []
            for connection in connections:
                connection_type = self.ConnectionTypes.get(connection)
                if connection_type and not connection_type.startswith("ANY"):
                    var_type = connection_type
                else:
                    related.extend(self.ExtractRelatedConnections(connection))
            if var_type.startswith("ANY") and len(related) > 0:
                self.RelatedConnections.append(related)
            else:
                for connection in related:
                    self.ConnectionTypes[connection] = var_type

    def GetUsedEno(self, body, connections):
        """
            Function checks whether value on given connection
            comes from block, that has used EN input and
            returns variable name for ENO output.

            This is needed to avoid value propagation from blocks
            with false signal on EN input.

        :param body:
            body of the block for that program is currently generated
        :param connections:
            connection, that's source is checked for EN/ENO usage
        :return:
            if EN/ENO are not used, then None is returned
            Otherwise BOOL variable corresponding to ENO
            output is returned.
        """

        if len(connections) != 1:
            return None
        ref_local_id = connections[0].getrefLocalId()
        blk = body.getcontentInstance(ref_local_id)
        if blk is None:
            return None

        if not hasattr(blk, "inputVariables"):
            return None

        for invar in blk.inputVariables.getvariable():
            if invar.getformalParameter() == "EN":
                if len(invar.getconnectionPointIn().getconnections()) > 0:
                    if blk.getinstanceName() is None:
                        var_name = "_TMP_%s%d_ENO" % (blk.gettypeName(), blk.getlocalId())
                    else:
                        var_name = "%s.ENO" % blk.getinstanceName()
                    return var_name
        return None

    def ComputeProgram(self, pou):
        body = pou.getbody()
        if isinstance(body, list):
            body = body[0]
        body_content = body.getcontent()
        body_type = body_content.getLocalTag()
        if body_type in ["IL", "ST"]:
            text = body_content.getanyText()
            self.ParentGenerator.GeneratePouProgramInText(text.upper())
            self.Program = [(ReIndentText(text, len(self.CurrentIndent)),
                             (self.TagName, "body", len(self.CurrentIndent)))]
        elif body_type == "SFC":
            self.IndentRight()
            for instance in body.getcontentInstances():
                if isinstance(instance, StepClass):
                    self.GenerateSFCStep(instance, pou)
                elif isinstance(instance, ActionBlockClass):
                    self.GenerateSFCStepActions(instance, pou)
                elif isinstance(instance, TransitionClass):
                    self.GenerateSFCTransition(instance, pou)
                elif isinstance(instance, JumpStepClass):
                    self.GenerateSFCJump(instance, pou)
            if len(self.InitialSteps) > 0 and len(self.SFCComputedBlocks) > 0:
                action_name = "COMPUTE_FUNCTION_BLOCKS"
                action_infos = {"qualifier": "S", "content": action_name}
                self.SFCNetworks["Steps"][self.InitialSteps[0]]["actions"].append(action_infos)
                self.SFCNetworks["Actions"][action_name] = (self.SFCComputedBlocks, ())
                self.Program = []
            self.IndentLeft()
            for initialstep in self.InitialSteps:
                self.ComputeSFCStep(initialstep)
        else:
            otherInstances = {"outVariables&coils": [], "blocks": [], "connectors": []}
            orderedInstances = []
            for instance in body.getcontentInstances():
                if isinstance(instance, (OutVariableClass, InOutVariableClass, BlockClass)):
                    executionOrderId = instance.getexecutionOrderId()
                    if executionOrderId > 0:
                        orderedInstances.append((executionOrderId, instance))
                    elif isinstance(instance, (OutVariableClass, InOutVariableClass)):
                        otherInstances["outVariables&coils"].append(instance)
                    elif isinstance(instance, BlockClass):
                        otherInstances["blocks"].append(instance)
                elif isinstance(instance, ConnectorClass):
                    otherInstances["connectors"].append(instance)
                elif isinstance(instance, CoilClass):
                    otherInstances["outVariables&coils"].append(instance)
            orderedInstances.sort()
            otherInstances["outVariables&coils"].sort(SortInstances)
            otherInstances["blocks"].sort(SortInstances)
            instances = [instance for (executionOrderId, instance) in orderedInstances]
            instances.extend(otherInstances["outVariables&coils"] + otherInstances["blocks"] + otherInstances["connectors"])
            for instance in instances:
                if isinstance(instance, (OutVariableClass, InOutVariableClass)):
                    connections = instance.connectionPointIn.getconnections()
                    if connections is not None:
                        expression = self.ComputeExpression(body, connections)
                        if expression is not None:
                            eno_var = self.GetUsedEno(body, connections)
                            if eno_var is not None:
                                self.Program += [(self.CurrentIndent + "IF %s" % eno_var, ())]
                                self.Program += [(" THEN\n  ", ())]
                                self.IndentRight()

                            self.Program += [(self.CurrentIndent, ()),
                                             (instance.getexpression(), (self.TagName, "io_variable", instance.getlocalId(), "expression")),
                                             (" := ", ())]
                            self.Program += expression
                            self.Program += [(";\n", ())]

                            if eno_var is not None:
                                self.IndentLeft()
                                self.Program += [(self.CurrentIndent + "END_IF;\n", ())]
                elif isinstance(instance, BlockClass):
                    block_type = instance.gettypeName()
                    self.ParentGenerator.GeneratePouProgram(block_type)
                    block_infos = self.GetBlockType(block_type, tuple([self.ConnectionTypes.get(variable.connectionPointIn, "ANY") for variable in instance.inputVariables.getvariable() if variable.getformalParameter() != "EN"]))
                    if block_infos is None:
                        block_infos = self.GetBlockType(block_type)
                    if block_infos is None:
                        raise PLCGenException(
                            _("Undefined block type \"{a1}\" in \"{a2}\" POU").
                            format(a1=block_type, a2=self.Name))
                    try:
                        self.GenerateBlock(instance, block_infos, body, None)
                    except ValueError as e:
                        raise PLCGenException(str(e))
                elif isinstance(instance, ConnectorClass):
                    connector = instance.getname()
                    if self.ComputedConnectors.get(connector, None):
                        continue
                    expression = self.ComputeExpression(body, instance.connectionPointIn.getconnections())
                    if expression is not None:
                        self.ComputedConnectors[connector] = expression
                elif isinstance(instance, CoilClass):
                    connections = instance.connectionPointIn.getconnections()
                    if connections is not None:
                        coil_info = (self.TagName, "coil", instance.getlocalId())
                        expression = self.ComputeExpression(body, connections)
                        if expression is not None:
                            expression = self.ExtractModifier(instance, expression, coil_info)
                            self.Program += [(self.CurrentIndent, ())]
                            self.Program += [(instance.getvariable(), coil_info + ("reference",))]
                            self.Program += [(" := ", ())] + expression + [(";\n", ())]

    def FactorizePaths(self, paths):
        same_paths = {}
        uncomputed_index = range(len(paths))
        factorized_paths = []
        for num, path in enumerate(paths):
            if isinstance(path, list):
                if len(path) > 1:
                    str_path = str(path[-1:])
                    same_paths.setdefault(str_path, [])
                    same_paths[str_path].append((path[:-1], num))
            else:
                factorized_paths.append(path)
                uncomputed_index.remove(num)
        for same_path, elements in same_paths.items():
            if len(elements) > 1:
                elements_paths = self.FactorizePaths([path for path, num in elements])
                if len(elements_paths) > 1:
                    factorized_paths.append([tuple(elements_paths)] + eval(same_path))
                else:
                    factorized_paths.append(elements_paths + eval(same_path))
                for path, num in elements:
                    uncomputed_index.remove(num)
        for num in uncomputed_index:
            factorized_paths.append(paths[num])
        factorized_paths.sort()
        return factorized_paths

    def GenerateBlock(self, block, block_infos, body, link, order=False, to_inout=False):

        def _GetBlockName(name, type):
            """function returns name of function or function block instance"""
            if name:
                # function blocks
                blockname = "{a1}({a2})".format(a1=name, a2=type)
            else:
                # functions
                blockname = type
            return blockname

        def _RaiseUnconnectedInOutError(name, type, parameter, place):
            blockname = _GetBlockName(name, type)
            raise ValueError(
                _("InOut variable {a1} in block {a2} in POU {a3} must be connected.").
                format(a1=parameter, a2=blockname, a3=place))

        name = block.getinstanceName()
        type = block.gettypeName()
        executionOrderId = block.getexecutionOrderId()
        input_variables = block.inputVariables.getvariable()
        output_variables = block.outputVariables.getvariable()
        inout_variables = {}
        for input_variable in input_variables:
            for output_variable in output_variables:
                if input_variable.getformalParameter() == output_variable.getformalParameter():
                    inout_variables[input_variable.getformalParameter()] = ""
        input_names = [input[0] for input in block_infos["inputs"]]
        output_names = [output[0] for output in block_infos["outputs"]]
        if block_infos["type"] == "function":
            if not self.ComputedBlocks.get(block, False) and not order:
                self.ComputedBlocks[block] = True
                connected_vars = []
                if not block_infos["extensible"]:
                    input_connected = dict([("EN", None)] +
                                           [(input_name, None) for input_name in input_names])
                    for variable in input_variables:
                        parameter = variable.getformalParameter()
                        if parameter in input_connected:
                            input_connected[parameter] = variable
                    if input_connected["EN"] is None:
                        input_connected.pop("EN")
                        input_parameters = input_names
                    else:
                        input_parameters = ["EN"] + input_names
                else:
                    input_connected = dict([(variable.getformalParameter(), variable)
                                            for variable in input_variables])
                    input_parameters = [variable.getformalParameter()
                                        for variable in input_variables]
                one_input_connected = False
                all_input_connected = True
                for i, parameter in enumerate(input_parameters):
                    variable = input_connected.get(parameter)
                    if variable is not None:
                        input_info = (self.TagName, "block", block.getlocalId(), "input", i)
                        connections = variable.connectionPointIn.getconnections()
                        if connections is not None:
                            if parameter != "EN":
                                one_input_connected = True
                            if parameter in inout_variables:
                                expression = self.ComputeExpression(body, connections, executionOrderId > 0, True)
                                if expression is not None:
                                    inout_variables[parameter] = expression
                                else:
                                    _RaiseUnconnectedInOutError(name, type, parameter, self.Name)
                            else:
                                expression = self.ComputeExpression(body, connections, executionOrderId > 0)
                            if expression is not None:
                                connected_vars.append(([(parameter, input_info), (" := ", ())],
                                                       self.ExtractModifier(variable, expression, input_info)))
                        else:
                            all_input_connected = False
                    else:
                        all_input_connected = False
                if len(output_variables) > 1 or not all_input_connected:
                    vars = [name + value for name, value in connected_vars]
                else:
                    vars = [value for name, value in connected_vars]
                if one_input_connected:
                    for i, variable in enumerate(output_variables):
                        parameter = variable.getformalParameter()
                        if parameter not in inout_variables and parameter in output_names + ["", "ENO"]:
                            if variable.getformalParameter() == "":
                                variable_name = "%s%d" % (type, block.getlocalId())
                            else:
                                variable_name = "_TMP_%s%d_%s" % (type, block.getlocalId(), parameter)
                            if self.Interface[-1][0] != "VAR" or self.Interface[-1][1] is not None or self.Interface[-1][2]:
                                self.Interface.append(("VAR", None, False, []))
                            if variable.connectionPointOut in self.ConnectionTypes:
                                self.Interface[-1][3].append((self.ConnectionTypes[variable.connectionPointOut], variable_name, None, None))
                            else:
                                self.Interface[-1][3].append(("ANY", variable_name, None, None))
                            if len(output_variables) > 1 and parameter not in ["", "OUT"]:
                                vars.append([(parameter, (self.TagName, "block", block.getlocalId(), "output", i)),
                                             (" => %s" % variable_name, ())])
                            else:
                                output_info = (self.TagName, "block", block.getlocalId(), "output", i)
                                output_name = variable_name
                    self.Program += [(self.CurrentIndent, ()),
                                     (output_name, output_info),
                                     (" := ", ()),
                                     (type, (self.TagName, "block", block.getlocalId(), "type")),
                                     ("(", ())]
                    self.Program += JoinList([(", ", ())], vars)
                    self.Program += [(");\n", ())]
                else:
                    msg = _("\"{a1}\" function cancelled in \"{a2}\" POU: No input connected").format(a1=type, a2=self.TagName.split("::")[-1])
                    self.Warnings.append(msg)
        elif block_infos["type"] == "functionBlock":
            if not self.ComputedBlocks.get(block, False) and not order:
                self.ComputedBlocks[block] = True
                vars = []
                offset_idx = 0
                for variable in input_variables:
                    parameter = variable.getformalParameter()
                    if parameter in input_names or parameter == "EN":
                        if parameter == "EN":
                            input_idx = 0
                            offset_idx = 1
                        else:
                            input_idx = offset_idx + input_names.index(parameter)
                        input_info = (self.TagName, "block", block.getlocalId(), "input", input_idx)
                        connections = variable.connectionPointIn.getconnections()
                        if connections is not None:
                            expression = self.ComputeExpression(body, connections, executionOrderId > 0, parameter in inout_variables)
                            if expression is not None:
                                vars.append([(parameter, input_info),
                                             (" := ", ())] + self.ExtractModifier(variable, expression, input_info))
                            elif parameter in inout_variables:
                                _RaiseUnconnectedInOutError(name, type, parameter, self.Name)
                self.Program += [(self.CurrentIndent, ()),
                                 (name, (self.TagName, "block", block.getlocalId(), "name")),
                                 ("(", ())]
                self.Program += JoinList([(", ", ())], vars)
                self.Program += [(");\n", ())]

        if link is not None:
            connectionPoint = link.getposition()[-1]
            output_parameter = link.getformalParameter()
        else:
            connectionPoint = None
            output_parameter = None

        output_variable = None
        output_idx = 0
        if output_parameter is not None:
            if output_parameter in output_names or output_parameter == "ENO":
                for variable in output_variables:
                    if variable.getformalParameter() == output_parameter:
                        output_variable = variable
                        if output_parameter != "ENO":
                            output_idx = output_names.index(output_parameter)
        else:
            for i, variable in enumerate(output_variables):
                blockPointx, blockPointy = variable.connectionPointOut.getrelPositionXY()
                if connectionPoint is None or \
                   block.getx() + blockPointx == connectionPoint.getx() and \
                   block.gety() + blockPointy == connectionPoint.gety():
                    output_variable = variable
                    output_parameter = variable.getformalParameter()
                    output_idx = i

        if output_variable is not None:
            if block_infos["type"] == "function":
                output_info = (self.TagName, "block", block.getlocalId(), "output", output_idx)
                if output_parameter in inout_variables:
                    for variable in input_variables:
                        if variable.getformalParameter() == output_parameter:
                            connections = variable.connectionPointIn.getconnections()
                            if connections is not None:
                                expression = self.ComputeExpression(
                                    body, connections, executionOrderId > 0, True)
                                output_value = expression
                                break
                else:
                    if output_parameter == "":
                        output_name = "%s%d" % (type, block.getlocalId())
                    else:
                        output_name = "_TMP_%s%d_%s" % (type, block.getlocalId(), output_parameter)
                    output_value = [(output_name, output_info)]
                return self.ExtractModifier(output_variable, output_value, output_info)
            if block_infos["type"] == "functionBlock":
                output_info = (self.TagName, "block", block.getlocalId(), "output", output_idx)
                output_name = self.ExtractModifier(output_variable, [("%s.%s" % (name, output_parameter), output_info)], output_info)
                if to_inout:
                    variable_name = "%s_%s" % (name, output_parameter)
                    if not self.IsAlreadyDefined(variable_name):
                        if self.Interface[-1][0] != "VAR" or self.Interface[-1][1] is not None or self.Interface[-1][2]:
                            self.Interface.append(("VAR", None, False, []))
                        if variable.connectionPointOut in self.ConnectionTypes:
                            self.Interface[-1][3].append(
                                (self.ConnectionTypes[output_variable.connectionPointOut], variable_name, None, None))
                        else:
                            self.Interface[-1][3].append(("ANY", variable_name, None, None))
                        self.Program += [(self.CurrentIndent, ()),
                                         ("%s := " % variable_name, ())]
                        self.Program += output_name
                        self.Program += [(";\n", ())]
                    return [(variable_name, ())]
                return output_name
        if link is not None:
            if output_parameter is None:
                output_parameter = ""
            blockname = _GetBlockName(name, type)
            raise ValueError(
                _("No output {a1} variable found in block {a2} in POU {a3}. Connection must be broken").
                format(a1=output_parameter, a2=blockname, a3=self.Name))

    def GeneratePaths(self, connections, body, order=False, to_inout=False):
        paths = []
        for connection in connections:
            localId = connection.getrefLocalId()
            next = body.getcontentInstance(localId)
            if isinstance(next, LeftPowerRailClass):
                paths.append(None)
            elif isinstance(next, (InVariableClass, InOutVariableClass)):
                paths.append(str([(next.getexpression(), (self.TagName, "io_variable", localId, "expression"))]))
            elif isinstance(next, BlockClass):
                block_type = next.gettypeName()
                self.ParentGenerator.GeneratePouProgram(block_type)
                block_infos = self.GetBlockType(block_type, tuple([self.ConnectionTypes.get(variable.connectionPointIn, "ANY") for variable in next.inputVariables.getvariable() if variable.getformalParameter() != "EN"]))
                if block_infos is None:
                    block_infos = self.GetBlockType(block_type)
                if block_infos is None:
                    raise PLCGenException(
                        _("Undefined block type \"{a1}\" in \"{a2}\" POU").
                        format(a1=block_type, a2=self.Name))
                try:
                    paths.append(str(self.GenerateBlock(next, block_infos, body, connection, order, to_inout)))
                except ValueError as e:
                    raise PLCGenException(str(e))
            elif isinstance(next, ContinuationClass):
                name = next.getname()
                computed_value = self.ComputedConnectors.get(name, None)
                if computed_value is not None:
                    paths.append(str(computed_value))
                else:
                    connector = None
                    for instance in body.getcontentInstances():
                        if isinstance(instance, ConnectorClass) and instance.getname() == name:
                            if connector is not None:
                                raise PLCGenException(
                                    _("More than one connector found corresponding to \"{a1}\" continuation in \"{a2}\" POU").
                                    format(a1=name, a2=self.Name))
                            connector = instance
                    if connector is not None:
                        connections = connector.connectionPointIn.getconnections()
                        if connections is not None:
                            expression = self.ComputeExpression(body, connections, order)
                            if expression is not None:
                                self.ComputedConnectors[name] = expression
                                paths.append(str(expression))
                    else:
                        raise PLCGenException(
                            _("No connector found corresponding to \"{a1}\" continuation in \"{a2}\" POU").
                            format(a1=name, a2=self.Name))
            elif isinstance(next, ContactClass):
                contact_info = (self.TagName, "contact", next.getlocalId())
                variable = str(self.ExtractModifier(next, [(next.getvariable(), contact_info + ("reference",))], contact_info))
                result = self.GeneratePaths(next.connectionPointIn.getconnections(), body, order)
                if len(result) == 0:
                    raise PLCGenException(_("Contact \"{a1}\" in POU \"{a2}\" must be connected.").
                                          format(a1=next.getvariable(), a2=self.Name))
                if len(result) > 1:
                    factorized_paths = self.FactorizePaths(result)
                    if len(factorized_paths) > 1:
                        paths.append([variable, tuple(factorized_paths)])
                    else:
                        paths.append([variable] + factorized_paths)
                elif isinstance(result[0], list):
                    paths.append([variable] + result[0])
                elif result[0] is not None:
                    paths.append([variable, result[0]])
                else:
                    paths.append(variable)
            elif isinstance(next, CoilClass):
                paths.append(self.GeneratePaths(next.connectionPointIn.getconnections(), body, order))
        return paths

    def ComputePaths(self, paths, first=False):
        if isinstance(paths, tuple):
            if None in paths:
                return [("TRUE", ())]
            else:
                vars = [self.ComputePaths(path) for path in paths]
                if first:
                    return JoinList([(" OR ", ())], vars)
                else:
                    return [("(", ())] + JoinList([(" OR ", ())], vars) + [(")", ())]
        elif isinstance(paths, list):
            vars = [self.ComputePaths(path) for path in paths]
            return JoinList([(" AND ", ())], vars)
        elif paths is None:
            return [("TRUE", ())]
        else:
            return eval(paths)

    def ComputeExpression(self, body, connections, order=False, to_inout=False):
        paths = self.GeneratePaths(connections, body, order, to_inout)
        if len(paths) == 0:
            return None
        if len(paths) > 1:
            factorized_paths = self.FactorizePaths(paths)
            if len(factorized_paths) > 1:
                paths = tuple(factorized_paths)
            else:
                paths = factorized_paths[0]
        else:
            paths = paths[0]
        return self.ComputePaths(paths, True)

    def ExtractModifier(self, variable, expression, var_info):
        if variable.getnegated():
            return [("NOT(", var_info + ("negated",))] + expression + [(")", ())]
        else:
            storage = variable.getstorage()
            if storage in ["set", "reset"]:
                self.Program += [(self.CurrentIndent + "IF ", var_info + (storage,))] + expression
                self.Program += [(" THEN\n  ", ())]
                if storage == "set":
                    return [("TRUE; (*set*)\n" + self.CurrentIndent + "END_IF", ())]
                else:
                    return [("FALSE; (*reset*)\n" + self.CurrentIndent + "END_IF", ())]
            edge = variable.getedge()
            if edge == "rising":
                return self.AddTrigger("R_TRIG", expression, var_info + ("rising",))
            elif edge == "falling":
                return self.AddTrigger("F_TRIG", expression, var_info + ("falling",))
        return expression

    def AddTrigger(self, edge, expression, var_info):
        if self.Interface[-1][0] != "VAR" or self.Interface[-1][1] is not None or self.Interface[-1][2]:
            self.Interface.append(("VAR", None, False, []))
        i = 1
        name = "%s%d" % (edge, i)
        while self.IsAlreadyDefined(name):
            i += 1
            name = "%s%d" % (edge, i)
        self.Interface[-1][3].append((edge, name, None, None))
        self.Program += [(self.CurrentIndent, ()), (name, var_info), ("(CLK := ", ())]
        self.Program += expression
        self.Program += [(");\n", ())]
        return [("%s.Q" % name, var_info)]

    def ExtractDivergenceInput(self, divergence, pou):
        connectionPointIn = divergence.getconnectionPointIn()
        if connectionPointIn is not None:
            connections = connectionPointIn.getconnections()
            if connections is not None and len(connections) == 1:
                instanceLocalId = connections[0].getrefLocalId()
                body = pou.getbody()
                if isinstance(body, list):
                    body = body[0]
                return body.getcontentInstance(instanceLocalId)
        return None

    def ExtractConvergenceInputs(self, convergence, pou):
        instances = []
        for connectionPointIn in convergence.getconnectionPointIn():
            connections = connectionPointIn.getconnections()
            if connections is not None and len(connections) == 1:
                instanceLocalId = connections[0].getrefLocalId()
                body = pou.getbody()
                if isinstance(body, list):
                    body = body[0]
                instances.append(body.getcontentInstance(instanceLocalId))
        return instances

    def GenerateSFCStep(self, step, pou):
        step_name = step.getname()
        if step_name not in self.SFCNetworks["Steps"].keys():
            if step.getinitialStep():
                self.InitialSteps.append(step_name)
            step_infos = {"id":          step.getlocalId(),
                          "initial":     step.getinitialStep(),
                          "transitions": [],
                          "actions":     []}
            self.SFCNetworks["Steps"][step_name] = step_infos
            if step.connectionPointIn is not None:
                instances = []
                connections = step.connectionPointIn.getconnections()
                if connections is not None and len(connections) == 1:
                    instanceLocalId = connections[0].getrefLocalId()
                    body = pou.getbody()
                    if isinstance(body, list):
                        body = body[0]
                    instance = body.getcontentInstance(instanceLocalId)
                    if isinstance(instance, TransitionClass):
                        instances.append(instance)
                    elif isinstance(instance, SelectionConvergenceClass):
                        instances.extend(self.ExtractConvergenceInputs(instance, pou))
                    elif isinstance(instance, SimultaneousDivergenceClass):
                        transition = self.ExtractDivergenceInput(instance, pou)
                        if transition is not None:
                            if isinstance(transition, TransitionClass):
                                instances.append(transition)
                            elif isinstance(transition, SelectionConvergenceClass):
                                instances.extend(self.ExtractConvergenceInputs(transition, pou))
                for instance in instances:
                    self.GenerateSFCTransition(instance, pou)
                    if instance in self.SFCNetworks["Transitions"].keys():
                        target_info = (self.TagName, "transition", instance.getlocalId(), "to", step_infos["id"])
                        self.SFCNetworks["Transitions"][instance]["to"].append([(step_name, target_info)])

    def GenerateSFCJump(self, jump, pou):
        jump_target = jump.gettargetName()
        if not pou.hasstep(jump_target):
            pname = pou.getname()
            raise PLCGenException(
                _("SFC jump in pou \"{a1}\" refers to non-existent SFC step \"{a2}\"").
                format(a1=pname, a2=jump_target))

        if jump.connectionPointIn is not None:
            instances = []
            connections = jump.connectionPointIn.getconnections()
            if connections is not None and len(connections) == 1:
                instanceLocalId = connections[0].getrefLocalId()
                body = pou.getbody()
                if isinstance(body, list):
                    body = body[0]
                instance = body.getcontentInstance(instanceLocalId)
                if isinstance(instance, TransitionClass):
                    instances.append(instance)
                elif isinstance(instance, SelectionConvergenceClass):
                    instances.extend(self.ExtractConvergenceInputs(instance, pou))
                elif isinstance(instance, SimultaneousDivergenceClass):
                    transition = self.ExtractDivergenceInput(instance, pou)
                    if transition is not None:
                        if isinstance(transition, TransitionClass):
                            instances.append(transition)
                        elif isinstance(transition, SelectionConvergenceClass):
                            instances.extend(self.ExtractConvergenceInputs(transition, pou))
            for instance in instances:
                self.GenerateSFCTransition(instance, pou)
                if instance in self.SFCNetworks["Transitions"].keys():
                    target_info = (self.TagName, "jump", jump.getlocalId(), "target")
                    self.SFCNetworks["Transitions"][instance]["to"].append([(jump_target, target_info)])

    def GenerateSFCStepActions(self, actionBlock, pou):
        connections = actionBlock.connectionPointIn.getconnections()
        if connections is not None and len(connections) == 1:
            stepLocalId = connections[0].getrefLocalId()
            body = pou.getbody()
            if isinstance(body, list):
                body = body[0]
            step = body.getcontentInstance(stepLocalId)
            self.GenerateSFCStep(step, pou)
            step_name = step.getname()
            if step_name in self.SFCNetworks["Steps"].keys():
                actions = actionBlock.getactions()
                for i, action in enumerate(actions):
                    action_infos = {"id":        actionBlock.getlocalId(),
                                    "qualifier": action["qualifier"],
                                    "content":   action["value"],
                                    "num":       i}
                    if "duration" in action:
                        action_infos["duration"] = action["duration"]
                    if "indicator" in action:
                        action_infos["indicator"] = action["indicator"]
                    if action["type"] == "reference":
                        self.GenerateSFCAction(action["value"], pou)
                    else:
                        action_name = "%s_INLINE%d" % (step_name.upper(), self.GetActionNumber())
                        self.SFCNetworks["Actions"][action_name] = ([
                            (self.CurrentIndent, ()),
                            (action["value"], (
                                self.TagName, "action_block", action_infos["id"],
                                "action", i, "inline")),
                            ("\n", ())], ())
                        action_infos["content"] = action_name
                    self.SFCNetworks["Steps"][step_name]["actions"].append(action_infos)

    def GenerateSFCAction(self, action_name, pou):
        if action_name not in self.SFCNetworks["Actions"].keys():
            actionContent = pou.getaction(action_name)
            if actionContent is not None:
                previous_tagname = self.TagName
                self.TagName = ComputePouActionName(self.Name, action_name)
                self.ComputeProgram(actionContent)
                self.SFCNetworks["Actions"][action_name] = (self.Program, (self.TagName, "name"))
                self.Program = []
                self.TagName = previous_tagname

    def GenerateSFCTransition(self, transition, pou):
        if transition not in self.SFCNetworks["Transitions"].keys():
            steps = []
            connections = transition.connectionPointIn.getconnections()
            if connections is not None and len(connections) == 1:
                instanceLocalId = connections[0].getrefLocalId()
                body = pou.getbody()
                if isinstance(body, list):
                    body = body[0]
                instance = body.getcontentInstance(instanceLocalId)
                if isinstance(instance, StepClass):
                    steps.append(instance)
                elif isinstance(instance, SelectionDivergenceClass):
                    step = self.ExtractDivergenceInput(instance, pou)
                    if step is not None:
                        if isinstance(step, StepClass):
                            steps.append(step)
                        elif isinstance(step, SimultaneousConvergenceClass):
                            steps.extend(self.ExtractConvergenceInputs(step, pou))
                elif isinstance(instance, SimultaneousConvergenceClass):
                    steps.extend(self.ExtractConvergenceInputs(instance, pou))
            transition_infos = {"id":       transition.getlocalId(),
                                "priority": transition.getpriority(),
                                "from":     [],
                                "to":       [],
                                "content":  []}
            self.SFCNetworks["Transitions"][transition] = transition_infos
            transitionValues = transition.getconditionContent()
            if transitionValues["type"] == "inline":
                transition_infos["content"] = [("\n%s:= " % self.CurrentIndent, ()),
                                               (transitionValues["value"], (self.TagName, "transition", transition.getlocalId(), "inline")),
                                               (";\n", ())]
            elif transitionValues["type"] == "reference":
                transitionContent = pou.gettransition(transitionValues["value"])
                transitionType = transitionContent.getbodyType()
                transitionBody = transitionContent.getbody()
                previous_tagname = self.TagName
                self.TagName = ComputePouTransitionName(self.Name, transitionValues["value"])
                if transitionType == "IL":
                    transition_infos["content"] = [(":\n", ()),
                                                   (ReIndentText(transitionBody.getcontent().getanyText(), len(self.CurrentIndent)), (self.TagName, "body", len(self.CurrentIndent)))]
                elif transitionType == "ST":
                    transition_infos["content"] = [("\n", ()),
                                                   (ReIndentText(transitionBody.getcontent().getanyText(), len(self.CurrentIndent)), (self.TagName, "body", len(self.CurrentIndent)))]
                else:
                    for instance in transitionBody.getcontentInstances():
                        if isinstance(instance, OutVariableClass) and instance.getexpression() == transitionValues["value"] or \
                           isinstance(instance, CoilClass) and instance.getvariable() == transitionValues["value"]:
                            connections = instance.connectionPointIn.getconnections()
                            if connections is not None:
                                expression = self.ComputeExpression(transitionBody, connections)
                                if expression is not None:
                                    transition_infos["content"] = [("\n%s:= " % self.CurrentIndent, ())] + expression + [(";\n", ())]
                                    self.SFCComputedBlocks += self.Program
                                    self.Program = []
                    if "content" not in transition_infos:
                        raise PLCGenException(
                            _("Transition \"%s\" body must contain an output variable or coil referring to its name")
                            % transitionValues["value"])
                self.TagName = previous_tagname
            elif transitionValues["type"] == "connection":
                body = pou.getbody()
                if isinstance(body, list):
                    body = body[0]
                connections = transitionValues["value"].getconnections()
                if connections is not None:
                    expression = self.ComputeExpression(body, connections)
                    if expression is not None:
                        transition_infos["content"] = [("\n%s:= " % self.CurrentIndent, ())] + expression + [(";\n", ())]
                        self.SFCComputedBlocks += self.Program
                        self.Program = []
            for step in steps:
                self.GenerateSFCStep(step, pou)
                step_name = step.getname()
                if step_name in self.SFCNetworks["Steps"].keys():
                    transition_infos["from"].append([(step_name, (self.TagName, "transition", transition.getlocalId(), "from", step.getlocalId()))])
                    self.SFCNetworks["Steps"][step_name]["transitions"].append(transition)

    def ComputeSFCStep(self, step_name):
        if step_name in self.SFCNetworks["Steps"].keys():
            step_infos = self.SFCNetworks["Steps"].pop(step_name)
            self.Program += [(self.CurrentIndent, ())]
            if step_infos["initial"]:
                self.Program += [("INITIAL_", ())]
            self.Program += [("STEP ", ()),
                             (step_name, (self.TagName, "step", step_infos["id"], "name")),
                             (":\n", ())]
            actions = []
            self.IndentRight()
            for action_infos in step_infos["actions"]:
                if action_infos.get("id", None) is not None:
                    action_info = (self.TagName, "action_block", action_infos["id"], "action", action_infos["num"])
                else:
                    action_info = ()
                actions.append(action_infos["content"])
                self.Program += [(self.CurrentIndent, ()),
                                 (action_infos["content"], action_info + ("reference",)),
                                 ("(", ()),
                                 (action_infos["qualifier"], action_info + ("qualifier",))]
                if "duration" in action_infos:
                    self.Program += [(", ", ()),
                                     (action_infos["duration"], action_info + ("duration",))]
                if "indicator" in action_infos:
                    self.Program += [(", ", ()),
                                     (action_infos["indicator"], action_info + ("indicator",))]
                self.Program += [(");\n", ())]
            self.IndentLeft()
            self.Program += [("%sEND_STEP\n\n" % self.CurrentIndent, ())]
            for action in actions:
                self.ComputeSFCAction(action)
            for transition in step_infos["transitions"]:
                self.ComputeSFCTransition(transition)

    def ComputeSFCAction(self, action_name):
        if action_name in self.SFCNetworks["Actions"].keys():
            action_content, action_info = self.SFCNetworks["Actions"].pop(action_name)
            self.Program += [("%sACTION " % self.CurrentIndent, ()),
                             (action_name, action_info),
                             (":\n", ())]
            self.Program += action_content
            self.Program += [("%sEND_ACTION\n\n" % self.CurrentIndent, ())]

    def ComputeSFCTransition(self, transition):
        if transition in self.SFCNetworks["Transitions"].keys():
            transition_infos = self.SFCNetworks["Transitions"].pop(transition)
            self.Program += [("%sTRANSITION" % self.CurrentIndent, ())]
            if transition_infos["priority"] is not None:
                self.Program += [(" (PRIORITY := ", ()),
                                 ("%d" % transition_infos["priority"], (self.TagName, "transition", transition_infos["id"], "priority")),
                                 (")", ())]
            self.Program += [(" FROM ", ())]
            if len(transition_infos["from"]) > 1:
                self.Program += [("(", ())]
                self.Program += JoinList([(", ", ())], transition_infos["from"])
                self.Program += [(")", ())]
            elif len(transition_infos["from"]) == 1:
                self.Program += transition_infos["from"][0]
            else:
                raise PLCGenException(
                    _("Transition with content \"{a1}\" not connected to a previous step in \"{a2}\" POU").
                    format(a1=transition_infos["content"], a2=self.Name))
            self.Program += [(" TO ", ())]
            if len(transition_infos["to"]) > 1:
                self.Program += [("(", ())]
                self.Program += JoinList([(", ", ())], transition_infos["to"])
                self.Program += [(")", ())]
            elif len(transition_infos["to"]) == 1:
                self.Program += transition_infos["to"][0]
            else:
                raise PLCGenException(
                    _("Transition with content \"{a1}\" not connected to a next step in \"{a2}\" POU").
                    format(a1=transition_infos["content"], a2=self.Name))
            self.Program += transition_infos["content"]
            self.Program += [("%sEND_TRANSITION\n\n" % self.CurrentIndent, ())]
            for [(step_name, _step_infos)] in transition_infos["to"]:
                self.ComputeSFCStep(step_name)

    def GenerateProgram(self, pou):
        self.ComputeInterface(pou)
        self.ComputeConnectionTypes(pou)
        self.ComputeProgram(pou)

        program = [("%s " % self.Type, ()),
                   (self.Name, (self.TagName, "name"))]
        if self.ReturnType is not None:
            program += [(" : ", ()),
                        (self.ReturnType, (self.TagName, "return"))]
        program += [("\n", ())]
        if len(self.Interface) == 0:
            raise PLCGenException(_("No variable defined in \"%s\" POU") % self.Name)
        if len(self.Program) == 0:
            raise PLCGenException(_("No body defined in \"%s\" POU") % self.Name)
        var_number = 0
        for list_type, option, _located, variables in self.Interface:
            variable_type = errorVarTypes.get(list_type, "var_local")
            program += [("  %s" % list_type, ())]
            if option is not None:
                program += [(" %s" % option, (self.TagName, variable_type, (var_number, var_number + len(variables)), option.lower()))]
            program += [("\n", ())]
            for var_type, var_name, var_address, var_initial in variables:
                program += [("    ", ())]
                if var_name:
                    program += [(var_name, (self.TagName, variable_type, var_number, "name")),
                                (" ", ())]
                if var_address is not None:
                    program += [("AT ", ()),
                                (var_address, (self.TagName, variable_type, var_number, "location")),
                                (" ", ())]
                program += [(": ", ()),
                            (var_type, (self.TagName, variable_type, var_number, "type"))]
                if var_initial is not None:
                    program += [(" := ", ()),
                                (self.ParentGenerator.ComputeValue(var_initial, var_type), (self.TagName, variable_type, var_number, "initial value"))]
                program += [(";\n", ())]
                var_number += 1
            program += [("  END_VAR\n", ())]
        program += [("\n", ())]
        program += self.Program
        program += [("END_%s\n\n" % self.Type, ())]
        return program


def GenerateCurrentProgram(controler, project, errors, warnings):
    generator = ProgramGenerator(controler, project, errors, warnings)
    if hasattr(controler, "logger"):
        def log(txt):
            controler.logger.write("    "+txt+"\n")
    else:
        def log(txt):
            pass

    generator.GenerateProgram(log)
    return generator.GetGeneratedProgram()
