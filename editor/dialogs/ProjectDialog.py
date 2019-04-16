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

from controls.ProjectPropertiesPanel import ProjectPropertiesPanel


class ProjectDialog(wx.Dialog):

    def __init__(self, parent, enable_required=True):
        wx.Dialog.__init__(self, parent, title=_('Project properties'),
                           style=wx.DEFAULT_DIALOG_STYLE)

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)

        self.ProjectProperties = ProjectPropertiesPanel(
            self, enable_required=enable_required, scrolling=False)
        main_sizer.AddWindow(self.ProjectProperties, flag=wx.GROW)

        self.ButtonSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL | wx.CENTRE)
        self.Bind(wx.EVT_BUTTON, self.OnOK,
                  self.ButtonSizer.GetAffirmativeButton())
        main_sizer.AddSizer(self.ButtonSizer, border=20,
                            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.SetSizer(main_sizer)
        self.ProjectProperties.Fit()
        self.Fit()

    def OnOK(self, event):
        values = self.ProjectProperties.GetValues()
        error = []
        for param, name in [("projectName", _("Project Name")),
                            ("productName", _("Product Name")),
                            ("productVersion", _("Product Version")),
                            ("companyName", _("Company Name"))]:
            if values[param] == "":
                error.append(name)
        if len(error) > 0:
            text = ""
            for i, item in enumerate(error):
                if i == 0:
                    text += item
                elif i == len(error) - 1:
                    text += _(" and %s") % item
                else:
                    text += ", %s" % item
            dialog = wx.MessageDialog(
                self,
                _("Form isn't complete. %s must be filled!") % text,
                _("Error"), wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def SetValues(self, values):
        self.ProjectProperties.SetValues(values)

    def GetValues(self):
        return self.ProjectProperties.GetValues()
