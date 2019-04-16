#!/usr/bin/env python
# -*- coding: utf-8 -*-

# See COPYING file for copyrights details.

from __future__ import absolute_import
import wx
import wx.dataview as dv
import PSKManagement as PSK
from PSKManagement import *
from dialogs.IDMergeDialog import IDMergeDialog


class IDBrowserModel(dv.PyDataViewIndexListModel):
    def __init__(self, project_path, columncount):
        self.project_path = project_path
        self.columncount = columncount
        self.data = PSK.GetData(project_path)
        dv.PyDataViewIndexListModel.__init__(self, len(self.data))

    def _saveData(self):
        PSK.SaveData(self.project_path, self.data)

    def GetColumnType(self, col):
        return "string"

    def GetValueByRow(self, row, col):
        return self.data[row][col]

    def SetValueByRow(self, value, row, col):
        self.data[row][col] = value
        self._saveData()

    def GetColumnCount(self):
        return len(self.data[0]) if self.data else self.columncount

    def GetCount(self):
        return len(self.data)

    def Compare(self, item1, item2, col, ascending):
        if not ascending:  # swap sort order?
            item2, item1 = item1, item2
        row1 = self.GetRow(item1)
        row2 = self.GetRow(item2)
        if col == 0:
            return cmp(int(self.data[row1][col]), int(self.data[row2][col]))
        else:
            return cmp(self.data[row1][col], self.data[row2][col])

    def DeleteRows(self, rows):
        rows = list(rows)
        rows.sort(reverse=True)

        for row in rows:
            PSK.DeleteID(self.project_path, self.data[row][COL_ID])
            del self.data[row]
            self.RowDeleted(row)
        self._saveData()

    def AddRow(self, value):
        self.data.append(value)
        self.RowAppended()
        self._saveData()

    def Import(self, filepath, sircb):
        data = PSK.ImportIDs(self.project_path, filepath, sircb)
        if data is not None:
            self.data = data
            self.Reset(len(self.data))

    def Export(self, filepath):
        PSK.ExportIDs(self.project_path, filepath)


colflags = dv.DATAVIEW_COL_RESIZABLE | dv.DATAVIEW_COL_SORTABLE


class IDBrowser(wx.Panel):
    def __init__(self, parent, ctr, SelectURICallBack=None, SelectIDCallBack=None, **kwargs):
        big = self.isManager = SelectURICallBack is None and SelectIDCallBack is None
        wx.Panel.__init__(self, parent, -1, size=(800 if big else 450,
                                                  600 if big else 200))

        self.SelectURICallBack = SelectURICallBack
        self.SelectIDCallBack = SelectIDCallBack

        dvStyle = wx.BORDER_THEME | dv.DV_ROW_LINES
        if self.isManager:
            # no multiple selection in selector mode
            dvStyle |= dv.DV_MULTIPLE
        self.dvc = dv.DataViewCtrl(self, style=dvStyle)

        def args(*a, **k):
            return (a, k)

        ColumnsDesc = [
            args(_("ID"), COL_ID, width=70),
            args(_("Last URI"), COL_URI, width=300 if big else 80),
            args(_("Description"), COL_DESC, width=300 if big else 200,
                 mode=dv.DATAVIEW_CELL_EDITABLE
                 if self.isManager
                 else dv.DATAVIEW_CELL_INERT),
            args(_("Last connection"), COL_LAST, width=120),
        ]

        self.model = IDBrowserModel(ctr.ProjectPath, len(ColumnsDesc))
        self.dvc.AssociateModel(self.model)

        col_list = []
        for a, k in ColumnsDesc:
            col_list.append(
                self.dvc.AppendTextColumn(*a, **dict(k, flags=colflags)))
        col_list[COL_LAST].SetSortOrder(False)

        # TODO : sort by last bvisit by default

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.dvc, 1, wx.EXPAND)

        btnbox = wx.BoxSizer(wx.HORIZONTAL)
        if self.isManager:

            # deletion of secret and metadata
            deleteButton = wx.Button(self, label=_("Delete ID"))
            self.Bind(wx.EVT_BUTTON, self.OnDeleteButton, deleteButton)
            btnbox.Add(deleteButton, 0, wx.LEFT | wx.RIGHT, 5)

            # export all
            exportButton = wx.Button(self, label=_("Export all"))
            self.Bind(wx.EVT_BUTTON, self.OnExportButton, exportButton)
            btnbox.Add(exportButton, 0, wx.LEFT | wx.RIGHT, 5)

            # import with a merge -> duplicates are asked for
            importButton = wx.Button(self, label=_("Import"))
            self.Bind(wx.EVT_BUTTON, self.OnImportButton, importButton)
            btnbox.Add(importButton, 0, wx.LEFT | wx.RIGHT, 5)

        else:
            # selector mode
            self.useURIButton = wx.Button(self, label=_("Use last URI"))
            self.Bind(wx.EVT_BUTTON, self.OnUseURIButton, self.useURIButton)
            self.useURIButton.Disable()
            btnbox.Add(self.useURIButton, 0, wx.LEFT | wx.RIGHT, 5)

        self.Sizer.Add(btnbox, 0, wx.TOP | wx.BOTTOM, 5)
        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectionChanged, self.dvc)

    def OnDeleteButton(self, evt):
        items = self.dvc.GetSelections()
        rows = [self.model.GetRow(item) for item in items]

        # Ask if user really wants to delete
        if wx.MessageBox(_('Are you sure to delete selected IDs?'),
                         _('Delete IDs'),
                         wx.YES_NO | wx.CENTRE | wx.NO_DEFAULT) != wx.YES:
            return

        self.model.DeleteRows(rows)

    def OnSelectionChanged(self, evt):
        if not self.isManager:
            items = self.dvc.GetSelections()
            somethingSelected = len(items) > 0
            self.useURIButton.Enable(somethingSelected)
            if somethingSelected:
                row = self.model.GetRow(items[0])
                ID = self.model.GetValueByRow(row, COL_ID)
                self.SelectIDCallBack(ID)

    def OnUseURIButton(self, evt):
        row = self.model.GetRow(self.dvc.GetSelections()[0])
        URI = self.model.GetValueByRow(row, COL_URI)
        if URI:
            self.SelectURICallBack(URI)

    def OnExportButton(self, evt):
        dialog = wx.FileDialog(self, _("Choose a file"),
                               wildcard=_("PSK ZIP files (*.zip)|*.zip"),
                               style=wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            self.model.Export(dialog.GetPath())

    # pylint: disable=unused-variable
    def ShouldIReplaceCallback(self, existing, replacement):
        ID, URI, DESC, LAST = existing
        _ID, _URI, _DESC, _LAST = replacement
        dlg = IDMergeDialog(
            self,
            _("Import IDs"),
            (_("Replace information for ID {ID} ?") + "\n\n" +
             _("Existing:") + "\n    " +
             _("Description:") + " {DESC}\n    " +
             _("Last known URI:") + " {URI}\n    " +
             _("Last connection:") + " {LAST}\n\n" +
             _("Replacement:") + "\n    " +
             _("Description:") + " {_DESC}\n    " +
             _("Last known URI:") + " {_URI}\n    " +
             _("Last connection:") + " {_LAST}\n").format(**locals()),
            _("Do the same for following IDs"),
            [_("Replace"), _("Keep"), _("Cancel")])

        answer = dlg.ShowModal()  # return value ignored as we have "Ok" only anyhow
        if answer == wx.ID_CANCEL:
            return CANCEL

        if dlg.OptionChecked():
            if answer == wx.ID_YES:
                return REPLACE_ALL
            return KEEP_ALL
        else:
            if answer == wx.ID_YES:
                return REPLACE
            return KEEP

    def OnImportButton(self, evt):
        dialog = wx.FileDialog(self, _("Choose a file"),
                               wildcard=_("PSK ZIP files (*.zip)|*.zip"),
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.model.Import(dialog.GetPath(),
                              self.ShouldIReplaceCallback)
