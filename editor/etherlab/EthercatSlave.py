#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
#
# Copyright (C) 2011-2014: Laurent BESSARD, Edouard TISSERANT
#                          RTES Lab : CRKim, JBLee, youcu
#                          Higen Motor : Donggu Kang
#
# See COPYING file for copyrights details.

from __future__ import absolute_import

from PLCControler import LOCATION_CONFNODE, LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT, LOCATION_VAR_MEMORY
from ConfigTreeNode import ConfigTreeNode

from etherlab.ConfigEditor import NodeEditor

# ------------------------------------------
from etherlab.CommonEtherCATFunction import _CommonSlave
# ------------------------------------------


TYPECONVERSION = {"BOOL": "X", "SINT": "B", "INT": "W", "DINT": "D", "LINT": "L",
                  "USINT": "B", "UINT": "W", "UDINT": "D", "ULINT": "L",
                  "BYTE": "B", "WORD": "W", "DWORD": "D", "LWORD": "L"}

DATATYPECONVERSION = {"BOOL": "BIT", "SINT": "S8", "INT": "S16", "DINT": "S32", "LINT": "S64",
                      "USINT": "U8", "UINT": "U16", "UDINT": "U32", "ULINT": "U64",
                      "BYTE": "U8", "WORD": "U16", "DWORD": "U32", "LWORD": "U64"}

VARCLASSCONVERSION = {"T": LOCATION_VAR_INPUT, "R": LOCATION_VAR_OUTPUT, "RT": LOCATION_VAR_MEMORY}


def ExtractHexDecValue(value):
    try:
        return int(value)
    except Exception:
        pass
    try:
        return int(value.replace("#", "0"), 16)
    except Exception:
        raise ValueError("Invalid value for HexDecValue \"%s\"" % value)


def GenerateHexDecValue(value, base=10):
    if base == 10:
        return str(value)
    elif base == 16:
        return "#x%.8x" % value
    else:
        raise ValueError("Not supported base")


def ExtractName(names, default=None):
    if len(names) == 1:
        return names[0].getcontent()
    else:
        for name in names:
            if name.getLcId() == 1033:
                return name.getcontent()
    return default


# --------------------------------------------------
#                    Ethercat Node
# --------------------------------------------------

class _EthercatSlaveCTN(object):
    NODE_PROFILE = None
    EditorType = NodeEditor

    def __init__(self):
        # ----------- call ethercat mng. function --------------
        self.CommonMethod = _CommonSlave(self)

    def GetIconName(self):
        return "Slave"

    def ExtractHexDecValue(self, value):
        return ExtractHexDecValue(value)

    def GetSizeOfType(self, type):
        return TYPECONVERSION.get(self.GetCTRoot().GetBaseType(type), None)

    def GetSlavePos(self):
        return self.BaseParams.getIEC_Channel()

    def GetParamsAttributes(self, path=None):
        if path:
            parts = path.split(".", 1)
            if self.MandatoryParams and parts[0] == self.MandatoryParams[0]:
                return self.MandatoryParams[1].getElementInfos(parts[0], parts[1])
            elif self.CTNParams and parts[0] == self.CTNParams[0]:
                return self.CTNParams[1].getElementInfos(parts[0], parts[1])
        else:
            params = []
            if self.CTNParams:
                params.append(self.CTNParams[1].getElementInfos(self.CTNParams[0]))
            else:
                params.append({
                    'use': 'required',
                    'type': 'element',
                    'name': 'SlaveParams',
                    'value': None,
                    'children': []
                })

            slave_type = self.CTNParent.GetSlaveType(self.GetSlavePos())
            params[0]['children'].insert(
                0,
                {
                    'use': 'optional',
                    'type': self.CTNParent.GetSlaveTypesLibrary(self.NODE_PROFILE),
                    'name': 'Type',
                    'value': (slave_type["device_type"], slave_type)
                })
            params[0]['children'].insert(
                1,
                {
                    'use': 'optional',
                    'type': 'unsignedLong',
                    'name': 'Alias',
                    'value': self.CTNParent.GetSlaveAlias(self.GetSlavePos())
                })
            return params

    def SetParamsAttribute(self, path, value):
        self.GetSlaveInfos()
        position = self.BaseParams.getIEC_Channel()

        if path == "SlaveParams.Type":
            self.CTNParent.SetSlaveType(position, value)
            slave_type = self.CTNParent.GetSlaveType(self.GetSlavePos())
            value = (slave_type["device_type"], slave_type)
            # if self._View is not None:
            #     wx.CallAfter(self._View.EtherCATManagementTreebook.SlaveStatePanel.RefreshSlaveInfos())
            #     self._View.EtherCATManagementTreebook.SlaveStatePanel.RefreshSlaveInfos()
            #     self._View.EtherCATManagementTreebook.PDOMonitoringPanel.PDOInfoUpdate()
            #     self._View.EtherCATManagementTreebook.SmartView.Create_SmartView()
            return value, True
        elif path == "SlaveParams.Alias":
            self.CTNParent.SetSlaveAlias(position, value)
            return value, True

        value, refresh = ConfigTreeNode.SetParamsAttribute(self, path, value)

        # Filter IEC_Channel, Slave_Type and Alias that have specific behavior
        if path == "BaseParams.IEC_Channel" and value != position:
            self.CTNParent.SetSlavePosition(position, value)

        return value, refresh

    def GetSlaveInfos(self):
        return self.CTNParent.GetSlaveInfos(self.GetSlavePos())

    def GetSlaveVariables(self, limits):
        return self.CTNParent.GetSlaveVariables(self.GetSlavePos(), limits)

    def GetVariableLocationTree(self):
        return {
            "name": self.BaseParams.getName(),
            "type": LOCATION_CONFNODE,
            "location": self.GetFullIEC_Channel(),
            "children": self.CTNParent.GetDeviceLocationTree(self.GetSlavePos(), self.GetCurrentLocation(), self.BaseParams.getName())
        }

    def CTNGenerate_C(self, buildpath, locations):
        return [], "", False
