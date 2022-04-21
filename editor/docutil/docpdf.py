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
from __future__ import print_function
import os
import wx


readerexepath = None


def get_acroversion():
    " Return version of Adobe Acrobat executable or None"
    from six.moves import winreg
    adobesoft = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'Software\Adobe')
    for index in range(winreg.QueryInfoKey(adobesoft)[0]):
        key = winreg.EnumKey(adobesoft, index)
        if "acrobat" in key.lower():
            acrokey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'Software\\Adobe\\%s' % key)
            for index in range(winreg.QueryInfoKey(acrokey)[0]):
                numver = winreg.EnumKey(acrokey, index)
                try:
                    res = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE, 'Software\\Adobe\\%s\\%s\\InstallPath' % (key, numver))
                    return res
                except Exception:
                    pass
    return None


def open_win_pdf(readerexepath, pdffile, pagenum=None):
    if pagenum is not None:
        os.spawnl(os.P_DETACH, readerexepath, "AcroRd32.exe", "/A", "page=%d=OpenActions" % pagenum, '"%s"' % pdffile)
    else:
        os.spawnl(os.P_DETACH, readerexepath, "AcroRd32.exe", '"%s"' % pdffile)


def open_lin_pdf(readerexepath, pdffile, pagenum=None):
    if pagenum is None:
        os.system("%s -remote DS301 %s &" % (readerexepath, pdffile))
    else:
        print("Open pdf %s at page %d" % (pdffile, pagenum))
        os.system("%s -remote DS301 %s %d &" % (readerexepath, pdffile, pagenum))


def open_pdf(pdffile, pagenum=None):
    if wx.Platform == '__WXMSW__':
        try:
            readerpath = get_acroversion()
        except Exception:
            wx.MessageBox("Acrobat Reader is not found or installed !")
            return None

        readerexepath = os.path.join(readerpath, "AcroRd32.exe")
        if os.path.isfile(readerexepath):
            open_win_pdf(readerexepath, pdffile, pagenum)
        else:
            return None
    else:
        readerexepath = os.path.join("/usr/bin", "xpdf")
        if os.path.isfile(readerexepath):
            open_lin_pdf(readerexepath, pdffile, pagenum)
        else:
            wx.MessageBox("xpdf is not found or installed !")
            return None
