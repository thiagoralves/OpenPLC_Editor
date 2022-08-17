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
from functools import reduce
import wx
import wx.stc
from six.moves import xrange

if wx.Platform == '__WXMSW__':
    faces = {
        'times': 'Times New Roman',
        'mono':  'Courier New',
        'helv':  'Arial',
        'other': 'Comic Sans MS',
        'size':  10,
    }
else:
    faces = {
        'times': 'Times',
        'mono':  'FreeMono',
        'helv':  'Helvetica',
        'other': 'new century schoolbook',
        'size':  12,
    }

NAVIGATION_KEYS = [
    wx.WXK_END,
    wx.WXK_HOME,
    wx.WXK_LEFT,
    wx.WXK_UP,
    wx.WXK_RIGHT,
    wx.WXK_DOWN,
    wx.WXK_PAGEUP,
    wx.WXK_PAGEDOWN,
    wx.WXK_NUMPAD_HOME,
    wx.WXK_NUMPAD_LEFT,
    wx.WXK_NUMPAD_UP,
    wx.WXK_NUMPAD_RIGHT,
    wx.WXK_NUMPAD_DOWN,
    wx.WXK_NUMPAD_PAGEUP,
    wx.WXK_NUMPAD_PAGEDOWN,
    wx.WXK_NUMPAD_END]


def GetCursorPos(old, new):
    if old == "":
        return 0
    old_length = len(old)
    new_length = len(new)
    common_length = min(old_length, new_length)
    i = 0
    for i in xrange(common_length):
        if old[i] != new[i]:
            break
    if old_length < new_length:
        if common_length > 0 and old[i] != new[i]:
            return i + new_length - old_length
        else:
            return i + new_length - old_length + 1
    elif old_length > new_length or i < min(old_length, new_length) - 1:
        if common_length > 0 and old[i] != new[i]:
            return i
        else:
            return i + 1
    else:
        return None


class CustomStyledTextCtrl(wx.stc.StyledTextCtrl):

    def __init__(self, *args, **kwargs):
        wx.stc.StyledTextCtrl.__init__(self, *args, **kwargs)

        self.Bind(wx.EVT_MOTION, self.OnMotion)

    def OnMotion(self, event):
        if wx.Platform == '__WXMSW__':
            if not event.Dragging():
                x, _y = event.GetPosition()
                margin_width = reduce(
                    lambda x, y: x + y,
                    [self.GetMarginWidth(i) for i in xrange(3)],
                    0)
                if x <= margin_width:
                    self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
                else:
                    self.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))
            else:
                event.Skip()
        else:
            event.Skip()

    def AppendText(self, text):
        self.GotoPos(self.GetLength())
        self.AddText(text)
