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
import wx
import subprocess


def _get_inkscape_path():
    """ Return the Inkscape binary path """

    if wx.Platform == '__WXMSW__':
        from six.moves import winreg
        inkcmd = None
        tries = [(winreg.HKEY_LOCAL_MACHINE, 'Software\\Classes\\svgfile\\shell\\Inkscape\\command'),
                 (winreg.HKEY_LOCAL_MACHINE, 'Software\\Classes\\inkscape.svg\\shell\\open\\command'),
                 (winreg.HKEY_CURRENT_USER, 'Software\\Classes\\inkscape.svg\\shell\\open\\command')]

        for subreg, key in tries:
            try:
                inkcmd = winreg.QueryValue(subreg, key)
                break;
            except OSError:
                pass

        if inkcmd is None:
            return None

        return inkcmd.replace('"%1"', '').strip().replace('"', '')

    else:
        try:
            return subprocess.check_output("command -v inkscape", shell=True).strip()
        except subprocess.CalledProcessError:
            return None

_inkscape_path = None
def get_inkscape_path():
    """ Return the Inkscape binary path """

    global _inkscape_path

    if _inkscape_path is not None:
        return _inkscape_path

    _inkscape_path = _get_inkscape_path()
    return _inkscape_path


def _get_inkscape_version():
    inkpath = get_inkscape_path()
    if inkpath is None:
        return None
    return map(int, 
        subprocess.check_output([inkpath,"--version"]).split()[1].split('.'))

_inkscape_version = None
def get_inkscape_version():
    global _inkscape_version

    if _inkscape_version is not None:
        return _inkscape_version

    _inkscape_version = _get_inkscape_version()
    return _inkscape_version

def open_svg(svgfile):
    """ Generic function to open SVG file """
    
    inkpath = get_inkscape_path()
    if inkpath is None:
        wx.MessageBox("Inkscape is not found or installed !")
    else:
        subprocess.Popen([inkpath,svgfile])
