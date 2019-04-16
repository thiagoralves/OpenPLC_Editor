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
from __future__ import division
import re
from builtins import str as text

import wx
import wx.grid
import wx.lib.buttons
from six import string_types
from six.moves import xrange


from plcopen.structures import LOCATIONDATATYPES, TestIdentifier, IEC_KEYWORDS, DefaultType
from plcopen.VariableInfoCollector import _VariableInfos
from graphics.GraphicCommons import REFRESH_HIGHLIGHT_PERIOD, ERROR_HIGHLIGHT
from dialogs.ArrayTypeDialog import ArrayTypeDialog
from controls.CustomGrid import CustomGrid
from controls.CustomTable import CustomTable
from controls.LocationCellEditor import LocationCellEditor
from util.BitmapLibrary import GetBitmap
from util.TranslationCatalogs import NoTranslate


# -------------------------------------------------------------------------------
#                                 Helpers
# -------------------------------------------------------------------------------


[
    TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU, PROJECTTREE,
    POUINSTANCEVARIABLESPANEL, LIBRARYTREE, SCALING, PAGETITLES
] = range(10)


def GetVariableTableColnames(location):
    _ = NoTranslate
    cols = ["#",
            _("Name"),
            _("Class"),
            _("Type"),
            _("Location"),
            _("Initial Value"),
            _("Option"),
            _("Documentation")]
    if not location:
        del cols[4]  # remove 'Location' column
    return cols


def GetOptions(constant=True, retain=True, non_retain=True):
    _ = NoTranslate
    options = [""]
    if constant:
        options.append(_("Constant"))
    if retain:
        options.append(_("Retain"))
    if non_retain:
        options.append(_("Non-Retain"))
    return options


def GetFilterChoiceTransfer():
    _ = NoTranslate
    return {_("All"): _("All"), _("Interface"): _("Interface"),
            _("   Input"): _("Input"), _("   Output"): _("Output"), _("   InOut"): _("InOut"),
            _("   External"): _("External"), _("Variables"): _("Variables"), _("   Local"): _("Local"),
            _("   Temp"): _("Temp"), _("Global"): _("Global")}  # , _("Access") : _("Access")}


CheckOptionForClass = {
    "Local": lambda x: x,
    "Temp": lambda x: "",
    "Input": lambda x: {"Retain": "Retain", "Non-Retain": "Non-Retain"}.get(x, ""),
    "InOut": lambda x: "",
    "Output": lambda x: {"Retain": "Retain", "Non-Retain": "Non-Retain"}.get(x, ""),
    "Global": lambda x: {"Constant": "Constant", "Retain": "Retain"}.get(x, ""),
    "External": lambda x: {"Constant": "Constant"}.get(x, "")
}

LOCATION_MODEL = re.compile(r"((?:%[IQM](?:\*|(?:[XBWLD]?[0-9]+(?:\.[0-9]+)*)))?)$")
LOCATION_MODEL_SET = re.compile(r"((?:%[IQM](?:[XBWLD]?[0-9]+(?:\.[0-9]+)*))?)$")


# -------------------------------------------------------------------------------
#                            Variables Panel Table
# -------------------------------------------------------------------------------


class VariableTable(CustomTable):

    """
    A custom wx.grid.Grid Table using user supplied data
    """
    def __init__(self, parent, data, colnames):
        # The base class must be initialized *first*
        CustomTable.__init__(self, parent, data, colnames)
        self.old_value = None
        self.OPTIONS_DICT = dict([(_(option), option)
                                  for option in GetOptions()])
        self.VARIABLE_CLASSES_DICT = dict([(_(_class), _class)
                                           for _class in GetFilterChoiceTransfer().itervalues()])

    def GetValueByName(self, row, colname):
        if row < self.GetNumberRows():
            return getattr(self.data[row], colname)

    def SetValueByName(self, row, colname, value):
        if row < self.GetNumberRows():
            setattr(self.data[row], colname, value)

    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            if col == 0:
                return self.data[row].Number
            colname = self.GetColLabelValue(col, False)
            if colname == "Initial Value":
                colname = "InitialValue"
            value = getattr(self.data[row], colname, "")
            if colname == "Type" and isinstance(value, tuple):
                if value[0] == "array":
                    return "ARRAY [%s] OF %s" % (",".join(map("..".join, value[2])), value[1])
            if not isinstance(value, string_types):
                value = str(value)
            if colname in ["Class", "Option"]:
                return _(value)
            return value

    def SetValue(self, row, col, value):
        if col < len(self.colnames):
            colname = self.GetColLabelValue(col, False)
            if colname == "Name":
                self.old_value = getattr(self.data[row], colname)
            elif colname == "Class":
                value = self.VARIABLE_CLASSES_DICT[value]
                self.SetValueByName(row, "Option", CheckOptionForClass[value](self.GetValueByName(row, "Option")))
                if value == "External":
                    self.SetValueByName(row, "InitialValue", "")
            elif colname == "Option":
                value = self.OPTIONS_DICT[value]
            elif colname == "Initial Value":
                colname = "InitialValue"
            setattr(self.data[row], colname, value)

    def GetOldValue(self):
        return self.old_value

    def _GetRowEdit(self, row):
        row_edit = self.GetValueByName(row, "Edit")
        var_type = self.Parent.GetTagName()
        bodytype = self.Parent.Controler.GetEditedElementBodyType(var_type)
        if bodytype in ["ST", "IL"]:
            row_edit = True
        return row_edit

    def _updateColAttrs(self, grid):
        """
        wx.grid.Grid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """
        for row in range(self.GetNumberRows()):
            var_class = self.GetValueByName(row, "Class")
            var_type = self.GetValueByName(row, "Type")
            row_highlights = self.Highlights.get(row, {})
            for col in range(self.GetNumberCols()):
                editor = None
                renderer = None
                colname = self.GetColLabelValue(col, False)
                if self.Parent.Debug:
                    grid.SetReadOnly(row, col, True)
                else:
                    if colname == "Option":
                        options = GetOptions(constant=var_class in ["Local", "External", "Global"],
                                             retain=self.Parent.ElementType != "function" and var_class in ["Local", "Input", "Output", "Global"],
                                             non_retain=self.Parent.ElementType != "function" and var_class in ["Local", "Input", "Output"])
                        if len(options) > 1:
                            editor = wx.grid.GridCellChoiceEditor()
                            editor.SetParameters(",".join(map(_, options)))
                        else:
                            grid.SetReadOnly(row, col, True)
                    elif col != 0 and self._GetRowEdit(row):
                        grid.SetReadOnly(row, col, False)
                        if colname == "Name":
                            editor = wx.grid.GridCellTextEditor()
                            renderer = wx.grid.GridCellStringRenderer()
                        elif colname == "Initial Value":
                            if var_class not in ["External", "InOut"]:
                                if self.Parent.Controler.IsEnumeratedType(var_type):
                                    editor = wx.grid.GridCellChoiceEditor()
                                    editor.SetParameters(",".join([""] + self.Parent.Controler.GetEnumeratedDataValues(var_type)))
                                else:
                                    editor = wx.grid.GridCellTextEditor()
                                renderer = wx.grid.GridCellStringRenderer()
                            else:
                                grid.SetReadOnly(row, col, True)
                        elif colname == "Location":
                            if var_class in ["Local", "Global"] and self.Parent.Controler.IsLocatableType(var_type):
                                editor = LocationCellEditor(self, self.Parent.Controler)
                                renderer = wx.grid.GridCellStringRenderer()
                            else:
                                grid.SetReadOnly(row, col, True)
                        elif colname == "Class":
                            if len(self.Parent.ClassList) == 1:
                                grid.SetReadOnly(row, col, True)
                            else:
                                editor = wx.grid.GridCellChoiceEditor()
                                excluded = []
                                if self.Parent.IsFunctionBlockType(var_type):
                                    excluded.extend(["Local", "Temp"])
                                editor.SetParameters(",".join([_(choice) for choice in self.Parent.ClassList if choice not in excluded]))
                    elif colname != "Documentation":
                        grid.SetReadOnly(row, col, True)

                grid.SetCellEditor(row, col, editor)
                grid.SetCellRenderer(row, col, renderer)

                if colname == "Location" and LOCATION_MODEL.match(self.GetValueByName(row, colname)) is None:
                    highlight_colours = ERROR_HIGHLIGHT
                else:
                    highlight_colours = row_highlights.get(colname.lower(), [(wx.WHITE, wx.BLACK)])[-1]
                grid.SetCellBackgroundColour(row, col, highlight_colours[0])
                grid.SetCellTextColour(row, col, highlight_colours[1])
            self.ResizeRow(grid, row)


# -------------------------------------------------------------------------------
#                         Variable Panel Drop Target
# -------------------------------------------------------------------------------


class VariableDropTarget(wx.TextDropTarget):
    '''
    This allows dragging a variable location from somewhere to the Location
    column of a variable row.

    The drag source should be a TextDataObject containing a Python tuple like:
        ('%ID0.0.0', 'location', 'REAL')

    c_ext/CFileEditor.py has an example of this (you can drag a C extension
    variable to the Location column of the variable panel).
    '''
    def __init__(self, parent):
        wx.TextDropTarget.__init__(self)
        self.ParentWindow = parent

    def OnDropText(self, x, y, data):
        self.ParentWindow.ParentWindow.Select()
        x, y = self.ParentWindow.VariablesGrid.CalcUnscrolledPosition(x, y)
        col = self.ParentWindow.VariablesGrid.XToCol(x)
        row = self.ParentWindow.VariablesGrid.YToRow(y)
        message = None
        element_type = self.ParentWindow.ElementType
        try:
            values = eval(data)
        except Exception:
            message = _("Invalid value \"%s\" for variable grid element") % data
            values = None
        if not isinstance(values, tuple):
            message = _("Invalid value \"%s\" for variable grid element") % data
            values = None
        if values is not None:
            if col != wx.NOT_FOUND and row != wx.NOT_FOUND:
                colname = self.ParentWindow.Table.GetColLabelValue(col, False)
                if colname == "Location" and values[1] == "location":
                    if not self.ParentWindow.Table.GetValueByName(row, "Edit"):
                        message = _("Can't give a location to a function block instance")
                    elif self.ParentWindow.Table.GetValueByName(row, "Class") not in ["Local", "Global"]:
                        message = _("Can only give a location to local or global variables")
                    else:
                        location = values[0]
                        variable_type = self.ParentWindow.Table.GetValueByName(row, "Type")
                        base_type = self.ParentWindow.Controler.GetBaseType(variable_type)

                        if values[2] is not None:
                            base_location_type = self.ParentWindow.Controler.GetBaseType(values[2])
                            if values[2] != variable_type and base_type != base_location_type:
                                message = _("Incompatible data types between \"{a1}\" and \"{a2}\"").\
                                          format(a1=values[2], a2=variable_type)

                        if message is None:
                            if not location.startswith("%"):
                                if location[0].isdigit() and base_type != "BOOL":
                                    message = _("Incompatible size of data between \"%s\" and \"BOOL\"") % location
                                elif location[0] not in LOCATIONDATATYPES:
                                    message = _("Unrecognized data size \"%s\"") % location[0]
                                elif base_type not in LOCATIONDATATYPES[location[0]]:
                                    message = _("Incompatible size of data between \"{a1}\" and \"{a2}\"").\
                                              format(a1=location, a2=variable_type)
                                else:
                                    dialog = wx.SingleChoiceDialog(
                                        self.ParentWindow.ParentWindow.ParentWindow,
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
                                        return
                                    if selected == 0:
                                        location = "%I" + location
                                    elif selected == 1:
                                        location = "%Q" + location
                                    else:
                                        location = "%M" + location

                            if message is None:
                                self.ParentWindow.Table.SetValue(row, col, location)
                                self.ParentWindow.Table.ResetView(self.ParentWindow.VariablesGrid)
                                self.ParentWindow.SaveValues()
                elif colname == "Initial Value" and values[1] == "Constant":
                    if not self.ParentWindow.Table.GetValueByName(row, "Edit"):
                        message = _("Can't set an initial value to a function block instance")
                    else:
                        self.ParentWindow.Table.SetValue(row, col, values[0])
                        self.ParentWindow.Table.ResetView(self.ParentWindow.VariablesGrid)
                        self.ParentWindow.SaveValues()
            elif (element_type not in ["config", "resource", "function"] and values[1] == "Global" and
                  self.ParentWindow.Filter in ["All", "Interface", "External"] or
                  element_type != "function" and values[1] in ["location", "NamedConstant"]):
                if values[1] in ["location", "NamedConstant"]:
                    var_name = values[3]
                else:
                    var_name = values[0]
                tagname = self.ParentWindow.GetTagName()
                dlg = wx.TextEntryDialog(
                    self.ParentWindow.ParentWindow.ParentWindow,
                    _("Confirm or change variable name"),
                    _('Variable Drop'), var_name)
                dlg.SetValue(var_name)
                var_name = dlg.GetValue() if dlg.ShowModal() == wx.ID_OK else None
                dlg.Destroy()
                if var_name is None:
                    return
                elif var_name.upper() in [
                        name.upper() for name in
                        self.ParentWindow.Controler.GetProjectPouNames(self.ParentWindow.Debug)]:
                    message = _("\"%s\" pou already exists!") % var_name
                elif not var_name.upper() in [
                        name.upper()
                        for name in self.ParentWindow.Controler.
                        GetEditedElementVariables(tagname, self.ParentWindow.Debug)]:
                    var_infos = self.ParentWindow.DefaultValue.copy()
                    var_infos.Name = var_name
                    var_infos.Type = values[2]
                    var_infos.Documentation = values[4]
                    if values[1] == "location":
                        location = values[0]
                        if not location.startswith("%"):
                            dialog = wx.SingleChoiceDialog(
                                self.ParentWindow.ParentWindow.ParentWindow,
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
                                return
                            if selected == 0:
                                location = "%I" + location
                            elif selected == 1:
                                location = "%Q" + location
                            else:
                                location = "%M" + location
                        if element_type == "functionBlock":
                            configs = self.ParentWindow.Controler.GetProjectConfigNames(
                                self.ParentWindow.Debug)
                            if len(configs) == 0:
                                return
                            if not var_name.upper() in [
                                    name.upper() for name in
                                    self.ParentWindow.Controler.GetConfigurationVariableNames(configs[0])]:
                                self.ParentWindow.Controler.AddConfigurationGlobalVar(
                                    configs[0], values[2], var_name, location, "")
                            var_infos.Class = "External"
                        else:
                            if element_type == "program":
                                var_infos.Class = "Local"
                            else:
                                var_infos.Class = "Global"
                            var_infos.Location = location
                    elif values[1] == "NamedConstant":
                        if element_type in ["functionBlock", "program"]:
                            var_infos.Class = "Local"
                            var_infos.InitialValue = values[0]
                        else:
                            return
                    else:
                        var_infos.Class = "External"
                    var_infos.Number = len(self.ParentWindow.Values)
                    self.ParentWindow.Values.append(var_infos)
                    self.ParentWindow.SaveValues()
                    self.ParentWindow.RefreshValues()
                else:
                    message = _("\"%s\" element for this pou already exists!") % var_name

        if message is not None:
            wx.CallAfter(self.ShowMessage, message)

    def ShowMessage(self, message):
        message = wx.MessageDialog(self.ParentWindow, message, _("Error"), wx.OK | wx.ICON_ERROR)
        message.ShowModal()
        message.Destroy()


# -------------------------------------------------------------------------------
#                               Variable Panel
# -------------------------------------------------------------------------------


class VariablePanel(wx.Panel):

    def __init__(self, parent, window, controler, element_type, debug=False):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)

        self.VARIABLE_CHOICES_DICT = dict([(_(_class), _class) for
                                           _class in GetFilterChoiceTransfer().iterkeys()])

        self.MainSizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=0)
        self.MainSizer.AddGrowableCol(0)
        self.MainSizer.AddGrowableRow(1)

        controls_sizer = wx.FlexGridSizer(cols=10, hgap=5, rows=1, vgap=5)
        controls_sizer.AddGrowableCol(5)
        controls_sizer.AddGrowableRow(0)
        self.MainSizer.AddSizer(controls_sizer, border=5, flag=wx.GROW | wx.ALL)

        self.ReturnTypeLabel = wx.StaticText(self, label=_('Return Type:'))
        controls_sizer.AddWindow(self.ReturnTypeLabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.ReturnType = wx.ComboBox(self,
                                      size=wx.Size(145, -1), style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnReturnTypeChanged, self.ReturnType)
        controls_sizer.AddWindow(self.ReturnType)

        self.DescriptionLabel = wx.StaticText(self, label=_('Description:'))
        controls_sizer.AddWindow(self.DescriptionLabel, flag=wx.ALIGN_CENTER_VERTICAL)

        self.Description = wx.TextCtrl(self,
                                       size=wx.Size(250, -1), style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDescriptionChanged, self.Description)
        self.Description.Bind(wx.EVT_KILL_FOCUS, self.OnDescriptionChanged)
        controls_sizer.AddWindow(self.Description)

        class_filter_label = wx.StaticText(self, label=_('Class Filter:'))
        controls_sizer.AddWindow(class_filter_label, flag=wx.ALIGN_CENTER_VERTICAL)

        self.ClassFilter = wx.ComboBox(self,
                                       size=wx.Size(145, -1), style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnClassFilter, self.ClassFilter)
        controls_sizer.AddWindow(self.ClassFilter)

        for name, bitmap, help in [
                ("AddButton", "add_element", _("Add variable")),
                ("DeleteButton", "remove_element", _("Remove variable")),
                ("UpButton", "up", _("Move variable up")),
                ("DownButton", "down", _("Move variable down"))]:
            button = wx.lib.buttons.GenBitmapButton(self, bitmap=GetBitmap(bitmap),
                                                    size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            controls_sizer.AddWindow(button)

        self.VariablesGrid = CustomGrid(self, style=wx.VSCROLL | wx.HSCROLL)
        self.VariablesGrid.SetDropTarget(VariableDropTarget(self))
        self.VariablesGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE,
                                self.OnVariablesGridCellChange)
        self.VariablesGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                                self.OnVariablesGridCellLeftClick)
        self.VariablesGrid.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN,
                                self.OnVariablesGridEditorShown)
        self.MainSizer.AddWindow(self.VariablesGrid, flag=wx.GROW)

        self.SetSizer(self.MainSizer)

        self.ParentWindow = window
        self.Controler = controler
        self.ElementType = element_type
        self.Debug = debug

        self.RefreshHighlightsTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnRefreshHighlightsTimer,
                  self.RefreshHighlightsTimer)

        self.Filter = "All"
        self.FilterChoices = []
        self.FilterChoiceTransfer = GetFilterChoiceTransfer()

        self.DefaultValue = _VariableInfos("LocalVar0", "", "", "", "", True, "", DefaultType, ([], []), 0)

        if element_type in ["config", "resource"]:
            self.DefaultTypes = {"All": "Global"}
        else:
            self.DefaultTypes = {"All": "Local", "Interface": "Input", "Variables": "Local"}

        if element_type in ["config", "resource"] \
           or element_type in ["program", "transition", "action"]:
            # this is an element that can have located variables
            self.Table = VariableTable(self, [], GetVariableTableColnames(True))

            if element_type in ["config", "resource"]:
                self.FilterChoices = ["All", "Global"]  # ,"Access"]
            else:
                self.FilterChoices = ["All",
                                      "Interface", "   Input", "   Output", "   InOut", "   External",
                                      "Variables", "   Local", "   Temp"]  # ,"Access"]

            # these condense the ColAlignements list
            left = wx.ALIGN_LEFT
            center = wx.ALIGN_CENTER

            #                        Num     Name    Class   Type    Loc     Init    Option   Doc
            self.ColSettings = {
                "size":             [40,     80,     100,    80,     110,    120,    100,     160],
                "alignement":       [center, left,   left,   left,   left,   left,   left,    left],
                "fixed_size":       [True,   False,  True,   False,  True,   True,   True,    False],
            }

        else:
            # this is an element that cannot have located variables
            self.Table = VariableTable(self, [], GetVariableTableColnames(False))

            if element_type == "function":
                self.FilterChoices = ["All",
                                      "Interface", "   Input", "   Output", "   InOut",
                                      "Variables", "   Local"]
            else:
                self.FilterChoices = ["All",
                                      "Interface", "   Input", "   Output", "   InOut", "   External",
                                      "Variables", "   Local", "   Temp"]

            # these condense the alignements list
            left = wx.ALIGN_LEFT
            center = wx.ALIGN_CENTER

            #                        Num     Name    Class   Type    Init    Option   Doc
            self.ColSettings = {
                "size":             [40,     80,     100,    80,     120,    100,     160],
                "alignement":       [center, left,   left,   left,   left,   left,    left],
                "fixed_size":       [True,   False,  True,   False,  True,   True,    False],
            }

        self.PanelWidthMin = sum(self.ColSettings["size"])

        self.ElementType = element_type
        self.BodyType = None

        for choice in self.FilterChoices:
            self.ClassFilter.Append(_(choice))

        reverse_transfer = {}
        for filter, choice in self.FilterChoiceTransfer.items():
            reverse_transfer[choice] = filter
        self.ClassFilter.SetStringSelection(_(reverse_transfer[self.Filter]))
        self.RefreshTypeList()

        self.VariablesGrid.SetTable(self.Table)
        self.VariablesGrid.SetButtons({"Add": self.AddButton,
                                       "Delete": self.DeleteButton,
                                       "Up": self.UpButton,
                                       "Down": self.DownButton})
        self.VariablesGrid.SetEditable(not self.Debug)

        def _AddVariable(new_row):
            row_content = self.DefaultValue.copy()
            if new_row > 0:
                # doesn't copy values of previous var if it's non-editable (like a FB)
                if self.Values[new_row-1].Edit:
                    row_content = self.Values[new_row-1].copy()
                old_name = self.Values[new_row-1].Name
                row_content.Name = self.Controler.GenerateNewName(
                    self.TagName, old_name, old_name+'%d')

                # increment location address
                if row_content.Location != "" and LOCATION_MODEL_SET.match(row_content.Location):
                    old_location = row_content.Location
                    model = re.compile(r"%[IQM][XBWLD]?(.*\.|)")
                    prefix = model.match(old_location).group(0)
                    addr = int(re.split(model, old_location)[-1]) + 1
                    row_content.Location = prefix + text(addr)

            if not row_content.Class:
                row_content.Class = self.DefaultTypes.get(self.Filter, self.Filter)

            if self.Filter == "All" and len(self.Values) > 0:
                self.Values.insert(new_row, row_content)
            else:
                self.Values.append(row_content)
                new_row = self.Table.GetNumberRows()
            self.SaveValues()
            if self.ElementType == "resource":
                self.ParentWindow.RefreshView(variablepanel=False)
            self.RefreshValues()
            return new_row
        setattr(self.VariablesGrid, "_AddRow", _AddVariable)

        def _DeleteVariable(row):
            if _GetRowEdit(row):
                self.Values.remove(self.Table.GetRow(row))
                self.SaveValues()
                if self.ElementType == "resource":
                    self.ParentWindow.RefreshView(variablepanel=False)
                self.RefreshValues()
        setattr(self.VariablesGrid, "_DeleteRow", _DeleteVariable)

        def _MoveVariable(row, move):
            if self.Filter == "All":
                new_row = max(0, min(row + move, len(self.Values) - 1))
                if new_row != row:
                    self.Values.insert(new_row, self.Values.pop(row))
                    self.SaveValues()
                    self.RefreshValues()
                return new_row
            return row
        setattr(self.VariablesGrid, "_MoveRow", _MoveVariable)

        def _GetRowEdit(row):
            row_edit = False
            if self:
                row_edit = self.Table.GetValueByName(row, "Edit")
                bodytype = self.Controler.GetEditedElementBodyType(self.TagName)
                row_edit = row_edit or (bodytype in ["ST", "IL"])
            return row_edit

        def _RefreshButtons():
            if self:
                table_length = len(self.Table.data)
                row_edit = True
                row = 0
                if table_length > 0:
                    row = self.VariablesGrid.GetGridCursorRow()
                    row_edit = _GetRowEdit(row)
                self.AddButton.Enable(not self.Debug)
                self.DeleteButton.Enable(not self.Debug and (table_length > 0 and row_edit))
                self.UpButton.Enable(not self.Debug and (table_length > 0 and row > 0 and self.Filter == "All"))
                self.DownButton.Enable(not self.Debug and (table_length > 0 and row < table_length - 1 and self.Filter == "All"))
        setattr(self.VariablesGrid, "RefreshButtons", _RefreshButtons)

        panel_width = window.Parent.ScreenRect.Width - 35
        if panel_width > self.PanelWidthMin:
            stretch_cols_width = panel_width
            stretch_cols_sum = 0
            for col in range(len(self.ColSettings["fixed_size"])):
                if self.ColSettings["fixed_size"][col]:
                    stretch_cols_width -= self.ColSettings["size"][col]
                else:
                    stretch_cols_sum += self.ColSettings["size"][col]

        self.VariablesGrid.SetRowLabelSize(0)
        for col in range(self.Table.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.ColSettings["alignement"][col], wx.ALIGN_CENTRE)
            self.VariablesGrid.SetColAttr(col, attr)
            self.VariablesGrid.SetColMinimalWidth(col, self.ColSettings["size"][col])
            if (panel_width > self.PanelWidthMin) and not self.ColSettings["fixed_size"][col]:
                self.VariablesGrid.SetColSize(col, int((self.ColSettings["size"][col]/stretch_cols_sum)*stretch_cols_width))
            else:
                self.VariablesGrid.SetColSize(col, self.ColSettings["size"][col])

    def __del__(self):
        self.RefreshHighlightsTimer.Stop()

    def SetTagName(self, tagname):
        self.TagName = tagname
        self.BodyType = self.Controler.GetEditedElementBodyType(self.TagName)

    def GetTagName(self):
        return self.TagName

    def IsFunctionBlockType(self, name):
        if isinstance(name, tuple) or \
           self.ElementType != "function" and self.BodyType in ["ST", "IL"]:
            return False
        else:
            return self.Controler.GetBlockType(name, debug=self.Debug) is not None

    def RefreshView(self):
        self.PouNames = self.Controler.GetProjectPouNames(self.Debug)
        returnType = None
        description = None

        words = self.TagName.split("::")
        if self.ElementType == "config":
            self.Values = self.Controler.GetConfigurationGlobalVars(words[1], self.Debug)
        elif self.ElementType == "resource":
            self.Values = self.Controler.GetConfigurationResourceGlobalVars(words[1], words[2], self.Debug)
        else:
            if self.ElementType == "function":
                self.ReturnType.Clear()
                for data_type in self.Controler.GetDataTypes(self.TagName, debug=self.Debug):
                    self.ReturnType.Append(data_type)
                returnType = self.Controler.GetEditedElementInterfaceReturnType(self.TagName, debug=self.Debug)
            description = self.Controler.GetPouDescription(words[1])
            self.Values = self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug)

        if returnType is not None:
            self.ReturnType.SetStringSelection(returnType)
            self.ReturnType.Enable(not self.Debug)
            self.ReturnTypeLabel.Show()
            self.ReturnType.Show()
        else:
            self.ReturnType.Enable(False)
            self.ReturnTypeLabel.Hide()
            self.ReturnType.Hide()

        if description is not None:
            self.Description.SetValue(description)
            self.Description.Enable(not self.Debug)
            self.DescriptionLabel.Show()
            self.Description.Show()
        else:
            self.Description.Enable(False)
            self.DescriptionLabel.Hide()
            self.Description.Hide()

        self.RefreshValues()
        self.VariablesGrid.RefreshButtons()
        self.MainSizer.Layout()

    def OnReturnTypeChanged(self, event):
        words = self.TagName.split("::")
        self.Controler.SetPouInterfaceReturnType(words[1], self.ReturnType.GetStringSelection())
        self.Controler.BufferProject()
        self.ParentWindow.RefreshView(variablepanel=False)
        self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        event.Skip()

    def OnDescriptionChanged(self, event):
        words = self.TagName.split("::")
        old_description = self.Controler.GetPouDescription(words[1])
        new_description = self.Description.GetValue()
        if new_description != old_description:
            self.Controler.SetPouDescription(words[1], new_description)
            self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        event.Skip()

    def OnClassFilter(self, event):
        self.Filter = self.FilterChoiceTransfer[self.VARIABLE_CHOICES_DICT[self.ClassFilter.GetStringSelection()]]
        self.RefreshTypeList()
        self.RefreshValues()
        self.VariablesGrid.RefreshButtons()
        event.Skip()

    def RefreshTypeList(self):
        if self.Filter == "All":
            self.ClassList = [self.FilterChoiceTransfer[choice] for choice in self.FilterChoices if self.FilterChoiceTransfer[choice] not in ["All", "Interface", "Variables"]]
        elif self.Filter == "Interface":
            self.ClassList = ["Input", "Output", "InOut", "External"]
        elif self.Filter == "Variables":
            self.ClassList = ["Local", "Temp"]
        else:
            self.ClassList = [self.Filter]

    def ShowErrorMessage(self, message):
        dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def OnVariableNameChange(self, old_name, new_name):
        """ propagate renaming of variable to the rest of the project """
        if old_name != "":
            self.Controler.UpdateEditedElementUsedVariable(self.TagName, old_name, new_name)
        self.Controler.BufferProject()
        wx.CallAfter(self.ParentWindow.RefreshView, False)
        self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)

    def CheckVariableName(self, value, row):
        if not TestIdentifier(value):
            message = _("\"%s\" is not a valid identifier!") % value
        elif value.upper() in IEC_KEYWORDS:
            message = _("\"%s\" is a keyword. It can't be used!") % value
        elif value.upper() in self.PouNames:
            message = _("A POU named \"%s\" already exists!") % value
        elif value.upper() in [var.Name.upper() for var in self.Values if var != self.Table.data[row]]:
            message = _("A variable with \"%s\" as name already exists in this pou!") % value
        else:
            return None
        return message

    def OnVariablesGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        colname = self.Table.GetColLabelValue(col, False)
        value = self.Table.GetValue(row, col)
        message = None

        if colname == "Name" and value != "":
            message = self.CheckVariableName(value, row)
            if message is None:
                self.SaveValues(False)
                old_value = self.Table.GetOldValue()
                self.OnVariableNameChange(old_value, value)
        else:
            self.SaveValues()
            if colname == "Class":
                self.ClearLocation(row, col, value)
                wx.CallAfter(self.ParentWindow.RefreshView)
            elif colname == "Location":
                wx.CallAfter(self.ParentWindow.RefreshView)

        if message is not None:
            wx.CallAfter(self.ShowErrorMessage, message)
            event.Veto()
        else:
            event.Skip()

    def ClearLocation(self, row, col, value):
        if self.Values[row].Location != '':
            if self.Table.GetColLabelValue(col, False) == 'Class' and value not in ["Local", "Global"] or \
               self.Table.GetColLabelValue(col, False) == 'Type' and not self.Controler.IsLocatableType(value):
                self.Values[row].Location = ''
                self.RefreshValues()
                self.SaveValues()

    def BuildStdIECTypesMenu(self, type_menu):
        # build a submenu containing standard IEC types
        base_menu = wx.Menu(title='')
        for base_type in self.Controler.GetBaseTypes():
            item = base_menu.Append(wx.ID_ANY, help='', kind=wx.ITEM_NORMAL, text=base_type)
            self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(base_type), item)

        type_menu.AppendMenu(wx.ID_ANY, _("Base Types"), base_menu)

    def BuildUserTypesMenu(self, type_menu):
        # build a submenu containing user-defined types
        datatype_menu = wx.Menu(title='')
        datatypes = self.Controler.GetDataTypes(basetypes=False, confnodetypes=False)
        for datatype in datatypes:
            item = datatype_menu.Append(wx.ID_ANY, help='', kind=wx.ITEM_NORMAL, text=datatype)
            self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(datatype), item)

        type_menu.AppendMenu(wx.ID_ANY, _("User Data Types"), datatype_menu)

    def BuildLibsTypesMenu(self, type_menu):
        for category in self.Controler.GetConfNodeDataTypes():
            if len(category["list"]) > 0:
                # build a submenu containing confnode types
                confnode_datatype_menu = wx.Menu(title='')
                for datatype in category["list"]:
                    item = confnode_datatype_menu.Append(wx.ID_ANY, help='', kind=wx.ITEM_NORMAL, text=datatype)
                    self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(datatype), item)

                type_menu.AppendMenu(wx.ID_ANY, category["name"], confnode_datatype_menu)

    def BuildProjectTypesMenu(self, type_menu, classtype):
        # build a submenu containing function block types
        bodytype = self.Controler.GetEditedElementBodyType(self.TagName)
        _pouname, poutype = self.Controler.GetEditedElementType(self.TagName)
        if classtype in ["Input", "Output", "InOut", "External", "Global"] or \
           poutype != "function" and bodytype in ["ST", "IL"]:
            functionblock_menu = wx.Menu(title='')
            fbtypes = self.Controler.GetFunctionBlockTypes(self.TagName)
            for functionblock_type in fbtypes:
                item = functionblock_menu.Append(wx.ID_ANY, help='', kind=wx.ITEM_NORMAL, text=functionblock_type)
                self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(functionblock_type), item)

            type_menu.AppendMenu(wx.ID_ANY, _("Function Block Types"), functionblock_menu)

    def BuildArrayTypesMenu(self, type_menu):
        item = type_menu.Append(wx.ID_ANY, help='', kind=wx.ITEM_NORMAL, text=_("Array"))
        self.Bind(wx.EVT_MENU, self.VariableArrayTypeFunction, item)

    def OnVariablesGridEditorShown(self, event):
        row, col = event.GetRow(), event.GetCol()

        label_value = self.Table.GetColLabelValue(col, False)
        if label_value == "Type":
            old_value = self.Values[row].Type
            classtype = self.Table.GetValueByName(row, "Class")
            type_menu = wx.Menu(title='')   # the root menu

            self.BuildStdIECTypesMenu(type_menu)

            self.BuildUserTypesMenu(type_menu)

            self.BuildLibsTypesMenu(type_menu)

            self.BuildProjectTypesMenu(type_menu, classtype)

            self.BuildArrayTypesMenu(type_menu)

            rect = self.VariablesGrid.BlockToDeviceRect((row, col), (row, col))
            corner_x = rect.x + rect.width
            corner_y = rect.y + self.VariablesGrid.GetColLabelSize()

            # pop up this new menu
            self.VariablesGrid.PopupMenuXY(type_menu, corner_x, corner_y)
            type_menu.Destroy()
            event.Veto()
            value = self.Values[row].Type
            if old_value != value:
                self.ClearLocation(row, col, value)
        else:
            event.Skip()

    def GetVariableTypeFunction(self, base_type):
        def VariableTypeFunction(event):
            row = self.VariablesGrid.GetGridCursorRow()
            self.Table.SetValueByName(row, "Type", base_type)
            self.Table.ResetView(self.VariablesGrid)
            self.SaveValues(False)
            self.ParentWindow.RefreshView(variablepanel=False)
            self.Controler.BufferProject()
            self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        return VariableTypeFunction

    def VariableArrayTypeFunction(self, event):
        row = self.VariablesGrid.GetGridCursorRow()
        dialog = ArrayTypeDialog(self,
                                 self.Controler.GetDataTypes(self.TagName),
                                 self.Table.GetValueByName(row, "Type"))
        if dialog.ShowModal() == wx.ID_OK:
            self.Table.SetValueByName(row, "Type", dialog.GetValue())
            self.Table.ResetView(self.VariablesGrid)
            self.SaveValues(False)
            self.ParentWindow.RefreshView(variablepanel=False)
            self.Controler.BufferProject()
            self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        dialog.Destroy()

    def OnVariablesGridCellLeftClick(self, event):
        row = event.GetRow()
        if not self.Debug and (event.GetCol() == 0 and self.Table.GetValueByName(row, "Edit")):
            var_name = self.Table.GetValueByName(row, "Name")
            var_class = self.Table.GetValueByName(row, "Class")
            var_type = self.Table.GetValueByName(row, "Type")
            data = wx.TextDataObject(str((var_name, var_class, var_type, self.TagName)))
            dragSource = wx.DropSource(self.VariablesGrid)
            dragSource.SetData(data)
            dragSource.DoDragDrop()
        event.Skip()

    def RefreshValues(self):
        data = []
        for num, variable in enumerate(self.Values):
            if variable.Class in self.ClassList:
                variable.Number = num + 1
                data.append(variable)
        self.Table.SetData(data)
        self.Table.ResetView(self.VariablesGrid)

    def SaveValues(self, buffer=True):
        words = self.TagName.split("::")
        if self.ElementType == "config":
            self.Controler.SetConfigurationGlobalVars(words[1], self.Values)
        elif self.ElementType == "resource":
            self.Controler.SetConfigurationResourceGlobalVars(words[1], words[2], self.Values)
        else:
            if self.ReturnType.IsEnabled():
                self.Controler.SetPouInterfaceReturnType(words[1], self.ReturnType.GetStringSelection())
            self.Controler.SetPouInterfaceVars(words[1], self.Values)
        if buffer:
            self.Controler.BufferProject()
            self.ParentWindow._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def OnRefreshHighlightsTimer(self, event):
        self.Table.ResetView(self.VariablesGrid)
        event.Skip()

    def AddVariableHighlight(self, infos, highlight_type):
        if isinstance(infos[0], tuple):
            for i in xrange(*infos[0]):
                self.Table.AddHighlight((i,) + infos[1:], highlight_type)
            cell_visible = infos[0][0]
        else:
            self.Table.AddHighlight(infos, highlight_type)
            cell_visible = infos[0]
        colnames = [colname.lower() for colname in self.Table.colnames]
        self.VariablesGrid.MakeCellVisible(cell_visible, colnames.index(infos[1]))
        self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def RemoveVariableHighlight(self, infos, highlight_type):
        if isinstance(infos[0], tuple):
            for i in xrange(*infos[0]):
                self.Table.RemoveHighlight((i,) + infos[1:], highlight_type)
        else:
            self.Table.RemoveHighlight(infos, highlight_type)
        self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def ClearHighlights(self, highlight_type=None):
        self.Table.ClearHighlights(highlight_type)
        self.Table.ResetView(self.VariablesGrid)
