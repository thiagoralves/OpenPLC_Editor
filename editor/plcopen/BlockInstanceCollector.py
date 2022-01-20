#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Beremiz.
# See COPYING file for copyrights details.

from __future__ import absolute_import
from collections import OrderedDict, namedtuple
from plcopen.XSLTModelQuery import XSLTModelQuery, _StringValue, _BoolValue, _translate_args

# -------------------------------------------------------------------------------
#           Helpers object for generating pou block instances list
# -------------------------------------------------------------------------------


_Point = namedtuple("Point", ["x", "y"])

_BlockInstanceInfos = namedtuple(
    "BlockInstanceInfos",
    ["type", "id", "x", "y", "width", "height", "specific_values", "inputs", "outputs"])

_BlockSpecificValues = (
    namedtuple("BlockSpecificValues",
               ["name", "execution_order"]),
    [_StringValue, int])
_VariableSpecificValues = (
    namedtuple("VariableSpecificValues",
               ["name", "value_type", "execution_order"]),
    [_StringValue, _StringValue, int])
_ConnectionSpecificValues = (
    namedtuple("ConnectionSpecificValues", ["name"]),
    [_StringValue])

_PowerRailSpecificValues = (
    namedtuple("PowerRailSpecificValues", ["connectors"]),
    [int])

_LDElementSpecificValues = (
    namedtuple("LDElementSpecificValues",
               ["name", "negated", "edge", "storage", "execution_order"]),
    [_StringValue, _BoolValue, _StringValue, _StringValue, int])

_DivergenceSpecificValues = (
    namedtuple("DivergenceSpecificValues", ["connectors"]),
    [int])

_SpecificValuesTuples = {
    "comment": (
        namedtuple("CommentSpecificValues", ["content"]),
        [_StringValue]),
    "input": _VariableSpecificValues,
    "output": _VariableSpecificValues,
    "inout": _VariableSpecificValues,
    "connector": _ConnectionSpecificValues,
    "continuation": _ConnectionSpecificValues,
    "leftPowerRail": _PowerRailSpecificValues,
    "rightPowerRail": _PowerRailSpecificValues,
    "contact": _LDElementSpecificValues,
    "coil": _LDElementSpecificValues,
    "step": (
        namedtuple("StepSpecificValues", ["name", "initial", "action"]),
        [_StringValue, _BoolValue, lambda x: x]),
    "transition": (
        namedtuple("TransitionSpecificValues",
                   ["priority", "condition_type", "condition", "connection"]),
        [int, _StringValue, _StringValue, lambda x: x]),
    "selectionDivergence": _DivergenceSpecificValues,
    "selectionConvergence": _DivergenceSpecificValues,
    "simultaneousDivergence": _DivergenceSpecificValues,
    "simultaneousConvergence": _DivergenceSpecificValues,
    "jump": (
        namedtuple("JumpSpecificValues", ["target"]),
        [_StringValue]),
    "actionBlock": (
        namedtuple("ActionBlockSpecificValues", ["actions"]),
        [lambda x: x]),
}

_InstanceConnectionInfos = namedtuple(
    "InstanceConnectionInfos",
    ["name", "negated", "edge", "position", "links"])

_ConnectionLinkInfos = namedtuple(
    "ConnectionLinkInfos",
    ["refLocalId", "formalParameter", "points"])


class _ActionInfos(object):
    __slots__ = ["qualifier", "type", "value", "duration", "indicator"]

    def __init__(self, *args):
        for attr, value in zip(self.__slots__, args):
            setattr(self, attr, value if value is not None else "")

    def copy(self):
        return _ActionInfos(*[getattr(self, attr) for attr in self.__slots__])


class BlockInstanceFactory(object):

    def __init__(self, block_instances):
        self.BlockInstances = block_instances
        self.CurrentInstance = None
        self.SpecificValues = None
        self.CurrentConnection = None
        self.CurrentLink = None

    def SetSpecificValues(self, context, *args):
        self.SpecificValues = list(args)
        self.CurrentInstance = None
        self.CurrentConnection = None
        self.CurrentLink = None

    def AddBlockInstance(self, context, *args):
        specific_values_tuple, specific_values_translation = \
            _SpecificValuesTuples.get(args[0][0], _BlockSpecificValues)

        if args[0][0] == "step" and len(self.SpecificValues) < 3 or \
           args[0][0] == "transition" and len(self.SpecificValues) < 4:
            self.SpecificValues.append([None])
        elif args[0][0] == "actionBlock" and len(self.SpecificValues) < 1:
            self.SpecificValues.append([[]])
        specific_values = specific_values_tuple(*_translate_args(
            specific_values_translation, self.SpecificValues))
        self.SpecificValues = None

        self.CurrentInstance = _BlockInstanceInfos(
            *(_translate_args([_StringValue, int] + [float] * 4, args) +
              [specific_values, [], []]))

        self.BlockInstances[self.CurrentInstance.id] = self.CurrentInstance

    def AddInstanceConnection(self, context, *args):
        connection_args = _translate_args(
            [_StringValue] * 2 + [_BoolValue, _StringValue] + [float] * 2, args)

        self.CurrentConnection = _InstanceConnectionInfos(
            *(connection_args[1:4] + [
                _Point(*connection_args[4:6]), []]))

        if self.CurrentInstance is not None:
            if connection_args[0] == "input":
                self.CurrentInstance.inputs.append(self.CurrentConnection)
            else:
                self.CurrentInstance.outputs.append(self.CurrentConnection)
        else:
            self.SpecificValues.append([self.CurrentConnection])

    def AddConnectionLink(self, context, *args):
        self.CurrentLink = _ConnectionLinkInfos(
            *(_translate_args([int, _StringValue], args) + [[]]))
        self.CurrentConnection.links.append(self.CurrentLink)

    def AddLinkPoint(self, context, *args):
        self.CurrentLink.points.append(_Point(
            *_translate_args([float] * 2, args)))

    def AddAction(self, context, *args):
        if len(self.SpecificValues) == 0:
            self.SpecificValues.append([[]])
        translated_args = _translate_args([_StringValue] * 5, args)
        self.SpecificValues[0][0].append(_ActionInfos(*translated_args))


class BlockInstanceCollector(XSLTModelQuery):
    """ object for collecting instances path list"""
    def __init__(self, controller):
        XSLTModelQuery.__init__(self,
                                controller,
                                "pou_block_instances.xslt",
                                [(name, self.FactoryCaller(name))
                                 for name in ["AddBlockInstance",
                                              "SetSpecificValues",
                                              "AddInstanceConnection",
                                              "AddConnectionLink",
                                              "AddLinkPoint",
                                              "AddAction"]])

    def FactoryCaller(self, funcname):
        def CallFactory(*args):
            return getattr(self.factory, funcname)(*args)
        return CallFactory

    def Collect(self, root, debug):
        element_instances = OrderedDict()
        self.factory = BlockInstanceFactory(element_instances)
        self._process_xslt(root, debug)
        self.factory = None
        return element_instances
