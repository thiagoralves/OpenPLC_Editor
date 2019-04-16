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

from controls import ProjectPropertiesPanel, VariablePanel
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor
from plcopen.types_enums import ComputeConfigurationName


class ProjectNodeEditor(ConfTreeNodeEditor):

    SHOW_BASE_PARAMS = False
    ENABLE_REQUIRED = True
    CONFNODEEDITOR_TABS = [
        (_("Config variables"), "_create_VariablePanel"),
        (_("Project properties"), "_create_ProjectPropertiesPanel")]

    def _create_VariablePanel(self, prnt):
        self.VariableEditorPanel = VariablePanel(prnt, self, self.Controler, "config", self.Debug)
        self.VariableEditorPanel.SetTagName(self.TagName)

        return self.VariableEditorPanel

    def _create_ProjectPropertiesPanel(self, prnt):
        self.ProjectProperties = ProjectPropertiesPanel(prnt, self.Controler, self.ParentWindow, self.ENABLE_REQUIRED)

        return self.ProjectProperties

    def __init__(self, parent, controler, window):
        configuration = controler.GetProjectMainConfigurationName()
        if configuration is not None:
            tagname = ComputeConfigurationName(configuration)
        else:
            tagname = ""

        ConfTreeNodeEditor.__init__(self, parent, controler, window, tagname)

        buttons_sizer = self.GenerateMethodButtonSizer()
        self.MainSizer.InsertSizer(0, buttons_sizer, 0, border=5, flag=wx.ALL)
        self.MainSizer.Layout()

        self.VariableEditor = self.VariableEditorPanel

    def GetTagName(self):
        return self.Controler.CTNName()

    def SetTagName(self, tagname):
        self.TagName = tagname
        if self.VariableEditor is not None:
            self.VariableEditor.SetTagName(tagname)

    def GetTitle(self):
        fullname = _(self.Controler.CTNName())
        if self.Controler.CTNTestModified():
            return "~%s~" % fullname
        return fullname

    def RefreshView(self, variablepanel=True):
        ConfTreeNodeEditor.RefreshView(self)
        self.VariableEditorPanel.RefreshView()
        self.ProjectProperties.RefreshView()

    def GetBufferState(self):
        return self.Controler.GetBufferState()

    def Undo(self):
        self.Controler.LoadPrevious()
        self.ParentWindow.CloseTabsWithoutModel()

    def Redo(self):
        self.Controler.LoadNext()
        self.ParentWindow.CloseTabsWithoutModel()
