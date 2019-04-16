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

from controls.CustomStyledTextCtrl import faces

TOOLTIP_MAX_CHARACTERS = 30  # Maximum number of characters by line in ToolTip
TOOLTIP_MAX_LINE = 5         # Maximum number of line in ToolTip
TOOLTIP_WAIT_PERIOD = 0.5    # Wait period before displaying tooltip in second

# -------------------------------------------------------------------------------
#                               Custom ToolTip
# -------------------------------------------------------------------------------


class CustomToolTip(wx.PopupWindow):
    """
    Class that implements a custom tool tip
    """

    def __init__(self, parent, tip, restricted=True):
        """
        Constructor
        @param parent: Parent window
        @param tip: Tip text (may be multiline)
        @param restricted: Tool tip must follow size restriction in line and
            characters number defined (default True)
        """
        wx.PopupWindow.__init__(self, parent)

        self.Restricted = restricted

        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.SetTip(tip)

        # Initialize text font style
        self.Font = wx.Font(
            faces["size"],
            wx.SWISS,
            wx.NORMAL,
            wx.NORMAL,
            faceName=faces["mono"])

        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetFont(self, font):
        """
        Set tool tip text font style
        @param font: wx.Font object containing font style
        """
        self.Font = font
        self.RefreshTip()

    def SetTip(self, tip):
        """
        Set tool tip text
        @param tip: Tool tip text
        """
        if self.Restricted:
            # Compute tip text line return
            self.Tip = []
            for line in tip.splitlines():
                if line != "":
                    words = line.split()
                    new_line = words[0]
                    for word in words[1:]:
                        # Add word to line
                        if len(new_line + " " + word) <= TOOLTIP_MAX_CHARACTERS:
                            new_line += " " + word
                        # Create new line
                        else:
                            self.Tip.append(new_line)
                            new_line = word
                    self.Tip.append(new_line)
                else:
                    self.Tip.append(line)

            # Restrict number of lines
            if len(self.Tip) > TOOLTIP_MAX_LINE:
                self.Tip = self.Tip[:TOOLTIP_MAX_LINE]

                # Add ... to the end of last line to indicate that tool tip
                # text is too long
                if len(self.Tip[-1]) < TOOLTIP_MAX_CHARACTERS - 3:
                    self.Tip[-1] += "..."
                else:
                    self.Tip[-1] = self.Tip[-1][:TOOLTIP_MAX_CHARACTERS - 3] + \
                                   "..."
        else:
            self.Tip = tip.splitlines()

        # Prevent to call wx method in non-wx threads
        wx.CallAfter(self.RefreshTip)

    def SetToolTipPosition(self, pos):
        """
        Set tool tip position
        @param pos: New tool tip position
        """
        # Get screen size to prevent tool tip to go out of the screen
        screen_width, screen_height = wx.GetDisplaySize()

        # Calculate position of tool tip to stay in screen limits
        tip_width, tip_height = self.GetToolTipSize()
        self.SetPosition(wx.Point(
            max(0, min(pos.x, screen_width - tip_width)),
            max(0, min(pos.y, screen_height - tip_height))))

    def GetToolTipSize(self):
        """
        Get tool tip size according to tip text and restriction
        @return: wx.Size(tool_tip_width, tool_tip_height)
        """
        max_width = max_height = 0

        # Create a memory DC for calculating text extent
        dc = wx.MemoryDC(wx.EmptyBitmap(1, 1))
        dc.SetFont(self.Font)

        # Compute max tip text size
        for line in self.Tip:
            w, h = dc.GetTextExtent(line)
            max_width = max(max_width, w)
            max_height += h

        return wx.Size(max_width + 4, max_height + 4)

    def RefreshTip(self):
        """
        Refresh tip on screen
        """
        # Prevent to call this function if tool tip destroyed
        if self:
            # Refresh tool tip size and position
            self.SetClientSize(self.GetToolTipSize())

            # Redraw tool tip
            self.Refresh()

    def OnPaint(self, event):
        """
        Callback for Paint Event
        @param event: Paint event
        """
        # Get buffered paint DC for tool tip
        dc = wx.AutoBufferedPaintDC(self)
        dc.Clear()

        # Set DC drawing style
        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.Brush(wx.Colour(255, 238, 170)))
        dc.SetFont(self.Font)

        # Draw Tool tip
        dc.BeginDrawing()
        tip_width, tip_height = self.GetToolTipSize()

        # Draw background rectangle
        dc.DrawRectangle(0, 0, tip_width, tip_height)

        # Draw tool tip text
        line_offset = 0
        for line in self.Tip:
            dc.DrawText(line, 2, line_offset + 2)
            _line_width, line_height = dc.GetTextExtent(line)
            line_offset += line_height

        dc.EndDrawing()

        event.Skip()
