from __future__ import absolute_import

import wx
from controls.IDBrowser import IDBrowser


class IDManager(wx.Dialog):
    def __init__(self, parent, ctr):
        self.ctr = ctr
        wx.Dialog.__init__(self,
                           name='IDManager', parent=parent,
                           title=_('URI Editor'),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           size=(800, 600))
        # start IDBrowser in manager mode
        self.browser = IDBrowser(self, ctr)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnEscapeKey)

    def OnEscapeKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()
