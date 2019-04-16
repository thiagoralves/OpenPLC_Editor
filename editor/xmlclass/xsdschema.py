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
from types import FunctionType
from xml.dom import minidom
from future.builtins import round
from six import string_types
from past.builtins import long

from xmlclass.xmlclass import *


def GenerateDictFacets(facets):
    return dict([(name, (None, False)) for name in facets])


def GenerateSimpleTypeXMLText(function):
    def generateXMLTextMethod(value, name=None, indent=0):
        text = ""
        if name is not None:
            ind1, _ind2 = getIndent(indent, name)
            text += ind1 + "<%s>" % name
        text += function(value)
        if name is not None:
            text += "</%s>\n" % name
        return text
    return generateXMLTextMethod


def GenerateFloatXMLText(extra_values=None, decimal=None):
    float_format = (lambda x: "{:.{width}f}".format(x, width=decimal).rstrip('0')
                    if decimal is not None else str)
    extra_values = [] if extra_values is None else extra_values

    def generateXMLTextMethod(value, name=None, indent=0):
        text = ""
        if name is not None:
            ind1, _ind2 = getIndent(indent, name)
            text += ind1 + "<%s>" % name
        if isinstance(value, int):
            text += str(value)
        elif value in extra_values or value % 1 != 0:
            text += float_format(value)
        else:
            text += "{:.0f}".format(value)
        if name is not None:
            text += "</%s>\n" % name
        return text
    return generateXMLTextMethod


DEFAULT_FACETS = GenerateDictFacets(["pattern", "whiteSpace", "enumeration"])
NUMBER_FACETS = GenerateDictFacets(DEFAULT_FACETS.keys() + ["maxInclusive", "maxExclusive", "minInclusive", "minExclusive"])
DECIMAL_FACETS = GenerateDictFacets(NUMBER_FACETS.keys() + ["totalDigits", "fractionDigits"])
STRING_FACETS = GenerateDictFacets(DEFAULT_FACETS.keys() + ["length", "minLength", "maxLength"])

ALL_FACETS = ["pattern", "whiteSpace", "enumeration", "maxInclusive",
              "maxExclusive", "minInclusive", "minExclusive", "totalDigits",
              "fractionDigits", "length", "minLength", "maxLength"]


# -------------------------------------------------------------------------------
#                           Structure reducing functions
# -------------------------------------------------------------------------------


# Documentation elements

def ReduceAppInfo(factory, attributes, elements):
    return {"type": "appinfo", "source": attributes.get("source", None),
            "content": "\n".join(elements)}


def ReduceDocumentation(factory, attributes, elements):
    return {"type": "documentation", "source": attributes.get("source", None),
            "language": attributes.get("lang", "any"), "content": "\n".join(elements)}


def ReduceAnnotation(factory, attributes, elements):
    _annotations, children = factory.ReduceElements(elements)
    annotation = {"type": "annotation", "appinfo": [], "documentation": {}}
    for child in children:
        if child["type"] == "appinfo":
            annotation["appinfo"].append((child["source"], child["content"]))
        elif child["type"] == "documentation":
            if child["source"] is not None:
                text = "(source: %(source)s):\n%(content)s\n\n" % child
            else:
                text = child["content"] + "\n\n"
            if not child["language"] in annotation["documentation"]:
                annotation["documentation"] = text
            else:
                annotation["documentation"] += text
    return annotation

# Simple type elements


def GenerateFacetReducing(facetname, canbefixed):
    def ReduceFacet(factory, attributes, elements):
        annotations, _children = factory.ReduceElements(elements)
        if "value" in attributes:
            facet = {"type": facetname, "value": attributes["value"], "doc": annotations}
            if canbefixed:
                facet["fixed"] = attributes.get("fixed", False)
            return facet
        raise ValueError("A value must be defined for the \"%s\" facet!" % facetname)
    return ReduceFacet


def ReduceList(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)
    list = {"type": "list", "itemType": attributes.get("itemType", None), "doc": annotations}

    if len(children) > 0 and children[0]["type"] == SIMPLETYPE:
        if list["itemType"] is None:
            list["itemType"] = children[0]
        else:
            raise ValueError("Only one base type can be defined for restriction!")
    if list["itemType"] is None:
        raise ValueError("No base type has been defined for list!")
    return list


def ReduceUnion(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)
    union = {"type": "union", "memberTypes": attributes.get("memberTypes", []), "doc": annotations}

    for child in children:
        if child["type"] == SIMPLETYPE:
            union["memberTypes"].append(child)
    if len(union["memberTypes"]) == 0:
        raise ValueError("No base type has been defined for union!")
    return union


def CreateSimpleType(factory, attributes, typeinfos):
    # Initialize type informations
    facets = {}
    simpleType = {"type": SIMPLETYPE, "final": attributes.get("final", [])}
    if "name" in attributes:
        simpleType["name"] = attributes["name"]

    if typeinfos["type"] in ["restriction", "extension"]:
        # Search for base type definition
        if isinstance(typeinfos["base"], string_types):
            basetypeinfos = factory.FindSchemaElement(typeinfos["base"], SIMPLETYPE)
            if basetypeinfos is None:
                raise "\"%s\" isn't defined!" % typeinfos["base"]
        else:
            basetypeinfos = typeinfos["base"]

        # Check that base type is a simple type
        if basetypeinfos["type"] != SIMPLETYPE:
            raise ValueError("Base type given isn't a simpleType!")

        simpleType["basename"] = basetypeinfos["basename"]

        # Check that derivation is allowed
        if "final" in basetypeinfos:
            if "#all" in basetypeinfos["final"]:
                raise ValueError("Base type can't be derivated!")
            if "restriction" in basetypeinfos["final"] and typeinfos["type"] == "restriction":
                raise ValueError("Base type can't be derivated by restriction!")

        # Extract simple type facets
        for facet in typeinfos.get("facets", []):
            facettype = facet["type"]
            if facettype not in basetypeinfos["facets"]:
                raise ValueError("\"%s\" facet can't be defined for \"%s\" type!" % (facettype, type))
            elif basetypeinfos["facets"][facettype][1]:
                raise ValueError("\"%s\" facet is fixed on base type!" % facettype)
            value = facet["value"]
            basevalue = basetypeinfos["facets"][facettype][0]
            if facettype in ["enumeration", "pattern"]:
                value = basetypeinfos["extract"](value, False)
                if len(facets) == 0:
                    facets[facettype] = ([value], False)
                    continue
                elif facets.keys() == [facettype]:
                    facets[facettype][0].append(value)
                    continue
                else:
                    raise ValueError("\"%s\" facet can't be defined with another facet type!" % facettype)
            elif "enumeration" in facets:
                raise ValueError("\"enumeration\" facet can't be defined with another facet type!")
            elif "pattern" in facets:
                raise ValueError("\"pattern\" facet can't be defined with another facet type!")
            elif facettype in facets:
                raise ValueError("\"%s\" facet can't be defined two times!" % facettype)
            elif facettype == "length":
                if "minLength" in facets:
                    raise ValueError("\"length\" and \"minLength\" facets can't be defined at the same time!")
                if "maxLength" in facets:
                    raise ValueError("\"length\" and \"maxLength\" facets can't be defined at the same time!")
                try:
                    value = int(value)
                except Exception:
                    raise ValueError("\"length\" must be an integer!")
                if value < 0:
                    raise ValueError("\"length\" can't be negative!")
                elif basevalue is not None and basevalue != value:
                    raise ValueError("\"length\" can't be different from \"length\" defined in base type!")
            elif facettype == "minLength":
                if "length" in facets:
                    raise ValueError("\"length\" and \"minLength\" facets can't be defined at the same time!")
                try:
                    value = int(value)
                except Exception:
                    raise ValueError("\"minLength\" must be an integer!")
                if value < 0:
                    raise ValueError("\"minLength\" can't be negative!")
                elif "maxLength" in facets and value > facets["maxLength"]:
                    raise ValueError("\"minLength\" must be lesser than or equal to \"maxLength\"!")
                elif basevalue is not None and basevalue < value:
                    raise ValueError("\"minLength\" can't be lesser than \"minLength\" defined in base type!")
            elif facettype == "maxLength":
                if "length" in facets:
                    raise ValueError("\"length\" and \"maxLength\" facets can't be defined at the same time!")
                try:
                    value = int(value)
                except Exception:
                    raise ValueError("\"maxLength\" must be an integer!")
                if value < 0:
                    raise ValueError("\"maxLength\" can't be negative!")
                elif "minLength" in facets and value < facets["minLength"]:
                    raise ValueError("\"minLength\" must be lesser than or equal to \"maxLength\"!")
                elif basevalue is not None and basevalue > value:
                    raise ValueError("\"maxLength\" can't be greater than \"maxLength\" defined in base type!")
            elif facettype == "minInclusive":
                if "minExclusive" in facets:
                    raise ValueError("\"minExclusive\" and \"minInclusive\" facets can't be defined at the same time!")
                value = basetypeinfos["extract"](facet["value"], False)
                if "maxInclusive" in facets and value > facets["maxInclusive"][0]:
                    raise ValueError("\"minInclusive\" must be lesser than or equal to \"maxInclusive\"!")
                elif "maxExclusive" in facets and value >= facets["maxExclusive"][0]:
                    raise ValueError("\"minInclusive\" must be lesser than \"maxExclusive\"!")
            elif facettype == "minExclusive":
                if "minInclusive" in facets:
                    raise ValueError("\"minExclusive\" and \"minInclusive\" facets can't be defined at the same time!")
                value = basetypeinfos["extract"](facet["value"], False)
                if "maxInclusive" in facets and value >= facets["maxInclusive"][0]:
                    raise ValueError("\"minExclusive\" must be lesser than \"maxInclusive\"!")
                elif "maxExclusive" in facets and value >= facets["maxExclusive"][0]:
                    raise ValueError("\"minExclusive\" must be lesser than \"maxExclusive\"!")
            elif facettype == "maxInclusive":
                if "maxExclusive" in facets:
                    raise ValueError("\"maxExclusive\" and \"maxInclusive\" facets can't be defined at the same time!")
                value = basetypeinfos["extract"](facet["value"], False)
                if "minInclusive" in facets and value < facets["minInclusive"][0]:
                    raise ValueError("\"minInclusive\" must be lesser than or equal to \"maxInclusive\"!")
                elif "minExclusive" in facets and value <= facets["minExclusive"][0]:
                    raise ValueError("\"minExclusive\" must be lesser than \"maxInclusive\"!")
            elif facettype == "maxExclusive":
                if "maxInclusive" in facets:
                    raise ValueError("\"maxExclusive\" and \"maxInclusive\" facets can't be defined at the same time!")
                value = basetypeinfos["extract"](facet["value"], False)
                if "minInclusive" in facets and value <= facets["minInclusive"][0]:
                    raise ValueError("\"minInclusive\" must be lesser than \"maxExclusive\"!")
                elif "minExclusive" in facets and value <= facets["minExclusive"][0]:
                    raise ValueError("\"minExclusive\" must be lesser than \"maxExclusive\"!")
            elif facettype == "whiteSpace":
                if basevalue == "collapse" and value in ["preserve", "replace"] or basevalue == "replace" and value == "preserve":
                    raise ValueError("\"whiteSpace\" is incompatible with \"whiteSpace\" defined in base type!")
            elif facettype == "totalDigits":
                if "fractionDigits" in facets and value <= facets["fractionDigits"][0]:
                    raise ValueError("\"fractionDigits\" must be lesser than or equal to \"totalDigits\"!")
                elif basevalue is not None and value > basevalue:
                    raise ValueError("\"totalDigits\" can't be greater than \"totalDigits\" defined in base type!")
            elif facettype == "fractionDigits":
                if "totalDigits" in facets and value <= facets["totalDigits"][0]:
                    raise ValueError("\"fractionDigits\" must be lesser than or equal to \"totalDigits\"!")
                elif basevalue is not None and value > basevalue:
                    raise ValueError("\"totalDigits\" can't be greater than \"totalDigits\" defined in base type!")
            facets[facettype] = (value, facet.get("fixed", False))

        # Report not redefined facet from base type to new created type
        for facettype, facetvalue in basetypeinfos["facets"].items():
            if facettype not in facets:
                facets[facettype] = facetvalue

        # Generate extract value for new created type
        def ExtractSimpleTypeValue(attr, extract=True):
            value = basetypeinfos["extract"](attr, extract)
            for facetname, (facetvalue, _facetfixed) in facets.items():
                if facetvalue is not None:
                    if facetname == "enumeration" and value not in facetvalue:
                        raise ValueError("\"%s\" not in enumerated values" % value)
                    elif facetname == "length" and len(value) != facetvalue:
                        raise ValueError("value must have a length of %d" % facetvalue)
                    elif facetname == "minLength" and len(value) < facetvalue:
                        raise ValueError("value must have a length of %d at least" % facetvalue)
                    elif facetname == "maxLength" and len(value) > facetvalue:
                        raise ValueError("value must have a length of %d at most" % facetvalue)
                    elif facetname == "minInclusive" and value < facetvalue:
                        raise ValueError("value must be greater than or equal to %s" % str(facetvalue))
                    elif facetname == "minExclusive" and value <= facetvalue:
                        raise ValueError("value must be greater than %s" % str(facetvalue))
                    elif facetname == "maxInclusive" and value > facetvalue:
                        raise ValueError("value must be lesser than or equal to %s" % str(facetvalue))
                    elif facetname == "maxExclusive" and value >= facetvalue:
                        raise ValueError("value must be lesser than %s" % str(facetvalue))
                    elif facetname == "pattern":
                        model = re.compile("(?:%s)?$" % "|".join(map(lambda x: "(?:%s)" % x, facetvalue)))
                        result = model.match(value)
                        if result is None:
                            if len(facetvalue) > 1:
                                raise ValueError("value doesn't follow any of the patterns %s" % ",".join(facetvalue))
                            else:
                                raise ValueError("value doesn't follow the pattern %s" % facetvalue[0])
                    elif facetname == "whiteSpace":
                        if facetvalue == "replace":
                            value = GetNormalizedString(value, False)
                        elif facetvalue == "collapse":
                            value = GetToken(value, False)
            return value

        def CheckSimpleTypeValue(value):
            for facetname, (facetvalue, _facetfixed) in facets.items():
                if facetvalue is not None:
                    if facetname == "enumeration" and value not in facetvalue:
                        return False
                    elif facetname == "length" and len(value) != facetvalue:
                        return False
                    elif facetname == "minLength" and len(value) < facetvalue:
                        return False
                    elif facetname == "maxLength" and len(value) > facetvalue:
                        return False
                    elif facetname == "minInclusive" and value < facetvalue:
                        return False
                    elif facetname == "minExclusive" and value <= facetvalue:
                        return False
                    elif facetname == "maxInclusive" and value > facetvalue:
                        return False
                    elif facetname == "maxExclusive" and value >= facetvalue:
                        return False
                    elif facetname == "pattern":
                        model = re.compile("(?:%s)?$" % "|".join(map(lambda x: "(?:%s)" % x, facetvalue)))
                        result = model.match(value)
                        if result is None:
                            if len(facetvalue) > 1:
                                raise ValueError("value doesn't follow any of the patterns %s" % ",".join(facetvalue))
                            else:
                                raise ValueError("value doesn't follow the pattern %s" % facetvalue[0])
            return True

        def SimpleTypeInitialValue():
            for facetname, (facetvalue, _facetfixed) in facets.items():
                if facetvalue is not None:
                    if facetname == "enumeration":
                        return facetvalue[0]
                    elif facetname == "length":
                        return " "*facetvalue
                    elif facetname == "minLength":
                        return " "*facetvalue
                    elif facetname == "minInclusive" and facetvalue > 0:
                        return facetvalue
                    elif facetname == "minExclusive" and facetvalue >= 0:
                        return facetvalue + 1
                    elif facetname == "maxInclusive" and facetvalue < 0:
                        return facetvalue
                    elif facetname == "maxExclusive" and facetvalue <= 0:
                        return facetvalue - 1
            return basetypeinfos["initial"]()

        GenerateSimpleType = basetypeinfos["generate"]

    elif typeinfos["type"] == "list":
        # Search for item type definition
        if isinstance(typeinfos["itemType"], string_types):
            itemtypeinfos = factory.FindSchemaElement(typeinfos["itemType"], SIMPLETYPE)
            if itemtypeinfos is None:
                raise "\"%s\" isn't defined!" % typeinfos["itemType"]
        else:
            itemtypeinfos = typeinfos["itemType"]

        # Check that item type is a simple type
        if itemtypeinfos["type"] != SIMPLETYPE:
            raise ValueError("Item type given isn't a simpleType!")

        simpleType["basename"] = "list"

        # Check that derivation is allowed
        if "final" in itemtypeinfos:
            if "#all" in itemtypeinfos["final"]:
                raise ValueError("Item type can't be derivated!")
            if "list" in itemtypeinfos["final"]:
                raise ValueError("Item type can't be derivated by list!")

        # Generate extract value for new created type
        def ExtractSimpleTypeValue(attr, extract=True):
            values = []
            for value in GetToken(attr, extract).split(" "):
                values.append(itemtypeinfos["extract"](value, False))
            return values

        def CheckSimpleTypeValue(value):
            for item in value:
                result = itemtypeinfos["check"](item)
                if not result:
                    return result
            return True

        def SimpleTypeInitialValue():
            return []

        GenerateSimpleType = GenerateSimpleTypeXMLText(lambda x: " ".join(map(itemtypeinfos["generate"], x)))

        facets = GenerateDictFacets(["length", "maxLength", "minLength", "enumeration", "pattern"])
        facets["whiteSpace"] = ("collapse", False)

    elif typeinfos["type"] == "union":
        # Search for member types definition
        membertypesinfos = []
        for membertype in typeinfos["memberTypes"]:
            if isinstance(membertype, string_types):
                infos = factory.FindSchemaElement(membertype, SIMPLETYPE)
                if infos is None:
                    raise ValueError("\"%s\" isn't defined!" % membertype)
            else:
                infos = membertype

            # Check that member type is a simple type
            if infos["type"] != SIMPLETYPE:
                raise ValueError("Member type given isn't a simpleType!")

            # Check that derivation is allowed
            if "final" in infos:
                if "#all" in infos["final"]:
                    raise ValueError("Item type can't be derivated!")
                if "union" in infos["final"]:
                    raise ValueError("Member type can't be derivated by union!")

            membertypesinfos.append(infos)

        simpleType["basename"] = "union"

        # Generate extract value for new created type
        def ExtractSimpleTypeValue(attr, extract=True):
            for infos in membertypesinfos:
                try:
                    return infos["extract"](attr, False)
                except Exception:
                    pass
            raise ValueError("\"%s\" isn't valid for type defined for union!")

        def CheckSimpleTypeValue(value):
            for infos in membertypesinfos:
                result = infos["check"](value)
                if result:
                    return result
            return False

        SimpleTypeInitialValue = membertypesinfos[0]["initial"]

        def GenerateSimpleTypeFunction(value):
            if isinstance(value, bool):
                return {True: "true", False: "false"}[value]
            else:
                return str(value)
        GenerateSimpleType = GenerateSimpleTypeXMLText(GenerateSimpleTypeFunction)

        facets = GenerateDictFacets(["pattern", "enumeration"])

    simpleType["facets"] = facets
    simpleType["extract"] = ExtractSimpleTypeValue
    simpleType["initial"] = SimpleTypeInitialValue
    simpleType["check"] = CheckSimpleTypeValue
    simpleType["generate"] = GenerateSimpleType
    return simpleType


def ReduceSimpleType(factory, attributes, elements):
    # Reduce all the simple type children
    annotations, children = factory.ReduceElements(elements)

    simpleType = CreateSimpleType(factory, attributes, children[0])
    simpleType["doc"] = annotations

    return simpleType

# Complex type


def ExtractAttributes(factory, elements, base=None):
    attrs = []
    attrnames = {}
    if base is not None:
        basetypeinfos = factory.FindSchemaElement(base)
        if not isinstance(basetypeinfos, string_types) and basetypeinfos["type"] == COMPLEXTYPE:
            attrnames = dict(map(lambda x: (x["name"], True), basetypeinfos["attributes"]))

    for element in elements:
        if element["type"] == ATTRIBUTE:
            if attrnames.get(element["name"], False):
                raise ValueError("\"%s\" attribute has been defined two times!" % element["name"])
            else:
                attrnames[element["name"]] = True
                attrs.append(element)
        elif element["type"] == "attributeGroup":
            attrgroup = factory.FindSchemaElement(element["ref"], ATTRIBUTESGROUP)
            for attr in attrgroup["attributes"]:
                if attrnames.get(attr["name"], False):
                    raise ValueError("\"%s\" attribute has been defined two times!" % attr["name"])
                else:
                    attrnames[attr["name"]] = True
                    attrs.append(attr)
        elif element["type"] == "anyAttribute":
            raise ValueError("\"anyAttribute\" element isn't supported yet!")
    return attrs


def ReduceRestriction(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)
    restriction = {"type": "restriction", "base": attributes.get("base", None), "facets": [], "doc": annotations}
    if len(children) > 0 and children[0]["type"] == SIMPLETYPE:
        if restriction["base"] is None:
            restriction["base"] = children.pop(0)
        else:
            raise ValueError("Only one base type can be defined for restriction!")
    if restriction["base"] is None:
        raise ValueError("No base type has been defined for restriction!")

    while len(children) > 0 and children[0]["type"] in ALL_FACETS:
        restriction["facets"].append(children.pop(0))
    restriction["attributes"] = ExtractAttributes(factory, children, restriction["base"])
    return restriction


def ReduceExtension(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)
    if "base" not in attributes:
        raise ValueError("No base type has been defined for extension!")
    extension = {"type": "extension", "attributes": [], "elements": [], "base": attributes["base"], "doc": annotations}
    if len(children) > 0:
        if children[0]["type"] in ["group", "all", CHOICE, "sequence"]:
            group = children.pop(0)
            if group["type"] in ["all", "sequence"]:
                extension["elements"] = group["elements"]
                extension["order"] = group["order"]
            elif group["type"] == CHOICE:
                content = group.copy()
                content["name"] = "content"
                extension["elements"].append(content)
            elif group["type"] == "group":
                elmtgroup = factory.FindSchemaElement(group["ref"], ELEMENTSGROUP)
                if "elements" in elmtgroup:
                    extension["elements"] = elmtgroup["elements"]
                    extension["order"] = elmtgroup["order"]
                else:
                    content = elmtgroup.copy()
                    content["name"] = "content"
                    extension["elements"].append(content)
        extension["attributes"] = ExtractAttributes(factory, children)
    return extension


def ReduceSimpleContent(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    simpleContent = children[0].copy()

    basetypeinfos = factory.FindSchemaElement(simpleContent["base"])
    if basetypeinfos["type"] == SIMPLETYPE:
        contenttypeinfos = simpleContent.copy()
        simpleContent.pop("base")
    elif (basetypeinfos["type"] == COMPLEXTYPE and
          len(basetypeinfos["elements"]) == 1 and
          basetypeinfos["elements"][0]["name"] == "content" and
          "elmt_type" in basetypeinfos["elements"][0] and
          basetypeinfos["elements"][0]["elmt_type"]["type"] == SIMPLETYPE):
        contenttypeinfos = simpleContent.copy()
        contenttypeinfos["base"] = basetypeinfos["elements"][0]["elmt_type"]
    else:
        raise ValueError("No compatible base type defined for simpleContent!")
    contenttypeinfos = CreateSimpleType(factory, attributes, contenttypeinfos)

    simpleContent["elements"] = [{"name": "content", "type": ELEMENT,
                                  "elmt_type": contenttypeinfos, "doc": annotations,
                                  "minOccurs": 1, "maxOccurs": 1}]
    simpleContent["type"] = "simpleContent"
    return simpleContent


def ReduceComplexContent(factory, attributes, elements):
    _annotations, children = factory.ReduceElements(elements)
    complexContent = children[0].copy()
    complexContent["type"] = "complexContent"
    return complexContent


def ReduceComplexType(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    if len(children) > 0:
        if children[0]["type"] in ["simpleContent", "complexContent"]:
            complexType = children[0].copy()
            complexType.update(attributes)
            complexType["type"] = COMPLEXTYPE
            return complexType
        elif children[0]["type"] in ["group", "all", CHOICE, "sequence"]:
            complexType = {"type": COMPLEXTYPE, "elements": [], "order": True, "doc": annotations}
            complexType.update(attributes)
            group = children.pop(0)
            if group["type"] in ["all", "sequence"]:
                choice_number = 0
                for element in group["elements"]:
                    if element["type"] == CHOICE:
                        choice_number += 1
                if (group["minOccurs"] == 0 or group["maxOccurs"] != 1) and len(group["elements"]) > 1 or choice_number > 1:
                    content = {"type": CHOICE, "name": "content", "choices": [group], "minOccurs": 1, "maxOccurs": 1}
                    complexType["elements"].append(content)
                else:
                    if len(group["elements"]) == 1:
                        if group["minOccurs"] == 0:
                            group["elements"][0]["minOccurs"] = group["minOccurs"]
                        if group["maxOccurs"] != 1:
                            group["elements"][0]["maxOccurs"] = group["maxOccurs"]
                    for element in group["elements"]:
                        if element["type"] == CHOICE:
                            element["name"] = "content"
                    complexType["elements"] = group["elements"]
                    complexType["order"] = group["order"]
            elif group["type"] == CHOICE:
                content = group.copy()
                content["name"] = "content"
                complexType["elements"].append(content)
            elif group["type"] == "group":
                elmtgroup = factory.FindSchemaElement(group["ref"], ELEMENTSGROUP)
                if "elements" in elmtgroup:
                    complexType["elements"] = elmtgroup["elements"]
                    complexType["order"] = elmtgroup["order"]
                else:
                    content = elmtgroup.copy()
                    content["name"] = "content"
                    complexType["elements"].append(content)
        else:
            complexType = {"elements": [], "order": True, "doc": annotations}
            complexType.update(attributes)
            complexType["type"] = COMPLEXTYPE
        complexType["attributes"] = ExtractAttributes(factory, children)
        return complexType
    else:
        raise ValueError("\"ComplexType\" can't be empty!")


# Attribute elements

def ReduceAnyAttribute(factory, attributes, elements):
    return {"type": "anyAttribute"}


def ReduceAttribute(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    if "default" in attributes:
        if "fixed" in attributes:
            raise ValueError("\"default\" and \"fixed\" can't be defined at the same time!")
        elif attributes.get("use", "optional") != "optional":
            raise ValueError("if \"default\" present, \"use\" can only have the value \"optional\"!")

    attribute = {"type": ATTRIBUTE, "attr_type": attributes.get("type", None), "doc": annotations}
    if len(children) > 0:
        if attribute["attr_type"] is None:
            attribute["attr_type"] = children[0]
        else:
            raise ValueError("Only one type can be defined for attribute!")

    if "ref" in attributes:
        if "name" in attributes:
            raise ValueError("\"ref\" and \"name\" can't be defined at the same time!")
        elif "form" in attributes:
            raise ValueError("\"ref\" and \"form\" can't be defined at the same time!")
        elif attribute["attr_type"] is not None:
            raise ValueError("if \"ref\" is present, no type can be defined!")
    elif attribute["attr_type"] is None:
        raise ValueError("No type has been defined for attribute \"%s\"!" % attributes["name"])

    if "type" in attributes:
        tmp_attrs = attributes.copy()
        tmp_attrs.pop("type")
        attribute.update(tmp_attrs)
    else:
        attribute.update(attributes)
    return attribute


def ReduceAttributeGroup(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)
    if "ref" in attributes:
        return {"type": "attributeGroup", "ref": attributes["ref"], "doc": annotations}
    else:
        return {"type": ATTRIBUTESGROUP, "attributes": ExtractAttributes(factory, children), "doc": annotations}


# Elements groups

def ReduceAny(factory, attributes, elements):
    annotations, _children = factory.ReduceElements(elements)

    any = {"type": ANY, "doc": annotations}
    any.update(attributes)
    return any


def ReduceElement(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    types = []
    constraints = []
    for child in children:
        if child["type"] == CONSTRAINT:
            constraints.append(child)
        else:
            types.append(child)

    if "default" in attributes and "fixed" in attributes:
        raise ValueError("\"default\" and \"fixed\" can't be defined at the same time!")

    if "ref" in attributes:
        for attr in ["name", "default", "fixed", "form", "block", "type"]:
            if attr in attributes:
                raise ValueError("\"ref\" and \"%s\" can't be defined at the same time!" % attr)
        if "nillable" in attributes:
            raise ValueError("\"ref\" and \"nillable\" can't be defined at the same time!")
        if len(types) > 0:
            raise ValueError("No type and no constraints can be defined where \"ref\" is defined!")

        infos = factory.FindSchemaElement(attributes["ref"], ELEMENT)
        if infos is not None:
            element = infos.copy()
            element["constraints"] = constraints
            element["minOccurs"] = attributes["minOccurs"]
            element["maxOccurs"] = attributes["maxOccurs"]
            return element
        else:
            raise ValueError("\"%s\" base type isn't defined or circular referenced!" % attributes["ref"])

    elif "name" in attributes:
        element = {"type": ELEMENT, "elmt_type": attributes.get("type", None), "constraints": constraints, "doc": annotations}
        if len(types) > 0:
            if element["elmt_type"] is None:
                element["elmt_type"] = types[0]
            else:
                raise ValueError("Only one type can be defined for attribute!")
        elif element["elmt_type"] is None:
            element["elmt_type"] = "tag"
            element["type"] = TAG

        if "type" in attributes:
            tmp_attrs = attributes.copy()
            tmp_attrs.pop("type")
            element.update(tmp_attrs)
        else:
            element.update(attributes)
        return element
    else:
        raise ValueError("\"Element\" must have at least a \"ref\" or a \"name\" defined!")


def ReduceAll(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    for child in children:
        if child["maxOccurs"] == "unbounded" or child["maxOccurs"] > 1:
            raise ValueError("\"all\" item can't have \"maxOccurs\" attribute greater than 1!")

    return {"type": "all", "elements": children, "minOccurs": attributes["minOccurs"],
            "maxOccurs": attributes["maxOccurs"], "order": False, "doc": annotations}


def ReduceChoice(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    choices = []
    for child in children:
        if child["type"] in [ELEMENT, ANY, TAG]:
            choices.append(child)
        elif child["type"] == "sequence":
            child["minOccurs"] = child["maxOccurs"] = 1
            choices.append(child)
            # raise ValueError("\"sequence\" in \"choice\" is not supported. Create instead a new complex type!")
        elif child["type"] == CHOICE:
            choices.extend(child["choices"])
        elif child["type"] == "group":
            elmtgroup = factory.FindSchemaElement(child["ref"], ELEMENTSGROUP)
            if "choices" not in elmtgroup:
                raise ValueError("Only group composed of \"choice\" can be referenced in \"choice\" element!")
            choices_tmp = []
            for choice in elmtgroup["choices"]:
                if not isinstance(choice["elmt_type"], string_types) and choice["elmt_type"]["type"] == COMPLEXTYPE:
                    elmt_type = "%s_%s" % (elmtgroup["name"], choice["name"])
                    if factory.TargetNamespace is not None:
                        elmt_type = "%s:%s" % (factory.TargetNamespace, elmt_type)
                    new_choice = choice.copy()
                    new_choice["elmt_type"] = elmt_type
                    choices_tmp.append(new_choice)
                else:
                    choices_tmp.append(choice)
            choices.extend(choices_tmp)

    for choice in choices:
        attributes["minOccurs"] = min(attributes["minOccurs"], choice["minOccurs"])
        choice["minOccurs"] = 1

    return {"type": CHOICE, "choices": choices, "minOccurs": attributes["minOccurs"],
            "maxOccurs": attributes["maxOccurs"], "doc": annotations}


def ReduceSequence(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    sequence = []
    for child in children:
        if child["type"] in [ELEMENT, ANY, TAG, CHOICE]:
            sequence.append(child)
        elif child["type"] == "sequence":
            sequence.extend(child["elements"])
        elif child["type"] == "group":
            elmtgroup = factory.FindSchemaElement(child["ref"], ELEMENTSGROUP)
            if "elements" not in elmtgroup or not elmtgroup["order"]:
                raise ValueError("Only group composed of \"sequence\" can be referenced in \"sequence\" element!")
            elements_tmp = []
            for element in elmtgroup["elements"]:
                if not isinstance(element["elmt_type"], string_types) and element["elmt_type"]["type"] == COMPLEXTYPE:
                    elmt_type = "%s_%s" % (elmtgroup["name"], element["name"])
                    if factory.TargetNamespace is not None:
                        elmt_type = "%s:%s" % (factory.TargetNamespace, elmt_type)
                    new_element = element.copy()
                    new_element["elmt_type"] = elmt_type
                    elements_tmp.append(new_element)
                else:
                    elements_tmp.append(element)
            sequence.extend(elements_tmp)

    return {"type": "sequence", "elements": sequence, "minOccurs": attributes["minOccurs"],
            "maxOccurs": attributes["maxOccurs"], "order": True, "doc": annotations}


def ReduceGroup(factory, attributes, elements):
    annotations, children = factory.ReduceElements(elements)

    if "ref" in attributes:
        return {"type": "group", "ref": attributes["ref"], "doc": annotations}
    else:
        element = children[0]
        group = {"type": ELEMENTSGROUP, "doc": annotations}
        if element["type"] == CHOICE:
            group["choices"] = element["choices"]
        else:
            group.update({"elements": element["elements"], "order": element["order"]})
        group.update(attributes)
        return group

# Constraint elements


def ReduceUnique(factory, attributes, elements):
    _annotations, children = factory.ReduceElements(elements)

    unique = {"type": CONSTRAINT, "const_type": "unique", "selector": children[0], "fields": children[1:]}
    unique.update(attributes)
    return unique


def ReduceKey(factory, attributes, elements):
    _annotations, children = factory.ReduceElements(elements)

    key = {"type": CONSTRAINT, "const_type": "key", "selector": children[0], "fields": children[1:]}
    key.update(attributes)
    return key


def ReduceKeyRef(factory, attributes, elements):
    _annotations, children = factory.ReduceElements(elements)

    keyref = {"type": CONSTRAINT, "const_type": "keyref", "selector": children[0], "fields": children[1:]}
    keyref.update(attributes)
    return keyref


def ReduceSelector(factory, attributes, elements):
    factory.ReduceElements(elements)

    selector = {"type": CONSTRAINT, "const_type": "selector"}
    selector.update(attributes)
    return selector


def ReduceField(factory, attributes, elements):
    factory.ReduceElements(elements)

    field = {"type": CONSTRAINT, "const_type": "field"}
    field.update(attributes)
    return field


# Inclusion elements

def ReduceImport(factory, attributes, elements):
    factory.ReduceElements(elements)
    raise ValueError("\"import\" element isn't supported yet!")


def ReduceInclude(factory, attributes, elements):
    factory.ReduceElements(elements)

    if factory.FileName is None:
        raise ValueError("Include in XSD string not yet supported")
    filepath = attributes["schemaLocation"]
    if filepath is not None and not os.path.exists(filepath):
        filepath = os.path.join(factory.BaseFolder, filepath)
        if not os.path.exists(filepath):
            raise ValueError("No file '%s' found for include" % attributes["schemaLocation"])
    xsdfile = open(filepath, 'r')
    include_factory = XSDClassFactory(minidom.parse(xsdfile), filepath)
    xsdfile.close()
    include_factory.CreateClasses()

    if factory.TargetNamespace == include_factory.TargetNamespace:
        factory.Namespaces[factory.TargetNamespace].update(include_factory.Namespaces[include_factory.TargetNamespace])
    else:
        factory.Namespaces[include_factory.TargetNamespace] = include_factory.Namespaces[include_factory.TargetNamespace]
    factory.ComputedClasses.update(include_factory.ComputedClasses)
    factory.ComputedClassesLookUp.update(include_factory.ComputedClassesLookUp)
    factory.EquivalentClassesParent.update(include_factory.EquivalentClassesParent)
    return None


def ReduceRedefine(factory, attributes, elements):
    factory.ReduceElements(elements)
    raise ValueError("\"redefine\" element isn't supported yet!")


# Schema element

def ReduceSchema(factory, attributes, elements):
    factory.AttributeFormDefault = attributes["attributeFormDefault"]
    factory.ElementFormDefault = attributes["elementFormDefault"]
    factory.BlockDefault = attributes["blockDefault"]
    factory.FinalDefault = attributes["finalDefault"]

    targetNamespace = attributes.get("targetNamespace", None)
    factory.TargetNamespace = factory.DefinedNamespaces.get(targetNamespace, None)
    if factory.TargetNamespace is not None:
        factory.etreeNamespaceFormat = "{%s}%%s" % targetNamespace
    factory.Namespaces[factory.TargetNamespace] = {}

    _annotations, children = factory.ReduceElements(elements, True)

    for child in children:
        if "name" in child:
            infos = factory.GetQualifiedNameInfos(child["name"], factory.TargetNamespace, True)
            if infos is None:
                factory.Namespaces[factory.TargetNamespace][child["name"]] = child
            elif not CompareSchema(infos, child):
                raise ValueError("\"%s\" is defined twice in targetNamespace!" % child["name"])


def CompareSchema(schema, reference):
    if isinstance(schema, list):
        if not isinstance(reference, list) or len(schema) != len(reference):
            return False
        for i, value in enumerate(schema):
            result = CompareSchema(value, reference[i])
            if not result:
                return result
        return True
    elif isinstance(schema, dict):
        if not isinstance(reference, dict) or len(schema) != len(reference):
            return False
        for name, value in schema.items():
            ref_value = reference.get(name, None)
            if ref_value is None and value is not None:
                return False
            result = CompareSchema(value, ref_value)
            if not result:
                return result
        return True
    elif isinstance(schema, FunctionType):
        if not isinstance(reference, FunctionType) or schema.__name__ != reference.__name__:
            return False
        else:
            return True
    return schema == reference


# -------------------------------------------------------------------------------
#                       Base class for XSD schema extraction
# -------------------------------------------------------------------------------


class XSDClassFactory(ClassFactory):

    def __init__(self, document, filepath=None, debug=False):
        ClassFactory.__init__(self, document, filepath, debug)
        self.Namespaces["xml"] = {
            "lang": {
                "type": SYNTAXATTRIBUTE,
                "extract": {
                    "default": GenerateModelNameExtraction("lang", LANGUAGE_model)
                }
            }
        }
        self.Namespaces["xsi"] = {
            "noNamespaceSchemaLocation": {
                "type": SYNTAXATTRIBUTE,
                "extract": {
                    "default": NotSupportedYet("noNamespaceSchemaLocation")
                }
            },
            "nil": {
                "type": SYNTAXATTRIBUTE,
                "extract": {
                    "default": NotSupportedYet("nil")
                }
            },
            "schemaLocation": {
                "type": SYNTAXATTRIBUTE,
                "extract": {
                    "default": NotSupportedYet("schemaLocation")
                }
            },
            "type": {
                "type": SYNTAXATTRIBUTE,
                "extract": {
                    "default": NotSupportedYet("type")
                }
            }
        }

    def ParseSchema(self):
        for child in self.Document.childNodes:
            if child.nodeType == self.Document.ELEMENT_NODE:
                schema = child
                break
        for qualified_name, attr in schema._attrs.items():
            namespace, name = DecomposeQualifiedName(qualified_name)
            if namespace == "xmlns":
                value = GetAttributeValue(attr)
                self.DefinedNamespaces[value] = name
                self.NSMAP[name] = value
                if value == "http://www.w3.org/2001/XMLSchema":
                    self.SchemaNamespace = name
                    self.Namespaces[self.SchemaNamespace] = XSD_NAMESPACE
        self.Schema = XSD_NAMESPACE["schema"]["extract"]["default"](self, schema)
        ReduceSchema(self, self.Schema[1], self.Schema[2])

    def FindSchemaElement(self, element_name, element_type=None):
        namespace, name = DecomposeQualifiedName(element_name)
        element = self.GetQualifiedNameInfos(name, namespace, True)
        if element is None and namespace == self.TargetNamespace and name not in self.CurrentCompilations:
            self.CurrentCompilations.append(name)
            element = self.CreateSchemaElement(name, element_type)
            self.CurrentCompilations.pop(-1)
            if element is not None:
                self.Namespaces[self.TargetNamespace][name] = element
        if element is None:
            if name in self.CurrentCompilations:
                if self.Debug:
                    print("Warning : \"%s\" is circular referenced!" % element_name)
            else:
                raise ValueError("\"%s\" isn't defined!" % element_name)
        if element_type is not None and element["type"] != element_type:
            raise ValueError("\"%s\" isn't of the expected type!" % element_name)
        return element

    def CreateSchemaElement(self, element_name, element_type):
        for type, attributes, elements in self.Schema[2]:
            _namespace, name = DecomposeQualifiedName(type)
            if attributes.get("name", None) == element_name:
                element_infos = None
                if element_type in (ATTRIBUTE, None) and name == "attribute":
                    element_infos = ReduceAttribute(self, attributes, elements)
                elif element_type in (ELEMENT, None) and name == "element":
                    element_infos = ReduceElement(self, attributes, elements)
                elif element_type in (ATTRIBUTESGROUP, None) and name == "attributeGroup":
                    element_infos = ReduceAttributeGroup(self, attributes, elements)
                elif element_type in (ELEMENTSGROUP, None) and name == "group":
                    element_infos = ReduceGroup(self, attributes, elements)
                elif element_type in (SIMPLETYPE, None) and name == "simpleType":
                    element_infos = ReduceSimpleType(self, attributes, elements)
                elif element_type in (COMPLEXTYPE, None) and name == "complexType":
                    element_infos = ReduceComplexType(self, attributes, elements)
                if element_infos is not None:
                    self.Namespaces[self.TargetNamespace][element_name] = element_infos
                    return element_infos
        return None


def GenerateParserFromXSD(filepath):
    """
    This function opens the xsd file and generate a xml parser with class lookup from
    the xml tree
    """
    xsdfile = open(filepath, 'r')
    xsdstring = xsdfile.read()
    xsdfile.close()
    cwd = os.getcwd()
    os.chdir(os.path.dirname(filepath))
    parser = GenerateParser(XSDClassFactory(minidom.parseString(xsdstring), filepath), xsdstring)
    os.chdir(cwd)
    return parser


def GenerateParserFromXSDstring(xsdstring):
    """
    This function generate a xml from the xsd given as a string
    """
    return GenerateParser(XSDClassFactory(minidom.parseString(xsdstring)), xsdstring)


# -------------------------------------------------------------------------------
#                           XSD schema syntax elements
# -------------------------------------------------------------------------------


XSD_NAMESPACE = {

    # -------------------------------------------------------------------------------
    #                           Syntax elements definition
    # -------------------------------------------------------------------------------

    "all": {
        "struct": """
        <all
          id = ID
          maxOccurs = 1 : 1
          minOccurs = (0 | 1) : 1
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, element*)
        </all>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "all", ["id", "maxOccurs", "minOccurs"],
                re.compile("((?:annotation )?(?:element )*)"))
        },
        "reduce": ReduceAll
    },

    "annotation": {
        "struct": """
        <annotation
          id = ID
          {any attributes with non-schema namespace . . .}>
          Content: (appinfo | documentation)*
        </annotation>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "annotation", ["id"],
                re.compile("((?:app_info |documentation )*)"))
        },
        "reduce": ReduceAnnotation
    },

    "any": {
        "struct": """
        <any
          id = ID
          maxOccurs = (nonNegativeInteger | unbounded)  : 1
          minOccurs = nonNegativeInteger : 1
          namespace = ((##any | ##other) | List of (anyURI | (##targetNamespace | ##local)) )  : ##any
          processContents = (lax | skip | strict) : strict
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </any>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "any",
                ["id", "maxOccurs", "minOccurs", "namespace", "processContents"],
                re.compile("((?:annotation )?(?:simpleType )*)"))
        },
        "reduce": ReduceAny
    },

    "anyAttribute": {
        "struct": """
        <anyAttribute
          id = ID
          namespace = ((##any | ##other) | List of (anyURI | (##targetNamespace | ##local)) )  : ##any
          processContents = (lax | skip | strict) : strict
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </anyAttribute>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "anyAttribute", ["id", "namespace", "processContents"], ONLY_ANNOTATION)
        },
        "reduce": ReduceAnyAttribute
    },

    "appinfo": {
        "struct": """
        <appinfo
          source = anyURI
          {any attributes with non-schema namespace . . .}>
          Content: ({any})*
        </appinfo>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement("appinfo", ["source"], re.compile("(.*)"), True)
        },
        "reduce": ReduceAppInfo
    },

    "attribute": {
        "struct": """
        <attribute
          default = string
          fixed = string
          form = (qualified | unqualified)
          id = ID
          name = NCName
          ref = QName
          type = QName
          use = (optional | prohibited | required) : optional
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, simpleType?)
        </attribute>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "attribute",
                ["default", "fixed", "form", "id", "name", "ref", "type", "use"],
                re.compile("((?:annotation )?(?:simpleType )?)")),
            "schema": GenerateElement(
                "attribute",
                ["default", "fixed", "form", "id", "name", "type"],
                re.compile("((?:annotation )?(?:simpleType )?)"))
        },
        "reduce": ReduceAttribute
    },

    "attributeGroup": {
        "struct": """
        <attributeGroup
          id = ID
          name = NCName
          ref = QName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, ((attribute | attributeGroup)*, anyAttribute?))
        </attributeGroup>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "attributeGroup",
                ["id", "ref"], ONLY_ANNOTATION),
            "schema": GenerateElement(
                "attributeGroup",
                ["id", "name"],
                re.compile("((?:annotation )?(?:(?:attribute |attributeGroup )*(?:anyAttribute )?))"))
        },
        "reduce": ReduceAttributeGroup
    },

    "choice": {
        "struct": """
        <choice
          id = ID
          maxOccurs = (nonNegativeInteger | unbounded)  : 1
          minOccurs = nonNegativeInteger : 1
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (element | group | choice | sequence | any)*)
        </choice>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "choice",
                ["id", "maxOccurs", "minOccurs"],
                re.compile("((?:annotation )?(?:element |group |choice |sequence |any )*)"))
        },
        "reduce": ReduceChoice
    },

    "complexContent": {
        "struct": """
        <complexContent
          id = ID
          mixed = boolean
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (restriction | extension))
        </complexContent>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "complexContent",
                ["id", "mixed"],
                re.compile("((?:annotation )?(?:restriction |extension ))"))
        },
        "reduce": ReduceComplexContent
    },

    "complexType": {
        "struct": """
        <complexType
          abstract = boolean : false
          block = (#all | List of (extension | restriction))
          final = (#all | List of (extension | restriction))
          id = ID
          mixed = boolean : false
          name = NCName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (simpleContent | complexContent | ((group | all | choice | sequence)?, ((attribute | attributeGroup)*, anyAttribute?))))
        </complexType>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "complexType",
                ["abstract", "block", "final", "id", "mixed", "name"],
                re.compile("((?:annotation )?(?:simpleContent |complexContent |(?:(?:group |all |choice |sequence )?(?:(?:attribute |attributeGroup )*(?:anyAttribute )?))))"))
        },
        "reduce": ReduceComplexType
    },

    "documentation": {
        "struct": """
        <documentation
          source = anyURI
          xml:lang = language
          {any attributes with non-schema namespace . . .}>
          Content: ({any})*
        </documentation>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "documentation",
                ["source", "lang"],
                re.compile("(.*)"), True)
        },
        "reduce": ReduceDocumentation
    },

    "element": {
        "struct": """
        <element
          abstract = boolean : false
          block = (#all | List of (extension | restriction | substitution))
          default = string
          final = (#all | List of (extension | restriction))
          fixed = string
          form = (qualified | unqualified)
          id = ID
          maxOccurs = (nonNegativeInteger | unbounded)  : 1
          minOccurs = nonNegativeInteger : 1
          name = NCName
          nillable = boolean : false
          ref = QName
          substitutionGroup = QName
          type = QName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, ((simpleType | complexType)?, (unique | key | keyref)*))
        </element>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "element",
                ["abstract", "block", "default", "final", "fixed", "form", "id", "maxOccurs", "minOccurs", "name", "nillable", "ref", "substitutionGroup", "type"],
                re.compile("((?:annotation )?(?:simpleType |complexType )?(?:unique |key |keyref )*)")),
            "schema": GenerateElement(
                "element",
                ["abstract", "block", "default", "final", "fixed", "form", "id", "name", "nillable", "substitutionGroup", "type"],
                re.compile("((?:annotation )?(?:simpleType |complexType )?(?:unique |key |keyref )*)"))
        },
        "reduce": ReduceElement
    },

    "enumeration": {
        "struct": """
        <enumeration
          id = ID
          value = anySimpleType
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </enumeration>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement("enumeration", ["id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("enumeration", False)
    },

    "extension": {
        "struct": """
        <extension
          base = QName
          id = ID
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, ((group | all | choice | sequence)?, ((attribute | attributeGroup)*, anyAttribute?)))
        </extension>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "extension",
                ["base", "id"],
                re.compile("((?:annotation )?(?:(?:attribute |attributeGroup )*(?:anyAttribute )?))")),
            "complexContent": GenerateElement(
                "extension",
                ["base", "id"],
                re.compile("((?:annotation )?(?:group |all |choice |sequence )?(?:(?:attribute |attributeGroup )*(?:anyAttribute )?))"))
        },
        "reduce": ReduceExtension
    },

    "field": {
        "struct": """
        <field
          id = ID
          xpath = a subset of XPath expression, see below
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </field>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement("field", ["id", "xpath"], ONLY_ANNOTATION)
        },
        "reduce": ReduceField
    },

    "fractionDigits": {
        "struct": """
        <fractionDigits
          fixed = boolean : false
          id = ID
          value = nonNegativeInteger
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </fractionDigits>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "fractionDigits",
                ["fixed", "id", "value"],
                ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("fractionDigits", True)
    },

    "group": {
        "struct": """
        <group
          id = ID
          maxOccurs = (nonNegativeInteger | unbounded)  : 1
          minOccurs = nonNegativeInteger : 1
          name = NCName
          ref = QName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (all | choice | sequence)?)
        </group>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "group",
                ["id", "maxOccurs", "minOccurs", "ref"],
                re.compile("((?:annotation )?(?:all |choice |sequence )?)")),
            "schema": GenerateElement(
                "group",
                ["id", "name"],
                re.compile("((?:annotation )?(?:all |choice |sequence )?)"))
        },
        "reduce": ReduceGroup
    },

    "import": {
        "struct": """
        <import
          id = ID
          namespace = anyURI
          schemaLocation = anyURI
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </import>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "import",
                ["id", "namespace", "schemaLocation"],
                ONLY_ANNOTATION)
        },
        "reduce": ReduceImport
    },

    "include": {
        "struct": """
        <include
          id = ID
          schemaLocation = anyURI
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </include>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "include",
                ["id", "schemaLocation"],
                ONLY_ANNOTATION)
        },
        "reduce": ReduceInclude
    },

    "key": {
        "struct": """
        <key
          id = ID
          name = NCName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (selector, field+))
        </key>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "key", ["id", "name"],
                re.compile("((?:annotation )?(?:selector (?:field )+))"))
        },
        "reduce": ReduceKey
    },

    "keyref": {
        "struct": """
        <keyref
          id = ID
          name = NCName
          refer = QName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (selector, field+))
        </keyref>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "keyref", ["id", "name", "refer"],
                re.compile("((?:annotation )?(?:selector (?:field )+))"))
        },
        "reduce": ReduceKeyRef
    },

    "length": {
        "struct": """
        <length
          fixed = boolean : false
          id = ID
          value = nonNegativeInteger
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </length>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "length", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("length", True)
    },

    "list": {
        "struct": """
        <list
          id = ID
          itemType = QName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, simpleType?)
        </list>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "list", ["id", "itemType"],
                re.compile("((?:annotation )?(?:simpleType )?)$"))
        },
        "reduce": ReduceList
    },

    "maxExclusive": {
        "struct": """
        <maxInclusive
          fixed = boolean : false
          id = ID
          value = anySimpleType
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </maxInclusive>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "maxExclusive", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("maxExclusive", True)
    },

    "maxInclusive": {
        "struct": """
        <maxExclusive
          fixed = boolean : false
          id = ID
          value = anySimpleType
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </maxExclusive>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "maxInclusive", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("maxInclusive", True)
    },

    "maxLength": {
        "struct": """
        <maxLength
          fixed = boolean : false
          id = ID
          value = nonNegativeInteger
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </maxLength>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "maxLength", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("maxLength", True)
    },

    "minExclusive": {
        "struct": """
        <minExclusive
          fixed = boolean : false
          id = ID
          value = anySimpleType
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </minExclusive>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "minExclusive", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("minExclusive", True)
    },

    "minInclusive": {
        "struct": """
        <minInclusive
          fixed = boolean : false
          id = ID
          value = anySimpleType
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </minInclusive>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "minInclusive", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("minInclusive", True)
    },

    "minLength": {
        "struct": """
        <minLength
          fixed = boolean : false
          id = ID
          value = nonNegativeInteger
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </minLength>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "minLength", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("minLength", True)
    },

    "pattern": {
        "struct": """
        <pattern
          id = ID
          value = string
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </pattern>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement("pattern", ["id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("pattern", False)
    },

    "redefine": {
        "struct": """
        <redefine
          id = ID
          schemaLocation = anyURI
          {any attributes with non-schema namespace . . .}>
          Content: (annotation | (simpleType | complexType | group | attributeGroup))*
        </redefine>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "refine", ["id", "schemaLocation"],
                re.compile("((?:annotation |(?:simpleType |complexType |group |attributeGroup ))*)"))
        },
        "reduce": ReduceRedefine
    },

    "restriction": {
        "struct": """
        <restriction
          base = QName
          id = ID
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (group | all | choice | sequence)?, ((attribute | attributeGroup)*, anyAttribute?))
        </restriction>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "restriction",
                ["base", "id"],
                re.compile("((?:annotation )?(?:(?:simpleType )?(?:(?:minExclusive |minInclusive |maxExclusive |maxInclusive |totalDigits |fractionDigits |length |minLength |maxLength |enumeration |whiteSpace |pattern )*)))")),
            "simpleContent": GenerateElement(
                "restriction",
                ["base", "id"],
                re.compile("((?:annotation )?(?:(?:simpleType )?(?:(?:minExclusive |minInclusive |maxExclusive |maxInclusive |totalDigits |fractionDigits |length |minLength |maxLength |enumeration |whiteSpace |pattern )*)?(?:(?:attribute |attributeGroup )*(?:anyAttribute )?)))")),
            "complexContent": GenerateElement(
                "restriction",
                ["base", "id"],
                re.compile("((?:annotation )?(?:(?:simpleType )?(?:group |all |choice |sequence )?(?:(?:attribute |attributeGroup )*(?:anyAttribute )?)))")),
        },
        "reduce": ReduceRestriction
    },

    "schema": {
        "struct": """
        <schema
          attributeFormDefault = (qualified | unqualified) : unqualified
          blockDefault = (#all | List of (extension | restriction | substitution))  : ''
          elementFormDefault = (qualified | unqualified) : unqualified
          finalDefault = (#all | List of (extension | restriction | list | union))  : ''
          id = ID
          targetNamespace = anyURI
          version = token
          xml:lang = language
          {any attributes with non-schema namespace . . .}>
          Content: ((include | import | redefine | annotation)*, (((simpleType | complexType | group | attributeGroup) | element | attribute | notation), annotation*)*)
        </schema>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "schema",
                ["attributeFormDefault",
                 "blockDefault",
                 "elementFormDefault",
                 "finalDefault",
                 "id",
                 "targetNamespace",
                 "version",
                 "lang"],
                re.compile("((?:include |import |redefine |annotation )*(?:(?:(?:simpleType |complexType |group |attributeGroup )|element |attribute |annotation )(?:annotation )*)*)"))
        }
    },

    "selector": {
        "struct": """
        <selector
          id = ID
          xpath = a subset of XPath expression, see below
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </selector>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement("selector", ["id", "xpath"], ONLY_ANNOTATION)
        },
        "reduce": ReduceSelector
    },

    "sequence": {
        "struct": """
        <sequence
          id = ID
          maxOccurs = (nonNegativeInteger | unbounded)  : 1
          minOccurs = nonNegativeInteger : 1
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (element | group | choice | sequence | any)*)
        </sequence>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "sequence", ["id", "maxOccurs", "minOccurs"],
                re.compile("((?:annotation )?(?:element |group |choice |sequence |any )*)"))
        },
        "reduce": ReduceSequence
    },

    "simpleContent": {
        "struct": """
        <simpleContent
          id = ID
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (restriction | extension))
        </simpleContent>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "simpleContent", ["id"],
                re.compile("((?:annotation )?(?:restriction |extension ))"))
        },
        "reduce": ReduceSimpleContent
    },

    "simpleType": {
        "struct": """
        <simpleType
          final = (#all | List of (list | union | restriction))
          id = ID
          name = NCName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (restriction | list | union))
        </simpleType>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "simpleType", ["final", "id", "name"],
                re.compile("((?:annotation )?(?:restriction |list |union ))"))
        },
        "reduce": ReduceSimpleType
    },

    "totalDigits": {
        "struct": """
        <totalDigits
          fixed = boolean : false
          id = ID
          value = positiveInteger
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </totalDigits>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "totalDigits", ["fixed", "id", "value"], ONLY_ANNOTATION),
        },
        "reduce": GenerateFacetReducing("totalDigits", True)
    },

    "union": {
        "struct": """
        <union
          id = ID
          memberTypes = List of QName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, simpleType*)
        </union>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "union", ["id", "memberTypes"],
                re.compile("((?:annotation )?(?:simpleType )*)"))
        },
        "reduce": ReduceUnion
    },

    "unique": {
        "struct": """
        <unique
          id = ID
          name = NCName
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?, (selector, field+))
        </unique>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "unique", ["id", "name"],
                re.compile("((?:annotation )?(?:selector |(?:field )+))"))
        },
        "reduce": ReduceUnique
    },

    "whiteSpace": {
        "struct": """
        <whiteSpace
          fixed = boolean : false
          id = ID
          value = (collapse | preserve | replace)
          {any attributes with non-schema namespace . . .}>
          Content: (annotation?)
        </whiteSpace>""",
        "type": SYNTAXELEMENT,
        "extract": {
            "default": GenerateElement(
                "whiteSpace", ["fixed", "id", "value"], ONLY_ANNOTATION)
        },
        "reduce": GenerateFacetReducing("whiteSpace", True)
    },

    # -------------------------------------------------------------------------------
    #                       Syntax attributes definition
    # -------------------------------------------------------------------------------

    "abstract": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetBoolean
        },
        "default": {
            "default": False
        }
    },

    "attributeFormDefault": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateEnumeratedExtraction(
                "member attributeFormDefault", ["qualified", "unqualified"])
        },
        "default": {
            "default": "unqualified"
        }
    },

    "base": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member base", QName_model)
        }
    },

    "block": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateGetList("block", ["restriction", "extension", "substitution"])
        }
    },

    "blockDefault": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateGetList("block", ["restriction", "extension", "substitution"])
        },
        "default": {
            "default": ""
        }
    },

    "default": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetAttributeValue
        }
    },

    "elementFormDefault": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateEnumeratedExtraction("member elementFormDefault", ["qualified", "unqualified"])
        },
        "default": {
            "default": "unqualified"
        }
    },

    "final": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateGetList("final", ["restriction", "extension", "substitution"]),
            "simpleType": GenerateGetList("final", ["list", "union", "restriction"])
        }
    },

    "finalDefault": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateGetList("finalDefault", ["restriction", "extension", "list", "union"])
        },
        "default": {
            "default": ""
        }
    },

    "fixed": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetBoolean,
            "attribute": GetAttributeValue,
            "element": GetAttributeValue
        },
        "default": {
            "default": False,
            "attribute": None,
            "element": None
        }
    },

    "form": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateEnumeratedExtraction("member form", ["qualified", "unqualified"])
        }
    },

    "id": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member id", NCName_model)
        }
    },

    "itemType": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member itemType", QName_model)
        }
    },

    "memberTypes": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameListExtraction("member memberTypes", QNames_model)
        },
    },

    "maxOccurs": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateLimitExtraction(),
            "all": GenerateLimitExtraction(1, 1, False)
        },
        "default": {
            "default": 1
        }
    },

    "minOccurs": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateLimitExtraction(unbounded=False),
            "all": GenerateLimitExtraction(0, 1, False)
        },
        "default": {
            "default": 1
        }
    },

    "mixed": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetBoolean
        },
        "default": {
            "default": None,
            "complexType": False
        }
    },

    "name": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member name", NCName_model)
        }
    },

    "namespace": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member namespace", URI_model),
            "any": GetNamespaces
        },
        "default": {
            "default": None,
            "any": "##any"
        }
    },

    "nillable": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetBoolean
        },
    },

    "processContents": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateEnumeratedExtraction("member processContents", ["lax", "skip", "strict"])
        },
        "default": {
            "default": "strict"
        }
    },

    "ref": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member ref", QName_model)
        }
    },

    "refer": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member refer", QName_model)
        }
    },

    "schemaLocation": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member schemaLocation", URI_model)
        }
    },

    "source": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member source", URI_model)
        }
    },

    "substitutionGroup": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member substitutionGroup", QName_model)
        }
    },

    "targetNamespace": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member targetNamespace", URI_model)
        }
    },

    "type": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateModelNameExtraction("member type", QName_model)
        }
    },

    "use": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GenerateEnumeratedExtraction("member usage", ["required", "optional", "prohibited"])
        },
        "default": {
            "default": "optional"
        }
    },

    "value": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetAttributeValue,
            "fractionDigits": GenerateIntegerExtraction(minInclusive=0),
            "length": GenerateIntegerExtraction(minInclusive=0),
            "maxLength": GenerateIntegerExtraction(minInclusive=0),
            "minLength": GenerateIntegerExtraction(minInclusive=0),
            "totalDigits": GenerateIntegerExtraction(minExclusive=0),
            "whiteSpace": GenerateEnumeratedExtraction("value", ["collapse", "preserve", "replace"])
        }
    },

    "version": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            "default": GetToken
        }
    },

    "xpath": {
        "type": SYNTAXATTRIBUTE,
        "extract": {
            # "default": NotSupportedYet("xpath")
            "default": GetAttributeValue
        }
    },

    # -------------------------------------------------------------------------------
    #                           Simple types definition
    # -------------------------------------------------------------------------------

    "string": {
        "type": SIMPLETYPE,
        "basename": "string",
        "extract": GetAttributeValue,
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)},

    "normalizedString": {
        "type": SIMPLETYPE,
        "basename": "normalizedString",
        "extract": GetNormalizedString,
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "token": {
        "type": SIMPLETYPE,
        "basename": "token",
        "extract": GetToken,
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "base64Binary": {
        "type": SIMPLETYPE,
        "basename": "base64Binary",
        "extract": NotSupportedYet("base64Binary"),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, (int, long))
    },

    "hexBinary": {
        "type": SIMPLETYPE,
        "basename": "hexBinary",
        "extract": GetHexInteger,
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: ("%."+str(int(round(len("%X" % x)/2.)*2))+"X") % x),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, (int, long))
    },

    "integer": {
        "type": SIMPLETYPE,
        "basename": "integer",
        "extract": GenerateIntegerExtraction(),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "positiveInteger": {
        "type": SIMPLETYPE,
        "basename": "positiveInteger",
        "extract": GenerateIntegerExtraction(minExclusive=0),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 1,
        "check": lambda x: isinstance(x, int)
    },

    "negativeInteger": {
        "type": SIMPLETYPE,
        "basename": "negativeInteger",
        "extract": GenerateIntegerExtraction(maxExclusive=0),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: -1,
        "check": lambda x: isinstance(x, int)
    },

    "nonNegativeInteger": {
        "type": SIMPLETYPE,
        "basename": "nonNegativeInteger",
        "extract": GenerateIntegerExtraction(minInclusive=0),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "nonPositiveInteger": {
        "type": SIMPLETYPE,
        "basename": "nonPositiveInteger",
        "extract": GenerateIntegerExtraction(maxInclusive=0),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "long": {
        "type": SIMPLETYPE,
        "basename": "long",
        "extract": GenerateIntegerExtraction(minInclusive=-2**63, maxExclusive=2**63),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "unsignedLong": {
        "type": SIMPLETYPE,
        "basename": "unsignedLong",
        "extract": GenerateIntegerExtraction(minInclusive=0, maxExclusive=2**64),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "int": {
        "type": SIMPLETYPE,
        "basename": "int",
        "extract": GenerateIntegerExtraction(minInclusive=-2**31, maxExclusive=2**31),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "unsignedInt": {
        "type": SIMPLETYPE,
        "basename": "unsignedInt",
        "extract": GenerateIntegerExtraction(minInclusive=0, maxExclusive=2**32),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "short": {
        "type": SIMPLETYPE,
        "basename": "short",
        "extract": GenerateIntegerExtraction(minInclusive=-2**15, maxExclusive=2**15),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "unsignedShort": {
        "type": SIMPLETYPE,
        "basename": "unsignedShort",
        "extract": GenerateIntegerExtraction(minInclusive=0, maxExclusive=2**16),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "byte": {
        "type": SIMPLETYPE,
        "basename": "byte",
        "extract": GenerateIntegerExtraction(minInclusive=-2**7, maxExclusive=2**7),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "unsignedByte": {
        "type": SIMPLETYPE,
        "basename": "unsignedByte",
        "extract": GenerateIntegerExtraction(minInclusive=0, maxExclusive=2**8),
        "facets": DECIMAL_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: 0,
        "check": lambda x: isinstance(x, int)
    },

    "decimal": {
        "type": SIMPLETYPE,
        "basename": "decimal",
        "extract": GenerateFloatExtraction("decimal"),
        "facets": DECIMAL_FACETS,
        "generate": GenerateFloatXMLText(decimal=3),
        "initial": lambda: 0.,
        "check": lambda x: isinstance(x, (int, float))
    },

    "float": {
        "type": SIMPLETYPE,
        "basename": "float",
        "extract": GenerateFloatExtraction("float", ["INF", "-INF", "NaN"]),
        "facets": NUMBER_FACETS,
        "generate": GenerateFloatXMLText(["INF", "-INF", "NaN"]),
        "initial": lambda: 0.,
        "check": lambda x: {"INF": True, "-INF": True, "NaN": True}.get(x, isinstance(x, (int, float)))
    },

    "double": {
        "type": SIMPLETYPE,
        "basename": "double",
        "extract": GenerateFloatExtraction("double", ["INF", "-INF", "NaN"]),
        "facets": NUMBER_FACETS,
        "generate": GenerateFloatXMLText(["INF", "-INF", "NaN"]),
        "initial": lambda: 0.,
        "check": lambda x: {"INF": True, "-INF": True, "NaN": True}.get(x, isinstance(x, (int, float)))
    },

    "boolean": {
        "type": SIMPLETYPE,
        "basename": "boolean",
        "extract": GetBoolean,
        "facets": GenerateDictFacets(["pattern", "whiteSpace"]),
        "generate": GenerateSimpleTypeXMLText(lambda x: {True: "true", False: "false"}[x]),
        "initial": lambda: False,
        "check": lambda x: isinstance(x, bool)
    },

    "duration": {
        "type": SIMPLETYPE,
        "basename": "duration",
        "extract": NotSupportedYet("duration"),
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "dateTime": {
        "type": SIMPLETYPE,
        "basename": "dateTime",
        "extract": GetDateTime,
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(datetime.datetime.isoformat),
        "initial": lambda: datetime.datetime(1, 1, 1, 0, 0, 0, 0),
        "check": lambda x: isinstance(x, datetime.datetime)
    },

    "date": {
        "type": SIMPLETYPE,
        "basename": "date",
        "extract": GetDate,
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(datetime.date.isoformat),
        "initial": lambda: datetime.date(1, 1, 1),
        "check": lambda x: isinstance(x, datetime.date)
    },

    "time": {
        "type": SIMPLETYPE,
        "basename": "time",
        "extract": GetTime,
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(datetime.time.isoformat),
        "initial": lambda: datetime.time(0, 0, 0, 0),
        "check": lambda x: isinstance(x, datetime.time)
    },

    "gYear": {
        "type": SIMPLETYPE,
        "basename": "gYear",
        "extract": NotSupportedYet("gYear"),
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "gYearMonth": {
        "type": SIMPLETYPE,
        "basename": "gYearMonth",
        "extract": NotSupportedYet("gYearMonth"),
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "gMonth": {
        "type": SIMPLETYPE,
        "basename": "gMonth",
        "extract": NotSupportedYet("gMonth"),
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "gMonthDay": {
        "type": SIMPLETYPE,
        "basename": "gMonthDay",
        "extract": NotSupportedYet("gMonthDay"),
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "gDay": {
        "type": SIMPLETYPE,
        "basename": "gDay",
        "extract": NotSupportedYet("gDay"),
        "facets": NUMBER_FACETS,
        "generate": GenerateSimpleTypeXMLText(str),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "Name": {
        "type": SIMPLETYPE,
        "basename": "Name",
        "extract": GenerateModelNameExtraction("Name", Name_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "QName": {
        "type": SIMPLETYPE,
        "basename": "QName",
        "extract": GenerateModelNameExtraction("QName", QName_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "NCName": {
        "type": SIMPLETYPE,
        "basename": "NCName",
        "extract": GenerateModelNameExtraction("NCName", NCName_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "anyURI": {
        "type": SIMPLETYPE,
        "basename": "anyURI",
        "extract": GenerateModelNameExtraction("anyURI", URI_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "language": {
        "type": SIMPLETYPE,
        "basename": "language",
        "extract": GenerateModelNameExtraction("language", LANGUAGE_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "en",
        "check": lambda x: isinstance(x, string_types)
    },

    "ID": {
        "type": SIMPLETYPE,
        "basename": "ID",
        "extract": GenerateModelNameExtraction("ID", Name_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "IDREF": {
        "type": SIMPLETYPE,
        "basename": "IDREF",
        "extract": GenerateModelNameExtraction("IDREF", Name_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "IDREFS": {
        "type": SIMPLETYPE,
        "basename": "IDREFS",
        "extract": GenerateModelNameExtraction("IDREFS", Names_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "ENTITY": {
        "type": SIMPLETYPE,
        "basename": "ENTITY",
        "extract": GenerateModelNameExtraction("ENTITY", Name_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "ENTITIES": {
        "type": SIMPLETYPE,
        "basename": "ENTITIES",
        "extract": GenerateModelNameExtraction("ENTITIES", Names_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "NOTATION": {
        "type": SIMPLETYPE,
        "basename": "NOTATION",
        "extract": GenerateModelNameExtraction("NOTATION", Name_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "NMTOKEN": {
        "type": SIMPLETYPE,
        "basename": "NMTOKEN",
        "extract": GenerateModelNameExtraction("NMTOKEN", NMToken_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    "NMTOKENS": {
        "type": SIMPLETYPE,
        "basename": "NMTOKENS",
        "extract": GenerateModelNameExtraction("NMTOKENS", NMTokens_model),
        "facets": STRING_FACETS,
        "generate": GenerateSimpleTypeXMLText(lambda x: x),
        "initial": lambda: "",
        "check": lambda x: isinstance(x, string_types)
    },

    # Complex Types
    "anyType": {"type": COMPLEXTYPE, "extract": lambda x: None},
}
