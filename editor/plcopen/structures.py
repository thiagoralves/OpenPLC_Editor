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
from collections import OrderedDict
from functools import reduce

from plcopen.plcopen import LoadProject
from plcopen.definitions import *

TypeHierarchy = dict(TypeHierarchy_list)


def IsOfType(type, reference):
    """
    Returns true if the given data type is the same that "reference" meta-type or one of its types.
    """
    if reference is None:
        return True
    elif type == reference:
        return True
    else:
        parent_type = TypeHierarchy[type]
        if parent_type is not None:
            return IsOfType(parent_type, reference)
    return False


def GetSubTypes(type):
    """
    Returns list of all types that correspont to the ANY* meta type
    """
    return [typename for typename, _parenttype in TypeHierarchy.items() if not typename.startswith("ANY") and IsOfType(typename, type)]


DataTypeRange = dict(DataTypeRange_list)

"""
Ordered list of common Function Blocks defined in the IEC 61131-3
Each block have this attributes:
    - "name" : The block name
    - "type" : The block type. It can be "function", "functionBlock" or "program"
    - "extensible" : Boolean that define if the block is extensible
    - "inputs" : List of the block inputs
    - "outputs" : List of the block outputs
    - "comment" : Comment that will be displayed in the block popup
    - "generate" : Method that generator will call for generating ST block code
Inputs and outputs are a tuple of characteristics that are in order:
    - The name
    - The data type
    - The default modifier which can be "none", "negated", "rising" or "falling"
"""

StdBlckLibs = {libname: LoadProject(tc6fname)[0]
               for libname, tc6fname in StdTC6Libs}
StdBlckLst = [{"name": libname, "list":
               [GetBlockInfos(pous) for pous in lib.getpous()]}
              for libname, lib in StdBlckLibs.iteritems()]

# -------------------------------------------------------------------------------
#                             Test identifier
# -------------------------------------------------------------------------------

IDENTIFIER_MODEL = re.compile(
    "(?:%(letter)s|_(?:%(letter)s|%(digit)s))(?:_?(?:%(letter)s|%(digit)s))*$" %
    {"letter": "[a-zA-Z]", "digit": "[0-9]"})


def TestIdentifier(identifier):
    """
    Test if identifier is valid
    """
    return IDENTIFIER_MODEL.match(identifier) is not None

# -------------------------------------------------------------------------------
#                        Standard functions list generation
# -------------------------------------------------------------------------------


def csv_file_to_table(file):
    """
    take a .csv file and translate it it a "csv_table"
    """
    table = [[column.strip()
              for column in line.split(';')]
             for line in file.readlines()]
    return table


def find_section(section_name, table):
    """
    seek into the csv table to a section ( section_name match 1st field )
    return the matching row without first field
    """
    fields = [None]
    while fields[0] != section_name:
        fields = table.pop(0)
    return fields[1:]


def get_standard_funtions_input_variables(table):
    """
    extract the standard functions standard parameter names and types...
    return a { ParameterName: Type, ...}
    """
    variables = find_section("Standard_functions_variables_types", table)
    standard_funtions_input_variables = {}
    fields = [True, True]
    while fields[1]:
        fields = table.pop(0)
        variable_from_csv = dict([(champ, val) for champ, val in zip(variables, fields[1:]) if champ != ''])
        standard_funtions_input_variables[variable_from_csv['name']] = variable_from_csv['type']
    return standard_funtions_input_variables


def csv_input_translate(str_decl, variables, base):
    """
    translate .csv file input declaration into PLCOpenEditor interessting values
    in : "(ANY_NUM, ANY_NUM)" and { ParameterName: Type, ...}
    return [("IN1","ANY_NUM","none"),("IN2","ANY_NUM","none")]
    """
    decl = str_decl.replace('(', '').replace(')', '').replace(' ', '').split(',')
    params = []

    len_of_not_predifined_variable = len([True for param_type in decl if param_type not in variables])

    for param_type in decl:
        if param_type in variables.keys():
            param_name = param_type
            param_type = variables[param_type]
        elif len_of_not_predifined_variable > 1:
            param_name = "IN%d" % base
            base += 1
        else:
            param_name = "IN"
        params.append((param_name, param_type, "none"))
    return params


def get_standard_funtions(table):
    """
    Returns this kind of declaration for all standard functions

            [{"name" : "Numerical", 'list': [   {
                'baseinputnumber': 1,
                'comment': 'Addition',
                'extensible': True,
                'inputs': [   ('IN1', 'ANY_NUM', 'none'),
                              ('IN2', 'ANY_NUM', 'none')],
                'name': 'ADD',
                'outputs': [('OUT', 'ANY_NUM', 'none')],
                'type': 'function'}, ...... ] },.....]
    """

    variables = get_standard_funtions_input_variables(table)

    fonctions = find_section("Standard_functions_type", table)

    Standard_Functions_Decl = []
    Current_section = None

    translate = {
        "extensible": lambda x: {"yes": True, "no": False}[x],
        "inputs": lambda x: csv_input_translate(x, variables, baseinputnumber),
        "outputs": lambda x: [("OUT", x, "none")]}

    for fields in table:
        if fields[1]:
            # If function section name given
            if fields[0]:
                words = fields[0].split('"')
                if len(words) > 1:
                    section_name = words[1]
                else:
                    section_name = fields[0]
                Current_section = {"name": section_name, "list": []}
                Standard_Functions_Decl.append(Current_section)
            if Current_section:
                Function_decl = dict([(champ, val) for champ, val in zip(fonctions, fields[1:]) if champ])
                baseinputnumber = int(Function_decl.get("baseinputnumber", 1))
                Function_decl["baseinputnumber"] = baseinputnumber
                for param, value in Function_decl.iteritems():
                    if param in translate:
                        Function_decl[param] = translate[param](value)
                Function_decl["type"] = "function"

                if Function_decl["name"].startswith('*') or Function_decl["name"].endswith('*'):
                    input_ovrloading_types = GetSubTypes(Function_decl["inputs"][0][1])
                    output_types = GetSubTypes(Function_decl["outputs"][0][1])
                else:
                    input_ovrloading_types = [None]
                    output_types = [None]

                funcdeclname_orig = Function_decl["name"]
                funcdeclname = Function_decl["name"].strip('*_')
                fdc = Function_decl["inputs"][:]
                for intype in input_ovrloading_types:
                    if intype is not None:
                        Function_decl["inputs"] = []
                        for decl_tpl in fdc:
                            if IsOfType(intype, decl_tpl[1]):
                                Function_decl["inputs"] += [(decl_tpl[0], intype, decl_tpl[2])]
                            else:
                                Function_decl["inputs"] += [(decl_tpl)]

                            if funcdeclname_orig.startswith('*'):
                                funcdeclin = intype + '_' + funcdeclname
                            else:
                                funcdeclin = funcdeclname
                    else:
                        funcdeclin = funcdeclname

                    for outype in output_types:
                        if outype is not None:
                            decl_tpl = Function_decl["outputs"][0]
                            Function_decl["outputs"] = [(decl_tpl[0], outype,  decl_tpl[2])]
                            if funcdeclname_orig.endswith('*'):
                                funcdeclout = funcdeclin + '_' + outype
                            else:
                                funcdeclout = funcdeclin
                        else:
                            funcdeclout = funcdeclin
                        Function_decl["name"] = funcdeclout

                        # apply filter given in "filter" column
                        filter_name = Function_decl["filter"]
                        store = True
                        for (InTypes, OutTypes) in ANY_TO_ANY_FILTERS.get(filter_name, []):
                            outs = reduce(lambda a, b: a or b,
                                          map(lambda testtype: IsOfType(
                                              Function_decl["outputs"][0][1],
                                              testtype), OutTypes))
                            inps = reduce(lambda a, b: a or b,
                                          map(lambda testtype: IsOfType(
                                              Function_decl["inputs"][0][1],
                                              testtype), InTypes))
                            if inps and outs and Function_decl["outputs"][0][1] != Function_decl["inputs"][0][1]:
                                store = True
                                break
                            else:
                                store = False
                        if store:
                            # create the copy of decl dict to be appended to section
                            Function_decl_copy = Function_decl.copy()
                            Current_section["list"].append(Function_decl_copy)
            else:
                raise ValueError("First function must be in a category")

    return Standard_Functions_Decl


StdBlckLst.extend(get_standard_funtions(csv_file_to_table(open(StdFuncsCSV))))

# Dictionary to speedup block type fetching by name
StdBlckDct = OrderedDict()

for section in StdBlckLst:
    for desc in section["list"]:
        words = desc["comment"].split('"')
        if len(words) > 1:
            desc["comment"] = words[1]
        desc["usage"] = ("\n (%s) => (%s)" %
                         (", ".join(["%s:%s" % (input[1], input[0])
                                     for input in desc["inputs"]]),
                          ", ".join(["%s:%s" % (output[1], output[0])
                                     for output in desc["outputs"]])))
        BlkLst = StdBlckDct.setdefault(desc["name"], [])
        BlkLst.append((section["name"], desc))

# -------------------------------------------------------------------------------
#                            Languages Keywords
# -------------------------------------------------------------------------------

# Keywords for Pou Declaration
POU_BLOCK_START_KEYWORDS = ["FUNCTION", "FUNCTION_BLOCK", "PROGRAM"]
POU_BLOCK_END_KEYWORDS = ["END_FUNCTION", "END_FUNCTION_BLOCK", "END_PROGRAM"]
POU_KEYWORDS = ["EN", "ENO", "F_EDGE", "R_EDGE"] + POU_BLOCK_START_KEYWORDS + POU_BLOCK_END_KEYWORDS
for category in StdBlckLst:
    for block in category["list"]:
        if block["name"] not in POU_KEYWORDS:
            POU_KEYWORDS.append(block["name"])


# Keywords for Type Declaration
TYPE_BLOCK_START_KEYWORDS = ["TYPE", "STRUCT"]
TYPE_BLOCK_END_KEYWORDS = ["END_TYPE", "END_STRUCT"]
TYPE_KEYWORDS = ["ARRAY", "OF", "T", "D", "TIME_OF_DAY", "DATE_AND_TIME"] + TYPE_BLOCK_START_KEYWORDS + TYPE_BLOCK_END_KEYWORDS
TYPE_KEYWORDS.extend([keyword for keyword in TypeHierarchy.keys() if keyword not in TYPE_KEYWORDS])


# Keywords for Variable Declaration
VAR_BLOCK_START_KEYWORDS = ["VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT", "VAR_TEMP", "VAR_EXTERNAL"]
VAR_BLOCK_END_KEYWORDS = ["END_VAR"]
VAR_KEYWORDS = ["AT", "CONSTANT", "RETAIN", "NON_RETAIN"] + VAR_BLOCK_START_KEYWORDS + VAR_BLOCK_END_KEYWORDS


# Keywords for Configuration Declaration
CONFIG_BLOCK_START_KEYWORDS = ["CONFIGURATION", "RESOURCE", "VAR_ACCESS", "VAR_CONFIG", "VAR_GLOBAL"]
CONFIG_BLOCK_END_KEYWORDS = ["END_CONFIGURATION", "END_RESOURCE", "END_VAR"]
CONFIG_KEYWORDS = ["ON", "PROGRAM", "WITH", "READ_ONLY", "READ_WRITE", "TASK"] + CONFIG_BLOCK_START_KEYWORDS + CONFIG_BLOCK_END_KEYWORDS

# Keywords for Structured Function Chart
SFC_BLOCK_START_KEYWORDS = ["ACTION", "INITIAL_STEP", "STEP", "TRANSITION"]
SFC_BLOCK_END_KEYWORDS = ["END_ACTION", "END_STEP", "END_TRANSITION"]
SFC_KEYWORDS = ["FROM", "TO"] + SFC_BLOCK_START_KEYWORDS + SFC_BLOCK_END_KEYWORDS


# Keywords for Instruction List
IL_KEYWORDS = [
    "TRUE", "FALSE", "LD", "LDN", "ST", "STN", "S", "R", "AND", "ANDN", "OR", "ORN",
    "XOR", "XORN", "NOT", "ADD", "SUB", "MUL", "DIV", "MOD", "GT", "GE", "EQ", "NE",
    "LE", "LT", "JMP", "JMPC", "JMPCN", "CAL", "CALC", "CALCN", "RET", "RETC", "RETCN"
]


# Keywords for Structured Text
ST_BLOCK_START_KEYWORDS = ["IF", "ELSIF", "ELSE", "CASE", "FOR", "WHILE", "REPEAT"]
ST_BLOCK_END_KEYWORDS = ["END_IF", "END_CASE", "END_FOR", "END_WHILE", "END_REPEAT"]
ST_KEYWORDS = [
    "TRUE", "FALSE", "THEN", "OF", "TO", "BY", "DO", "DO", "UNTIL", "EXIT",
    "RETURN", "NOT", "MOD", "AND", "XOR", "OR"
] + ST_BLOCK_START_KEYWORDS + ST_BLOCK_END_KEYWORDS

# All the keywords of IEC
IEC_BLOCK_START_KEYWORDS = []
IEC_BLOCK_END_KEYWORDS = []
IEC_KEYWORDS = ["E", "TRUE", "FALSE"]
for all_keywords, keywords_list in [(IEC_BLOCK_START_KEYWORDS, [POU_BLOCK_START_KEYWORDS, TYPE_BLOCK_START_KEYWORDS,
                                                                VAR_BLOCK_START_KEYWORDS, CONFIG_BLOCK_START_KEYWORDS,
                                                                SFC_BLOCK_START_KEYWORDS, ST_BLOCK_START_KEYWORDS]),
                                    (IEC_BLOCK_END_KEYWORDS, [POU_BLOCK_END_KEYWORDS, TYPE_BLOCK_END_KEYWORDS,
                                                              VAR_BLOCK_END_KEYWORDS, CONFIG_BLOCK_END_KEYWORDS,
                                                              SFC_BLOCK_END_KEYWORDS, ST_BLOCK_END_KEYWORDS]),
                                    (IEC_KEYWORDS, [POU_KEYWORDS, TYPE_KEYWORDS, VAR_KEYWORDS, CONFIG_KEYWORDS,
                                                    SFC_KEYWORDS, IL_KEYWORDS, ST_KEYWORDS])]:
    for keywords in keywords_list:
        all_keywords.extend([keyword for keyword in keywords if keyword not in all_keywords])
