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


class FindInPouDialog(wx.Dialog):

    def _init_icon(self, parent):
        if parent and parent.icon:
            self.SetIcon(parent.icon)

    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent, title=_("Find"),
            style=wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.RESIZE_BORDER)

        self._init_icon(parent)
        panel = wx.Panel(self, style=wx.TAB_TRAVERSAL)

        main_sizer = wx.FlexGridSizer(cols=1, hgap=5, rows=2, vgap=5)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)

        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSizer(controls_sizer, border=20,
                            flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        patterns_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=1, vgap=5)
        patterns_sizer.AddGrowableCol(1)
        controls_sizer.AddSizer(patterns_sizer, border=5, flag=wx.GROW | wx.BOTTOM)

        find_label = wx.StaticText(panel, label=_("Find:"))
        patterns_sizer.AddWindow(find_label, flag=wx.ALIGN_CENTER_VERTICAL)

        self.FindPattern = wx.TextCtrl(panel)
        self.Bind(wx.EVT_TEXT, self.OnFindPatternChanged, self.FindPattern)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEscapeKey)
        patterns_sizer.AddWindow(self.FindPattern, flag=wx.GROW)

        params_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.AddSizer(params_sizer, border=5, flag=wx.GROW | wx.BOTTOM)

        direction_staticbox = wx.StaticBox(panel, label=_("Direction"))
        direction_staticboxsizer = wx.StaticBoxSizer(
            direction_staticbox, wx.VERTICAL)
        params_sizer.AddSizer(direction_staticboxsizer, 1, border=5,
                              flag=wx.GROW | wx.RIGHT)

        self.Forward = wx.RadioButton(panel, label=_("Forward"),
                                      style=wx.RB_GROUP)
        direction_staticboxsizer.AddWindow(self.Forward, border=5,
                                           flag=wx.ALL | wx.GROW)

        self.Backward = wx.RadioButton(panel, label=_("Backward"))
        direction_staticboxsizer.AddWindow(self.Backward, border=5,
                                           flag=wx.ALL | wx.GROW)

        options_staticbox = wx.StaticBox(panel, label=_("Options"))
        options_staticboxsizer = wx.StaticBoxSizer(
            options_staticbox, wx.VERTICAL)
        params_sizer.AddSizer(options_staticboxsizer, 1, flag=wx.GROW)

        self.CaseSensitive = wx.CheckBox(panel, label=_("Case sensitive"))
        self.CaseSensitive.SetValue(True)
        options_staticboxsizer.AddWindow(self.CaseSensitive, border=5,
                                         flag=wx.ALL | wx.GROW)

        self.WrapSearch = wx.CheckBox(panel, label=_("Wrap search"))
        self.WrapSearch.SetValue(True)
        options_staticboxsizer.AddWindow(self.WrapSearch, border=5,
                                         flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.GROW)

        self.RegularExpressions = wx.CheckBox(panel, label=_("Regular expressions"))
        options_staticboxsizer.AddWindow(self.RegularExpressions, border=5,
                                         flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.GROW)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(buttons_sizer, border=20,
                            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT)

        self.FindButton = wx.Button(panel, label=_("Find"))
        self.FindButton.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnFindButton, self.FindButton)
        buttons_sizer.AddWindow(self.FindButton, border=5, flag=wx.RIGHT)

        self.CloseButton = wx.Button(panel, label=_("Close"))
        self.Bind(wx.EVT_BUTTON, self.OnCloseButton, self.CloseButton)
        buttons_sizer.AddWindow(self.CloseButton)

        # set the longest message here, to use it length to calculate
        # optimal size of dialog window
        self.RegExpSyntaxErrMsg = _("Syntax error in regular expression of pattern to search!")
        self.StatusLabel = wx.StaticText(panel, label=self.RegExpSyntaxErrMsg)
        controls_sizer.AddWindow(self.StatusLabel, flag=wx.ALIGN_CENTER_VERTICAL)

        panel.SetSizer(main_sizer)
        main_sizer.Fit(self)

        # clear message after dialog size calculation
        self.SetStatusText("")

        self.ParentWindow = parent

        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        self.infosPrev = {}
        self.criteria = {}
        self.FindPattern.SetFocus()
        self.RefreshButtonsState()

    def RefreshButtonsState(self):
        find_pattern = self.FindPattern.GetValue()
        self.FindButton.Enable(find_pattern != "")

    def OnCloseFrame(self, event):
        self.Hide()
        event.Veto()

    def OnCloseButton(self, event):
        self.Hide()
        event.Skip()

    def OnEscapeKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.OnCloseButton(event)
        else:
            event.Skip()

    def OnFindPatternChanged(self, event):
        self.RefreshButtonsState()
        event.Skip()

    def SetStatusText(self, msg):
        self.StatusLabel.SetLabel(msg)
        self.Layout()

    def OnFindButton(self, event):
        infos = {
            "find_pattern": self.FindPattern.GetValue(),
            "wrap": self.WrapSearch.GetValue(),
            "case_sensitive": self.CaseSensitive.GetValue(),
            "regular_expression": self.RegularExpressions.GetValue(),
            "filter": "all"}

        if self.infosPrev != infos:
            self.infosPrev = infos
            message = ""
            try:
                self.criteria = infos
                CompilePattern(self.criteria)
            except Exception:
                self.criteria.clear()
                message = self.RegExpSyntaxErrMsg
            self.SetStatusText(message)
        if len(self.criteria) > 0:
            wx.CallAfter(self.ParentWindow.FindInPou,
                         {True: 1, False: -1}[self.Forward.GetValue()],
                         self.criteria)
        event.Skip()
