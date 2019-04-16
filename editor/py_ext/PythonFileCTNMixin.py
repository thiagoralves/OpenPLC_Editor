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
import re
from builtins import str as text

import util.paths as paths
from xmlclass import GenerateParserFromXSD

from CodeFileTreeNode import CodeFile
from py_ext.PythonEditor import PythonEditor


class PythonFileCTNMixin(CodeFile):

    CODEFILE_NAME = "PyFile"
    SECTIONS_NAMES = [
        "globals",
        "init",
        "cleanup",
        "start",
        "stop"]
    EditorType = PythonEditor

    def __init__(self):
        CodeFile.__init__(self)

        filepath = self.PythonFileName()

        if os.path.isfile(filepath):
            PythonParser = GenerateParserFromXSD(paths.AbsNeighbourFile(__file__, "py_ext_xsd.xsd"))

            xmlfile = open(filepath, 'r')
            pythonfile_xml = xmlfile.read()
            xmlfile.close()

            pythonfile_xml = pythonfile_xml.replace(
                'xmlns="http://www.w3.org/2001/XMLSchema"',
                'xmlns:xhtml="http://www.w3.org/1999/xhtml"')
            for cre, repl in [
                    (re.compile(r"(?<!<xhtml:p>)(?:<!\[CDATA\[)"), "<xhtml:p><![CDATA["),
                    (re.compile(r"(?:]]>)(?!</xhtml:p>)"), "]]></xhtml:p>")]:
                pythonfile_xml = cre.sub(repl, pythonfile_xml)

            try:
                python_code, error = PythonParser.LoadXMLString(pythonfile_xml)
                if error is None:
                    self.CodeFile.globals.setanyText(python_code.getanyText())
                    os.remove(filepath)
                    self.CreateCodeFileBuffer(False)
                    self.OnCTNSave()
            except Exception as exc:
                error = text(exc)

            if error is not None:
                self.GetCTRoot().logger.write_error(
                    _("Couldn't import old %s file.") % self.CTNName())

    def CodeFileName(self):
        return os.path.join(self.CTNPath(), "pyfile.xml")

    def PythonFileName(self):
        return os.path.join(self.CTNPath(), "py_ext.xml")

    PreSectionsTexts = {}
    PostSectionsTexts = {}

    def GetSection(self, section):
        return self.PreSectionsTexts.get(section, "") + "\n" + \
               getattr(self.CodeFile, section).getanyText() + "\n" + \
               self.PostSectionsTexts.get(section, "")

    def CTNGenerate_C(self, buildpath, locations):
        # location string for that CTN
        location_str = "_".join(map(str, self.GetCurrentLocation()))
        configname = self.GetCTRoot().GetProjectConfigNames()[0]

        def _onchangecode(var):
            return '"' + var.getonchange() + \
                "('" + var.getname() + "')\"" \
                if var.getonchange() else '""'

        def _onchange(var):
            return repr(var.getonchange()) \
                if var.getonchange() else None

        pyextname = self.CTNName()
        varinfos = map(
            lambda variable: {
                "name": variable.getname(),
                "desc": repr(variable.getdesc()),
                "onchangecode": _onchangecode(variable),
                "onchange": _onchange(variable),
                "opts": repr(variable.getopts()),
                "configname": configname.upper(),
                "uppername": variable.getname().upper(),
                "IECtype": variable.gettype(),
                "initial": repr(variable.getinitial()),
                "pyextname": pyextname
            },
            self.CodeFile.variables.variable)
        # python side PLC global variables access stub
        globalstubs = "\n".join([
            """\
_%(name)s_ctype, _%(name)s_unpack, _%(name)s_pack = \\
    TypeTranslator["%(IECtype)s"]
_PySafeGetPLCGlob_%(name)s = PLCBinary.__SafeGetPLCGlob_%(name)s
_PySafeGetPLCGlob_%(name)s.restype = None
_PySafeGetPLCGlob_%(name)s.argtypes = [ctypes.POINTER(_%(name)s_ctype)]
_PySafeSetPLCGlob_%(name)s = PLCBinary.__SafeSetPLCGlob_%(name)s
_PySafeSetPLCGlob_%(name)s.restype = None
_PySafeSetPLCGlob_%(name)s.argtypes = [ctypes.POINTER(_%(name)s_ctype)]
_%(pyextname)sGlobalsDesc.append((
    "%(name)s",
    "%(IECtype)s",
    %(initial)s,
    %(desc)s,
    %(onchange)s,
    %(opts)s))
""" % varinfo for varinfo in varinfos])

        # Runtime calls (start, stop, init, and cleanup)
        rtcalls = ""
        for section in self.SECTIONS_NAMES:
            if section != "globals":
                rtcalls += "def _runtime_%s_%s():\n" % (location_str, section)
                sectiontext = self.GetSection(section).strip()
                if sectiontext:
                    rtcalls += '    ' + \
                        sectiontext.replace('\n', '\n    ')+"\n\n"
                else:
                    rtcalls += "    pass\n\n"

        globalsection = self.GetSection("globals")

        loc_dict = {
            "pyextname": pyextname,
            "globalstubs": globalstubs,
            "globalsection": globalsection,
            "rtcalls": rtcalls,
        }

        PyFileContent = """\
#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Code generated by Beremiz python mixin confnode
##

## Code for PLC global variable access
from runtime.typemapping import TypeTranslator
import ctypes
_%(pyextname)sGlobalsDesc = []
__ext_name__ = "%(pyextname)s"
PLCGlobalsDesc.append(( "%(pyextname)s" , _%(pyextname)sGlobalsDesc ))
%(globalstubs)s

## User code in "global" scope
%(globalsection)s

## Beremiz python runtime calls
%(rtcalls)s

del __ext_name__

""" % loc_dict

        # write generated content to python file
        runtimefile_path = os.path.join(buildpath,
                                        "runtime_%s.py" % location_str)
        runtimefile = open(runtimefile_path, 'w')
        runtimefile.write(PyFileContent.encode('utf-8'))
        runtimefile.close()

        # C code for safe global variables access

        vardecfmt = """\
extern  __IEC_%(IECtype)s_t %(configname)s__%(uppername)s;
IEC_%(IECtype)s __%(name)s_rbuffer = __INIT_%(IECtype)s;
IEC_%(IECtype)s __%(name)s_wbuffer;
long __%(name)s_rlock = 0;
long __%(name)s_wlock = 0;
int __%(name)s_wbuffer_written = 0;
void __SafeGetPLCGlob_%(name)s(IEC_%(IECtype)s *pvalue){
    while(AtomicCompareExchange(&__%(name)s_rlock, 0, 1));
    *pvalue = __%(name)s_rbuffer;
    AtomicCompareExchange((long*)&__%(name)s_rlock, 1, 0);
}
void __SafeSetPLCGlob_%(name)s(IEC_%(IECtype)s *value){
    while(AtomicCompareExchange(&__%(name)s_wlock, 0, 1));
    __%(name)s_wbuffer = *value;
    __%(name)s_wbuffer_written = 1;
    AtomicCompareExchange((long*)&__%(name)s_wlock, 1, 0);
}

"""

        vardeconchangefmt = """\
PYTHON_POLL* __%(name)s_notifier;
"""

        varretfmt = """\
    if(!AtomicCompareExchange(&__%(name)s_wlock, 0, 1)){
        if(__%(name)s_wbuffer_written == 1){
            %(configname)s__%(uppername)s.value = __%(name)s_wbuffer;
            __%(name)s_wbuffer_written = 0;
        }
        AtomicCompareExchange((long*)&__%(name)s_wlock, 1, 0);
    }
"""
        varpubfmt = """\
    if(!AtomicCompareExchange(&__%(name)s_rlock, 0, 1)){
        __%(name)s_rbuffer = __GET_VAR(%(configname)s__%(uppername)s);
        AtomicCompareExchange((long*)&__%(name)s_rlock, 1, 0);
    }
"""

        varpubonchangefmt = """\
    if(!AtomicCompareExchange(&__%(name)s_rlock, 0, 1)){
        IEC_%(IECtype)s tmp = __GET_VAR(%(configname)s__%(uppername)s);
        if(__%(name)s_rbuffer != tmp){
            __%(name)s_rbuffer = %(configname)s__%(uppername)s.value;
            PYTHON_POLL_body__(__%(name)s_notifier);
        }
        AtomicCompareExchange((long*)&__%(name)s_rlock, 1, 0);
    }
"""
        varinitonchangefmt = """\
    __%(name)s_notifier = __GET_GLOBAL_ON%(uppername)sCHANGE();
    __SET_VAR(__%(name)s_notifier->,TRIG,,__BOOL_LITERAL(TRUE));
    __SET_VAR(__%(name)s_notifier->,CODE,,__STRING_LITERAL(%(onchangelen)d,%(onchangecode)s));
"""
        vardec = "\n".join([(vardecfmt + vardeconchangefmt
                             if varinfo["onchange"] else vardecfmt) % varinfo
                            for varinfo in varinfos])
        varret = "\n".join([varretfmt % varinfo for varinfo in varinfos])
        varpub = "\n".join([(varpubonchangefmt if varinfo["onchange"] else
                             varpubfmt) % varinfo
                            for varinfo in varinfos])
        varinit = "\n".join([varinitonchangefmt %
                             dict(onchangelen=len(varinfo["onchangecode"]), **varinfo)
                             for varinfo in varinfos if varinfo["onchange"]])

        loc_dict = {
            "vardec": vardec,
            "varinit": varinit,
            "varret": varret,
            "varpub": varpub,
            "location_str": location_str,
        }

        # TODO : use config name obtained from model instead of default
        # "config.h". User cannot change config name, but project imported
        # or created in older beremiz vesion could use different name.
        PyCFileContent = """\
/*
 * Code generated by Beremiz py_ext confnode
 * for safe global variables access
 */
#include "iec_types_all.h"
#include "POUS.h"
#include "config.h"
#include "beremiz.h"

/* User variables reference */
%(vardec)s

/* Beremiz confnode functions */
int __init_%(location_str)s(int argc,char **argv){
%(varinit)s
    return 0;
}

void __cleanup_%(location_str)s(void){
}

void __retrieve_%(location_str)s(void){
%(varret)s
}

void __publish_%(location_str)s(void){
%(varpub)s
}
""" % loc_dict

        Gen_PyCfile_path = os.path.join(buildpath, "PyCFile_%s.c" % location_str)
        pycfile = open(Gen_PyCfile_path, 'w')
        pycfile.write(PyCFileContent)
        pycfile.close()

        matiec_CFLAGS = '"-I%s"' % os.path.abspath(
            self.GetCTRoot().GetIECLibPath())

        return ([(Gen_PyCfile_path, matiec_CFLAGS)],
                "",
                True,
                ("runtime_%s.py" % location_str, open(runtimefile_path, "rb")))
