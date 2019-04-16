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
import sys
import shutil
from xml.dom import minidom

import wx

import util.paths as paths
from py_ext import PythonFileCTNMixin


class WxGladeHMI(PythonFileCTNMixin):

    ConfNodeMethods = [
        {
            "bitmap":    "editWXGLADE",
            "name":    _("WXGLADE GUI"),
            "tooltip": _("Edit a WxWidgets GUI with WXGlade"),
            "method":   "_editWXGLADE"
        },
    ]

    def GetIconName(self):
        return "wxGlade"

    def ConfNodePath(self):
        return paths.AbsDir(__file__)

    def _getWXGLADEpath(self, project_path=None):
        if project_path is None:
            project_path = self.CTNPath()
        # define name for wxGlade gui file
        return os.path.join(project_path, "hmi.wxg")

    def GetWxGladePath(self):
        path = None
        try:
            from wxglade import __file__ as fileName
            path = os.path.dirname(fileName)
            return path
        except ImportError:
            pass

        defLibDir = "/usr/share/wxglade"
        if os.path.isdir(defLibDir):
            path = defLibDir

        return path

    def launch_wxglade(self, options, wait=False):
        path = self.GetWxGladePath()
        glade = os.path.join(path, 'wxglade.py')
        if wx.Platform == '__WXMSW__':
            glade = "\"%s\"" % glade
        mode = {False: os.P_NOWAIT, True: os.P_WAIT}[wait]
        os.spawnv(mode, sys.executable,
                  ["\"%s\"" % sys.executable] + [glade] + options)

    def OnCTNSave(self, from_project_path=None):
        if from_project_path is not None:
            shutil.copyfile(self._getWXGLADEpath(from_project_path),
                            self._getWXGLADEpath())
        return PythonFileCTNMixin.OnCTNSave(self, from_project_path)

    def CTNGenerate_C(self, buildpath, locations):

        # list containing description of all objects declared in wxglade
        hmi_objects = []
        # list containing only description of the main frame object
        main_frames = []

        wxgfile_path = self._getWXGLADEpath()
        if os.path.exists(wxgfile_path):
            wxgfile = open(wxgfile_path, 'r')
            wxgtree = minidom.parse(wxgfile)
            wxgfile.close()

            for node in wxgtree.childNodes[1].childNodes:
                if node.nodeType == wxgtree.ELEMENT_NODE:
                    name = node.getAttribute("name")
                    wxglade_object_desc = {
                        "name": name,
                        "class": node.getAttribute("class"),
                        "handlers": [
                            hnode.firstChild.data for hnode in
                            node.getElementsByTagName("handler")]}

                    hmi_objects.append(wxglade_object_desc)
                    if name == self.CTNName():
                        main_frames.append(wxglade_object_desc)

            hmipyfile_path = os.path.join(self._getBuildPath(), "hmi.py")
            if wx.Platform == '__WXMSW__':
                wxgfile_path = "\"%s\"" % wxgfile_path
                wxghmipyfile_path = "\"%s\"" % hmipyfile_path
            else:
                wxghmipyfile_path = hmipyfile_path
            self.launch_wxglade(
                ['-o', wxghmipyfile_path, '-g', 'python', wxgfile_path], wait=True)

            hmipyfile = open(hmipyfile_path, 'r')
            define_hmi = hmipyfile.read().decode('utf-8')
            hmipyfile.close()

        else:
            define_hmi = ""

        global_hmi = ("global %s\n" % ",".join(
            [x["name"] for x in main_frames]) if len(main_frames) > 0 else "")

        declare_hmi = \
            "\n".join(["%(name)s = None\n" % x for x in main_frames]) + \
            "\n".join(["\n".join(["%(class)s.%(h)s = %(h)s" % dict(x, h=h)
                                  for h in x['handlers']])
                       for x in hmi_objects]) + """\

def OnCloseFrame(evt):
    wx.MessageBox(_("Please stop PLC to close"))

def InitHMI():
    """ + global_hmi + "\n" + "\n".join(["""\
    %(name)s = %(class)s(None)
    %(name)s.Bind(wx.EVT_CLOSE, OnCloseFrame)
    %(name)s.Show()

""" % x for x in main_frames]) + """\
def CleanupHMI():
    """ + global_hmi + "\n" + "\n".join(["""\
    if %(name)s is not None:
        %(name)s.Destroy()
""" % x for x in main_frames])

        self.PreSectionsTexts = {
            "globals": define_hmi,
            "start":   global_hmi,
            "stop":    "CleanupHMI()\n"
        }
        self.PostSectionsTexts = {
            "globals": declare_hmi,
            "start":   "InitHMI()\n",
        }

        if len(main_frames) == 0 and \
           len(getattr(self.CodeFile, "start").getanyText().strip()) == 0:
            self.GetCTRoot().logger.write_warning(
                _("Warning: WxGlade HMI has no object with name identical to extension name, and no python code is provided in start section to create object.\n"))

        return PythonFileCTNMixin.CTNGenerate_C(self, buildpath, locations)

    def _editWXGLADE(self):
        wxg_filename = self._getWXGLADEpath()
        open_wxglade = True
        if not self.GetCTRoot().CheckProjectPathPerm():
            dialog = wx.MessageDialog(self.GetCTRoot().AppFrame,
                                      _("You don't have write permissions.\nOpen wxGlade anyway ?"),
                                      _("Open wxGlade"),
                                      wx.YES_NO | wx.ICON_QUESTION)
            open_wxglade = dialog.ShowModal() == wx.ID_YES
            dialog.Destroy()
        if open_wxglade:
            if not os.path.exists(wxg_filename):
                hmi_name = self.BaseParams.getName()
                open(wxg_filename, "w").write("""<?xml version="1.0"?>
    <application path="" name="" class="" option="0" language="python" top_window="%(name)s" encoding="UTF-8" use_gettext="0" overwrite="0" use_new_namespace="1" for_version="2.8" is_template="0">
        <object class="%(class)s" name="%(name)s" base="EditFrame">
            <style>wxDEFAULT_FRAME_STYLE</style>
            <title>frame_1</title>
            <object class="wxBoxSizer" name="sizer_1" base="EditBoxSizer">
                <orient>wxVERTICAL</orient>
            <object class="sizerslot" />
        </object>
        </object>
    </application>
    """ % {"name": hmi_name, "class": "Class_%s" % hmi_name})
            if wx.Platform == '__WXMSW__':
                wxg_filename = "\"%s\"" % wxg_filename
            self.launch_wxglade([wxg_filename])
