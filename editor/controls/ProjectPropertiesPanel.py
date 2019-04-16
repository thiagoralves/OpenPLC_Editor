#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2012: Edouard TISSERANT and Laurent BESSARD
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
from wx.lib.scrolledpanel import ScrolledPanel

from xmlclass.xmlclass import URI_model

# -------------------------------------------------------------------------------
#                                 Helpers
# -------------------------------------------------------------------------------

REQUIRED_PARAMS = ["projectName", "productName", "productVersion", "companyName"]

[
    TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU, PROJECTTREE,
    POUINSTANCEVARIABLESPANEL, LIBRARYTREE, SCALING, PAGETITLES
] = range(10)


# -------------------------------------------------------------------------------
#                       Project Properties Panel
# -------------------------------------------------------------------------------


class ProjectPropertiesPanel(wx.Notebook):

    def AddSizerParams(self, parent, sizer, params):
        for idx, (name, label) in enumerate(params):
            border = 0
            if idx == 0:
                border |= wx.TOP
            elif idx == len(params) - 1:
                border |= wx.BOTTOM

            st = wx.StaticText(parent, label=label)
            sizer.AddWindow(st, border=10,
                            flag=wx.ALIGN_CENTER_VERTICAL | border | wx.LEFT)

            tc = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER)
            setattr(self, name, tc)
            callback = self.GetTextCtrlChangedFunction(tc, name)
            self.Bind(wx.EVT_TEXT_ENTER, callback, tc)
            tc.Bind(wx.EVT_KILL_FOCUS, callback)
            sizer.AddWindow(tc, border=10,
                            flag=wx.GROW | border | wx.RIGHT)

    def __init__(self, parent, controller=None, window=None, enable_required=True, scrolling=True):
        wx.Notebook.__init__(self, parent)

        self.Controller = controller
        self.ParentWindow = window
        self.Values = None

        # Project Panel elements

        self.ProjectPanel = ScrolledPanel(self, style=wx.TAB_TRAVERSAL)
        self.ProjectPanel.SetAutoLayout(1)
        if scrolling:
            self.ProjectPanel.SetupScrolling()
        projectpanel_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=5, vgap=15)
        projectpanel_sizer.AddGrowableCol(1)
        self.ProjectPanel.SetSizer(projectpanel_sizer)

        self.AddSizerParams(self.ProjectPanel, projectpanel_sizer,
                            [("projectName",    _('Project Name (required):')),
                             ("projectVersion", _('Project Version (optional):')),
                             ("productName",    _('Product Name (required):')),
                             ("productVersion", _('Product Version (required):')),
                             ("productRelease", _('Product Release (optional):'))])

        self.AddPage(self.ProjectPanel, _("Project"))

        # Author Panel elements

        self.AuthorPanel = ScrolledPanel(self, style=wx.TAB_TRAVERSAL)
        self.AuthorPanel.SetAutoLayout(1)
        if scrolling:
            self.AuthorPanel.SetupScrolling()
        authorpanel_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=4, vgap=15)
        authorpanel_sizer.AddGrowableCol(1)
        self.AuthorPanel.SetSizer(authorpanel_sizer)

        self.AddSizerParams(self.AuthorPanel, authorpanel_sizer,
                            [("companyName",  _('Company Name (required):')),
                             ("companyURL",   _('Company URL (optional):')),
                             ("authorName",   _('Author Name (optional):')),
                             ("organization", _('Organization (optional):'))])

        self.AddPage(self.AuthorPanel, _("Author"))

        # Graphics Panel elements

        self.GraphicsPanel = ScrolledPanel(self, style=wx.TAB_TRAVERSAL)
        self.GraphicsPanel.SetAutoLayout(1)
        if scrolling:
            self.GraphicsPanel.SetupScrolling()
        graphicpanel_sizer = wx.FlexGridSizer(cols=1, hgap=5, rows=4, vgap=5)
        graphicpanel_sizer.AddGrowableCol(0)
        graphicpanel_sizer.AddGrowableRow(3)
        self.GraphicsPanel.SetSizer(graphicpanel_sizer)

        pageSize_st = wx.StaticText(self.GraphicsPanel,
                                    label=_('Page Size (optional):'))
        graphicpanel_sizer.AddWindow(
            pageSize_st, border=10,
            flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.LEFT | wx.RIGHT)

        pageSize_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=2, vgap=5)
        pageSize_sizer.AddGrowableCol(1)
        graphicpanel_sizer.AddSizer(pageSize_sizer, border=10,
                                    flag=wx.GROW | wx.LEFT | wx.RIGHT)

        for name, label in [('PageWidth', _('Width:')),
                            ('PageHeight', _('Height:'))]:
            st = wx.StaticText(self.GraphicsPanel, label=label)
            pageSize_sizer.AddWindow(st, border=12,
                                     flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT)

            sp = wx.SpinCtrl(self.GraphicsPanel,
                             min=0, max=2**16, style=wx.TE_PROCESS_ENTER)
            setattr(self, name, sp)
            callback = self.GetPageSizeChangedFunction(sp, name)
            self.Bind(wx.EVT_TEXT_ENTER, callback, sp)
            sp.Bind(wx.EVT_KILL_FOCUS, callback)
            pageSize_sizer.AddWindow(sp, flag=wx.GROW)

        scaling_st = wx.StaticText(self.GraphicsPanel,
                                   label=_('Grid Resolution:'))
        graphicpanel_sizer.AddWindow(scaling_st, border=10,
                                     flag=wx.GROW | wx.LEFT | wx.RIGHT)

        scaling_nb = wx.Notebook(self.GraphicsPanel)
        graphicpanel_sizer.AddWindow(scaling_nb, border=10,
                                     flag=wx.GROW | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.Scalings = {}
        for language, translation in [("FBD", _("FBD")), ("LD", _("LD")), ("SFC", _("SFC"))]:
            scaling_panel = wx.Panel(scaling_nb, style=wx.TAB_TRAVERSAL)
            scalingpanel_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=2, vgap=5)
            scalingpanel_sizer.AddGrowableCol(1)
            scaling_panel.SetSizer(scalingpanel_sizer)

            scaling_controls = []
            for idx, (name, label) in enumerate([('XScale', _('Horizontal:')),
                                                 ('YScale', _('Vertical:'))]):
                if idx == 0:
                    border = wx.TOP
                else:
                    border = wx.BOTTOM

                st = wx.StaticText(scaling_panel, label=label)
                scalingpanel_sizer.AddWindow(
                    st, border=10,
                    flag=wx.ALIGN_CENTER_VERTICAL | border | wx.LEFT)

                sp = wx.SpinCtrl(scaling_panel,
                                 min=0, max=2**16, style=wx.TE_PROCESS_ENTER)
                scaling_controls.append(sp)
                callback = self.GetScalingChangedFunction(sp, language, name)
                self.Bind(wx.EVT_TEXT_ENTER, callback, sp)
                sp.Bind(wx.EVT_KILL_FOCUS, callback)
                scalingpanel_sizer.AddWindow(sp, border=10,
                                             flag=wx.GROW | border | wx.RIGHT)

            self.Scalings[language] = scaling_controls
            scaling_nb.AddPage(scaling_panel, translation)

        self.AddPage(self.GraphicsPanel, _("Graphics"))

        # Miscellaneous Panel elements

        self.MiscellaneousPanel = ScrolledPanel(parent=self,
                                                name='MiscellaneousPanel',
                                                style=wx.TAB_TRAVERSAL)
        self.MiscellaneousPanel.SetAutoLayout(1)
        if scrolling:
            self.MiscellaneousPanel.SetupScrolling()
        miscellaneouspanel_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=2, vgap=15)
        miscellaneouspanel_sizer.AddGrowableCol(1)
        miscellaneouspanel_sizer.AddGrowableRow(1)
        self.MiscellaneousPanel.SetSizer(miscellaneouspanel_sizer)

        language_label = wx.StaticText(self.MiscellaneousPanel,
                                       label=_('Language (optional):'))
        miscellaneouspanel_sizer.AddWindow(language_label, border=10,
                                           flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.LEFT)

        self.Language = wx.ComboBox(self.MiscellaneousPanel,
                                    style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnLanguageChanged, self.Language)
        miscellaneouspanel_sizer.AddWindow(self.Language, border=10,
                                           flag=wx.GROW | wx.TOP | wx.RIGHT)

        description_label = wx.StaticText(
            self.MiscellaneousPanel, label=_('Content Description (optional):'))
        miscellaneouspanel_sizer.AddWindow(description_label, border=10,
                                           flag=wx.BOTTOM | wx.LEFT)

        self.ContentDescription = wx.TextCtrl(
            self.MiscellaneousPanel, size=wx.Size(240, 150),
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnContentDescriptionChanged,
                  self.ContentDescription)
        self.ContentDescription.Bind(wx.EVT_KILL_FOCUS,
                                     self.OnContentDescriptionChanged)
        miscellaneouspanel_sizer.AddWindow(self.ContentDescription, border=10,
                                           flag=wx.GROW | wx.BOTTOM | wx.RIGHT)

        self.AddPage(self.MiscellaneousPanel, _("Miscellaneous"))

        for param in REQUIRED_PARAMS:
            getattr(self, param).Enable(enable_required)

        languages = ["", "en-US", "fr-FR", "zh-CN", "ru-RU"]

        for language in languages:
            self.Language.Append(language)

    def RefreshView(self):
        if self.Controller is not None:
            self.SetValues(self.Controller.GetProjectProperties())

    def SetValues(self, values):
        self.Values = values
        for item, value in values.items():
            if item == "language":
                self.Language.SetStringSelection(value)
            elif item == "contentDescription":
                self.ContentDescription.SetValue(value)
            elif item == "pageSize":
                self.PageWidth.SetValue(value[0])
                self.PageHeight.SetValue(value[1])
            elif item == "scaling":
                for language, (x, y) in value.items():
                    if language in self.Scalings:
                        self.Scalings[language][0].SetValue(x)
                        self.Scalings[language][1].SetValue(y)
            else:
                tc = getattr(self, item, None)
                if tc is not None:
                    tc.SetValue(value)

    def GetValues(self):
        values = {}
        for param in ["projectName", "projectVersion",
                      "productName", "productVersion",
                      "productRelease", "companyName",
                      "companyURL", "authorName",
                      "organization"]:
            value = getattr(self, param).GetValue()
            if param in REQUIRED_PARAMS or value != "":
                values[param] = value
            else:
                values[param] = None
        language = self.Language.GetStringSelection()
        if language != "":
            values["language"] = language
        else:
            values["language"] = None
        content_description = self.ContentDescription.GetValue()
        if content_description != "":
            values["contentDescription"] = content_description
        else:
            values["contentDescription"] = None
        values["pageSize"] = (self.PageWidth.GetValue(), self.PageHeight.GetValue())
        values["scaling"] = {}
        for language in ["FBD", "LD", "SFC"]:
            values["scaling"][language] = (self.Scalings[language][0].GetValue(),
                                           self.Scalings[language][1].GetValue())
        return values

    def GetTextCtrlChangedFunction(self, textctrl, name):
        def TextCtrlChangedFunction(event):
            if self.Controller is not None and self.Values is not None:
                old_value = self.Values.get(name)
                new_value = textctrl.GetValue()
                if name in REQUIRED_PARAMS and new_value == "":
                    new_value = None
                if name == 'companyURL':
                    if not URI_model.match(new_value):
                        new_value = None
                        dialog = wx.MessageDialog(self, _('Invalid URL!\n'
                                                          'Please enter correct URL address.'),
                                                  _("Error"), wx.OK | wx.ICON_ERROR)
                        dialog.ShowModal()
                        dialog.Destroy()
                if old_value != new_value:
                    self.Controller.SetProjectProperties(properties={name: new_value})
                    self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU,
                                               PROJECTTREE, PAGETITLES)
                    wx.CallAfter(self.RefreshView)
            event.Skip()
        return TextCtrlChangedFunction

    def GetPageSizeChangedFunction(self, spinctrl, name):
        def PageSizeChangedFunction(event):
            if self.Controller is not None:
                if self.Values is not None:
                    old_value = self.Values.get("pageSize")
                else:
                    old_value = (0, 0)
                if name == 'PageWidth':
                    new_value = (spinctrl.GetValue(), old_value[1])
                else:
                    new_value = (old_value[0], spinctrl.GetValue())
                if old_value != new_value:
                    self.Controller.SetProjectProperties(properties={"pageSize": new_value})
                    self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU,
                                               PAGETITLES, SCALING)
                    wx.CallAfter(self.RefreshView)
            event.Skip()
        return PageSizeChangedFunction

    def GetScalingChangedFunction(self, spinctrl, language, name):
        def ScalingChangedFunction(event):
            if self.Controller is not None:
                old_value = (0, 0)
                if self.Values is not None:
                    scaling = self.Values.get("scaling")
                    if scaling is not None:
                        old_value = scaling.get(language)
                if name == 'XScale':
                    new_value = (spinctrl.GetValue(), old_value[1])
                else:
                    new_value = (old_value[0], spinctrl.GetValue())
                if old_value != new_value:
                    self.Controller.SetProjectProperties(properties={"scaling": {language: new_value}})
                    self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU,
                                               PAGETITLES, SCALING)
                    wx.CallAfter(self.RefreshView)
            event.Skip()
        return ScalingChangedFunction

    def OnLanguageChanged(self, event):
        if self.Controller is not None:
            if self.Values is not None:
                old_value = self.Values.get("language")
            else:
                old_value = None
            new_value = self.Language.GetStringSelection()
            if new_value == "":
                new_value = None
            if old_value != new_value:
                self.Controller.SetProjectProperties(properties={"language": new_value})
                self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES)
                wx.CallAfter(self.RefreshView)
        event.Skip()

    def OnContentDescriptionChanged(self, event):
        if self.Controller is not None:
            if self.Values is not None:
                old_value = self.Values.get("contentDescription")
            else:
                old_value = None
            new_value = self.ContentDescription.GetValue()
            if new_value == "":
                new_value = None
            if old_value != new_value:
                self.Controller.SetProjectProperties(properties={"contentDescription": new_value})
                self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES)
                wx.CallAfter(self.RefreshView)
        event.Skip()
