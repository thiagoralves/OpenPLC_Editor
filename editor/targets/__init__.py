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

# Package initialisation


"""
Beremiz Targets

- Target are python packages, containing at least one "XSD" file
- Target class may inherit from a toolchain_(toolchainname)
- The target folder's name must match to name define in the XSD for TargetType
"""
import sys
from os import listdir, path

import util.paths as paths

_base_path = paths.AbsDir(__file__)
sys.path.append(_base_path)

def _GetLocalTargetClassFactory(name):
    m = __import__(name, globals(), locals())
    return lambda: getattr(m, name + "_target")


targets = dict([(name, {"xsd":   path.join(_base_path, name, "XSD"),
                        "class": _GetLocalTargetClassFactory(name),
                        "code":  {fname: path.join(_base_path, name, fname)
                                  for fname in listdir(path.join(_base_path, name))
                                  if (fname.startswith("plc_%s_main" % name) and
                                      fname.endswith(".c"))}})
                for name in listdir(_base_path)
                if (path.isdir(path.join(_base_path, name)) and
                    not name.startswith("__"))])

toolchains = {"gcc":  path.join(_base_path, "XSD_toolchain_gcc"),
              "makefile":  path.join(_base_path, "XSD_toolchain_makefile")}


def GetBuilder(targetname):
    return targets[targetname]["class"]()


def GetTargetChoices():
    DictXSD_toolchain = {}
    targetchoices = ""

    # Get all xsd toolchains
    for toolchainname, xsdfilename in toolchains.items():
        if path.isfile(xsdfilename):
            with open(xsdfilename) as f:
                DictXSD_toolchain["toolchain_" + toolchainname] = f.read()


    # Get all xsd targets
    for target_name, nfo in targets.items():
        with open(nfo["xsd"]) as f:
            xsd_string = f.read()
            targetchoices += xsd_string % dict(DictXSD_toolchain,
                                           target_name=target_name)

    return targetchoices


def GetTargetCode(targetname):
    codedesc = targets[targetname]["code"]
    code = "\n".join([open(fpath).read() for _fname, fpath in sorted(codedesc.items())])
    return code


def GetHeader():
    filename = paths.AbsNeighbourFile(__file__, "beremiz.h")
    return open(filename).read()


def GetCode(name):
    filename = paths.AbsNeighbourFile(__file__, name)
    return open(filename).read()
