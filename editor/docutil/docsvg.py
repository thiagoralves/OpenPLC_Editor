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
import subprocess
import wx


def get_inkscape_path():
    """ Return the Inkscape path """
    from six.moves import winreg
    try:
        svgexepath = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE,
                                       'Software\\Classes\\svgfile\\shell\\Inkscape\\command')
    except OSError:
        svgexepath = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE,
                                       'Software\\Classes\\inkscape.svg\\shell\\open\\command')
    svgexepath = svgexepath.replace('"%1"', '')
    return svgexepath.replace('"', '')


def open_win_svg(svgexepath, svgfile):
    """ Open Inkscape on Windows platform """
    popenargs = [svgexepath]
    if svgfile is not None:
        popenargs.append(svgfile)
    subprocess.Popen(popenargs)


def open_lin_svg(svgexepath, svgfile):
    """ Open Inkscape on Linux platform """
    if os.path.isfile("/usr/bin/inkscape"):
        os.system("%s %s &" % (svgexepath, svgfile))


def open_svg(svgfile):
    """ Generic function to open SVG file """
    if wx.Platform == '__WXMSW__':
        try:
            open_win_svg(get_inkscape_path(), svgfile)
        except Exception:
            wx.MessageBox("Inkscape is not found or installed !")
            return None
    else:
        svgexepath = os.path.join("/usr/bin", "inkscape")
        if os.path.isfile(svgexepath):
            open_lin_svg(svgexepath, svgfile)
        else:
            wx.MessageBox("Inkscape is not found or installed !")
            return None
