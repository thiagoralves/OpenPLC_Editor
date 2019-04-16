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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from __future__ import absolute_import
from __future__ import division
from time import time as gettime
from cycler import cycler

import numpy
import wx
import matplotlib
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import _convert_agg_to_wx_bitmap
from matplotlib.backends.backend_agg import FigureCanvasAgg
from mpl_toolkits.mplot3d import Axes3D
from six.moves import xrange

from editors.DebugViewer import REFRESH_PERIOD
from controls.DebugVariablePanel.DebugVariableViewer import *
from controls.DebugVariablePanel.GraphButton import GraphButton


# Graph variable display type
GRAPH_PARALLEL, GRAPH_ORTHOGONAL = range(2)

# Canvas height
[SIZE_MINI, SIZE_MIDDLE, SIZE_MAXI] = [0, 100, 200]

CANVAS_BORDER = (30., 20.)  # Border height on at bottom and top of graph
CANVAS_PADDING = 8.5        # Border inside graph where no label is drawn
VALUE_LABEL_HEIGHT = 17.    # Height of variable label in graph
AXES_LABEL_HEIGHT = 12.75   # Height of variable value in graph

# Colors used cyclically for graph curves
COLOR_CYCLE = ['r', 'b', 'g', 'm', 'y', 'k']
# Color for graph cursor
CURSOR_COLOR = '#800080'

# -------------------------------------------------------------------------------
#                      Debug Variable Graphic Viewer Helpers
# -------------------------------------------------------------------------------


def merge_ranges(ranges):
    """
    Merge variables data range in a list to return a range of minimal min range
    value and maximal max range value extended of 10% for keeping a padding
    around graph in canvas
    @param ranges: [(range_min_value, range_max_value),...]
    @return: merged_range_min_value, merged_range_max_value
    """
    # Get minimal and maximal range value
    min_value = max_value = None
    for range_min, range_max in ranges:
        # Update minimal range value
        if min_value is None:
            min_value = range_min
        elif range_min is not None:
            min_value = min(min_value, range_min)

        # Update maximal range value
        if max_value is None:
            max_value = range_max
        elif range_min is not None:
            max_value = max(max_value, range_max)

    # Calculate range center and width if at least one valid range is defined
    if min_value is not None and max_value is not None:
        center = (min_value + max_value) / 2.
        range_size = max(1.0, max_value - min_value)

    # Set default center and with if no valid range is defined
    else:
        center = 0.5
        range_size = 1.0

    # Return range expended from 10 %
    return center - range_size * 0.55, center + range_size * 0.55

# -------------------------------------------------------------------------------
#                   Debug Variable Graphic Viewer Drop Target
# -------------------------------------------------------------------------------


class DebugVariableGraphicDropTarget(wx.TextDropTarget):
    """
    Class that implements a custom drop target class for Debug Variable Graphic
    Viewer
    """

    def __init__(self, parent, window):
        """
        Constructor
        @param parent: Reference to Debug Variable Graphic Viewer
        @param window: Reference to the Debug Variable Panel
        """
        wx.TextDropTarget.__init__(self)
        self.ParentControl = parent
        self.ParentWindow = window

    def __del__(self):
        """
        Destructor
        """
        # Remove reference to Debug Variable Graphic Viewer and Debug Variable
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
            target_idx = self.ParentControl.GetIndex()

            # If mouse is dropped in graph canvas bounding box and graph is
            # not 3D canvas, graphs will be merged
            rect = self.ParentControl.GetAxesBoundingBox()
            if not self.ParentControl.Is3DCanvas() and rect.InsideXY(x, y):
                # Default merge type is parallel
                merge_type = GRAPH_PARALLEL

                # If mouse is dropped in left part of graph canvas, graph
                # wall be merged orthogonally
                merge_rect = wx.Rect(rect.x, rect.y,
                                     rect.width / 2., rect.height)
                if merge_rect.InsideXY(x, y):
                    merge_type = GRAPH_ORTHOGONAL

                # Merge graphs
                wx.CallAfter(self.ParentWindow.MergeGraphs,
                             values[0], target_idx,
                             merge_type, force=True)

            else:
                _width, height = self.ParentControl.GetSize()

                # Get Before which Viewer the variable has to be moved or added
                # according to the position of mouse in Viewer.
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
#                      Debug Variable Graphic Viewer Class
# -------------------------------------------------------------------------------


class DebugVariableGraphicViewer(DebugVariableViewer, FigureCanvas):
    """
    Class that implements a Viewer that display variable values as a graphs
    """

    def __init__(self, parent, window, items, graph_type):
        """
        Constructor
        @param parent: Parent wx.Window of DebugVariableText
        @param window: Reference to the Debug Variable Panel
        @param items: List of DebugVariableItem displayed by Viewer
        @param graph_type: Graph display type (Parallel or orthogonal)
        """
        DebugVariableViewer.__init__(self, window, items)

        self.GraphType = graph_type        # Graph type display
        self.CursorTick = None             # Tick of the graph cursor

        # Mouse position when start dragging
        self.MouseStartPos = None
        # Tick when moving tick start
        self.StartCursorTick = None
        # Canvas size when starting to resize canvas
        self.CanvasStartSize = None

        # List of current displayed contextual buttons
        self.ContextualButtons = []
        # Reference to item for which contextual buttons was displayed
        self.ContextualButtonsItem = None

        # Flag indicating that zoom fit current displayed data range or whole
        # data range if False
        self.ZoomFit = False

        # Create figure for drawing graphs
        self.Figure = matplotlib.figure.Figure(facecolor='w')
        # Defined border around figure in canvas
        self.Figure.subplotpars.update(top=0.95, left=0.1,
                                       bottom=0.1, right=0.95)

        FigureCanvas.__init__(self, parent, -1, self.Figure)
        self.SetWindowStyle(wx.WANTS_CHARS)
        self.SetBackgroundColour(wx.WHITE)

        # Bind wx events
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnResize)

        # Set canvas min size
        canvas_size = self.GetCanvasMinSize()
        self.SetMinSize(canvas_size)

        # Define Viewer drop target
        self.SetDropTarget(DebugVariableGraphicDropTarget(self, window))

        # Connect matplotlib events
        self.mpl_connect('button_press_event', self.OnCanvasButtonPressed)
        self.mpl_connect('motion_notify_event', self.OnCanvasMotion)
        self.mpl_connect('button_release_event', self.OnCanvasButtonReleased)
        self.mpl_connect('scroll_event', self.OnCanvasScroll)

        # Add buttons for zooming on current displayed data range
        self.Buttons.append(
            GraphButton(0, 0, "fit_graph", self.OnZoomFitButton))

        # Add buttons for changing canvas size with predefined height
        for size, bitmap in zip(
                [SIZE_MINI, SIZE_MIDDLE, SIZE_MAXI],
                ["minimize_graph", "middle_graph", "maximize_graph"]):
            self.Buttons.append(GraphButton(0, 0, bitmap,
                                            self.GetOnChangeSizeButton(size)))

        # Add buttons for exporting graph values to clipboard and close graph
        for bitmap, callback in [
                ("export_graph_mini", self.OnExportGraphButton),
                ("delete_graph", self.OnCloseButton)]:
            self.Buttons.append(GraphButton(0, 0, bitmap, callback))

        # Update graphs elements
        self.ResetGraphics()
        self.RefreshLabelsPosition(canvas_size.height)

    def AddItem(self, item):
        """
        Add an item to the list of items displayed by Viewer
        @param item: Item to add to the list
        """
        DebugVariableViewer.AddItem(self, item)
        self.ResetGraphics()

    def RemoveItem(self, item):
        """
        Remove an item from the list of items displayed by Viewer
        @param item: Item to remove from the list
        """
        DebugVariableViewer.RemoveItem(self, item)

        # If list of items is not empty
        if not self.ItemsIsEmpty():
            # Return to parallel graph if there is only one item
            # especially if it's actually orthogonal
            if len(self.Items) == 1:
                self.GraphType = GRAPH_PARALLEL
            self.ResetGraphics()

    def SetCursorTick(self, cursor_tick):
        """
        Set cursor tick
        @param cursor_tick: Cursor tick
        """
        self.CursorTick = cursor_tick

    def SetZoomFit(self, zoom_fit):
        """
        Set flag indicating that zoom fit current displayed data range
        @param zoom_fit: Flag for zoom fit (False: zoom fit whole data range)
        """
        # Flag is different from the actual one
        if zoom_fit != self.ZoomFit:
            # Save new flag value
            self.ZoomFit = zoom_fit

            # Update button for zoom fit bitmap
            self.Buttons[0].SetBitmap("full_graph" if zoom_fit else "fit_graph")

            # Refresh canvas
            self.RefreshViewer()

    def SubscribeAllDataConsumers(self):
        """
        Function that unsubscribe and remove every item that store values of
        a variable that doesn't exist in PLC anymore
        """
        DebugVariableViewer.SubscribeAllDataConsumers(self)

        # Graph still have data to display
        if not self.ItemsIsEmpty():
            # Reset flag indicating that zoom fit current displayed data range
            self.SetZoomFit(False)

            self.ResetGraphics()

    def Is3DCanvas(self):
        """
        Return if Viewer is a 3D canvas
        @return: True if Viewer is a 3D canvas
        """
        return self.GraphType == GRAPH_ORTHOGONAL and len(self.Items) == 3

    def GetButtons(self):
        """
        Return list of buttons defined in Viewer
        @return: List of buttons
        """
        # Add contextual buttons to default buttons
        return self.Buttons + self.ContextualButtons

    def PopupContextualButtons(self, item, rect, direction=wx.RIGHT):
        """
        Show contextual menu for item aside a label of this item defined
        by the bounding box of label in figure
        @param item: Item for which contextual is shown
        @param rect: Bounding box of label aside which drawing menu
        @param direction: Direction in which buttons must be drawn
        """
        # Return immediately if contextual menu for item is already shown
        if self.ContextualButtonsItem == item:
            return

        # Close already shown contextual menu
        self.DismissContextualButtons()

        # Save item for which contextual menu is shown
        self.ContextualButtonsItem = item

        # If item variable is forced, add button for release variable to
        # contextual menu
        if self.ContextualButtonsItem.IsForced():
            self.ContextualButtons.append(
                GraphButton(0, 0, "release", self.OnReleaseItemButton))

        # Add other buttons to contextual menu
        for bitmap, callback in [
                ("force", self.OnForceItemButton),
                ("export_graph_mini", self.OnExportItemGraphButton),
                ("delete_graph", self.OnRemoveItemButton)]:
            self.ContextualButtons.append(GraphButton(0, 0, bitmap, callback))

        # If buttons are shown at left side or upper side of rect, positions
        # will be set in reverse order
        buttons = self.ContextualButtons[:]
        if direction in [wx.TOP, wx.LEFT]:
            buttons.reverse()

        # Set contextual menu buttons position aside rect depending on
        # direction given
        offset = 0
        for button in buttons:
            w, h = button.GetSize()
            if direction in [wx.LEFT, wx.RIGHT]:
                x = rect.x + (- w - offset
                              if direction == wx.LEFT
                              else rect.width + offset)
                y = rect.y + (rect.height - h) // 2
                offset += w
            else:
                x = rect.x + (rect.width - w) // 2
                y = rect.y + (- h - offset
                              if direction == wx.TOP
                              else rect.height + offset)
                offset += h
            button.SetPosition(x, y)
            button.Show()

        # Refresh canvas
        self.ParentWindow.ForceRefresh()

    def DismissContextualButtons(self):
        """
        Close current shown contextual menu
        """
        # Return immediately if no contextual menu is shown
        if self.ContextualButtonsItem is None:
            return

        # Reset variables corresponding to contextual menu
        self.ContextualButtonsItem = None
        self.ContextualButtons = []

        # Refresh canvas
        self.ParentWindow.ForceRefresh()

    def IsOverContextualButton(self, x, y):
        """
        Return if point is over one contextual button of Viewer
        @param x: X coordinate of point
        @param y: Y coordinate of point
        @return: contextual button where point is over
        """
        for button in self.ContextualButtons:
            if button.HitTest(x, y):
                return button
        return None

    def ExportGraph(self, item=None):
        """
        Export item(s) data to clipboard in CSV format
        @param item: Item from which data to export, all items if None
        (default None)
        """
        self.ParentWindow.CopyDataToClipboard(
            [(item, [entry for entry in item.GetData()])
             for item in (self.Items
                          if item is None
                          else [item])])

    def OnZoomFitButton(self):
        """
        Function called when Viewer Zoom Fit button is pressed
        """
        # Toggle zoom fit flag value
        self.SetZoomFit(not self.ZoomFit)

    def GetOnChangeSizeButton(self, height):
        """
        Function that generate callback function for change Viewer height to
        pre-defined height button
        @param height: Height that change Viewer to
        @return: callback function
        """
        def OnChangeSizeButton():
            self.SetCanvasHeight(height)
        return OnChangeSizeButton

    def OnExportGraphButton(self):
        """
        Function called when Viewer Export button is pressed
        """
        # Export data of every item in Viewer
        self.ExportGraph()

    def OnForceItemButton(self):
        """
        Function called when contextual menu Force button is pressed
        """
        # Open dialog for forcing item variable value
        self.ForceValue(self.ContextualButtonsItem)
        # Close contextual menu
        self.DismissContextualButtons()

    def OnReleaseItemButton(self):
        """
        Function called when contextual menu Release button is pressed
        """
        # Release item variable value
        self.ReleaseValue(self.ContextualButtonsItem)
        # Close contextual menu
        self.DismissContextualButtons()

    def OnExportItemGraphButton(self):
        """
        Function called when contextual menu Export button is pressed
        """
        # Export data of item variable
        self.ExportGraph(self.ContextualButtonsItem)
        # Close contextual menu
        self.DismissContextualButtons()

    def OnRemoveItemButton(self):
        """
        Function called when contextual menu Remove button is pressed
        """
        # Remove item from Viewer
        wx.CallAfter(self.ParentWindow.DeleteValue, self,
                     self.ContextualButtonsItem)
        # Close contextual menu
        self.DismissContextualButtons()

    def HandleCursorMove(self, event):
        """
        Update Cursor position according to mouse position and graph type
        @param event: Mouse event
        """
        start_tick, end_tick = self.ParentWindow.GetRange()
        cursor_tick = None
        items = self.ItemsDict.values()

        # Graph is orthogonal
        if self.GraphType == GRAPH_ORTHOGONAL:
            # Extract items data displayed in canvas figure
            start_tick = max(start_tick, self.GetItemsMinCommonTick())
            end_tick = max(end_tick, start_tick)
            x_data = items[0].GetData(start_tick, end_tick)
            y_data = items[1].GetData(start_tick, end_tick)

            # Search for the nearest point from mouse position
            if len(x_data) > 0 and len(y_data) > 0:
                length = min(len(x_data), len(y_data))
                d = numpy.sqrt((x_data[:length, 1]-event.xdata) ** 2 +
                               (y_data[:length, 1]-event.ydata) ** 2)

                # Set cursor tick to the tick of this point
                cursor_tick = x_data[numpy.argmin(d), 0]

        # Graph is parallel
        else:
            # Extract items tick
            data = items[0].GetData(start_tick, end_tick)

            # Search for point that tick is the nearest from mouse X position
            # and set cursor tick to the tick of this point
            if len(data) > 0:
                cursor_tick = data[numpy.argmin(
                    numpy.abs(data[:, 0] - event.xdata)), 0]

        # Update cursor tick
        if cursor_tick is not None:
            self.ParentWindow.SetCursorTick(cursor_tick)

    def OnCanvasButtonPressed(self, event):
        """
        Function called when a button of mouse is pressed
        @param event: Mouse event
        """
        # Get mouse position, graph Y coordinate is inverted in matplotlib
        # comparing to wx
        _width, height = self.GetSize()
        x, y = event.x, height - event.y

        # Return immediately if mouse is over a button
        if self.IsOverButton(x, y):
            return

        # Mouse was clicked inside graph figure
        if event.inaxes == self.Axes:

            # Find if it was on an item label
            item_idx = None
            # Check every label paired with corresponding item
            for i, t in ([pair for pair in enumerate(self.AxesLabels)] +
                         [pair for pair in enumerate(self.Labels)]):
                # Get label bounding box
                (x0, y0), (x1, y1) = t.get_window_extent().get_points()
                rect = wx.Rect(x0, height - y1, x1 - x0, y1 - y0)
                # Check if mouse was over label
                if rect.InsideXY(x, y):
                    item_idx = i
                    break

            # If an item label have been clicked
            if item_idx is not None:
                # Hide buttons and contextual buttons
                self.ShowButtons(False)
                self.DismissContextualButtons()

                # Start a drag'n drop from mouse position in wx coordinate of
                # parent
                xw, yw = self.GetPosition()
                self.ParentWindow.StartDragNDrop(
                    self, self.ItemsDict.values()[item_idx],
                    x + xw, y + yw,  # Current mouse position
                    x + xw, y + yw)  # Mouse position when button was clicked

            # Don't handle mouse button if canvas is 3D and let matplotlib do
            # the default behavior (rotate 3D axes)
            elif not self.Is3DCanvas():
                # Save mouse position when clicked
                self.MouseStartPos = wx.Point(x, y)

                # Mouse button was left button, start moving cursor
                if event.button == 1:
                    # Save current tick in case a drag'n drop is initiate to
                    # restore it
                    self.StartCursorTick = self.CursorTick

                    self.HandleCursorMove(event)

                # Mouse button is middle button and graph is parallel, start
                # moving graph along X coordinate (tick)
                elif event.button == 2 and self.GraphType == GRAPH_PARALLEL:
                    self.StartCursorTick = self.ParentWindow.GetRange()[0]

        # Mouse was clicked outside graph figure and over resize highlight with
        # left button, start resizing Viewer
        elif event.button == 1 and event.y <= 5:
            self.MouseStartPos = wx.Point(x, y)
            self.CanvasStartSize = height

    def OnCanvasButtonReleased(self, event):
        """
        Function called when a button of mouse is released
        @param event: Mouse event
        """
        # If a drag'n drop is in progress, stop it
        if self.ParentWindow.IsDragging():
            _width, height = self.GetSize()
            xw, yw = self.GetPosition()
            item = self.ParentWindow.DraggingAxesPanel.ItemsDict.values()[0]
            # Give mouse position in wx coordinate of parent
            self.ParentWindow.StopDragNDrop(item.GetVariable(),
                                            xw + event.x, yw + height - event.y)

        else:
            # Reset any move in progress
            self.MouseStartPos = None
            self.CanvasStartSize = None

            # Handle button under mouse if it exist
            _width, height = self.GetSize()
            self.HandleButton(event.x, height - event.y)

    def OnCanvasMotion(self, event):
        """
        Function called when a button of mouse is moved over Viewer
        @param event: Mouse event
        """
        _width, height = self.GetSize()

        # If a drag'n drop is in progress, move canvas dragged
        if self.ParentWindow.IsDragging():
            xw, yw = self.GetPosition()
            # Give mouse position in wx coordinate of parent
            self.ParentWindow.MoveDragNDrop(
                xw + event.x,
                yw + height - event.y)

        # If a Viewer resize is in progress, change Viewer size
        elif event.button == 1 and self.CanvasStartSize is not None:
            _width, height = self.GetSize()
            self.SetCanvasHeight(
                self.CanvasStartSize + height - event.y - self.MouseStartPos.y)

        # If no button is pressed, show or hide contextual buttons or resize
        # highlight
        elif event.button is None:
            # Compute direction for items label according graph type
            if self.GraphType == GRAPH_PARALLEL:  # Graph is parallel
                directions = [wx.RIGHT] * len(self.AxesLabels) + \
                             [wx.LEFT] * len(self.Labels)
            elif len(self.AxesLabels) > 0:         # Graph is orthogonal in 2D
                directions = [wx.RIGHT, wx.TOP,    # Directions for AxesLabels
                              wx.LEFT, wx.BOTTOM]  # Directions for Labels
            else:  # Graph is orthogonal in 3D
                directions = [wx.LEFT] * len(self.Labels)

            # Find if mouse is over an item label
            item_idx = None
            menu_direction = None
            for (i, t), dir in zip(
                    [pair for pair in enumerate(self.AxesLabels)] +
                    [pair for pair in enumerate(self.Labels)],
                    directions):
                # Check every label paired with corresponding item
                (x0, y0), (x1, y1) = t.get_window_extent().get_points()
                rect = wx.Rect(x0, height - y1, x1 - x0, y1 - y0)
                # Check if mouse was over label
                if rect.InsideXY(event.x, height - event.y):
                    item_idx = i
                    menu_direction = dir
                    break

            # If mouse is over an item label,
            if item_idx is not None:
                self.PopupContextualButtons(
                    self.ItemsDict.values()[item_idx],
                    rect, menu_direction)
                return

            # If mouse isn't over a contextual menu, hide the current shown one
            # if it exists
            if self.IsOverContextualButton(event.x, height - event.y) is None:
                self.DismissContextualButtons()

            # Update resize highlight
            if event.y <= 5:
                if self.SetHighlight(HIGHLIGHT_RESIZE):
                    self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
                    self.ParentWindow.ForceRefresh()
            else:
                if self.SetHighlight(HIGHLIGHT_NONE):
                    self.SetCursor(wx.NullCursor)
                    self.ParentWindow.ForceRefresh()

        # Handle buttons if canvas is not 3D
        elif not self.Is3DCanvas():

            # If left button is pressed
            if event.button == 1:

                # Mouse is inside graph figure
                if event.inaxes == self.Axes:

                    # If a cursor move is in progress, update cursor position
                    if self.MouseStartPos is not None:
                        self.HandleCursorMove(event)

                # Mouse is outside graph figure, cursor move is in progress and
                # there is only one item in Viewer, start a drag'n drop
                elif self.MouseStartPos is not None and len(self.Items) == 1:
                    xw, yw = self.GetPosition()
                    self.ParentWindow.SetCursorTick(self.StartCursorTick)
                    self.ParentWindow.StartDragNDrop(
                        self, self.ItemsDict.values()[0],
                        # Current mouse position
                        event.x + xw, height - event.y + yw,
                        # Mouse position when button was clicked
                        self.MouseStartPos.x + xw,
                        self.MouseStartPos.y + yw)

            # If middle button is pressed and moving graph along X coordinate
            # is in progress
            elif (event.button == 2 and
                  self.GraphType == GRAPH_PARALLEL and
                  self.MouseStartPos is not None):
                start_tick, end_tick = self.ParentWindow.GetRange()
                rect = self.GetAxesBoundingBox()

                # Move graph along X coordinate
                self.ParentWindow.SetCanvasPosition(
                    self.StartCursorTick +
                    (self.MouseStartPos.x - event.x) *
                    (end_tick - start_tick) // rect.width)

    def OnCanvasScroll(self, event):
        """
        Function called when a wheel mouse is use in Viewer
        @param event: Mouse event
        """
        # Change X range of graphs if mouse is in canvas figure and ctrl is
        # pressed
        if event.inaxes is not None and event.guiEvent.ControlDown():

            # Calculate position of fixed tick point according to graph type
            # and mouse position
            if self.GraphType == GRAPH_ORTHOGONAL:
                start_tick, end_tick = self.ParentWindow.GetRange()
                tick = (start_tick + end_tick) / 2.
            else:
                tick = event.xdata
            self.ParentWindow.ChangeRange(int(-event.step) // 3, tick)

            # Vetoing event to prevent parent panel to be scrolled
            self.ParentWindow.VetoScrollEvent = True

    def OnLeftDClick(self, event):
        """
        Function called when a left mouse button is double clicked
        @param event: Mouse event
        """
        # Check that double click was done inside figure
        pos = event.GetPosition()
        rect = self.GetAxesBoundingBox()
        if rect.InsideXY(pos.x, pos.y):
            # Reset Cursor tick to value before starting clicking
            self.ParentWindow.SetCursorTick(self.StartCursorTick)
            # Toggle to text Viewer(s)
            self.ParentWindow.ToggleViewerType(self)

        else:
            event.Skip()

    # Cursor tick move for each arrow key
    KEY_CURSOR_INCREMENT = {
        wx.WXK_LEFT: -1,
        wx.WXK_RIGHT: 1,
        wx.WXK_UP: 10,
        wx.WXK_DOWN: -10}

    def OnKeyDown(self, event):
        """
        Function called when key is pressed
        @param event: wx.KeyEvent
        """
        # If cursor is shown and arrow key is pressed, move cursor tick
        if self.CursorTick is not None:
            move = self.KEY_CURSOR_INCREMENT.get(event.GetKeyCode(), None)
            if move is not None:
                self.ParentWindow.MoveCursorTick(move)
        event.Skip()

    def OnLeave(self, event):
        """
        Function called when mouse leave Viewer
        @param event: wx.MouseEvent
        """
        # If Viewer is not resizing, reset resize highlight
        if self.CanvasStartSize is None:
            self.SetHighlight(HIGHLIGHT_NONE)
            self.SetCursor(wx.NullCursor)
            DebugVariableViewer.OnLeave(self, event)
        else:
            event.Skip()

    def GetCanvasMinSize(self):
        """
        Return the minimum size of Viewer so that all items label can be
        displayed
        @return: wx.Size containing Viewer minimum size
        """
        # The minimum height take in account the height of all items, padding
        # inside figure and border around figure
        return wx.Size(200,
                       CANVAS_BORDER[0] + CANVAS_BORDER[1] +
                       2 * CANVAS_PADDING + VALUE_LABEL_HEIGHT * len(self.Items))

    def SetCanvasHeight(self, height):
        """
        Set Viewer size checking that it respects Viewer minimum size
        @param height: Viewer height
        """
        min_width, min_height = self.GetCanvasMinSize()
        height = max(height, min_height)
        self.SetMinSize(wx.Size(min_width, height))
        self.RefreshLabelsPosition(height)
        self.ParentWindow.RefreshGraphicsSizer()

    def GetAxesBoundingBox(self, parent_coordinate=False):
        """
        Return figure bounding box in wx coordinate
        @param parent_coordinate: True if use parent coordinate (default False)
        """
        # Calculate figure bounding box. Y coordinate is inverted in matplotlib
        # figure comparing to wx panel
        width, height = self.GetSize()
        ax, ay, aw, ah = self.figure.gca().get_position().bounds
        bbox = wx.Rect(ax * width, height - (ay + ah) * height - 1,
                       aw * width + 2, ah * height + 1)

        # If parent_coordinate, add Viewer position in parent
        if parent_coordinate:
            xw, yw = self.GetPosition()
            bbox.x += xw
            bbox.y += yw

        return bbox

    def RefreshHighlight(self, x, y):
        """
        Refresh Viewer highlight according to mouse position
        @param x: X coordinate of mouse pointer
        @param y: Y coordinate of mouse pointer
        """
        _width, height = self.GetSize()

        # Mouse is over Viewer figure and graph is not 3D
        bbox = self.GetAxesBoundingBox()
        if bbox.InsideXY(x, y) and not self.Is3DCanvas():
            rect = wx.Rect(bbox.x, bbox.y, bbox.width // 2, bbox.height)
            # Mouse is over Viewer left part of figure
            if rect.InsideXY(x, y):
                self.SetHighlight(HIGHLIGHT_LEFT)

            # Mouse is over Viewer right part of figure
            else:
                self.SetHighlight(HIGHLIGHT_RIGHT)

        # Mouse is over upper part of Viewer
        elif y < height // 2:
            # Viewer is upper one in Debug Variable Panel, show highlight
            if self.ParentWindow.IsViewerFirst(self):
                self.SetHighlight(HIGHLIGHT_BEFORE)

            # Viewer is not the upper one, show highlight in previous one
            # It prevents highlight to move when mouse leave one Viewer to
            # another
            else:
                self.SetHighlight(HIGHLIGHT_NONE)
                self.ParentWindow.HighlightPreviousViewer(self)

        # Mouse is over lower part of Viewer
        else:
            self.SetHighlight(HIGHLIGHT_AFTER)

    def OnAxesMotion(self, event):
        """
        Function overriding default function called when mouse is dragged for
        rotating graph preventing refresh to be called too quickly
        @param event: Mouse event
        """
        if self.Is3DCanvas():
            # Call default function at most 10 times per second
            current_time = gettime()
            if current_time - self.LastMotionTime > REFRESH_PERIOD:
                self.LastMotionTime = current_time
                Axes3D._on_move(self.Axes, event)

    def GetAddTextFunction(self):
        """
        Return function for adding text in figure according to graph type
        @return: Function adding text to figure
        """
        text_func = (self.Axes.text2D if self.Is3DCanvas() else self.Axes.text)

        def AddText(*args, **kwargs):
            args = [0, 0, ""]
            kwargs["transform"] = self.Axes.transAxes
            return text_func(*args, **kwargs)
        return AddText

    def SetAxesColor(self, color):
        self.Axes.set_prop_cycle(cycler('color', color))

    def ResetGraphics(self):
        """
        Reset figure and graphical elements displayed in it
        Called any time list of items or graph type change
        """
        # Clear figure from any axes defined
        self.Figure.clear()

        # Add 3D projection if graph is in 3D
        if self.Is3DCanvas():
            self.Axes = self.Figure.gca(projection='3d')
            self.SetAxesColor(['b'])

            # Override function to prevent too much refresh when graph is
            # rotated
            self.LastMotionTime = gettime()
            setattr(self.Axes, "_on_move", self.OnAxesMotion)

            # Init graph mouse event so that graph can be rotated
            self.Axes.mouse_init()

            # Set size of Z axis labels
            self.Axes.tick_params(axis='z', labelsize='small')

        else:
            self.Axes = self.Figure.gca()
            self.SetAxesColor(COLOR_CYCLE)

        # Set size of X and Y axis labels
        self.Axes.tick_params(axis='x', labelsize='small')
        self.Axes.tick_params(axis='y', labelsize='small')

        # Init variables storing graphical elements added to figure
        self.Plots = []       # List of curves
        self.VLine = None     # Vertical line for cursor
        self.HLine = None     # Horizontal line for cursor (only orthogonal 2D)
        self.AxesLabels = []  # List of items variable path text label
        self.Labels = []      # List of items text label

        # Get function to add a text in figure according to graph type
        add_text_func = self.GetAddTextFunction()

        # Graph type is parallel or orthogonal in 3D
        if self.GraphType == GRAPH_PARALLEL or self.Is3DCanvas():
            num_item = len(self.Items)
            for idx in xrange(num_item):

                # Get color from color cycle (black if only one item)
                color = ('k' if num_item == 1 else
                         COLOR_CYCLE[idx % len(COLOR_CYCLE)])

                # In 3D graph items variable label are not displayed as text
                # in figure, but as axis title
                if not self.Is3DCanvas():
                    # Items variable labels are in figure upper left corner
                    self.AxesLabels.append(
                        add_text_func(size='small', color=color,
                                      verticalalignment='top'))

                # Items variable labels are in figure lower right corner
                self.Labels.append(
                    add_text_func(size='large', color=color,
                                  horizontalalignment='right'))

        # Graph type is orthogonal in 2D
        else:
            # X coordinate labels are in figure lower side
            self.AxesLabels.append(add_text_func(size='small'))
            self.Labels.append(
                add_text_func(size='large',
                              horizontalalignment='right'))

            # Y coordinate labels are vertical and in figure left side
            self.AxesLabels.append(
                add_text_func(size='small', rotation='vertical',
                              verticalalignment='bottom'))
            self.Labels.append(
                add_text_func(size='large', rotation='vertical',
                              verticalalignment='top'))

        # Refresh position of labels according to Viewer size
        _width, height = self.GetSize()
        self.RefreshLabelsPosition(height)

    def RefreshLabelsPosition(self, height):
        """
        Function called when mouse leave Viewer
        @param event: wx.MouseEvent
        """
        # Figure position like text position in figure are expressed is ratio
        # canvas size and figure size. As we want that border around figure and
        # text position in figure don't change when canvas size change, we
        # expressed border and text position in pixel on screen and apply the
        # ratio calculated hereafter to get border and text position in
        # matplotlib coordinate
        canvas_ratio = 1. / height  # Divide by canvas height in pixel
        graph_ratio = 1. / (
            (1.0 - (CANVAS_BORDER[0] + CANVAS_BORDER[1]) * canvas_ratio) *
            height)             # Divide by figure height in pixel

        # Update position of figure (keeping up and bottom border the same
        # size)
        self.Figure.subplotpars.update(
            top=1.0 - CANVAS_BORDER[1] * canvas_ratio,
            bottom=CANVAS_BORDER[0] * canvas_ratio)

        # Update position of items labels
        if self.GraphType == GRAPH_PARALLEL or self.Is3DCanvas():
            num_item = len(self.Items)
            for idx in xrange(num_item):

                # In 3D graph items variable label are not displayed
                if not self.Is3DCanvas():
                    # Items variable labels are in figure upper left corner
                    self.AxesLabels[idx].set_position(
                        (0.05,
                         1.0 - (CANVAS_PADDING +
                                AXES_LABEL_HEIGHT * idx) * graph_ratio))

                # Items variable labels are in figure lower right corner
                self.Labels[idx].set_position(
                    (0.95,
                     CANVAS_PADDING * graph_ratio +
                     (num_item - idx - 1) * VALUE_LABEL_HEIGHT * graph_ratio))
        else:
            # X coordinate labels are in figure lower side
            self.AxesLabels[0].set_position(
                (0.1, CANVAS_PADDING * graph_ratio))
            self.Labels[0].set_position(
                (0.95, CANVAS_PADDING * graph_ratio))

            # Y coordinate labels are vertical and in figure left side
            self.AxesLabels[1].set_position(
                (0.05, 2 * CANVAS_PADDING * graph_ratio))
            self.Labels[1].set_position(
                (0.05, 1.0 - CANVAS_PADDING * graph_ratio))

        # Update subplots
        self.Figure.subplots_adjust()

    def RefreshViewer(self, refresh_graphics=True):
        """
        Function called to refresh displayed by matplotlib canvas
        @param refresh_graphics: Flag indicating that graphs have to be
        refreshed (False: only label values have to be refreshed)
        """
        # Refresh graphs if needed
        if refresh_graphics:
            # Get tick range of values to display
            start_tick, end_tick = self.ParentWindow.GetRange()

            # Graph is parallel
            if self.GraphType == GRAPH_PARALLEL:
                # Init list of data range for each variable displayed
                ranges = []

                # Get data and range for each variable displayed
                for idx, item in enumerate(self.Items):
                    data, min_value, max_value = item.GetDataAndValueRange(
                        start_tick, end_tick, not self.ZoomFit)

                    # Check that data is not empty
                    if data is not None:
                        # Add variable range to list of variable data range
                        ranges.append((min_value, max_value))

                        # Add plot to canvas if not yet created
                        if len(self.Plots) <= idx:
                            self.Plots.append(
                                self.Axes.plot(data[:, 0], data[:, 1])[0])

                        # Set data to already created plot in canvas
                        else:
                            self.Plots[idx].set_data(data[:, 0], data[:, 1])

                # Get X and Y axis ranges
                x_min, x_max = start_tick, end_tick
                y_min, y_max = merge_ranges(ranges)

                # Display cursor in canvas if a cursor tick is defined and it is
                # include in values tick range
                if self.CursorTick is not None and \
                   start_tick <= self.CursorTick <= end_tick:

                    # Define a vertical line to display cursor position if no
                    # line is already defined
                    if self.VLine is None:
                        self.VLine = self.Axes.axvline(self.CursorTick,
                                                       color=CURSOR_COLOR)

                    # Set value of vertical line if already defined
                    else:
                        self.VLine.set_xdata((self.CursorTick, self.CursorTick))
                    self.VLine.set_visible(True)

                # Hide vertical line if cursor tick is not defined or reset
                elif self.VLine is not None:
                    self.VLine.set_visible(False)

            # Graph is orthogonal
            else:
                # Update tick range, removing ticks that don't have a value for
                # each variable
                start_tick = max(start_tick, self.GetItemsMinCommonTick())
                end_tick = max(end_tick, start_tick)
                items = self.ItemsDict.values()

                # Get data and range for first variable (X coordinate)
                x_data, x_min, x_max = items[0].GetDataAndValueRange(
                    start_tick, end_tick, not self.ZoomFit)

                # Get data and range for second variable (Y coordinate)
                y_data, y_min, y_max = items[1].GetDataAndValueRange(
                    start_tick, end_tick, not self.ZoomFit)

                # Normalize X and Y coordinates value range
                x_min, x_max = merge_ranges([(x_min, x_max)])
                y_min, y_max = merge_ranges([(y_min, y_max)])

                # Get X and Y coordinates for cursor if cursor tick is defined
                if self.CursorTick is not None:
                    x_cursor, _x_forced = items[0].GetValue(
                        self.CursorTick, raw=True)
                    y_cursor, _y_forced = items[1].GetValue(
                        self.CursorTick, raw=True)

                # Get common data length so that each value has an x and y
                # coordinate
                length = (min(len(x_data), len(y_data))
                          if x_data is not None and y_data is not None
                          else 0)

                # Graph is orthogonal 2D
                if len(self.Items) < 3:

                    # Check that x and y data are not empty
                    if x_data is not None and y_data is not None:

                        # Add plot to canvas if not yet created
                        if len(self.Plots) == 0:
                            self.Plots.append(
                                self.Axes.plot(x_data[:, 1][:length],
                                               y_data[:, 1][:length])[0])

                        # Set data to already created plot in canvas
                        else:
                            self.Plots[0].set_data(
                                x_data[:, 1][:length],
                                y_data[:, 1][:length])

                    # Display cursor in canvas if a cursor tick is defined and it is
                    # include in values tick range
                    if self.CursorTick is not None and \
                       start_tick <= self.CursorTick <= end_tick:

                        # Define a vertical line to display cursor x coordinate
                        # if no line is already defined
                        if self.VLine is None:
                            self.VLine = self.Axes.axvline(x_cursor,
                                                           color=CURSOR_COLOR)
                        # Set value of vertical line if already defined
                        else:
                            self.VLine.set_xdata((x_cursor, x_cursor))

                        # Define a horizontal line to display cursor y
                        # coordinate if no line is already defined
                        if self.HLine is None:
                            self.HLine = self.Axes.axhline(y_cursor,
                                                           color=CURSOR_COLOR)
                        # Set value of horizontal line if already defined
                        else:
                            self.HLine.set_ydata((y_cursor, y_cursor))

                        self.VLine.set_visible(True)
                        self.HLine.set_visible(True)

                    # Hide vertical and horizontal line if cursor tick is not
                    # defined or reset
                    else:
                        if self.VLine is not None:
                            self.VLine.set_visible(False)
                        if self.HLine is not None:
                            self.HLine.set_visible(False)

                # Graph is orthogonal 3D
                else:
                    # Remove all plots already defined in 3D canvas
                    while len(self.Axes.lines) > 0:
                        self.Axes.lines.pop()

                    # Get data and range for third variable (Z coordinate)
                    z_data, z_min, z_max = items[2].GetDataAndValueRange(
                        start_tick, end_tick, not self.ZoomFit)

                    # Normalize Z coordinate value range
                    z_min, z_max = merge_ranges([(z_min, z_max)])

                    # Check that x, y and z data are not empty
                    if x_data is not None and \
                       y_data is not None and \
                       z_data is not None:

                        # Get common data length so that each value has an x, y
                        # and z coordinate
                        length = min(length, len(z_data))

                        # Add plot to canvas
                        self.Axes.plot(x_data[:, 1][:length],
                                       y_data[:, 1][:length],
                                       zs=z_data[:, 1][:length])

                    # Display cursor in canvas if a cursor tick is defined and
                    # it is include in values tick range
                    if self.CursorTick is not None and \
                       start_tick <= self.CursorTick <= end_tick:

                        # Get Z coordinate for cursor
                        z_cursor, _z_forced = items[2].GetValue(
                            self.CursorTick, raw=True)

                        # Add 3 lines parallel to x, y and z axis to display
                        # cursor position in 3D
                        for kwargs in [{"xs": numpy.array([x_min, x_max])},
                                       {"ys": numpy.array([y_min, y_max])},
                                       {"zs": numpy.array([z_min, z_max])}]:
                            for param, value in [
                                    ("xs", numpy.array([x_cursor, x_cursor])),
                                    ("ys", numpy.array([y_cursor, y_cursor])),
                                    ("zs", numpy.array([z_cursor, z_cursor]))]:
                                kwargs.setdefault(param, value)
                            kwargs["color"] = CURSOR_COLOR
                            self.Axes.plot(**kwargs)

                    # Set Z axis limits
                    self.Axes.set_zlim(z_min, z_max)

            # Set X and Y axis limits
            self.Axes.set_xlim(x_min, x_max)
            self.Axes.set_ylim(y_min, y_max)

        # Get value and forced flag for each variable displayed in graph
        # If cursor tick is not defined get value and flag of last received
        # or get value and flag of variable at cursor tick
        args = [(
            item.GetValue(self.CursorTick)
            if self.CursorTick is not None
            else (item.GetValue(), item.IsForced())) for item in self.Items]
        values, forced = zip(*args)

        # Get path of each variable displayed simplified using panel variable
        # name mask
        labels = [item.GetVariable(self.ParentWindow.GetVariableNameMask())
                  for item in self.Items]

        # Get style for each variable according to
        styles = map(lambda x: {True: 'italic', False: 'normal'}[x], forced)

        # Graph is orthogonal 3D, set variables path as 3D axis label
        if self.Is3DCanvas():
            for idx, label_func in enumerate([self.Axes.set_xlabel,
                                              self.Axes.set_ylabel,
                                              self.Axes.set_zlabel]):
                label_func(labels[idx], fontdict={'size': 'small',
                                                  'color': COLOR_CYCLE[idx]})

        # Graph is not orthogonal 3D, set variables path in axes labels
        else:
            for label, text in zip(self.AxesLabels, labels):
                label.set_text(text)

        # Set value label text and style according to value and forced flag for
        # each variable displayed
        for label, value, style in zip(self.Labels, values, styles):
            label.set_text(value)
            label.set_style(style)

        # Refresh figure
        self.draw()

    def draw(self, drawDC=None):
        """
        Render the figure.
        """
        # Render figure using agg
        FigureCanvasAgg.draw(self)

        # Get bitmap of figure rendered
        self.bitmap = _convert_agg_to_wx_bitmap(self.get_renderer(), None)
        if wx.VERSION < (3, 0, 0):
            self.bitmap.UseAlpha()

        # Create DC for rendering graphics in bitmap
        destDC = wx.MemoryDC()
        destDC.SelectObject(self.bitmap)

        # Get Graphics Context for DC, for anti-aliased and transparent
        # rendering
        destGC = wx.GCDC(destDC)

        destGC.BeginDrawing()

        # Get canvas size and figure bounding box in canvas
        width, height = self.GetSize()
        bbox = self.GetAxesBoundingBox()

        # If highlight to display is resize, draw thick grey line at bottom
        # side of canvas
        if self.Highlight == HIGHLIGHT_RESIZE:
            destGC.SetPen(HIGHLIGHT['RESIZE_PEN'])
            destGC.SetBrush(HIGHLIGHT['RESIZE_BRUSH'])
            destGC.DrawRectangle(0, height - 5, width, 5)

        # If highlight to display is merging graph, draw 50% transparent blue
        # rectangle on left or right part of figure depending on highlight type
        elif self.Highlight in [HIGHLIGHT_LEFT, HIGHLIGHT_RIGHT]:
            destGC.SetPen(HIGHLIGHT['DROP_PEN'])
            destGC.SetBrush(HIGHLIGHT['DROP_BRUSH'])

            x_offset = (bbox.width // 2
                        if self.Highlight == HIGHLIGHT_RIGHT
                        else 0)
            destGC.DrawRectangle(bbox.x + x_offset, bbox.y,
                                 bbox.width // 2, bbox.height)

        # Draw other Viewer common elements
        self.DrawCommonElements(destGC, self.GetButtons())

        destGC.EndDrawing()

        self._isDrawn = True
        self.gui_repaint(drawDC=drawDC)
