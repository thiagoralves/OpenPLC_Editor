#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Beremiz.
# See COPYING file for copyrights details.

from __future__ import absolute_import
from plcopen.XSLTModelQuery import XSLTModelQuery


class InstancesPathCollector(XSLTModelQuery):
    """ object for collecting instances path list"""
    def __init__(self, controller):
        self.Instances = []
        XSLTModelQuery.__init__(self,
                                controller,
                                "instances_path.xslt",
                                [("AddInstance", self.AddInstance)])

    def AddInstance(self, context, *args):
        self.Instances.append(args[0][0])

    def Collect(self, root, name, debug):
        self._process_xslt(root, debug, instance_type=name)
        res = self.Instances
        self.Instances = []
        return res
