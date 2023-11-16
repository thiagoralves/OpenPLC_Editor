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



import os
from POULibrary import POULibrary
from py_ext.PythonFileCTNMixin import PythonFileCTNMixin
import util.paths as paths

pyext_python_lib_code = """

import csv
from collections import OrderedDict

csv_int_files = {}
def CSVRdInt(fname, rowidx, colidx):
    \"\"\"
    Return value at row/column pointed by integer indexes
    Assumes data starts at first row and first column, no headers.
    \"\"\"
    global csv_int_files
    data = csv_int_files.get(fname, None)
    if data is None:
        data = list()
        try:
            csvfile = open(fname, 'rb')
        except IOError:
            return "#FILE_NOT_FOUND"
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            for row in reader:
                data.append(row)
        except csv.Error:
            return "#CSV_ERROR"
        finally:
            csvfile.close()
        csv_int_files[fname] = data
    
    try:
        row = data[rowidx]
    except IndexError:
        return "#ROW_NOT_FOUND"

    try:
        return row[colidx]
    except IndexError:
        return "#COL_NOT_FOUND"


csv_str_files = {}
def CSVRdStr(fname, rowname, colname):
    \"\"\"
    Return value at row/column pointed by a pair of names as string
    Assumes first row is column headers and first column is row name.
    \"\"\"
    global csv_str_files
    entry = csv_str_files.get(fname, None)
    if entry is None:
        data = dict()
        try:
            csvfile = open(fname, 'rb')
        except IOError:
            return "#FILE_NOT_FOUND"
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)
            headers = dict([(name, index) for index, name in enumerate(reader.next()[1:])])
            for row in reader:
                data[row[0]] = row[1:]
        except csv.Error:
            return "#CSV_ERROR"
        finally:
            csvfile.close()
        csv_str_files[fname] = (headers, data)
    else:
        headers, data = entry
    
    try:
        row = data[rowname]
    except KeyError:
        return "#ROW_NOT_FOUND"

    try:
        colidx = headers[colname]
    except KeyError:
        return "#COL_NOT_FOUND"

    try:
        return row[colidx]
    except IndexError:
        return "#COL_NOT_FOUND"

def pyext_csv_reload():
    global csv_int_files, csv_str_files
    csv_int_files.clear()
    csv_str_files.clear()

"""

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

        runtimefile_path = os.path.join(buildpath, "runtime_00_pyext.py")
        runtimefile = open(runtimefile_path, 'w')
        runtimefile.write(pyext_python_lib_code)
        runtimefile.close()
        return ((["py_ext"], [(Gen_Pythonfile_path, IECCFLAGS)], True), "",
                ("runtime_00_pyext.py", open(runtimefile_path, "rb")))



class PythonFile(PythonFileCTNMixin):

    def GetIconName(self):
        return "Pyfile"
