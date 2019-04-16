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

from dialogs.BrowseLocationsDialog import BrowseLocationsDialog


class LocationCellControl(wx.PyControl):

    '''
    Custom cell editor control with a text box and a button that launches
    the BrowseLocationsDialog.
    '''
    def __init__(self, parent):
        wx.PyControl.__init__(self, parent)

        main_sizer = wx.FlexGridSizer(cols=2, hgap=0, rows=1, vgap=0)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)

        # create location text control
        self.Location = wx.TextCtrl(self, size=wx.Size(0, -1),
                                    style=wx.TE_PROCESS_ENTER)
        self.Location.Bind(wx.EVT_KEY_DOWN, self.OnLocationChar)
        main_sizer.AddWindow(self.Location, flag=wx.GROW)

        # create browse button
        self.BrowseButton = wx.Button(self, label='...', size=wx.Size(30, -1))
        self.BrowseButton.Bind(wx.EVT_BUTTON, self.OnBrowseButtonClick)
        main_sizer.AddWindow(self.BrowseButton, flag=wx.GROW)

        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.SetSizer(main_sizer)

        self.Controller = None
        self.VarType = None
        self.Default = False
        self.VariableName = None

    def __del__(self):
        self.Controller = None

    def SetController(self, controller):
        self.Controller = controller

    def SetVarType(self, vartype):
        self.VarType = vartype

    def GetVarType(self):
        return self.VarType

    def SetValue(self, value):
        self.Default = value
        self.VariableName = None
        self.VarType = None
        self.Location.SetValue(value)

    def GetValue(self):
        return self.Location.GetValue()

    def GetName(self):
        return self.VariableName

    def OnSize(self, event):
        self.Layout()

    def OnBrowseButtonClick(self, event):
        # pop up the location browser dialog
        dialog = BrowseLocationsDialog(self, self.VarType, self.Controller)
        if dialog.ShowModal() == wx.ID_OK:
            infos = dialog.GetValues()
        else:
            infos = None
        dialog.Destroy()

        if infos is not None:
            location = infos["location"]
            # set the location
            if not infos["location"].startswith("%"):
                dialog = wx.SingleChoiceDialog(
                    self,
                    _("Select a variable class:"),
                    _("Variable class"),
                    [_("Input"), _("Output"), _("Memory")],
                    wx.DEFAULT_DIALOG_STYLE | wx.OK | wx.CANCEL)
                if dialog.ShowModal() == wx.ID_OK:
                    selected = dialog.GetSelection()
                else:
                    selected = None
                dialog.Destroy()
                if selected is None:
                    self.Location.SetFocus()
                    return
                if selected == 0:
                    location = "%I" + location
                elif selected == 1:
                    location = "%Q" + location
                else:
                    location = "%M" + location

            self.Location.SetValue(location)
            self.VariableName = infos["var_name"]
            self.VarType = infos["IEC_type"]

            # when user selected something, end editing immediately
            # so that changes over multiple colums appear
            wx.CallAfter(self.Parent.Parent.CloseEditControl)

        self.Location.SetFocus()

    def OnLocationChar(self, event):
        keycode = event.GetKeyCode()
        if keycode in [wx.WXK_RETURN, wx.WXK_TAB]:
            self.Parent.Parent.ProcessEvent(event)
        elif keycode == wx.WXK_ESCAPE:
            self.Location.SetValue(self.Default)
            self.Parent.Parent.CloseEditControl()
        else:
            event.Skip()

    def SetInsertionPoint(self, i):
        self.Location.SetInsertionPoint(i)

    def SetFocus(self):
        self.Location.SetFocus()


class LocationCellEditor(wx.grid.PyGridCellEditor):
    '''
    Grid cell editor that uses LocationCellControl to display a browse button.
    '''
    def __init__(self, table, controller):
        wx.grid.PyGridCellEditor.__init__(self)

        self.Table = table
        self.Controller = controller

    def __del__(self):
        self.CellControl = None
        self.Controller = None

    def Create(self, parent, id, evt_handler):
        self.CellControl = LocationCellControl(parent)
        self.SetControl(self.CellControl)
        if evt_handler:
            self.CellControl.PushEventHandler(evt_handler)

    def BeginEdit(self, row, col, grid):
        self.CellControl.Enable()
        self.CellControl.SetController(self.Controller)
        self.CellControl.SetValue(self.Table.GetValueByName(row, 'Location'))
        if isinstance(self.CellControl, LocationCellControl):
            self.CellControl.SetVarType(self.Table.GetValueByName(row, 'Type'))
        self.CellControl.SetFocus()

    def EndEditInternal(self, row, col, grid, old_loc):
        loc = self.CellControl.GetValue()
        changed = loc != old_loc
        if changed:
            name = self.CellControl.GetName()
            if name is not None:
                message = self.Table.Parent.CheckVariableName(name, row)
                if message is not None:
                    wx.CallAfter(self.Table.Parent.ShowErrorMessage, message)
                    return None
                old_name = self.Table.GetValueByName(row, 'Name')
                self.Table.SetValueByName(row, 'Name', name)
                self.Table.Parent.OnVariableNameChange(old_name, name)
            self.Table.SetValueByName(row, 'Location', loc)
            var_type = self.CellControl.GetVarType()
            if var_type is not None:
                self.Table.SetValueByName(row, 'Type', var_type)
        else:
            wx.CallAfter(self.Table.Parent.ShowErrorMessage,
                         _("Selected location is identical to previous one"))
        self.CellControl.Disable()
        return changed

    if wx.VERSION >= (3, 0, 0):
        def EndEdit(self, row, col, grid, oldval):
            return self.EndEditInternal(row, col, grid, oldval)
    else:
        def EndEdit(self, row, col, grid):
            old_loc = self.Table.GetValueByName(row, 'Location')
            return self.EndEditInternal(row, col, grid, old_loc)

    def SetSize(self, rect):
        self.CellControl.SetDimensions(rect.x + 1, rect.y,
                                       rect.width, rect.height,
                                       wx.SIZE_ALLOW_MINUS_ONE)

    def Clone(self):
        return LocationCellEditor(self.Table, self.Controller)
