#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
# Copyright (C) 2022: Edouard TISSERANT
#
# See COPYING file for copyrights details.



import wx


# class RichMessageDialog is still not available in wxPython 3.0.2
class  MessageBoxOnce(wx.Dialog):
    """
    wx.MessageBox that user can ask not to show again
    """
    def __init__(self, title, message, config_key):
        self.Config = wx.ConfigBase.Get()
        self.config_key = config_key
        dont_show = self.Config.Read(self.config_key) == "True"

        if dont_show:
            return

        wx.Dialog.__init__(self, None, title=title)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        message = wx.StaticText(self, label=message)
        main_sizer.Add(message, border=20,
            flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.LEFT | wx.RIGHT)

        self.check = wx.CheckBox(self, label=_("don't show this message again"))
        main_sizer.Add(self.check, border=20,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        Button = wx.Button(self, label="OK")

        self.Bind(wx.EVT_BUTTON, self.OnOKButton, Button)
        buttons_sizer.Add(Button)

        main_sizer.Add(buttons_sizer, border=20,
                            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT)

        self.SetSizer(main_sizer)
        self.Fit()

        self.ShowModal()

    def OnOKButton(self, event):
        if self.check.GetValue():
            self.Config.Write(self.config_key, "True")
        self.EndModal(wx.ID_OK)
