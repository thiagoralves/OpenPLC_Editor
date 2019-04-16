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

from plcopen.structures import TestIdentifier, IEC_KEYWORDS
from util.TranslationCatalogs import NoTranslate


def GetActionLanguages():
    _ = NoTranslate
    return [_("IL"), _("ST"), _("LD"), _("FBD")]


class PouActionDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title=_('Create a new action'))

        self.ACTION_LANGUAGES_DICT = dict([(_(language), language)
                                           for language in GetActionLanguages()])

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)

        infos_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=3, vgap=15)
        infos_sizer.AddGrowableCol(1)
        main_sizer.AddSizer(infos_sizer, border=20,
                            flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        actionname_label = wx.StaticText(self, label=_('Action Name:'))
        infos_sizer.AddWindow(actionname_label, border=4,
                              flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP)

        self.ActionName = wx.TextCtrl(self, size=wx.Size(180, -1))
        infos_sizer.AddWindow(self.ActionName, flag=wx.GROW)

        language_label = wx.StaticText(self, label=_('Language:'))
        infos_sizer.AddWindow(language_label, border=4,
                              flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP)

        self.Language = wx.ComboBox(self, style=wx.CB_READONLY)
        infos_sizer.AddWindow(self.Language, flag=wx.GROW)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL | wx.CENTRE)
        self.Bind(wx.EVT_BUTTON, self.OnOK,
                  button_sizer.GetAffirmativeButton())
        main_sizer.AddSizer(button_sizer, border=20,
                            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.SetSizer(main_sizer)

        for option in GetActionLanguages():
            self.Language.Append(_(option))

        self.Fit()
        self.PouNames = []
        self.PouElementNames = []

    def OnOK(self, event):
        error = []
        action_name = self.ActionName.GetValue()
        if action_name == "":
            error.append(_("Action Name"))
        if self.Language.GetSelection() == -1:
            error.append(_("Language"))
        message = None
        if len(error) > 0:
            text = ""
            for i, item in enumerate(error):
                if i == 0:
                    text += item
                elif i == len(error) - 1:
                    text += _(" and %s") % item
                else:
                    text += _(", %s") % item
            message = _("Form isn't complete. %s must be filled!") % text
        elif not TestIdentifier(action_name):
            message = _("\"%s\" is not a valid identifier!") % action_name
        elif action_name.upper() in IEC_KEYWORDS:
            message = _("\"%s\" is a keyword. It can't be used!") % action_name
        elif action_name.upper() in self.PouNames:
            message = _("A POU named \"%s\" already exists!") % action_name
        elif action_name.upper() in self.PouElementNames:
            message = _("\"%s\" element for this pou already exists!") % action_name
        if message is not None:
            dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def SetPouNames(self, pou_names):
        self.PouNames = [pou_name.upper() for pou_name in pou_names]

    def SetPouElementNames(self, element_names):
        self.PouElementNames = [element_name.upper() for element_name in element_names]

    def SetValues(self, values):
        for item, value in values.items():
            if item == "actionName":
                self.ActionName.SetValue(value)
            elif item == "language":
                self.Language.SetStringSelection(_(value))

    def GetValues(self):
        values = {}
        values["actionName"] = self.ActionName.GetValue()
        values["language"] = self.ACTION_LANGUAGES_DICT[self.Language.GetStringSelection()]
        return values
