from __future__ import absolute_import
import threading
from builtins import str as text

import platform
import wx
import wx.xrc
import os

import serial.tools.list_ports

# -------------------------------------------------------------------------------
#                        Debugger Remote Connection Dialog
# -------------------------------------------------------------------------------

"""Dialog to configure remote debugger parameters"""
class DebuggerRemoteConnDialog(wx.Dialog):

    """
    Constructor
    @param parent: Parent wx.Window of dialog for modal
    @param connector: Connector for the remote target
    """
    def __init__( self, parent, connector ):
        self.connector = connector

        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Debugger Remote Configuration", pos = wx.DefaultPosition, size = wx.Size( 450,250 ), style = wx.DEFAULT_DIALOG_STYLE )

        #self.SetSizeHints( wx.Size( 450,250 ), wx.DefaultSize )
        self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        fgSizer3 = wx.FlexGridSizer( 0, 3, 0, 0 )
        fgSizer3.SetFlexibleDirection( wx.BOTH )
        fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"Protocol:", wx.DefaultPosition, wx.Size( 60,-1 ), wx.ALIGN_RIGHT )
        self.m_staticText2.Wrap( -1 )

        fgSizer3.Add( self.m_staticText2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.radioSerial = wx.RadioButton( self, wx.ID_ANY, u"Serial - RTU", wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.radioSerial.Bind(wx.EVT_RADIOBUTTON, self.onUIChange)
        fgSizer3.Add( self.radioSerial, 0, wx.ALL, 5 )

        self.radioEthernet = wx.RadioButton( self, wx.ID_ANY, u"Ethernet - TCP", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.radioEthernet.Bind(wx.EVT_RADIOBUTTON, self.onUIChange)
        fgSizer3.Add( self.radioEthernet, 0, wx.ALL, 5 )


        bSizer2.Add( fgSizer3, 1, wx.EXPAND, 5 )

        fgSizer1 = wx.FlexGridSizer( 0, 6, 0, 0 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Slave ID:", wx.DefaultPosition, wx.Size( 60,-1 ), wx.ALIGN_RIGHT )
        self.m_staticText3.Wrap( -1 )

        fgSizer1.Add( self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.txtSlaveID = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 30,-1 ), 0 )
        fgSizer1.Add( self.txtSlaveID, 0, wx.ALL, 5 )

        self.m_staticText51 = wx.StaticText( self, wx.ID_ANY, u"Port:", wx.DefaultPosition, wx.Size( 30,-1 ), wx.ALIGN_RIGHT )
        self.m_staticText51.Wrap( -1 )

        fgSizer1.Add( self.m_staticText51, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.comboSerialPortChoices = []
        self.comboSerialPort = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 130,-1 ), self.comboSerialPortChoices, 0 )
        self.reloadComboChoices(None) # Initialize the com port combo box
        fgSizer1.Add( self.comboSerialPort, 0, wx.ALL, 5 )
        self.comboSerialPort.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.reloadComboChoices)

        self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"Baud:", wx.DefaultPosition, wx.Size( 30,-1 ), wx.ALIGN_RIGHT )
        self.m_staticText4.Wrap( -1 )

        fgSizer1.Add( self.m_staticText4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        comboBaudChoices = [ u"9600", u"14400", u"19200", u"38400", u"57600", u"115200" ]
        self.comboBaud = wx.ComboBox( self, wx.ID_ANY, u"115200", wx.DefaultPosition, wx.Size( 80,-1 ), comboBaudChoices, 0 )
        self.comboBaud.SetSelection( 5 )
        fgSizer1.Add( self.comboBaud, 0, wx.ALL, 5 )


        bSizer2.Add( fgSizer1, 1, wx.EXPAND, 5 )

        self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer2.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

        fgSizer2 = wx.FlexGridSizer( 0, 4, 0, 0 )
        fgSizer2.SetFlexibleDirection( wx.BOTH )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"IP Address:", wx.DefaultPosition, wx.Size( 60,-1 ), wx.ALIGN_RIGHT )
        self.m_staticText5.Wrap( -1 )

        fgSizer2.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.txtIP = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 210,-1 ), 0 )
        fgSizer2.Add( self.txtIP, 0, wx.ALL, 5 )

        self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Port:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )

        fgSizer2.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.txtIpPort = wx.TextCtrl( self, wx.ID_ANY, u"502", wx.DefaultPosition, wx.Size( 80,-1 ), 0 )
        fgSizer2.Add( self.txtIpPort, 0, wx.ALL, 5 )


        bSizer2.Add( fgSizer2, 1, wx.EXPAND, 5 )

        self.btnConnect = wx.Button( self, wx.ID_ANY, u"Connect", wx.Point( -1,-1 ), wx.Size( 150,40 ), 0 )
        self.btnConnect.Bind(wx.EVT_BUTTON, self.onQuit)
        bSizer2.Add( self.btnConnect, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 15 )


        self.SetSizer( bSizer2 )
        self.Layout()

        self.Centre( wx.BOTH )

        self.loadSettings()


    def onUIChange(self, e):
        # Update Dialog items
        if (self.radioSerial.GetValue() == True):
            self.txtIP.Enable(False)
            self.txtIpPort.Enable(False)
            self.txtSlaveID.Enable(True)
            self.comboBaud.Enable(True)
            self.comboSerialPort.Enable(True)
        elif (self.radioEthernet.GetValue() == True):
            self.txtIP.Enable(True)
            self.txtIpPort.Enable(True)
            self.txtSlaveID.Enable(False)
            self.comboBaud.Enable(False)
            self.comboSerialPort.Enable(False)

    def reloadComboChoices(self, event):
         self.comboSerialPort.Clear()
         self.comboSerialPortChoices = {comport.description:comport.device for comport in serial.tools.list_ports.comports()}
         self.comboSerialPort.SetItems(list(self.comboSerialPortChoices.keys()))

    def loadSettings(self):
        # Read settings from connector
        remoteSettings = self.connector.ReadRemoteSettings()
        if remoteSettings != None:
            if (remoteSettings['mode'] == 'TCP'):
                wx.CallAfter(self.radioEthernet.SetValue, True)
            else:
                wx.CallAfter(self.radioSerial.SetValue, True)
            
            wx.CallAfter(self.txtIP.SetValue, remoteSettings['ip'])
            wx.CallAfter(self.txtIpPort.SetValue, str(remoteSettings['ipport']))
            wx.CallAfter(self.txtSlaveID.SetValue, str(remoteSettings['slaveid']))
            wx.CallAfter(self.comboBaud.SetValue, str(remoteSettings['baud']))

            self.reloadComboChoices(None)
            reversedComboSerialPortChoices = {v: k for k, v in self.comboSerialPortChoices.items()}
            portName = reversedComboSerialPortChoices.get(remoteSettings['comport'])
            if portName != None:
                wx.CallAfter(self.comboSerialPort.SetValue, portName)
            else:
                wx.CallAfter(self.comboSerialPort.SetValue, '')

            wx.CallAfter(self.onUIChange, None)

    def onQuit(self, event):
        # Defaults
        mode = 'TCP'
        slaveid = 1
        baud = 115200
        serialPort = 'COM1'
        ip = '127.0.0.1'
        ipport = 502

        if self.radioSerial.GetValue() == True:
            mode = 'RTU'       
            try:
                slaveid = int(str(self.txtSlaveID.GetValue()))
                baud = int(str(self.comboBaud.GetValue()))
                if self.comboSerialPort.GetValue() in self.comboSerialPortChoices:
                    serialPort = str(self.comboSerialPortChoices[self.comboSerialPort.GetValue()])
                else:
                    # Bad serial port selected
                    self.EndModal(-1)
                    return
            except:
                self.EndModal(-1)
                return
        else:
            try:
                ip = str(self.txtIP.GetValue())
                ipport = int(str(self.txtIpPort.GetValue()))
            except:
                self.EndModal(-1)
                return
            
        self.connector.ConfigureRemote(mode, ip, ipport, serialPort, slaveid, baud)

        self.EndModal(0)
        

    def __del__( self ):
        pass
