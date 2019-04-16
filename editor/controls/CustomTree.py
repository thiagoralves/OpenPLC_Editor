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
import wx
import wx.lib.agw.customtreectrl as CT

from util.BitmapLibrary import GetBitmap

# Customize CustomTreeItem for adding icon on item left
CT.GenericTreeItem._ExtraImage = None


def SetExtraImage(self, image):
    self._type = (1 if image is not None else 0)
    self._ExtraImage = image


CT.GenericTreeItem.SetExtraImage = SetExtraImage

_DefaultGetCurrentCheckedImage = CT.GenericTreeItem.GetCurrentCheckedImage


def GetCurrentCheckedImage(self):
    if self._ExtraImage is not None:
        return self._ExtraImage
    return _DefaultGetCurrentCheckedImage(self)


CT.GenericTreeItem.GetCurrentCheckedImage = GetCurrentCheckedImage


class CustomTree(CT.CustomTreeCtrl):

    def __init__(self, *args, **kwargs):
        CT.CustomTreeCtrl.__init__(self, *args, **kwargs)

        self.BackgroundBitmap = None
        self.BackgroundAlign = wx.ALIGN_LEFT | wx.ALIGN_TOP

        self.AddMenu = None
        self.Enabled = False

        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    def SetBackgroundBitmap(self, bitmap, align):
        self.BackgroundBitmap = bitmap
        self.BackgroundAlign = align

    def SetImageListCheck(self, sizex, sizey, imglist=None):
        CT.CustomTreeCtrl.SetImageListCheck(self, sizex, sizey, imglist=None)

        self.ExtraImages = {}
        for image in ["function", "functionBlock", "program"]:
            self.ExtraImages[image] = self._imageListCheck.Add(GetBitmap(image.upper()))

    def SetItemExtraImage(self, item, bitmap):
        dc = wx.ClientDC(self)
        image = self.ExtraImages.get(bitmap)
        if image is not None:
            item.SetExtraImage(image)
        else:
            item.SetExtraImage(None)
        self.CalculateSize(item, dc)
        self.RefreshLine(item)

    def SetAddMenu(self, add_menu):
        self.AddMenu = add_menu

    def Enable(self, enabled):
        self.Enabled = enabled

    def GetBitmapRect(self):
        client_size = self.GetClientSize()
        bitmap_size = self.BackgroundBitmap.GetSize()

        if self.BackgroundAlign & wx.ALIGN_RIGHT:
            x = client_size[0] - bitmap_size[0]
        elif self.BackgroundAlign & wx.ALIGN_CENTER_HORIZONTAL:
            x = (client_size[0] - bitmap_size[0]) // 2
        else:
            x = 0

        if self.BackgroundAlign & wx.ALIGN_BOTTOM:
            y = client_size[1] - bitmap_size[1]
        elif self.BackgroundAlign & wx.ALIGN_CENTER_VERTICAL:
            y = (client_size[1] - bitmap_size[1]) // 2
        else:
            y = 0

        return wx.Rect(x, y, bitmap_size[0], bitmap_size[1])

    def OnLeftUp(self, event):
        if self.Enabled:
            pos = event.GetPosition()
            _item, flags = self.HitTest(pos)

            bitmap_rect = self.GetBitmapRect()
            if ((bitmap_rect.InsideXY(pos.x, pos.y) or
                 flags & wx.TREE_HITTEST_NOWHERE) and self.AddMenu is not None):
                wx.CallAfter(self.PopupMenuXY, self.AddMenu, pos.x, pos.y)
        event.Skip()

    def OnEraseBackground(self, event):
        dc = event.GetDC()

        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)

        dc.Clear()

        bitmap_rect = self.GetBitmapRect()
        dc.DrawBitmap(self.BackgroundBitmap, bitmap_rect.x, bitmap_rect.y)

    def OnScroll(self, event):
        wx.CallAfter(self.Refresh)
        event.Skip()

    def OnSize(self, event):
        CT.CustomTreeCtrl.OnSize(self, event)
        self.Refresh()
