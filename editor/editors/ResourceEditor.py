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
import wx.lib.buttons
import wx.grid
from six.moves import xrange

from graphics.GraphicCommons import REFRESH_HIGHLIGHT_PERIOD, ERROR_HIGHLIGHT
from controls import CustomGrid, CustomTable, DurationCellEditor
from dialogs.DurationEditorDialog import IEC_TIME_MODEL
from editors.EditorPanel import EditorPanel
from util.BitmapLibrary import GetBitmap
from util.TranslationCatalogs import NoTranslate
from plcopen.structures import TestIdentifier, IEC_KEYWORDS


# -------------------------------------------------------------------------------
#                          Configuration Editor class
# -------------------------------------------------------------------------------


[
    ID_CONFIGURATIONEDITOR,
] = [wx.NewId() for _init_ctrls in range(1)]


class ConfigurationEditor(EditorPanel):

    ID = ID_CONFIGURATIONEDITOR
    VARIABLE_PANEL_TYPE = "config"

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


# -------------------------------------------------------------------------------
#                            Resource Editor class
# -------------------------------------------------------------------------------

def GetTasksTableColnames():
    _ = NoTranslate
    return [_("Name"), _("Triggering"), _("Single"), _("Interval"), _("Priority")]


def GetTaskTriggeringOptions():
    _ = NoTranslate
    return [_("Interrupt"), _("Cyclic")]


def SingleCellEditor(*x):
    return wx.grid.GridCellChoiceEditor()


def CheckSingle(single, varlist):
    return single in varlist


def GetInstancesTableColnames():
    _ = NoTranslate
    return [_("Name"), _("Type"), _("Task")]


class ResourceTable(CustomTable):
    """
    A custom wx.grid.Grid Table using user supplied data
    """
    def __init__(self, parent, data, colnames):
        # The base class must be initialized *first*
        CustomTable.__init__(self, parent, data, colnames)
        self.ColAlignements = []
        self.ColSizes = []
        self.TASKTRIGGERINGOPTIONS_DICT = dict([(_(option), option)
                                                for option in GetTaskTriggeringOptions()])

    def GetColAlignements(self):
        return self.ColAlignements

    def SetColAlignements(self, list):
        self.ColAlignements = list

    def GetColSizes(self):
        return self.ColSizes

    def SetColSizes(self, list):
        self.ColSizes = list

    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            colname = self.GetColLabelValue(col, False)
            value = self.data[row].get(colname, "")
            if colname == "Triggering":
                return _(value)
            return value

    def SetValue(self, row, col, value):
        if col < len(self.colnames):
            colname = self.GetColLabelValue(col, False)
            if colname == "Triggering":
                value = self.TASKTRIGGERINGOPTIONS_DICT[value]
            self.data[row][colname] = value

    def _updateColAttrs(self, grid):
        """
        wx.grid.Grid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """

        for col in range(self.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.ColAlignements[col], wx.ALIGN_CENTRE)
            grid.SetColAttr(col, attr)
            grid.SetColSize(col, self.ColSizes[col])

        for row in range(self.GetNumberRows()):
            row_highlights = self.Highlights.get(row, {})
            for col in range(self.GetNumberCols()):
                editor = None
                renderer = None
                error = False
                colname = self.GetColLabelValue(col, False)
                grid.SetReadOnly(row, col, False)
                if colname == "Name":
                    editor = wx.grid.GridCellTextEditor()
                    renderer = wx.grid.GridCellStringRenderer()
                elif colname == "Interval":
                    editor = DurationCellEditor(self, colname)
                    renderer = wx.grid.GridCellStringRenderer()
                    if self.GetValueByName(row, "Triggering") != "Cyclic":
                        grid.SetReadOnly(row, col, True)
                    interval = self.GetValueByName(row, colname)
                    if interval != "" and IEC_TIME_MODEL.match(interval.upper()) is None:
                        error = True
                elif colname == "Single":
                    editor = SingleCellEditor(self, colname)
                    editor.SetParameters(self.Parent.VariableList)
                    if self.GetValueByName(row, "Triggering") != "Interrupt":
                        grid.SetReadOnly(row, col, True)
                    single = self.GetValueByName(row, colname)
                    if single != "" and not CheckSingle(single, self.Parent.VariableList):
                        error = True
                elif colname == "Triggering":
                    editor = wx.grid.GridCellChoiceEditor()
                    editor.SetParameters(",".join(map(_, GetTaskTriggeringOptions())))
                elif colname == "Type":
                    editor = wx.grid.GridCellChoiceEditor()
                    editor.SetParameters(self.Parent.TypeList)
                elif colname == "Priority":
                    editor = wx.grid.GridCellNumberEditor()
                    editor.SetParameters("0,65535")
                elif colname == "Task":
                    editor = wx.grid.GridCellChoiceEditor()
                    editor.SetParameters(self.Parent.TaskList)

                grid.SetCellEditor(row, col, editor)
                grid.SetCellRenderer(row, col, renderer)

                if error:
                    highlight_colours = ERROR_HIGHLIGHT
                else:
                    highlight_colours = row_highlights.get(colname.lower(), [(wx.WHITE, wx.BLACK)])[-1]
                grid.SetCellBackgroundColour(row, col, highlight_colours[0])
                grid.SetCellTextColour(row, col, highlight_colours[1])
            self.ResizeRow(grid, row)

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def AddHighlight(self, infos, highlight_type):
        row_highlights = self.Highlights.setdefault(infos[0], {})
        col_highlights = row_highlights.setdefault(infos[1], [])
        col_highlights.append(highlight_type)

    def ClearHighlights(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = {}
        else:
            for _row, row_highlights in self.Highlights.iteritems():
                row_items = row_highlights.items()
                for col, col_highlights in row_items:
                    if highlight_type in col_highlights:
                        col_highlights.remove(highlight_type)
                    if len(col_highlights) == 0:
                        row_highlights.pop(col)


class ResourceEditor(EditorPanel):

    VARIABLE_PANEL_TYPE = "resource"

    def _init_Editor(self, parent):
        self.Editor = wx.Panel(parent, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL)

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=5)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)
        main_sizer.AddGrowableRow(1)

        tasks_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=5)
        tasks_sizer.AddGrowableCol(0)
        tasks_sizer.AddGrowableRow(1)
        main_sizer.AddSizer(tasks_sizer, border=5,
                            flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        tasks_buttons_sizer = wx.FlexGridSizer(cols=5, hgap=5, rows=1, vgap=0)
        tasks_buttons_sizer.AddGrowableCol(0)
        tasks_buttons_sizer.AddGrowableRow(0)
        tasks_sizer.AddSizer(tasks_buttons_sizer, flag=wx.GROW)

        tasks_label = wx.StaticText(self.Editor, label=_(u'Tasks:'))
        tasks_buttons_sizer.AddWindow(tasks_label, flag=wx.ALIGN_BOTTOM)

        for name, bitmap, help in [
                ("AddTaskButton", "add_element", _("Add task")),
                ("DeleteTaskButton", "remove_element", _("Remove task")),
                ("UpTaskButton", "up", _("Move task up")),
                ("DownTaskButton", "down", _("Move task down"))]:
            button = wx.lib.buttons.GenBitmapButton(self.Editor,
                                                    bitmap=GetBitmap(bitmap),
                                                    size=wx.Size(28, 28),
                                                    style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            tasks_buttons_sizer.AddWindow(button)

        self.TasksGrid = CustomGrid(self.Editor, style=wx.VSCROLL)
        self.TasksGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnTasksGridCellChange)
        tasks_sizer.AddWindow(self.TasksGrid, flag=wx.GROW)

        instances_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=5)
        instances_sizer.AddGrowableCol(0)
        instances_sizer.AddGrowableRow(1)
        main_sizer.AddSizer(instances_sizer, border=5,
                            flag=wx.GROW | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        instances_buttons_sizer = wx.FlexGridSizer(cols=5, hgap=5, rows=1, vgap=0)
        instances_buttons_sizer.AddGrowableCol(0)
        instances_buttons_sizer.AddGrowableRow(0)
        instances_sizer.AddSizer(instances_buttons_sizer, flag=wx.GROW)

        instances_label = wx.StaticText(self.Editor, label=_(u'Instances:'))
        instances_buttons_sizer.AddWindow(instances_label, flag=wx.ALIGN_BOTTOM)

        for name, bitmap, help in [
                ("AddInstanceButton", "add_element", _("Add instance")),
                ("DeleteInstanceButton", "remove_element", _("Remove instance")),
                ("UpInstanceButton", "up", _("Move instance up")),
                ("DownInstanceButton", "down", _("Move instance down"))]:
            button = wx.lib.buttons.GenBitmapButton(
                self.Editor, bitmap=GetBitmap(bitmap),
                size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            instances_buttons_sizer.AddWindow(button)

        self.InstancesGrid = CustomGrid(self.Editor, style=wx.VSCROLL)
        self.InstancesGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnInstancesGridCellChange)
        instances_sizer.AddWindow(self.InstancesGrid, flag=wx.GROW)

        self.Editor.SetSizer(main_sizer)

    def __init__(self, parent, tagname, window, controler):
        EditorPanel.__init__(self, parent, tagname, window, controler)

        self.RefreshHighlightsTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnRefreshHighlightsTimer, self.RefreshHighlightsTimer)

        self.TasksDefaultValue = {"Name": "task0", "Triggering": "Cyclic",
                                  "Single": "", "Interval": "T#20ms", "Priority": 0}
        self.TasksTable = ResourceTable(self, [], GetTasksTableColnames())
        self.TasksTable.SetColAlignements([wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_RIGHT, wx.ALIGN_RIGHT])
        self.TasksTable.SetColSizes([200, 100, 100, 150, 100])
        self.TasksGrid.SetTable(self.TasksTable)
        self.TasksGrid.SetButtons({"Add": self.AddTaskButton,
                                   "Delete": self.DeleteTaskButton,
                                   "Up": self.UpTaskButton,
                                   "Down": self.DownTaskButton})

        def _AddTask(new_row):
            if new_row > 0:
                row_content = self.TasksTable.data[new_row-1].copy()
                old_name = row_content['Name']
                row_content['Name'] =\
                    self.Controler.GenerateNewName(self.TagName, old_name, old_name+'%d')
            else:
                row_content = self.TasksDefaultValue.copy()

            self.TasksTable.InsertRow(new_row, row_content)
            self.RefreshModel()
            self.RefreshView()
            return new_row
        setattr(self.TasksGrid, "_AddRow", _AddTask)

        def _DeleteTask(row):
            self.TasksTable.RemoveRow(row)
            self.RefreshModel()
            self.RefreshView()
        setattr(self.TasksGrid, "_DeleteRow", _DeleteTask)

        def _MoveTask(row, move):
            new_row = self.TasksTable.MoveRow(row, move)
            if new_row != row:
                self.RefreshModel()
                self.RefreshView()
            return new_row
        setattr(self.TasksGrid, "_MoveRow", _MoveTask)

        self.TasksGrid.SetRowLabelSize(0)
        self.TasksTable.ResetView(self.TasksGrid)
        self.TasksGrid.RefreshButtons()

        self.InstancesDefaultValue = {"Name": "instance0", "Type": "", "Task": ""}
        self.InstancesTable = ResourceTable(self, [], GetInstancesTableColnames())
        self.InstancesTable.SetColAlignements([wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_LEFT])
        self.InstancesTable.SetColSizes([200, 150, 150])
        self.InstancesGrid.SetTable(self.InstancesTable)
        self.InstancesGrid.SetButtons({"Add": self.AddInstanceButton,
                                       "Delete": self.DeleteInstanceButton,
                                       "Up": self.UpInstanceButton,
                                       "Down": self.DownInstanceButton})

        def _AddInstance(new_row):
            if new_row > 0:
                row_content = self.InstancesTable.data[new_row - 1].copy()
                old_name = row_content['Name']
                row_content['Name'] =\
                    self.Controler.GenerateNewName(self.TagName, old_name, old_name+'%d')
            else:
                row_content = self.InstancesDefaultValue.copy()

            self.InstancesTable.InsertRow(new_row, row_content)
            self.RefreshModel()
            self.RefreshView()
            return new_row
        setattr(self.InstancesGrid, "_AddRow", _AddInstance)

        def _DeleteInstance(row):
            self.InstancesTable.RemoveRow(row)
            self.RefreshModel()
            self.RefreshView()
        setattr(self.InstancesGrid, "_DeleteRow", _DeleteInstance)

        def _MoveInstance(row, move):
            new_row = max(0, min(row + move, self.InstancesTable.GetNumberRows() - 1))
            if new_row != row:
                if self.InstancesTable.GetValueByName(row, "Task") != self.InstancesTable.GetValueByName(new_row, "Task"):
                    return row
                self.InstancesTable.MoveRow(row, move)
                self.RefreshModel()
                self.RefreshView()
            return new_row
        setattr(self.InstancesGrid, "_MoveRow", _MoveInstance)

        def _RefreshInstanceButtons():
            if self:
                rows = self.InstancesTable.GetNumberRows()
                row = self.InstancesGrid.GetGridCursorRow()
                self.DeleteInstanceButton.Enable(rows > 0)
                self.UpInstanceButton.Enable(
                    row > 0 and
                    self.InstancesTable.GetValueByName(row, "Task") == self.InstancesTable.GetValueByName(row - 1, "Task"))
                self.DownInstanceButton.Enable(
                    0 <= row < rows - 1 and
                    self.InstancesTable.GetValueByName(row, "Task") == self.InstancesTable.GetValueByName(row + 1, "Task"))
        setattr(self.InstancesGrid, "RefreshButtons", _RefreshInstanceButtons)

        self.InstancesGrid.SetRowLabelSize(0)
        self.InstancesTable.ResetView(self.InstancesGrid)
        self.InstancesGrid.RefreshButtons()

        self.TasksGrid.SetFocus()

    def __del__(self):
        self.RefreshHighlightsTimer.Stop()

    def RefreshTypeList(self):
        self.TypeList = ""
        blocktypes = self.Controler.GetBlockResource()
        for blocktype in blocktypes:
            self.TypeList += ",%s" % blocktype

    def RefreshTaskList(self):
        self.TaskList = ""
        for row in xrange(self.TasksTable.GetNumberRows()):
            self.TaskList += ",%s" % self.TasksTable.GetValueByName(row, "Name")

    def RefreshVariableList(self):
        self.VariableList = ""
        for variable in self.Controler.GetEditedResourceVariables(self.TagName):
            self.VariableList += ",%s" % variable

    def RefreshModel(self):
        self.Controler.SetEditedResourceInfos(self.TagName, self.TasksTable.GetData(), self.InstancesTable.GetData())
        self.RefreshBuffer()

    # Buffer the last model state
    def RefreshBuffer(self):
        self.Controler.BufferProject()
        self.ParentWindow.RefreshTitle()
        self.ParentWindow.RefreshFileMenu()
        self.ParentWindow.RefreshEditMenu()

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

    def RefreshView(self, variablepanel=True):
        EditorPanel.RefreshView(self, variablepanel)

        tasks, instances = self.Controler.GetEditedResourceInfos(self.TagName)
        self.TasksTable.SetData(tasks)
        self.InstancesTable.SetData(instances)
        self.RefreshTypeList()
        self.RefreshTaskList()
        self.RefreshVariableList()
        self.TasksTable.ResetView(self.TasksGrid)
        self.InstancesTable.ResetView(self.InstancesGrid)
        self.TasksGrid.RefreshButtons()
        self.InstancesGrid.RefreshButtons()

    def ShowErrorMessage(self, message):
        dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def OnTasksGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        if self.TasksTable.GetColLabelValue(col, False) == "Name":
            value = self.TasksTable.GetValue(row, col)
            message = None

            if not TestIdentifier(value):
                message = _("\"%s\" is not a valid identifier!") % value
            elif value.upper() in IEC_KEYWORDS:
                message = _("\"%s\" is a keyword. It can't be used!") % value
            elif value.upper() in [var["Name"].upper() for i, var in enumerate(self.TasksTable.data) if i != row]:
                message = _("A task with the same name already exists!")
            if message is not None:
                event.Veto()
                wx.CallAfter(self.ShowErrorMessage, message)
                return

            tasklist = [name for name in self.TaskList.split(",") if name != ""]
            for i in xrange(self.TasksTable.GetNumberRows()):
                task = self.TasksTable.GetValueByName(i, "Name")
                if task in tasklist:
                    tasklist.remove(task)
            if len(tasklist) > 0:
                old_name = tasklist[0].upper()
                new_name = self.TasksTable.GetValue(row, col)
                for i in xrange(self.InstancesTable.GetNumberRows()):
                    name = self.InstancesTable.GetValueByName(i, "Task").upper()
                    if old_name == name:
                        self.InstancesTable.SetValueByName(i, "Task", new_name)
        if self.TasksTable.GetColLabelValue(col, False) == "Triggering":
            self.TasksTable.SetValueByName(row, "Interval", "T#20ms")
        self.RefreshModel()
        colname = self.TasksTable.GetColLabelValue(col, False)
        if colname in ["Triggering", "Name", "Single", "Interval"]:
            wx.CallAfter(self.RefreshView, False)
        event.Skip()

    def OnInstancesGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        if self.InstancesTable.GetColLabelValue(col, False) == "Name":
            value = self.InstancesTable.GetValue(row, col)
            message = None

            if not TestIdentifier(value):
                message = _("\"%s\" is not a valid identifier!") % value
            elif value.upper() in IEC_KEYWORDS:
                message = _("\"%s\" is a keyword. It can't be used!") % value
            elif value.upper() in [var["Name"].upper() for i, var in enumerate(self.InstancesTable.data) if i != row]:
                message = _("An instance with the same name already exists!")
            if message is not None:
                event.Veto()
                wx.CallAfter(self.ShowErrorMessage, message)
                return

        self.RefreshModel()
        self.ParentWindow.RefreshPouInstanceVariablesPanel()
        self.InstancesGrid.RefreshButtons()
        event.Skip()

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def OnRefreshHighlightsTimer(self, event):
        self.RefreshView()
        event.Skip()

    def AddHighlight(self, infos, start, end, highlight_type):
        EditorPanel.AddHighlight(self, infos, start, end, highlight_type)

        if infos[0] == "task":
            self.TasksTable.AddHighlight(infos[1:], highlight_type)
        elif infos[0] == "instance":
            self.InstancesTable.AddHighlight(infos[1:], highlight_type)
        self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def ClearHighlights(self, highlight_type=None):
        EditorPanel.ClearHighlights(self, highlight_type)

        self.TasksTable.ClearHighlights(highlight_type)
        self.InstancesTable.ClearHighlights(highlight_type)
        self.TasksTable.ResetView(self.TasksGrid)
        self.InstancesTable.ResetView(self.InstancesGrid)
