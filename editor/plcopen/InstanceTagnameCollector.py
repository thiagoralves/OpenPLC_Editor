#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Beremiz.
# See COPYING file for copyrights details.

from __future__ import absolute_import
from plcopen.XSLTModelQuery import XSLTModelQuery
from plcopen.types_enums import *


class InstanceTagName(object):
    """Helpers object for generating instance tagname"""

    def __init__(self):
        self.TagName = None

    def GetTagName(self):
        return self.TagName

    def ConfigTagName(self, context, *args):
        self.TagName = ComputeConfigurationName(args[0][0])

    def ResourceTagName(self, context, *args):
        self.TagName = ComputeConfigurationResourceName(args[0][0], args[1][0])

    def PouTagName(self, context, *args):
        self.TagName = ComputePouName(args[0][0])

    def ActionTagName(self, context, *args):
        self.TagName = ComputePouActionName(args[0][0], args[0][1])

    def TransitionTagName(self, context, *args):
        self.TagName = ComputePouTransitionName(args[0][0], args[0][1])


class InstanceTagnameCollector(XSLTModelQuery):
    """ object for collecting instances path list"""
    def __init__(self, controller):
        XSLTModelQuery.__init__(self,
                                controller,
                                "instance_tagname.xslt",
                                [(name, self.FactoryCaller(name))
                                 for name in ["ConfigTagName",
                                              "ResourceTagName",
                                              "PouTagName",
                                              "ActionTagName",
                                              "TransitionTagName"]])

    def FactoryCaller(self, funcname):
        def CallFactory(*args):
            return getattr(self.factory, funcname)(*args)
        return CallFactory

    def Collect(self, root, debug, instance_path):
        self.factory = InstanceTagName()
        self._process_xslt(root, debug, instance_path=instance_path)
        res = self.factory.GetTagName()
        self.factory = None
        return res
