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
import wx.grid

if wx.Platform == '__WXMSW__':
    ROW_HEIGHT = 20
else:
    ROW_HEIGHT = 28


class CustomTable(wx.grid.PyGridTableBase):

    """
    A custom wx.grid.Grid Table using user supplied data
    """
    def __init__(self, parent, data, colnames):
        # The base class must be initialized *first*
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.colnames = colnames
        self.Highlights = {}
        self.Parent = parent
        # XXX
        # we need to store the row length and collength to
        # see if the table has changed size
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

    def GetNumberCols(self):
        return len(self.colnames)

    def GetNumberRows(self):
        return len(self.data)

    def GetColLabelValue(self, col, translate=True):
        if col < len(self.colnames):
            if translate:
                return _(self.colnames[col])
            return self.colnames[col]

    def GetRowLabelValue(self, row, translate=True):
        return row

    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            return self.data[row].get(self.GetColLabelValue(col, False), "")

    def SetValue(self, row, col, value):
        if col < len(self.colnames):
            self.data[row][self.GetColLabelValue(col, False)] = value

    def GetValueByName(self, row, colname):
        if row < self.GetNumberRows():
            return self.data[row].get(colname)

    def SetValueByName(self, row, colname, value):
        if row < self.GetNumberRows():
            self.data[row][colname] = value

    def ResetView(self, grid):
        """
        (wx.grid.Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        grid.CloseEditControl()
        grid.BeginBatch()
        for current, new, delmsg, addmsg in [
                (
                    self._rows,
                    self.GetNumberRows(),
                    wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                    wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED
                ),
                (
                    self._cols,
                    self.GetNumberCols(),
                    wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
                    wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED
                ),
        ]:
            if new < current:
                msg = wx.grid.GridTableMessage(self, delmsg, new, current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(self, addmsg, new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)
        grid.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        # update the column rendering scheme
        self._updateColAttrs(grid)

        # update the scrollbars and the displayed part of the grid
        grid.AdjustScrollbars()
        grid.ForceRefresh()

    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

    def _updateColAttrs(self, grid):
        """
        wx.grid.Grid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """
        for row in range(self.GetNumberRows()):
            row_highlights = self.Highlights.get(row, {})
            for col in range(self.GetNumberCols()):
                colname = self.GetColLabelValue(col, False)

                grid.SetReadOnly(row, col, True)
                grid.SetCellEditor(row, col, None)
                grid.SetCellRenderer(row, col, None)

                highlight_colours = row_highlights.get(colname.lower(), [(wx.WHITE, wx.BLACK)])[-1]
                grid.SetCellBackgroundColour(row, col, highlight_colours[0])
                grid.SetCellTextColour(row, col, highlight_colours[1])
            self.ResizeRow(grid, row)

    def ResizeRow(self, grid, row):
        if grid.GetRowSize(row) < ROW_HEIGHT:
            grid.SetRowMinimalHeight(row, ROW_HEIGHT)
            grid.AutoSizeRow(row, False)

    def SetData(self, data):
        self.data = data

    def GetData(self):
        return self.data

    def GetCurrentIndex(self):
        return self.CurrentIndex

    def SetCurrentIndex(self, index):
        self.CurrentIndex = index

    def AppendRow(self, row_content):
        self.data.append(row_content)

    def InsertRow(self, index, row_content):
        self.data.insert(index, row_content)

    def MoveRow(self, row_index, move):
        new_index = max(0, min(row_index + move, len(self.data) - 1))
        if new_index != row_index:
            self.data.insert(new_index, self.data.pop(row_index))
        return new_index

    def RemoveRow(self, row_index):
        self.data.pop(row_index)

    def GetRow(self, row_index):
        return self.data[row_index]

    def Empty(self):
        self.data = []

    def AddHighlight(self, infos, highlight_type):
        row_highlights = self.Highlights.setdefault(infos[0], {})
        col_highlights = row_highlights.setdefault(infos[1], [])
        col_highlights.append(highlight_type)

    def RemoveHighlight(self, infos, highlight_type):
        row_highlights = self.Highlights.get(infos[0])
        if row_highlights is not None:
            col_highlights = row_highlights.get(infos[1])
            if col_highlights is not None and highlight_type in col_highlights:
                col_highlights.remove(highlight_type)
            if len(col_highlights) == 0:
                row_highlights.pop(infos[1])

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
