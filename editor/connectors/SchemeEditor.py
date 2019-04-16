#!/usr/bin/env python
# -*- coding: utf-8 -*-

# See COPYING file for copyrights details.

from __future__ import absolute_import

from functools import partial
import wx

from controls.IDBrowser import IDBrowser


class SchemeEditor(wx.Panel):
    def __init__(self, scheme, parent, *args, **kwargs):
        self.txtctrls = {}
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.fieldsizer = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)

        if self.EnableIDSelector:
            self.model = self.model + [("ID", _("ID:"))]

        for tag, label in self.model:
            txtctrl = wx.TextCtrl(parent=self, size=wx.Size(200, -1))
            self.txtctrls[tag] = txtctrl
            for win, flag in [
                    (wx.StaticText(self, label=label),
                     wx.ALIGN_CENTER_VERTICAL),
                    (txtctrl, wx.GROW)]:
                self.fieldsizer.AddWindow(win, flag=flag)

        self.fieldsizer.AddSpacer(20)

        if self.EnableIDSelector:
            self.mainsizer = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
            self.mainsizer.AddSizer(self.fieldsizer)
            self.idselector = IDBrowser(
                self, parent.ctr,
                # use a callafter, as editor can be deleted by calling SetURI
                partial(wx.CallAfter, parent.SetURI),
                self.txtctrls["ID"].SetValue)
            self.mainsizer.AddWindow(self.idselector)
            self.SetSizer(self.mainsizer)
        else:
            self.SetSizer(self.fieldsizer)

    def SetFields(self, fields):
        for tag, _label in self.model:
            self.txtctrls[tag].SetValue(fields[tag])

    def GetFields(self):
        return {tag: self.txtctrls[tag].GetValue() for tag, _label in self.model}
