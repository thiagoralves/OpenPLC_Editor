from __future__ import absolute_import
import threading
import time
from builtins import str as text

import urllib.request
import ssl
import platform

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
		
        self.SetSizeHints( wx.Size( 450,150 ), wx.DefaultSize )

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

        return_code = 0
        updater_thread = threading.Thread(target=self.updater, args=([return_code]))
        updater_thread.start()

    def __del__( self ):
        pass

    def updater(self, return_code):
        #Read current revision
        local_revision = 0
        try:
            f = open("revision", "r")
            local_revision = int(f.read())
        except OSError:
            local_revision = 0
        
        #Download revision file from GitHub
        if platform.system() == 'Darwin':
            context = ssl._create_unverified_context() #bypass SSL errors on macOS - TODO: fix it later
            cloud_file = urllib.request.urlopen('https://github.com/thiagoralves/OpenPLC_Editor/blob/master/revision?raw=true', context=context)
        else:
            cloud_file = urllib.request.urlopen('https://github.com/thiagoralves/OpenPLC_Editor/blob/master/revision?raw=true')
        
        cloud_revision = int(cloud_file.read().decode('utf-8'))
        if (cloud_revision > local_revision):
            r = wx.MessageDialog(None, 'There is a newer version available. \nCurrent revision: ' + str(local_revision) + '\nUpdate: ' + str(cloud_revision) + '\n\nWould you like to update?', 'OpenPLC Editor Update', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
            if r == wx.ID_YES:
                wx.CallAfter(self.update_msg_lbl.SetLabelText, 'Downloading update...')
            else:
                self.EndModal(wx.ID_OK)
        else:
            wx.MessageDialog(None, "You're running the most recent version of OpenPLC Editor. There are no updates available at this time.", 'OpenPLC Editor Update', wx.OK | wx.OK_DEFAULT).ShowModal()
            self.EndModal(wx.ID_OK)
            
    def onUIChange(self, e):
        pass

    def OnCancel(self, event):
        self.EndModal(wx.ID_OK)

    def startUpdater(self):
        pass