from __future__ import absolute_import
import threading
import time
from builtins import str as text

import urllib2
import ssl
import platform
from subprocess import check_output

import wx
import wx.xrc
import os

# -------------------------------------------------------------------------------
#                            Editor Update Dialog
# -------------------------------------------------------------------------------

global update_finished

class EditorUpdateDialog(wx.Dialog):
    """Dialog to configure upload parameters"""

    update_finished = 0
    update_cancelled = False

    def __init__(self, parent):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        """
        
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"OpenPLC Editor Updater", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_DIALOG_STYLE )
		
        self.SetSizeHintsSz( wx.Size( 450,150 ), wx.DefaultSize )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.update_msg_lbl = wx.StaticText( self, wx.ID_ANY, u"Checking for updates...", wx.Point( -1,-1 ), wx.Size( 400,-1 ), wx.ALIGN_CENTRE )
        self.update_msg_lbl.Wrap( -1 )
        self.update_msg_lbl.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString ) )
        bSizer2.Add( self.update_msg_lbl, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10 )

        self.m_gauge1 = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size( 400,-1 ), wx.GA_HORIZONTAL )
        self.m_gauge1.SetValue( 0 )
        self.m_gauge1.SetRange(100)
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

    def incrementGauge(self):
        if self.update_cancelled is True:
            return
        
        current_value = self.m_gauge1.GetValue()
        if (current_value < 80):
            wx.CallAfter(self.m_gauge1.SetValue, current_value+5)
        else:
            wx.CallAfter(self.update_msg_lbl.SetLabelText, 'Checking update...')
        
        if self.update_finished == 0:
            threading.Timer(3, self.incrementGauge).start()
        elif self.update_finished == 1:
            wx.CallAfter(self.m_gauge1.SetValue, 100)
            wx.CallAfter(self.update_msg_lbl.SetLabelText, 'Update finished! Please restart OpenPLC Editor.')
            wx.CallAfter(self.cancel_button.SetLabel, 'Ok')
        elif self.update_finished == -1:
            wx.CallAfter(self.m_gauge1.SetValue, 0)
            wx.CallAfter(self.update_msg_lbl.SetLabelText, 'Error while trying to download update.\nCheck your internet connection and try again.')
            wx.CallAfter(self.cancel_button.SetLabel, 'Ok')

    def cloneRepository(self):
        self.update_finished = 0
        self.incrementGauge()
        run_script = './update.sh'
        if platform.system() == 'Windows':
            run_script = 'update.cmd'
        return_str = check_output(run_script, shell=True)
        last_line = return_str[-35:]
        if 'Update applied successfully' in last_line:
            self.update_finished = 1
        else:
            self.update_finished = -1
        
    def shouldUpdate(self, local_revision, cloud_revision):
        r = wx.MessageDialog(None, 'There is a newer version available. \nCurrent revision: ' + str(local_revision) + '\nUpdate: ' + str(cloud_revision) + '\n\nWould you like to update?', 'OpenPLC Editor Update', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION).ShowModal()
        if r == wx.ID_YES:
            wx.CallAfter(self.update_msg_lbl.SetLabelText, 'Downloading update...')
            updater_thread = threading.Thread(target=self.cloneRepository)
            updater_thread.start()
        else:
            self.EndModal(wx.ID_OK)

    def updater(self, return_code):
        #Read current revision
        local_revision = 0
        try:
            f = open("revision", "r")
            local_revision = int(f.read())
        except IOError:
            local_revision = 0
        
        #Download revision file from GitHub
        if platform.system() == 'Darwin':
            context = ssl._create_unverified_context() #bypass SSL errors on macOS - TODO: fix it later
            cloud_file = urllib2.urlopen('https://github.com/thiagoralves/OpenPLC_Editor/blob/master/revision?raw=true', context=context)
        else:
            cloud_file = urllib2.urlopen('https://github.com/thiagoralves/OpenPLC_Editor/blob/master/revision?raw=true')
        
        cloud_revision = int(cloud_file.read().decode('utf-8'))
        if (cloud_revision > local_revision):
            wx.CallAfter(self.shouldUpdate, local_revision, cloud_revision)
        else:
            r = wx.MessageDialog(None, "You're running the most recent version of OpenPLC Editor. There are no updates available at this time.", 'OpenPLC Editor Update', wx.OK | wx.OK_DEFAULT)
            wx.CallAfter(r.ShowModal)
            wx.CallAfter(self.EndModal, wx.ID_OK)
            
    def onUIChange(self, e):
        pass

    def OnCancel(self, event):
        self.update_cancelled = True
        self.EndModal(wx.ID_OK)

    def startUpdater(self):
        pass
