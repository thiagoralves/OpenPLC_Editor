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
import os
import re
import traceback
from builtins import str as text
from copy import deepcopy

from lxml import etree
from xmlclass import GenerateParserFromXSDstring

from PLCControler import UndoBuffer
from ConfigTreeNode import XSDSchemaErrorMessage

from plcopen.plcopen import TestTextElement
from editors.CodeFileEditor import GetSectionsText

CODEFILE_XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <xsd:element name="%(codefile_name)s">
    <xsd:complexType>
      <xsd:sequence>
        %(includes_section)s
        <xsd:element name="variables">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="variable" minOccurs="0" maxOccurs="unbounded">
                <xsd:complexType>
                  <xsd:attribute name="name" type="xsd:string" use="required"/>
                  <xsd:attribute name="type" type="xsd:string" use="required"/>
                  <xsd:attribute name="class" use="optional">
                    <xsd:simpleType>
                      <xsd:restriction base="xsd:string">
                        <xsd:enumeration value="input"/>
                        <xsd:enumeration value="memory"/>
                        <xsd:enumeration value="output"/>
                      </xsd:restriction>
                    </xsd:simpleType>
                  </xsd:attribute>
                  <xsd:attribute name="initial" type="xsd:string" use="optional" default=""/>
                  <xsd:attribute name="desc" type="xsd:string" use="optional" default=""/>
                  <xsd:attribute name="onchange" type="xsd:string" use="optional" default=""/>
                  <xsd:attribute name="opts" type="xsd:string" use="optional" default=""/>
                </xsd:complexType>
              </xsd:element>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
        %(sections)s
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
  <xsd:complexType name="CodeText">
    <xsd:annotation>
      <xsd:documentation>Formatted text according to parts of XHTML 1.1</xsd:documentation>
    </xsd:annotation>
    <xsd:sequence>
      <xsd:any namespace="http://www.w3.org/1999/xhtml" processContents="lax"/>
    </xsd:sequence>
  </xsd:complexType>
</xsd:schema>"""

SECTION_TAG_ELEMENT = "<xsd:element name=\"%s\" type=\"CodeText\"/>"


class CodeFile(object):

    CODEFILE_NAME = "CodeFile"
    SECTIONS_NAMES = []

    def __init__(self):
        sections_str = {"codefile_name": self.CODEFILE_NAME}
        if "includes" in self.SECTIONS_NAMES:
            sections_str["includes_section"] = SECTION_TAG_ELEMENT % "includes"
        else:
            sections_str["includes_section"] = ""
        sections_str["sections"] = "\n".join(
            [SECTION_TAG_ELEMENT % name
             for name in self.SECTIONS_NAMES if name != "includes"])

        self.CodeFileParser = GenerateParserFromXSDstring(
            CODEFILE_XSD % sections_str)
        self.CodeFileVariables = etree.XPath("variables/variable")

        filepath = self.CodeFileName()
        if os.path.isfile(filepath):
            xmlfile = open(filepath, 'r')
            codefile_xml = xmlfile.read()
            xmlfile.close()

            codefile_xml = codefile_xml.replace(
                '<%s>' % self.CODEFILE_NAME,
                '<%s xmlns:xhtml="http://www.w3.org/1999/xhtml">' % self.CODEFILE_NAME)
            for cre, repl in [
                    (re.compile(r"(?<!<xhtml:p>)(?:<!\[CDATA\[)"), "<xhtml:p><![CDATA["),
                    (re.compile(r"(?:]]>)(?!</xhtml:p>)"), "]]></xhtml:p>")]:
                codefile_xml = cre.sub(repl, codefile_xml)

            try:
                self.CodeFile, error = self.CodeFileParser.LoadXMLString(codefile_xml)
                if error is not None:
                    (fname, lnum, src) = ((self.CODEFILE_NAME,) + error)
                    self.GetCTRoot().logger.write_warning(XSDSchemaErrorMessage.format(a1=fname, a2=lnum, a3=src))
                self.CreateCodeFileBuffer(True)
            except Exception as exc:
                msg = _("Couldn't load confnode parameters {a1} :\n {a2}").format(a1=self.CTNName(), a2=text(exc))
                self.GetCTRoot().logger.write_error(msg)
                self.GetCTRoot().logger.write_error(traceback.format_exc())
                raise Exception
        else:
            self.CodeFile = self.CodeFileParser.CreateRoot()
            self.CreateCodeFileBuffer(False)
            self.OnCTNSave()

    def GetBaseTypes(self):
        return self.GetCTRoot().GetBaseTypes()

    def GetDataTypes(self, basetypes=False):
        return self.GetCTRoot().GetDataTypes(basetypes=basetypes)

    def GenerateNewName(self, name, format):
        return self.GetCTRoot().GenerateNewName(
            None, name, format,
            exclude=dict([(var.getname().upper(), True)
                          for var in self.CodeFile.variables.getvariable()]))

    def SetVariables(self, variables):
        self.CodeFile.variables.setvariable([])
        for var in variables:
            variable = self.CodeFileParser.CreateElement("variable", "variables")
            variable.setname(var["Name"])
            variable.settype(var["Type"])
            variable.setinitial(var["Initial"])
            variable.setdesc(var["Description"])
            variable.setonchange(var["OnChange"])
            variable.setopts(var["Options"])
            self.CodeFile.variables.appendvariable(variable)

    def GetVariables(self):
        datas = []
        for var in self.CodeFileVariables(self.CodeFile):
            datas.append({
                "Name":        var.getname(),
                "Type":        var.gettype(),
                "Initial":     var.getinitial(),
                "Description": var.getdesc(),
                "OnChange":    var.getonchange(),
                "Options":     var.getopts(),
            })
        return datas

    def SetTextParts(self, parts):
        for section in self.SECTIONS_NAMES:
            section_code = parts.get(section)
            if section_code is not None:
                getattr(self.CodeFile, section).setanyText(section_code)

    def GetTextParts(self):
        return dict([(section, getattr(self.CodeFile, section).getanyText())
                     for section in self.SECTIONS_NAMES])

    def CTNTestModified(self):
        return self.ChangesToSave or not self.CodeFileIsSaved()

    def OnCTNSave(self, from_project_path=None):
        filepath = self.CodeFileName()

        xmlfile = open(filepath, "w")
        xmlfile.write(etree.tostring(
            self.CodeFile,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'))
        xmlfile.close()

        self.MarkCodeFileAsSaved()
        return True

    def CTNGlobalInstances(self):
        variables = self.CodeFileVariables(self.CodeFile)
        ret = [(variable.getname(),
                variable.gettype(),
                variable.getinitial())
               for variable in variables]
        return ret

    def CTNSearch(self, criteria):
        variables = self.GetVariables()
        results = []
        tagname = self.CTNFullName()
        for index, var in enumerate(variables):
            varname = var["Name"]
            results.extend([((tagname, "var_inout", index, "name"),) + result
                            for result in TestTextElement(varname, criteria)])
        results.extend([((tagname, "body"),) + result
                        for result in TestTextElement(
                            GetSectionsText(self, lambda x:""), criteria)])
        return results

# -------------------------------------------------------------------------------
#                      Current Buffering Management Functions
# -------------------------------------------------------------------------------

    def Copy(self, model):
        """
        Return a copy of the codefile model
        """
        return deepcopy(model)

    def CreateCodeFileBuffer(self, saved):
        self.Buffering = False
        self.CodeFileBuffer = UndoBuffer(self.CodeFileParser.Dumps(self.CodeFile), saved)

    def BufferCodeFile(self):
        self.CodeFileBuffer.Buffering(self.CodeFileParser.Dumps(self.CodeFile))

    def StartBuffering(self):
        self.Buffering = True

    def EndBuffering(self):
        if self.Buffering:
            self.CodeFileBuffer.Buffering(self.CodeFileParser.Dumps(self.CodeFile))
            self.Buffering = False

    def MarkCodeFileAsSaved(self):
        self.EndBuffering()
        self.CodeFileBuffer.CurrentSaved()

    def CodeFileIsSaved(self):
        return self.CodeFileBuffer.IsCurrentSaved() and not self.Buffering

    def LoadPrevious(self):
        self.EndBuffering()
        self.CodeFile = self.CodeFileParser.Loads(self.CodeFileBuffer.Previous())

    def LoadNext(self):
        self.CodeFile = self.CodeFileParser.Loads(self.CodeFileBuffer.Next())

    def GetBufferState(self):
        first = self.CodeFileBuffer.IsFirst() and not self.Buffering
        last = self.CodeFileBuffer.IsLast()
        return not first, not last
