#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2012: Edouard TISSERANT and Laurent BESSARD
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
from collections import namedtuple

import wx
import wx.lib.agw.customtreectrl as CT
import wx.lib.buttons

from plcopen.types_enums import *

from util.BitmapLibrary import GetBitmap


# Customize CustomTreeItem for adding icon on item right
CT.GenericTreeItem._rightimages = []


def SetRightImages(self, images):
    self._rightimages = images


CT.GenericTreeItem.SetRightImages = SetRightImages


def GetRightImages(self):
    return self._rightimages


CT.GenericTreeItem.GetRightImages = GetRightImages


class CustomTreeCtrlWithRightImage(CT.CustomTreeCtrl):

    def SetRightImageList(self, imageList):
        self._imageListRight = imageList

    def GetLineHeight(self, item):
        height = CT.CustomTreeCtrl.GetLineHeight(self, item)
        rightimages = item.GetRightImages()
        if len(rightimages) > 0:
            _r_image_w, r_image_h = self._imageListRight.GetSize(rightimages[0])
            return max(height, r_image_h + 8)
        return height

    def GetItemRightImagesBBox(self, item):
        rightimages = item.GetRightImages()
        if len(rightimages) > 0:
            w, _h = self.GetClientSize()
            total_h = self.GetLineHeight(item)
            r_image_w, r_image_h = self._imageListRight.GetSize(rightimages[0])

            bbox_width = (r_image_w + 4) * len(rightimages) + 4
            bbox_height = r_image_h + 8
            bbox_x = w - bbox_width
            bbox_y = item.GetY() + ((total_h > r_image_h) and [(total_h-r_image_h)//2] or [0])[0]

            return wx.Rect(bbox_x, bbox_y, bbox_width, bbox_height)

        return None

    def IsOverItemRightImage(self, item, point):
        rightimages = item.GetRightImages()
        if len(rightimages) > 0:
            point = self.CalcUnscrolledPosition(point)
            r_image_w, r_image_h = self._imageListRight.GetSize(rightimages[0])
            images_bbx = self.GetItemRightImagesBBox(item)

            rect = wx.Rect(images_bbx.x + 4, images_bbx.y + 4,
                           r_image_w, r_image_h)
            for r_image in rightimages:
                if rect.Inside(point):
                    return r_image
                rect.x += r_image_w + 4

            return None

    def PaintItem(self, item, dc, level, align):
        CT.CustomTreeCtrl.PaintItem(self, item, dc, level, align)

        rightimages = item.GetRightImages()
        if len(rightimages) > 0:
            images_bbx = self.GetItemRightImagesBBox(item)
            r_image_w, _r_image_h = self._imageListRight.GetSize(rightimages[0])

            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetPen(wx.TRANSPARENT_PEN)

            dc.DrawRectangle(images_bbx.x, images_bbx.y,
                             images_bbx.width, images_bbx.height)
            x_pos = images_bbx.x + 4
            for r_image in rightimages:
                self._imageListRight.Draw(
                    r_image, dc, x_pos, images_bbx.y + 4,
                    wx.IMAGELIST_DRAW_TRANSPARENT)
                x_pos += r_image_w + 4


_ButtonCallbacks = namedtuple("ButtonCallbacks", ["leftdown", "dclick"])


class PouInstanceVariablesPanel(wx.Panel):

    def __init__(self, parent, window, controller, debug):
        wx.Panel.__init__(self, name='PouInstanceTreePanel',
                          parent=parent, pos=wx.Point(0, 0),
                          size=wx.Size(0, 0), style=wx.TAB_TRAVERSAL)

        self.ParentButton = wx.lib.buttons.GenBitmapButton(
            self, bitmap=GetBitmap("top"), size=wx.Size(28, 28), style=wx.NO_BORDER)
        self.ParentButton.SetToolTipString(_("Parent instance"))
        self.Bind(wx.EVT_BUTTON, self.OnParentButtonClick,
                  self.ParentButton)

        self.InstanceChoice = wx.ComboBox(self, size=wx.Size(0, 0), style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnInstanceChoiceChanged,
                  self.InstanceChoice)

        self.DebugButton = wx.lib.buttons.GenBitmapButton(
            self, bitmap=GetBitmap("debug_instance"), size=wx.Size(28, 28), style=wx.NO_BORDER)
        self.DebugButton.SetToolTipString(_("Debug instance"))
        self.Bind(wx.EVT_BUTTON, self.OnDebugButtonClick,
                  self.DebugButton)

        self.VariablesList = CustomTreeCtrlWithRightImage(
            self,
            style=wx.SUNKEN_BORDER,
            agwStyle=(CT.TR_NO_BUTTONS |
                      CT.TR_SINGLE |
                      CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                      CT.TR_HIDE_ROOT |
                      CT.TR_NO_LINES |
                      getattr(CT, "TR_ALIGN_WINDOWS_RIGHT", CT.TR_ALIGN_WINDOWS)))
        self.VariablesList.SetIndent(0)
        self.VariablesList.SetSpacing(5)
        self.VariablesList.DoSelectItem = lambda *x, **y: True
        self.VariablesList.Bind(CT.EVT_TREE_ITEM_ACTIVATED,
                                self.OnVariablesListItemActivated)
        self.VariablesList.Bind(wx.EVT_LEFT_DOWN, self.OnVariablesListLeftDown)
        self.VariablesList.Bind(wx.EVT_KEY_DOWN, self.OnVariablesListKeyDown)

        self.TreeRightImageList = wx.ImageList(24, 24)
        self.EditImage = self.TreeRightImageList.Add(GetBitmap("edit"))
        self.DebugInstanceImage = self.TreeRightImageList.Add(GetBitmap("debug_instance"))
        self.VariablesList.SetRightImageList(self.TreeRightImageList)

        self.ButtonCallBacks = {
            self.EditImage: _ButtonCallbacks(
                self.EditButtonCallback, None),
            self.DebugInstanceImage: _ButtonCallbacks(
                self.DebugButtonCallback, self.DebugButtonDClickCallback)}

        buttons_sizer = wx.FlexGridSizer(cols=3, hgap=0, rows=1, vgap=0)
        buttons_sizer.AddWindow(self.ParentButton)
        buttons_sizer.AddWindow(self.InstanceChoice, flag=wx.GROW)
        buttons_sizer.AddWindow(self.DebugButton)
        buttons_sizer.AddGrowableCol(1)
        buttons_sizer.AddGrowableRow(0)

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
        main_sizer.AddSizer(buttons_sizer, flag=wx.GROW)
        main_sizer.AddWindow(self.VariablesList, flag=wx.GROW)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)

        self.SetSizer(main_sizer)

        self.ParentWindow = window
        self.Controller = controller
        self.Debug = debug
        if not self.Debug:
            self.DebugButton.Hide()

        self.PouTagName = None
        self.PouInfos = None
        self.PouInstance = None

    def __del__(self):
        self.Controller = None

    def SetTreeImageList(self, tree_image_list):
        self.VariablesList.SetImageList(tree_image_list)

    def SetController(self, controller):
        self.Controller = controller

        self.RefreshView()

    def SetPouType(self, tagname, pou_instance=None):
        if self.Controller is not None:
            if tagname == "Project":
                config_name = self.Controller.GetProjectMainConfigurationName()
                if config_name is not None:
                    tagname = ComputeConfigurationName(config_name)
            if pou_instance is not None:
                self.PouInstance = pou_instance

            if self.PouTagName != tagname:
                self.PouTagName = tagname
                self.RefreshView()
            else:
                self.RefreshInstanceChoice()
        else:
            self.RefreshView()

    def ResetView(self):
        self.Controller = None

        self.PouTagName = None
        self.PouInfos = None
        self.PouInstance = None

        self.RefreshView()

    def RefreshView(self):
        self.Freeze()
        self.VariablesList.DeleteAllItems()

        if self.Controller is not None and self.PouTagName is not None:
            if self.PouTagName.split('::')[0] in ['A', 'T']:
                self.PouInfos = self.Controller.GetPouVariables('P::%s' % self.PouTagName.split('::')[1], self.Debug)
            else:
                self.PouInfos = self.Controller.GetPouVariables(self.PouTagName, self.Debug)
            if None in self.Controller.GetEditedElementType(self.PouTagName, self.Debug) and self.PouInfos is not None:
                self.PouInfos.debug = False
        else:
            self.PouInfos = None
        if self.PouInfos is not None:
            root = self.VariablesList.AddRoot("", data=self.PouInfos)
            for var_infos in self.PouInfos.variables:
                if var_infos.type is not None:
                    text = "%s (%s)" % (var_infos.name, var_infos.type)
                else:
                    text = var_infos.name

                right_images = []
                if var_infos.edit:
                    right_images.append(self.EditImage)

                if var_infos.debug and self.Debug:
                    right_images.append(self.DebugInstanceImage)

                item = self.VariablesList.AppendItem(root, text)
                item.SetRightImages(right_images)
                self.VariablesList.SetItemImage(item, self.ParentWindow.GetTreeImage(var_infos.var_class))
                self.VariablesList.SetPyData(item, var_infos)

        self.RefreshInstanceChoice()
        self.RefreshButtons()

        self.Thaw()

    def RefreshInstanceChoice(self):
        self.InstanceChoice.Clear()
        self.InstanceChoice.SetValue("")
        if self.Controller is not None and self.PouInfos is not None:
            instances = self.Controller.SearchPouInstances(self.PouTagName, self.Debug)
            for instance in instances:
                self.InstanceChoice.Append(instance)
            if len(instances) == 1:
                self.PouInstance = instances[0]
            if self.PouInfos.var_class in [ITEM_CONFIGURATION, ITEM_RESOURCE]:
                self.PouInstance = None
                self.InstanceChoice.SetSelection(0)
            elif self.PouInstance in instances:
                self.InstanceChoice.SetStringSelection(self.PouInstance)
            else:
                self.PouInstance = None
                self.InstanceChoice.SetValue(_("Select an instance"))

    def RefreshButtons(self):
        enabled = self.InstanceChoice.GetSelection() != -1
        self.ParentButton.Enable(enabled and self.PouInfos.var_class != ITEM_CONFIGURATION)
        self.DebugButton.Enable(enabled and self.PouInfos.debug and self.Debug)

        root = self.VariablesList.GetRootItem()
        if root is not None and root.IsOk():
            item, item_cookie = self.VariablesList.GetFirstChild(root)
            while item is not None and item.IsOk():
                panel = self.VariablesList.GetItemWindow(item)
                if panel is not None:
                    for child in panel.GetChildren():
                        if child.GetName() != "edit":
                            child.Enable(enabled)
                item, item_cookie = self.VariablesList.GetNextChild(root, item_cookie)

    def EditButtonCallback(self, infos):
        var_class = infos.var_class
        if var_class == ITEM_RESOURCE:
            tagname = ComputeConfigurationResourceName(
                self.InstanceChoice.GetStringSelection(),
                infos.name)
        elif var_class == ITEM_TRANSITION:
            tagname = ComputePouTransitionName(
                self.PouTagName.split("::")[1],
                infos.name)
        elif var_class == ITEM_ACTION:
            tagname = ComputePouActionName(
                self.PouTagName.split("::")[1],
                infos.name)
        else:
            var_class = ITEM_POU
            tagname = ComputePouName(infos.type)
        self.ParentWindow.EditProjectElement(var_class, tagname)

    def DebugButtonCallback(self, infos):
        if self.InstanceChoice.GetSelection() != -1:
            var_class = infos.var_class
            instance_path = self.InstanceChoice.GetStringSelection()
            if self.PouTagName.split("::")[0] in ["A", "T"]:
                pos = instance_path.rfind('.')
                instance_path = instance_path[0:pos]
            var_path = "%s.%s" % (instance_path, infos.name)
            if var_class in ITEMS_VARIABLE:
                self.ParentWindow.AddDebugVariable(var_path.upper(), force=True)
            elif var_class == ITEM_TRANSITION:
                self.ParentWindow.OpenDebugViewer(
                    var_class,
                    var_path,
                    ComputePouTransitionName(
                        self.PouTagName.split("::")[1],
                        infos.name))
            elif var_class == ITEM_ACTION:
                self.ParentWindow.OpenDebugViewer(
                    var_class,
                    var_path,
                    ComputePouActionName(
                        self.PouTagName.split("::")[1],
                        infos.name))
            else:
                self.ParentWindow.OpenDebugViewer(
                    var_class,
                    var_path,
                    ComputePouName(infos.type))

    def DebugButtonDClickCallback(self, infos):
        if self.InstanceChoice.GetSelection() != -1:
            if infos.var_class in ITEMS_VARIABLE:
                self.ParentWindow.AddDebugVariable(
                    "%s.%s" % (self.InstanceChoice.GetStringSelection().upper(),
                               infos.name.upper()),
                    force=True,
                    graph=True)

    def ShowInstanceChoicePopup(self):
        self.InstanceChoice.SetFocusFromKbd()
        size = self.InstanceChoice.GetSize()
        event = wx.MouseEvent(wx.EVT_LEFT_DOWN._getEvtType())
        event.x = size.width // 2
        event.y = size.height // 2
        event.SetEventObject(self.InstanceChoice)
        # event = wx.KeyEvent(wx.EVT_KEY_DOWN._getEvtType())
        # event.m_keyCode = wx.WXK_SPACE
        self.InstanceChoice.GetEventHandler().ProcessEvent(event)

    def OnParentButtonClick(self, event):
        if self.InstanceChoice.GetSelection() != -1:
            parent_path = self.InstanceChoice.GetStringSelection().rsplit(".", 1)[0]
            tagname = self.Controller.GetPouInstanceTagName(parent_path, self.Debug)
            if tagname is not None:
                wx.CallAfter(self.SetPouType, tagname, parent_path)
                wx.CallAfter(self.ParentWindow.SelectProjectTreeItem, tagname)
        event.Skip()

    def OnInstanceChoiceChanged(self, event):
        self.RefreshButtons()
        event.Skip()

    def OnDebugButtonClick(self, event):
        if self.InstanceChoice.GetSelection() != -1:
            self.ParentWindow.OpenDebugViewer(
                self.PouInfos.var_class,
                self.InstanceChoice.GetStringSelection(),
                self.PouTagName)
        event.Skip()

    def OnVariablesListItemActivated(self, event):
        selected_item = event.GetItem()
        if selected_item is not None and selected_item.IsOk():
            item_infos = self.VariablesList.GetPyData(selected_item)
            if item_infos is not None:

                item_button = self.VariablesList.IsOverItemRightImage(
                    selected_item, event.GetPoint())
                if item_button is not None:
                    callback = self.ButtonCallBacks[item_button].dclick
                    if callback is not None:
                        callback(item_infos)

                elif item_infos.var_class not in ITEMS_VARIABLE:
                    instance_path = self.InstanceChoice.GetStringSelection()
                    if item_infos.var_class == ITEM_RESOURCE:
                        if instance_path != "":
                            tagname = ComputeConfigurationResourceName(
                                instance_path,
                                item_infos.name)
                        else:
                            tagname = None
                    else:
                        parent_infos = self.VariablesList.GetPyData(selected_item.GetParent())
                        if item_infos.var_class == ITEM_ACTION:
                            tagname = ComputePouActionName(parent_infos.type, item_infos.name)
                        elif item_infos.var_class == ITEM_TRANSITION:
                            tagname = ComputePouTransitionName(parent_infos.type, item_infos.name)
                        else:
                            tagname = ComputePouName(item_infos.type)
                    if tagname is not None:
                        if instance_path != "":
                            item_path = "%s.%s" % (instance_path, item_infos.name)
                        else:
                            item_path = None
                        self.SetPouType(tagname, item_path)
                        self.ParentWindow.SelectProjectTreeItem(tagname)
        event.Skip()

    def OnVariablesListLeftDown(self, event):
        if self.InstanceChoice.GetSelection() == -1:
            wx.CallAfter(self.ShowInstanceChoicePopup)
        else:
            instance_path = self.InstanceChoice.GetStringSelection()
            item, flags = self.VariablesList.HitTest(event.GetPosition())
            if item is not None:
                item_infos = self.VariablesList.GetPyData(item)
                if item_infos is not None:

                    item_button = self.VariablesList.IsOverItemRightImage(
                        item, event.GetPosition())
                    if item_button is not None:
                        callback = self.ButtonCallBacks[item_button].leftdown
                        if callback is not None:
                            callback(item_infos)

                    elif (flags & CT.TREE_HITTEST_ONITEMLABEL and
                          item_infos.var_class in ITEMS_VARIABLE):
                        self.ParentWindow.EnsureTabVisible(
                            self.ParentWindow.DebugVariablePanel)
                        item_path = "%s.%s" % (instance_path, item_infos.name)
                        data = wx.TextDataObject(str((item_path, "debug")))
                        dragSource = wx.DropSource(self.VariablesList)
                        dragSource.SetData(data)
                        dragSource.DoDragDrop()
        event.Skip()

    def OnVariablesListKeyDown(self, event):
        keycode = event.GetKeyCode()
        if keycode != wx.WXK_LEFT:
            event.Skip()
