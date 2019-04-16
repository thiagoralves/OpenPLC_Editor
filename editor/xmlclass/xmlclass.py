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
from __future__ import print_function
import os
import re
import datetime
from functools import reduce
from xml.dom import minidom
from xml.sax.saxutils import unescape
from collections import OrderedDict
from builtins import str as text

from six import string_types
from six.moves import xrange
from lxml import etree


def CreateNode(name):
    node = minidom.Node()
    node.nodeName = name
    node._attrs = {}
    node.childNodes = []
    return node


def NodeRenameAttr(node, old_name, new_name):
    node._attrs[new_name] = node._attrs.pop(old_name)


def NodeSetAttr(node, name, value):
    attr = minidom.Attr(name)
    txt = minidom.Text()
    txt.data = value
    attr.childNodes[0] = txt
    node._attrs[name] = attr


# Regular expression models for checking all kind of
# string values defined in XML standard

Name_model = re.compile(r'([a-zA-Z_\:][\w\.\-\:]*)$')
Names_model = re.compile(r'([a-zA-Z_\:][\w\.\-\:]*(?: [a-zA-Z_\:][\w\.\-\:]*)*)$')
NMToken_model = re.compile(r'([\w\.\-\:]*)$')
NMTokens_model = re.compile(r'([\w\.\-\:]*(?: [\w\.\-\:]*)*)$')
QName_model = re.compile(r'((?:[a-zA-Z_][\w]*:)?[a-zA-Z_][\w]*)$')
QNames_model = re.compile(r'((?:[a-zA-Z_][\w]*:)?[a-zA-Z_][\w]*(?: (?:[a-zA-Z_][\w]*:)?[a-zA-Z_][\w]*)*)$')
NCName_model = re.compile(r'([a-zA-Z_][\w]*)$')
URI_model = re.compile(r'((?:htt(p|ps)://|/)?(?:[\w.-]*/?)*)$')
LANGUAGE_model = re.compile(r'([a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})*)$')

ONLY_ANNOTATION = re.compile(r"((?:annotation )?)")

"""
Regular expression models for extracting dates and times from a string
"""
time_model = re.compile(r'([0-9]{2}):([0-9]{2}):([0-9]{2}(?:\.[0-9]*)?)(?:Z)?$')
date_model = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})((?:[\-\+][0-9]{2}:[0-9]{2})|Z)?$')
datetime_model = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})[ T]([0-9]{2}):([0-9]{2}):([0-9]{2}(?:\.[0-9]*)?)((?:[\-\+][0-9]{2}:[0-9]{2})|Z)?$')


class xml_timezone(datetime.tzinfo):

    def SetOffset(self, offset):
        if offset == "Z":
            self.__offset = datetime.timedelta(minutes=0)
            self.__name = "UTC"
        else:
            sign = {"-": -1, "+": 1}[offset[0]]
            hours, minutes = [int(val) for val in offset[1:].split(":")]
            self.__offset = datetime.timedelta(minutes=sign * (hours * 60 + minutes))
            self.__name = ""

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)


[
    SYNTAXELEMENT, SYNTAXATTRIBUTE, SIMPLETYPE, COMPLEXTYPE, COMPILEDCOMPLEXTYPE,
    ATTRIBUTESGROUP, ELEMENTSGROUP, ATTRIBUTE, ELEMENT, CHOICE, ANY, TAG, CONSTRAINT,
] = range(13)


def NotSupportedYet(type):
    """
    Function that generates a function that point out to user that datatype
    used is not supported by xmlclass yet
    @param type: data type
    @return: function generated
    """
    def GetUnknownValue(attr):
        raise ValueError("\"%s\" type isn't supported by \"xmlclass\" yet!" % type)
    return GetUnknownValue


def getIndent(indent, balise):
    """
    This function calculates the number of whitespace for indentation
    """
    first = indent * 2
    second = first + len(balise) + 1
    return u'\t'.expandtabs(first), u'\t'.expandtabs(second)


def GetAttributeValue(attr, extract=True):
    """
    Function that extracts data from a tree node
    @param attr: tree node containing data to extract
    @param extract: attr is a tree node or not
    @return: data extracted as string
    """
    if not extract:
        return attr
    if len(attr.childNodes) == 1:
        return text(unescape(attr.childNodes[0].data))
    else:
        # content is a CDATA
        txt = u''
        for node in attr.childNodes:
            if not (node.nodeName == "#text" and node.data.strip() == u''):
                txt += text(unescape(node.data))
        return text


def GetNormalizedString(attr, extract=True):
    """
    Function that normalizes a string according to XML 1.0. Replace
    tabulations, line feed and carriage return by white space
    @param attr: tree node containing data to extract or data to normalize
    @param extract: attr is a tree node or not
    @return: data normalized as string
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    return value.replace("\t", " ").replace("\r", " ").replace("\n", " ")


def GetToken(attr, extract=True):
    """
    Function that tokenizes a string according to XML 1.0. Remove any leading
    and trailing white space and replace internal sequence of two or more
    spaces by only one white space
    @param attr: tree node containing data to extract or data to tokenize
    @param extract: attr is a tree node or not
    @return: data tokenized as string
    """
    return " ".join([part for part in
                     GetNormalizedString(attr, extract).split(" ")
                     if part])


def GetHexInteger(attr, extract=True):
    """
    Function that extracts an hexadecimal integer from a tree node or a string
    @param attr: tree node containing data to extract or data as a string
    @param extract: attr is a tree node or not
    @return: data as an integer
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    if len(value) % 2 != 0:
        raise ValueError("\"%s\" isn't a valid hexadecimal integer!" % value)
    try:
        return int(value, 16)
    except Exception:
        raise ValueError("\"%s\" isn't a valid hexadecimal integer!" % value)


def GenerateIntegerExtraction(minInclusive=None, maxInclusive=None,
                              minExclusive=None, maxExclusive=None):
    """
    Function that generates an extraction function for integer defining min and
    max of integer value
    @param minInclusive: inclusive minimum
    @param maxInclusive: inclusive maximum
    @param minExclusive: exclusive minimum
    @param maxExclusive: exclusive maximum
    @return: function generated
    """
    def GetInteger(attr, extract=True):
        """
        Function that extracts an integer from a tree node or a string
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: data as an integer
        """

        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        try:
            # TODO: permit to write value like 1E2
            value = int(value)
        except Exception:
            raise ValueError("\"%s\" isn't a valid integer!" % value)
        if minInclusive is not None and value < minInclusive:
            raise ValueError("\"%d\" isn't greater or equal to %d!" %
                             (value, minInclusive))
        if maxInclusive is not None and value > maxInclusive:
            raise ValueError("\"%d\" isn't lesser or equal to %d!" %
                             (value, maxInclusive))
        if minExclusive is not None and value <= minExclusive:
            raise ValueError("\"%d\" isn't greater than %d!" %
                             (value, minExclusive))
        if maxExclusive is not None and value >= maxExclusive:
            raise ValueError("\"%d\" isn't lesser than %d!" %
                             (value, maxExclusive))
        return value
    return GetInteger


def GenerateFloatExtraction(type, extra_values=None):
    """
    Function that generates an extraction function for float
    @param type: name of the type of float
    @return: function generated
    """
    extra_values = [] if extra_values is None else extra_values

    def GetFloat(attr, extract=True):
        """
        Function that extracts a float from a tree node or a string
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: data as a float
        """
        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        if value in extra_values:
            return value
        try:
            return float(value)
        except Exception:
            raise ValueError("\"%s\" isn't a valid %s!" % (value, type))
    return GetFloat


def GetBoolean(attr, extract=True):
    """
    Function that extracts a boolean from a tree node or a string
    @param attr: tree node containing data to extract or data as a string
    @param extract: attr is a tree node or not
    @return: data as a boolean
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    if value == "true" or value == "1":
        return True
    elif value == "false" or value == "0":
        return False
    else:
        raise ValueError("\"%s\" isn't a valid boolean!" % value)


def GetTime(attr, extract=True):
    """
    Function that extracts a time from a tree node or a string
    @param attr: tree node containing data to extract or data as a string
    @param extract: attr is a tree node or not
    @return: data as a time
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    result = time_model.match(value)
    if result:
        values = result.groups()
        time_values = [int(v) for v in values[:2]]
        seconds = float(values[2])
        time_values.extend([int(seconds), int((seconds % 1) * 1000000)])
        return datetime.time(*time_values)
    else:
        raise ValueError("\"%s\" isn't a valid time!" % value)


def GetDate(attr, extract=True):
    """
    Function that extracts a date from a tree node or a string
    @param attr: tree node containing data to extract or data as a string
    @param extract: attr is a tree node or not
    @return: data as a date
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    result = date_model.match(value)
    if result:
        values = result.groups()
        date_values = [int(v) for v in values[:3]]
        if values[3] is not None:
            tz = xml_timezone()
            tz.SetOffset(values[3])
            date_values.append(tz)
        return datetime.date(*date_values)
    else:
        raise ValueError("\"%s\" isn't a valid date!" % value)


def GetDateTime(attr, extract=True):
    """
    Function that extracts date and time from a tree node or a string
    @param attr: tree node containing data to extract or data as a string
    @param extract: attr is a tree node or not
    @return: data as date and time
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    result = datetime_model.match(value)
    if result:
        values = result.groups()
        datetime_values = [int(v) for v in values[:5]]
        seconds = float(values[5])
        datetime_values.extend([int(seconds), int((seconds % 1) * 1000000)])
        if values[6] is not None:
            tz = xml_timezone()
            tz.SetOffset(values[6])
            datetime_values.append(tz)
        return datetime.datetime(*datetime_values)
    else:
        raise ValueError("\"%s\" isn't a valid datetime!" % value)


def GenerateModelNameExtraction(type, model):
    """
    Function that generates an extraction function for string matching a model
    @param type: name of the data type
    @param model: model that data must match
    @return: function generated
    """
    def GetModelName(attr, extract=True):
        """
        Function that extracts a string from a tree node or not and check that
        string extracted or given match the model
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: data as a string if matching
        """
        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        result = model.match(value)
        if not result:
            raise ValueError("\"%s\" isn't a valid %s!" % (value, type))
        return value
    return GetModelName


def GenerateLimitExtraction(min=None, max=None, unbounded=True):
    """
    Function that generates an extraction function for integer defining min and
    max of integer value
    @param min: minimum limit value
    @param max: maximum limit value
    @param unbounded: value can be "unbounded" or not
    @return: function generated
    """
    def GetLimit(attr, extract=True):
        """
        Function that extracts a string from a tree node or not and check that
        string extracted or given is in a list of values
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: data as a string
        """
        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        if value == "unbounded":
            if unbounded:
                return value
            else:
                raise ValueError("Member limit can't be defined to \"unbounded\"!")
        try:
            limit = int(value)
        except Exception:
            raise ValueError("\"%s\" isn't a valid value for this member limit!" % value)
        if limit < 0:
            raise ValueError("Member limit can't be negative!")
        elif min is not None and limit < min:
            raise ValueError("Member limit can't be lower than \"%d\"!" % min)
        elif max is not None and limit > max:
            raise ValueError("Member limit can't be upper than \"%d\"!" % max)
        return limit
    return GetLimit


def GenerateEnumeratedExtraction(type, list):
    """
    Function that generates an extraction function for enumerated values
    @param type: name of the data type
    @param list: list of possible values
    @return: function generated
    """
    def GetEnumerated(attr, extract=True):
        """
        Function that extracts a string from a tree node or not and check that
        string extracted or given is in a list of values
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: data as a string
        """
        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        if value in list:
            return value
        else:
            raise ValueError(
                "\"%s\" isn't a valid value for %s!" % (value, type))
    return GetEnumerated


def GetNamespaces(attr, extract=True):
    """
    Function that extracts a list of namespaces from a tree node or a string
    @param attr: tree node containing data to extract or data as a string
    @param extract: attr is a tree node or not
    @return: list of namespaces
    """
    if extract:
        value = GetAttributeValue(attr)
    else:
        value = attr
    if value == "":
        return []
    elif value == "##any" or value == "##other":
        namespaces = [value]
    else:
        namespaces = []
        for item in value.split(" "):
            if item == "##targetNamespace" or item == "##local":
                namespaces.append(item)
            else:
                result = URI_model.match(item)
                if result is not None:
                    namespaces.append(item)
                else:
                    raise ValueError("\"%s\" isn't a valid value for namespace!" % value)
    return namespaces


def GenerateGetList(type, list):
    """
    Function that generates an extraction function for a list of values
    @param type: name of the data type
    @param list: list of possible values
    @return: function generated
    """
    def GetLists(attr, extract=True):
        """
        Function that extracts a list of values from a tree node or a string
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: list of values
        """
        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        if value == "":
            return []
        elif value == "#all":
            return [value]
        else:
            values = []
            for item in value.split(" "):
                if item in list:
                    values.append(item)
                else:
                    raise ValueError(
                        "\"%s\" isn't a valid value for %s!" % (value, type))
            return values
    return GetLists


def GenerateModelNameListExtraction(type, model):
    """
    Function that generates an extraction function for list of string matching
    a model
    @param type: name of the data type
    @param model: model that list elements must match
    @return: function generated
    """
    def GetModelNameList(attr, extract=True):
        """
        Function that extracts a list of string from a tree node or not and
        check that all extracted items match the model
        @param attr: tree node containing data to extract or data as a string
        @param extract: attr is a tree node or not
        @return: data as a list of string if matching
        """
        if extract:
            value = GetAttributeValue(attr)
        else:
            value = attr
        values = []
        for item in value.split(" "):
            result = model.match(item)
            if result is not None:
                values.append(item)
            else:
                raise ValueError("\"%s\" isn't a valid value for %s!" % (value, type))
        return values
    return GetModelNameList


def GenerateAnyInfos(infos):

    def GetTextElement(tree):
        if infos["namespace"][0] == "##any":
            return tree.xpath("p")[0]
        return tree.xpath("ns:p", namespaces={"ns": infos["namespace"][0]})[0]

    def ExtractAny(tree):
        return GetTextElement(tree).text

    def GenerateAny(tree, value):
        GetTextElement(tree).text = etree.CDATA(value)

    def InitialAny():
        if infos["namespace"][0] == "##any":
            element_name = "p"
        else:
            element_name = "{%s}p" % infos["namespace"][0]
        p = etree.Element(element_name)
        p.text = etree.CDATA("")
        return p

    return {
        "type": COMPLEXTYPE,
        "extract": ExtractAny,
        "generate": GenerateAny,
        "initial": InitialAny,
        "check": lambda x: isinstance(x, (string_types, etree.ElementBase))
    }


def GenerateTagInfos(infos):
    def ExtractTag(tree):
        if len(tree._attrs) > 0:
            raise ValueError("\"%s\" musn't have attributes!" % infos["name"])
        if len(tree.childNodes) > 0:
            raise ValueError("\"%s\" musn't have children!" % infos["name"])
        if infos["minOccurs"] == 0:
            return True
        else:
            return None

    def GenerateTag(value, name=None, indent=0):
        if name is not None and not (infos["minOccurs"] == 0 and value is None):
            ind1, _ind2 = getIndent(indent, name)
            return ind1 + "<%s/>\n" % name
        else:
            return ""

    return {
        "type": TAG,
        "extract": ExtractTag,
        "generate": GenerateTag,
        "initial": lambda: None,
        "check": lambda x: x is None or infos["minOccurs"] == 0 and x
    }


def FindTypeInfos(factory, infos):
    if isinstance(infos, string_types):
        namespace, name = DecomposeQualifiedName(infos)
        return factory.GetQualifiedNameInfos(name, namespace)
    return infos


def GetElementInitialValue(factory, infos):
    infos["elmt_type"] = FindTypeInfos(factory, infos["elmt_type"])
    if infos["minOccurs"] == 1:
        element_name = factory.etreeNamespaceFormat % infos["name"]
        if infos["elmt_type"]["type"] == SIMPLETYPE:
            def initial_value():
                value = factory.Parser.makeelement(element_name)
                value.text = (infos["elmt_type"]["generate"](infos["elmt_type"]["initial"]()))
                value._init_()
                return value
        else:
            def initial_value():
                value = infos["elmt_type"]["initial"]()
                if infos["type"] != ANY:
                    DefaultElementClass.__setattr__(value, "tag", element_name)
                return value
        return [initial_value() for dummy in xrange(infos["minOccurs"])]
    else:
        return []


def GetContentInfos(name, choices):
    for choice_infos in choices:
        if choice_infos["type"] == "sequence":
            for element_infos in choice_infos["elements"]:
                if element_infos["type"] == CHOICE:
                    if GetContentInfos(name, element_infos["choices"]):
                        return choice_infos
                elif element_infos["name"] == name:
                    return choice_infos
        elif choice_infos["name"] == name:
            return choice_infos
    return None


def ComputeContentChoices(factory, name, infos):
    choices = []
    for choice in infos["choices"]:
        if choice["type"] == "sequence":
            choice["name"] = "sequence"
            for sequence_element in choice["elements"]:
                if sequence_element["type"] != CHOICE:
                    element_infos = factory.ExtractTypeInfos(sequence_element["name"], name, sequence_element["elmt_type"])
                    if element_infos is not None:
                        sequence_element["elmt_type"] = element_infos
        elif choice["elmt_type"] == "tag":
            choice["elmt_type"] = GenerateTagInfos(choice)
            factory.AddToLookupClass(choice["name"], name, DefaultElementClass)
        else:
            choice_infos = factory.ExtractTypeInfos(choice["name"], name, choice["elmt_type"])
            if choice_infos is not None:
                choice["elmt_type"] = choice_infos
        choices.append((choice["name"], choice))
    return choices


def GenerateContentInfos(factory, name, choices):
    choices_dict = {}
    for choice_name, infos in choices:
        if choice_name == "sequence":
            for element in infos["elements"]:
                if element["type"] == CHOICE:
                    element["elmt_type"] = GenerateContentInfos(factory, name, ComputeContentChoices(factory, name, element))
                elif element["name"] in choices_dict:
                    raise ValueError("'%s' element defined two times in choice" % choice_name)
                else:
                    choices_dict[element["name"]] = infos
        else:
            if choice_name in choices_dict:
                raise ValueError("'%s' element defined two times in choice" % choice_name)
            choices_dict[choice_name] = infos
    prefix = ("%s:" % factory.TargetNamespace
              if factory.TargetNamespace is not None else "")
    choices_xpath = "|".join(map(lambda x: prefix + x, choices_dict.keys()))

    def GetContentInitial():
        content_name, infos = choices[0]
        if content_name == "sequence":
            content_value = []
            for dummy in xrange(infos["minOccurs"]):
                for element_infos in infos["elements"]:
                    content_value.extend(GetElementInitialValue(factory, element_infos))
        else:
            content_value = GetElementInitialValue(factory, infos)
        return content_value

    return {
        "type": COMPLEXTYPE,
        "choices_xpath": etree.XPath(choices_xpath, namespaces=factory.NSMAP),
        "initial": GetContentInitial,
    }

# -------------------------------------------------------------------------------
#                           Structure extraction functions
# -------------------------------------------------------------------------------


def DecomposeQualifiedName(name):
    result = QName_model.match(name)
    if not result:
        raise ValueError("\"%s\" isn't a valid QName value!" % name)
    parts = result.groups()[0].split(':')
    if len(parts) == 1:
        return None, parts[0]
    return parts


def GenerateElement(element_name, attributes, elements_model,
                    accept_text=False):
    def ExtractElement(factory, node):
        attrs = factory.ExtractNodeAttrs(element_name, node, attributes)
        children_structure = ""
        children = []
        for child in node.childNodes:
            if child.nodeName not in ["#comment", "#text"]:
                namespace, childname = DecomposeQualifiedName(child.nodeName)
                children_structure += "%s " % childname
        result = elements_model.match(children_structure)
        if not result:
            raise ValueError("Invalid structure for \"%s\" children!. First element invalid." % node.nodeName)
        valid = result.groups()[0]
        if len(valid) < len(children_structure):
            raise ValueError("Invalid structure for \"%s\" children!. Element number %d invalid." % (node.nodeName, len(valid.split(" ")) - 1))
        for child in node.childNodes:
            if child.nodeName != "#comment" and \
               (accept_text or child.nodeName != "#text"):
                if child.nodeName == "#text":
                    children.append(GetAttributeValue(node))
                else:
                    namespace, childname = DecomposeQualifiedName(child.nodeName)
                    infos = factory.GetQualifiedNameInfos(childname, namespace)
                    if infos["type"] != SYNTAXELEMENT:
                        raise ValueError("\"%s\" can't be a member child!" % childname)
                    if element_name in infos["extract"]:
                        children.append(infos["extract"][element_name](factory, child))
                    else:
                        children.append(infos["extract"]["default"](factory, child))
        return node.nodeName, attrs, children
    return ExtractElement


class ClassFactory(object):
    """
    Class that generate class from an XML Tree
    """

    def __init__(self, document, filepath=None, debug=False):
        self.Document = document
        if filepath is not None:
            self.BaseFolder, self.FileName = os.path.split(filepath)
        else:
            self.BaseFolder = self.FileName = None
        self.Debug = debug

        # Dictionary for stocking Classes and Types definitions created from
        # the XML tree
        self.XMLClassDefinitions = {}

        self.DefinedNamespaces = {}
        self.NSMAP = {}
        self.Namespaces = {}
        self.SchemaNamespace = None
        self.TargetNamespace = None
        self.etreeNamespaceFormat = "%s"
        self.Parser = None

        self.CurrentCompilations = []

        # Dictionaries for stocking Classes and Types generated
        self.ComputeAfter = []
        if self.FileName is not None:
            self.ComputedClasses = {self.FileName: {}}
        else:
            self.ComputedClasses = {}
        self.ComputedClassesInfos = {}
        self.ComputedClassesLookUp = {}
        self.EquivalentClassesParent = {}
        self.AlreadyComputed = {}

    def GetQualifiedNameInfos(self, name, namespace=None, canbenone=False):
        if namespace is None:
            if name in self.Namespaces[self.SchemaNamespace]:
                return self.Namespaces[self.SchemaNamespace][name]
            for space, elements in self.Namespaces.iteritems():
                if space != self.SchemaNamespace and name in elements:
                    return elements[name]
            parts = name.split("_", 1)
            if len(parts) > 1:
                group = self.GetQualifiedNameInfos(parts[0], namespace)
                if group is not None and group["type"] == ELEMENTSGROUP:
                    elements = []
                    if "elements" in group:
                        elements = group["elements"]
                    elif "choices" in group:
                        elements = group["choices"]
                    for element in elements:
                        if element["name"] == parts[1]:
                            return element
            if not canbenone:
                raise ValueError("Unknown element \"%s\" for any defined namespaces!" % name)
        elif namespace in self.Namespaces:
            if name in self.Namespaces[namespace]:
                return self.Namespaces[namespace][name]
            parts = name.split("_", 1)
            if len(parts) > 1:
                group = self.GetQualifiedNameInfos(parts[0], namespace)
                if group is not None and group["type"] == ELEMENTSGROUP:
                    elements = []
                    if "elements" in group:
                        elements = group["elements"]
                    elif "choices" in group:
                        elements = group["choices"]
                    for element in elements:
                        if element["name"] == parts[1]:
                            return element
            if not canbenone:
                raise ValueError("Unknown element \"%s\" for namespace \"%s\"!" % (name, namespace))
        elif not canbenone:
            raise ValueError("Unknown namespace \"%s\"!" % namespace)
        return None

    def SplitQualifiedName(self, name, namespace=None, canbenone=False):
        if namespace is None:
            if name in self.Namespaces[self.SchemaNamespace]:
                return name, None
            for space, elements in self.Namespaces.items():
                if space != self.SchemaNamespace and name in elements:
                    return name, None
            parts = name.split("_", 1)
            if len(parts) > 1:
                group = self.GetQualifiedNameInfos(parts[0], namespace)
                if group is not None and group["type"] == ELEMENTSGROUP:
                    elements = []
                    if "elements" in group:
                        elements = group["elements"]
                    elif "choices" in group:
                        elements = group["choices"]
                    for element in elements:
                        if element["name"] == parts[1]:
                            return parts[1], parts[0]
            if not canbenone:
                raise ValueError("Unknown element \"%s\" for any defined namespaces!" % name)
        elif namespace in self.Namespaces:
            if name in self.Namespaces[namespace]:
                return name, None
            parts = name.split("_", 1)
            if len(parts) > 1:
                group = self.GetQualifiedNameInfos(parts[0], namespace)
                if group is not None and group["type"] == ELEMENTSGROUP:
                    elements = []
                    if "elements" in group:
                        elements = group["elements"]
                    elif "choices" in group:
                        elements = group["choices"]
                    for element in elements:
                        if element["name"] == parts[1]:
                            return parts[1], parts[0]
            if not canbenone:
                raise ValueError("Unknown element \"%s\" for namespace \"%s\"!" % (name, namespace))
        elif not canbenone:
            raise ValueError("Unknown namespace \"%s\"!" % namespace)
        return None, None

    def ExtractNodeAttrs(self, element_name, node, valid_attrs):
        attrs = {}
        for qualified_name, attr in node._attrs.items():
            namespace, name = DecomposeQualifiedName(qualified_name)
            if name in valid_attrs:
                infos = self.GetQualifiedNameInfos(name, namespace)
                if infos["type"] != SYNTAXATTRIBUTE:
                    raise ValueError("\"%s\" can't be a member attribute!" % name)
                elif name in attrs:
                    raise ValueError("\"%s\" attribute has been twice!" % name)
                elif element_name in infos["extract"]:
                    attrs[name] = infos["extract"][element_name](attr)
                else:
                    attrs[name] = infos["extract"]["default"](attr)
            elif namespace == "xmlns":
                infos = self.GetQualifiedNameInfos("anyURI", self.SchemaNamespace)
                value = infos["extract"](attr)
                self.DefinedNamespaces[value] = name
                self.NSMAP[name] = value
            else:
                raise ValueError("Invalid attribute \"%s\" for member \"%s\"!" % (qualified_name, node.nodeName))
        for attr in valid_attrs:
            if attr not in attrs and \
               attr in self.Namespaces[self.SchemaNamespace] and \
               "default" in self.Namespaces[self.SchemaNamespace][attr]:
                if element_name in self.Namespaces[self.SchemaNamespace][attr]["default"]:
                    default = self.Namespaces[self.SchemaNamespace][attr]["default"][element_name]
                else:
                    default = self.Namespaces[self.SchemaNamespace][attr]["default"]["default"]
                if default is not None:
                    attrs[attr] = default
        return attrs

    def ReduceElements(self, elements, schema=False):
        result = []
        for child_infos in elements:
            if child_infos is not None:
                if "name" in child_infos[1] and schema:
                    self.CurrentCompilations.append(child_infos[1]["name"])
                namespace, name = DecomposeQualifiedName(child_infos[0])
                infos = self.GetQualifiedNameInfos(name, namespace)
                if infos["type"] != SYNTAXELEMENT:
                    raise ValueError("\"%s\" can't be a member child!" % name)
                element = infos["reduce"](self, child_infos[1], child_infos[2])
                if element is not None:
                    result.append(element)
                if "name" in child_infos[1] and schema:
                    self.CurrentCompilations.pop(-1)
        annotations = []
        children = []
        for element in result:
            if element["type"] == "annotation":
                annotations.append(element)
            else:
                children.append(element)
        return annotations, children

    def AddComplexType(self, typename, infos):
        if typename not in self.XMLClassDefinitions:
            self.XMLClassDefinitions[typename] = infos
        else:
            raise ValueError("\"%s\" class already defined. Choose another name!" % typename)

    def ParseSchema(self):
        pass

    def AddEquivalentClass(self, name, base):
        if name != base:
            equivalences = self.EquivalentClassesParent.setdefault(self.etreeNamespaceFormat % base, {})
            equivalences[self.etreeNamespaceFormat % name] = True

    def AddDistinctionBetweenParentsInLookupClass(
            self, lookup_classes, parent, typeinfos):
        parent = (self.etreeNamespaceFormat % parent
                  if parent is not None else None)
        parent_class = lookup_classes.get(parent)
        if parent_class is not None:
            if isinstance(parent_class, list):
                if typeinfos not in parent_class:
                    lookup_classes[parent].append(typeinfos)
            elif parent_class != typeinfos:
                lookup_classes[parent] = [typeinfos, parent_class]
        else:
            lookup_classes[parent] = typeinfos

    def AddToLookupClass(self, name, parent, typeinfos):
        lookup_name = self.etreeNamespaceFormat % name
        if isinstance(typeinfos, string_types):
            self.AddEquivalentClass(name, typeinfos)
            typeinfos = self.etreeNamespaceFormat % typeinfos
        lookup_classes = self.ComputedClassesLookUp.get(lookup_name)
        if lookup_classes is None:
            self.ComputedClassesLookUp[lookup_name] = (typeinfos, parent)
        elif isinstance(lookup_classes, dict):
            self.AddDistinctionBetweenParentsInLookupClass(
                lookup_classes, parent, typeinfos)
        else:
            lookup_classes = {
                self.etreeNamespaceFormat % lookup_classes[1]
                if lookup_classes[1] is not None else None: lookup_classes[0]}
            self.AddDistinctionBetweenParentsInLookupClass(
                lookup_classes, parent, typeinfos)
            self.ComputedClassesLookUp[lookup_name] = lookup_classes

    def ExtractTypeInfos(self, name, parent, typeinfos):
        if isinstance(typeinfos, string_types):
            namespace, type_name = DecomposeQualifiedName(typeinfos)
            infos = self.GetQualifiedNameInfos(type_name, namespace)
            if name != "base":
                if infos["type"] == SIMPLETYPE:
                    self.AddToLookupClass(name, parent, DefaultElementClass)
                elif namespace == self.TargetNamespace:
                    self.AddToLookupClass(name, parent, type_name)
            if infos["type"] == COMPLEXTYPE:
                type_name, parent = self.SplitQualifiedName(type_name, namespace)
                result = self.CreateClass(type_name, parent, infos)
                if result is not None and not isinstance(result, string_types):
                    self.Namespaces[self.TargetNamespace][result["name"]] = result
                return result
            elif infos["type"] == ELEMENT and infos["elmt_type"]["type"] == COMPLEXTYPE:
                type_name, parent = self.SplitQualifiedName(type_name, namespace)
                result = self.CreateClass(type_name, parent, infos["elmt_type"])
                if result is not None and not isinstance(result, string_types):
                    self.Namespaces[self.TargetNamespace][result["name"]] = result
                return result
            else:
                return infos
        elif typeinfos["type"] == COMPLEXTYPE:
            return self.CreateClass(name, parent, typeinfos)
        elif typeinfos["type"] == SIMPLETYPE:
            return typeinfos

    def GetEquivalentParents(self, parent):
        return reduce(lambda x, y: x + y,
                      [[p] + self.GetEquivalentParents(p)
                       for p in self.EquivalentClassesParent.get(parent, {}).keys()], [])

    def CreateClasses(self):
        """
        Method that generates the classes
        """
        self.ParseSchema()
        for name, infos in self.Namespaces[self.TargetNamespace].items():
            if infos["type"] == ELEMENT:
                if not isinstance(infos["elmt_type"], string_types) and \
                   infos["elmt_type"]["type"] == COMPLEXTYPE:
                    self.ComputeAfter.append((name, None, infos["elmt_type"], True))
                    while len(self.ComputeAfter) > 0:
                        result = self.CreateClass(*self.ComputeAfter.pop(0))
                        if result is not None and not isinstance(result, string_types):
                            self.Namespaces[self.TargetNamespace][result["name"]] = result
            elif infos["type"] == COMPLEXTYPE:
                self.ComputeAfter.append((name, None, infos))
                while len(self.ComputeAfter) > 0:
                    result = self.CreateClass(*self.ComputeAfter.pop(0))
                    if result is not None and \
                       not isinstance(result, string_types):
                        self.Namespaces[self.TargetNamespace][result["name"]] = result
            elif infos["type"] == ELEMENTSGROUP:
                elements = []
                if "elements" in infos:
                    elements = infos["elements"]
                elif "choices" in infos:
                    elements = infos["choices"]
                for element in elements:
                    if not isinstance(element["elmt_type"], string_types) and \
                       element["elmt_type"]["type"] == COMPLEXTYPE:
                        self.ComputeAfter.append((element["name"], infos["name"], element["elmt_type"]))
                        while len(self.ComputeAfter) > 0:
                            result = self.CreateClass(*self.ComputeAfter.pop(0))
                            if result is not None and \
                               not isinstance(result, string_types):
                                self.Namespaces[self.TargetNamespace][result["name"]] = result

        for name, parents in self.ComputedClassesLookUp.iteritems():
            if isinstance(parents, dict):
                computed_classes = parents.items()
            elif parents[1] is not None:
                computed_classes = [(self.etreeNamespaceFormat % parents[1], parents[0])]
            else:
                computed_classes = []
            for parent, computed_class in computed_classes:
                for equivalent_parent in self.GetEquivalentParents(parent):
                    if not isinstance(parents, dict):
                        parents = dict(computed_classes)
                        self.ComputedClassesLookUp[name] = parents
                    parents[equivalent_parent] = computed_class

        return self.ComputedClasses

    def CreateClass(self, name, parent, classinfos, baseclass=False):
        if parent is not None:
            classname = "%s_%s" % (parent, name)
        else:
            classname = name

        # Checks that classe haven't been generated yet
        if self.AlreadyComputed.get(classname, False):
            return self.ComputedClassesInfos.get(classname, None)

        # If base classes haven't been generated
        bases = []
        base_infos = classinfos.get("base", None)
        if base_infos is not None:
            namespace, base_name = DecomposeQualifiedName(base_infos)
            if namespace == self.TargetNamespace:
                self.AddEquivalentClass(name, base_name)
            result = self.ExtractTypeInfos("base", name, base_infos)
            if result is None:
                namespace, base_name = DecomposeQualifiedName(base_infos)
                if self.AlreadyComputed.get(base_name, False):
                    self.ComputeAfter.append((name, parent, classinfos))
                    if self.TargetNamespace is not None:
                        return "%s:%s" % (self.TargetNamespace, classname)
                    else:
                        return classname
            elif result is not None:
                if self.FileName is not None:
                    classinfos["base"] = self.ComputedClasses[self.FileName].get(result["name"], None)
                    if classinfos["base"] is None:
                        for filename, classes in self.ComputedClasses.iteritems():
                            if filename != self.FileName:
                                classinfos["base"] = classes.get(result["name"], None)
                                if classinfos["base"] is not None:
                                    break
                else:
                    classinfos["base"] = self.ComputedClasses.get(result["name"], None)
                if classinfos["base"] is None:
                    raise ValueError("No class found for base type")
                bases.append(classinfos["base"])
        bases.append(DefaultElementClass)
        bases = tuple(bases)
        classmembers = {"__doc__": classinfos.get("doc", ""), "IsBaseClass": baseclass}

        self.AlreadyComputed[classname] = True

        for attribute in classinfos["attributes"]:
            infos = self.ExtractTypeInfos(attribute["name"], name, attribute["attr_type"])
            if infos is not None:
                if infos["type"] != SIMPLETYPE:
                    raise ValueError("\"%s\" type is not a simple type!" % attribute["attr_type"])
                attrname = attribute["name"]
                if attribute["use"] == "optional":
                    classmembers["add%s" % attrname] = generateAddMethod(attrname, self, attribute)
                    classmembers["delete%s" % attrname] = generateDeleteMethod(attrname)
                classmembers["set%s" % attrname] = generateSetMethod(attrname)
                classmembers["get%s" % attrname] = generateGetMethod(attrname)
            else:
                raise ValueError("\"%s\" type unrecognized!" % attribute["attr_type"])
            attribute["attr_type"] = infos

        for element in classinfos["elements"]:
            if element["type"] == CHOICE:
                elmtname = element["name"]
                choices = ComputeContentChoices(self, name, element)
                classmembers["get%schoices" % elmtname] = generateGetChoicesMethod(element["choices"])
                if element["maxOccurs"] == "unbounded" or element["maxOccurs"] > 1:
                    classmembers["append%sbytype" % elmtname] = generateAppendChoiceByTypeMethod(element["maxOccurs"], self, element["choices"])
                    classmembers["insert%sbytype" % elmtname] = generateInsertChoiceByTypeMethod(element["maxOccurs"], self, element["choices"])
                else:
                    classmembers["set%sbytype" % elmtname] = generateSetChoiceByTypeMethod(self, element["choices"])
                infos = GenerateContentInfos(self, name, choices)
            elif element["type"] == ANY:
                elmtname = element["name"] = "anyText"
                element["minOccurs"] = element["maxOccurs"] = 1
                infos = GenerateAnyInfos(element)
            else:
                elmtname = element["name"]
                if element["elmt_type"] == "tag":
                    infos = GenerateTagInfos(element)
                    self.AddToLookupClass(element["name"], name, DefaultElementClass)
                else:
                    infos = self.ExtractTypeInfos(element["name"], name, element["elmt_type"])
            if infos is not None:
                element["elmt_type"] = infos
            if element["maxOccurs"] == "unbounded" or element["maxOccurs"] > 1:
                classmembers["append%s" % elmtname] = generateAppendMethod(elmtname, element["maxOccurs"], self, element)
                classmembers["insert%s" % elmtname] = generateInsertMethod(elmtname, element["maxOccurs"], self, element)
                classmembers["remove%s" % elmtname] = generateRemoveMethod(elmtname, element["minOccurs"])
                classmembers["count%s" % elmtname] = generateCountMethod(elmtname)
            else:
                if element["minOccurs"] == 0:
                    classmembers["add%s" % elmtname] = generateAddMethod(elmtname, self, element)
                    classmembers["delete%s" % elmtname] = generateDeleteMethod(elmtname)
            classmembers["set%s" % elmtname] = generateSetMethod(elmtname)
            classmembers["get%s" % elmtname] = generateGetMethod(elmtname)

        classmembers["_init_"] = generateInitMethod(self, classinfos)
        classmembers["StructurePattern"] = GetStructurePattern(classinfos)
        classmembers["getElementAttributes"] = generateGetElementAttributes(self, classinfos)
        classmembers["getElementInfos"] = generateGetElementInfos(self, classinfos)
        classmembers["setElementValue"] = generateSetElementValue(self, classinfos)

        class_definition = type(str(name), bases, classmembers)
        setattr(class_definition, "__getattr__", generateGetattrMethod(self, class_definition, classinfos))
        setattr(class_definition, "__setattr__", generateSetattrMethod(self, class_definition, classinfos))
        class_infos = {
            "type": COMPILEDCOMPLEXTYPE,
            "name": classname,
            "initial": generateClassCreateFunction(self, class_definition),
        }
        if self.FileName is not None:
            self.ComputedClasses[self.FileName][classname] = class_definition
        else:
            self.ComputedClasses[classname] = class_definition
        self.ComputedClassesInfos[classname] = class_infos

        self.AddToLookupClass(name, parent, class_definition)
        self.AddToLookupClass(classname, None, class_definition)

        return class_infos

    def PrintClasses(self):
        """
        Method that print the classes generated
        """
        items = self.ComputedClasses.items()
        items.sort()
        if self.FileName is not None:
            for filename, classes in items:
                print("File '%s':" % filename)
                class_items = classes.items()
                class_items.sort()
                for classname, xmlclass in class_items:
                    print("%s: %s" % (classname, str(xmlclass)))
        else:
            for classname, xmlclass in items:
                print("%s: %s" % (classname, str(xmlclass)))

    def PrintClassNames(self):
        classnames = self.XMLClassDefinitions.keys()
        classnames.sort()
        for classname in classnames:
            print(classname)


def ComputeMultiplicity(name, infos):
    """
    Method that generate the method for generating the xml tree structure model by
    following the attributes list defined
    """
    if infos["minOccurs"] == 0:
        if infos["maxOccurs"] == "unbounded":
            return "(?:%s)*" % name
        elif infos["maxOccurs"] == 1:
            return "(?:%s)?" % name
        else:
            return "(?:%s){,%d}" % (name, infos["maxOccurs"])
    elif infos["minOccurs"] == 1:
        if infos["maxOccurs"] == "unbounded":
            return "(?:%s)+" % name
        elif infos["maxOccurs"] == 1:
            return "(?:%s)" % name
        else:
            return "(?:%s){1,%d}" % (name, infos["maxOccurs"])
    else:
        if infos["maxOccurs"] == "unbounded":
            return "(?:%s){%d,}" % (name, infos["minOccurs"])
        else:
            return "(?:%s){%d,%d}" % (name,
                                      infos["minOccurs"],
                                      infos["maxOccurs"])


def GetStructurePattern(classinfos):
    base_structure_pattern = (
        classinfos["base"].StructurePattern.pattern[:-1]
        if "base" in classinfos else "")
    elements = []
    for element in classinfos["elements"]:
        if element["type"] == ANY:
            infos = element.copy()
            infos["minOccurs"] = 0
            elements.append(ComputeMultiplicity(r"#text |#cdata-section |\w* ", infos))
        elif element["type"] == CHOICE:
            choices = []
            for infos in element["choices"]:
                if infos["type"] == "sequence":
                    structure = "(?:%s)" % GetStructurePattern(infos)
                else:
                    structure = "%s " % infos["name"]
                choices.append(ComputeMultiplicity(structure, infos))
            elements.append(ComputeMultiplicity("|".join(choices), element))
        elif element["name"] == "content" and element["elmt_type"]["type"] == SIMPLETYPE:
            elements.append("(?:#text |#cdata-section )?")
        else:
            elements.append(ComputeMultiplicity("%s " % element["name"], element))
    if classinfos.get("order", True) or len(elements) == 0:
        return re.compile(base_structure_pattern + "".join(elements) + "$")
    else:
        raise ValueError("XSD structure not yet supported!")


def generateClassCreateFunction(factory, class_definition):
    """
    Method that generate the method for creating a class instance
    """
    def classCreatefunction():
        return factory.Parser.CreateElementFromClass(class_definition)
    return classCreatefunction


def generateGetattrMethod(factory, class_definition, classinfos):
    attributes = dict([(attr["name"], attr) for attr in classinfos["attributes"] if attr["use"] != "prohibited"])
    elements = dict([(element["name"], element) for element in classinfos["elements"]])

    def getattrMethod(self, name):
        if name in attributes:
            attribute_infos = attributes[name]
            attribute_infos["attr_type"] = FindTypeInfos(factory, attribute_infos["attr_type"])
            value = self.get(name)
            if value is not None:
                return attribute_infos["attr_type"]["extract"](value, extract=False)
            elif "fixed" in attribute_infos:
                return attribute_infos["attr_type"]["extract"](attribute_infos["fixed"], extract=False)
            elif "default" in attribute_infos:
                return attribute_infos["attr_type"]["extract"](attribute_infos["default"], extract=False)
            return None

        elif name in elements:
            element_infos = elements[name]
            element_infos["elmt_type"] = FindTypeInfos(factory, element_infos["elmt_type"])
            if element_infos["type"] == CHOICE:
                content = element_infos["elmt_type"]["choices_xpath"](self)
                if element_infos["maxOccurs"] == "unbounded" or element_infos["maxOccurs"] > 1:
                    return content
                elif len(content) > 0:
                    return content[0]
                return None
            elif element_infos["type"] == ANY:
                return element_infos["elmt_type"]["extract"](self)
            elif name == "content" and element_infos["elmt_type"]["type"] == SIMPLETYPE:
                return element_infos["elmt_type"]["extract"](self.text, extract=False)
            else:
                element_name = factory.etreeNamespaceFormat % name
                if element_infos["maxOccurs"] == "unbounded" or element_infos["maxOccurs"] > 1:
                    values = self.findall(element_name)
                    if element_infos["elmt_type"]["type"] == SIMPLETYPE:
                        return map(lambda value:
                                   element_infos["elmt_type"]["extract"](value.text, extract=False),
                                   values)
                    return values
                else:
                    value = self.find(element_name)
                    if element_infos["elmt_type"]["type"] == SIMPLETYPE:
                        return element_infos["elmt_type"]["extract"](value.text, extract=False)
                    return value

        elif "base" in classinfos:
            return classinfos["base"].__getattr__(self, name)

        return DefaultElementClass.__getattribute__(self, name)

    return getattrMethod


def generateSetattrMethod(factory, class_definition, classinfos):
    attributes = dict([(attr["name"], attr) for attr in classinfos["attributes"] if attr["use"] != "prohibited"])
    optional_attributes = dict([(attr["name"], True) for attr in classinfos["attributes"] if attr["use"] == "optional"])
    elements = OrderedDict([(element["name"], element) for element in classinfos["elements"]])

    def setattrMethod(self, name, value):
        if name in attributes:
            attribute_infos = attributes[name]
            attribute_infos["attr_type"] = FindTypeInfos(factory, attribute_infos["attr_type"])
            if optional_attributes.get(name, False):
                default = attribute_infos.get("default", None)
                if value is None or value == default:
                    self.attrib.pop(name, None)
                    return
            elif "fixed" in attribute_infos:
                return
            return self.set(name, attribute_infos["attr_type"]["generate"](value))

        elif name in elements:
            element_infos = elements[name]
            element_infos["elmt_type"] = FindTypeInfos(factory, element_infos["elmt_type"])
            if element_infos["type"] == ANY:
                element_infos["elmt_type"]["generate"](self, value)

            elif name == "content" and element_infos["elmt_type"]["type"] == SIMPLETYPE:
                self.text = element_infos["elmt_type"]["generate"](value)

            else:
                prefix = ("%s:" % factory.TargetNamespace
                          if factory.TargetNamespace is not None else "")
                element_xpath = (prefix + name
                                 if name != "content"
                                 else elements["content"]["elmt_type"]["choices_xpath"].path)

                for element in self.xpath(element_xpath, namespaces=factory.NSMAP):
                    self.remove(element)

                if value is not None:
                    element_idx = elements.keys().index(name)
                    if element_idx > 0:
                        previous_elements_xpath = "|".join(map(
                            lambda x: prefix + x
                            if x != "content"
                            else elements["content"]["elmt_type"]["choices_xpath"].path,
                            elements.keys()[:element_idx]))

                        insertion_point = len(self.xpath(previous_elements_xpath, namespaces=factory.NSMAP))
                    else:
                        insertion_point = 0

                    if not isinstance(value, list):
                        value = [value]

                    for element in reversed(value):
                        if element_infos["elmt_type"]["type"] == SIMPLETYPE:
                            tmp_element = factory.Parser.makeelement(factory.etreeNamespaceFormat % name)
                            tmp_element.text = element_infos["elmt_type"]["generate"](element)
                            element = tmp_element
                        self.insert(insertion_point, element)

        elif "base" in classinfos:
            return classinfos["base"].__setattr__(self, name, value)

        else:
            raise AttributeError("'%s' can't have an attribute '%s'." % (self.__class__.__name__, name))

    return setattrMethod


def gettypeinfos(name, facets):
    if "enumeration" in facets and facets["enumeration"][0] is not None:
        return facets["enumeration"][0]
    elif "maxInclusive" in facets:
        limits = {"max": None, "min": None}
        if facets["maxInclusive"][0] is not None:
            limits["max"] = facets["maxInclusive"][0]
        elif facets["maxExclusive"][0] is not None:
            limits["max"] = facets["maxExclusive"][0] - 1
        if facets["minInclusive"][0] is not None:
            limits["min"] = facets["minInclusive"][0]
        elif facets["minExclusive"][0] is not None:
            limits["min"] = facets["minExclusive"][0] + 1
        if limits["max"] is not None or limits["min"] is not None:
            return limits
    return name


def generateGetElementAttributes(factory, classinfos):
    def getElementAttributes(self):
        attr_list = []
        if "base" in classinfos:
            attr_list.extend(classinfos["base"].getElementAttributes(self))
        for attr in classinfos["attributes"]:
            if attr["use"] != "prohibited":
                attr_params = {
                    "name": attr["name"],
                    "use": attr["use"],
                    "type": gettypeinfos(attr["attr_type"]["basename"], attr["attr_type"]["facets"]),
                    "value": getattr(self, attr["name"], "")}
                attr_list.append(attr_params)
        return attr_list
    return getElementAttributes


def generateGetElementInfos(factory, classinfos):
    attributes = dict([(attr["name"], attr) for attr in classinfos["attributes"] if attr["use"] != "prohibited"])
    elements = dict([(element["name"], element) for element in classinfos["elements"]])

    def getElementInfos(self, name, path=None, derived=False):
        attr_type = "element"
        value = None
        use = "required"
        children = []
        if path is not None:
            parts = path.split(".", 1)
            if parts[0] in attributes:
                if len(parts) != 1:
                    raise ValueError("Wrong path!")
                attr_type = gettypeinfos(attributes[parts[0]]["attr_type"]["basename"],
                                         attributes[parts[0]]["attr_type"]["facets"])
                value = getattr(self, parts[0], "")
            elif parts[0] in elements:
                if elements[parts[0]]["elmt_type"]["type"] == SIMPLETYPE:
                    if len(parts) != 1:
                        raise ValueError("Wrong path!")
                    attr_type = gettypeinfos(elements[parts[0]]["elmt_type"]["basename"],
                                             elements[parts[0]]["elmt_type"]["facets"])
                    value = getattr(self, parts[0], "")
                elif parts[0] == "content":
                    return self.content.getElementInfos(self.content.getLocalTag(), path)
                else:
                    attr = getattr(self, parts[0], None)
                    if attr is None:
                        raise ValueError("Wrong path!")
                    if len(parts) == 1:
                        return attr.getElementInfos(parts[0])
                    else:
                        return attr.getElementInfos(parts[0], parts[1])
            elif "content" in elements:
                if len(parts) > 0:
                    return self.content.getElementInfos(name, path)
            elif "base" in classinfos:
                classinfos["base"].getElementInfos(name, path)
            else:
                raise ValueError("Wrong path!")
        else:
            if not derived:
                children.extend(self.getElementAttributes())
            if "base" in classinfos:
                children.extend(classinfos["base"].getElementInfos(self, name, derived=True)["children"])
            for element_name, element in elements.items():
                if element["minOccurs"] == 0:
                    use = "optional"
                if element_name == "content" and element["type"] == CHOICE:
                    attr_type = [(choice["name"], None) for choice in element["choices"]]
                    if self.content is None:
                        value = ""
                    else:
                        value = self.content.getLocalTag()
                        if self.content is not None:
                            children.extend(self.content.getElementInfos(value)["children"])
                elif element["elmt_type"]["type"] == SIMPLETYPE:
                    children.append({
                        "name": element_name,
                        "require": element["minOccurs"] != 0,
                        "type": gettypeinfos(element["elmt_type"]["basename"],
                                             element["elmt_type"]["facets"]),
                        "value": getattr(self, element_name, None)})
                else:
                    instance = getattr(self, element_name, None)
                    if instance is None:
                        instance = element["elmt_type"]["initial"]()
                    children.append(instance.getElementInfos(element_name))
        return {"name": name, "type": attr_type, "value": value, "use": use, "children": children}
    return getElementInfos


def generateSetElementValue(factory, classinfos):
    attributes = dict([(attr["name"], attr) for attr in classinfos["attributes"] if attr["use"] != "prohibited"])
    elements = dict([(element["name"], element) for element in classinfos["elements"]])

    def setElementValue(self, path, value):
        if path is not None:
            parts = path.split(".", 1)
            if parts[0] in attributes:
                if len(parts) != 1:
                    raise ValueError("Wrong path!")
                if attributes[parts[0]]["attr_type"]["basename"] == "boolean":
                    setattr(self, parts[0], value)
                elif attributes[parts[0]]["use"] == "optional" and value == "":
                    if "default" in attributes[parts[0]]:
                        setattr(self, parts[0],
                                attributes[parts[0]]["attr_type"]["extract"](
                                    attributes[parts[0]]["default"], False))
                    else:
                        setattr(self, parts[0], None)
                else:
                    setattr(self, parts[0], attributes[parts[0]]["attr_type"]["extract"](value, False))
            elif parts[0] in elements:
                if elements[parts[0]]["elmt_type"]["type"] == SIMPLETYPE:
                    if len(parts) != 1:
                        raise ValueError("Wrong path!")
                    if elements[parts[0]]["elmt_type"]["basename"] == "boolean":
                        setattr(self, parts[0], value)
                    elif attributes[parts[0]]["minOccurs"] == 0 and value == "":
                        setattr(self, parts[0], None)
                    else:
                        setattr(self, parts[0], elements[parts[0]]["elmt_type"]["extract"](value, False))
                else:
                    instance = getattr(self, parts[0], None)
                    if instance is None and elements[parts[0]]["minOccurs"] == 0:
                        instance = elements[parts[0]]["elmt_type"]["initial"]()
                        setattr(self, parts[0], instance)
                    if instance is not None:
                        if len(parts) > 1:
                            instance.setElementValue(parts[1], value)
                        else:
                            instance.setElementValue(None, value)
            elif "content" in elements:
                if len(parts) > 0:
                    self.content.setElementValue(path, value)
            elif "base" in classinfos:
                classinfos["base"].setElementValue(self, path, value)
        elif "content" in elements:
            if value == "":
                if elements["content"]["minOccurs"] == 0:
                    self.setcontent([])
                else:
                    raise ValueError("\"content\" element is required!")
            else:
                self.setcontentbytype(value)
    return setElementValue


def generateInitMethod(factory, classinfos):
    """
    Methods that generates the different methods for setting and getting the attributes
    """

    def initMethod(self):
        if "base" in classinfos:
            classinfos["base"]._init_(self)
        for attribute in classinfos["attributes"]:
            attribute["attr_type"] = FindTypeInfos(factory, attribute["attr_type"])
            if attribute["use"] == "required":
                self.set(attribute["name"], attribute["attr_type"]["generate"](attribute["attr_type"]["initial"]()))
        for element in classinfos["elements"]:
            if element["type"] != CHOICE:
                initial = GetElementInitialValue(factory, element)
                if initial is not None:
                    map(self.append, initial)
    return initMethod


def generateSetMethod(attr):
    def setMethod(self, value):
        setattr(self, attr, value)
    return setMethod


def generateGetMethod(attr):
    def getMethod(self):
        return getattr(self, attr, None)
    return getMethod


def generateAddMethod(attr, factory, infos):
    def addMethod(self):
        if infos["type"] == ATTRIBUTE:
            infos["attr_type"] = FindTypeInfos(factory, infos["attr_type"])
            if "default" not in infos:
                setattr(self, attr, infos["attr_type"]["initial"]())
        elif infos["type"] == ELEMENT:
            infos["elmt_type"] = FindTypeInfos(factory, infos["elmt_type"])
            value = infos["elmt_type"]["initial"]()
            DefaultElementClass.__setattr__(value, "tag", factory.etreeNamespaceFormat % attr)
            setattr(self, attr, value)
            value._init_()
        else:
            raise ValueError("Invalid class attribute!")
    return addMethod


def generateDeleteMethod(attr):
    def deleteMethod(self):
        setattr(self, attr, None)
    return deleteMethod


def generateAppendMethod(attr, maxOccurs, factory, infos):
    def appendMethod(self, value):
        infos["elmt_type"] = FindTypeInfos(factory, infos["elmt_type"])
        attr_list = getattr(self, attr)
        if maxOccurs == "unbounded" or len(attr_list) < maxOccurs:
            if len(attr_list) == 0:
                setattr(self, attr, [value])
            else:
                attr_list[-1].addnext(value)
        else:
            raise ValueError("There can't be more than %d values in \"%s\"!" % (maxOccurs, attr))
    return appendMethod


def generateInsertMethod(attr, maxOccurs, factory, infos):
    def insertMethod(self, index, value):
        infos["elmt_type"] = FindTypeInfos(factory, infos["elmt_type"])
        attr_list = getattr(self, attr)
        if maxOccurs == "unbounded" or len(attr_list) < maxOccurs:
            if len(attr_list) == 0:
                setattr(self, attr, [value])
            elif index == 0:
                attr_list[0].addprevious(value)
            else:
                attr_list[min(index - 1, len(attr_list) - 1)].addnext(value)
        else:
            raise ValueError("There can't be more than %d values in \"%s\"!" % (maxOccurs, attr))
    return insertMethod


def generateGetChoicesMethod(choice_types):
    def getChoicesMethod(self):
        return [choice["name"] for choice in choice_types]
    return getChoicesMethod


def generateSetChoiceByTypeMethod(factory, choice_types):
    choices = dict([(choice["name"], choice) for choice in choice_types])

    def setChoiceMethod(self, content_type):
        if content_type not in choices:
            raise ValueError("Unknown \"%s\" choice type for \"content\"!" % content_type)
        choices[content_type]["elmt_type"] = FindTypeInfos(factory, choices[content_type]["elmt_type"])
        new_content = choices[content_type]["elmt_type"]["initial"]()
        DefaultElementClass.__setattr__(new_content, "tag", factory.etreeNamespaceFormat % content_type)
        self.content = new_content
        return new_content
    return setChoiceMethod


def generateAppendChoiceByTypeMethod(maxOccurs, factory, choice_types):
    choices = dict([(choice["name"], choice) for choice in choice_types])

    def appendChoiceMethod(self, content_type):
        if content_type not in choices:
            raise ValueError("Unknown \"%s\" choice type for \"content\"!" % content_type)
        choices[content_type]["elmt_type"] = FindTypeInfos(factory, choices[content_type]["elmt_type"])
        if maxOccurs == "unbounded" or len(self.content) < maxOccurs:
            new_element = choices[content_type]["elmt_type"]["initial"]()
            DefaultElementClass.__setattr__(new_element, "tag", factory.etreeNamespaceFormat % content_type)
            self.appendcontent(new_element)
            return new_element
        else:
            raise ValueError("There can't be more than %d values in \"content\"!" % maxOccurs)
    return appendChoiceMethod


def generateInsertChoiceByTypeMethod(maxOccurs, factory, choice_types):
    choices = dict([(choice["name"], choice) for choice in choice_types])

    def insertChoiceMethod(self, index, content_type):
        if content_type not in choices:
            raise ValueError("Unknown \"%s\" choice type for \"content\"!" % content_type)
        choices[type]["elmt_type"] = FindTypeInfos(factory, choices[content_type]["elmt_type"])
        if maxOccurs == "unbounded" or len(self.content) < maxOccurs:
            new_element = choices[content_type]["elmt_type"]["initial"]()
            DefaultElementClass.__setattr__(new_element, "tag", factory.etreeNamespaceFormat % content_type)
            self.insertcontent(index, new_element)
            return new_element
        else:
            raise ValueError("There can't be more than %d values in \"content\"!" % maxOccurs)
    return insertChoiceMethod


def generateRemoveMethod(attr, minOccurs):
    def removeMethod(self, index):
        attr_list = getattr(self, attr)
        if len(attr_list) > minOccurs:
            self.remove(attr_list[index])
        else:
            raise ValueError("There can't be less than %d values in \"%s\"!" % (minOccurs, attr))
    return removeMethod


def generateCountMethod(attr):
    def countMethod(self):
        return len(getattr(self, attr))
    return countMethod


NAMESPACE_PATTERN = re.compile(r"xmlns(?:\:[^\=]*)?=\"[^\"]*\" ")


class DefaultElementClass(etree.ElementBase):

    StructurePattern = re.compile("$")

    def _init_(self):
        pass

    def getLocalTag(self):
        return etree.QName(self.tag).localname

    def tostring(self):
        return NAMESPACE_PATTERN.sub("", etree.tostring(self, pretty_print=True, encoding='utf-8')).decode('utf-8')


class XMLElementClassLookUp(etree.PythonElementClassLookup):

    def __init__(self, classes, *args, **kwargs):
        etree.PythonElementClassLookup.__init__(self, *args, **kwargs)
        self.LookUpClasses = classes
        self.ElementTag = None
        self.ElementClass = None

    def GetElementClass(self, element_tag, parent_tag=None, default=DefaultElementClass):
        element_class = self.LookUpClasses.get(element_tag, (default, None))
        if not isinstance(element_class, dict):
            if isinstance(element_class[0], string_types):
                return self.GetElementClass(element_class[0], default=default)
            return element_class[0]

        element_with_parent_class = element_class.get(parent_tag, default)
        if isinstance(element_with_parent_class, string_types):
            return self.GetElementClass(element_with_parent_class, default=default)
        return element_with_parent_class

    def SetLookupResult(self, element, element_class):
        """
        Set lookup result for the next 'lookup' callback made by lxml backend.
        Lookup result is used only if element matches with tag's name submited to 'lookup'.
        This is done, because there is no way to submit extra search parameters for
        etree.PythonElementClassLookup.lookup() from etree.XMLParser.makeelement()
        It's valid only for a signle 'lookup' call.

        :param element:
            element's tag name
        :param element_class:
            element class that should be returned on
            match in the next 'lookup' call.
        :return:
            Nothing
        """
        self.ElementTag = element
        self.ElementClass = element_class

    def ResetLookupResult(self):
        """Reset lookup result, so it don't influence next lookups"""
        self.ElementTag = None
        self.ElementClass = None

    def GetLookupResult(self, element):
        """Returns previously set SetLookupResult() lookup result"""
        element_class = None
        if self.ElementTag is not None and self.ElementTag == element.tag:
            element_class = self.ElementClass
        self.ResetLookupResult()
        return element_class

    def lookup(self, document, element):
        """
        Lookup for element class for given element tag.
        If return None from this method, the fallback is called.

        :param document:
            opaque document instance that contains the Element
        :param element:
            lightweight Element proxy implementation that is only valid during the lookup.
            Do not try to keep a reference to it.
            Once the lookup is done, the proxy will be invalid.
        :return:
            Returns element class corresponding to given element.
        """
        element_class = self.GetLookupResult(element)
        if element_class is not None:
            return element_class

        parent = element.getparent()
        element_class = self.GetElementClass(
            element.tag, parent.tag if parent is not None else None)
        if isinstance(element_class, list):
            children = "".join([
                "%s " % etree.QName(child.tag).localname
                for child in element])
            for possible_class in element_class:
                if isinstance(possible_class, string_types):
                    possible_class = self.GetElementClass(possible_class)
                if possible_class.StructurePattern.match(children) is not None:
                    return possible_class
            return element_class[0]
        return element_class


class XMLClassParser(etree.XMLParser):
    def __init__(self, *args, **kwargs):
        etree.XMLParser.__init__(self, *args, **kwargs)

    def initMembers(self, namespaces, default_namespace_format, base_class, xsd_schema):
        self.DefaultNamespaceFormat = default_namespace_format
        self.NSMAP = namespaces
        targetNamespace = etree.QName(default_namespace_format % "d").namespace
        if targetNamespace is not None:
            self.RootNSMAP = {
                name if targetNamespace != uri else None: uri
                for name, uri in namespaces.iteritems()}
        else:
            self.RootNSMAP = namespaces
        self.BaseClass = base_class
        self.XSDSchema = xsd_schema

    def set_element_class_lookup(self, class_lookup):
        etree.XMLParser.set_element_class_lookup(self, class_lookup)
        self.ClassLookup = class_lookup

    def LoadXMLString(self, xml_string):
        tree = etree.fromstring(xml_string, self)
        if not self.XSDSchema.validate(tree):
            error = self.XSDSchema.error_log.last_error
            return tree, (error.line, error.message)
        return tree, None

    def Dumps(self, xml_obj):
        return etree.tostring(xml_obj, encoding='utf-8')

    def Loads(self, xml_string):
        return etree.fromstring(xml_string, self)

    def CreateRoot(self):
        if self.BaseClass is not None:
            root = self.makeelement(
                self.DefaultNamespaceFormat % self.BaseClass[0],
                nsmap=self.RootNSMAP)
            root._init_()
            return root
        return None

    def GetElementClass(self, element_tag, parent_tag=None):
        return self.ClassLookup.GetElementClass(
            self.DefaultNamespaceFormat % element_tag,
            self.DefaultNamespaceFormat % parent_tag
            if parent_tag is not None else parent_tag,
            None)

    def CreateElement(self, element_tag, parent_tag=None, class_idx=None):
        """
        Create XML element based on elements and parent's tag names.

        :param element_tag:
            element's tag name
        :param parent_tag:
            optional parent's tag name. Default value is None.
        :param class_idx:
            optional index of class in list of founded classes
            with same element and parent. Default value is None.
        :return:
            created XML element
            (subclass of lxml.etree._Element created by class factory)
        """
        element_class = self.GetElementClass(element_tag, parent_tag)
        if isinstance(element_class, list):
            if class_idx is not None and class_idx < len(element_class):
                element_class = element_class[class_idx]
            else:
                raise ValueError("No corresponding class found!")
        return self.CreateElementFromClass(element_class, element_tag)

    def CreateElementFromClass(self, element_class, element_tag=None):
        """
        Create XML element instance of submitted element's class.
        Submitted class should be subclass of lxml.etree._Element.

        element_class shouldn't be used to create XML element
        directly using element_class(), because lxml backend
        should be aware what class handles what xml element,
        otherwise default lxml.etree._Element will be used.

        :param element_class:
            element class
        :param element_tag:
            optional element's tag name.
            If omitted it's calculated from element_class instance.
        :return:
            created XML element
            (subclass of lxml.etree._Element created by class factory)
        """
        if element_tag is None:
            element_tag = element_class().tag
        etag = self.DefaultNamespaceFormat % element_tag
        self.ClassLookup.SetLookupResult(etag, element_class)
        new_element = self.makeelement(etag)
        self.ClassLookup.ResetLookupResult()
        DefaultElementClass.__setattr__(new_element, "tag", self.DefaultNamespaceFormat % element_tag)
        new_element._init_()
        return new_element


def GenerateParser(factory, xsdstring):
    """
    This function generate a xml parser from a class factory
    """

    parser = XMLClassParser(strip_cdata=False, remove_blank_text=True)
    factory.Parser = parser

    ComputedClasses = factory.CreateClasses()
    if factory.FileName is not None:
        ComputedClasses = ComputedClasses[factory.FileName]
    BaseClass = [(name, XSDclass) for name, XSDclass in ComputedClasses.items() if XSDclass.IsBaseClass]

    parser.initMembers(
        factory.NSMAP,
        factory.etreeNamespaceFormat,
        BaseClass[0] if len(BaseClass) == 1 else None,
        etree.XMLSchema(etree.fromstring(xsdstring)))

    class_lookup = XMLElementClassLookUp(factory.ComputedClassesLookUp)
    parser.set_element_class_lookup(class_lookup)

    return parser
