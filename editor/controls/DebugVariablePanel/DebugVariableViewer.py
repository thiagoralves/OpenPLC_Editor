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
from collections import OrderedDict
from functools import reduce

import wx
from matplotlib.backends.backend_wxagg import _convert_agg_to_wx_bitmap

from dialogs.ForceVariableDialog import ForceVariableDialog

# Viewer highlight types
[HIGHLIGHT_NONE,
 HIGHLIGHT_BEFORE,
 HIGHLIGHT_AFTER,
 HIGHLIGHT_LEFT,
 HIGHLIGHT_RIGHT,
 HIGHLIGHT_RESIZE] = range(6)

# Viewer highlight styles
HIGHLIGHT = {
}

# -------------------------------------------------------------------------------
#                        Base Debug Variable Viewer Class
# -------------------------------------------------------------------------------


class DebugVariableViewer(object):
    """
    Class that implements a generic viewer that display a list of variable values
    This class has to be inherited to effectively display variable values
    """

    def __init__(self, window, items=None):
        """
        Constructor
        @param window: Reference to the Debug Variable Panel
        @param items: List of DebugVariableItem displayed by Viewer
        """
        self.ParentWindow = window
        items = [] if items is None else items
        self.ItemsDict = OrderedDict([(item.GetVariable(), item)
                                      for item in items])
        self.Items = self.ItemsDict.viewvalues()

        # Variable storing current highlight displayed in Viewer
        self.Highlight = HIGHLIGHT_NONE
        # List of buttons
        self.Buttons = []
        self.InitHighlightPensBrushes()

    def __del__(self):
        """
        Destructor
        """
        # Remove reference to Debug Variable Panel
        self.ParentWindow = None

    def InitHighlightPensBrushes(self):
        """
        Init global pens and brushes
        """
        if not HIGHLIGHT:
            HIGHLIGHT['DROP_PEN'] = wx.Pen(wx.Colour(0, 128, 255))
            HIGHLIGHT['DROP_BRUSH'] = wx.Brush(wx.Colour(0, 128, 255, 128))
            HIGHLIGHT['RESIZE_PEN'] = wx.Pen(wx.Colour(200, 200, 200))
            HIGHLIGHT['RESIZE_BRUSH'] = wx.Brush(wx.Colour(200, 200, 200))

    def GetIndex(self):
        """
        Return position of Viewer in Debug Variable Panel
        @return: Position of Viewer
        """
        return self.ParentWindow.GetViewerIndex(self)

    def GetItem(self, variable):
        """
        Return item storing values of a variable
        @param variable: Variable path
        @return: Item storing values of this variable
        """
        return self.ItemsDict.get(variable, None)

    def GetItems(self):
        """
        Return items displayed by Viewer
        @return: List of items displayed in Viewer
        """
        return self.ItemsDict.values()

    def AddItem(self, item):
        """
        Add an item to the list of items displayed by Viewer
        @param item: Item to add to the list
        """
        self.ItemsDict[item.GetVariable()] = item

    def RemoveItem(self, item):
        """
        Remove an item from the list of items displayed by Viewer
        @param item: Item to remove from the list
        """
        self.ItemsDict.pop(item.GetVariable(), None)

    def ClearItems(self):
        """
        Clear list of items displayed by Viewer
        """
        # Unsubscribe every items of the list
        for item in self.Items:
            self.ParentWindow.RemoveDataConsumer(item)

        # Clear list
        self.ItemsDict.clear()

    def ItemsIsEmpty(self):
        """
        Return if list of items displayed by Viewer is empty
        @return: True if list is empty
        """
        return len(self.Items) == 0

    def SubscribeAllDataConsumers(self):
        """
        Function that unsubscribe and remove every item that store values of
        a variable that doesn't exist in PLC anymore
        """
        for item in self.ItemsDict.values()[:]:
            iec_path = item.GetVariable()

            # Check that variablepath exist in PLC
            if self.ParentWindow.GetDataType(iec_path) is None:
                # If not, unsubscribe and remove it
                self.ParentWindow.RemoveDataConsumer(item)
                self.RemoveItem(item)
            else:
                # If it exist, resubscribe and refresh data type
                self.ParentWindow.AddDataConsumer(iec_path.upper(), item, True)
                item.RefreshVariableType()

    def ResetItemsData(self):
        """
        Reset data stored in every items displayed in Viewer
        """
        for item in self.Items:
            item.ResetData()

    def GetItemsMinCommonTick(self):
        """
        Return the minimum tick common to all iems displayed in Viewer
        @return: Minimum common tick between items
        """
        return reduce(max, [item.GetData()[0, 0]
                            for item in self.Items
                            if len(item.GetData()) > 0], 0)

    def RefreshViewer(self):
        """
        Method that refresh the content displayed by Viewer
        Need to be overridden by inherited classes
        """
        pass

    def SetHighlight(self, highlight):
        """
        Set Highlight type displayed in Viewer
        @return: True if highlight has changed
        """
        # Return immediately if highlight don't change
        if self.Highlight == highlight:
            return False

        self.Highlight = highlight
        return True

    def GetButtons(self):
        """
        Return list of buttons defined in Viewer
        @return: List of buttons
        """
        return self.Buttons

    def IsOverButton(self, x, y):
        """
        Return if point is over one button of Viewer
        @param x: X coordinate of point
        @param y: Y coordinate of point
        @return: button where point is over
        """
        for button in self.GetButtons():
            if button.HitTest(x, y):
                return button
        return None

    def HandleButton(self, x, y):
        """
        Search for the button under point and if found execute associated
        callback
        @param x: X coordinate of point
        @param y: Y coordinate of point
        @return: True if a button was found and callback executed
        """
        button = self.IsOverButton(x, y)
        if button is None:
            return False

        button.ProcessCallback()
        return True

    def ShowButtons(self, show):
        """
        Set display state of buttons in Viewer
        @param show: Display state (True if buttons must be displayed)
        """
        # Change display of every buttons
        for button in self.Buttons:
            button.Show(show)

        # Refresh button positions
        self.RefreshButtonsPosition()
        self.RefreshViewer()

    def RefreshButtonsPosition(self):
        """
        Function that refresh buttons position in Viewer
        """
        # Get Viewer size
        width, _height = self.GetSize()

        # Buttons are align right so we calculate buttons positions in
        # reverse order
        buttons = self.Buttons[:]
        buttons.reverse()

        # Position offset on x coordinate
        x_offset = 0
        for button in buttons:
            # Buttons are stacked right, removing those that are not active
            if button.IsEnabled():
                # Update button position according to button width and offset
                # on x coordinate
                w, _h = button.GetSize()
                button.SetPosition(width - 5 - w - x_offset, 5)
                # Update offset on x coordinate
                x_offset += w + 2

    def DrawCommonElements(self, dc, buttons=None):
        """
        Function that draw common graphics for every Viewers
        @param dc: wx.DC object corresponding to Device context where drawing
        common graphics
        @param buttons: List of buttons to draw if different from default
        (default None)
        """
        # Get Viewer size
        width, height = self.GetSize()

        # Set dc styling for drop before or drop after highlight
        dc.SetPen(HIGHLIGHT['DROP_PEN'])
        dc.SetBrush(HIGHLIGHT['DROP_BRUSH'])

        # Draw line at upper side of Viewer if highlight is drop before
        if self.Highlight == HIGHLIGHT_BEFORE:
            dc.DrawLine(0, 1, width - 1, 1)

        # Draw line at lower side of Viewer if highlight is drop before
        elif self.Highlight == HIGHLIGHT_AFTER:
            dc.DrawLine(0, height - 1, width - 1, height - 1)

        # If no specific buttons are defined, get default buttons
        if buttons is None:
            buttons = self.Buttons
        # Draw buttons
        for button in buttons:
            button.Draw(dc)

        # If graph dragging is processing
        if self.ParentWindow.IsDragging():
            destBBox = self.ParentWindow.GetDraggingAxesClippingRegion(self)
            srcPos = self.ParentWindow.GetDraggingAxesPosition(self)
            if destBBox.width > 0 and destBBox.height > 0:
                srcPanel = self.ParentWindow.DraggingAxesPanel
                srcBBox = srcPanel.GetAxesBoundingBox()

                srcX = srcBBox.x - (srcPos.x if destBBox.x == 0 else 0)
                srcY = srcBBox.y - (srcPos.y if destBBox.y == 0 else 0)

                srcBmp = _convert_agg_to_wx_bitmap(
                    srcPanel.get_renderer(), None)
                srcDC = wx.MemoryDC()
                srcDC.SelectObject(srcBmp)

                dc.Blit(destBBox.x, destBBox.y,
                        int(destBBox.width), int(destBBox.height),
                        srcDC, srcX, srcY)

    def OnEnter(self, event):
        """
        Function called when entering Viewer
        @param event: wx.MouseEvent
        """
        # Display buttons
        self.ShowButtons(True)
        event.Skip()

    def OnLeave(self, event):
        """
        Function called when leaving Viewer
        @param event: wx.MouseEvent
        """
        # Hide buttons
        self.ShowButtons(False)
        event.Skip()

    def OnCloseButton(self):
        """
        Function called when Close button is pressed
        """
        wx.CallAfter(self.ParentWindow.DeleteValue, self)

    def OnForceButton(self):
        """
        Function called when Force button is pressed
        """
        self.ForceValue(self.ItemsDict.values()[0])

    def OnReleaseButton(self):
        """
        Function called when Release button is pressed
        """
        self.ReleaseValue(self.ItemsDict.values()[0])

    def OnMouseDragging(self, x, y):
        """
        Function called when mouse is dragged over Viewer
        @param x: X coordinate of mouse pointer
        @param y: Y coordinate of mouse pointer
        """
        xw, yw = self.GetPosition()
        # Refresh highlight in Debug Variable Panel (highlight can be displayed
        # in another Viewer
        self.ParentWindow.RefreshHighlight(x + xw, y + yw)

    def RefreshHighlight(self, x, y):
        """
        Function called by Debug Variable Panel asking Viewer to refresh
        highlight according to mouse position
        @param x: X coordinate of mouse pointer
        @param y: Y coordinate of mouse pointer
        """
        # Get Viewer size
        _width, height = self.GetSize()

        # Mouse is in the first half of Viewer
        if y < height // 2:
            # If Viewer is the upper one, draw drop before highlight
            if self.ParentWindow.IsViewerFirst(self):
                self.SetHighlight(HIGHLIGHT_BEFORE)

            # Else draw drop after highlight in previous Viewer
            else:
                self.SetHighlight(HIGHLIGHT_NONE)
                self.ParentWindow.HighlightPreviousViewer(self)

        # Mouse is in the second half of Viewer, draw drop after highlight
        else:
            self.SetHighlight(HIGHLIGHT_AFTER)

    def OnEraseBackground(self, event):
        """
        Function called when Viewer background is going to be erase
        @param event: wx.EraseEvent
        """
        # Prevent flicker on Windows
        pass

    def OnResize(self, event):
        """
        Function called when Viewer size changed
        @param event: wx.ResizeEvent
        """
        # Refresh button positions
        self.RefreshButtonsPosition()
        self.ParentWindow.ForceRefresh()
        event.Skip()

    def ForceValue(self, item):
        """
        Force value of item given
        @param item: Item to force value
        """
        # Check variable data type
        iec_path = item.GetVariable()
        iec_type = self.ParentWindow.GetDataType(iec_path)
        # Return immediately if not found
        if iec_type is None:
            return

        # Open a dialog to enter varaible forced value
        dialog = ForceVariableDialog(self, iec_type, str(item.GetValue()))
        if dialog.ShowModal() == wx.ID_OK:
            self.ParentWindow.ForceDataValue(iec_path.upper(),
                                             dialog.GetValue())

    def ReleaseValue(self, item):
        """
        Release value of item given
        @param item: Item to release value
        """
        self.ParentWindow.ReleaseDataValue(
            item.GetVariable().upper())
