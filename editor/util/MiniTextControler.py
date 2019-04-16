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

"""
Minimal tab controller for a simple text editor
"""


from __future__ import absolute_import
import os


class MiniTextControler(object):

    def __init__(self, filepath, controller):
        self.FilePath = filepath
        self.BaseController = controller

    def __del__(self):
        self.BaseController = None

    def CTNFullName(self):
        return ""

    def SetEditedElementText(self, tagname, text):
        file = open(self.FilePath, "w")
        file.write(text)
        file.close()

    def GetEditedElementText(self, tagname, debug=False):
        if os.path.isfile(self.FilePath):
            file = open(self.FilePath, "r")
            text = file.read()
            file.close()
            return text
        return ""

    def GetEditedElementInterfaceVars(self, tagname, tree=False, debug=False):
        return []

    def GetEditedElementType(self, tagname, debug=False):
        return "program"

    def GetBlockType(self, type, inputs=None, debug=False):
        return self.BaseController.GetBlockType(type, inputs, debug)

    def GetBlockTypes(self, tagname="", debug=False):
        return self.BaseController.GetBlockTypes(tagname, debug)

    def GetDataTypes(self, tagname="", basetypes=True, only_locatables=False, debug=False):
        return self.BaseController.GetDataTypes(tagname, basetypes, only_locatables, debug)

    def GetEnumeratedDataValues(self, debug=False):
        return self.BaseController.GetEnumeratedDataValues(debug)

    def StartBuffering(self):
        pass

    def EndBuffering(self):
        pass

    def BufferProject(self):
        pass
