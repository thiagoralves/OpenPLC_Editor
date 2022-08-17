#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Beremiz.
# See COPYING file for copyrights details.

from __future__ import absolute_import
from plcopen.XSLTModelQuery import XSLTModelQuery, _StringValue, _BoolValue, _translate_args

# -------------------------------------------------------------------------------
#                 Helpers object for generating pou var list
# -------------------------------------------------------------------------------


class _VariableInfos(object):
    __slots__ = ["Name", "Class", "Option", "Location", "InitialValue",
                 "Edit", "Documentation", "Type", "Tree", "Number"]

    def __init__(self, *args):
        for attr, value in zip(self.__slots__, args):
            setattr(self, attr, value if value is not None else "")

    def copy(self):
        return _VariableInfos(*[getattr(self, attr) for attr in self.__slots__])


class VariablesInfosFactory(object):
    """ Helpers object for generating pou var list """

    def __init__(self, variables):
        self.Variables = variables
        self.TreeStack = []
        self.Type = None
        self.Dimensions = None

    def SetType(self, context, *args):
        self.Type = args[0][0]

    def GetType(self):
        if len(self.Dimensions) > 0:
            return ("array", self.Type, self.Dimensions)
        return self.Type

    def GetTree(self):
        return (self.TreeStack.pop(-1), self.Dimensions)

    def AddDimension(self, context, *args):
        self.Dimensions.append(tuple(
            _translate_args([_StringValue] * 2, args)))

    def AddTree(self, context, *args):
        self.TreeStack.append([])
        self.Dimensions = []

    def AddVarToTree(self, context, *args):
        var = (args[0][0], self.Type, self.GetTree())
        self.TreeStack[-1].append(var)

    def AddVariable(self, context, *args):
        self.Variables.append(_VariableInfos(*(
            _translate_args([_StringValue] * 5 + [_BoolValue] + [_StringValue], args) +
            [self.GetType(), self.GetTree()])))


class VariableInfoCollector(XSLTModelQuery):
    def __init__(self, controller):
        XSLTModelQuery.__init__(self,
                                controller,
                                "variables_infos.xslt",
                                [(name, self.FactoryCaller(name))
                                 for name in [
                                     "SetType",
                                     "AddDimension",
                                     "AddTree",
                                     "AddVarToTree",
                                     "AddVariable"]])

    def FactoryCaller(self, funcname):
        def CallFactory(*args):
            return getattr(self.factory, funcname)(*args)
        return CallFactory

    def Collect(self, root, debug, variables, tree):
        self.factory = VariablesInfosFactory(variables)
        self._process_xslt(root, debug, tree=str(tree))
        res = self.factory
        self.factory = None
        return res
