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
Misc definitions
"""


from __future__ import absolute_import
import os
from functools import reduce

from util.BitmapLibrary import AddBitmapFolder
from util.TranslationCatalogs import AddCatalog


def CheckPathPerm(path):
    """ Helper func to check path write permission """
    if path is None or not os.path.isdir(path):
        return False
    for root, dirs, files in os.walk(path):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for name in files:
            if os.access(root, os.W_OK) is not True or os.access(os.path.join(root, name), os.W_OK) is not True:
                return False
    return True


def GetClassImporter(param):
    """
    is used to resolve library class names in features.py
    if param is a string, returns a callable that return the class pointed by param
    if a class is given, then returns a callable that returns the given class.
    """

    if isinstance(param, str):
        def factory():
            # on-demand import, only when using class
            mod = __import__(param.rsplit('.', 1)[0])
            return reduce(getattr, param.split('.')[1:], mod)
        return factory
    else:
        return lambda: param


def InstallLocalRessources(CWD):
    # Beremiz bitmaps
    AddBitmapFolder(os.path.join(CWD, "images"))

    # Internationalization
    AddCatalog(os.path.join(CWD, "locale"))
