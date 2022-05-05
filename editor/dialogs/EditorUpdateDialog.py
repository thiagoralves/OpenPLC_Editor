from __future__ import absolute_import
import threading
from builtins import str as text

import wx
import wx.xrc
import os

# -------------------------------------------------------------------------------
#                            Editor Update Dialog
# -------------------------------------------------------------------------------


class EditorUpdateDialog(wx.Dialog):
    """Dialog to configure upload parameters"""

    def __init__(self, parent):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        """

        if os.name == 'nt':
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"OpenPLC Editor Updater", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_DIALOG_STYLE )
        else:
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"OpenPLC Editor Updater", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_DIALOG_STYLE )
		
        self.SetSizeHintsSz( wx.Size( 450,150 ), wx.DefaultSize )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.update_msg_lbl = wx.StaticText( self, wx.ID_ANY, u"Checking for updates...", wx.Point( -1,-1 ), wx.Size( -1,-1 ), wx.ALIGN_LEFT )
        self.update_msg_lbl.Wrap( -1 )
        bSizer2.Add( self.update_msg_lbl, 0, wx.ALIGN_CENTER|wx.ALL, 10 )

        self.m_gauge1 = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 400,-1 ), wx.GA_HORIZONTAL )
        self.m_gauge1.SetValue( 0 ) 
        bSizer2.Add( self.m_gauge1, 0, wx.ALIGN_CENTER|wx.ALL, 15 )

        self.cancel_button = wx.Button( self, wx.ID_ANY, u"Cancel", wx.Point( -1,-1 ), wx.Size( 150,40 ), 0 )
        bSizer2.Add( self.cancel_button, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 15 )
        self.cancel_button.Bind(wx.EVT_BUTTON, self.OnCancel)

        self.SetSizer( bSizer2 )
        self.Layout()
        bSizer2.Fit( self )

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass

    def onUIChange(self, e):
        pass

    def OnCancel(self, event):
        self.EndModal(wx.ID_OK)

    def startUpdater(self):
        pass