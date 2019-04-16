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

    def CTNGenerate_C(self, buildpath, locations):
        current_location = self.GetCurrentLocation()

        location_str = "_".join(map(str, current_location))
        slave_pos = self.GetSlavePos()

        # Open CIA402 node code template file
        plc_cia402node_filepath = os.path.join(os.path.split(__file__)[0],
                                               "plc_cia402node.c")
        plc_cia402node_file = open(plc_cia402node_filepath, 'r')
        plc_cia402node_code = plc_cia402node_file.read()
        plc_cia402node_file.close()

        # Init list of generated strings for each code template file section
        fieldbus_interface_declaration = []
        fieldbus_interface_definition = []
        init_axis_params = []
        extra_variables_retrieve = []
        extra_variables_publish = []
        extern_located_variables_declaration = []
        entry_variables = []
        init_entry_variables = []

        # Fieldbus interface code sections
        for blocktype_infos in FIELDBUS_INTERFACE_GLOBAL_INSTANCES:
            blocktype = blocktype_infos["blocktype"]
            ucase_blocktype = blocktype.upper()
            blockname = "_".join([ucase_blocktype, location_str])

            extract_inputs = "\n".join([
                """\
                __SET_VAR(%s->, %s,, %s);""" % (blockname, input_name, input_value)
                for (input_name, input_value) in
                [("EXECUTE", "__GET_VAR(data__->EXECUTE)")] + [
                    (input["name"].upper(),
                     "__GET_VAR(data__->%s)" % input["name"].upper())
                    for input in blocktype_infos["inputs"]
                ]])

            return_outputs = "\n".join([
                """\
                __SET_VAR(data__->,%(output_name)s,,
                __GET_VAR(%(blockname)s->%(output_name)s));""" % {
                    "output_name": output_name,
                    "blockname": blockname
                }
                for output_name in ["DONE", "BUSY", "ERROR"] + [
                    output["name"].upper()
                    for output in blocktype_infos["outputs"]]
            ])

            loc_dict = {
                "ucase_blocktype": ucase_blocktype,
                "blocktype": blocktype,
                "blockname": blockname,
                "location_str": location_str,
                "extract_inputs": extract_inputs,
                "return_outputs": return_outputs,
            }

            fieldbus_interface_declaration.append("""
extern void ETHERLAB%(ucase_blocktype)s_body__(ETHERLAB%(ucase_blocktype)s* data__);
void __%(blocktype)s_%(location_str)s(MC_%(ucase_blocktype)s *data__) {
__DECLARE_GLOBAL_PROTOTYPE(ETHERLAB%(ucase_blocktype)s, %(blockname)s);
ETHERLAB%(ucase_blocktype)s* %(blockname)s = __GET_GLOBAL_%(blockname)s();
__SET_VAR(%(blockname)s->, POS,, AxsPub.axis->NetworkPosition);
%(extract_inputs)s
ETHERLAB%(ucase_blocktype)s_body__(%(blockname)s);
%(return_outputs)s
}""" % loc_dict)

            fieldbus_interface_definition.append("""\
        AxsPub.axis->__mcl_func_MC_%(blocktype)s = __%(blocktype)s_%(location_str)s;\
""" % loc_dict)

        # Get a copy list of default variables to map
        variables = NODE_VARIABLES[:]

        # Set AxisRef public struct members value
        node_params = self.CTNParams[1].getElementInfos(self.CTNParams[0])
        for param in node_params["children"]:
            param_name = param["name"]

            # Param is optional variables section enable flag
            extra_node_variable_infos = EXTRA_NODE_VARIABLES_DICT.get(param_name)
            if extra_node_variable_infos is not None:
                param_name = param_name.replace("Enable", "") + "Enabled"

                if not param["value"]:
                    continue

                # Optional variables section is enabled
                for variable_infos in extra_node_variable_infos:
                    var_name = variable_infos["description"][0]

                    # Add each variables defined in section description to the
                    # list of variables to map
                    variables.append(variable_infos["description"])

                    # Add code to publish or retrive variable
                    coded = [
                        ("retrieve",
                         extra_variables_retrieve,
                         "    AxsPub.axis->%(var_name)s = *(AxsPub.%(var_name)s);"),
                        ("publish",
                         extra_variables_publish,
                         "    *(AxsPub.%(var_name)s) = AxsPub.axis->%(var_name)s;")
                    ]
                    for var_exchange_dir, _str_list, default_template in coded:
                        template = variable_infos.get(var_exchange_dir, default_template)
                        if template is not None:
                            extra_variables_publish.append(template % locals())

            # Set AxisRef public struct member value if defined
            if param["value"] is not None:
                param_value = ({True: "1", False: "0"}[param["value"]]
                               if param["type"] == "boolean"
                               else str(param["value"]))

                init_axis_params.append("""\
                AxsPub.axis->%(param_name)s = %(param_value)s;""" % {
                    "param_value": param_value,
                    "param_name": param_name,
                })

        # Add each variable in list of variables to map to master list of
        # variables to add to network configuration
        for name, index, subindex, var_type, dir in variables:
            var_size = self.GetSizeOfType(var_type)
            loc_dict = {
                "var_size": var_size,
                "var_type": var_type,
                "name:": name,
                "location_str": location_str,
                "index": index,
                "subindex": subindex,
            }
            var_name = """\
__%(dir)s%(var_size)s%(location_str)s_%(index)d_%(subindex)d""" % loc_dict
            loc_dict["var_name"] = var_name

            extern_located_variables_declaration.append(
                "IEC_%(var_type)s *%(var_name)s;" % loc_dict)
            entry_variables.append(
                "    IEC_%(var_type)s *%(name)s;" % loc_dict)
            init_entry_variables.append(
                "    AxsPub.%(name)s = %(var_name)s;" % loc_dict)

            self.CTNParent.FileGenerator.DeclareVariable(
                slave_pos, index, subindex, var_type, dir, var_name)

        # Add newline between string in list of generated strings for sections
        [fieldbus_interface_declaration, fieldbus_interface_definition,
         init_axis_params, extra_variables_retrieve, extra_variables_publish,
         extern_located_variables_declaration, entry_variables,
         init_entry_variables] = map("\n".join, [
             fieldbus_interface_declaration, fieldbus_interface_definition,
             init_axis_params, extra_variables_retrieve, extra_variables_publish,
             extern_located_variables_declaration, entry_variables,
             init_entry_variables])

        # Write generated content to CIA402 node file
        Gen_CIA402Nodefile_path = os.path.join(buildpath,
                                               "cia402node_%s.c" % location_str)
        cia402nodefile = open(Gen_CIA402Nodefile_path, 'w')
        cia402nodefile.write(plc_cia402node_code % locals())
        cia402nodefile.close()

        return [(Gen_CIA402Nodefile_path, '"-I%s"' % os.path.abspath(self.GetCTRoot().GetIECLibPath()))], "", True
