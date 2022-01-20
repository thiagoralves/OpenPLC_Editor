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
import re
from collections import OrderedDict

from six.moves import xrange
from lxml import etree

from xmlclass import *
import util.paths as paths


#: Dictionary that makes the relation between var names
#: in plcopen and displayed values

VarTypes = {
    "Local":    "localVars",
    "Temp":     "tempVars",
    "Input":    "inputVars",
    "Output":   "outputVars",
    "InOut":    "inOutVars",
    "External": "externalVars",
    "Global":   "globalVars",
    "Access":   "accessVars"
}

searchResultVarTypes = {
    "inputVars":  "var_input",
    "outputVars": "var_output",
    "inOutVars":  "var_inout"
}


#: Define in which order var types must be displayed

VarOrder = ["Local", "Temp", "Input", "Output", "InOut", "External", "Global", "Access"]


#:  Define which action qualifier must be associated with a duration

QualifierList = OrderedDict([
    ("N", False),
    ("R", False),
    ("S", False),
    ("L", True),
    ("D", True),
    ("P", False),
    ("P0", False),
    ("P1", False),
    ("SD", True),
    ("DS", True),
    ("SL", True)])


FILTER_ADDRESS_MODEL = r"(%%[IQM](?:[XBWDL])?)(%s)((?:\.[0-9]+)*)"


def update_address(address, address_model, new_leading):
    result = address_model.match(address)
    if result is None:
        return address
    groups = result.groups()
    return groups[0] + new_leading + groups[2]


def _init_and_compare(function, v1, v2):
    if v1 is None:
        return v2
    if v2 is not None:
        return function(v1, v2)
    return v1


class rect(object):
    """
    Helper class for bounding_box calculation
    """

    def __init__(self, x=None, y=None, width=None, height=None):
        self.x_min = x
        self.x_max = None
        self.y_min = y
        self.y_max = None
        if width is not None and x is not None:
            self.x_max = x + width
        if height is not None and y is not None:
            self.y_max = y + height

    def update(self, x, y):
        self.x_min = _init_and_compare(min, self.x_min, x)
        self.x_max = _init_and_compare(max, self.x_max, x)
        self.y_min = _init_and_compare(min, self.y_min, y)
        self.y_max = _init_and_compare(max, self.y_max, y)

    def union(self, rect):
        self.x_min = _init_and_compare(min, self.x_min, rect.x_min)
        self.x_max = _init_and_compare(max, self.x_max, rect.x_max)
        self.y_min = _init_and_compare(min, self.y_min, rect.y_min)
        self.y_max = _init_and_compare(max, self.y_max, rect.y_max)

    def bounding_box(self):
        width = height = None
        if self.x_min is not None and self.x_max is not None:
            width = self.x_max - self.x_min
        if self.y_min is not None and self.y_max is not None:
            height = self.y_max - self.y_min
        return self.x_min, self.y_min, width, height


def TextLenInRowColumn(text):
    if text == "":
        return (0, 0)
    lines = text.split("\n")
    return len(lines) - 1, len(lines[-1])


def CompilePattern(criteria):
    flag = 0 if criteria["case_sensitive"] else re.IGNORECASE
    find_pattern = criteria["find_pattern"]
    if not criteria["regular_expression"]:
        find_pattern = re.escape(find_pattern)
    criteria["pattern"] = re.compile(find_pattern, flag)


def TestTextElement(text, criteria):
    lines = text.splitlines()
    test_result = []
    result = criteria["pattern"].search(text)
    while result is not None:
        prev_pos = result.span()[1]
        start = TextLenInRowColumn(text[:result.start()])
        end = TextLenInRowColumn(text[:result.end() - 1])
        test_result.append((start, end, "\n".join(lines[start[0]:end[0] + 1])))
        result = criteria["pattern"].search(text, result.end())
        if result is not None and prev_pos == result.end():
            break
    return test_result


def TextMatched(str1, str2):
    return str1 and str2 and (str1.upper() == str2.upper())


PLCOpenParser = GenerateParserFromXSD(paths.AbsNeighbourFile(__file__, "tc6_xml_v201.xsd"))


def PLCOpen_XPath(xpath):
    return etree.XPath(xpath, namespaces=PLCOpenParser.NSMAP)


LOAD_POU_PROJECT_TEMPLATE = """
<project xmlns:ns1="http://www.plcopen.org/xml/tc6_0201"
         xmlns:xhtml="http://www.w3.org/1999/xhtml"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema"
         xmlns="http://www.plcopen.org/xml/tc6_0201">
  <fileHeader companyName="" productName="" productVersion=""
              creationDateTime="1970-01-01T00:00:00"/>
  <contentHeader name="paste_project">
    <coordinateInfo>
      <fbd><scaling x="0" y="0"/></fbd>
      <ld><scaling x="0" y="0"/></ld>
      <sfc><scaling x="0" y="0"/></sfc>
    </coordinateInfo>
  </contentHeader>
  <types>
    <dataTypes/>
    <pous>%s</pous>
  </types>
  <instances>
    <configurations/>
  </instances>
</project>
"""


def LOAD_POU_INSTANCES_PROJECT_TEMPLATE(body_type):
    return LOAD_POU_PROJECT_TEMPLATE % """
<pou name="paste_pou" pouType="program">
  <body>
    <%(body_type)s>%%s</%(body_type)s>
  </body>
</pou>""" % locals()


PLCOpen_v1_file = open(paths.AbsNeighbourFile(__file__, "TC6_XML_V10_B.xsd"))
PLCOpen_v1_xml = PLCOpen_v1_file.read()
PLCOpen_v1_file.close()
PLCOpen_v1_xml = PLCOpen_v1_xml.replace(
    "http://www.plcopen.org/xml/tc6.xsd",
    "http://www.plcopen.org/xml/tc6_0201")
PLCOpen_v1_xsd = etree.XMLSchema(etree.fromstring(PLCOpen_v1_xml))

# XPath for file compatibility process
ProjectResourcesXPath = PLCOpen_XPath("ppx:instances/ppx:configurations/ppx:configuration/ppx:resource")
ResourceInstancesXpath = PLCOpen_XPath("ppx:pouInstance | ppx:task/ppx:pouInstance")
TransitionsConditionXPath = PLCOpen_XPath("ppx:types/ppx:pous/ppx:pou/ppx:body/*/ppx:transition/ppx:condition")
ConditionConnectionsXPath = PLCOpen_XPath("ppx:connection")
ActionBlocksXPath = PLCOpen_XPath("ppx:types/ppx:pous/ppx:pou/ppx:body/*/ppx:actionBlock")
ActionBlocksConnectionPointOutXPath = PLCOpen_XPath("ppx:connectionPointOut")


def LoadProjectXML(project_xml):
    project_xml = project_xml.replace(
        "http://www.plcopen.org/xml/tc6.xsd",
        "http://www.plcopen.org/xml/tc6_0201")
    for cre, repl in [
            (re.compile(r"(?<!<xhtml:p>)(?:<!\[CDATA\[)"), "<xhtml:p><![CDATA["),
            (re.compile(r"(?:]]>)(?!</xhtml:p>)"), "]]></xhtml:p>")]:
        project_xml = cre.sub(repl, project_xml)

    try:
        tree, error = PLCOpenParser.LoadXMLString(project_xml)
        if error is None:
            return tree, None

        if PLCOpen_v1_xsd.validate(tree):
            # Make file compatible with PLCOpen v2

            # Update resource interval value
            for resource in ProjectResourcesXPath(tree):
                for task in resource.gettask():
                    interval = task.get("interval")
                    if interval is not None:
                        result = time_model.match(interval)
                        if result is not None:
                            values = result.groups()
                            time_values = [int(v) for v in values[:2]]
                            seconds = float(values[2])
                            time_values.extend([int(seconds), int((seconds % 1) * 1000000)])
                            text = "T#"
                            if time_values[0] != 0:
                                text += "%dh" % time_values[0]
                            if time_values[1] != 0:
                                text += "%dm" % time_values[1]
                            if time_values[2] != 0:
                                text += "%ds" % time_values[2]
                            if time_values[3] != 0:
                                if time_values[3] % 1000 != 0:
                                    text += "%.3fms" % (time_values[3] / 1000)
                                else:
                                    text += "%dms" % (time_values[3] // 1000)
                            task.set("interval", text)

                # Update resources pou instance attributes
                for pouInstance in ResourceInstancesXpath(resource):
                    type_name = pouInstance.attrib.pop("type")
                    if type_name is not None:
                        pouInstance.set("typeName", type_name)

            # Update transitions condition
            for transition_condition in TransitionsConditionXPath(tree):
                connections = ConditionConnectionsXPath(transition_condition)
                if len(connections) > 0:
                    connectionPointIn = PLCOpenParser.CreateElement("connectionPointIn", "condition")
                    transition_condition.setcontent(connectionPointIn)
                    connectionPointIn.setrelPositionXY(0, 0)
                    for connection in connections:
                        connectionPointIn.append(connection)

            # Update actionBlocks
            for actionBlock in ActionBlocksXPath(tree):
                for connectionPointOut in ActionBlocksConnectionPointOutXPath(actionBlock):
                    actionBlock.remove(connectionPointOut)

                for action in actionBlock.getaction():
                    action.set("localId", "0")
                    relPosition = PLCOpenParser.CreateElement("relPosition", "action")
                    relPosition.set("x", "0")
                    relPosition.set("y", "0")
                    action.setrelPosition(relPosition)

            return tree, None

        return tree, error

    except Exception as e:
        return None, str(e)


def LoadProject(filepath):
    project_file = open(filepath)
    project_xml = project_file.read()
    project_file.close()
    return LoadProjectXML(project_xml)


project_pou_xpath = PLCOpen_XPath("/ppx:project/ppx:types/ppx:pous/ppx:pou")


def LoadPou(xml_string):
    root, error = LoadProjectXML(LOAD_POU_PROJECT_TEMPLATE % xml_string)
    return project_pou_xpath(root)[0], error


project_pou_instances_xpath = {
    body_type: PLCOpen_XPath(
        "/ppx:project/ppx:types/ppx:pous/ppx:pou[@name='paste_pou']/ppx:body/ppx:%s/*" % body_type)
    for body_type in ["FBD", "LD", "SFC"]}


def LoadPouInstances(xml_string, body_type):
    root, error = LoadProjectXML(
        LOAD_POU_INSTANCES_PROJECT_TEMPLATE(body_type) % xml_string)
    return project_pou_instances_xpath[body_type](root), error


def SaveProject(project, filepath):
    project_file = open(filepath, 'w')
    project_file.write(etree.tostring(
        project,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf-8'))
    project_file.close()


# ----------------------------------------------------------------------


def _updateFormattedTextClass(cls):
    def updateElementName(self, old_name, new_name):
        text = self.getanyText()
        pattern = re.compile('\\b' + old_name + '\\b', re.IGNORECASE)
        text = pattern.sub(new_name, text)
        self.setanyText(text)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        text = self.getanyText()
        startpos = 0
        result = address_model.search(text, startpos)
        while result is not None:
            groups = result.groups()
            new_address = groups[0] + new_leading + groups[2]
            text = text[:result.start()] + new_address + text[result.end():]
            startpos = result.start() + len(new_address)
            result = address_model.search(text, startpos)
        self.setanyText(text)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def hasblock(self, block_type):
        text = self.getanyText()
        pattern = re.compile('\\b' + block_type + '\\b', re.IGNORECASE)
        return pattern.search(text) is not None
    setattr(cls, "hasblock", hasblock)

    def Search(self, criteria, parent_infos):
        return [(tuple(parent_infos),) + result for result in TestTextElement(self.getanyText(), criteria)]
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("formattedText")
if cls:
    _updateFormattedTextClass(cls)


# ----------------------------------------------------------------------


def _updateProjectClass(cls):
    def setname(self, name):
        self.contentHeader.setname(name)
    setattr(cls, "setname", setname)

    def getname(self):
        return self.contentHeader.getname()
    setattr(cls, "getname", getname)

    def getfileHeader(self):
        fileheader_obj = self.fileHeader
        return {
            attr: value if value is not None else ""
            for attr, value in [
                ("companyName", fileheader_obj.getcompanyName()),
                ("companyURL", fileheader_obj.getcompanyURL()),
                ("productName", fileheader_obj.getproductName()),
                ("productVersion", fileheader_obj.getproductVersion()),
                ("productRelease", fileheader_obj.getproductRelease()),
                ("creationDateTime", fileheader_obj.getcreationDateTime()),
                ("contentDescription", fileheader_obj.getcontentDescription())]
        }
    setattr(cls, "getfileHeader", getfileHeader)

    def setfileHeader(self, fileheader):
        fileheader_obj = self.fileHeader
        for attr in ["companyName", "companyURL", "productName",
                     "productVersion", "productRelease", "creationDateTime",
                     "contentDescription"]:
            value = fileheader.get(attr)
            if value is not None:
                setattr(fileheader_obj, attr, value)
    setattr(cls, "setfileHeader", setfileHeader)

    def getcontentHeader(self):
        contentheader_obj = self.contentHeader
        contentheader = {
            attr: value if value is not None else ""
            for attr, value in [
                ("projectName", contentheader_obj.getname()),
                ("projectVersion", contentheader_obj.getversion()),
                ("modificationDateTime", contentheader_obj.getmodificationDateTime()),
                ("organization", contentheader_obj.getorganization()),
                ("authorName", contentheader_obj.getauthor()),
                ("language", contentheader_obj.getlanguage())]
        }
        contentheader["pageSize"] = self.contentHeader.getpageSize()
        contentheader["scaling"] = self.contentHeader.getscaling()
        return contentheader
    setattr(cls, "getcontentHeader", getcontentHeader)

    def setcontentHeader(self, contentheader):
        contentheader_obj = self.contentHeader
        for attr, value in contentheader.iteritems():
            func = {"projectName": contentheader_obj.setname,
                    "projectVersion": contentheader_obj.setversion,
                    "authorName": contentheader_obj.setauthor,
                    "pageSize": lambda v: contentheader_obj.setpageSize(*v),
                    "scaling": contentheader_obj.setscaling}.get(attr)
            if func is not None and value is not None:
                func(value)
            elif attr in ["modificationDateTime", "organization", "language"]:
                setattr(contentheader_obj, attr, value)
    setattr(cls, "setcontentHeader", setcontentHeader)

    def gettypeElementFunc(element_type):
        elements_xpath = PLCOpen_XPath(
            "ppx:types/ppx:%(element_type)ss/ppx:%(element_type)s[@name=$name]" % locals())

        def gettypeElement(self, name):
            elements = elements_xpath(self, name=name)
            if len(elements) == 1:
                return elements[0]
            return None
        return gettypeElement

    datatypes_xpath = PLCOpen_XPath("ppx:types/ppx:dataTypes/ppx:dataType")
    filtered_datatypes_xpath = PLCOpen_XPath(
        "ppx:types/ppx:dataTypes/ppx:dataType[@name!=$exclude]")

    def getdataTypes(self, exclude=None):
        if exclude is not None:
            return filtered_datatypes_xpath(self, exclude=exclude)
        return datatypes_xpath(self)
    setattr(cls, "getdataTypes", getdataTypes)

    setattr(cls, "getdataType", gettypeElementFunc("dataType"))

    def appenddataType(self, name):
        if self.getdataType(name) is not None:
            raise ValueError("\"%s\" Data Type already exists !!!" % name)
        self.types.appenddataTypeElement(name)
    setattr(cls, "appenddataType", appenddataType)

    def insertdataType(self, index, datatype):
        self.types.insertdataTypeElement(index, datatype)
    setattr(cls, "insertdataType", insertdataType)

    def removedataType(self, name):
        self.types.removedataTypeElement(name)
    setattr(cls, "removedataType", removedataType)

    def getpous(self, exclude=None, filter=None):
        filter = [] if filter is None else filter
        return self.xpath(
            "ppx:types/ppx:pous/ppx:pou%s%s" %
            (("[@name!='%s']" % exclude) if exclude is not None else '',
             ("[%s]" % " or ".join(
                 map(lambda x: "@pouType='%s'" % x, filter)))
             if len(filter) > 0 else ""),
            namespaces=PLCOpenParser.NSMAP)
    setattr(cls, "getpous", getpous)

    setattr(cls, "getpou", gettypeElementFunc("pou"))

    def appendpou(self, name, pou_type, body_type):
        self.types.appendpouElement(name, pou_type, body_type)
    setattr(cls, "appendpou", appendpou)

    def insertpou(self, index, pou):
        self.types.insertpouElement(index, pou)
    setattr(cls, "insertpou", insertpou)

    def removepou(self, name):
        self.types.removepouElement(name)
    setattr(cls, "removepou", removepou)

    configurations_xpath = PLCOpen_XPath(
        "ppx:instances/ppx:configurations/ppx:configuration")

    def getconfigurations(self):
        return configurations_xpath(self)
    setattr(cls, "getconfigurations", getconfigurations)

    configuration_xpath = PLCOpen_XPath(
        "ppx:instances/ppx:configurations/ppx:configuration[@name=$name]")

    def getconfiguration(self, name):
        configurations = configuration_xpath(self, name=name)
        if len(configurations) == 1:
            return configurations[0]
        return None
    setattr(cls, "getconfiguration", getconfiguration)

    def addconfiguration(self, name):
        if self.getconfiguration(name) is not None:
            raise ValueError(_("\"%s\" configuration already exists !!!") % name)
        new_configuration = PLCOpenParser.CreateElement("configuration", "configurations")
        new_configuration.setname(name)
        self.instances.configurations.appendconfiguration(new_configuration)
    setattr(cls, "addconfiguration", addconfiguration)

    def removeconfiguration(self, name):
        configuration = self.getconfiguration(name)
        if configuration is None:
            raise ValueError(_("\"%s\" configuration doesn't exist !!!") % name)
        self.instances.configurations.remove(configuration)
    setattr(cls, "removeconfiguration", removeconfiguration)

    resources_xpath = PLCOpen_XPath(
        "ppx:instances/ppx:configurations/ppx:configuration[@name=$configname]/ppx:resource[@name=$name]")

    def getconfigurationResource(self, config_name, name):
        resources = resources_xpath(self, configname=config_name, name=name)
        if len(resources) == 1:
            return resources[0]
        return None
    setattr(cls, "getconfigurationResource", getconfigurationResource)

    def addconfigurationResource(self, config_name, name):
        if self.getconfigurationResource(config_name, name) is not None:
            raise ValueError(
                _("\"{a1}\" resource already exists in \"{a2}\" configuration !!!").
                format(a1=name, a2=config_name))

        configuration = self.getconfiguration(config_name)
        if configuration is not None:
            new_resource = PLCOpenParser.CreateElement("resource", "configuration")
            new_resource.setname(name)
            configuration.appendresource(new_resource)
    setattr(cls, "addconfigurationResource", addconfigurationResource)

    def removeconfigurationResource(self, config_name, name):
        configuration = self.getconfiguration(config_name)
        found = False
        if configuration is not None:
            resource = self.getconfigurationResource(config_name, name)
            if resource is not None:
                configuration.remove(resource)
                found = True
        if not found:
            raise ValueError(
                _("\"{a1}\" resource doesn't exist in \"{a2}\" configuration !!!").
                format(a1=name, a2=config_name))

    setattr(cls, "removeconfigurationResource", removeconfigurationResource)

    def updateElementName(self, old_name, new_name):
        for datatype in self.getdataTypes():
            datatype.updateElementName(old_name, new_name)
        for pou in self.getpous():
            pou.updateElementName(old_name, new_name)
        for configuration in self.getconfigurations():
            configuration.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, old_leading, new_leading):
        address_model = re.compile(FILTER_ADDRESS_MODEL % old_leading)
        for pou in self.getpous():
            pou.updateElementAddress(address_model, new_leading)
        for configuration in self.getconfigurations():
            configuration.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def removeVariableByAddress(self, address):
        for pou in self.getpous():
            pou.removeVariableByAddress(address)
        for configuration in self.getconfigurations():
            configuration.removeVariableByAddress(address)
    setattr(cls, "removeVariableByAddress", removeVariableByAddress)

    def removeVariableByFilter(self, leading):
        address_model = re.compile(FILTER_ADDRESS_MODEL % leading)
        for pou in self.getpous():
            pou.removeVariableByFilter(address_model)
        for configuration in self.getconfigurations():
            configuration.removeVariableByFilter(address_model)
    setattr(cls, "removeVariableByFilter", removeVariableByFilter)

    enumerated_values_xpath = PLCOpen_XPath(
        "ppx:types/ppx:dataTypes/ppx:dataType/ppx:baseType/ppx:enum/ppx:values/ppx:value")

    def GetEnumeratedDataTypeValues(self):
        return [value.getname() for value in enumerated_values_xpath(self)]
    setattr(cls, "GetEnumeratedDataTypeValues", GetEnumeratedDataTypeValues)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        result = self.types.Search(criteria, parent_infos)
        for configuration in self.instances.configurations.getconfiguration():
            result.extend(configuration.Search(criteria, parent_infos))
        return result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("project")
if cls:
    _updateProjectClass(cls)


# ----------------------------------------------------------------------


def _updateContentHeaderProjectClass(cls):
    def setpageSize(self, width, height):
        self.coordinateInfo.setpageSize(width, height)
    setattr(cls, "setpageSize", setpageSize)

    def getpageSize(self):
        return self.coordinateInfo.getpageSize()
    setattr(cls, "getpageSize", getpageSize)

    def setscaling(self, scaling):
        for language, (x, y) in scaling.items():
            self.coordinateInfo.setscaling(language, x, y)
    setattr(cls, "setscaling", setscaling)

    def getscaling(self):
        scaling = {}
        scaling["FBD"] = self.coordinateInfo.getscaling("FBD")
        scaling["LD"] = self.coordinateInfo.getscaling("LD")
        scaling["SFC"] = self.coordinateInfo.getscaling("SFC")
        return scaling
    setattr(cls, "getscaling", getscaling)


cls = PLCOpenParser.GetElementClass("contentHeader", "project")
if cls:
    _updateContentHeaderProjectClass(cls)


# ----------------------------------------------------------------------


def _updateCoordinateInfoContentHeaderClass(cls):
    def setpageSize(self, width, height):
        if width == 0 and height == 0:
            self.deletepageSize()
        else:
            if self.pageSize is None:
                self.addpageSize()
            self.pageSize.setx(width)
            self.pageSize.sety(height)
    setattr(cls, "setpageSize", setpageSize)

    def getpageSize(self):
        if self.pageSize is not None:
            return self.pageSize.getx(), self.pageSize.gety()
        return 0, 0
    setattr(cls, "getpageSize", getpageSize)

    def setscaling(self, language, x, y):
        if language == "FBD":
            self.fbd.scaling.setx(x)
            self.fbd.scaling.sety(y)
        elif language == "LD":
            self.ld.scaling.setx(x)
            self.ld.scaling.sety(y)
        elif language == "SFC":
            self.sfc.scaling.setx(x)
            self.sfc.scaling.sety(y)
    setattr(cls, "setscaling", setscaling)

    def getscaling(self, language):
        if language == "FBD":
            return self.fbd.scaling.getx(), self.fbd.scaling.gety()
        elif language == "LD":
            return self.ld.scaling.getx(), self.ld.scaling.gety()
        elif language == "SFC":
            return self.sfc.scaling.getx(), self.sfc.scaling.gety()
        return 0, 0
    setattr(cls, "getscaling", getscaling)


cls = PLCOpenParser.GetElementClass("coordinateInfo", "contentHeader")
if cls:
    _updateCoordinateInfoContentHeaderClass(cls)


# ----------------------------------------------------------------------


def _Search(attributes, criteria, parent_infos):
    search_result = []
    for attr, value in attributes:
        if value is not None:
            search_result.extend([(tuple(parent_infos + [attr]),) + result for result in TestTextElement(value, criteria)])
    return search_result


def _updateConfigurationResourceElementName(self, old_name, new_name):
    for varlist in self.getglobalVars():
        for var in varlist.getvariable():
            var_address = var.getaddress()
            if var_address is not None:
                if TextMatched(var_address, old_name):
                    var.setaddress(new_name)
                if TextMatched(var.getname(), old_name):
                    var.setname(new_name)


def _updateConfigurationResourceElementAddress(self, address_model, new_leading):
    for varlist in self.getglobalVars():
        for var in varlist.getvariable():
            var_address = var.getaddress()
            if var_address is not None:
                var.setaddress(update_address(var_address, address_model, new_leading))


def _removeConfigurationResourceVariableByAddress(self, address):
    for varlist in self.getglobalVars():
        variables = varlist.getvariable()
        for i in xrange(len(variables)-1, -1, -1):
            if variables[i].getaddress() == address:
                variables.remove(variables[i])


def _removeConfigurationResourceVariableByFilter(self, address_model):
    for varlist in self.getglobalVars():
        variables = varlist.getvariable()
        for i in xrange(len(variables)-1, -1, -1):
            var_address = variables[i].getaddress()
            if var_address is not None:
                result = address_model.match(var_address)
                if result is not None:
                    variables.remove(variables[i])


def _SearchInConfigurationResource(self, criteria, parent_infos=None):
    parent_infos = [] if parent_infos is None else parent_infos
    search_result = _Search([("name", self.getname())], criteria, parent_infos)
    var_number = 0
    for varlist in self.getglobalVars():
        variable_type = searchResultVarTypes.get("globalVars", "var_local")
        variables = varlist.getvariable()
        for modifier, has_modifier in [("constant", varlist.getconstant()),
                                       ("retain", varlist.getretain()),
                                       ("non_retain", varlist.getnonretain())]:
            if has_modifier:
                for result in TestTextElement(modifier, criteria):
                    search_result.append((tuple(parent_infos + [variable_type, (var_number, var_number + len(variables)), modifier]),) + result)
                break
        for variable in variables:
            search_result.extend(variable.Search(criteria, parent_infos + [variable_type, var_number]))
            var_number += 1
    return search_result


# ----------------------------------------------------------------------


def _updateConfigurationConfigurationsClass(cls):
    def addglobalVar(self, var_type, name, location="", description=""):
        globalvars = self.getglobalVars()
        if len(globalvars) == 0:
            globalvars.append(PLCOpenParser.CreateElement("varList"))
        var = PLCOpenParser.CreateElement("variable", "varListPlain")
        var.setname(name)
        var.settype(var_type)
        if location != "":
            var.setaddress(location)
        if description != "":
            ft = PLCOpenParser.CreateElement("documentation", "variable")
            ft.setanyText(description)
            var.setdocumentation(ft)
        globalvars[-1].appendvariable(var)
    setattr(cls, "addglobalVar", addglobalVar)

    def updateElementName(self, old_name, new_name):
        _updateConfigurationResourceElementName(self, old_name, new_name)
        for resource in self.getresource():
            resource.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        _updateConfigurationResourceElementAddress(self, address_model, new_leading)
        for resource in self.getresource():
            resource.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    setattr(cls, "removeVariableByAddress", _removeConfigurationResourceVariableByAddress)
    setattr(cls, "removeVariableByFilter", _removeConfigurationResourceVariableByFilter)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = []
        parent_infos = parent_infos + ["C::%s" % self.getname()]
        filter = criteria["filter"]
        if filter == "all" or "configuration" in filter:
            search_result = _SearchInConfigurationResource(self, criteria, parent_infos)
            for resource in self.getresource():
                search_result.extend(resource.Search(criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("configuration", "configurations")
if cls:
    _updateConfigurationConfigurationsClass(cls)


# ----------------------------------------------------------------------


def _updateResourceConfigurationClass(cls):
    def updateElementName(self, old_name, new_name):
        _updateConfigurationResourceElementName(self, old_name, new_name)
        for instance in self.getpouInstance():
            instance.updateElementName(old_name, new_name)
        for task in self.gettask():
            task.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        _updateConfigurationResourceElementAddress(self, address_model, new_leading)
        for task in self.gettask():
            task.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    setattr(cls, "removeVariableByAddress", _removeConfigurationResourceVariableByAddress)
    setattr(cls, "removeVariableByFilter", _removeConfigurationResourceVariableByFilter)

    def Search(self, criteria, parent_infos=None):
        # FIXME  : two next lines are incompatible [][-1] raises exception !
        parent_infos = [] if parent_infos is None else parent_infos
        parent_infos = parent_infos[:-1] + ["R::%s::%s" % (parent_infos[-1].split("::")[1], self.getname())]
        search_result = _SearchInConfigurationResource(self, criteria, parent_infos)
        task_number = 0
        instance_number = 0
        for task in self.gettask():
            results = TestTextElement(task.getname(), criteria)
            for result in results:
                search_result.append((tuple(parent_infos + ["task", task_number, "name"]),) + result)
            search_result.extend(task.Search(criteria, parent_infos + ["task", task_number]))
            task_number += 1
            for instance in task.getpouInstance():
                search_result.extend(task.Search(criteria, parent_infos + ["instance", instance_number]))
                for result in results:
                    search_result.append((tuple(parent_infos + ["instance", instance_number, "task"]),) + result)
                instance_number += 1
        for instance in self.getpouInstance():
            search_result.extend(instance.Search(criteria, parent_infos + ["instance", instance_number]))
            instance_number += 1
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("resource", "configuration")
if cls:
    _updateResourceConfigurationClass(cls)


# ----------------------------------------------------------------------


def _updateTaskResourceClass(cls):
    def updateElementName(self, old_name, new_name):
        if TextMatched(self.single, old_name):
            self.single = new_name
        if TextMatched(self.interval, old_name):
            self.interval = new_name
        for instance in self.getpouInstance():
            instance.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        if self.single is not None:
            self.single = update_address(self.single, address_model, new_leading)
        if self.interval is not None:
            self.interval = update_address(self.interval, address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        return _Search([("single", self.getsingle()),
                        ("interval", self.getinterval()),
                        ("priority", str(self.getpriority()))],
                       criteria, parent_infos)
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("task", "resource")
if cls:
    _updateTaskResourceClass(cls)


# ----------------------------------------------------------------------


def _updatePouInstanceClass(cls):
    def updateElementName(self, old_name, new_name):
        if TextMatched(self.typeName, old_name):
            self.typeName = new_name
    setattr(cls, "updateElementName", updateElementName)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        return _Search([("name", self.getname()),
                        ("type", self.gettypeName())],
                       criteria, parent_infos)
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("pouInstance")
if cls:
    _updatePouInstanceClass(cls)


# ----------------------------------------------------------------------


def _updateVariableVarListPlain(cls):
    def gettypeAsText(self):
        vartype_content = self.gettype().getcontent()
        vartype_content_name = vartype_content.getLocalTag()
        # Variable type is a user data type
        if vartype_content_name == "derived":
            return vartype_content.getname()
        # Variable type is a string type
        elif vartype_content_name in ["string", "wstring"]:
            return vartype_content_name.upper()
        # Variable type is an array
        elif vartype_content_name == "array":
            base_type = vartype_content.baseType.getcontent()
            base_type_name = base_type.getLocalTag()
            # Array derived directly from a user defined type
            if base_type_name == "derived":
                basetype_name = base_type.getname()
            # Array derived directly from a string type
            elif base_type_name in ["string", "wstring"]:
                basetype_name = base_type_name.upper()
            # Array derived directly from an elementary type
            else:
                basetype_name = base_type_name
            return "ARRAY [%s] OF %s" % (",".join(map(lambda x: "%s..%s" % (x.getlower(), x.getupper()), vartype_content.getdimension())), basetype_name)
        # Variable type is an elementary type
        return vartype_content_name
    setattr(cls, "gettypeAsText", gettypeAsText)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = _Search([("name", self.getname()),
                                 ("type", self.gettypeAsText()),
                                 ("location", self.getaddress())],
                                criteria, parent_infos)
        initial = self.getinitialValue()
        if initial is not None:
            search_result.extend(_Search([("initial value", initial.getvalue())], criteria, parent_infos))
        doc = self.getdocumentation()
        if doc is not None:
            search_result.extend(doc.Search(criteria, parent_infos + ["documentation"]))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("variable", "varListPlain")
if cls:
    _updateVariableVarListPlain(cls)


# ----------------------------------------------------------------------


def _updateTypesProjectClass(cls):
    def getdataTypeElements(self):
        return self.dataTypes.getdataType()
    setattr(cls, "getdataTypeElements", getdataTypeElements)

    def getdataTypeElement(self, name):
        elements = self.dataTypes.getdataType()
        for element in elements:
            if TextMatched(element.getname(), name):
                return element
        return None
    setattr(cls, "getdataTypeElement", getdataTypeElement)

    def appenddataTypeElement(self, name):
        new_datatype = PLCOpenParser.CreateElement("dataType", "dataTypes")
        self.dataTypes.appenddataType(new_datatype)
        new_datatype.setname(name)
        new_datatype.baseType.setcontent(PLCOpenParser.CreateElement("BOOL", "dataType"))
    setattr(cls, "appenddataTypeElement", appenddataTypeElement)

    def insertdataTypeElement(self, index, dataType):
        self.dataTypes.insertdataType(index, dataType)
    setattr(cls, "insertdataTypeElement", insertdataTypeElement)

    def removedataTypeElement(self, name):
        found = False
        for element in self.dataTypes.getdataType():
            if TextMatched(element.getname(), name):
                self.dataTypes.remove(element)
                found = True
                break
        if not found:
            raise ValueError(_("\"%s\" Data Type doesn't exist !!!") % name)
    setattr(cls, "removedataTypeElement", removedataTypeElement)

    def getpouElements(self):
        return self.pous.getpou()
    setattr(cls, "getpouElements", getpouElements)

    def getpouElement(self, name):
        elements = self.pous.getpou()
        for element in elements:
            if TextMatched(element.getname(), name):
                return element
        return None
    setattr(cls, "getpouElement", getpouElement)

    def appendpouElement(self, name, pou_type, body_type):
        for element in self.pous.getpou():
            if TextMatched(element.getname(), name):
                raise ValueError(_("\"%s\" POU already exists !!!") % name)
        new_pou = PLCOpenParser.CreateElement("pou", "pous")
        self.pous.appendpou(new_pou)
        new_pou.setname(name)
        new_pou.setpouType(pou_type)
        new_pou.appendbody(PLCOpenParser.CreateElement("body", "pou"))
        new_pou.setbodyType(body_type)
    setattr(cls, "appendpouElement", appendpouElement)

    def insertpouElement(self, index, pou):
        self.pous.insertpou(index, pou)
    setattr(cls, "insertpouElement", insertpouElement)

    def removepouElement(self, name):
        found = False
        for element in self.pous.getpou():
            if TextMatched(element.getname(), name):
                self.pous.remove(element)
                found = True
                break
        if not found:
            raise ValueError(_("\"%s\" POU doesn't exist !!!") % name)
    setattr(cls, "removepouElement", removepouElement)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = []
        for datatype in self.dataTypes.getdataType():
            search_result.extend(datatype.Search(criteria, parent_infos))
        for pou in self.pous.getpou():
            search_result.extend(pou.Search(criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("types", "project")
if cls:
    _updateTypesProjectClass(cls)


# ----------------------------------------------------------------------


def _updateBaseTypeElementName(self, old_name, new_name):
    self.baseType.updateElementName(old_name, new_name)


def _updateDataTypeDataTypesClass(cls):
    setattr(cls, "updateElementName", _updateBaseTypeElementName)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = []
        filter = criteria["filter"]
        if filter == "all" or "datatype" in filter:
            parent_infos = parent_infos + ["D::%s" % self.getname()]
            search_result.extend(_Search([("name", self.getname())], criteria, parent_infos))
            search_result.extend(self.baseType.Search(criteria, parent_infos))
            if self.initialValue is not None:
                search_result.extend(_Search([("initial", self.initialValue.getvalue())], criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("dataType", "dataTypes")
if cls:
    _updateDataTypeDataTypesClass(cls)


# ----------------------------------------------------------------------


def _updateDataTypeClass(cls):
    def updateElementName(self, old_name, new_name):
        content_name = self.content.getLocalTag()
        if content_name in ["derived", "array", "subrangeSigned", "subrangeUnsigned"]:
            self.content.updateElementName(old_name, new_name)
        elif content_name == "struct":
            for element in self.content.getvariable():
                element.type.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = []
        content_name = self.content.getLocalTag()
        if content_name in ["derived", "array", "enum", "subrangeSigned", "subrangeUnsigned"]:
            search_result.extend(self.content.Search(criteria, parent_infos + ["base"]))
        elif content_name == "struct":
            for i, element in enumerate(self.content.getvariable()):
                search_result.extend(element.Search(criteria, parent_infos + ["struct", i]))
        else:
            if content_name in ["string", "wstring"]:
                content_name = content_name.upper()
            search_result.extend(_Search([("base", content_name)], criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("dataType")
if cls:
    _updateDataTypeClass(cls)


# ----------------------------------------------------------------------


def _updateDerivedDataTypeClass(cls):
    def updateElementName(self, old_name, new_name):
        if TextMatched(self.name, old_name):
            self.name = new_name
    setattr(cls, "updateElementName", updateElementName)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        return [(tuple(parent_infos),) + result for result in TestTextElement(self.name, criteria)]
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("derived", "dataType")
if cls:
    _updateDerivedDataTypeClass(cls)


# ----------------------------------------------------------------------


def _updateArrayDataTypeClass(cls):
    setattr(cls, "updateElementName", _updateBaseTypeElementName)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = self.baseType.Search(criteria, parent_infos)
        for i, dimension in enumerate(self.getdimension()):
            search_result.extend(_Search([("lower", dimension.getlower()),
                                          ("upper", dimension.getupper())],
                                         criteria, parent_infos + ["range", i]))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("array", "dataType")
if cls:
    _updateArrayDataTypeClass(cls)


# ----------------------------------------------------------------------


def _SearchInSubrange(self, criteria, parent_infos=None):
    parent_infos = [] if parent_infos is None else parent_infos
    search_result = self.baseType.Search(criteria, parent_infos)
    search_result.extend(_Search([("lower", self.range.getlower()),
                                  ("upper", self.range.getupper())],
                                 criteria, parent_infos))
    return search_result


cls = PLCOpenParser.GetElementClass("subrangeSigned", "dataType")
if cls:
    setattr(cls, "updateElementName", _updateBaseTypeElementName)
    setattr(cls, "Search", _SearchInSubrange)


# ----------------------------------------------------------------------


cls = PLCOpenParser.GetElementClass("subrangeUnsigned", "dataType")
if cls:
    setattr(cls, "updateElementName", _updateBaseTypeElementName)
    setattr(cls, "Search", _SearchInSubrange)


# ----------------------------------------------------------------------


def _updateEnumDataTypeClass(cls):
    def updateElementName(self, old_name, new_name):
        pass
    setattr(cls, "updateElementName", updateElementName)

    enumerated_datatype_values_xpath = PLCOpen_XPath("ppx:values/ppx:value")

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = []
        for i, value in enumerate(enumerated_datatype_values_xpath(self)):
            for result in TestTextElement(value.getname(), criteria):
                search_result.append((tuple(parent_infos + ["value", i]),) + result)
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("enum", "dataType")
if cls:
    _updateEnumDataTypeClass(cls)


# ----------------------------------------------------------------------


def _getvariableTypeinfos(variable_type):
    type_content = variable_type.getcontent()
    type_content_type = type_content.getLocalTag()
    if type_content_type == "derived":
        return type_content.getname()
    return type_content_type.upper()


def _updatePouPousClass(cls):
    def getblockInfos(self):
        block_infos = {
            "name": self.getname(),
            "type": self.getpouType(),
            "extensible": False,
            "inputs": [],
            "outputs": [],
            "comment": self.getdescription()}
        if self.interface is not None:
            return_type = self.interface.getreturnType()
            if return_type is not None:
                block_infos["outputs"].append(
                    ("OUT", _getvariableTypeinfos(return_type), "none"))
            block_infos["inputs"].extend(
                [(var.getname(), _getvariableTypeinfos(var.type), "none")
                 for var in block_inputs_xpath(self)])
            block_infos["outputs"].extend(
                [(var.getname(), _getvariableTypeinfos(var.type), "none")
                 for var in block_outputs_xpath(self)])

        block_infos["usage"] = ("\n (%s) => (%s)" %
                                (", ".join(["%s:%s" % (input[1], input[0])
                                            for input in block_infos["inputs"]]),
                                 ", ".join(["%s:%s" % (output[1], output[0])
                                            for output in block_infos["outputs"]])))
        return block_infos
    setattr(cls, "getblockInfos", getblockInfos)

    def setdescription(self, description):
        doc = self.getdocumentation()
        if doc is None:
            doc = PLCOpenParser.CreateElement("documentation", "pou")
            self.setdocumentation(doc)
        doc.setanyText(description)
    setattr(cls, "setdescription", setdescription)

    def getdescription(self):
        doc = self.getdocumentation()
        if doc is not None:
            return doc.getanyText()
        return ""
    setattr(cls, "getdescription", getdescription)

    def setbodyType(self, body_type):
        if len(self.body) > 0:
            if body_type in ["IL", "ST", "LD", "FBD", "SFC"]:
                self.body[0].setcontent(PLCOpenParser.CreateElement(body_type, "body"))
            else:
                raise ValueError("%s isn't a valid body type!" % type)
    setattr(cls, "setbodyType", setbodyType)

    def getbodyType(self):
        if len(self.body) > 0:
            return self.body[0].getcontent().getLocalTag()
    setattr(cls, "getbodyType", getbodyType)

    def resetexecutionOrder(self):
        if len(self.body) > 0:
            self.body[0].resetexecutionOrder()
    setattr(cls, "resetexecutionOrder", resetexecutionOrder)

    def compileexecutionOrder(self):
        if len(self.body) > 0:
            self.body[0].compileexecutionOrder()
    setattr(cls, "compileexecutionOrder", compileexecutionOrder)

    def setelementExecutionOrder(self, instance, new_executionOrder):
        if len(self.body) > 0:
            self.body[0].setelementExecutionOrder(instance, new_executionOrder)
    setattr(cls, "setelementExecutionOrder", setelementExecutionOrder)

    def addinstance(self, instance):
        if len(self.body) > 0:
            self.body[0].appendcontentInstance(instance)
    setattr(cls, "addinstance", addinstance)

    def getinstances(self):
        if len(self.body) > 0:
            return self.body[0].getcontentInstances()
        return []
    setattr(cls, "getinstances", getinstances)

    def getinstance(self, id):
        if len(self.body) > 0:
            return self.body[0].getcontentInstance(id)
        return None
    setattr(cls, "getinstance", getinstance)

    def getinstancesIds(self):
        if len(self.body) > 0:
            return self.body[0].getcontentInstancesIds()
        return []
    setattr(cls, "getinstancesIds", getinstancesIds)

    def getinstanceByName(self, name):
        if len(self.body) > 0:
            return self.body[0].getcontentInstanceByName(name)
        return None
    setattr(cls, "getinstanceByName", getinstanceByName)

    def removeinstance(self, id):
        if len(self.body) > 0:
            self.body[0].removecontentInstance(id)
    setattr(cls, "removeinstance", removeinstance)

    def settext(self, text):
        if len(self.body) > 0:
            self.body[0].settext(text)
    setattr(cls, "settext", settext)

    def gettext(self):
        if len(self.body) > 0:
            return self.body[0].gettext()
        return ""
    setattr(cls, "gettext", gettext)

    def getvars(self):
        vars = []
        if self.interface is not None:
            reverse_types = {}
            for name, value in VarTypes.items():
                reverse_types[value] = name
            for varlist in self.interface.getcontent():
                vars.append((reverse_types[varlist.getLocalTag()], varlist))
        return vars
    setattr(cls, "getvars", getvars)

    def setvars(self, vars):
        if self.interface is None:
            self.interface = PLCOpenParser.CreateElement("interface", "pou")
        self.interface.setcontent(vars)
    setattr(cls, "setvars", setvars)

    def addpouExternalVar(self, var_type, name):
        self.addpouVar(var_type, name, "externalVars")
    setattr(cls, "addpouExternalVar", addpouExternalVar)

    def addpouVar(self, var_type, name, var_class="localVars", location="", description="", initval=""):
        if self.interface is None:
            self.interface = PLCOpenParser.CreateElement("interface", "pou")
        content = self.interface.getcontent()
        if len(content) == 0:
            varlist = PLCOpenParser.CreateElement(var_class, "interface")
            self.interface.setcontent([varlist])
        elif content[-1].getLocalTag() != var_class:
            varlist = PLCOpenParser.CreateElement(var_class, "interface")
            content[-1].addnext(varlist)
        else:
            varlist = content[-1]
            variables = varlist.getvariable()
            if varlist.getconstant() or varlist.getretain() or len(variables) > 0 and variables[0].getaddress():
                varlist = PLCOpenParser.CreateElement(var_class, "interface")
                content[-1].addnext(varlist)
        var = PLCOpenParser.CreateElement("variable", "varListPlain")
        var.setname(name)
        var.settype(var_type)
        if location != "":
            var.setaddress(location)
        if description != "":
            ft = PLCOpenParser.CreateElement("documentation", "variable")
            ft.setanyText(description)
            var.setdocumentation(ft)
        if initval != "":
            el = PLCOpenParser.CreateElement("initialValue", "variable")
            el.setvalue(initval)
            var.setinitialValue(el)

        varlist.appendvariable(var)
    setattr(cls, "addpouVar", addpouVar)
    setattr(cls, "addpouLocalVar", addpouVar)

    def changepouVar(self, old_type, old_name, new_type, new_name):
        if self.interface is not None:
            content = self.interface.getcontent()
            for varlist in content:
                variables = varlist.getvariable()
                for var in variables:
                    if TextMatched(var.getname(), old_name):
                        vartype_content = var.gettype().getcontent()
                        if vartype_content.getLocalTag() == "derived" and TextMatched(vartype_content.getname(), old_type):
                            var.setname(new_name)
                            vartype_content.setname(new_type)
                            return
    setattr(cls, "changepouVar", changepouVar)

    def removepouVar(self, var_type, name):
        if self.interface is not None:
            content = self.interface.getcontent()
            for varlist in content:
                for var in varlist.getvariable():
                    if TextMatched(var.getname(), name):
                        vartype_content = var.gettype().getcontent()
                        if vartype_content.getLocalTag() == "derived" and TextMatched(vartype_content.getname(), var_type):
                            varlist.remove(var)
                            if len(varlist.getvariable()) == 0:
                                self.interface.remove(varlist)
                            break
    setattr(cls, "removepouVar", removepouVar)

    def hasstep(self, name=None):
        if self.getbodyType() in ["SFC"]:
            for instance in self.getinstances():
                if isinstance(instance, PLCOpenParser.GetElementClass("step", "sfcObjects")) and TextMatched(instance.getname(), name):
                    return True
        return False
    setattr(cls, "hasstep", hasstep)

    def hasblock(self, name=None, block_type=None):
        if self.getbodyType() in ["FBD", "LD", "SFC"]:
            for instance in self.getinstances():
                if isinstance(instance, PLCOpenParser.GetElementClass("block", "fbdObjects")) \
                   and (TextMatched(instance.getinstanceName(), name) or
                        TextMatched(instance.gettypeName(), block_type)):
                    return True
            if self.transitions:
                for transition in self.transitions.gettransition():
                    result = transition.hasblock(name, block_type)
                    if result:
                        return result
            if self.actions:
                for action in self.actions.getaction():
                    result = action.hasblock(name, block_type)
                    if result:
                        return result
        elif block_type is not None and len(self.body) > 0:
            return self.body[0].hasblock(block_type)
        return False
    setattr(cls, "hasblock", hasblock)

    def addtransition(self, name, body_type):
        if self.transitions is None:
            self.addtransitions()
            self.transitions.settransition([])
        transition = PLCOpenParser.CreateElement("transition", "transitions")
        self.transitions.appendtransition(transition)
        transition.setname(name)
        transition.setbodyType(body_type)
        if body_type == "ST":
            transition.settext(":= ;")
    setattr(cls, "addtransition", addtransition)

    def gettransition(self, name):
        if self.transitions is not None:
            for transition in self.transitions.gettransition():
                if TextMatched(transition.getname(), name):
                    return transition
        return None
    setattr(cls, "gettransition", gettransition)

    def gettransitionList(self):
        if self.transitions is not None:
            return self.transitions.gettransition()
        return []
    setattr(cls, "gettransitionList", gettransitionList)

    def removetransition(self, name):
        if self.transitions is not None:
            removed = False
            for transition in self.transitions.gettransition():
                if TextMatched(transition.getname(), name):
                    if transition.getbodyType() in ["FBD", "LD", "SFC"]:
                        for instance in transition.getinstances():
                            if isinstance(instance, PLCOpenParser.GetElementClass("block", "fbdObjects")):
                                self.removepouVar(instance.gettypeName(),
                                                  instance.getinstanceName())
                    self.transitions.remove(transition)
                    removed = True
                    break
            if not removed:
                raise ValueError(_("Transition with name %s doesn't exist!") % name)
    setattr(cls, "removetransition", removetransition)

    def addaction(self, name, body_type):
        if self.actions is None:
            self.addactions()
            self.actions.setaction([])
        action = PLCOpenParser.CreateElement("action", "actions")
        self.actions.appendaction(action)
        action.setname(name)
        action.setbodyType(body_type)
    setattr(cls, "addaction", addaction)

    def getaction(self, name):
        if self.actions is not None:
            for action in self.actions.getaction():
                if TextMatched(action.getname(), name):
                    return action
        return None
    setattr(cls, "getaction", getaction)

    def getactionList(self):
        if self.actions is not None:
            return self.actions.getaction()
        return []
    setattr(cls, "getactionList", getactionList)

    def removeaction(self, name):
        if self.actions is not None:
            removed = False
            for action in self.actions.getaction():
                if TextMatched(action.getname(), name):
                    if action.getbodyType() in ["FBD", "LD", "SFC"]:
                        for instance in action.getinstances():
                            if isinstance(instance, PLCOpenParser.GetElementClass("block", "fbdObjects")):
                                self.removepouVar(instance.gettypeName(),
                                                  instance.getinstanceName())
                    self.actions.remove(action)
                    removed = True
                    break
            if not removed:
                raise ValueError(_("Action with name %s doesn't exist!") % name)
    setattr(cls, "removeaction", removeaction)

    def updateElementName(self, old_name, new_name):
        if self.interface is not None:
            for content in self.interface.getcontent():
                for var in content.getvariable():
                    var_address = var.getaddress()
                    if var_address is not None:
                        if TextMatched(var_address, old_name):
                            var.setaddress(new_name)
                        if TextMatched(var.getname(), old_name):
                            var.setname(new_name)
                    var_type_content = var.gettype().getcontent()
                    if var_type_content.getLocalTag() == "derived":
                        if TextMatched(var_type_content.getname(), old_name):
                            var_type_content.setname(new_name)
        self.body[0].updateElementName(old_name, new_name)
        for action in self.getactionList():
            action.updateElementName(old_name, new_name)
        for transition in self.gettransitionList():
            transition.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        if self.interface is not None:
            for content in self.interface.getcontent():
                for var in content.getvariable():
                    var_address = var.getaddress()
                    if var_address is not None:
                        var.setaddress(update_address(var_address, address_model, new_leading))
        self.body[0].updateElementAddress(address_model, new_leading)
        for action in self.getactionList():
            action.updateElementAddress(address_model, new_leading)
        for transition in self.gettransitionList():
            transition.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def removeVariableByAddress(self, address):
        if self.interface is not None:
            for content in self.interface.getcontent():
                for variable in content.getvariable():
                    if TextMatched(variable.getaddress(), address):
                        content.remove(variable)
    setattr(cls, "removeVariableByAddress", removeVariableByAddress)

    def removeVariableByFilter(self, address_model):
        if self.interface is not None:
            for content in self.interface.getcontent():
                for variable in content.getvariable():
                    var_address = variable.getaddress()
                    if var_address is not None:
                        result = address_model.match(var_address)
                        if result is not None:
                            content.remove(variable)
    setattr(cls, "removeVariableByFilter", removeVariableByFilter)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        search_result = []
        filter = criteria["filter"]
        if filter == "all" or self.getpouType() in filter:
            if parent_infos == []:
                parent_infos = parent_infos + ["P::%s" % self.getname()]
            search_result.extend(_Search([("name", self.getname())], criteria, parent_infos))
            if self.interface is not None:
                var_number = 0
                for content in self.interface.getcontent():
                    variable_type = searchResultVarTypes.get(content, "var_local")
                    variables = content.getvariable()
                    for modifier, has_modifier in [("constant", content.getconstant()),
                                                   ("retain", content.getretain()),
                                                   ("non_retain", content.getnonretain())]:
                        if has_modifier:
                            for result in TestTextElement(modifier, criteria):
                                search_result.append((tuple(parent_infos + [variable_type, (var_number, var_number + len(variables)), modifier]),) + result)
                            break
                    for variable in variables:
                        search_result.extend(variable.Search(criteria, parent_infos + [variable_type, var_number]))
                        var_number += 1
            if len(self.body) > 0:
                search_result.extend(self.body[0].Search(criteria, parent_infos))
            for action in self.getactionList():
                search_result.extend(action.Search(criteria, parent_infos))
            for transition in self.gettransitionList():
                search_result.extend(transition.Search(criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("pou", "pous")
if cls:
    block_inputs_xpath = PLCOpen_XPath(
        "ppx:interface/*[self::ppx:inputVars or self::ppx:inOutVars]/ppx:variable")
    block_outputs_xpath = PLCOpen_XPath(
        "ppx:interface/*[self::ppx:outputVars or self::ppx:inOutVars]/ppx:variable")
    _updatePouPousClass(cls)


# ----------------------------------------------------------------------


def setbodyType(self, body_type):
    if body_type in ["IL", "ST", "LD", "FBD", "SFC"]:
        self.body.setcontent(PLCOpenParser.CreateElement(body_type, "body"))
    else:
        raise ValueError("%s isn't a valid body type!" % type)


def getbodyType(self):
    return self.body.getcontent().getLocalTag()


def resetexecutionOrder(self):
    self.body.resetexecutionOrder()


def compileexecutionOrder(self):
    self.body.compileexecutionOrder()


def setelementExecutionOrder(self, instance, new_executionOrder):
    self.body.setelementExecutionOrder(instance, new_executionOrder)


def addinstance(self, instance):
    self.body.appendcontentInstance(instance)


def getinstances(self):
    return self.body.getcontentInstances()


def getinstance(self, id):
    return self.body.getcontentInstance(id)


def getrandomInstance(self, exclude):
    return self.body.getcontentRandomInstance(exclude)


def getinstanceByName(self, name):
    return self.body.getcontentInstanceByName(name)


def removeinstance(self, id):
    self.body.removecontentInstance(id)


def settext(self, text):
    self.body.settext(text)


def gettext(self):
    return self.body.gettext()


def hasblock(self, name=None, block_type=None):
    if self.getbodyType() in ["FBD", "LD", "SFC"]:
        for instance in self.getinstances():
            if isinstance(instance, PLCOpenParser.GetElementClass("block", "fbdObjects")) and \
               (TextMatched(instance.getinstanceName(), name) or TextMatched(instance.gettypeName(), block_type)):
                return True
    elif block_type is not None:
        return self.body.hasblock(block_type)
    return False


def updateElementName(self, old_name, new_name):
    self.body.updateElementName(old_name, new_name)


def updateElementAddress(self, address_model, new_leading):
    self.body.updateElementAddress(address_model, new_leading)


# ----------------------------------------------------------------------

def _updateTransitionTransitionsClass(cls):
    setattr(cls, "setbodyType", setbodyType)
    setattr(cls, "getbodyType", getbodyType)
    setattr(cls, "resetexecutionOrder", resetexecutionOrder)
    setattr(cls, "compileexecutionOrder", compileexecutionOrder)
    setattr(cls, "setelementExecutionOrder", setelementExecutionOrder)
    setattr(cls, "addinstance", addinstance)
    setattr(cls, "getinstances", getinstances)
    setattr(cls, "getinstance", getinstance)
    setattr(cls, "getrandomInstance", getrandomInstance)
    setattr(cls, "getinstanceByName", getinstanceByName)
    setattr(cls, "removeinstance", removeinstance)
    setattr(cls, "settext", settext)
    setattr(cls, "gettext", gettext)
    setattr(cls, "hasblock", hasblock)
    setattr(cls, "updateElementName", updateElementName)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos):
        search_result = []
        parent_infos = parent_infos[:-1] + ["T::%s::%s" % (parent_infos[-1].split("::")[1], self.getname())]
        for result in TestTextElement(self.getname(), criteria):
            search_result.append((tuple(parent_infos + ["name"]),) + result)
        search_result.extend(self.body.Search(criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("transition", "transitions")
if cls:
    _updateTransitionTransitionsClass(cls)


# ----------------------------------------------------------------------


def _updateActionActionsClass(cls):
    setattr(cls, "setbodyType", setbodyType)
    setattr(cls, "getbodyType", getbodyType)
    setattr(cls, "resetexecutionOrder", resetexecutionOrder)
    setattr(cls, "compileexecutionOrder", compileexecutionOrder)
    setattr(cls, "setelementExecutionOrder", setelementExecutionOrder)
    setattr(cls, "addinstance", addinstance)
    setattr(cls, "getinstances", getinstances)
    setattr(cls, "getinstance", getinstance)
    setattr(cls, "getrandomInstance", getrandomInstance)
    setattr(cls, "getinstanceByName", getinstanceByName)
    setattr(cls, "removeinstance", removeinstance)
    setattr(cls, "settext", settext)
    setattr(cls, "gettext", gettext)
    setattr(cls, "hasblock", hasblock)
    setattr(cls, "updateElementName", updateElementName)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos):
        search_result = []
        parent_infos = parent_infos[:-1] + ["A::%s::%s" % (parent_infos[-1].split("::")[1], self.getname())]
        for result in TestTextElement(self.getname(), criteria):
            search_result.append((tuple(parent_infos + ["name"]),) + result)
        search_result.extend(self.body.Search(criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("action", "actions")
if cls:
    _updateActionActionsClass(cls)


# ----------------------------------------------------------------------


def _updateBodyClass(cls):
    cls.currentExecutionOrderId = 0
    cls.checkedBlocksDict = {}

    def resetcurrentExecutionOrderId(self):
        object.__setattr__(self, "currentExecutionOrderId", 0)
    setattr(cls, "resetcurrentExecutionOrderId", resetcurrentExecutionOrderId)

    def getnewExecutionOrderId(self):
        object.__setattr__(self, "currentExecutionOrderId", self.currentExecutionOrderId + 1)
        return self.currentExecutionOrderId
    setattr(cls, "getnewExecutionOrderId", getnewExecutionOrderId)

    def resetexecutionOrder(self):
        if self.content.getLocalTag() == "FBD":
            for element in self.content.getcontent():
                if not isinstance(element, (PLCOpenParser.GetElementClass("comment", "commonObjects"),
                                            PLCOpenParser.GetElementClass("connector", "commonObjects"),
                                            PLCOpenParser.GetElementClass("continuation", "commonObjects"))):
                    element.setexecutionOrderId(0)
            self.checkedBlocksDict.clear()
        else:
            raise TypeError(_("Can only generate execution order on FBD networks!"))
    setattr(cls, "resetexecutionOrder", resetexecutionOrder)

    def compileexecutionOrder(self):
        if self.content.getLocalTag() == "FBD":
            self.resetexecutionOrder()
            self.resetcurrentExecutionOrderId()
            for element in self.content.getcontent():
                if isinstance(element, PLCOpenParser.GetElementClass("outVariable", "fbdObjects")) and element.getexecutionOrderId() == 0:
                    connections = element.connectionPointIn.getconnections()
                    if connections and len(connections) == 1:
                        self.compileelementExecutionOrder(connections[0])
                    element.setexecutionOrderId(self.getnewExecutionOrderId())
        else:
            raise TypeError(_("Can only generate execution order on FBD networks!"))
    setattr(cls, "compileexecutionOrder", compileexecutionOrder)

    def compileelementExecutionOrder(self, link):
        if self.content.getLocalTag() == "FBD":
            localid = link.getrefLocalId()
            instance = self.getcontentInstance(localid)
            self.checkedBlocksDict[localid] = True
            if isinstance(instance, PLCOpenParser.GetElementClass("block", "fbdObjects")) and instance.getexecutionOrderId() == 0:
                for variable in instance.inputVariables.getvariable():
                    connections = variable.connectionPointIn.getconnections()
                    if connections and len(connections) == 1:
                        if not connections[0].getrefLocalId() in self.checkedBlocksDict:
                            self.compileelementExecutionOrder(connections[0])
                if instance.getexecutionOrderId() == 0:
                    instance.setexecutionOrderId(self.getnewExecutionOrderId())
            elif isinstance(instance, PLCOpenParser.GetElementClass("continuation", "commonObjects")) and instance.getexecutionOrderId() == 0:
                for tmp_instance in self.getcontentInstances():
                    if isinstance(tmp_instance, PLCOpenParser.GetElementClass("connector", "commonObjects")) and \
                       TextMatched(tmp_instance.getname(), instance.getname()) and \
                       tmp_instance.getexecutionOrderId() == 0:
                        connections = tmp_instance.connectionPointIn.getconnections()
                        if connections and len(connections) == 1:
                            self.compileelementExecutionOrder(connections[0])
        else:
            raise TypeError(_("Can only generate execution order on FBD networks!"))
    setattr(cls, "compileelementExecutionOrder", compileelementExecutionOrder)

    def setelementExecutionOrder(self, instance, new_executionOrder):
        if self.content.getLocalTag() == "FBD":
            old_executionOrder = instance.getexecutionOrderId()
            if old_executionOrder is not None and old_executionOrder != 0 and new_executionOrder != 0:
                for element in self.content.getcontent():
                    if element != instance and not isinstance(element, PLCOpenParser.GetElementClass("comment", "commonObjects")):
                        element_executionOrder = element.getexecutionOrderId()
                        if old_executionOrder <= element_executionOrder <= new_executionOrder:
                            element.setexecutionOrderId(element_executionOrder - 1)
                        if new_executionOrder <= element_executionOrder <= old_executionOrder:
                            element.setexecutionOrderId(element_executionOrder + 1)
            instance.setexecutionOrderId(new_executionOrder)
        else:
            raise TypeError(_("Can only generate execution order on FBD networks!"))
    setattr(cls, "setelementExecutionOrder", setelementExecutionOrder)

    def appendcontentInstance(self, instance):
        if self.content.getLocalTag() in ["LD", "FBD", "SFC"]:
            self.content.appendcontent(instance)
        else:
            raise TypeError(_("%s body don't have instances!") % self.content.getLocalTag())
    setattr(cls, "appendcontentInstance", appendcontentInstance)

    def getcontentInstances(self):
        if self.content.getLocalTag() in ["LD", "FBD", "SFC"]:
            return self.content.getcontent()
        else:
            raise TypeError(_("%s body don't have instances!") % self.content.getLocalTag())
    setattr(cls, "getcontentInstances", getcontentInstances)

    instance_by_id_xpath = PLCOpen_XPath("*[@localId=$localId]")
    instance_by_name_xpath = PLCOpen_XPath("ppx:block[@instanceName=$name]")

    def getcontentInstance(self, local_id):
        if self.content.getLocalTag() in ["LD", "FBD", "SFC"]:
            instance = instance_by_id_xpath(self.content, localId=local_id)
            if len(instance) > 0:
                return instance[0]
            return None
        else:
            raise TypeError(_("%s body don't have instances!") % self.content.getLocalTag())
    setattr(cls, "getcontentInstance", getcontentInstance)

    def getcontentInstancesIds(self):
        if self.content.getLocalTag() in ["LD", "FBD", "SFC"]:
            return OrderedDict([(instance.getlocalId(), True)
                                for instance in self.content])
        else:
            raise TypeError(_("%s body don't have instances!") % self.content.getLocalTag())
    setattr(cls, "getcontentInstancesIds", getcontentInstancesIds)

    def getcontentInstanceByName(self, name):
        if self.content.getLocalTag() in ["LD", "FBD", "SFC"]:
            instance = instance_by_name_xpath(self.content)
            if len(instance) > 0:
                return instance[0]
            return None
        else:
            raise TypeError(_("%s body don't have instances!") % self.content.getLocalTag())
    setattr(cls, "getcontentInstanceByName", getcontentInstanceByName)

    def removecontentInstance(self, local_id):
        if self.content.getLocalTag() in ["LD", "FBD", "SFC"]:
            instance = instance_by_id_xpath(self.content, localId=local_id)
            if len(instance) > 0:
                self.content.remove(instance[0])
            else:
                raise ValueError(_("Instance with id %d doesn't exist!") % id)
        else:
            raise TypeError(_("%s body don't have instances!") % self.content.getLocalTag())
    setattr(cls, "removecontentInstance", removecontentInstance)

    def settext(self, text):
        if self.content.getLocalTag() in ["IL", "ST"]:
            self.content.setanyText(text)
        else:
            raise TypeError(_("%s body don't have text!") % self.content.getLocalTag())
    setattr(cls, "settext", settext)

    def gettext(self):
        if self.content.getLocalTag() in ["IL", "ST"]:
            return self.content.getanyText()
        else:
            raise TypeError(_("%s body don't have text!") % self.content.getLocalTag())
    setattr(cls, "gettext", gettext)

    def hasblock(self, block_type):
        if self.content.getLocalTag() in ["IL", "ST"]:
            return self.content.hasblock(block_type)
        else:
            raise TypeError(_("%s body don't have text!") % self.content.getLocalTag())
    setattr(cls, "hasblock", hasblock)

    def updateElementName(self, old_name, new_name):
        if self.content.getLocalTag() in ["IL", "ST"]:
            self.content.updateElementName(old_name, new_name)
        else:
            for element in self.content.getcontent():
                element.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        if self.content.getLocalTag() in ["IL", "ST"]:
            self.content.updateElementAddress(address_model, new_leading)
        else:
            for element in self.content.getcontent():
                element.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        if self.content.getLocalTag() in ["IL", "ST"]:
            search_result = self.content.Search(criteria, parent_infos + ["body", 0])
        else:
            search_result = []
            for element in self.content.getcontent():
                search_result.extend(element.Search(criteria, parent_infos))
        return search_result
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("body")
if cls:
    _updateBodyClass(cls)


# ----------------------------------------------------------------------


def getx(self):
    return self.position.getx()


def gety(self):
    return self.position.gety()


def setx(self, x):
    self.position.setx(x)


def sety(self, y):
    self.position.sety(y)


def _getBoundingBox(self):
    return rect(self.getx(), self.gety(), self.getwidth(), self.getheight())


def _getConnectionsBoundingBox(connectionPointIn):
    bbox = rect()
    connections = connectionPointIn.getconnections()
    if connections is not None:
        for connection in connections:
            for x, y in connection.getpoints():
                bbox.update(x, y)
    return bbox


def _getBoundingBoxSingle(self):
    bbox = _getBoundingBox(self)
    if self.connectionPointIn is not None:
        bbox.union(_getConnectionsBoundingBox(self.connectionPointIn))
    return bbox


def _getBoundingBoxMultiple(self):
    bbox = _getBoundingBox(self)
    for connectionPointIn in self.getconnectionPointIn():
        bbox.union(_getConnectionsBoundingBox(connectionPointIn))
    return bbox


def _filterConnections(connectionPointIn, localId, connections):
    in_connections = connectionPointIn.getconnections()
    if in_connections is not None:
        for connection in in_connections:
            connected = connection.getrefLocalId()
            if not (localId, connected) in connections and \
               not (connected, localId) in connections:
                connectionPointIn.remove(connection)


def _filterConnectionsSingle(self, connections):
    if self.connectionPointIn is not None:
        _filterConnections(self.connectionPointIn, self.localId, connections)


def _filterConnectionsMultiple(self, connections):
    for connectionPointIn in self.getconnectionPointIn():
        _filterConnections(connectionPointIn, self.localId, connections)


def _getconnectionsdefinition(instance, connections_end):
    local_id = instance.getlocalId()
    return dict([((local_id, end), True) for end in connections_end])


def _updateConnectionsId(connectionPointIn, translation):
    connections_end = []
    connections = connectionPointIn.getconnections()
    if connections is not None:
        for connection in connections:
            refLocalId = connection.getrefLocalId()
            new_reflocalId = translation.get(refLocalId, refLocalId)
            connection.setrefLocalId(new_reflocalId)
            connections_end.append(new_reflocalId)
    return connections_end


def _updateConnectionsIdSingle(self, translation):
    connections_end = []
    if self.connectionPointIn is not None:
        connections_end = _updateConnectionsId(self.connectionPointIn, translation)
    return _getconnectionsdefinition(self, connections_end)


def _updateConnectionsIdMultiple(self, translation):
    connections_end = []
    for connectionPointIn in self.getconnectionPointIn():
        connections_end.extend(_updateConnectionsId(connectionPointIn, translation))
    return _getconnectionsdefinition(self, connections_end)


def _translate(self, dx, dy):
    self.setx(self.getx() + dx)
    self.sety(self.gety() + dy)


def _translateConnections(connectionPointIn, dx, dy):
    connections = connectionPointIn.getconnections()
    if connections is not None:
        for connection in connections:
            for position in connection.getposition():
                position.setx(position.getx() + dx)
                position.sety(position.gety() + dy)


def _translateSingle(self, dx, dy):
    _translate(self, dx, dy)
    if self.connectionPointIn is not None:
        _translateConnections(self.connectionPointIn, dx, dy)


def _translateMultiple(self, dx, dy):
    _translate(self, dx, dy)
    for connectionPointIn in self.getconnectionPointIn():
        _translateConnections(connectionPointIn, dx, dy)


def _updateElementName(self, old_name, new_name):
    pass


def _updateElementAddress(self, address_model, new_leading):
    pass


def _SearchInElement(self, criteria, parent_infos=None):
    return []


_connectionsFunctions = {
    "bbox": {"none": _getBoundingBox,
             "single": _getBoundingBoxSingle,
             "multiple": _getBoundingBoxMultiple},
    "translate": {"none": _translate,
                  "single": _translateSingle,
                  "multiple": _translateMultiple},
    "filter": {"none": lambda self, connections: None,
               "single": _filterConnectionsSingle,
               "multiple": _filterConnectionsMultiple},
    "update": {"none": lambda self, translation: {},
               "single": _updateConnectionsIdSingle,
               "multiple": _updateConnectionsIdMultiple},
}


def _initElementClass(name, parent, connectionPointInType="none"):
    cls = PLCOpenParser.GetElementClass(name, parent)
    if cls:
        setattr(cls, "getx", getx)
        setattr(cls, "gety", gety)
        setattr(cls, "setx", setx)
        setattr(cls, "sety", sety)
        setattr(cls, "updateElementName", _updateElementName)
        setattr(cls, "updateElementAddress", _updateElementAddress)
        setattr(cls, "getBoundingBox", _connectionsFunctions["bbox"][connectionPointInType])
        setattr(cls, "translate", _connectionsFunctions["translate"][connectionPointInType])
        setattr(cls, "filterConnections", _connectionsFunctions["filter"][connectionPointInType])
        setattr(cls, "updateConnectionsId", _connectionsFunctions["update"][connectionPointInType])
        setattr(cls, "Search", _SearchInElement)
    return cls


# ----------------------------------------------------------------------


def _updateCommentCommonObjectsClass(cls):
    def setcontentText(self, text):
        self.content.setanyText(text)
    setattr(cls, "setcontentText", setcontentText)

    def getcontentText(self):
        return self.content.getanyText()
    setattr(cls, "getcontentText", getcontentText)

    def updateElementName(self, old_name, new_name):
        self.content.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        self.content.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        return self.content.Search(criteria, parent_infos + ["comment", self.getlocalId(), "content"])
    setattr(cls, "Search", Search)


cls = _initElementClass("comment", "commonObjects")
if cls:
    _updateCommentCommonObjectsClass(cls)


# ----------------------------------------------------------------------


def _updateBlockFbdObjectsClass(cls):
    def getBoundingBox(self):
        bbox = _getBoundingBox(self)
        for input in self.inputVariables.getvariable():
            bbox.union(_getConnectionsBoundingBox(input.connectionPointIn))
        return bbox
    setattr(cls, "getBoundingBox", getBoundingBox)

    def updateElementName(self, old_name, new_name):
        if TextMatched(self.typeName, old_name):
            self.typeName = new_name
    setattr(cls, "updateElementName", updateElementName)

    def filterConnections(self, connections):
        for input in self.inputVariables.getvariable():
            _filterConnections(input.connectionPointIn, self.localId, connections)
    setattr(cls, "filterConnections", filterConnections)

    def updateConnectionsId(self, translation):
        connections_end = []
        for input in self.inputVariables.getvariable():
            connections_end.extend(_updateConnectionsId(input.connectionPointIn, translation))
        return _getconnectionsdefinition(self, connections_end)
    setattr(cls, "updateConnectionsId", updateConnectionsId)

    def translate(self, dx, dy):
        _translate(self, dx, dy)
        for input in self.inputVariables.getvariable():
            _translateConnections(input.connectionPointIn, dx, dy)
    setattr(cls, "translate", translate)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        parent_infos = parent_infos + ["block", self.getlocalId()]
        search_result = _Search([("name", self.getinstanceName()),
                                 ("type", self.gettypeName())],
                                criteria, parent_infos)
        for i, variable in enumerate(self.inputVariables.getvariable()):
            for result in TestTextElement(variable.getformalParameter(), criteria):
                search_result.append((tuple(parent_infos + ["input", i]),) + result)
        for i, variable in enumerate(self.outputVariables.getvariable()):
            for result in TestTextElement(variable.getformalParameter(), criteria):
                search_result.append((tuple(parent_infos + ["output", i]),) + result)
        return search_result
    setattr(cls, "Search", Search)


cls = _initElementClass("block", "fbdObjects")
if cls:
    _updateBlockFbdObjectsClass(cls)


# ----------------------------------------------------------------------


_initElementClass("leftPowerRail", "ldObjects")
_initElementClass("rightPowerRail", "ldObjects", "multiple")


def _UpdateLDElementName(self, old_name, new_name):
    if TextMatched(self.variable, old_name):
        self.variable = new_name


def _UpdateLDElementAddress(self, address_model, new_leading):
    self.variable = update_address(self.variable, address_model, new_leading)


def _getSearchInLDElement(ld_element_type):
    def SearchInLDElement(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        return _Search([("reference", self.variable)], criteria, parent_infos + [ld_element_type, self.getlocalId()])
    return SearchInLDElement


# ----------------------------------------------------------------------


cls = _initElementClass("contact", "ldObjects", "single")
if cls:
    setattr(cls, "updateElementName", _UpdateLDElementName)
    setattr(cls, "updateElementAddress", _UpdateLDElementAddress)
    setattr(cls, "Search", _getSearchInLDElement("contact"))


# ----------------------------------------------------------------------


cls = _initElementClass("coil", "ldObjects", "single")
if cls:
    setattr(cls, "updateElementName", _UpdateLDElementName)
    setattr(cls, "updateElementAddress", _UpdateLDElementAddress)
    setattr(cls, "Search", _getSearchInLDElement("coil"))


# ----------------------------------------------------------------------


def _updateStepSfcObjectSingleClass(cls):
    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        return _Search([("name", self.getname())], criteria, parent_infos + ["step", self.getlocalId()])
    setattr(cls, "Search", Search)


cls = _initElementClass("step", "sfcObjects", "single")
if cls:
    _updateStepSfcObjectSingleClass(cls)


# ----------------------------------------------------------------------


def _updateTransitionSfcObjectsClass(cls):
    def setconditionContent(self, condition_type, value):
        if self.condition is None:
            self.addcondition()
        if condition_type == "connection":
            condition = PLCOpenParser.CreateElement("connectionPointIn", "condition")
        else:
            condition = PLCOpenParser.CreateElement(condition_type, "condition")
        self.condition.setcontent(condition)
        if condition_type == "reference":
            condition.setname(value)
        elif condition_type == "inline":
            condition.setcontent(PLCOpenParser.CreateElement("ST", "inline"))
            condition.settext(value)
    setattr(cls, "setconditionContent", setconditionContent)

    def getconditionContent(self):
        if self.condition is not None:
            content = self.condition.getcontent()
            values = {"type": content.getLocalTag()}
            if values["type"] == "reference":
                values["value"] = content.getname()
            elif values["type"] == "inline":
                values["value"] = content.gettext()
            elif values["type"] == "connectionPointIn":
                values["type"] = "connection"
                values["value"] = content
            return values
        return ""
    setattr(cls, "getconditionContent", getconditionContent)

    def getconditionConnection(self):
        if self.condition is not None:
            content = self.condition.getcontent()
            if content.getLocalTag() == "connectionPointIn":
                return content
        return None
    setattr(cls, "getconditionConnection", getconditionConnection)

    def getBoundingBox(self):
        bbox = _getBoundingBoxSingle(self)
        condition_connection = self.getconditionConnection()
        if condition_connection is not None:
            bbox.union(_getConnectionsBoundingBox(condition_connection))
        return bbox
    setattr(cls, "getBoundingBox", getBoundingBox)

    def translate(self, dx, dy):
        _translateSingle(self, dx, dy)
        condition_connection = self.getconditionConnection()
        if condition_connection is not None:
            _translateConnections(condition_connection, dx, dy)
    setattr(cls, "translate", translate)

    def filterConnections(self, connections):
        _filterConnectionsSingle(self, connections)
        condition_connection = self.getconditionConnection()
        if condition_connection is not None:
            _filterConnections(condition_connection, self.localId, connections)
    setattr(cls, "filterConnections", filterConnections)

    def updateConnectionsId(self, translation):
        connections_end = []
        if self.connectionPointIn is not None:
            connections_end = _updateConnectionsId(self.connectionPointIn, translation)
        condition_connection = self.getconditionConnection()
        if condition_connection is not None:
            connections_end.extend(_updateConnectionsId(condition_connection, translation))
        return _getconnectionsdefinition(self, connections_end)
    setattr(cls, "updateConnectionsId", updateConnectionsId)

    def updateElementName(self, old_name, new_name):
        if self.condition is not None:
            content = self.condition.getcontent()
            content_name = content.getLocalTag()
            if content_name == "reference":
                if TextMatched(content.getname(), old_name):
                    content.setname(new_name)
            elif content_name == "inline":
                content.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        if self.condition is not None:
            content = self.condition.getcontent()
            content_name = content.getLocalTag()
            if content_name == "reference":
                content.setname(update_address(content.getname(), address_model, new_leading))
            elif content_name == "inline":
                content.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def getconnections(self):
        condition_connection = self.getconditionConnection()
        if condition_connection is not None:
            return condition_connection.getconnections()
        return None
    setattr(cls, "getconnections", getconnections)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        parent_infos = parent_infos + ["transition", self.getlocalId()]
        search_result = []
        content = self.condition.getcontent()
        content_name = content.getLocalTag()
        if content_name == "reference":
            search_result.extend(_Search([("reference", content.getname())], criteria, parent_infos))
        elif content_name == "inline":
            search_result.extend(content.Search(criteria, parent_infos + ["inline"]))
        return search_result
    setattr(cls, "Search", Search)


cls = _initElementClass("transition", "sfcObjects")
if cls:
    _updateTransitionSfcObjectsClass(cls)


# ----------------------------------------------------------------------


_initElementClass("selectionDivergence", "sfcObjects", "single")
_initElementClass("selectionConvergence", "sfcObjects", "multiple")
_initElementClass("simultaneousDivergence", "sfcObjects", "single")
_initElementClass("simultaneousConvergence", "sfcObjects", "multiple")


def _updateJumpStepSfcObjectSingleClass(cls):
    def Search(self, criteria, parent_infos):
        return _Search([("target", self.gettargetName())], criteria, parent_infos + ["jump", self.getlocalId()])
    setattr(cls, "Search", Search)


cls = _initElementClass("jumpStep", "sfcObjects", "single")
if cls:
    _updateJumpStepSfcObjectSingleClass(cls)


# ----------------------------------------------------------------------


def _updateActionActionBlockClass(cls):
    def setreferenceName(self, name):
        if self.reference is not None:
            self.reference.setname(name)
    setattr(cls, "setreferenceName", setreferenceName)

    def getreferenceName(self):
        if self.reference is not None:
            return self.reference.getname()
        return None
    setattr(cls, "getreferenceName", getreferenceName)

    def setinlineContent(self, content):
        if self.inline is not None:
            self.inline.setcontent(PLCOpenParser.CreateElement("ST", "inline"))
            self.inline.settext(content)
    setattr(cls, "setinlineContent", setinlineContent)

    def getinlineContent(self):
        if self.inline is not None:
            return self.inline.gettext()
        return None
    setattr(cls, "getinlineContent", getinlineContent)

    def updateElementName(self, old_name, new_name):
        if self.reference is not None and TextMatched(self.reference.getname(), old_name):
            self.reference.setname(new_name)
        if self.inline is not None:
            self.inline.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        if self.reference is not None:
            self.reference.setname(update_address(self.reference.getname(), address_model, new_leading))
        if self.inline is not None:
            self.inline.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        qualifier = self.getqualifier()
        if qualifier is None:
            qualifier = "N"
        return _Search([("inline", self.getinlineContent()),
                        ("reference", self.getreferenceName()),
                        ("qualifier", qualifier),
                        ("duration", self.getduration()),
                        ("indicator", self.getindicator())],
                       criteria, parent_infos)
    setattr(cls, "Search", Search)


cls = PLCOpenParser.GetElementClass("action", "actionBlock")
if cls:
    _updateActionActionBlockClass(cls)


# ----------------------------------------------------------------------


def _updateActionBlockCommonObjectsSingleClass(cls):
    def setactions(self, actions):
        self.action = []
        for params in actions:
            action = PLCOpenParser.CreateElement("action", "actionBlock")
            self.appendaction(action)
            action.setqualifier(params.qualifier)
            if params.type == "reference":
                action.addreference()
                action.setreferenceName(params.value)
            else:
                action.addinline()
                action.setinlineContent(params.value)
            if params.duration != "":
                action.setduration(params.duration)
            if params.indicator != "":
                action.setindicator(params.indicator)
    setattr(cls, "setactions", setactions)

    def getactions(self):
        actions = []
        for action in self.action:
            params = {}
            params["qualifier"] = action.getqualifier()
            if params["qualifier"] is None:
                params["qualifier"] = "N"
            if action.getreference() is not None:
                params["type"] = "reference"
                params["value"] = action.getreferenceName()
            elif action.getinline() is not None:
                params["type"] = "inline"
                params["value"] = action.getinlineContent()
            duration = action.getduration()
            if duration:
                params["duration"] = duration
            indicator = action.getindicator()
            if indicator is not None:
                params["indicator"] = indicator
            actions.append(params)
        return actions
    setattr(cls, "getactions", getactions)

    def updateElementName(self, old_name, new_name):
        for action in self.action:
            action.updateElementName(old_name, new_name)
    setattr(cls, "updateElementName", updateElementName)

    def updateElementAddress(self, address_model, new_leading):
        for action in self.action:
            action.updateElementAddress(address_model, new_leading)
    setattr(cls, "updateElementAddress", updateElementAddress)

    def Search(self, criteria, parent_infos=None):
        parent_infos = [] if parent_infos is None else parent_infos
        parent_infos = parent_infos + ["action_block", self.getlocalId()]
        search_result = []
        for idx, action in enumerate(self.action):
            search_result.extend(action.Search(criteria, parent_infos + ["action", idx]))
        return search_result
    setattr(cls, "Search", Search)


cls = _initElementClass("actionBlock", "commonObjects", "single")
if cls:
    _updateActionBlockCommonObjectsSingleClass(cls)


# ----------------------------------------------------------------------


def _SearchInIOVariable(self, criteria, parent_infos=None):
    parent_infos = [] if parent_infos is None else parent_infos
    return _Search([("expression", self.expression)], criteria, parent_infos + ["io_variable", self.getlocalId()])


def _UpdateIOElementName(self, old_name, new_name):
    if TextMatched(self.expression, old_name):
        self.expression = new_name


def _UpdateIOElementAddress(self, address_model, new_leading):
    self.expression = update_address(self.expression, address_model, new_leading)


cls = _initElementClass("inVariable", "fbdObjects")
if cls:
    setattr(cls, "updateElementName", _UpdateIOElementName)
    setattr(cls, "updateElementAddress", _UpdateIOElementAddress)
    setattr(cls, "Search", _SearchInIOVariable)

cls = _initElementClass("outVariable", "fbdObjects", "single")
if cls:
    setattr(cls, "updateElementName", _UpdateIOElementName)
    setattr(cls, "updateElementAddress", _UpdateIOElementAddress)
    setattr(cls, "Search", _SearchInIOVariable)

cls = _initElementClass("inOutVariable", "fbdObjects", "single")
if cls:
    setattr(cls, "updateElementName", _UpdateIOElementName)
    setattr(cls, "updateElementAddress", _UpdateIOElementAddress)
    setattr(cls, "Search", _SearchInIOVariable)


def _SearchInConnector(self, criteria, parent_infos=None):
    parent_infos = [] if parent_infos is None else parent_infos
    return _Search([("name", self.getname())], criteria, parent_infos + ["connector", self.getlocalId()])


# ----------------------------------------------------------------------


def _updateContinuationCommonObjectsClass(cls):
    setattr(cls, "Search", _SearchInConnector)

    def updateElementName(self, old_name, new_name):
        if TextMatched(self.name, old_name):
            self.name = new_name
    setattr(cls, "updateElementName", updateElementName)


cls = _initElementClass("continuation", "commonObjects")
if cls:
    _updateContinuationCommonObjectsClass(cls)


# ----------------------------------------------------------------------


def _updateConnectorCommonObjectsSingleClass(cls):
    setattr(cls, "Search", _SearchInConnector)

    def updateElementName(self, old_name, new_name):
        if TextMatched(self.name, old_name):
            self.name = new_name
    setattr(cls, "updateElementName", updateElementName)


cls = _initElementClass("connector", "commonObjects", "single")
if cls:
    _updateConnectorCommonObjectsSingleClass(cls)


# ----------------------------------------------------------------------


def _updateConnectionClass(cls):
    def setpoints(self, points):
        positions = []
        for point in points:
            position = PLCOpenParser.CreateElement("position", "connection")
            position.setx(point.x)
            position.sety(point.y)
            positions.append(position)
        self.position = positions
    setattr(cls, "setpoints", setpoints)

    def getpoints(self):
        points = []
        for position in self.position:
            points.append((position.getx(), position.gety()))
        return points
    setattr(cls, "getpoints", getpoints)


cls = PLCOpenParser.GetElementClass("connection")
if cls:
    _updateConnectionClass(cls)


# ----------------------------------------------------------------------


def _updateConnectionPointInClass(cls):
    def setrelPositionXY(self, x, y):
        self.relPosition = PLCOpenParser.CreateElement("relPosition", "connectionPointIn")
        self.relPosition.setx(x)
        self.relPosition.sety(y)
    setattr(cls, "setrelPositionXY", setrelPositionXY)

    def getrelPositionXY(self):
        if self.relPosition is not None:
            return self.relPosition.getx(), self.relPosition.gety()
        return self.relPosition
    setattr(cls, "getrelPositionXY", getrelPositionXY)

    def addconnection(self):
        self.append(PLCOpenParser.CreateElement("connection", "connectionPointIn"))
    setattr(cls, "addconnection", addconnection)

    def removeconnection(self, idx):
        if len(self.content) > idx:
            self.remove(self.content[idx])
    setattr(cls, "removeconnection", removeconnection)

    def removeconnections(self):
        self.content = None
    setattr(cls, "removeconnections", removeconnections)

    connection_xpath = PLCOpen_XPath("ppx:connection")
    connection_by_position_xpath = PLCOpen_XPath("ppx:connection[position()=$pos]")

    def getconnections(self):
        return connection_xpath(self)
    setattr(cls, "getconnections", getconnections)

    def getconnection(self, idx):
        connection = connection_by_position_xpath(self, pos=idx+1)
        if len(connection) > 0:
            return connection[0]
        return None
    setattr(cls, "getconnection", getconnection)

    def setconnectionId(self, idx, local_id):
        connection = self.getconnection(idx)
        if connection is not None:
            connection.setrefLocalId(local_id)
    setattr(cls, "setconnectionId", setconnectionId)

    def getconnectionId(self, idx):
        connection = self.getconnection(idx)
        if connection is not None:
            return connection.getrefLocalId()
        return None
    setattr(cls, "getconnectionId", getconnectionId)

    def setconnectionPoints(self, idx, points):
        connection = self.getconnection(idx)
        if connection is not None:
            connection.setpoints(points)
    setattr(cls, "setconnectionPoints", setconnectionPoints)

    def getconnectionPoints(self, idx):
        connection = self.getconnection(idx)
        if connection is not None:
            return connection.getpoints()
        return []
    setattr(cls, "getconnectionPoints", getconnectionPoints)

    def setconnectionParameter(self, idx, parameter):
        connection = self.getconnection(idx)
        if connection is not None:
            connection.setformalParameter(parameter)
    setattr(cls, "setconnectionParameter", setconnectionParameter)

    def getconnectionParameter(self, idx):
        connection = self.getconnection(idx)
        if connection is not None:
            return connection.getformalParameter()
        return None
    setattr(cls, "getconnectionParameter", getconnectionParameter)


cls = PLCOpenParser.GetElementClass("connectionPointOut")
if cls:
    def setrelPositionXY(self, x, y):
        self.relPosition = PLCOpenParser.CreateElement("relPosition", "connectionPointOut")
        self.relPosition.setx(x)
        self.relPosition.sety(y)
    setattr(cls, "setrelPositionXY", setrelPositionXY)

    def getrelPositionXY(self):
        if self.relPosition is not None:
            return self.relPosition.getx(), self.relPosition.gety()
        return self.relPosition
    setattr(cls, "getrelPositionXY", getrelPositionXY)


cls = PLCOpenParser.GetElementClass("connectionPointIn")
if cls:
    _updateConnectionPointInClass(cls)


# ----------------------------------------------------------------------


def _updateValueClass(cls):
    def setvalue(self, value):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            content = PLCOpenParser.CreateElement("arrayValue", "value")
        elif value.startswith("(") and value.endswith(")"):
            content = PLCOpenParser.CreateElement("structValue", "value")
        else:
            content = PLCOpenParser.CreateElement("simpleValue", "value")
        content.setvalue(value)
        self.setcontent(content)
    setattr(cls, "setvalue", setvalue)

    def getvalue(self):
        return self.content.getvalue()
    setattr(cls, "getvalue", getvalue)


cls = PLCOpenParser.GetElementClass("value")
if cls:
    _updateValueClass(cls)


# ----------------------------------------------------------------------


def extractValues(values):
    items = values.split(",")
    i = 1
    while i < len(items):
        opened = items[i - 1].count("(") + items[i - 1].count("[")
        closed = items[i - 1].count(")") + items[i - 1].count("]")
        if opened > closed:
            items[i - 1] = ','.join([items[i - 1], items.pop(i)])
        elif opened == closed:
            i += 1
        else:
            raise ValueError(_("\"%s\" is an invalid value!") % values)
    return items


def _updateArrayValueValueClass(cls):
    def setvalue(self, value):
        elements = []
        for item in extractValues(value[1:-1]):
            item = item.strip()
            element = PLCOpenParser.CreateElement("value", "arrayValue")
            result = arrayValue_model.match(item)
            if result is not None:
                groups = result.groups()
                element.setrepetitionValue(groups[0])
                element.setvalue(groups[1].strip())
            else:
                element.setvalue(item)
            elements.append(element)
        self.value = elements
    setattr(cls, "setvalue", setvalue)

    def getvalue(self):
        values = []
        for element in self.value:
            try:
                repetition = int(element.getrepetitionValue())
            except Exception:
                repetition = 1
            if repetition > 1:
                value = element.getvalue()
                if value is None:
                    value = ""
                values.append("%s(%s)" % (repetition, value))
            else:
                values.append(element.getvalue())
        return "[%s]" % ", ".join(values)
    setattr(cls, "getvalue", getvalue)


cls = PLCOpenParser.GetElementClass("arrayValue", "value")
if cls:
    arrayValue_model = re.compile(r"([0-9]+)\((.*)\)$")
    _updateArrayValueValueClass(cls)

# ----------------------------------------------------------------------


def _updateStructValueValueClass(cls):
    def setvalue(self, value):
        elements = []
        for item in extractValues(value[1:-1]):
            result = structValue_model.match(item)
            if result is not None:
                groups = result.groups()
                element = PLCOpenParser.CreateElement("value", "structValue")
                element.setmember(groups[0].strip())
                element.setvalue(groups[1].strip())
                elements.append(element)
        self.value = elements
    setattr(cls, "setvalue", setvalue)

    def getvalue(self):
        values = []
        for element in self.value:
            values.append("%s := %s" % (element.getmember(), element.getvalue()))
        return "(%s)" % ", ".join(values)
    setattr(cls, "getvalue", getvalue)


cls = PLCOpenParser.GetElementClass("structValue", "value")
if cls:
    structValue_model = re.compile("(.*):=(.*)")
    _updateStructValueValueClass(cls)
