#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from __future__ import absolute_import
import os
import sys
from builtins import str as text


def AbsFile(file):
    if isinstance(file, str):
        file = text(file, sys.getfilesystemencoding())
    return file


def AbsDir(file):
    file = AbsFile(file)
    return os.path.dirname(os.path.realpath(file))


def AbsNeighbourFile(file, *args):
    return os.path.join(AbsDir(file), *args)


def AbsParentDir(file, level=1):
    path = AbsDir(file)
    for dummy in range(0, level):
        path = os.path.dirname(path)
    return path
