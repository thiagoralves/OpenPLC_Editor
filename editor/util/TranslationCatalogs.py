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
from six.moves import builtins
import wx


locale = None


builtins.__dict__['_'] = wx.GetTranslation


def GetDomain(path):
    for name in os.listdir(path):
        filepath = os.path.join(path, name)
        basename, fileext = os.path.splitext(name)
        if os.path.isdir(filepath):
            result = GetDomain(filepath)
            if result is not None:
                return result
        elif fileext == ".mo":
            return basename
    return None


def AddCatalog(locale_dir):
    if os.path.exists(locale_dir) and os.path.isdir(locale_dir):
        domain = GetDomain(locale_dir)
        if domain is not None:
            global locale
            if locale is None:
                # Define locale for wx
                wx.LogGui.EnableLogging(False)
                locale = wx.Locale(wx.LANGUAGE_DEFAULT)
                wx.LogGui.EnableLogging(True)

            locale.AddCatalogLookupPathPrefix(locale_dir)
            locale.AddCatalog(domain)


def NoTranslate(x):
    return x
