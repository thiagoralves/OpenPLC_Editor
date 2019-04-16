#
# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2018: Andrey Skvortsov <andrej.skvortzov@gmail.com>
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


class CommentEditDialog(wx.Dialog):
    """
    This dialog behaves like wx.TextEntryDialog,
    but additionaly it allows to set custom font and
    exact size for wx.TextCtrl.
    That allows to edit comment and immediately
    see how it'll be shown on wiresheet.
    """

    def __init__(self, parent, font, value="", size=wx.Size(400, 200)):
        """
        Constructor

        :param parent:
            parent window (wx.Window)
        :param font:
            the font for text control
        :param value:
            the default value, which may be the empty string
        :param size:
            desired initial size for text control.
            Minimal size of text control is limited
            by (100,100)
        """
        wx.Dialog.__init__(self, parent, title=_("Please enter comment text"))
        msg_label = wx.StaticText(self, label=_("Edit comment"))
        input_size = wx.Size(max(size[0], 100), max(size[1], 100))
        input = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        input.SetInitialSize(input_size)
        input.SetFont(font)
        input.SetValue(value)
        buttons = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=3, vgap=10)
        border = 20

        sizer.Add(msg_label, 0,
                  flag=wx.TOP | wx.LEFT | wx.RIGHT,
                  border=border)
        sizer.Add(input, 1,
                  flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
                  border=border)
        sizer.Add(buttons, 0,
                  flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                  border=border)

        self.SetSizerAndFit(sizer)
        self.input = input

    def SetValue(self, value):
        """Sets text value"""
        self.input.SetValue(value)

    def GetValue(self):
        """
        Returns the text that the user has entered
        if the user has pressed wx.OK,
        or the original value if the user has pressed Cancel.
        """
        return self.input.GetValue()
