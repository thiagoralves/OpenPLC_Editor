from __future__ import absolute_import

import wx
from connectors import ConnectorSchemes, EditorClassFromScheme
from controls.DiscoveryPanel import DiscoveryPanel


class UriEditor(wx.Dialog):
    def _init_ctrls(self, parent):
        self.UriTypeChoice = wx.Choice(parent=self, choices=self.choices)
        self.UriTypeChoice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnTypeChoice, self.UriTypeChoice)
        self.editor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ButtonSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)

    def _init_sizers(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        typeSizer = wx.BoxSizer(wx.HORIZONTAL)
        typeSizer.Add(wx.StaticText(self, wx.ID_ANY, _("Scheme :")), border=5,
                      flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        typeSizer.Add(self.UriTypeChoice, border=5, flag=wx.ALL)
        self.mainSizer.Add(typeSizer)

        self.mainSizer.Add(self.editor_sizer, border=5, flag=wx.ALL)
        self.mainSizer.Add(self.ButtonSizer, border=5,
                           flag=wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL)
        self.SetSizer(self.mainSizer)
        self.Layout()
        self.Fit()

    def __init__(self, parent, ctr, uri=''):
        self.ctr = ctr
        wx.Dialog.__init__(self,
                           name='UriEditor', parent=parent,
                           title=_('URI Editor'))
        self.choices = [_("- Search local network -")] + ConnectorSchemes()
        self._init_ctrls(parent)
        self._init_sizers()
        self.scheme = None
        self.scheme_editor = None
        self.SetURI(uri)
        self.CenterOnParent()

    def OnTypeChoice(self, event):
        index = event.GetSelection()
        self._replaceSchemeEditor(event.GetString() if index > 0 else None)

    def SetURI(self, uri):
        try:
            scheme, loc = uri.strip().split("://", 1)
            scheme = scheme.upper()
        except Exception:
            scheme = None

        if scheme in ConnectorSchemes():
            self.UriTypeChoice.SetStringSelection(scheme)
        else:
            self.UriTypeChoice.SetSelection(0)
            scheme = None

        self._replaceSchemeEditor(scheme)

        if scheme is not None:
            self.scheme_editor.SetLoc(loc)

    def GetURI(self):
        if self.scheme is None:
            return self.scheme_editor.GetURI()
        else:
            return self.scheme+"://"+self.scheme_editor.GetLoc()

    def _replaceSchemeEditor(self, scheme):
        self.scheme = scheme

        if self.scheme_editor is not None:
            self.editor_sizer.Detach(self.scheme_editor)
            self.scheme_editor.Destroy()
            self.scheme_editor = None

        if scheme is not None:
            EditorClass = EditorClassFromScheme(scheme)
            self.scheme_editor = EditorClass(scheme, self)
        else:
            # None is for searching local network
            self.scheme_editor = DiscoveryPanel(self)

        self.editor_sizer.Add(self.scheme_editor)
        self.scheme_editor.Refresh()

        self.editor_sizer.Layout()
        self.mainSizer.Layout()
        self.Fit()
