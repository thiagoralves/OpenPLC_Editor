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
import os

import wx

from PLCControler import LOCATION_CONFNODE, LOCATION_VAR_INPUT

from MotionLibrary import AxisXSD
from etherlab.EthercatSlave import _EthercatSlaveCTN, _CommonSlave
from etherlab.ConfigEditor import CIA402NodeEditor

# Definition of node variables that have to be mapped in PDO
# [(name, index, subindex, type,
#   direction for master ('I': input, 'Q': output)),...]
NODE_VARIABLES = [
    ("ControlWord",             0x6040, 0x00, "UINT", "Q"),
    ("TargetPosition",          0x607a, 0x00, "DINT", "Q"),
    ("TargetVelocity",          0x60ff, 0x00, "DINT", "Q"),
    ("TargetTorque",            0x6071, 0x00, "INT",  "Q"),
    ("ModesOfOperation",        0x6060, 0x00, "SINT", "Q"),
    ("StatusWord",              0x6041, 0x00, "UINT", "I"),
    ("ModesOfOperationDisplay", 0x6061, 0x00, "SINT", "I"),
    ("ActualPosition",          0x6064, 0x00, "DINT", "I"),
    ("ActualVelocity",          0x606c, 0x00, "DINT", "I"),
    ("ActualTorque",            0x6077, 0x00, "INT",  "I"),
]

# Definition of optional node variables that can be added to PDO mapping.
# A checkbox will be displayed for each section in node configuration panel to
# enable them
# [(section_name,
#   [{'description', (name, index, subindex, type,
#                     direction for master ('I': input, 'Q': output)),
#     'retrieve', string_template_for_retrieve_variable (None: not retrieved,
#                                 default string template if not defined),
#     'publish', string_template_for_publish_variable (None: not published,
#                                 default string template if not defined),
#    },...]
EXTRA_NODE_VARIABLES = [
    ("ErrorCode", [
        {"description": ("ErrorCode", 0x603F, 0x00, "UINT", "I"),
         "publish": None}
        ]),
    ("DigitalInputs", [
        {"description": ("DigitalInputs", 0x60FD, 0x00, "UDINT", "I"),
         "publish": None}
        ]),
    ("DigitalOutputs", [
        {"description": ("DigitalOutputs", 0x60FE, 0x00, "UDINT", "Q"),
         "retrieve": None}
        ]),
    ("TouchProbe", [
        {"description": ("TouchProbeFunction", 0x60B8, 0x00, "UINT", "Q"),
         "retrieve": None},
        {"description": ("TouchProbeStatus", 0x60B9, 0x00, "UINT", "I"),
         "publish": None},
        {"description": ("TouchProbePos1PosValue", 0x60BA, 0x00, "DINT", "I"),
         "publish": None},
        {"description": ("TouchProbePos1NegValue", 0x60BB, 0x00, "DINT", "I"),
         "publish": None},
        ]),
]

# List of parameters name in no configuration panel for optional variable
# sections
EXTRA_NODE_VARIABLES_DICT = {
    "Enable" + name: params
    for name, params in EXTRA_NODE_VARIABLES}

# List of block to define to interface MCL to fieldbus for specific functions
FIELDBUS_INTERFACE_GLOBAL_INSTANCES = [
    {"blocktype": "GetTorqueLimit",
     "inputs": [],
     "outputs": [{"name": "TorqueLimitPos", "type": "UINT"},
                 {"name": "TorqueLimitNeg", "type": "UINT"}]},
    {"blocktype": "SetTorqueLimit",
     "inputs": [{"name": "TorqueLimitPos", "type": "UINT"},
                {"name": "TorqueLimitNeg", "type": "UINT"}],
     "outputs": []},
]

# --------------------------------------------------
#                 Ethercat CIA402 Node
# --------------------------------------------------


class _EthercatCIA402SlaveCTN(_EthercatSlaveCTN):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="CIA402SlaveParams">
        <xsd:complexType>
          %s
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """ % ("\n".join(["""\
          <xsd:attribute name="Enable%s" type="xsd:boolean"
                         use="optional" default="false"/>""" % category
                      for category, variables in EXTRA_NODE_VARIABLES]) + AxisXSD)

    NODE_PROFILE = 402
    EditorType = CIA402NodeEditor

    ConfNodeMethods = [
        {
            "bitmap": "CIA402AxisRef",
            "name": _("Axis Ref"),
            "tooltip": _("Initiate Drag'n drop of Axis ref located variable"),
            "method": "_getCIA402AxisRef",
            "push": True,
        },
        {
            "bitmap": "CIA402NetPos",
            "name": _("Axis Pos"),
            "tooltip": _("Initiate Drag'n drop of Network position located variable"),
            "method": "_getCIA402NetworkPosition",
            "push": True,
        },
    ]

# --------------------------------------------------
#    class code
# --------------------------------------------------

    def __init__(self):
        _EthercatSlaveCTN.__init__(self)

        # ----------- call ethercat mng. function --------------
        self.CommonMethod = _CommonSlave(self)

    def GetIconName(self):
        return "CIA402Slave"

    def SetParamsAttribute(self, path, value):
        if path == "CIA402SlaveParams.Type":
            path = "SlaveParams.Type"
        elif path == "CIA402SlaveParams.Alias":
            path = "SlaveParams.Alias"
        return _EthercatSlaveCTN.SetParamsAttribute(self, path, value)

    def GetVariableLocationTree(self):
        axis_name = self.CTNName()
        current_location = self.GetCurrentLocation()
        children = [
            {
                "name": name_frmt % (axis_name),
                "type": LOCATION_VAR_INPUT,
                "size": "W",
                "IEC_type": iec_type,
                "var_name": var_name_frmt % axis_name,
                "location": location_frmt % (".".join(map(str, current_location))),
                "description": "",
                "children": []
            }
            for name_frmt, iec_type, var_name_frmt, location_frmt in [
                ("%s Network Position", "UINT", "%s_pos", "%%IW%s"),
                ("%s Axis Ref", "AXIS_REF", "%s", "%%IW%s.402")
            ]
        ]
        children.extend(self.CTNParent.GetDeviceLocationTree(self.GetSlavePos(),
                                                             current_location,
                                                             axis_name))
        return {
            "name": axis_name,
            "type": LOCATION_CONFNODE,
            "location": self.GetFullIEC_Channel(),
            "children": children,
        }

    def CTNGlobalInstances(self):
        current_location = self.GetCurrentLocation()
        return [("%s_%s" % (block_infos["blocktype"],
                            "_".join(map(str, current_location))),
                 "EtherLab%s" % block_infos["blocktype"], "")
                for block_infos in FIELDBUS_INTERFACE_GLOBAL_INSTANCES]

    def StartDragNDrop(self, data):
        data_obj = wx.TextDataObject(str(data))
        dragSource = wx.DropSource(self.GetCTRoot().AppFrame)
        dragSource.SetData(data_obj)
        dragSource.DoDragDrop()

    def _getCIA402NetworkPosition(self):
        self.StartDragNDrop(
            ("%%IW%s" % ".".join(map(str, self.GetCurrentLocation())),
             "location", "UINT", self.CTNName() + "_Pos", ""))

    def _getCIA402AxisRef(self):
        self.StartDragNDrop(
            ("%%IW%s.402" % ".".join(map(str, self.GetCurrentLocation())),
             "location", "AXIS_REF", self.CTNName(), ""))

    # add jblee
    """
    def LoadPDOSelectData(self):
        ReadData = []
        files = os.listdir(self.CTNPath())
        filepath = os.path.join(self.CTNPath(), "DataForPDO.txt")
        if os.path.isfile(filepath):
            PDODataRead = open(filepath, 'r')
            ReadData = PDODataRead.readlines()
            PDODataRead.close()

        if len(ReadData) > 1:
            for data in ReadData[0].split() :
                if data == "RxPDO":
                    continue
                self.SelectedRxPDOIndex.append(int(data, 0))

            for data in ReadData[1].split() :
                if data == "TxPDO":
                    continue
                self.SelectedTxPDOIndex.append(int(data, 0))
    """

    def LoadPDOSelectData(self):
        RxPDOData = self.BaseParams.getRxPDO()
        RxPDOs = []
        if RxPDOData != "None":
            RxPDOs = RxPDOData.split()
        if RxPDOs :
            for RxPDO in RxPDOs :
                self.SelectedRxPDOIndex.append(int(RxPDO, 0))

        TxPDOData = self.BaseParams.getTxPDO()
        TxPDOs = []
        if TxPDOData != "None":
            TxPDOs = TxPDOData.split()
        if TxPDOs :
            for TxPDO in TxPDOs :
                self.SelectedTxPDOIndex.append(int(TxPDO, 0))

    def LoadDefaultPDOSet(self):
        ReturnData = []
        rx_pdo_entries = self.CommonMethod.GetRxPDOCategory()
        if len(rx_pdo_entries):
            for i in range(len(rx_pdo_entries)):
                if rx_pdo_entries[i]['sm'] is not None:
                    ReturnData.append(rx_pdo_entries[i]['pdo_index'])

        tx_pdo_entries = self.CommonMethod.GetTxPDOCategory()
        if len(tx_pdo_entries):
            for i in range(len(tx_pdo_entries)):
                if tx_pdo_entries[i]['sm'] is not None:
                    ReturnData.append(tx_pdo_entries[i]['pdo_index'])

        if ReturnData :
            return ReturnData
        else :
            return [5632, 6656]
        
    def CTNGenerate_C(self, buildpath, locations):
        current_location = self.GetCurrentLocation()

        location_str = "_".join(map(str, current_location))

        # Open CIA402 node code template file
        plc_cia402node_filepath = os.path.join(os.path.split(__file__)[0],
                                               "plc_cia402node.c")
        plc_cia402node_file = open(plc_cia402node_filepath, 'r')
        plc_cia402node_code = plc_cia402node_file.read()
        plc_cia402node_file.close()
        # HSAHN 150726
        # add "default_variables_retrieve": [], "default_variables_publish": [],
		# As PDO mapping object, it will add auto-complete code.
        # add "modeofop_homing_method", "modeofop_computation_mode" by jblee
        str_completion = {
            "slave_pos": self.GetSlavePos(),
            "location": location_str,
            "MCL_headers": Headers,
            "extern_located_variables_declaration": [],
            "fieldbus_interface_declaration": [],
            "fieldbus_interface_definition": [],
            "entry_variables": [],
            "init_axis_params": [],
            "init_entry_variables": [],
            "default_variables_retrieve": [],
            "default_variables_publish": [],
            "extra_variables_retrieve": [],
            "extra_variables_publish": [],
            "modeofop_homing_method": [],
            "modeofop_computation_mode": []
        }
        
        for blocktype_infos in FIELDBUS_INTERFACE_GLOBAL_INSTANCES:
            texts = {
                "blocktype": blocktype_infos["blocktype"],
                "ucase_blocktype": blocktype_infos["blocktype"].upper(),
                "location": "_".join(map(str, current_location))
            }
            texts["blockname"] = "%(ucase_blocktype)s_%(location)s" % texts
            
            inputs = [{"input_name": "POS", "input_value": str(self.GetSlavePos())},
                      {"input_name": "EXECUTE", "input_value": "__GET_VAR(data__->EXECUTE)"}] +\
                     [{"input_name": input["name"].upper(), 
                       "input_value": "__GET_VAR(data__->%s)" % input["name"].upper()}
                      for input in blocktype_infos["inputs"]]
            input_texts = []
            for input_infos in inputs:
                input_infos.update(texts)
                input_texts.append(BLOCK_INPUT_TEMPLATE % input_infos)
            texts["extract_inputs"] = "\n".join(input_texts)
            
            outputs = [{"output_name": output} for output in ["DONE", "BUSY", "ERROR"]] + \
                      [{"output_name": output["name"].upper()} for output in blocktype_infos["outputs"]]
            output_texts = []
            for output_infos in outputs:
                output_infos.update(texts)
                output_texts.append(BLOCK_OUTPUT_TEMPLATE % output_infos)
            texts["return_outputs"] = "\n".join(output_texts)
            
            str_completion["fieldbus_interface_declaration"].append(
                    BLOCK_FUNCTION_TEMPLATE % texts)
            
            str_completion["fieldbus_interface_definition"].append(
                    BLOCK_FUNTION_DEFINITION_TEMPLATE % texts)

        variables = NODE_VARIABLES[:]

#HSAHN
#2015. 7. 24 PDO Variable
        #if PDO is not selected, use 1st PDO set
        self.LoadPDOSelectData()
        if not self.SelectedRxPDOIndex and not self.SelectedTxPDOIndex :
            self.SelectedPDOIndex = self.LoadDefaultPDOSet()
        else :
            self.SelectedPDOIndex = self.SelectedRxPDOIndex + self.SelectedTxPDOIndex

        add_idx = []
        for i in range(len(ADD_NODE_VARIABLES)):
            add_idx.append(ADD_NODE_VARIABLES[i]['index'])

        self.CommonMethod.RequestPDOInfo()
        pdo_info = self.CommonMethod.GetRxPDOCategory() + self.CommonMethod.GetTxPDOCategory()
        pdo_entry = self.CommonMethod.GetRxPDOInfo() + self.CommonMethod.GetTxPDOInfo()
        list_index = 0
        ModeOfOpFlag = False
        ModeOfOpDisplayFlag = False
        for i in range(len(pdo_info)):
            #if pdo_index is in the SelectedPDOIndex: put the PDO mapping information intto the "used" object
            if pdo_info[i]['pdo_index'] in self.SelectedPDOIndex:
                used = pdo_entry[list_index:list_index + pdo_info[i]['number_of_entry']]
                for used_data in used:
                    # 24672 -> 0x6060, Mode of Operation
                    if used_data['entry_index'] == 24672:
                        ModeOfOpFlag = True
                    # 24673 -> 0x6061, Mode of Operation Display
                    elif used_data["entry_index"] == 24673:
                        ModeOfOpDisplayFlag = True

                    if used_data['entry_index'] in add_idx:
                        idx = add_idx.index(used_data['entry_index'])
                        adder = list([ADD_NODE_VARIABLES[idx]['name'], ADD_NODE_VARIABLES[idx]['index'], \
                                     ADD_NODE_VARIABLES[idx]['sub-index'], ADD_NODE_VARIABLES[idx]['type'], \
                                     ADD_NODE_VARIABLES[idx]['direction']])
                        variables.append(adder)
                        if ADD_NODE_VARIABLES[idx]['direction'] == "Q":                           
                            parsed_string = ADD_NODE_VARIABLES[idx]['name'].replace("Target", "")
                            # add jblee
                            check_q_data = "    *(AxsPub.Target%s) = AxsPub.axis->Raw%sSetPoint;" %(parsed_string, parsed_string)
                            if check_q_data not in str_completion["default_variables_publish"]:
                                str_completion["default_variables_publish"].append(check_q_data)
                        elif ADD_NODE_VARIABLES[idx]['direction'] == "I":
                            parsed_string = ADD_NODE_VARIABLES[idx]['name'].replace("Actual", "")
                            # add jblee
                            check_i_data = "    AxsPub.axis->ActualRaw%s = *(AxsPub.Actual%s);" %(parsed_string, parsed_string)
                            if check_i_data not in str_completion["default_variables_retrieve"]:
                                str_completion["default_variables_retrieve"].append(check_i_data)
            list_index += pdo_info[i]['number_of_entry']
#HSAHN END

        params = self.CTNParams[1].getElementInfos(self.CTNParams[0])
        for param in params["children"]:
            if param["name"] in EXTRA_NODE_VARIABLES_DICT:
                if param["value"]:
                    extra_variables = EXTRA_NODE_VARIABLES_DICT.get(param["name"])
                    for variable_infos in extra_variables:
                        var_infos = {
                            "location": location_str,
                            "name": variable_infos["description"][0]
                        }
                        variables.append(variable_infos["description"])
                        retrieve_template = variable_infos.get("retrieve", DEFAULT_RETRIEVE)
                        publish_template = variable_infos.get("publish", DEFAULT_PUBLISH)
                        
                        if retrieve_template is not None:
                            str_completion["extra_variables_retrieve"].append(
                                retrieve_template % var_infos)
                        if publish_template is not None:
                            str_completion["extra_variables_publish"].append(
                                publish_template % var_infos)

            #elif param["value"] is not None:
            if param["value"] is not None:
                param_infos = {
                    "location": location_str,
                    "param_name": param["name"],
                }
                if param["type"] == "boolean":
                    param_infos["param_value"] = {True: "1", False: "0"}[param["value"]]
                    param_infos["param_name"] = param["name"].replace("Enable", "") + "Enabled"
                    if param["value"] == False:
                        continue
                else:
                    param_infos["param_value"] = str(param["value"])
                # param_name = param_name.replace("Enable", "") + "Enabled"
                str_completion["init_axis_params"].append(
                    "        __CIA402Node_%(location)s.axis->%(param_name)s = %(param_value)s;" % param_infos)
        
        check_variable = []
        for variable in variables:
            # add jblee
            if variable in check_variable:
                continue

            var_infos = dict(zip(["name", "index", "subindex", "var_type", "dir"], variable))
            var_infos["location"] = location_str
            var_infos["var_size"] = self.GetSizeOfType(var_infos["var_type"])
            var_infos["var_name"] = "__%(dir)s%(var_size)s%(location)s_%(index)d_%(subindex)d" % var_infos

            # add jblee
            if var_infos["index"] in [24672] and ModeOfOpFlag:
                str_completion["modeofop_homing_method"].append(MODEOFOP_HOMING_METHOD_TEMPLATE)
                str_completion["modeofop_computation_mode"].append(MODEOFOP_COMPUTATION_MODE_TEMPLATE)

            # add jblee
            if var_infos["index"] in [24672, 24673] and (not ModeOfOpFlag or not ModeOfOpDisplayFlag):
                continue

            str_completion["extern_located_variables_declaration"].append(
                    "IEC_%(var_type)s *%(var_name)s;" % var_infos)
            str_completion["entry_variables"].append(
                    "    IEC_%(var_type)s *%(name)s;" % var_infos)
            str_completion["init_entry_variables"].append(
                    "    __CIA402Node_%(location)s.%(name)s = %(var_name)s;" % var_infos)
            
            self.CTNParent.FileGenerator.DeclareVariable(
                    self.GetSlavePos(), var_infos["index"], var_infos["subindex"], 
                    var_infos["var_type"], var_infos["dir"], var_infos["var_name"])

            # add jblee
            check_variable.append(variable)
        
        for element in ["extern_located_variables_declaration", 
                        "fieldbus_interface_declaration",
                        "fieldbus_interface_definition",
                        "entry_variables", 
                        "init_axis_params", 
                        "init_entry_variables",
                        "default_variables_retrieve",
                        "default_variables_publish",
                        "extra_variables_retrieve",
                        "extra_variables_publish",
                        "modeofop_homing_method",
                        "modeofop_computation_mode"]:
            str_completion[element] = "\n".join(str_completion[element])
        
        Gen_CIA402Nodefile_path = os.path.join(buildpath, "cia402node_%s.c"%location_str)
        cia402nodefile = open(Gen_CIA402Nodefile_path, 'w')
        cia402nodefile.write(plc_cia402node_code % str_completion)
        cia402nodefile.close()

        return [(Gen_CIA402Nodefile_path, '"-I%s"' % os.path.abspath(self.GetCTRoot().GetIECLibPath()))], "", True
