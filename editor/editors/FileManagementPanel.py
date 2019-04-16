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
import os
import shutil

import wx
import wx.lib.buttons

from editors.EditorPanel import EditorPanel
from util.BitmapLibrary import GetBitmap
from controls import FolderTree


class FileManagementPanel(EditorPanel):

    def _init_Editor(self, parent):
        self.Editor = wx.Panel(parent)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        left_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSizer(left_sizer, 1, border=5, flag=wx.GROW | wx.ALL)

        managed_dir_label = wx.StaticText(self.Editor, label=_(self.TagName) + ":")
        left_sizer.AddWindow(managed_dir_label, border=5, flag=wx.GROW | wx.BOTTOM)

        FILTER = _("All files (*.*)|*.*|CSV files (*.csv)|*.csv")
        self.ManagedDir = FolderTree(self.Editor, self.Folder, FILTER)
        left_sizer.AddWindow(self.ManagedDir, 1, flag=wx.GROW)

        managed_treectrl = self.ManagedDir.GetTreeCtrl()
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeItemChanged, managed_treectrl)
        if self.EnableDragNDrop:
            self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnTreeBeginDrag, managed_treectrl)

        button_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSizer(button_sizer, border=5,
                            flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        for idx, (name, bitmap, help) in enumerate([
                ("DeleteButton", "remove_element", _("Remove file from left folder")),
                ("LeftCopyButton", "LeftCopy", _("Copy file from right folder to left")),
                ("RightCopyButton", "RightCopy", _("Copy file from left folder to right")),
                ("EditButton", "edit", _("Edit file"))]):
            button = wx.lib.buttons.GenBitmapButton(
                self.Editor,
                bitmap=GetBitmap(bitmap),
                size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            if idx > 0:
                flag = wx.TOP
            else:
                flag = 0
            self.Bind(wx.EVT_BUTTON, getattr(self, "On" + name), button)
            button_sizer.AddWindow(button, border=20, flag=flag)

        right_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSizer(right_sizer, 1, border=5, flag=wx.GROW | wx.ALL)

        if wx.Platform == '__WXMSW__':
            system_dir_label = wx.StaticText(self.Editor, label=_("My Computer:"))
        else:
            system_dir_label = wx.StaticText(self.Editor, label=_("Home Directory:"))
        right_sizer.AddWindow(system_dir_label, border=5, flag=wx.GROW | wx.BOTTOM)

        self.SystemDir = FolderTree(self.Editor, self.HomeDirectory, FILTER, False)
        right_sizer.AddWindow(self.SystemDir, 1, flag=wx.GROW)

        system_treectrl = self.SystemDir.GetTreeCtrl()
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeItemChanged, system_treectrl)

        self.Editor.SetSizer(main_sizer)

    def __init__(self, parent, controler, name, folder, enable_dragndrop=False):
        self.Folder = os.path.realpath(folder)
        self.EnableDragNDrop = enable_dragndrop

        if wx.Platform == '__WXMSW__':
            self.HomeDirectory = "/"
        else:
            self.HomeDirectory = os.path.expanduser("~")

        EditorPanel.__init__(self, parent, name, None, None)

        self.Controler = controler

        self.EditableFileExtensions = []
        self.EditButton.Hide()

        self.SetIcon(GetBitmap("FOLDER"))

    def __del__(self):
        self.Controler.OnCloseEditor(self)

    def GetTitle(self):
        return _(self.TagName)

    def SetEditableFileExtensions(self, extensions):
        self.EditableFileExtensions = extensions
        if len(self.EditableFileExtensions) > 0:
            self.EditButton.Show()

    def RefreshView(self):
        self.ManagedDir.RefreshTree()
        self.SystemDir.RefreshTree()
        self.RefreshButtonsState()

    def RefreshButtonsState(self):
        managed_filepath = self.ManagedDir.GetPath()
        system_filepath = self.SystemDir.GetPath()

        self.DeleteButton.Enable(os.path.isfile(managed_filepath))
        self.LeftCopyButton.Enable(os.path.isfile(system_filepath))
        self.RightCopyButton.Enable(os.path.isfile(managed_filepath))
        if len(self.EditableFileExtensions) > 0:
            self.EditButton.Enable(
                os.path.isfile(managed_filepath) and
                os.path.splitext(managed_filepath)[1] in self.EditableFileExtensions)

    def OnTreeItemChanged(self, event):
        self.RefreshButtonsState()
        event.Skip()

    def OnDeleteButton(self, event):
        filepath = self.ManagedDir.GetPath()
        if os.path.isfile(filepath):
            _folder, filename = os.path.split(filepath)

            dialog = wx.MessageDialog(self,
                                      _("Do you really want to delete the file '%s'?") % filename,
                                      _("Delete File"),
                                      wx.YES_NO | wx.ICON_QUESTION)
            remove = dialog.ShowModal() == wx.ID_YES
            dialog.Destroy()

            if remove:
                os.remove(filepath)
                self.ManagedDir.RefreshTree()
        event.Skip()

    def OnEditButton(self, event):
        filepath = self.ManagedDir.GetPath()
        if os.path.isfile(filepath) and \
           os.path.splitext(filepath)[1] in self.EditableFileExtensions:
            self.Controler._OpenView(filepath + "::")
        event.Skip()

    def CopyFile(self, src, dst):
        if os.path.isfile(src):
            _src_folder, src_filename = os.path.split(src)
            if os.path.isfile(dst):
                dst_folder, _dst_filename = os.path.split(dst)
            else:
                dst_folder = dst

            dst_filepath = os.path.join(dst_folder, src_filename)
            if os.path.isfile(dst_filepath):
                dialog = wx.MessageDialog(
                    self,
                    _("The file '%s' already exist.\nDo you want to replace it?") % src_filename,
                    _("Replace File"), wx.YES_NO | wx.ICON_QUESTION)
                copy = dialog.ShowModal() == wx.ID_YES
                dialog.Destroy()
            else:
                copy = True

            if copy:
                shutil.copyfile(src, dst_filepath)
                return dst_filepath
        return None

    def OnLeftCopyButton(self, event):
        filepath = self.CopyFile(self.SystemDir.GetPath(), self.ManagedDir.GetPath())
        if filepath is not None:
            self.ManagedDir.RefreshTree()
            self.ManagedDir.SetPath(filepath)
        event.Skip()

    def OnRightCopyButton(self, event):
        filepath = self.CopyFile(self.ManagedDir.GetPath(), self.SystemDir.GetPath())
        if filepath is not None:
            self.SystemDir.RefreshTree()
            self.SystemDir.SetPath(filepath)
        event.Skip()

    def OnTreeBeginDrag(self, event):
        filepath = self.ManagedDir.GetPath()
        if os.path.isfile(filepath):
            relative_filepath = filepath.replace(os.path.join(self.Folder, ""), "")
            data = wx.TextDataObject(str(("'%s'" % relative_filepath, "Constant")))
            dragSource = wx.DropSource(self)
            dragSource.SetData(data)
            dragSource.DoDragDrop()
