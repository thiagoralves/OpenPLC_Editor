#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov <andrej.skvortzov@gmail.com>
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
from plcopen.plcopen import *
from util.TranslationCatalogs import NoTranslate

# -------------------------------------------------------------------------------
#                          Search In Project Dialog
# -------------------------------------------------------------------------------


def GetElementsChoices():
    _ = NoTranslate
    return [("datatype", _("Data Type")),
            ("function", _("Function")),
            ("functionBlock", _("Function Block")),
            ("program", _("Program")),
            ("configuration", _("Configuration"))]


class SearchInProjectDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title=_('Search in Project'))

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=3, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)

        pattern_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=2, vgap=5)
        pattern_sizer.AddGrowableCol(0)
        main_sizer.AddSizer(pattern_sizer, border=20,
                            flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        pattern_label = wx.StaticText(self, label=_('Pattern to search:'))
        pattern_sizer.AddWindow(pattern_label, flag=wx.ALIGN_BOTTOM)

        self.CaseSensitive = wx.CheckBox(self, label=_('Case sensitive'))
        pattern_sizer.AddWindow(self.CaseSensitive, flag=wx.GROW)

        self.Pattern = wx.TextCtrl(self, size=wx.Size(250, -1))
        self.Bind(wx.EVT_TEXT, self.FindPatternChanged, self.Pattern)
        pattern_sizer.AddWindow(self.Pattern, flag=wx.GROW)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEscapeKey)
        self.RegularExpression = wx.CheckBox(self, label=_('Regular expression'))
        pattern_sizer.AddWindow(self.RegularExpression, flag=wx.GROW)

        scope_staticbox = wx.StaticBox(self, label=_('Scope'))
        scope_sizer = wx.StaticBoxSizer(scope_staticbox, wx.HORIZONTAL)
        main_sizer.AddSizer(scope_sizer, border=20,
                            flag=wx.GROW | wx.LEFT | wx.RIGHT)

        scope_selection_sizer = wx.BoxSizer(wx.VERTICAL)
        scope_sizer.AddSizer(scope_selection_sizer, 1, border=5,
                             flag=wx.GROW | wx.TOP | wx.LEFT | wx.BOTTOM)

        self.WholeProject = wx.RadioButton(self, label=_('Whole Project'), style=wx.RB_GROUP)
        self.WholeProject.SetValue(True)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnScopeChanged, self.WholeProject)
        scope_selection_sizer.AddWindow(self.WholeProject, border=5,
                                        flag=wx.GROW | wx.BOTTOM)

        self.OnlyElements = wx.RadioButton(self, label=_('Only Elements'))
        self.Bind(wx.EVT_RADIOBUTTON, self.OnScopeChanged, self.OnlyElements)
        self.OnlyElements.SetValue(False)
        scope_selection_sizer.AddWindow(self.OnlyElements, flag=wx.GROW)

        self.ElementsList = wx.CheckListBox(self)
        self.ElementsList.Enable(False)
        scope_sizer.AddWindow(self.ElementsList, 1, border=5,
                              flag=wx.GROW | wx.TOP | wx.RIGHT | wx.BOTTOM)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(buttons_sizer, border=20,
                            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT)

        self.FindButton = wx.Button(self, label=_("Find"))
        self.FindButton.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnFindButton, self.FindButton)
        buttons_sizer.AddWindow(self.FindButton, border=5, flag=wx.RIGHT)

        self.CloseButton = wx.Button(self, label=_("Close"))
        self.Bind(wx.EVT_BUTTON, self.OnCloseButton, self.CloseButton)
        buttons_sizer.AddWindow(self.CloseButton)

        self.SetSizer(main_sizer)

        for _name, label in GetElementsChoices():
            self.ElementsList.Append(_(label))

        self.Fit()
        self.infosPrev = {}
        self.criteria = {}
        self.Pattern.SetFocus()
        self.RefreshButtonsState()

    def RefreshButtonsState(self):
        find_pattern = self.Pattern.GetValue()
        self.FindButton.Enable(find_pattern != "")

    def GetCriteria(self):
        return self.criteria

    def FindPatternChanged(self, event):
        self.RefreshButtonsState()
        event.Skip()

    def OnScopeChanged(self, event):
        self.ElementsList.Enable(self.OnlyElements.GetValue())
        event.Skip()

    def OnCloseButton(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnEscapeKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.OnCloseButton(event)
        else:
            event.Skip()

    def OnFindButton(self, event):
        message = None
        infos = {
            "find_pattern": self.Pattern.GetValue(),
            "case_sensitive": self.CaseSensitive.GetValue(),
            "regular_expression": self.RegularExpression.GetValue(),
        }
        if self.WholeProject.GetValue():
            infos["filter"] = "all"
        elif self.OnlyElements.GetValue():
            infos["filter"] = []
            for index, (name, _label) in enumerate(GetElementsChoices()):
                if self.ElementsList.IsChecked(index):
                    infos["filter"].append(name)

        if self.infosPrev != infos:
            try:
                self.criteria = infos
                CompilePattern(self.criteria)
                self.infosPrev = infos
            except Exception:
                self.criteria.clear()
                message = _("Syntax error in regular expression of pattern to search!")

        if message is not None:
            dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
        else:
            self.EndModal(wx.ID_OK)
