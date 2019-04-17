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
from functools import reduce
import numpy
import os

import wx
import wx.lib.buttons


# pylint: disable=wrong-import-position
import matplotlib
matplotlib.use('WX')   # noqa
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import _convert_agg_to_wx_bitmap

from editors.DebugViewer import DebugViewer
from util.BitmapLibrary import GetBitmap

from controls.DebugVariablePanel.DebugVariableItem import DebugVariableItem
from controls.DebugVariablePanel.DebugVariableTextViewer import DebugVariableTextViewer
from controls.DebugVariablePanel.DebugVariableGraphicViewer import *


MILLISECOND = 1000000        # Number of nanosecond in a millisecond
SECOND = 1000 * MILLISECOND  # Number of nanosecond in a second
MINUTE = 60 * SECOND         # Number of nanosecond in a minute
HOUR = 60 * MINUTE           # Number of nanosecond in a hour
DAY = 24 * HOUR              # Number of nanosecond in a day

# Scrollbar increment in pixel
SCROLLBAR_UNIT = 10


def compute_mask(x, y):
    return [(xp if xp == yp else "*")
            for xp, yp in zip(x, y)]


def NextTick(variables):
    next_tick = None
    for _item, data in variables:
        if len(data) == 0:
            continue

        next_tick = (data[0][0]
                     if next_tick is None
                     else min(next_tick, data[0][0]))

    return next_tick

# -------------------------------------------------------------------------------
#                    Debug Variable Graphic Panel Drop Target
# -------------------------------------------------------------------------------


class DebugVariableDropTarget(wx.TextDropTarget):
    """
    Class that implements a custom drop target class for Debug Variable Graphic
    Panel
    """

    def __init__(self, window):
        """
        Constructor
        @param window: Reference to the Debug Variable Panel
        """
        wx.TextDropTarget.__init__(self)
        self.ParentWindow = window

    def __del__(self):
        """
        Destructor
        """
        # Remove reference to Debug Variable Panel
        self.ParentWindow = None

    def OnDragOver(self, x, y, d):
        """
        Function called when mouse is dragged over Drop Target
        @param x: X coordinate of mouse pointer
        @param y: Y coordinate of mouse pointer
        @param d: Suggested default for return value
        """
        # Signal Debug Variable Panel to refresh highlight giving mouse position
        self.ParentWindow.RefreshHighlight(x, y)
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

            # Drag'n Drop is an internal is an internal move inside Debug
            # Variable Panel
            if len(values) > 2 and values[2] == "move":
                self.ParentWindow.MoveValue(values[0])

            # Drag'n Drop was initiated by another control of Beremiz
            else:
                self.ParentWindow.InsertValue(values[0], force=True)

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


class DebugVariablePanel(wx.Panel, DebugViewer):
    """
    Class that implements a Viewer that display variable values as a graphs
    """

    def __init__(self, parent, producer, window):
        """
        Constructor
        @param parent: Reference to the parent wx.Window
        @param producer: Object receiving debug value and dispatching them to
        consumers
        @param window: Reference to Beremiz frame
        """
        wx.Panel.__init__(self, parent, style=wx.SP_3D | wx.TAB_TRAVERSAL)

        # List of values possible for graph range
        # Format is [(time_in_plain_text, value_in_nanosecond),...]
        self.RANGE_VALUES = [(_("%dms") % i, i * MILLISECOND) for i in (10, 20, 50, 100, 200, 500)] + \
                            [(_("%ds") % i, i * SECOND) for i in (1, 2, 5, 10, 20, 30)] + \
                            [(_("%dm") % i, i * MINUTE) for i in (1, 2, 5, 10, 20, 30)] + \
                            [(_("%dh") % i, i * HOUR) for i in (1, 2, 3, 6, 12, 24)]

        # Save Reference to Beremiz frame
        self.ParentWindow = window

        # Variable storing flag indicating that variable displayed in table
        # received new value and then table need to be refreshed
        self.HasNewData = False

        # Variable storing flag indicating that refresh has been forced, and
        # that next time refresh is possible, it will be done even if no new
        # data is available
        self.Force = False

        self.SetBackgroundColour(wx.WHITE)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.Ticks = numpy.array([])  # List of tick received
        self.StartTick = 0            # Tick starting range of data displayed
        self.Fixed = False            # Flag that range of data is fixed
        self.CursorTick = None        # Tick of cursor for displaying values

        self.DraggingAxesPanel = None
        self.DraggingAxesBoundingBox = None
        self.DraggingAxesMousePos = None
        self.VetoScrollEvent = False

        self.VariableNameMask = []

        self.GraphicPanels = []

        graphics_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(graphics_button_sizer, border=5, flag=wx.GROW | wx.ALL)

        range_label = wx.StaticText(self, label=_('Range:'))
        graphics_button_sizer.AddWindow(range_label, flag=wx.ALIGN_CENTER_VERTICAL)

        self.CanvasRange = wx.ComboBox(self, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnRangeChanged, self.CanvasRange)
        graphics_button_sizer.AddWindow(self.CanvasRange, 1,
                                        border=5,
                                        flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)

        self.CanvasRange.Clear()
        default_range_idx = 0
        for idx, (text, _value) in enumerate(self.RANGE_VALUES):
            self.CanvasRange.Append(text)
            if _value == 1000000000:
                default_range_idx = idx
        self.CanvasRange.SetSelection(default_range_idx)

        for name, bitmap, help in [
                ("CurrentButton",     "current",      _("Go to current value")),
                ("ExportGraphButton", "export_graph", _("Export graph values to clipboard"))]:
            button = wx.lib.buttons.GenBitmapButton(
                self, bitmap=GetBitmap(bitmap),
                size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            self.Bind(wx.EVT_BUTTON, getattr(self, "On" + name), button)
            graphics_button_sizer.AddWindow(button, border=5, flag=wx.LEFT)

        self.CanvasPosition = wx.ScrollBar(
            self, size=wx.Size(0, 16), style=wx.SB_HORIZONTAL)
        self.CanvasPosition.Bind(wx.EVT_SCROLL_THUMBTRACK,
                                 self.OnPositionChanging, self.CanvasPosition)
        self.CanvasPosition.Bind(wx.EVT_SCROLL_LINEUP,
                                 self.OnPositionChanging, self.CanvasPosition)
        self.CanvasPosition.Bind(wx.EVT_SCROLL_LINEDOWN,
                                 self.OnPositionChanging, self.CanvasPosition)
        self.CanvasPosition.Bind(wx.EVT_SCROLL_PAGEUP,
                                 self.OnPositionChanging, self.CanvasPosition)
        self.CanvasPosition.Bind(wx.EVT_SCROLL_PAGEDOWN,
                                 self.OnPositionChanging, self.CanvasPosition)
        main_sizer.AddWindow(self.CanvasPosition, border=5, flag=wx.GROW | wx.LEFT | wx.RIGHT | wx.BOTTOM)

        self.TickSizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(self.TickSizer, border=5, flag=wx.ALL | wx.GROW)

        self.TickLabel = wx.StaticText(self)
        self.TickSizer.AddWindow(self.TickLabel, border=5, flag=wx.RIGHT)

        self.MaskLabel = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_CENTER | wx.NO_BORDER)
        self.TickSizer.AddWindow(self.MaskLabel, 1, border=5, flag=wx.RIGHT | wx.GROW)

        self.TickTimeLabel = wx.StaticText(self)
        self.TickSizer.AddWindow(self.TickTimeLabel)

        self.GraphicsWindow = wx.ScrolledWindow(self, style=wx.HSCROLL | wx.VSCROLL)
        self.GraphicsWindow.SetBackgroundColour(wx.WHITE)
        self.GraphicsWindow.SetDropTarget(DebugVariableDropTarget(self))
        self.GraphicsWindow.Bind(wx.EVT_ERASE_BACKGROUND, self.OnGraphicsWindowEraseBackground)
        self.GraphicsWindow.Bind(wx.EVT_PAINT, self.OnGraphicsWindowPaint)
        self.GraphicsWindow.Bind(wx.EVT_SIZE, self.OnGraphicsWindowResize)
        self.GraphicsWindow.Bind(wx.EVT_MOUSEWHEEL, self.OnGraphicsWindowMouseWheel)

        main_sizer.AddWindow(self.GraphicsWindow, 1, flag=wx.GROW)

        self.GraphicsSizer = wx.BoxSizer(wx.VERTICAL)
        self.GraphicsWindow.SetSizer(self.GraphicsSizer)

        DebugViewer.__init__(self, producer, True)

        self.SetSizer(main_sizer)
        self.SetTickTime()

    def SetTickTime(self, ticktime=0):
        """
        Set Ticktime for calculate data range according to time range selected
        @param ticktime: Ticktime to apply to range (default: 0)
        """
        # Save ticktime
        self.Ticktime = ticktime

        # Set ticktime to millisecond if undefined
        if self.Ticktime == 0:
            self.Ticktime = MILLISECOND

        # Calculate range to apply to data
        self.CurrentRange = self.RANGE_VALUES[
            self.CanvasRange.GetSelection()][1] // self.Ticktime

    def SetDataProducer(self, producer):
        """
        Set Data Producer
        @param producer: Data Producer
        """
        DebugViewer.SetDataProducer(self, producer)

        # Set ticktime if data producer is available
        if self.DataProducer is not None:
            self.SetTickTime(self.DataProducer.GetTicktime())

    def RefreshNewData(self):
        """
        Called to refresh Panel according to values received by variables
        Can receive any parameters (not used here)
        """
        # Refresh graphs if new data is available or refresh is forced
        if self.HasNewData or self.Force:
            self.HasNewData = False
            self.RefreshView()

        DebugViewer.RefreshNewData(self)

    def NewDataAvailable(self, ticks):
        """
        Called by DataProducer for each tick captured or by panel to refresh
        graphs
        @param tick: PLC tick captured
        All other parameters are passed to refresh function
        """
        # If tick given
        if ticks is not None:
            tick = ticks[-1]

            # Save tick as start tick for range if data is still empty
            if len(self.Ticks) == 0:
                self.StartTick = ticks[0]

            # Add tick to list of ticks received
            self.Ticks = numpy.append(self.Ticks, ticks)

            # Update start tick for range if range follow ticks received
            if not self.Fixed or tick < self.StartTick + self.CurrentRange:
                self.StartTick = max(self.StartTick, tick - self.CurrentRange)

            # Force refresh if graph is fixed because range of data received
            # is too small to fill data range selected
            if self.Fixed and \
               self.Ticks[-1] - self.Ticks[0] < self.CurrentRange:
                self.Force = True

            self.HasNewData = False
            self.RefreshView()

        else:
            DebugViewer.NewDataAvailable(self, ticks)

    def ForceRefresh(self):
        """
        Called to force refresh of graphs
        """
        self.Force = True
        wx.CallAfter(self.NewDataAvailable, None)

    def SetCursorTick(self, cursor_tick):
        """
        Set Cursor for displaying values of items at a tick given
        @param cursor_tick: Tick of cursor
        """
        # Save cursor tick
        self.CursorTick = cursor_tick
        self.Fixed = cursor_tick is not None
        self.UpdateCursorTick()

    def MoveCursorTick(self, move):
        if self.CursorTick is not None:
            cursor_tick = max(self.Ticks[0],
                              min(self.CursorTick + move, self.Ticks[-1]))
            cursor_tick_idx = numpy.argmin(numpy.abs(self.Ticks - cursor_tick))
            if self.Ticks[cursor_tick_idx] == self.CursorTick:
                cursor_tick_idx = max(0,
                                      min(cursor_tick_idx + abs(move) // move,
                                          len(self.Ticks) - 1))
            self.CursorTick = self.Ticks[cursor_tick_idx]
            self.StartTick = max(
                self.Ticks[numpy.argmin(
                    numpy.abs(self.Ticks - self.CursorTick + self.CurrentRange))],
                min(self.StartTick, self.CursorTick))
            self.RefreshCanvasPosition()
            self.UpdateCursorTick()

    def ResetCursorTick(self):
        self.CursorTick = None
        self.Fixed = False
        self.UpdateCursorTick()

    def UpdateCursorTick(self):
        for panel in self.GraphicPanels:
            if isinstance(panel, DebugVariableGraphicViewer):
                panel.SetCursorTick(self.CursorTick)
        self.ForceRefresh()

    def StartDragNDrop(self, panel, item, x_mouse, y_mouse, x_mouse_start, y_mouse_start):
        if len(panel.GetItems()) > 1:
            self.DraggingAxesPanel = DebugVariableGraphicViewer(self.GraphicsWindow, self, [item], GRAPH_PARALLEL)
            self.DraggingAxesPanel.SetCursorTick(self.CursorTick)
            width, height = panel.GetSize()
            self.DraggingAxesPanel.SetSize(wx.Size(width, height))
            self.DraggingAxesPanel.ResetGraphics()
            self.DraggingAxesPanel.SetPosition(wx.Point(0, -height))
        else:
            self.DraggingAxesPanel = panel
        self.DraggingAxesBoundingBox = panel.GetAxesBoundingBox(parent_coordinate=True)
        self.DraggingAxesMousePos = wx.Point(
            x_mouse_start - self.DraggingAxesBoundingBox.x,
            y_mouse_start - self.DraggingAxesBoundingBox.y)
        self.MoveDragNDrop(x_mouse, y_mouse)

    def MoveDragNDrop(self, x_mouse, y_mouse):
        self.DraggingAxesBoundingBox.x = x_mouse - self.DraggingAxesMousePos.x
        self.DraggingAxesBoundingBox.y = y_mouse - self.DraggingAxesMousePos.y
        self.RefreshHighlight(x_mouse, y_mouse)

    def RefreshHighlight(self, x_mouse, y_mouse):
        for idx, panel in enumerate(self.GraphicPanels):
            x, y = panel.GetPosition()
            width, height = panel.GetSize()
            rect = wx.Rect(x, y, width, height)
            if rect.InsideXY(x_mouse, y_mouse) or \
               idx == 0 and y_mouse < 0 or \
               idx == len(self.GraphicPanels) - 1 and y_mouse > panel.GetPosition()[1]:
                panel.RefreshHighlight(x_mouse - x, y_mouse - y)
            else:
                panel.SetHighlight(HIGHLIGHT_NONE)
        if wx.Platform == "__WXMSW__":
            self.RefreshView()
        else:
            self.ForceRefresh()

    def ResetHighlight(self):
        for panel in self.GraphicPanels:
            panel.SetHighlight(HIGHLIGHT_NONE)
        if wx.Platform == "__WXMSW__":
            self.RefreshView()
        else:
            self.ForceRefresh()

    def IsDragging(self):
        return self.DraggingAxesPanel is not None

    def GetDraggingAxesClippingRegion(self, panel):
        x, y = panel.GetPosition()
        width, height = panel.GetSize()
        bbox = wx.Rect(x, y, width, height)
        bbox = bbox.Intersect(self.DraggingAxesBoundingBox)
        bbox.x -= x
        bbox.y -= y
        return bbox

    def GetDraggingAxesPosition(self, panel):
        x, y = panel.GetPosition()
        return wx.Point(self.DraggingAxesBoundingBox.x - x,
                        self.DraggingAxesBoundingBox.y - y)

    def StopDragNDrop(self, variable, x_mouse, y_mouse):
        if self.DraggingAxesPanel not in self.GraphicPanels:
            self.DraggingAxesPanel.Destroy()
        self.DraggingAxesPanel = None
        self.DraggingAxesBoundingBox = None
        self.DraggingAxesMousePos = None
        for idx, panel in enumerate(self.GraphicPanels):
            panel.SetHighlight(HIGHLIGHT_NONE)
            xw, yw = panel.GetPosition()
            width, height = panel.GetSize()
            bbox = wx.Rect(xw, yw, width, height)
            if bbox.InsideXY(x_mouse, y_mouse):
                panel.ShowButtons(True)
                merge_type = GRAPH_PARALLEL
                if isinstance(panel, DebugVariableTextViewer) or panel.Is3DCanvas():
                    if y_mouse > yw + height // 2:
                        idx += 1
                    wx.CallAfter(self.MoveValue, variable, idx, True)
                else:
                    rect = panel.GetAxesBoundingBox(True)
                    if rect.InsideXY(x_mouse, y_mouse):
                        merge_rect = wx.Rect(rect.x, rect.y, rect.width // 2, rect.height)
                        if merge_rect.InsideXY(x_mouse, y_mouse):
                            merge_type = GRAPH_ORTHOGONAL
                        wx.CallAfter(self.MergeGraphs, variable, idx, merge_type, force=True)
                    else:
                        if y_mouse > yw + height // 2:
                            idx += 1
                        wx.CallAfter(self.MoveValue, variable, idx, True)
                self.ForceRefresh()
                return
        width, height = self.GraphicsWindow.GetVirtualSize()
        rect = wx.Rect(0, 0, width, height)
        if rect.InsideXY(x_mouse, y_mouse):
            wx.CallAfter(self.MoveValue, variable, len(self.GraphicPanels), True)
        self.ForceRefresh()

    def RefreshGraphicsSizer(self):
        self.GraphicsSizer.Clear()

        for panel in self.GraphicPanels:
            self.GraphicsSizer.AddWindow(panel, flag=wx.GROW)

        self.GraphicsSizer.Layout()
        self.RefreshGraphicsWindowScrollbars()

    def RefreshView(self):
        """Triggers EVT_PAINT event to refresh UI"""
        if os.name == 'nt':
            self.DrawView()
        else:
            self.Refresh()

    def DrawView(self):
        """
        Redraw elements.
        Method is used by EVT_PAINT handler.
        """
        if os.name == 'nt':
            width, height = self.GraphicsWindow.GetVirtualSize()
            bitmap = wx.EmptyBitmap(width, height)
            dc = wx.BufferedDC(wx.ClientDC(self.GraphicsWindow), bitmap)
            dc.Clear()
            dc.BeginDrawing()
            if self.DraggingAxesPanel is not None:
                destBBox = self.DraggingAxesBoundingBox
                srcBBox = self.DraggingAxesPanel.GetAxesBoundingBox()
                
                srcBmp = _convert_agg_to_wx_bitmap(self.DraggingAxesPanel.get_renderer(), None)
                srcDC = wx.MemoryDC()
                srcDC.SelectObject(srcBmp)
                    
                dc.Blit(destBBox.x, destBBox.y, 
                        int(destBBox.width), int(destBBox.height), 
                        srcDC, srcBBox.x, srcBBox.y)
            dc.EndDrawing()
        
        self.RefreshCanvasPosition()

        if not self.Fixed or self.Force:
            self.Force = False
            refresh_graphics = True
        else:
            refresh_graphics = False

        if self.DraggingAxesPanel is not None and self.DraggingAxesPanel not in self.GraphicPanels:
            self.DraggingAxesPanel.RefreshViewer(refresh_graphics)
        for panel in self.GraphicPanels:
            if isinstance(panel, DebugVariableGraphicViewer):
                panel.RefreshViewer(refresh_graphics)
            else:
                panel.RefreshViewer()

        if self.CursorTick is not None:
            tick = self.CursorTick
        elif len(self.Ticks) > 0:
            tick = self.Ticks[-1]
        else:
            tick = None
        if tick is not None:
            self.TickLabel.SetLabel(label=_("Tick: %d") % tick)
            tick_duration = int(tick * self.Ticktime)
            not_null = False
            duration = ""
            for value, format in [(tick_duration // DAY, _("%dd")),
                                  ((tick_duration % DAY) // HOUR, _("%dh")),
                                  ((tick_duration % HOUR) // MINUTE, _("%dm")),
                                  ((tick_duration % MINUTE) // SECOND, _("%ds"))]:

                if value > 0 or not_null:
                    duration += format % value
                    not_null = True

            duration += _("%03gms") % ((tick_duration % SECOND) / MILLISECOND)
            self.TickTimeLabel.SetLabel("t: %s" % duration)
        else:
            self.TickLabel.SetLabel("")
            self.TickTimeLabel.SetLabel("")
        self.TickSizer.Layout()

    def SubscribeAllDataConsumers(self):
        DebugViewer.SubscribeAllDataConsumers(self)

        if self.DataProducer is not None:
            if self.DataProducer is not None:
                self.SetTickTime(self.DataProducer.GetTicktime())

        self.ResetCursorTick()

        for panel in self.GraphicPanels[:]:
            panel.SubscribeAllDataConsumers()
            if panel.ItemsIsEmpty():
                if panel.HasCapture():
                    panel.ReleaseMouse()
                self.GraphicPanels.remove(panel)
                panel.Destroy()

        self.ResetVariableNameMask()
        self.RefreshGraphicsSizer()
        self.ForceRefresh()

    def ResetView(self):
        self.UnsubscribeAllDataConsumers()

        self.Fixed = False
        for panel in self.GraphicPanels:
            panel.Destroy()
        self.GraphicPanels = []
        self.ResetVariableNameMask()
        self.RefreshGraphicsSizer()

    def SetCanvasPosition(self, tick):
        tick = max(self.Ticks[0], min(tick, self.Ticks[-1] - self.CurrentRange))
        self.StartTick = self.Ticks[numpy.argmin(numpy.abs(self.Ticks - tick))]
        self.Fixed = True
        self.RefreshCanvasPosition()
        self.ForceRefresh()

    def RefreshCanvasPosition(self):
        if len(self.Ticks) > 0:
            pos = int(self.StartTick - self.Ticks[0])
            range = int(self.Ticks[-1] - self.Ticks[0])
        else:
            pos = 0
            range = 0
        self.CanvasPosition.SetScrollbar(pos, self.CurrentRange, range, self.CurrentRange)

    def ChangeRange(self, dir, tick=None):
        current_range = self.CurrentRange
        current_range_idx = self.CanvasRange.GetSelection()
        new_range_idx = max(0, min(current_range_idx + dir, len(self.RANGE_VALUES) - 1))
        if new_range_idx != current_range_idx:
            self.CanvasRange.SetSelection(new_range_idx)
            self.CurrentRange = self.RANGE_VALUES[new_range_idx][1] / self.Ticktime
            if len(self.Ticks) > 0:
                if tick is None:
                    tick = self.StartTick + self.CurrentRange / 2.
                new_start_tick = min(tick - (tick - self.StartTick) * self.CurrentRange / current_range,
                                     self.Ticks[-1] - self.CurrentRange)
                self.StartTick = self.Ticks[numpy.argmin(numpy.abs(self.Ticks - new_start_tick))]
                self.Fixed = new_start_tick < self.Ticks[-1] - self.CurrentRange
            self.ForceRefresh()

    def RefreshRange(self):
        if len(self.Ticks) > 0:
            if self.Fixed and self.Ticks[-1] - self.Ticks[0] < self.CurrentRange:
                self.Fixed = False
            if self.Fixed:
                self.StartTick = min(self.StartTick, self.Ticks[-1] - self.CurrentRange)
            else:
                self.StartTick = max(self.Ticks[0], self.Ticks[-1] - self.CurrentRange)
        self.ForceRefresh()

    def OnRangeChanged(self, event):
        try:
            self.CurrentRange = self.RANGE_VALUES[self.CanvasRange.GetSelection()][1] // self.Ticktime
        except ValueError:
            self.CanvasRange.SetValue(str(self.CurrentRange))
        wx.CallAfter(self.RefreshRange)
        event.Skip()

    def OnCurrentButton(self, event):
        if len(self.Ticks) > 0:
            self.StartTick = max(self.Ticks[0], self.Ticks[-1] - self.CurrentRange)
            self.ResetCursorTick()
        event.Skip()

    def CopyDataToClipboard(self, variables):
        text = "tick;%s;\n" % ";".join([item.GetVariable() for item, data in variables])
        next_tick = NextTick(variables)
        while next_tick is not None:
            values = []
            for item, data in variables:
                if len(data) > 0:
                    if next_tick == data[0][0]:
                        var_type = item.GetVariableType()
                        if var_type in ["STRING", "WSTRING"]:
                            value = item.GetRawValue(int(data.pop(0)[2]))
                            if var_type == "STRING":
                                values.append("'%s'" % value)
                            else:
                                values.append('"%s"' % value)
                        else:
                            values.append("%.3f" % data.pop(0)[1])
                    else:
                        values.append("")
                else:
                    values.append("")
            text += "%d;%s;\n" % (next_tick, ";".join(values))
            next_tick = NextTick(variables)
        self.ParentWindow.SetCopyBuffer(text)

    def OnExportGraphButton(self, event):
        items = reduce(lambda x, y: x + y,
                       [panel.GetItems() for panel in self.GraphicPanels],
                       [])
        variables = [(item, [entry for entry in item.GetData()])
                     for item in items
                     if item.IsNumVariable()]
        wx.CallAfter(self.CopyDataToClipboard, variables)
        event.Skip()

    def OnPositionChanging(self, event):
        if len(self.Ticks) > 0:
            self.StartTick = self.Ticks[0] + event.GetPosition()
            self.Fixed = True
            self.ForceRefresh()
        event.Skip()

    def GetRange(self):
        return self.StartTick, self.StartTick + self.CurrentRange

    def GetViewerIndex(self, viewer):
        if viewer in self.GraphicPanels:
            return self.GraphicPanels.index(viewer)
        return None

    def IsViewerFirst(self, viewer):
        return viewer == self.GraphicPanels[0]

    def HighlightPreviousViewer(self, viewer):
        if self.IsViewerFirst(viewer):
            return
        idx = self.GetViewerIndex(viewer)
        if idx is None:
            return
        self.GraphicPanels[idx-1].SetHighlight(HIGHLIGHT_AFTER)

    def ResetVariableNameMask(self):
        items = []
        for panel in self.GraphicPanels:
            items.extend(panel.GetItems())
        if len(items) > 1:
            self.VariableNameMask = reduce(
                compute_mask, [item.GetVariable().split('.') for item in items])
        elif len(items) > 0:
            self.VariableNameMask = items[0].GetVariable().split('.')[:-1] + ['*']
        else:
            self.VariableNameMask = []
        self.MaskLabel.ChangeValue(".".join(self.VariableNameMask))
        self.MaskLabel.SetInsertionPoint(self.MaskLabel.GetLastPosition())

    def GetVariableNameMask(self):
        return self.VariableNameMask

    def InsertValue(self, iec_path, idx=None, force=False, graph=False):
        for panel in self.GraphicPanels:
            if panel.GetItem(iec_path) is not None:
                if graph and isinstance(panel, DebugVariableTextViewer):
                    self.ToggleViewerType(panel)
                return
        if idx is None:
            idx = len(self.GraphicPanels)
        item = DebugVariableItem(self, iec_path, True)
        result = self.AddDataConsumer(iec_path.upper(), item, True)
        if result is not None or force:

            self.Freeze()
            if item.IsNumVariable() and graph:
                panel = DebugVariableGraphicViewer(self.GraphicsWindow, self, [item], GRAPH_PARALLEL)
                if self.CursorTick is not None:
                    panel.SetCursorTick(self.CursorTick)
            else:
                panel = DebugVariableTextViewer(self.GraphicsWindow, self, [item])
            if idx is not None:
                self.GraphicPanels.insert(idx, panel)
            else:
                self.GraphicPanels.append(panel)
            self.ResetVariableNameMask()
            self.RefreshGraphicsSizer()
            self.Thaw()
            self.ForceRefresh()

    def MoveValue(self, iec_path, idx=None, graph=False):
        if idx is None:
            idx = len(self.GraphicPanels)
        source_panel = None
        item = None
        for panel in self.GraphicPanels:
            item = panel.GetItem(iec_path)
            if item is not None:
                source_panel = panel
                break
        if source_panel is not None:
            source_panel_idx = self.GraphicPanels.index(source_panel)

            if len(source_panel.GetItems()) == 1:

                if source_panel_idx < idx:
                    self.GraphicPanels.insert(idx, source_panel)
                    self.GraphicPanels.pop(source_panel_idx)
                elif source_panel_idx > idx:
                    self.GraphicPanels.pop(source_panel_idx)
                    self.GraphicPanels.insert(idx, source_panel)
                else:
                    return

            else:
                source_panel.RemoveItem(item)
                source_size = source_panel.GetSize()
                if item.IsNumVariable() and graph:
                    panel = DebugVariableGraphicViewer(self.GraphicsWindow, self, [item], GRAPH_PARALLEL)
                    panel.SetCanvasHeight(source_size.height)
                    if self.CursorTick is not None:
                        panel.SetCursorTick(self.CursorTick)

                else:
                    panel = DebugVariableTextViewer(self.GraphicsWindow, self, [item])

                self.GraphicPanels.insert(idx, panel)

                if source_panel.ItemsIsEmpty():
                    if source_panel.HasCapture():
                        source_panel.ReleaseMouse()
                    source_panel.Destroy()
                    self.GraphicPanels.remove(source_panel)

            self.ResetVariableNameMask()
            self.RefreshGraphicsSizer()
            self.ForceRefresh()

    def MergeGraphs(self, source, target_idx, merge_type, force=False):
        source_item = None
        source_panel = None
        for panel in self.GraphicPanels:
            source_item = panel.GetItem(source)
            if source_item is not None:
                source_panel = panel
                break
        if source_item is None:
            item = DebugVariableItem(self, source, True)
            if item.IsNumVariable():
                result = self.AddDataConsumer(source.upper(), item, True)
                if result is not None or force:
                    source_item = item
        if source_item is not None and source_item.IsNumVariable():
            if source_panel is not None:
                source_size = source_panel.GetSize()
            else:
                source_size = None
            target_panel = self.GraphicPanels[target_idx]
            graph_type = target_panel.GraphType
            if target_panel != source_panel:
                if merge_type == GRAPH_PARALLEL and graph_type != merge_type or \
                   merge_type == GRAPH_ORTHOGONAL and (
                           graph_type == GRAPH_PARALLEL and len(target_panel.Items) > 1 or
                           graph_type == GRAPH_ORTHOGONAL and len(target_panel.Items) >= 3):
                    return

                if source_panel is not None:
                    source_panel.RemoveItem(source_item)
                    if source_panel.ItemsIsEmpty():
                        if source_panel.HasCapture():
                            source_panel.ReleaseMouse()
                        source_panel.Destroy()
                        self.GraphicPanels.remove(source_panel)
            elif merge_type != graph_type and len(target_panel.Items) == 2:
                target_panel.RemoveItem(source_item)
            else:
                target_panel = None

            if target_panel is not None:
                target_panel.AddItem(source_item)
                target_panel.GraphType = merge_type
                size = target_panel.GetSize()
                if merge_type == GRAPH_ORTHOGONAL:
                    target_panel.SetCanvasHeight(size.width)
                elif source_size is not None and source_panel != target_panel:
                    target_panel.SetCanvasHeight(size.height + source_size.height)
                else:
                    target_panel.SetCanvasHeight(size.height)
                target_panel.ResetGraphics()

                self.ResetVariableNameMask()
                self.RefreshGraphicsSizer()
                self.ForceRefresh()

    def DeleteValue(self, source_panel, item=None):
        source_idx = self.GetViewerIndex(source_panel)
        if source_idx is not None:

            if item is None:
                source_panel.ClearItems()
                source_panel.Destroy()
                self.GraphicPanels.remove(source_panel)
                self.ResetVariableNameMask()
                self.RefreshGraphicsSizer()
            else:
                source_panel.RemoveItem(item)
                if source_panel.ItemsIsEmpty():
                    source_panel.Destroy()
                    self.GraphicPanels.remove(source_panel)
                    self.ResetVariableNameMask()
                    self.RefreshGraphicsSizer()
            if len(self.GraphicPanels) == 0:
                self.Fixed = False
                self.ResetCursorTick()
            self.ForceRefresh()

    def ToggleViewerType(self, panel):
        panel_idx = self.GetViewerIndex(panel)
        if panel_idx is not None:
            self.GraphicPanels.remove(panel)
            items = panel.GetItems()
            if isinstance(panel, DebugVariableGraphicViewer):
                for idx, item in enumerate(items):
                    new_panel = DebugVariableTextViewer(self.GraphicsWindow, self, [item])
                    self.GraphicPanels.insert(panel_idx + idx, new_panel)
            else:
                new_panel = DebugVariableGraphicViewer(self.GraphicsWindow, self, items, GRAPH_PARALLEL)
                self.GraphicPanels.insert(panel_idx, new_panel)
            panel.Destroy()
        self.RefreshGraphicsSizer()
        self.ForceRefresh()

    def ResetGraphicsValues(self):
        self.Ticks = numpy.array([])
        self.StartTick = 0
        for panel in self.GraphicPanels:
            panel.ResetItemsData()
        self.ResetCursorTick()

    def RefreshGraphicsWindowScrollbars(self):
        xstart, ystart = self.GraphicsWindow.GetViewStart()
        window_size = self.GraphicsWindow.GetClientSize()
        vwidth, vheight = self.GraphicsSizer.GetMinSize()
        posx = max(0, min(xstart, (vwidth - window_size[0]) // SCROLLBAR_UNIT))
        posy = max(0, min(ystart, (vheight - window_size[1]) // SCROLLBAR_UNIT))
        self.GraphicsWindow.Scroll(posx, posy)
        self.GraphicsWindow.SetScrollbars(SCROLLBAR_UNIT, SCROLLBAR_UNIT,
                                          vwidth // SCROLLBAR_UNIT,
                                          vheight // SCROLLBAR_UNIT,
                                          posx, posy)

    def OnGraphicsWindowEraseBackground(self, event):
        pass

    def OnGraphicsWindowPaint(self, event):
        """EVT_PAINT handler"""

        self.DrawView()
        event.Skip()

    def OnGraphicsWindowResize(self, event):
        size = self.GetSize()
        for panel in self.GraphicPanels:
            panel_size = panel.GetSize()
            if isinstance(panel, DebugVariableGraphicViewer) and \
               panel.GraphType == GRAPH_ORTHOGONAL and \
               panel_size.width == panel_size.height:
                panel.SetCanvasHeight(size.width)
        self.RefreshGraphicsWindowScrollbars()
        self.GraphicsSizer.Layout()
        event.Skip()

    def OnGraphicsWindowMouseWheel(self, event):
        if self.VetoScrollEvent:
            self.VetoScrollEvent = False
        else:
            event.Skip()
