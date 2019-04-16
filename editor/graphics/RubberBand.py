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

from graphics.GraphicCommons import GetScaledEventPosition


# -------------------------------------------------------------------------------
#                               Viewer RubberBand
# -------------------------------------------------------------------------------


class RubberBand(object):
    """
    Class that implements a rubberband for graphic Viewers
    """

    def __init__(self, viewer):
        """
        Constructor
        @param viewer: Viewer on which rubberband must be drawn
        """
        self.Viewer = viewer

        # wx.Panel on which rubberband will be drawn
        self.DrawingSurface = viewer.Editor

        self.Reset()

    def Reset(self):
        """
        Initialize internal attributes of rubberband
        """
        self.StartPoint = None
        self.CurrentBBox = None
        self.LastBBox = None

    def IsShown(self):
        """
        Indicate if rubberband is drawn on viewer
        @return: True if rubberband is drawn
        """
        return self.CurrentBBox is not None

    def GetCurrentExtent(self):
        """
        Return the rubberband bounding box
        @return: Rubberband bounding box (wx.Rect object)
        """
        # In case of rubberband not shown, return the last rubberband
        # bounding box
        if self.IsShown():
            return self.CurrentBBox
        return self.LastBBox

    def OnLeftDown(self, event, dc, scaling):
        """
        Called when left mouse is pressed on Viewer. Starts to edit a new
        rubberband bounding box
        @param event: Mouse event
        @param dc: Device Context of Viewer
        @param scaling: PLCOpen scaling applied on Viewer
        """
        # Save the point where mouse was pressed in Viewer unit, position may
        # be modified by scroll and zoom applied on viewer
        self.StartPoint = GetScaledEventPosition(event, dc, scaling)

        # Initialize rubberband bounding box
        self.CurrentBBox = wx.Rect(self.StartPoint.x, self.StartPoint.y, 0, 0)

        # Change viewer mouse cursor to reflect a rubberband bounding box is
        # edited
        self.DrawingSurface.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        self.Redraw()

    def OnMotion(self, event, dc, scaling):
        """
        Called when mouse is dragging over Viewer. Update the current edited
        rubberband bounding box
        @param event: Mouse event
        @param dc: Device Context of Viewer
        @param scaling: PLCOpen scaling applied on Viewer
        """
        # Get mouse position in Viewer unit, position may be modified by scroll
        # and zoom applied on viewer
        pos = GetScaledEventPosition(event, dc, scaling)

        # Save the last bounding box drawn for erasing it later
        self.LastBBox = wx.Rect(0, 0, 0, 0)
        self.LastBBox.Union(self.CurrentBBox)

        # Calculate new position and size of the box
        self.CurrentBBox.x = min(pos.x, self.StartPoint.x)
        self.CurrentBBox.y = min(pos.y, self.StartPoint.y)
        self.CurrentBBox.width = abs(pos.x - self.StartPoint.x) + 1
        self.CurrentBBox.height = abs(pos.y - self.StartPoint.y) + 1

        self.Redraw()

    def OnLeftUp(self, event, dc, scaling):
        """
        Called when mouse is release from Viewer. Erase the current edited
        rubberband bounding box
        @param event: Mouse event
        @param dc: Device Context of Viewer
        @param scaling: PLCOpen scaling applied on Viewer
        """
        # Change viewer mouse cursor to default
        self.DrawingSurface.SetCursor(wx.NullCursor)

        # Save the last edited bounding box
        self.LastBBox = self.CurrentBBox
        self.CurrentBBox = None

        self.Redraw()

    def DrawBoundingBoxes(self, bboxes, dc=None):
        """
        Draw a list of bounding box on Viewer in the order given using XOR
        logical function
        @param bboxes: List of bounding boxes to draw on viewer
        @param dc: Device Context of Viewer (default None)
        """
        # Get viewer Device Context if not given
        if dc is None:
            dc = self.Viewer.GetLogicalDC()

        # Save current viewer scale factors before resetting them in order to
        # avoid rubberband pen to be scaled
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)

        # Set DC drawing style
        dc.SetPen(wx.Pen(wx.WHITE, style=wx.DOT))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)

        # Draw the bounding boxes using viewer scale factor
        for bbox in bboxes:
            if bbox is not None:
                dc.DrawRectangle(
                    bbox.x * scalex, bbox.y * scaley,
                    bbox.width * scalex, bbox.height * scaley)

        dc.SetLogicalFunction(wx.COPY)

        # Restore Viewer scale factor
        dc.SetUserScale(scalex, scaley)

    def Redraw(self, dc=None):
        """
        Redraw rubberband on Viewer
        @param dc: Device Context of Viewer (default None)
        """
        # Erase last bbox and draw current bbox
        self.DrawBoundingBoxes([self.LastBBox, self.CurrentBBox], dc)

    def Erase(self, dc=None):
        """
        Erase rubberband from Viewer
        @param dc: Device Context of Viewer (default None)
        """
        # Erase last bbox
        self.DrawBoundingBoxes([self.LastBBox], dc)

    def Draw(self, dc=None):
        """
        Draw rubberband on Viewer
        @param dc: Device Context of Viewer (default None)
        """
        # Erase last bbox and draw current bbox
        self.DrawBoundingBoxes([self.CurrentBBox], dc)
