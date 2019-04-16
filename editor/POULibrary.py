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
from weakref import ref


class POULibrary(object):
    def __init__(self, CTR, LibName, TypeStack):
        from PLCControler import PLCControler
        self.CTR = ref(CTR)
        self.LibName = LibName
        self.LibraryControler = PLCControler()
        self.LibraryControler.OpenXMLFile(self.GetLibraryPath())
        self.LibraryControler.ClearConfNodeTypes()
        self.LibraryControler.AddConfNodeTypesList(TypeStack)
        self.program = None

    def GetSTCode(self):
        if not self.program:
            self.program = self.LibraryControler.GenerateProgram()[0]+"\n"
        return self.program

    def GetName(self):
        return self.LibName

    def GetCTR(self):
        return self.CTR()

    def GetTypes(self):
        return {"name": self.GetName(), "types": self.LibraryControler.Project}

    def GetLibraryPath(self):
        raise Exception("Not implemented")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):
        # Pure python or IEC libs doesn't produce C code
        return ((""), [], False), ""


def SimplePOULibraryFactory(path):
    class SimplePOULibrary(POULibrary):
        def GetLibraryPath(self):
            return path
    return SimplePOULibrary
