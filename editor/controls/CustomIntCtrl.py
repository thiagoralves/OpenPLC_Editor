#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
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
import wx
import wx.lib.intctrl


class CustomIntUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, id, value=0, object=None):
        wx.PyCommandEvent.__init__(self, CustomIntCtrl.wxEVT_COMMAND_CUSTOM_INT_UPDATED, id)

        self.__value = value
        self.SetEventObject(object)

    def GetValue(self):
        """Retrieve the value of the control at the time
        this event was generated."""
        return self.__value


class CustomIntCtrl(wx.lib.intctrl.IntCtrl):
    """
    This class provides a control that takes and returns long as
    value, and provides bounds support and optional value limiting.

    It handles entering negative numbers more user-friendly than
    original wx.lib.intctrl.IntCtrl.

    It applies limits as focus is changed to other control and
    sends event afterwards to signal that editing is done.
    """

    # Used to trap events indicating that the current
    # integer value of the control has been changed.
    wxEVT_COMMAND_CUSTOM_INT_UPDATED = wx.NewEventType()
    EVT_CUSTOM_INT = wx.PyEventBinder(wxEVT_COMMAND_CUSTOM_INT_UPDATED, 1)

    def __init__(self, *args, **kwargs):
        wx.lib.intctrl.IntCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_KILL_FOCUS, self.UpdateValue)
        self.SetLongAllowed(True)
        self.SetLimited(False)

    def GetValue(self):
        """
        Returns integer (long) value of the control,
        but handles entering negative numbers
        """
        s = wx.TextCtrl.GetValue(self)
        if s == '-':
            s = ''
        return self._fromGUI(s)

    def GetValueStr(self):
        """Returns string value of TextCtrl"""
        return wx.TextCtrl.GetValue(self)

    def UpdateValue(self, event):
        self.SetLimited(True)
        self.SetLimited(False)
        try:
            self.GetEventHandler().ProcessEvent(
                CustomIntUpdatedEvent(self.GetId(), self.GetValue(), self))
        except ValueError:
            return
        event.Skip()
