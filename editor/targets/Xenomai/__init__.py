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
from ..toolchain_gcc import toolchain_gcc


class Xenomai_target(toolchain_gcc):
    dlopen_prefix = "./"
    extension = ".so"

    def getXenoConfig(self, flagsname):
        """ Get xeno-config from target parameters """
        xeno_config = self.CTRInstance.GetTarget().getcontent().getXenoConfig()
        if xeno_config:
            from util.ProcessLogger import ProcessLogger
            status, result, _err_result = ProcessLogger(self.CTRInstance.logger,
                                                        xeno_config + " --skin=posix --skin=alchemy --no-auto-init --"+flagsname,
                                                        no_stdout=True).spin()
            if status:
                self.CTRInstance.logger.write_error(_("Unable to get Xenomai's %s \n") % flagsname)
            return [result.strip()]
        return []

    def getBuilderLDFLAGS(self):
        xeno_ldflags = self.getXenoConfig("ldflags")
        return toolchain_gcc.getBuilderLDFLAGS(self) + xeno_ldflags + ["-shared"]

    def getBuilderCFLAGS(self):
        xeno_cflags = self.getXenoConfig("cflags")
        return toolchain_gcc.getBuilderCFLAGS(self) + xeno_cflags + ["-fPIC"]
