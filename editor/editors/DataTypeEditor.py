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
import re
from six.moves import xrange

import wx
import wx.grid
import wx.lib.buttons
from plcopen.structures import IEC_KEYWORDS, TestIdentifier, DefaultType
from graphics.GraphicCommons import REFRESH_HIGHLIGHT_PERIOD
from controls import CustomEditableListBox, CustomGrid, CustomTable, CustomIntCtrl
from dialogs import ArrayTypeDialog
from editors.EditorPanel import EditorPanel
from util.BitmapLibrary import GetBitmap
from util.TranslationCatalogs import NoTranslate

# -------------------------------------------------------------------------------
#                                    Helpers
# -------------------------------------------------------------------------------

DIMENSION_MODEL = re.compile(r"([0-9]+)\.\.([0-9]+)$")


def AppendMenu(parent, help, id, kind, text):
    parent.Append(help=help, id=id, kind=kind, text=text)


def GetElementsTableColnames():
    _ = NoTranslate
    return ["#", _("Name"), _("Type"), _("Initial Value")]


def GetDatatypeTypes():
    _ = NoTranslate
    return [_("Directly"), _("Subrange"), _("Enumerated"), _("Array"), _("Structure")]


# -------------------------------------------------------------------------------
#                            Structure Elements Table
# -------------------------------------------------------------------------------


class ElementsTable(CustomTable):

    """
    A custom wx.grid.Grid Table using user supplied data
    """
    def __init__(self, parent, data, colnames):
        # The base class must be initialized *first*
        CustomTable.__init__(self, parent, data, colnames)
        self.old_value = None

    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            if col == 0:
                return row + 1
            colname = self.GetColLabelValue(col, False)
            value = self.data[row].get(colname, "")

            if colname == "Type" and isinstance(value, tuple):
                if value[0] == "array":
                    return "ARRAY [%s] OF %s" % (",".join(map("..".join, value[2])), value[1])
            return value

    def SetValue(self, row, col, value):
        if col < len(self.colnames):
            colname = self.GetColLabelValue(col, False)
            if colname == "Name":
                self.old_value = self.data[row][colname]
            self.data[row][colname] = value

    def GetOldValue(self):
        return self.old_value

    def _updateColAttrs(self, grid):
        """
        wx.grid.Grid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """

        for row in range(self.GetNumberRows()):
            row_highlights = self.Highlights.get(row, {})
            for col in range(self.GetNumberCols()):
                editor = None
                renderer = None
                colname = self.GetColLabelValue(col, False)
                if col != 0:
                    grid.SetReadOnly(row, col, False)
                    if colname == "Name":
                        editor = wx.grid.GridCellTextEditor()
                        renderer = wx.grid.GridCellStringRenderer()
                    elif colname == "Initial Value":
                        editor = wx.grid.GridCellTextEditor()
                        renderer = wx.grid.GridCellStringRenderer()
                    elif colname == "Type":
                        editor = wx.grid.GridCellTextEditor()
                else:
                    grid.SetReadOnly(row, col, True)

                grid.SetCellEditor(row, col, editor)
                grid.SetCellRenderer(row, col, renderer)

                highlight_colours = row_highlights.get(colname.lower(), [(wx.WHITE, wx.BLACK)])[-1]
                grid.SetCellBackgroundColour(row, col, highlight_colours[0])
                grid.SetCellTextColour(row, col, highlight_colours[1])
            self.ResizeRow(grid, row)

    def AddHighlight(self, infos, highlight_type):
        row_highlights = self.Highlights.setdefault(infos[0], {})
        if infos[1] == "initial":
            col_highlights = row_highlights.setdefault("initial value", [])
        else:
            col_highlights = row_highlights.setdefault(infos[1], [])
        col_highlights.append(highlight_type)

# -------------------------------------------------------------------------------
#                          Datatype Editor class
# -------------------------------------------------------------------------------


class DataTypeEditor(EditorPanel):

    def _init_Editor(self, parent):
        self.Editor = wx.Panel(parent, style=wx.SUNKEN_BORDER)

        self.MainSizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=10)
        self.MainSizer.AddGrowableCol(0)
        self.MainSizer.AddGrowableRow(1)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.MainSizer.AddSizer(top_sizer, border=5,
                                flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        derivation_type_label = wx.StaticText(self.Editor, label=_('Derivation Type:'))
        top_sizer.AddWindow(derivation_type_label, border=5,
                            flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT)

        self.DerivationType = wx.ComboBox(self.Editor,
                                          size=wx.Size(200, -1), style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnDerivationTypeChanged, self.DerivationType)
        top_sizer.AddWindow(self.DerivationType, border=5, flag=wx.GROW | wx.RIGHT)

        typeinfos_staticbox = wx.StaticBox(self.Editor, label=_('Type infos:'))
        typeinfos_sizer = wx.StaticBoxSizer(typeinfos_staticbox, wx.HORIZONTAL)
        self.MainSizer.AddSizer(typeinfos_sizer, border=5,
                                flag=wx.GROW | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        # Panel for Directly derived data types

        self.DirectlyPanel = wx.Panel(self.Editor, style=wx.TAB_TRAVERSAL)
        typeinfos_sizer.AddWindow(self.DirectlyPanel, 1)

        directly_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        directly_basetype_label = wx.StaticText(self.DirectlyPanel,
                                                label=_('Base Type:'))
        directly_panel_sizer.AddWindow(directly_basetype_label, 1, border=5,
                                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.DirectlyBaseType = wx.ComboBox(self.DirectlyPanel, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnInfosChanged, self.DirectlyBaseType)
        directly_panel_sizer.AddWindow(self.DirectlyBaseType, 1, border=5,
                                       flag=wx.GROW | wx.ALL)

        directly_initialvalue_label = wx.StaticText(self.DirectlyPanel,
                                                    label=_('Initial Value:'))
        directly_panel_sizer.AddWindow(directly_initialvalue_label, 1, border=5,
                                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.DirectlyInitialValue = wx.TextCtrl(self.DirectlyPanel,
                                                style=wx.TE_PROCESS_ENTER | wx.TE_RICH)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnReturnKeyPressed, self.DirectlyInitialValue)
        directly_panel_sizer.AddWindow(self.DirectlyInitialValue, 1, border=5,
                                       flag=wx.ALL)

        self.DirectlyPanel.SetSizer(directly_panel_sizer)

        # Panel for Subrange data types

        self.SubrangePanel = wx.Panel(self.Editor, style=wx.TAB_TRAVERSAL)
        typeinfos_sizer.AddWindow(self.SubrangePanel, 1)

        subrange_panel_sizer = wx.GridSizer(cols=4, hgap=5, rows=3, vgap=0)

        subrange_basetype_label = wx.StaticText(self.SubrangePanel,
                                                label=_('Base Type:'))
        subrange_panel_sizer.AddWindow(subrange_basetype_label, 1, border=5,
                                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.SubrangeBaseType = wx.ComboBox(self.SubrangePanel, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnSubrangeBaseTypeChanged,
                  self.SubrangeBaseType)
        subrange_panel_sizer.AddWindow(self.SubrangeBaseType, 1, border=5,
                                       flag=wx.GROW | wx.ALL)

        subrange_initialvalue_label = wx.StaticText(self.SubrangePanel,
                                                    label=_('Initial Value:'))
        subrange_panel_sizer.AddWindow(subrange_initialvalue_label, 1, border=5,
                                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.SubrangeInitialValue = CustomIntCtrl(self.SubrangePanel, style=wx.TAB_TRAVERSAL)
        self.SubrangeInitialValue.Bind(CustomIntCtrl.EVT_CUSTOM_INT, self.OnInfosChanged)
        subrange_panel_sizer.AddWindow(self.SubrangeInitialValue, 1, border=5,
                                       flag=wx.GROW | wx.ALL)

        subrange_minimum_label = wx.StaticText(self.SubrangePanel, label=_('Minimum:'))
        subrange_panel_sizer.AddWindow(subrange_minimum_label, 1, border=5,
                                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.SubrangeMinimum = CustomIntCtrl(self.SubrangePanel, style=wx.TAB_TRAVERSAL)
        self.SubrangeMinimum.Bind(CustomIntCtrl.EVT_CUSTOM_INT, self.OnSubrangeMinimumChanged)
        subrange_panel_sizer.AddWindow(self.SubrangeMinimum, 1, border=5,
                                       flag=wx.GROW | wx.ALL)

        for dummy in xrange(2):
            subrange_panel_sizer.AddWindow(wx.Size(0, 0), 1)

        subrange_maximum_label = wx.StaticText(self.SubrangePanel,
                                               label=_('Maximum:'))
        subrange_panel_sizer.AddWindow(subrange_maximum_label, 1, border=5,
                                       flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.SubrangeMaximum = CustomIntCtrl(self.SubrangePanel, style=wx.TAB_TRAVERSAL)
        self.SubrangeMaximum.Bind(CustomIntCtrl.EVT_CUSTOM_INT, self.OnSubrangeMaximumChanged)

        subrange_panel_sizer.AddWindow(self.SubrangeMaximum, 1, border=5,
                                       flag=wx.GROW | wx.ALL)

        self.SubrangePanel.SetSizer(subrange_panel_sizer)

        # Panel for Enumerated data types

        self.EnumeratedPanel = wx.Panel(self.Editor, style=wx.TAB_TRAVERSAL)
        typeinfos_sizer.AddWindow(self.EnumeratedPanel, 1)

        enumerated_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.EnumeratedValues = CustomEditableListBox(
            self.EnumeratedPanel,
            label=_("Values:"),
            style=(wx.gizmos.EL_ALLOW_NEW |
                   wx.gizmos.EL_ALLOW_EDIT |
                   wx.gizmos.EL_ALLOW_DELETE))
        setattr(self.EnumeratedValues, "_OnLabelEndEdit", self.OnEnumeratedValueEndEdit)
        for func in ["_OnAddButton", "_OnDelButton", "_OnUpButton", "_OnDownButton"]:
            setattr(self.EnumeratedValues, func, self.OnEnumeratedValuesChanged)
        enumerated_panel_sizer.AddWindow(self.EnumeratedValues, 1, border=5,
                                         flag=wx.GROW | wx.ALL)

        enumerated_panel_rightsizer = wx.BoxSizer(wx.HORIZONTAL)
        enumerated_panel_sizer.AddSizer(enumerated_panel_rightsizer, 1)

        enumerated_initialvalue_label = wx.StaticText(self.EnumeratedPanel,
                                                      label=_('Initial Value:'))
        enumerated_panel_rightsizer.AddWindow(enumerated_initialvalue_label, 1,
                                              border=5,
                                              flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.EnumeratedInitialValue = wx.ComboBox(self.EnumeratedPanel,
                                                  style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnInfosChanged, self.EnumeratedInitialValue)
        enumerated_panel_rightsizer.AddWindow(self.EnumeratedInitialValue, 1,
                                              border=5, flag=wx.ALL)

        self.EnumeratedPanel.SetSizer(enumerated_panel_sizer)

        # Panel for Array data types

        self.ArrayPanel = wx.Panel(self.Editor, style=wx.TAB_TRAVERSAL)
        typeinfos_sizer.AddWindow(self.ArrayPanel, 1)

        array_panel_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=2, vgap=0)
        array_panel_sizer.AddGrowableCol(0)
        array_panel_sizer.AddGrowableCol(1)
        array_panel_sizer.AddGrowableRow(1)

        array_panel_leftSizer = wx.BoxSizer(wx.HORIZONTAL)
        array_panel_sizer.AddSizer(array_panel_leftSizer, flag=wx.GROW)

        array_basetype_label = wx.StaticText(self.ArrayPanel, label=_('Base Type:'))
        array_panel_leftSizer.AddWindow(array_basetype_label, 1, border=5,
                                        flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.ArrayBaseType = wx.ComboBox(self.ArrayPanel, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnInfosChanged, self.ArrayBaseType)
        array_panel_leftSizer.AddWindow(self.ArrayBaseType, 1, border=5,
                                        flag=wx.GROW | wx.ALL)

        array_panel_rightsizer = wx.BoxSizer(wx.HORIZONTAL)
        array_panel_sizer.AddSizer(array_panel_rightsizer, flag=wx.GROW)

        array_initialvalue_label = wx.StaticText(self.ArrayPanel,
                                                 label=_('Initial Value:'))
        array_panel_rightsizer.AddWindow(array_initialvalue_label, 1, border=5,
                                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        self.ArrayInitialValue = wx.TextCtrl(self.ArrayPanel,
                                             style=wx.TE_PROCESS_ENTER | wx.TE_RICH)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnReturnKeyPressed, self.ArrayInitialValue)
        array_panel_rightsizer.AddWindow(self.ArrayInitialValue, 1, border=5,
                                         flag=wx.ALL)

        self.ArrayDimensions = CustomEditableListBox(
            self.ArrayPanel,
            label=_("Dimensions:"),
            style=(wx.gizmos.EL_ALLOW_NEW |
                   wx.gizmos.EL_ALLOW_EDIT |
                   wx.gizmos.EL_ALLOW_DELETE))
        for func in ["_OnLabelEndEdit", "_OnAddButton", "_OnDelButton",
                     "_OnUpButton", "_OnDownButton"]:
            setattr(self.ArrayDimensions, func, self.OnDimensionsChanged)
        array_panel_sizer.AddWindow(self.ArrayDimensions, 0, border=5,
                                    flag=wx.GROW | wx.ALL)

        self.ArrayPanel.SetSizer(array_panel_sizer)

        # Panel for Structure data types

        self.StructurePanel = wx.Panel(self.Editor, style=wx.TAB_TRAVERSAL)
        typeinfos_sizer.AddWindow(self.StructurePanel, 1)

        structure_panel_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
        structure_panel_sizer.AddGrowableCol(0)
        structure_panel_sizer.AddGrowableRow(1)

        structure_button_sizer = wx.FlexGridSizer(cols=5, hgap=5, rows=1, vgap=0)
        structure_button_sizer.AddGrowableCol(0)
        structure_button_sizer.AddGrowableRow(0)
        structure_panel_sizer.AddSizer(structure_button_sizer, 0, border=5,
                                       flag=wx.ALL | wx.GROW)

        structure_elements_label = wx.StaticText(self.StructurePanel,
                                                 label=_('Elements :'))
        structure_button_sizer.AddWindow(structure_elements_label, flag=wx.ALIGN_BOTTOM)

        for name, bitmap, help in [
                ("StructureAddButton", "add_element", _("Add element")),
                ("StructureDeleteButton", "remove_element", _("Remove element")),
                ("StructureUpButton", "up", _("Move element up")),
                ("StructureDownButton", "down", _("Move element down"))]:
            button = wx.lib.buttons.GenBitmapButton(self.StructurePanel,
                                                    bitmap=GetBitmap(bitmap),
                                                    size=wx.Size(28, 28),
                                                    style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            structure_button_sizer.AddWindow(button)

        self.StructureElementsGrid = CustomGrid(self.StructurePanel,
                                                size=wx.Size(0, 150), style=wx.VSCROLL)
        self.StructureElementsGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE,
                                        self.OnStructureElementsGridCellChange)
        self.StructureElementsGrid.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN,
                                        self.OnStructureElementsGridEditorShown)
        structure_panel_sizer.AddWindow(self.StructureElementsGrid, flag=wx.GROW)

        self.StructurePanel.SetSizer(structure_panel_sizer)

        self.Editor.SetSizer(self.MainSizer)

    def __init__(self, parent, tagname, window, controler):
        EditorPanel.__init__(self, parent, tagname, window, controler)

        self.StructureElementDefaultValue = {"Name": "", "Type": DefaultType, "Initial Value": ""}
        self.StructureElementsTable = ElementsTable(self, [], GetElementsTableColnames())
        self.StructureColSizes = [40, 150, 100, 250]
        self.StructureColAlignements = [wx.ALIGN_CENTER, wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_LEFT]

        self.StructureElementsGrid.SetTable(self.StructureElementsTable)
        self.StructureElementsGrid.SetButtons({"Add": self.StructureAddButton,
                                               "Delete": self.StructureDeleteButton,
                                               "Up": self.StructureUpButton,
                                               "Down": self.StructureDownButton})

        self.DATATYPE_TYPES_DICT = dict([(_(datatype), datatype) for datatype in GetDatatypeTypes()])

        def _AddStructureElement(new_row):
            self.StructureElementsTable.InsertRow(new_row, self.StructureElementDefaultValue.copy())
            self.RefreshTypeInfos()
            self.StructureElementsTable.ResetView(self.StructureElementsGrid)
            return new_row
        setattr(self.StructureElementsGrid, "_AddRow", _AddStructureElement)

        def _DeleteStructureElement(row):
            self.StructureElementsTable.RemoveRow(row)
            self.RefreshTypeInfos()
            self.StructureElementsTable.ResetView(self.StructureElementsGrid)
        setattr(self.StructureElementsGrid, "_DeleteRow", _DeleteStructureElement)

        def _MoveStructureElement(row, move):
            new_row = self.StructureElementsTable.MoveRow(row, move)
            if new_row != row:
                self.RefreshTypeInfos()
                self.StructureElementsTable.ResetView(self.StructureElementsGrid)
            return new_row
        setattr(self.StructureElementsGrid, "_MoveRow", _MoveStructureElement)

        self.StructureElementsGrid.SetRowLabelSize(0)
        for col in range(self.StructureElementsTable.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.StructureColAlignements[col], wx.ALIGN_CENTRE)
            self.StructureElementsGrid.SetColAttr(col, attr)
            self.StructureElementsGrid.SetColMinimalWidth(col, self.StructureColSizes[col])
            self.StructureElementsGrid.AutoSizeColumn(col, False)
        self.StructureElementsGrid.RefreshButtons()

        for datatype in GetDatatypeTypes():
            self.DerivationType.Append(_(datatype))
        self.SubrangePanel.Hide()
        self.EnumeratedPanel.Hide()
        self.ArrayPanel.Hide()
        self.StructurePanel.Hide()
        self.CurrentPanel = "Directly"
        self.Highlights = []
        self.Initializing = False

        self.HighlightControls = {
            ("Directly", "base"): self.DirectlyBaseType,
            ("Directly", "initial"): self.DirectlyInitialValue,
            ("Subrange", "base"): self.SubrangeBaseType,
            ("Subrange", "lower"): self.SubrangeMinimum,
            ("Subrange", "upper"): self.SubrangeMaximum,
            ("Subrange", "initial"): self.SubrangeInitialValue,
            ("Enumerated", "value"): self.EnumeratedValues,
            ("Enumerated", "initial"): self.EnumeratedInitialValue,
            ("Array", "initial"): self.ArrayInitialValue,
            ("Array", "base"): self.ArrayBaseType,
            ("Array", "range"): self.ArrayDimensions,
        }

        self.RefreshHighlightsTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnRefreshHighlightsTimer, self.RefreshHighlightsTimer)

    def __del__(self):
        self.RefreshHighlightsTimer.Stop()

    def GetBufferState(self):
        return self.Controler.GetBufferState()

    def Undo(self):
        self.Controler.LoadPrevious()
        self.ParentWindow.CloseTabsWithoutModel()

    def Redo(self):
        self.Controler.LoadNext()
        self.ParentWindow.CloseTabsWithoutModel()

    def HasNoModel(self):
        return self.Controler.GetEditedElement(self.TagName) is None

    def RefreshView(self):
        self.Initializing = True
        self.DirectlyBaseType.Clear()
        self.ArrayBaseType.Clear()
        for datatype in self.Controler.GetDataTypes(self.TagName):
            self.DirectlyBaseType.Append(datatype)
            self.ArrayBaseType.Append(datatype)
        self.DirectlyBaseType.SetSelection(0)
        self.SubrangeBaseType.Clear()
        words = self.TagName.split("::")
        for base_type in self.Controler.GetSubrangeBaseTypes(words[1]):
            self.SubrangeBaseType.Append(base_type)
        self.SubrangeBaseType.SetSelection(0)
        self.RefreshBoundsRange()
        type_infos = self.Controler.GetDataTypeInfos(self.TagName)
        if type_infos is not None:
            datatype = type_infos["type"]
            self.DerivationType.SetStringSelection(_(datatype))
            if type_infos["type"] == "Directly":
                self.DirectlyBaseType.SetStringSelection(type_infos["base_type"])
                self.DirectlyInitialValue.SetValue(type_infos["initial"])
            elif type_infos["type"] == "Subrange":
                self.SubrangeBaseType.SetStringSelection(type_infos["base_type"])
                self.RefreshBoundsRange()
                self.SubrangeMinimum.SetValue(int(type_infos["min"]))
                self.SubrangeMaximum.SetValue(int(type_infos["max"]))
                self.RefreshSubrangeInitialValueRange()
                if type_infos["initial"] != "":
                    self.SubrangeInitialValue.SetValue(int(type_infos["initial"]))
                else:
                    self.SubrangeInitialValue.SetValue(type_infos["min"])
            elif type_infos["type"] == "Enumerated":
                self.EnumeratedValues.SetStrings(type_infos["values"])
                self.RefreshEnumeratedValues()
                self.EnumeratedInitialValue.SetStringSelection(type_infos["initial"])
            elif type_infos["type"] == "Array":
                self.ArrayBaseType.SetStringSelection(type_infos["base_type"])
                self.ArrayDimensions.SetStrings(map("..".join, type_infos["dimensions"]))
                self.ArrayInitialValue.SetValue(type_infos["initial"])
            elif type_infos["type"] == "Structure":
                self.StructureElementsTable.SetData(type_infos["elements"])
            self.RefreshDisplayedInfos()
        self.ShowHighlights()
        self.StructureElementsTable.ResetView(self.StructureElementsGrid)
        self.StructureElementsGrid.RefreshButtons()
        self.Initializing = False

    def OnDerivationTypeChanged(self, event):
        wx.CallAfter(self.RefreshDisplayedInfos)
        wx.CallAfter(self.RefreshTypeInfos)
        event.Skip()

    def OnReturnKeyPressed(self, event):
        self.RefreshTypeInfos()

    def OnInfosChanged(self, event):
        self.RefreshTypeInfos()
        event.Skip()

    def OnSubrangeBaseTypeChanged(self, event):
        self.RefreshBoundsRange()
        self.RefreshTypeInfos()
        event.Skip()

    def OnSubrangeMinimumChanged(self, event):
        if not self.Initializing:
            wx.CallAfter(self.SubrangeMinimum.SetValue, min(self.SubrangeMaximum.GetValue(), self.SubrangeMinimum.GetValue()))
            wx.CallAfter(self.RefreshSubrangeInitialValueRange)
            wx.CallAfter(self.RefreshTypeInfos)
        event.Skip()

    def OnSubrangeMaximumChanged(self, event):
        if not self.Initializing:
            wx.CallAfter(self.SubrangeMaximum.SetValue, max(self.SubrangeMinimum.GetValue(), self.SubrangeMaximum.GetValue()))
            wx.CallAfter(self.RefreshSubrangeInitialValueRange)
            wx.CallAfter(self.RefreshTypeInfos)
        event.Skip()

    def OnDimensionsChanged(self, event):
        wx.CallAfter(self.RefreshTypeInfos)
        event.Skip()

    def OnEnumeratedValueEndEdit(self, event):
        text = event.GetText()
        values = self.EnumeratedValues.GetStrings()
        index = event.GetIndex()
        if index >= len(values) or values[index].upper() != text.upper():
            if text.upper() in [value.upper() for value in values]:
                message = wx.MessageDialog(self, _("\"%s\" value already defined!") % text, _("Error"), wx.OK | wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
                event.Veto()
            elif text.upper() in IEC_KEYWORDS:
                message = wx.MessageDialog(self, _("\"%s\" is a keyword. It can't be used!") % text, _("Error"), wx.OK | wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
            else:
                initial_selected = None
                if index < len(values) and self.EnumeratedInitialValue.GetStringSelection() == values[index]:
                    initial_selected = text
                wx.CallAfter(self.RefreshEnumeratedValues, initial_selected)
                wx.CallAfter(self.RefreshTypeInfos)
                event.Skip()
        else:
            event.Skip()

    def OnEnumeratedValuesChanged(self, event):
        wx.CallAfter(self.RefreshEnumeratedValues)
        wx.CallAfter(self.RefreshTypeInfos)
        event.Skip()

    def ShowErrorMessage(self, message):
        dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def OnStructureElementsGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        colname = self.StructureElementsTable.GetColLabelValue(col, False)
        value = self.StructureElementsTable.GetValue(row, col)
        if colname == "Name":
            message = None
            if not TestIdentifier(value):
                message = _("\"%s\" is not a valid identifier!") % value
            elif value.upper() in IEC_KEYWORDS:
                message = _("\"%s\" is a keyword. It can't be used!") % value
#            elif value.upper() in self.PouNames:
#                message = _("A pou with \"%s\" as name exists!")%value
            elif value.upper() in [var["Name"].upper() for idx, var in enumerate(self.StructureElementsTable.GetData()) if idx != row]:
                message = _("An element named \"%s\" already exists in this structure!") % value
            else:
                self.RefreshTypeInfos()
                wx.CallAfter(self.StructureElementsTable.ResetView, self.StructureElementsGrid)
#                old_value = self.Table.GetOldValue()
#                if old_value != "":
#                    self.Controler.UpdateEditedElementUsedVariable(self.TagName, old_value, value)
#                self.Controler.BufferProject()
                event.Skip()

            if message is not None:
                event.Veto()
                wx.CallAfter(self.ShowErrorMessage, message)
        else:
            self.RefreshTypeInfos()
            wx.CallAfter(self.StructureElementsTable.ResetView, self.StructureElementsGrid)
            event.Skip()

    def OnStructureElementsGridSelectCell(self, event):
        wx.CallAfter(self.RefreshStructureButtons)
        event.Skip()

    def OnStructureElementsGridEditorShown(self, event):
        row, col = event.GetRow(), event.GetCol()
        if self.StructureElementsTable.GetColLabelValue(col, False) == "Type":
            type_menu = wx.Menu(title='')

            base_menu = wx.Menu(title='')
            for base_type in self.Controler.GetBaseTypes():
                new_id = wx.NewId()
                AppendMenu(base_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=base_type)
                self.Bind(wx.EVT_MENU, self.GetElementTypeFunction(base_type), id=new_id)
            type_menu.AppendMenu(wx.NewId(), _("Base Types"), base_menu)

            datatype_menu = wx.Menu(title='')
            for datatype in self.Controler.GetDataTypes(self.TagName, False):
                new_id = wx.NewId()
                AppendMenu(datatype_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=datatype)
                self.Bind(wx.EVT_MENU, self.GetElementTypeFunction(datatype), id=new_id)
            type_menu.AppendMenu(wx.NewId(), _("User Data Types"), datatype_menu)

            new_id = wx.NewId()
            AppendMenu(type_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Array"))
            self.Bind(wx.EVT_MENU, self.ElementArrayTypeFunction, id=new_id)

#            functionblock_menu = wx.Menu(title='')
#            bodytype = self.Controler.GetEditedElementBodyType(self.TagName)
#            pouname, poutype = self.Controler.GetEditedElementType(self.TagName)
#            if classtype in ["Input","Output","InOut","External","Global"] or poutype != "function" and bodytype in ["ST", "IL"]:
#                for functionblock_type in self.Controler.GetFunctionBlockTypes(self.TagName):
#                    new_id = wx.NewId()
#                    AppendMenu(functionblock_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=functionblock_type)
#                    self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(functionblock_type), id=new_id)
#                type_menu.AppendMenu(wx.NewId(), _("Function Block Types"), functionblock_menu)

            rect = self.StructureElementsGrid.BlockToDeviceRect((row, col), (row, col))
            self.StructureElementsGrid.PopupMenuXY(type_menu, rect.x + rect.width, rect.y + self.StructureElementsGrid.GetColLabelSize())
            type_menu.Destroy()
            event.Veto()
        else:
            event.Skip()

    def GetElementTypeFunction(self, base_type):
        def ElementTypeFunction(event):
            row = self.StructureElementsGrid.GetGridCursorRow()
            self.StructureElementsTable.SetValueByName(row, "Type", base_type)
            self.RefreshTypeInfos()
            self.StructureElementsTable.ResetView(self.StructureElementsGrid)
        return ElementTypeFunction

    def ElementArrayTypeFunction(self, event):
        row = self.StructureElementsGrid.GetGridCursorRow()
        dialog = ArrayTypeDialog(self,
                                 self.Controler.GetDataTypes(self.TagName),
                                 self.StructureElementsTable.GetValueByName(row, "Type"))
        if dialog.ShowModal() == wx.ID_OK:
            self.StructureElementsTable.SetValueByName(row, "Type", dialog.GetValue())
            self.RefreshTypeInfos()
            self.StructureElementsTable.ResetView(self.StructureElementsGrid)
        dialog.Destroy()

    def RefreshDisplayedInfos(self):
        selected = self.DATATYPE_TYPES_DICT[self.DerivationType.GetStringSelection()]
        if selected != self.CurrentPanel:
            if self.CurrentPanel == "Directly":
                self.DirectlyPanel.Hide()
            elif self.CurrentPanel == "Subrange":
                self.SubrangePanel.Hide()
            elif self.CurrentPanel == "Enumerated":
                self.EnumeratedPanel.Hide()
            elif self.CurrentPanel == "Array":
                self.ArrayPanel.Hide()
            elif self.CurrentPanel == "Structure":
                self.StructurePanel.Hide()
            self.CurrentPanel = selected
            if selected == "Directly":
                self.DirectlyPanel.Show()
            elif selected == "Subrange":
                self.SubrangePanel.Show()
            elif selected == "Enumerated":
                self.EnumeratedPanel.Show()
            elif selected == "Array":
                self.ArrayPanel.Show()
            elif selected == "Structure":
                self.StructurePanel.Show()
            self.MainSizer.Layout()

    def RefreshEnumeratedValues(self, initial_selected=None):
        if initial_selected is None:
            initial_selected = self.EnumeratedInitialValue.GetStringSelection()
        self.EnumeratedInitialValue.Clear()
        self.EnumeratedInitialValue.Append("")
        for value in self.EnumeratedValues.GetStrings():
            self.EnumeratedInitialValue.Append(value)
        self.EnumeratedInitialValue.SetStringSelection(initial_selected)

    def RefreshBoundsRange(self):
        range = self.Controler.GetDataTypeRange(self.SubrangeBaseType.GetStringSelection())
        if range is not None:
            min_value, max_value = range
            self.SubrangeMinimum.SetBounds(min_value, max_value)
            self.SubrangeMinimum.SetValue(min(max(min_value, self.SubrangeMinimum.GetValue()), max_value))
            self.SubrangeMaximum.SetBounds(min_value, max_value)
            self.SubrangeMaximum.SetValue(min(max(min_value, self.SubrangeMaximum.GetValue()), max_value))

    def RefreshSubrangeInitialValueRange(self):
        self.SubrangeInitialValue.SetBounds(self.SubrangeMinimum.GetValue(), self.SubrangeMaximum.GetValue())

    def RefreshTypeInfos(self):
        selected = self.DATATYPE_TYPES_DICT[self.DerivationType.GetStringSelection()]
        infos = {"type": selected}
        if selected == "Directly":
            infos["base_type"] = self.DirectlyBaseType.GetStringSelection()
            infos["initial"] = self.DirectlyInitialValue.GetValue()
        elif selected == "Subrange":
            infos["base_type"] = self.SubrangeBaseType.GetStringSelection()
            infos["min"] = str(self.SubrangeMinimum.GetValue())
            infos["max"] = str(self.SubrangeMaximum.GetValue())
            initial_value = self.SubrangeInitialValue.GetValue()
            if initial_value == infos["min"]:
                infos["initial"] = ""
            else:
                infos["initial"] = str(initial_value)
        elif selected == "Enumerated":
            infos["values"] = self.EnumeratedValues.GetStrings()
            infos["initial"] = self.EnumeratedInitialValue.GetStringSelection()
        elif selected == "Array":
            infos["base_type"] = self.ArrayBaseType.GetStringSelection()
            infos["dimensions"] = []
            for dimensions in self.ArrayDimensions.GetStrings():
                result = DIMENSION_MODEL.match(dimensions)
                if result is None:
                    message = wx.MessageDialog(self, _("\"%s\" value isn't a valid array dimension!") % dimensions, _("Error"), wx.OK | wx.ICON_ERROR)
                    message.ShowModal()
                    message.Destroy()
                    self.RefreshView()
                    return
                bounds = result.groups()
                if int(bounds[0]) >= int(bounds[1]):
                    message = wx.MessageDialog(self, _("\"%s\" value isn't a valid array dimension!\nRight value must be greater than left value.") % dimensions, _("Error"), wx.OK | wx.ICON_ERROR)
                    message.ShowModal()
                    message.Destroy()
                    self.RefreshView()
                    return
                infos["dimensions"].append(bounds)
            infos["initial"] = self.ArrayInitialValue.GetValue()
        elif selected == "Structure":
            infos["elements"] = self.StructureElementsTable.GetData()
            infos["initial"] = ""
        self.Controler.SetDataTypeInfos(self.TagName, infos)
        self.ParentWindow.RefreshTitle()
        self.ParentWindow.RefreshFileMenu()
        self.ParentWindow.RefreshEditMenu()

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def OnRefreshHighlightsTimer(self, event):
        self.RefreshView()
        event.Skip()

    def ClearHighlights(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = []
        else:
            self.Highlights = [(infos, start, end, highlight) for (infos, start, end, highlight) in self.Highlights if highlight != highlight_type]
        for control in self.HighlightControls.itervalues():
            if isinstance(control, (wx.ComboBox, wx.SpinCtrl)):
                control.SetBackgroundColour(wx.NullColour)
                control.SetForegroundColour(wx.NullColour)
            elif isinstance(control, wx.TextCtrl):
                value = control.GetValueStr() if isinstance(control, CustomIntCtrl) else \
                        control.GetValue()
                control.SetStyle(0, len(value), wx.TextAttr(wx.NullColour))
            elif isinstance(control, wx.gizmos.EditableListBox):
                listctrl = control.GetListCtrl()
                for i in xrange(listctrl.GetItemCount()):
                    listctrl.SetItemBackgroundColour(i, wx.NullColour)
                    listctrl.SetItemTextColour(i, wx.NullColour)
        self.StructureElementsTable.ClearHighlights(highlight_type)
        self.RefreshView()

    def AddHighlight(self, infos, start, end, highlight_type):
        self.Highlights.append((infos, start, end, highlight_type))
        self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def ShowHighlights(self):
        type_infos = self.Controler.GetDataTypeInfos(self.TagName)
        for infos, start, end, highlight_type in self.Highlights:
            if infos[0] == "struct":
                self.StructureElementsTable.AddHighlight(infos[1:], highlight_type)
            else:
                control = self.HighlightControls.get((type_infos["type"], infos[0]), None)
                if control is not None:
                    if isinstance(control, (wx.ComboBox, wx.SpinCtrl)):
                        control.SetBackgroundColour(highlight_type[0])
                        control.SetForegroundColour(highlight_type[1])
                    elif isinstance(control, wx.TextCtrl):
                        control.SetStyle(start[1], end[1] + 1, wx.TextAttr(highlight_type[1], highlight_type[0]))
                    elif isinstance(control, wx.gizmos.EditableListBox):
                        listctrl = control.GetListCtrl()
                        listctrl.SetItemBackgroundColour(infos[1], highlight_type[0])
                        listctrl.SetItemTextColour(infos[1], highlight_type[1])
                        listctrl.Select(listctrl.FocusedItem, False)
