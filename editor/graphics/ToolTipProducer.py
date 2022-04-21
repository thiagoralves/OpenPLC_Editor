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

from controls.CustomToolTip import CustomToolTip, TOOLTIP_WAIT_PERIOD


# -------------------------------------------------------------------------------
#                           Tool Tip Producer class
# -------------------------------------------------------------------------------


class ToolTipProducer(object):
    """
    Class that implements an element that generate Tool Tip
    """

    def __init__(self, parent):
        """
        Constructor
        @param parent: Parent Viewer
        """
        self.Parent = parent

        self.ToolTip = None
        self.ToolTipPos = None

        # Timer for firing Tool tip display
        self.ToolTipTimer = wx.Timer(self.Parent, -1)
        self.Parent.Bind(wx.EVT_TIMER,
                         self.OnToolTipTimer,
                         self.ToolTipTimer)

    def __del__(self):
        """
        Destructor
        """
        self.DestroyToolTip()

    def OnToolTipTimer(self, event):
        """
        Callback for Tool Tip firing timer Event
        @param event: Tool tip text
        """
        # Get Tool Tip text
        value = self.GetToolTipValue()

        if value is not None and self.ToolTipPos is not None:
            # Create Tool Tip
            self.ToolTip = CustomToolTip(self.Parent, value)
            self.ToolTip.SetToolTipPosition(self.ToolTipPos)
            self.ToolTip.Show()

    def GetToolTipValue(self):
        """
        Return tool tip text
        Have to be overridden by inherited classes
        @return: Tool tip text (None if not overridden)
        """
        return None

    def DisplayToolTip(self, pos):
        """
        Display Tool tip
        @param pos: Tool tip position
        """
        # Destroy current displayed Tool tip
        self.DestroyToolTip()

        # Save Tool Tip position
        self.ToolTipPos = pos
        # Start Tool tip firing timer
        self.ToolTipTimer.Start(
            int(TOOLTIP_WAIT_PERIOD * 1000),
            oneShot=True)

    def SetToolTipText(self, text):
        """
        Set current Tool tip text
        @param text: Tool tip Text
        """
        if self.ToolTip is not None:
            self.ToolTip.SetTip(text)

    def DestroyToolTip(self):
        """
        Destroy current displayed Tool Tip
        """
        # Stop Tool tip firing timer
        self.ToolTipTimer.Stop()
        self.ToolTipPos = None

        # Destroy Tool Tip
        if self.ToolTip is not None:
            self.ToolTip.Destroy()
            self.ToolTip = None
