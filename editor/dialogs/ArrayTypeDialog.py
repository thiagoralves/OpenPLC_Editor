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
import re

import wx

from controls import CustomEditableListBox

# -------------------------------------------------------------------------------
#                                  Helpers
# -------------------------------------------------------------------------------

DIMENSION_MODEL = re.compile(r"([0-9]+)\.\.([0-9]+)$")

# -------------------------------------------------------------------------------
#                             Array Type Dialog
# -------------------------------------------------------------------------------


class ArrayTypeDialog(wx.Dialog):

    def __init__(self, parent, datatypes, infos):
        wx.Dialog.__init__(self, parent, title=_('Edit array type properties'))

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=3, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(top_sizer, border=20,
                            flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        basetype_label = wx.StaticText(self, label=_('Base Type:'))
        top_sizer.AddWindow(basetype_label, 1, flag=wx.ALIGN_BOTTOM)

        self.BaseType = wx.ComboBox(self, style=wx.CB_READONLY)
        top_sizer.AddWindow(self.BaseType, 1, flag=wx.GROW)

        self.Dimensions = CustomEditableListBox(self, label=_("Dimensions:"),
                                                style=(wx.gizmos.EL_ALLOW_NEW |
                                                       wx.gizmos.EL_ALLOW_EDIT |
                                                       wx.gizmos.EL_ALLOW_DELETE))
        for func in ["_OnLabelEndEdit",
                     "_OnAddButton",
                     "_OnDelButton",
                     "_OnUpButton",
                     "_OnDownButton"]:
            setattr(self.Dimensions, func, self.OnDimensionsChanged)
        main_sizer.AddSizer(self.Dimensions, border=20,
                            flag=wx.GROW | wx.LEFT | wx.RIGHT)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL | wx.CENTRE)
        self.Bind(wx.EVT_BUTTON, self.OnOK, button_sizer.GetAffirmativeButton())
        main_sizer.AddSizer(button_sizer, border=20,
                            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.SetSizer(main_sizer)

        for datatype in datatypes:
            self.BaseType.Append(datatype)

        if isinstance(infos, tuple) and infos[0] == "array":
            self.BaseType.SetStringSelection(infos[1])
            self.Dimensions.SetStrings(map("..".join, infos[2]))
        elif infos in datatypes:
            self.BaseType.SetStringSelection(infos)

        self.BaseType.SetFocus()
        self.Fit()

    def GetDimensions(self):
        message = None
        dimensions_list = []
        dimension_strings = self.Dimensions.GetStrings()
        if len(dimension_strings) == 0:
            message = _("Empty dimension isn't allowed.")

        for dimensions in dimension_strings:
            result = DIMENSION_MODEL.match(dimensions)
            if result is None:
                message = _("\"%s\" value isn't a valid array dimension!") % dimensions
                break
            bounds = result.groups()
            if int(bounds[0]) >= int(bounds[1]):
                message = _("\"%s\" value isn't a valid array dimension!\nRight value must be greater than left value.") % dimensions
                break
            dimensions_list.append(bounds)

        if message is not None:
            dlg = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return None
        return dimensions_list

    def OnDimensionsChanged(self, event):
        wx.CallAfter(self.GetDimensions)
        event.Skip()

    def OnOK(self, event):
        if self.GetDimensions() is not None:
            self.EndModal(wx.ID_OK)

    def GetValue(self):
        return "array", self.BaseType.GetStringSelection(), self.GetDimensions()
