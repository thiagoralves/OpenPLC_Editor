#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2013: Edouard TISSERANT and Laurent BESSARD
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
from datetime import datetime
from time import time as gettime
from weakref import proxy

import numpy
import wx
from six.moves import xrange

from controls.CustomToolTip import CustomToolTip, TOOLTIP_WAIT_PERIOD
from editors.DebugViewer import DebugViewer, REFRESH_PERIOD
from runtime.loglevels import LogLevelsCount, LogLevels
from util.BitmapLibrary import GetBitmap


THUMB_SIZE_RATIO = 1. / 8.


def ArrowPoints(direction, width, height, xoffset, yoffset):
    if direction == wx.TOP:
        return [wx.Point(xoffset + 1, yoffset + height - 2),
                wx.Point(xoffset + width // 2, yoffset + 1),
                wx.Point(xoffset + width - 1, yoffset + height - 2)]
    else:
        return [wx.Point(xoffset + 1, yoffset - height + 1),
                wx.Point(xoffset + width // 2, yoffset - 2),
                wx.Point(xoffset + width - 1, yoffset - height + 1)]


class LogScrollBar(wx.Panel):

    def __init__(self, parent, size):
        wx.Panel.__init__(self, parent, size=size)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)

        self.ThumbPosition = 0.  # -1 <= ThumbPosition <= 1
        self.ThumbScrollingStartPos = None

    def GetRangeRect(self):
        width, height = self.GetClientSize()
        return wx.Rect(0, width, width, height - 2 * width)

    def GetThumbRect(self):
        width, _height = self.GetClientSize()
        range_rect = self.GetRangeRect()
        thumb_size = range_rect.height * THUMB_SIZE_RATIO
        thumb_range = range_rect.height - thumb_size
        thumb_center_position = (thumb_size + (self.ThumbPosition + 1) * thumb_range) / 2.
        thumb_start = int(thumb_center_position - thumb_size / 2.)
        thumb_end = int(thumb_center_position + thumb_size / 2.)
        return wx.Rect(0, range_rect.y + thumb_start, width, thumb_end - thumb_start)

    def RefreshThumbPosition(self, thumb_position=None):
        if thumb_position is None:
            thumb_position = self.ThumbPosition
        if self.Parent.IsMessagePanelTop():
            thumb_position = max(0., thumb_position)
        if self.Parent.IsMessagePanelBottom():
            thumb_position = min(0., thumb_position)
        if thumb_position != self.ThumbPosition:
            self.ThumbPosition = thumb_position
            self.Parent.SetScrollSpeed(self.ThumbPosition)
        self.Refresh()

    def OnLeftDown(self, event):
        self.CaptureMouse()
        posx, posy = event.GetPosition()
        width, height = self.GetClientSize()
        range_rect = self.GetRangeRect()
        thumb_rect = self.GetThumbRect()
        if range_rect.InsideXY(posx, posy):
            if thumb_rect.InsideXY(posx, posy):
                self.ThumbScrollingStartPos = wx.Point(posx, posy)
            elif posy < thumb_rect.y:
                self.Parent.ScrollToLast()
            elif posy > thumb_rect.y + thumb_rect.height:
                self.Parent.ScrollToFirst()
        elif posy < width:
            self.Parent.ScrollMessagePanelByPage(1)
        elif posy > height - width:
            self.Parent.ScrollMessagePanelByPage(-1)
        event.Skip()

    def OnLeftUp(self, event):
        self.ThumbScrollingStartPos = None
        self.RefreshThumbPosition(0.)
        if self.HasCapture():
            self.ReleaseMouse()
        event.Skip()

    def OnMotion(self, event):
        if event.Dragging() and self.ThumbScrollingStartPos is not None:
            _posx, posy = event.GetPosition()
            range_rect = self.GetRangeRect()
            thumb_size = range_rect.height * THUMB_SIZE_RATIO
            thumb_range = range_rect.height - thumb_size
            self.RefreshThumbPosition(
                max(-1., min((posy - self.ThumbScrollingStartPos.y) * 2. // thumb_range, 1.)))
        event.Skip()

    def OnResize(self, event):
        self.Refresh()
        event.Skip()

    def OnEraseBackground(self, event):
        pass

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        gc = wx.GCDC(dc)

        width, height = self.GetClientSize()

        gc.SetPen(wx.Pen(wx.NamedColour("GREY"), 3))
        gc.SetBrush(wx.GREY_BRUSH)

        gc.DrawLines(ArrowPoints(wx.TOP, width * 0.75, width * 0.5, 2, (width + height) // 4 - 3))
        gc.DrawLines(ArrowPoints(wx.TOP, width * 0.75, width * 0.5, 2, (width + height) // 4 + 3))

        gc.DrawLines(ArrowPoints(wx.BOTTOM, width * 0.75, width * 0.5, 2, (height * 3 - width) // 4 + 3))
        gc.DrawLines(ArrowPoints(wx.BOTTOM, width * 0.75, width * 0.5, 2, (height * 3 - width) // 4 - 3))

        thumb_rect = self.GetThumbRect()
        exclusion_rect = wx.Rect(thumb_rect.x, thumb_rect.y,
                                 thumb_rect.width, thumb_rect.height)
        if self.Parent.IsMessagePanelTop():
            exclusion_rect.y, exclusion_rect.height = width, exclusion_rect.y + exclusion_rect.height - width
        if self.Parent.IsMessagePanelBottom():
            exclusion_rect.height = height - width - exclusion_rect.y
        if exclusion_rect != thumb_rect:
            colour = wx.NamedColour("LIGHT GREY")
            gc.SetPen(wx.Pen(colour))
            gc.SetBrush(wx.Brush(colour))

            gc.DrawRectangle(exclusion_rect.x, exclusion_rect.y,
                             exclusion_rect.width, exclusion_rect.height)

        gc.SetPen(wx.GREY_PEN)
        gc.SetBrush(wx.GREY_BRUSH)

        gc.DrawPolygon(ArrowPoints(wx.TOP, width, width, 0, 0))

        gc.DrawPolygon(ArrowPoints(wx.BOTTOM, width, width, 0, height))

        gc.DrawRectangle(thumb_rect.x, thumb_rect.y,
                         thumb_rect.width, thumb_rect.height)

        dc.EndDrawing()
        event.Skip()


BUTTON_SIZE = (70, 15)


class LogButton(object):

    def __init__(self, label, callback):
        self.Position = wx.Point(0, 0)
        self.Size = wx.Size(*BUTTON_SIZE)
        self.Label = label
        self.Shown = True
        self.Callback = callback

    def __del__(self):
        self.callback = None

    def GetSize(self):
        return self.Size

    def SetPosition(self, x, y):
        self.Position = wx.Point(x, y)

    def HitTest(self, x, y):
        rect = wx.Rect(self.Position.x, self.Position.y,
                       self.Size.width, self.Size.height)
        if rect.InsideXY(x, y):
            return True
        return False

    def ProcessCallback(self):
        if self.Callback is not None:
            wx.CallAfter(self.Callback)

    def Draw(self, dc):
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(wx.NamedColour("LIGHT GREY")))

        dc.DrawRectangle(self.Position.x, self.Position.y,
                         self.Size.width, self.Size.height)

        w, h = dc.GetTextExtent(self.Label)
        dc.DrawText(self.Label,
                    self.Position.x + (self.Size.width - w) // 2,
                    self.Position.y + (self.Size.height - h) // 2)


DATE_INFO_SIZE = 10
MESSAGE_INFO_SIZE = 18


class LogMessage(object):

    def __init__(self, tv_sec, tv_nsec, level, level_bitmap, msg):
        self.Date = datetime.utcfromtimestamp(tv_sec)
        self.Seconds = self.Date.second + tv_nsec * 1e-9
        self.Date = self.Date.replace(second=0)
        self.Timestamp = tv_sec + tv_nsec * 1e-9
        self.Level = level
        self.LevelBitmap = level_bitmap
        self.Message = msg
        self.DrawDate = True

    def __cmp__(self, other):
        if self.Date == other.Date:
            return cmp(self.Seconds, other.Seconds)
        return cmp(self.Date, other.Date)

    def GetFullText(self):
        date = self.Date.replace(second=int(self.Seconds))
        nsec = (self.Seconds % 1.) * 1e9
        return "%s at %s.%9.9d:\n%s" % (
            LogLevels[self.Level],
            str(date), nsec,
            self.Message)

    def Draw(self, dc, offset, width, draw_date):
        if draw_date:
            datetime_text = self.Date.strftime("%d/%m/%y %H:%M")
            dw, dh = dc.GetTextExtent(datetime_text)
            dc.DrawText(datetime_text, (width - dw) // 2, offset + (DATE_INFO_SIZE - dh) // 2)
            offset += DATE_INFO_SIZE

        seconds_text = "%12.9f" % self.Seconds
        sw, sh = dc.GetTextExtent(seconds_text)
        dc.DrawText(seconds_text, 5, offset + (MESSAGE_INFO_SIZE - sh) // 2)

        bw, bh = self.LevelBitmap.GetWidth(), self.LevelBitmap.GetHeight()
        dc.DrawBitmap(self.LevelBitmap, 10 + sw, offset + (MESSAGE_INFO_SIZE - bh) // 2)

        text = self.Message.replace("\n", " ")
        _mw, mh = dc.GetTextExtent(text)
        dc.DrawText(text, 15 + sw + bw, offset + (MESSAGE_INFO_SIZE - mh) // 2)

    def GetHeight(self, draw_date):
        if draw_date:
            return DATE_INFO_SIZE + MESSAGE_INFO_SIZE
        return MESSAGE_INFO_SIZE


SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR

CHANGE_TIMESTAMP_BUTTONS = [(_("1d"), DAY),
                            (_("1h"), HOUR),
                            (_("1m"), MINUTE),
                            (_("1s"), SECOND)]


class LogViewer(DebugViewer, wx.Panel):

    def __init__(self, parent, window):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER)
        DebugViewer.__init__(self, None, False, False)

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=5)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)

        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(filter_sizer, border=5, flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.GROW)

        self.MessageFilter = wx.ComboBox(self, style=wx.CB_READONLY)
        self.MessageFilter.Append(_("All"))
        levels = LogLevels[:3]
        levels.reverse()
        for level in levels:
            self.MessageFilter.Append(_(level))
        self.Bind(wx.EVT_COMBOBOX, self.OnMessageFilterChanged, self.MessageFilter)
        filter_sizer.AddWindow(self.MessageFilter, 1, border=5, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)

        self.SearchMessage = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.SearchMessage.ShowSearchButton(True)
        self.SearchMessage.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearchMessageChanged, self.SearchMessage)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN,
                  self.OnSearchMessageSearchButtonClick, self.SearchMessage)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN,
                  self.OnSearchMessageCancelButtonClick, self.SearchMessage)
        filter_sizer.AddWindow(self.SearchMessage, 3, border=5, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)

        self.CleanButton = wx.lib.buttons.GenBitmapButton(self, bitmap=GetBitmap("Clean"),
                                                          size=wx.Size(28, 28), style=wx.NO_BORDER)
        self.CleanButton.SetToolTipString(_("Clean log messages"))
        self.Bind(wx.EVT_BUTTON, self.OnCleanButton, self.CleanButton)
        filter_sizer.AddWindow(self.CleanButton)

        message_panel_sizer = wx.FlexGridSizer(cols=2, hgap=0, rows=1, vgap=0)
        message_panel_sizer.AddGrowableCol(0)
        message_panel_sizer.AddGrowableRow(0)
        main_sizer.AddSizer(message_panel_sizer, border=5, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.GROW)

        self.MessagePanel = wx.Panel(self)
        if wx.Platform == '__WXMSW__':
            self.Font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Courier New')
        else:
            self.Font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, faceName='Courier')
        self.MessagePanel.Bind(wx.EVT_LEFT_UP, self.OnMessagePanelLeftUp)
        self.MessagePanel.Bind(wx.EVT_RIGHT_UP, self.OnMessagePanelRightUp)
        self.MessagePanel.Bind(wx.EVT_LEFT_DCLICK, self.OnMessagePanelLeftDCLick)
        self.MessagePanel.Bind(wx.EVT_MOTION, self.OnMessagePanelMotion)
        self.MessagePanel.Bind(wx.EVT_LEAVE_WINDOW, self.OnMessagePanelLeaveWindow)
        self.MessagePanel.Bind(wx.EVT_MOUSEWHEEL, self.OnMessagePanelMouseWheel)
        self.MessagePanel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnMessagePanelEraseBackground)
        self.MessagePanel.Bind(wx.EVT_PAINT, self.OnMessagePanelPaint)
        self.MessagePanel.Bind(wx.EVT_SIZE, self.OnMessagePanelResize)
        message_panel_sizer.AddWindow(self.MessagePanel, flag=wx.GROW)

        self.MessageScrollBar = LogScrollBar(self, wx.Size(16, -1))
        message_panel_sizer.AddWindow(self.MessageScrollBar, flag=wx.GROW)

        self.SetSizer(main_sizer)

        self.LeftButtons = []
        for label, callback in [("+" + text, self.GenerateOnDurationButton(duration))
                                for text, duration in CHANGE_TIMESTAMP_BUTTONS]:
            self.LeftButtons.append(LogButton(label, callback))

        self.RightButtons = []
        for label, callback in [("-" + text, self.GenerateOnDurationButton(-duration))
                                for text, duration in CHANGE_TIMESTAMP_BUTTONS]:
            self.RightButtons.append(LogButton(label, callback))

        self.MessageFilter.SetSelection(0)
        self.LogSource = None
        self.ResetLogMessages()
        self.ParentWindow = window

        self.LevelIcons = [GetBitmap("LOG_" + level) for level in LogLevels]
        self.LevelFilters = [range(i) for i in xrange(4, 0, -1)]
        self.CurrentFilter = self.LevelFilters[0]
        self.CurrentSearchValue = ""

        self.ScrollSpeed = 0.
        self.LastStartTime = None
        self.ScrollTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnScrollTimer, self.ScrollTimer)

        self.LastMousePos = None
        self.MessageToolTip = None
        self.MessageToolTipTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnMessageToolTipTimer, self.MessageToolTipTimer)

    def __del__(self):
        self.ScrollTimer.Stop()

    def ResetLogMessages(self):
        self.ResetLogCounters()
        self.OldestMessages = []
        self.LogMessages = []
        self.LogMessagesTimestamp = numpy.array([])
        self.CurrentMessage = None
        self.HasNewData = False

    def SetLogSource(self, log_source):
        self.LogSource = proxy(log_source) if log_source is not None else None
        self.CleanButton.Enable(self.LogSource is not None)
        if log_source is not None:
            self.ResetLogMessages()
            wx.CallAfter(self.RefreshView)

    def GetLogMessageFromSource(self, msgidx, level):
        if self.LogSource is not None:
            answer = self.LogSource.GetLogMessage(level, msgidx)
            if answer is not None:
                msg, _tick, tv_sec, tv_nsec = answer
                return LogMessage(tv_sec, tv_nsec, level, self.LevelIcons[level], msg)
        return None

    def ResetLogCounters(self):
        self.previous_log_count = [None]*LogLevelsCount

    def SetLogCounters(self, log_count):
        new_messages = []
        for level, count, prev in zip(xrange(LogLevelsCount), log_count, self.previous_log_count):
            if count is not None and prev != count:
                if prev is None:
                    dump_end = max(-1, count - 10)
                    oldest_message = (-1, None)
                else:
                    dump_end = prev - 1
                for msgidx in xrange(count-1, dump_end, -1):
                    new_message = self.GetLogMessageFromSource(msgidx, level)
                    if new_message is None:
                        if prev is None:
                            oldest_message = (-1, None)
                        break
                    if prev is None:
                        oldest_message = (msgidx, new_message)
                        if len(new_messages) == 0:
                            new_messages = [new_message]
                        else:
                            new_messages.insert(0, new_message)
                    else:
                        new_messages.insert(0, new_message)
                if prev is None and len(self.OldestMessages) <= level:
                    self.OldestMessages.append(oldest_message)
                self.previous_log_count[level] = count
        new_messages.sort()
        if len(new_messages) > 0:
            self.HasNewData = True
            if self.CurrentMessage is not None:
                current_is_last = self.GetNextMessage(self.CurrentMessage)[0] is None
            else:
                current_is_last = True
            for new_message in new_messages:
                self.LogMessages.append(new_message)
                self.LogMessagesTimestamp = numpy.append(self.LogMessagesTimestamp, [new_message.Timestamp])
            if current_is_last:
                self.ScrollToLast(False)
                self.ResetMessageToolTip()
                self.MessageToolTipTimer.Stop()
                self.ParentWindow.SelectTab(self)
            self.NewDataAvailable(None)

    def FilterLogMessage(self, message, timestamp=None):
        return (message.Level in self.CurrentFilter and
                message.Message.find(self.CurrentSearchValue) != -1 and
                (timestamp is None or message.Timestamp < timestamp))

    def GetMessageByTimestamp(self, timestamp):
        if self.CurrentMessage is not None:
            msgidx = numpy.argmin(abs(self.LogMessagesTimestamp - timestamp))
            message = self.LogMessages[msgidx]
            if self.FilterLogMessage(message) and message.Timestamp > timestamp:
                return self.GetPreviousMessage(msgidx, timestamp)
            return message, msgidx
        return None, None

    def GetNextMessage(self, msgidx):
        while msgidx < len(self.LogMessages) - 1:
            message = self.LogMessages[msgidx + 1]
            if self.FilterLogMessage(message):
                return message, msgidx + 1
            msgidx += 1
        return None, None

    def GetPreviousMessage(self, msgidx, timestamp=None):
        message = None
        while 0 < msgidx < len(self.LogMessages):
            message = self.LogMessages[msgidx - 1]
            if self.FilterLogMessage(message, timestamp):
                return message, msgidx - 1
            msgidx -= 1
        if len(self.LogMessages) > 0:
            message = self.LogMessages[0]
            for _idx, msg in self.OldestMessages:
                if msg is not None and msg > message:
                    message = msg
            while message is not None:
                level = message.Level
                oldest_msgidx, _oldest_message = self.OldestMessages[level]
                if oldest_msgidx > 0:
                    message = self.GetLogMessageFromSource(oldest_msgidx - 1, level)
                    if message is not None:
                        self.OldestMessages[level] = (oldest_msgidx - 1, message)
                    else:
                        self.OldestMessages[level] = (-1, None)
                else:
                    message = None
                    self.OldestMessages[level] = (-1, None)
                if message is not None:
                    message_idx = 0
                    while (message_idx < len(self.LogMessages) and
                           self.LogMessages[message_idx] < message):
                        message_idx += 1
                    if len(self.LogMessages) > 0:
                        current_message = self.LogMessages[self.CurrentMessage]
                    else:
                        current_message = message
                    self.LogMessages.insert(message_idx, message)
                    self.LogMessagesTimestamp = numpy.insert(
                        self.LogMessagesTimestamp,
                        [message_idx],
                        [message.Timestamp])
                    self.CurrentMessage = self.LogMessages.index(current_message)
                    if message_idx == 0 and self.FilterLogMessage(message, timestamp):
                        return message, 0
                for _idx, msg in self.OldestMessages:
                    if msg is not None and (message is None or msg > message):
                        message = msg
        return None, None

    def RefreshNewData(self, *args, **kwargs):
        if self.HasNewData:
            self.HasNewData = False
            self.RefreshView()
        DebugViewer.RefreshNewData(self, *args, **kwargs)

    def RefreshView(self):
        width, height = self.MessagePanel.GetClientSize()
        bitmap = wx.EmptyBitmap(width, height)
        dc = wx.BufferedDC(wx.ClientDC(self.MessagePanel), bitmap)
        dc.Clear()
        dc.BeginDrawing()

        if self.CurrentMessage is not None:

            dc.SetFont(self.Font)

            for button in self.LeftButtons + self.RightButtons:
                button.Draw(dc)

            message_idx = self.CurrentMessage
            message = self.LogMessages[message_idx]
            draw_date = True
            offset = 5
            while offset < height and message is not None:
                message.Draw(dc, offset, width, draw_date)
                offset += message.GetHeight(draw_date)

                previous_message, message_idx = self.GetPreviousMessage(message_idx)
                if previous_message is not None:
                    draw_date = message.Date != previous_message.Date
                message = previous_message

        dc.EndDrawing()

        self.MessageScrollBar.RefreshThumbPosition()

    def IsPLCLogEmpty(self):
        empty = True
        for _level, prev in zip(xrange(LogLevelsCount), self.previous_log_count):
            if prev is not None:
                empty = False
                break
        return empty

    def IsMessagePanelTop(self, message_idx=None):
        if message_idx is None:
            message_idx = self.CurrentMessage
        if message_idx is not None:
            return self.GetNextMessage(message_idx)[0] is None
        return True

    def IsMessagePanelBottom(self, message_idx=None):
        if message_idx is None:
            message_idx = self.CurrentMessage
        if message_idx is not None:
            _width, height = self.MessagePanel.GetClientSize()
            offset = 5
            message = self.LogMessages[message_idx]
            draw_date = True
            while message is not None and offset < height:
                offset += message.GetHeight(draw_date)
                previous_message, message_idx = self.GetPreviousMessage(message_idx)
                if previous_message is not None:
                    draw_date = message.Date != previous_message.Date
                message = previous_message
            return offset < height
        return True

    def ScrollMessagePanel(self, scroll):
        if self.CurrentMessage is not None:
            message = self.LogMessages[self.CurrentMessage]
            while scroll > 0 and message is not None:
                message, msgidx = self.GetNextMessage(self.CurrentMessage)
                if message is not None:
                    self.CurrentMessage = msgidx
                    scroll -= 1
            while scroll < 0 and message is not None and not self.IsMessagePanelBottom():
                message, msgidx = self.GetPreviousMessage(self.CurrentMessage)
                if message is not None:
                    self.CurrentMessage = msgidx
                    scroll += 1
            self.RefreshView()

    def ScrollMessagePanelByPage(self, page):
        if self.CurrentMessage is not None:
            _width, height = self.MessagePanel.GetClientSize()
            message_per_page = max(1, (height - DATE_INFO_SIZE) // MESSAGE_INFO_SIZE - 1)
            self.ScrollMessagePanel(page * message_per_page)

    def ScrollMessagePanelByTimestamp(self, seconds):
        if self.CurrentMessage is not None:
            current_message = self.LogMessages[self.CurrentMessage]
            message, msgidx = self.GetMessageByTimestamp(current_message.Timestamp + seconds)
            if message is None or self.IsMessagePanelBottom(msgidx):
                self.ScrollToFirst()
            else:
                if seconds > 0 and self.CurrentMessage == msgidx and msgidx < len(self.LogMessages) - 1:
                    msgidx += 1
                self.CurrentMessage = msgidx
                self.RefreshView()

    def ResetMessagePanel(self):
        if len(self.LogMessages) > 0:
            self.CurrentMessage = len(self.LogMessages) - 1
            message = self.LogMessages[self.CurrentMessage]
            while message is not None and not self.FilterLogMessage(message):
                message, self.CurrentMessage = self.GetPreviousMessage(self.CurrentMessage)
            self.RefreshView()

    def OnMessageFilterChanged(self, event):
        self.CurrentFilter = self.LevelFilters[self.MessageFilter.GetSelection()]
        self.ResetMessagePanel()
        event.Skip()

    def OnSearchMessageChanged(self, event):
        self.CurrentSearchValue = self.SearchMessage.GetValue()
        self.ResetMessagePanel()
        event.Skip()

    def OnSearchMessageSearchButtonClick(self, event):
        self.CurrentSearchValue = self.SearchMessage.GetValue()
        self.ResetMessagePanel()
        event.Skip()

    def OnSearchMessageCancelButtonClick(self, event):
        self.CurrentSearchValue = ""
        self.SearchMessage.SetValue("")
        self.ResetMessagePanel()
        event.Skip()

    def OnCleanButton(self, event):
        if self.LogSource is not None and not self.IsPLCLogEmpty():
            self.LogSource.ResetLogCount()
        self.ResetLogMessages()
        self.RefreshView()
        event.Skip()

    def GenerateOnDurationButton(self, duration):
        def OnDurationButton():
            self.ScrollMessagePanelByTimestamp(duration)
        return OnDurationButton

    def GetCopyMessageToClipboardFunction(self, message):
        def CopyMessageToClipboardFunction(event):
            self.ParentWindow.SetCopyBuffer(message.GetFullText())
        return CopyMessageToClipboardFunction

    def GetMessageByScreenPos(self, posx, posy):
        if self.CurrentMessage is not None:
            _width, height = self.MessagePanel.GetClientSize()
            message_idx = self.CurrentMessage
            message = self.LogMessages[message_idx]
            draw_date = True
            offset = 5

            while offset < height and message is not None:
                if draw_date:
                    offset += DATE_INFO_SIZE

                if offset <= posy < offset + MESSAGE_INFO_SIZE:
                    return message

                offset += MESSAGE_INFO_SIZE

                previous_message, message_idx = self.GetPreviousMessage(message_idx)
                if previous_message is not None:
                    draw_date = message.Date != previous_message.Date
                message = previous_message
        return None

    def OnMessagePanelLeftUp(self, event):
        if self.CurrentMessage is not None:
            posx, posy = event.GetPosition()
            for button in self.LeftButtons + self.RightButtons:
                if button.HitTest(posx, posy):
                    button.ProcessCallback()
                    break
        event.Skip()

    def OnMessagePanelRightUp(self, event):
        message = self.GetMessageByScreenPos(*event.GetPosition())
        if message is not None:
            menu = wx.Menu(title='')

            new_id = wx.NewId()
            menu.Append(help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Copy"))
            self.Bind(wx.EVT_MENU, self.GetCopyMessageToClipboardFunction(message), id=new_id)

            self.MessagePanel.PopupMenu(menu)
            menu.Destroy()
        event.Skip()

    def OnMessagePanelLeftDCLick(self, event):
        message = self.GetMessageByScreenPos(*event.GetPosition())
        if message is not None:
            self.SearchMessage.SetFocus()
            self.SearchMessage.SetValue(message.Message)
        event.Skip()

    def ResetMessageToolTip(self):
        if self.MessageToolTip is not None:
            self.MessageToolTip.Destroy()
            self.MessageToolTip = None

    def OnMessageToolTipTimer(self, event):
        if self.LastMousePos is not None:
            message = self.GetMessageByScreenPos(*self.LastMousePos)
            if message is not None:
                tooltip_pos = self.MessagePanel.ClientToScreen(self.LastMousePos)
                tooltip_pos.x += 10
                tooltip_pos.y += 10
                self.MessageToolTip = CustomToolTip(self.MessagePanel, message.GetFullText(), False)
                self.MessageToolTip.SetFont(self.Font)
                self.MessageToolTip.SetToolTipPosition(tooltip_pos)
                self.MessageToolTip.Show()
        event.Skip()

    def OnMessagePanelMotion(self, event):
        if not event.Dragging():
            self.ResetMessageToolTip()
            self.LastMousePos = event.GetPosition()
            self.MessageToolTipTimer.Start(int(TOOLTIP_WAIT_PERIOD * 1000), oneShot=True)
        event.Skip()

    def OnMessagePanelLeaveWindow(self, event):
        self.ResetMessageToolTip()
        self.LastMousePos = None
        self.MessageToolTipTimer.Stop()
        event.Skip()

    def OnMessagePanelMouseWheel(self, event):
        self.ScrollMessagePanel(event.GetWheelRotation() // event.GetWheelDelta())
        event.Skip()

    def OnMessagePanelEraseBackground(self, event):
        pass

    def OnMessagePanelPaint(self, event):
        self.RefreshView()
        event.Skip()

    def OnMessagePanelResize(self, event):
        width, _height = self.MessagePanel.GetClientSize()
        offset = 2
        for button in self.LeftButtons:
            button.SetPosition(offset, 2)
            w, _h = button.GetSize()
            offset += w + 2
        offset = width - 2
        for button in self.RightButtons:
            w, _h = button.GetSize()
            button.SetPosition(offset - w, 2)
            offset -= w + 2
        if self.IsMessagePanelBottom():
            self.ScrollToFirst()
        else:
            self.RefreshView()
        event.Skip()

    def OnScrollTimer(self, event):
        if self.ScrollSpeed != 0.:
            speed_norm = abs(self.ScrollSpeed)
            period = REFRESH_PERIOD / speed_norm
            self.ScrollMessagePanel(-speed_norm / self.ScrollSpeed)
            self.LastStartTime = gettime()
            self.ScrollTimer.Start(int(period * 1000), True)
        event.Skip()

    def SetScrollSpeed(self, speed):
        if speed == 0.:
            self.ScrollTimer.Stop()
        else:
            speed_norm = abs(speed)
            period = REFRESH_PERIOD / speed_norm
            current_time = gettime()
            if self.LastStartTime is not None:
                elapsed_time = current_time - self.LastStartTime
                if elapsed_time > period:
                    self.ScrollMessagePanel(-speed_norm / speed)
                    self.LastStartTime = current_time
                else:
                    period -= elapsed_time
            else:
                self.LastStartTime = current_time
            self.ScrollTimer.Start(int(period * 1000), True)
        self.ScrollSpeed = speed

    def ScrollToLast(self, refresh=True):
        if len(self.LogMessages) > 0:
            self.CurrentMessage = len(self.LogMessages) - 1
            message = self.LogMessages[self.CurrentMessage]
            if not self.FilterLogMessage(message):
                message, self.CurrentMessage = self.GetPreviousMessage(self.CurrentMessage)
            if refresh:
                self.RefreshView()

    def ScrollToFirst(self):
        if len(self.LogMessages) > 0:
            message_idx = 0
            message = self.LogMessages[message_idx]
            if not self.FilterLogMessage(message):
                next_message, msgidx = self.GetNextMessage(message_idx)
                if next_message is not None:
                    message_idx = msgidx
                    message = next_message
            while message is not None:
                message, msgidx = self.GetPreviousMessage(message_idx)
                if message is not None:
                    message_idx = msgidx
            message = self.LogMessages[message_idx]
            if self.FilterLogMessage(message):
                while message is not None:
                    message, msgidx = self.GetNextMessage(message_idx)
                    if message is not None:
                        if not self.IsMessagePanelBottom(msgidx):
                            break
                        message_idx = msgidx
                self.CurrentMessage = message_idx
            else:
                self.CurrentMessage = None
            self.RefreshView()
