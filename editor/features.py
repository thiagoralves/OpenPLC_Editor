#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
#
# Copyright (C) 2007: Laurent BESSARD
# Copyright (C) 2007-2018: Edouard TISSERANT
#
# See COPYING file for copyrights details.

libraries = [
    ('Native', 'NativeLib.NativeLibrary', True),
    ('Python', 'py_ext.PythonLibrary', True),
    ('Etherlab', 'etherlab.EthercatMaster.EtherlabLibrary', False),
    ('SVGHMI', 'svghmi.SVGHMILibrary', False)]

catalog = [('c_ext', _('C extension'), _('Add C code accessing located variables synchronously'), 'c_ext.CFile')]
"""('opcua', _('OPC-UA client'), _('Map OPC-UA server as located variables'), 'opc_ua.OPCUAClient'),
    ('canfestival', _('CANopen support'), _('Map located variables over CANopen'), 'canfestival.canfestival.RootClass'),
    ('bacnet', _('Bacnet support'), _('Map located variables over Bacnet'), 'bacnet.bacnet.RootClass'),
    ('etherlab', _('EtherCAT master'), _('Map located variables over EtherCAT'), 'etherlab.etherlab.RootClass'),
    ('modbus', _('Modbus support'), _('Map located variables over Modbus'), 'modbus.modbus.RootClass'),
    ('c_ext', _('C extension'), _('Add C code accessing located variables synchronously'), 'c_ext.CFile'),
    ('py_ext', _('Python file'), _('Add Python code executed asynchronously'), 'py_ext.PythonFile'),
    ('wxglade_hmi', _('WxGlade GUI'), _('Add a simple WxGlade based GUI.'), 'wxglade_hmi.WxGladeHMI'),
    ('svghmi', _('SVGHMI'), _('SVG based HMI'), 'svghmi.SVGHMI')]"""

file_editors = []