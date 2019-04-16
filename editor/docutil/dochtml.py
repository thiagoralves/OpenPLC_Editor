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
import subprocess
import wx
import wx.html

HtmlFrameOpened = []


def OpenHtmlFrame(self, title, file, size):
    if title not in HtmlFrameOpened:
        HtmlFrameOpened.append(title)
        window = HtmlFrame(self, HtmlFrameOpened)
        window.SetTitle(title)
        window.SetHtmlPage(file)
        window.SetClientSize(size)
        window.Show()


[ID_HTMLFRAME, ID_HTMLFRAMEHTMLCONTENT] = [wx.NewId() for _init_ctrls in range(2)]
EVT_HTML_URL_CLICK = wx.NewId()


class HtmlWindowUrlClick(wx.PyEvent):
    def __init__(self, linkinfo):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_HTML_URL_CLICK)
        self.linkinfo = (linkinfo.GetHref(), linkinfo.GetTarget())


class UrlClickHtmlWindow(wx.html.HtmlWindow):
    """ HTML window that generates and OnLinkClicked event.

    Use this to avoid having to override HTMLWindow
    """
    def OnLinkClicked(self, linkinfo):
        wx.PostEvent(self, HtmlWindowUrlClick(linkinfo))

    def Bind(self, event, handler, source=None, id=wx.ID_ANY, id2=wx.ID_ANY):
        if event == HtmlWindowUrlClick:
            self.Connect(-1, -1, EVT_HTML_URL_CLICK, handler)
        else:
            wx.html.HtmlWindow.Bind(self, event, handler, source=source, id=id, id2=id2)


class HtmlFrame(wx.Frame):
    def _init_ctrls(self, prnt):
        self.SetIcon(prnt.icon)
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        self.HtmlContent = UrlClickHtmlWindow(id=ID_HTMLFRAMEHTMLCONTENT,
                                              name='HtmlContent', parent=self, pos=wx.Point(0, 0),
                                              size=wx.Size(-1, -1), style=wx.html.HW_SCROLLBAR_AUTO | wx.html.HW_NO_SELECTION)
        self.HtmlContent.Bind(HtmlWindowUrlClick, self.OnLinkClick)

    def __init__(self, parent, opened):
        wx.Frame.__init__(self, id=ID_HTMLFRAME, name='HtmlFrame',
                          parent=parent, pos=wx.Point(320, 231),
                          size=wx.Size(853, 616),
                          style=wx.DEFAULT_FRAME_STYLE, title='')
        self._init_ctrls(parent)
        self.HtmlFrameOpened = opened

    def SetHtmlCode(self, htmlcode):
        self.HtmlContent.SetPage(htmlcode)

    def SetHtmlPage(self, htmlpage):
        self.HtmlContent.LoadPage(htmlpage)

    def OnCloseFrame(self, event):
        self.HtmlFrameOpened.remove(self.GetTitle())
        event.Skip()

    def OnLinkClick(self, event):
        url = event.linkinfo[0]
        try:
            if wx.Platform == '__WXMSW__':
                import webbrowser
                webbrowser.open(url)
            elif subprocess.call("firefox %s" % url, shell=True) != 0:
                wx.MessageBox("""Firefox browser not found.\nPlease point your browser at :\n%s""" % url)
        except ImportError:
            wx.MessageBox('Please point your browser at: %s' % url)
