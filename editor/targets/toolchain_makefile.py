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
import os
import re
import operator
import hashlib
from functools import reduce
from util.ProcessLogger import ProcessLogger


includes_re = re.compile(r'\s*#include\s*["<]([^">]*)[">].*')


class toolchain_makefile(object):
    def __init__(self, CTRInstance):
        self.CTRInstance = CTRInstance
        self.md5key = None
        self.buildpath = None
        self.SetBuildPath(self.CTRInstance._getBuildPath())

    def SetBuildPath(self, buildpath):
        if self.buildpath != buildpath:
            self.buildpath = buildpath
            self.md5key = None

    def GetBinaryPath(self):
        return None

    def _GetMD5FileName(self):
        return os.path.join(self.buildpath, "lastbuildPLC.md5")

    def ResetBinaryMD5(self):
        self.md5key = None
        try:
            os.remove(self._GetMD5FileName())
        except Exception:
            pass

    def GetBinaryMD5(self):
        if self.md5key is not None:
            return self.md5key
        else:
            try:
                return open(self._GetMD5FileName(), "r").read()
            except IOError:
                return None

    def concat_deps(self, bn):
        # read source
        src = open(os.path.join(self.buildpath, bn), "r").read()
        # update direct dependencies
        deps = []
        for l in src.splitlines():
            res = includes_re.match(l)
            if res is not None:
                depfn = res.groups()[0]
                if os.path.exists(os.path.join(self.buildpath, depfn)):
                    # print bn + " depends on "+depfn
                    deps.append(depfn)
        # recurse through deps
        # TODO detect cicular deps.
        return reduce(operator.concat, map(self.concat_deps, deps), src)

    def build(self):
        srcfiles = []
        cflags = []
        wholesrcdata = ""
        for _Location, CFilesAndCFLAGS, _DoCalls in self.CTRInstance.LocationCFilesAndCFLAGS:
            # Get CFiles list to give it to makefile
            for CFile, CFLAGS in CFilesAndCFLAGS:
                CFileName = os.path.basename(CFile)
                wholesrcdata += self.concat_deps(CFileName)
                srcfiles.append(CFileName)
                if CFLAGS not in cflags:
                    cflags.append(CFLAGS)

        oldmd5 = self.md5key
        self.md5key = hashlib.md5(wholesrcdata).hexdigest()

        # Store new PLC filename based on md5 key
        f = open(self._GetMD5FileName(), "w")
        f.write(self.md5key)
        f.close()

        if oldmd5 != self.md5key:
            target = self.CTRInstance.GetTarget().getcontent()
            beremizcommand = {"src": ' '.join(srcfiles),
                              "cflags": ' '.join(cflags),
                              "md5": self.md5key,
                              "buildpath": self.buildpath}

            # clean sequence of multiple whitespaces
            cmd = re.sub(r"[ ]+", " ", target.getCommand().strip())

            command = [token % beremizcommand for token in cmd.split(' ')]

            # Call Makefile to build PLC code and link it with target specific code
            status, _result, _err_result = ProcessLogger(self.CTRInstance.logger,
                                                         command).spin()
            if status:
                self.md5key = None
                self.CTRInstance.logger.write_error(_("C compilation failed.\n"))
                return False
            return True
        else:
            self.CTRInstance.logger.write(_("Source didn't change, no build.\n"))
            return True
