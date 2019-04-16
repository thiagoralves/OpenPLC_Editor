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

import wx

from controls.DebugVariablePanel.DebugVariableViewer import DebugVariableViewer
from controls.DebugVariablePanel.GraphButton import GraphButton

# -------------------------------------------------------------------------------
#                     Debug Variable Text Viewer Drop Target
# -------------------------------------------------------------------------------


class DebugVariableTextDropTarget(wx.TextDropTarget):
    """
    Class that implements a custom drop target class for Debug Variable Text Viewer
    """

    def __init__(self, parent, window):
        """
        Constructor
        @param parent: Reference to Debug Variable Text Viewer
        @param window: Reference to the Debug Variable Panel
        """
        wx.TextDropTarget.__init__(self)
        self.ParentControl = parent
        self.ParentWindow = window

    def __del__(self):
        """
        Destructor
        """
        # Remove reference to Debug Variable Text Viewer and Debug Variable
        # Panel
        self.ParentControl = None
        self.ParentWindow = None

    def OnDragOver(self, x, y, d):
        """
        Function called when mouse is dragged over Drop Target
        @param x: X coordinate of mouse pointer
        @param y: Y coordinate of mouse pointer
        @param d: Suggested default for return value
        """
        # Signal parent that mouse is dragged over
        self.ParentControl.OnMouseDragging(x, y)

        return wx.TextDropTarget.OnDragOver(self, x, y, d)

    def OnDropText(self, x, y, data):
        """
        Function called when mouse is released in Drop Target
        @param x: X coordinate of mouse pointer
        @param y: Y coordinate of mouse pointer
        @param data: Text associated to drag'n drop
        """
        # Signal Debug Variable Panel to reset highlight
        self.ParentWindow.ResetHighlight()

        message = None

        # Check that data is valid regarding DebugVariablePanel
        try:
            values = eval(data)
            if not isinstance(values, tuple):
                raise ValueError
        except Exception:
            message = _("Invalid value \"%s\" for debug variable") % data
            values = None

        # Display message if data is invalid
        if message is not None:
            wx.CallAfter(self.ShowMessage, message)

        # Data contain a reference to a variable to debug
        elif values[1] == "debug":

            # Get Before which Viewer the variable has to be moved or added
            # according to the position of mouse in Viewer.
            _width, height = self.ParentControl.GetSize()
            target_idx = self.ParentControl.GetIndex()
            if y > height // 2:
                target_idx += 1

            # Drag'n Drop is an internal is an internal move inside Debug
            # Variable Panel
            if len(values) > 2 and values[2] == "move":
                self.ParentWindow.MoveValue(values[0],
                                            target_idx)

            # Drag'n Drop was initiated by another control of Beremiz
            else:
                self.ParentWindow.InsertValue(values[0],
                                              target_idx,
                                              force=True)

    def OnLeave(self):
        """
        Function called when mouse is leave Drop Target
        """
        # Signal Debug Variable Panel to reset highlight
        self.ParentWindow.ResetHighlight()

        return wx.TextDropTarget.OnLeave(self)

    def ShowMessage(self, message):
        """
        Show error message in Error Dialog
        @param message: Error message to display
        """
        dialog = wx.MessageDialog(self.ParentWindow,
                                  message,
                                  _("Error"),
                                  wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()


# -------------------------------------------------------------------------------
#                      Debug Variable Text Viewer Class
# -------------------------------------------------------------------------------

class DebugVariableTextViewer(DebugVariableViewer, wx.Panel):
    """
    Class that implements a Viewer that display variable values as a text
    """

    def __init__(self, parent, window, items=None):
        """
        Constructor
        @param parent: Parent wx.Window of DebugVariableText
        @param window: Reference to the Debug Variable Panel
        @param items: List of DebugVariableItem displayed by Viewer
        """
        DebugVariableViewer.__init__(self, window, items)

        wx.Panel.__init__(self, parent)
        # Set panel background colour
        self.SetBackgroundColour(wx.WHITE)
        # Define panel drop target
        self.SetDropTarget(DebugVariableTextDropTarget(self, window))

        # Bind events
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # Define panel min size for parent sizer layout
        self.SetMinSize(wx.Size(0, 25))

        # Add buttons to Viewer
        for bitmap, callback in [("force", self.OnForceButton),
                                 ("release", self.OnReleaseButton),
                                 ("delete_graph", self.OnCloseButton)]:
            self.Buttons.append(GraphButton(0, 0, bitmap, callback))

    def RefreshViewer(self):
        """Triggers EVT_PAINT event to refresh UI"""
        self.Refresh()

    def DrawViewer(self):
        """
        Redraw content displayed by Viewer
        """
        # Create buffered DC for drawing in panel
        width, height = self.GetSize()
        bitmap = wx.EmptyBitmap(width, height)
        dc = wx.BufferedDC(wx.ClientDC(self), bitmap)
        dc.Clear()

        # Get Graphics Context for DC, for anti-aliased and transparent
        # rendering
        gc = wx.GCDC(dc)

        gc.BeginDrawing()

        # Get first item
        item = self.ItemsDict.values()[0]

        # Get item variable path masked according Debug Variable Panel mask
        item_path = item.GetVariable(
            self.ParentWindow.GetVariableNameMask())

        # Draw item variable path at Viewer left side
        w, h = gc.GetTextExtent(item_path)
        gc.DrawText(item_path, 20, (height - h) // 2)

        # Update 'Release' button state and text color according to item forced
        # flag value
        item_forced = item.IsForced()
        self.Buttons[1].Enable(item_forced)
        self.RefreshButtonsPosition()
        if item_forced:
            gc.SetTextForeground(wx.BLUE)

        # Draw item current value at right side of Viewer
        item_value = item.GetValue()
        w, h = gc.GetTextExtent(item_value)
        gc.DrawText(item_value, width - 40 - w, (height - h) // 2)

        # Draw other Viewer common elements
        self.DrawCommonElements(gc)

        gc.EndDrawing()

    def OnLeftDown(self, event):
        """
        Function called when mouse left button is pressed
        @param event: wx.MouseEvent
        """
        # Get first item
        item = self.ItemsDict.values()[0]

        # Calculate item path bounding box
        _width, height = self.GetSize()
        item_path = item.GetVariable(
            self.ParentWindow.GetVariableNameMask())
        w, h = self.GetTextExtent(item_path)

        # Test if mouse has been pressed in this bounding box. In that case
        # start a move drag'n drop of item variable
        x, y = event.GetPosition()
        item_path_bbox = wx.Rect(20, (height - h) / 2, w, h)
        if item_path_bbox.InsideXY(x, y):
            self.ShowButtons(False)
            data = wx.TextDataObject(str((item.GetVariable(), "debug", "move")))
            dragSource = wx.DropSource(self)
            dragSource.SetData(data)
            dragSource.DoDragDrop()

        # In other case handle event normally
        else:
            event.Skip()

    def OnLeftUp(self, event):
        """
        Function called when mouse left button is released
        @param event: wx.MouseEvent
        """
        # Execute callback on button under mouse pointer if it exists
        x, y = event.GetPosition()
        wx.CallAfter(self.HandleButton, x, y)
        event.Skip()

    def OnLeftDClick(self, event):
        """
        Function called when mouse left button is double clicked
        @param event: wx.MouseEvent
        """
        # Only numeric variables can be toggled to graph canvas
        if self.ItemsDict.values()[0].IsNumVariable():
            self.ParentWindow.ToggleViewerType(self)

    def OnPaint(self, event):
        """
        Function called when redrawing Viewer content is needed
        @param event: wx.PaintEvent
        """
        self.DrawViewer()
        event.Skip()
