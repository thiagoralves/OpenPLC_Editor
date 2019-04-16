#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov
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
import os
from POULibrary import POULibrary
from py_ext.PythonFileCTNMixin import PythonFileCTNMixin
import util.paths as paths


class PythonLibrary(POULibrary):
    def GetLibraryPath(self):
        return paths.AbsNeighbourFile(__file__, "pous.xml")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):

        plc_python_filepath = paths.AbsNeighbourFile(__file__, "plc_python.c")
        plc_python_file = open(plc_python_filepath, 'r')
        plc_python_code = plc_python_file.read()
        plc_python_file.close()
        python_eval_fb_list = []
        for v in varlist:
            if v["vartype"] == "FB" and v["type"] in ["PYTHON_EVAL",
                                                      "PYTHON_POLL"]:
                python_eval_fb_list.append(v)
        python_eval_fb_count = max(1, len(python_eval_fb_list))

        # prepare python code
        plc_python_code = plc_python_code % {
            "python_eval_fb_count": python_eval_fb_count}

        Gen_Pythonfile_path = os.path.join(buildpath, "py_ext.c")
        pythonfile = open(Gen_Pythonfile_path, 'w')
        pythonfile.write(plc_python_code)
        pythonfile.close()

        return (["py_ext"], [(Gen_Pythonfile_path, IECCFLAGS)], True), ""


class PythonFile(PythonFileCTNMixin):

    def GetIconName(self):
        return "Pyfile"
