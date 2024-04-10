import re
import datetime
import threading
import serial.tools.list_ports
from builtins import str as text
from arduino import builder
import util.paths as paths

import wx
import wx.xrc

import time
import os
import platform
import json
import time
import glob

# -------------------------------------------------------------------------------
#                            Arduino Upload Dialog
# -------------------------------------------------------------------------------

class ArduinoUploadDialog(wx.Dialog):
    """Dialog to configure upload parameters"""

    def __init__(self, parent, st_code, arduino_ext, md5):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param st_code: Compiled PLC program as ST code.
        """
        self.plc_program = st_code
        self.arduino_sketch = arduino_ext
        self.md5 = md5
        self.last_update = 0
        self.update_subsystem = True
        current_dir = paths.AbsDir(__file__)
#
        if platform.system() == 'Windows':
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Transfer Program to PLC", pos = wx.DefaultPosition, size = wx.Size( 693,453 ), style = wx.DEFAULT_DIALOG_STYLE )
        elif platform.system() == 'Linux':
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Transfer Program to PLC", pos = wx.DefaultPosition, size = wx.Size( 720,590 ), style = wx.DEFAULT_DIALOG_STYLE )
        elif platform.system() == 'Darwin':
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Transfer Program to PLC", pos = wx.DefaultPosition, size = wx.Size( 700,453 ), style = wx.DEFAULT_DIALOG_STYLE )
        
        # load Hals automatically and initialize the board_type_comboChoices
        self.loadHals()
        board_type_comboChoices = []
        for board in self.hals:
            board_name = ""
            if self.hals[board]['version'] == "0":
                board_name = board + ' [NOT INSTALLED]'
            else:
                board_name = board + ' [' + self.hals[board]['version'] + ']'

            board_type_comboChoices.append(board_name)
        board_type_comboChoices.sort()

        self.SetSizeHintsSz( wx.Size( -1,-1 ), wx.DefaultSize )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.m_listbook2 = wx.Listbook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LB_LEFT )
        m_listbook2ImageSize = wx.Size( 100,100 )
        m_listbook2Index = 0
        m_listbook2Images = wx.ImageList( m_listbook2ImageSize.GetWidth(), m_listbook2ImageSize.GetHeight() )

        self.m_listbook2.AssignImageList( m_listbook2Images )
        self.m_panel5 = wx.Panel( self.m_listbook2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer21 = wx.BoxSizer( wx.VERTICAL )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )




        self.m_staticText1 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Board Type", wx.DefaultPosition, wx.Size( 80,-1 ), 0 )
        self.m_staticText1.Wrap( -1 )
        fgSizer1.Add( self.m_staticText1, 0, wx.ALIGN_CENTER|wx.BOTTOM|wx.LEFT|wx.TOP, 15 )

        self.board_type_combo = wx.ComboBox( self.m_panel5, wx.ID_ANY, u"Arduino Uno", wx.DefaultPosition, wx.Size( 410,-1 ), board_type_comboChoices, 0 )
        fgSizer1.Add( self.board_type_combo, 0, wx.ALIGN_CENTER|wx.BOTTOM|wx.TOP, 15 )
        self.board_type_combo.Bind(wx.EVT_COMBOBOX, self.onUIChange)

        self.m_staticText2 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"COM Port", wx.DefaultPosition, wx.Size( 80,-1 ), 0 )
        self.m_staticText2.Wrap( -1 )
        fgSizer1.Add( self.m_staticText2, 0, wx.ALIGN_CENTER|wx.ALIGN_TOP|wx.BOTTOM|wx.LEFT, 15 )

        self.com_port_combo = wx.ComboBox( self.m_panel5, wx.ID_ANY, u"COM1", wx.DefaultPosition, wx.Size( 410,-1 ), [""], 0 )
        self.reloadComboChoices(None) # Initialize the com port combo box
        fgSizer1.Add( self.com_port_combo, 0, wx.ALIGN_CENTER|wx.BOTTOM, 15 )
        self.com_port_combo.Bind(wx.EVT_COMBOBOX_DROPDOWN, self.reloadComboChoices)


        bSizer21.Add( fgSizer1, 1, wx.EXPAND, 5 )

        self.check_compile = wx.CheckBox( self.m_panel5, wx.ID_ANY, u"Compile Only", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer21.Add( self.check_compile, 0, wx.LEFT, 15 )
        self.check_compile.Bind(wx.EVT_CHECKBOX, self.onUIChange)

        self.m_staticline2 = wx.StaticLine( self.m_panel5, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer21.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )

        self.m_staticText3 = wx.StaticText( self.m_panel5, wx.ID_ANY, u"Compilation output", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText3.Wrap( -1 )
        bSizer21.Add( self.m_staticText3, 0, wx.ALL, 5 )

        self.output_text = wx.TextCtrl( self.m_panel5, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,230 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.VSCROLL )
        self.output_text.SetFont( wx.Font( 10, 75, 90, 90, False, "Consolas" ) )
        self.output_text.SetBackgroundColour( wx.BLACK )
        self.output_text.SetForegroundColour( wx.WHITE )
        self.output_text.SetDefaultStyle(wx.TextAttr(wx.WHITE))

        bSizer21.Add( self.output_text, 0, wx.ALL|wx.EXPAND, 5 )

        self.upload_button = wx.Button( self.m_panel5, wx.ID_ANY, u"Transfer to PLC", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.upload_button.SetMinSize( wx.Size( 150,30 ) )
        self.upload_button.Bind(wx.EVT_BUTTON, self.OnUpload)

        bSizer21.Add( self.upload_button, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.m_panel5.SetSizer( bSizer21 )
        self.m_panel5.Layout()
        bSizer21.Fit( self.m_panel5 )
        self.m_listbook2.AddPage( self.m_panel5, u"Transfer", True )
        m_listbook2Bitmap = wx.Bitmap(os.path.join(current_dir, "..", "images", "transfer_plc.png"), wx.BITMAP_TYPE_ANY )
        if ( m_listbook2Bitmap.IsOk() ):
            m_listbook2Images.Add( m_listbook2Bitmap )
            self.m_listbook2.SetPageImage( m_listbook2Index, m_listbook2Index )
            m_listbook2Index += 1

        self.m_panel6 = wx.Panel( self.m_listbook2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer3 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText4 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"This setting will allow you to change the default pin mapping for your board. Please be cautious while edditing, as mistakes can lead to compilation errors. Pin numbers should obey the Arduino notation for your board and must be comma-separated.", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText4.Wrap( 530 )
        self.m_staticText4.SetMinSize( wx.Size( -1,60 ) )

        bSizer3.Add( self.m_staticText4, 0, wx.ALL, 5 )

        self.m_staticText5 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Digital Inputs", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )
        bSizer3.Add( self.m_staticText5, 0, wx.ALL, 5 )

        self.din_txt = wx.TextCtrl( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.din_txt, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText6 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Digital Outputs", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )
        bSizer3.Add( self.m_staticText6, 0, wx.ALL, 5 )

        self.dout_txt = wx.TextCtrl( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.dout_txt, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText7 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Analog Inputs", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )
        bSizer3.Add( self.m_staticText7, 0, wx.ALL, 5 )

        self.ain_txt = wx.TextCtrl( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.ain_txt, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText8 = wx.StaticText( self.m_panel6, wx.ID_ANY, u"Analog Outputs", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText8.Wrap( -1 )
        bSizer3.Add( self.m_staticText8, 0, wx.ALL, 5 )

        self.aout_txt = wx.TextCtrl( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.aout_txt, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText9 = wx.StaticText( self.m_panel6, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText9.Wrap( -1 )
        self.m_staticText9.SetMinSize( wx.Size( -1,40 ) )

        bSizer3.Add( self.m_staticText9, 0, wx.ALL, 5 )

        gSizer1 = wx.GridSizer( 0, 2, 0, 0 )

        self.m_button2 = wx.Button( self.m_panel6, wx.ID_ANY, u"Restore Defaults", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button2.SetMinSize( wx.Size( 150,30 ) )
        self.m_button2.Bind(wx.EVT_BUTTON, self.restoreIODefaults)

        gSizer1.Add( self.m_button2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.m_button3 = wx.Button( self.m_panel6, wx.ID_ANY, u"Save Changes", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button3.SetMinSize( wx.Size( 150,30 ) )
        self.m_button3.Bind(wx.EVT_BUTTON, self.saveIO)

        gSizer1.Add( self.m_button3, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer3.Add( gSizer1, 1, wx.EXPAND, 5 )


        self.m_panel6.SetSizer( bSizer3 )
        self.m_panel6.Layout()
        bSizer3.Fit( self.m_panel6 )
        self.m_listbook2.AddPage( self.m_panel6, u"I/O Config", False )
        m_listbook2Bitmap = wx.Bitmap(os.path.join(current_dir, "..", "images", "io.png"), wx.BITMAP_TYPE_ANY )
        if ( m_listbook2Bitmap.IsOk() ):
            m_listbook2Images.Add( m_listbook2Bitmap )
            self.m_listbook2.SetPageImage( m_listbook2Index, m_listbook2Index )
            m_listbook2Index += 1

        self.m_panel7 = wx.Panel( self.m_listbook2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer4 = wx.BoxSizer( wx.VERTICAL )

        self.check_modbus_serial = wx.CheckBox( self.m_panel7, wx.ID_ANY, u"Enable Modbus RTU (Serial)", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.check_modbus_serial, 0, wx.ALL, 10 )
        self.check_modbus_serial.Bind(wx.EVT_CHECKBOX, self.onUIChange)

        fgSizer2 = wx.FlexGridSizer( 0, 4, 0, 0 )
        fgSizer2.SetFlexibleDirection( wx.BOTH )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText10 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Interface:", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_staticText10.Wrap( -1 )
        self.m_staticText10.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer2.Add( self.m_staticText10, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        serial_iface_comboChoices = [ u"Serial", u"Serial1", u"Serial2", u"Serial3" ]
        self.serial_iface_combo = wx.ComboBox( self.m_panel7, wx.ID_ANY, u"Serial", wx.DefaultPosition, wx.DefaultSize, serial_iface_comboChoices, wx.CB_READONLY )
        self.serial_iface_combo.SetSelection( 0 )
        self.serial_iface_combo.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer2.Add( self.serial_iface_combo, 0, wx.ALL, 5 )

        self.m_staticText11 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Baud:", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_staticText11.Wrap( -1 )
        self.m_staticText11.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer2.Add( self.m_staticText11, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        baud_rate_comboChoices = [ u"9600", u"14400", u"19200", u"38400", u"57600", u"115200" ]
        self.baud_rate_combo = wx.ComboBox( self.m_panel7, wx.ID_ANY, u"115200", wx.DefaultPosition, wx.DefaultSize, baud_rate_comboChoices, wx.CB_READONLY )
        self.baud_rate_combo.SetSelection( 5 )
        self.baud_rate_combo.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer2.Add( self.baud_rate_combo, 0, wx.ALL, 5 )

        self.m_staticText12 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Slave ID:", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_staticText12.Wrap( -1 )
        self.m_staticText12.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer2.Add( self.m_staticText12, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.slaveid_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.slaveid_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer2.Add( self.slaveid_txt, 0, wx.ALL, 5 )

        self.m_staticText13 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Tx Pin:", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_staticText13.Wrap( -1 )
        self.m_staticText13.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer2.Add( self.m_staticText13, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.txpin_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, u"-1", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.txpin_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer2.Add( self.txpin_txt, 0, wx.ALL, 5 )

        self.m_staticText23 = wx.StaticText( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText23.Wrap( -1 )
        self.m_staticText23.SetMaxSize( wx.Size( -1,15 ) )

        fgSizer2.Add( self.m_staticText23, 0, 0, 5 )


        bSizer4.Add( fgSizer2, 0, wx.EXPAND, 5 )

        self.m_staticline21 = wx.StaticLine( self.m_panel7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer4.Add( self.m_staticline21, 0, wx.ALL|wx.BOTTOM|wx.EXPAND|wx.TOP, 5 )

        self.check_modbus_tcp = wx.CheckBox( self.m_panel7, wx.ID_ANY, u"Enable Modbus TCP", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.check_modbus_tcp, 0, wx.ALL, 10 )
        self.check_modbus_tcp.Bind(wx.EVT_CHECKBOX, self.onUIChange)
        
        fgSizer3 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer3.SetFlexibleDirection( wx.BOTH )
        fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText14 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Interface:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText14.Wrap( -1 )
        self.m_staticText14.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer3.Add( self.m_staticText14, 0, wx.ALL, 5 )

        tcp_iface_comboChoices = [ u"Ethernet", u"WiFi" ]
        self.tcp_iface_combo = wx.ComboBox( self.m_panel7, wx.ID_ANY, u"Ethernet", wx.DefaultPosition, wx.DefaultSize, tcp_iface_comboChoices, wx.CB_READONLY )
        self.tcp_iface_combo.SetSelection( 0 )
        self.tcp_iface_combo.SetMinSize( wx.Size( 440,-1 ) )
        self.tcp_iface_combo.Bind(wx.EVT_COMBOBOX, self.onUIChange)

        fgSizer3.Add( self.tcp_iface_combo, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText15 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"MAC:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText15.Wrap( -1 )
        self.m_staticText15.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer3.Add( self.m_staticText15, 0, wx.ALL, 5 )

        self.mac_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, u"0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.mac_txt.SetMinSize( wx.Size( 440,-1 ) )

        fgSizer3.Add( self.mac_txt, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer4.Add( fgSizer3, 0, wx.EXPAND, 5 )

        fgSizer4 = wx.FlexGridSizer( 0, 4, 0, 0 )
        fgSizer4.SetFlexibleDirection( wx.BOTH )
        fgSizer4.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText17 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"IP:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText17.Wrap( -1 )
        self.m_staticText17.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer4.Add( self.m_staticText17, 0, wx.ALL, 5 )

        self.ip_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.ip_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer4.Add( self.ip_txt, 0, wx.ALL, 5 )

        self.m_staticText18 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"DNS:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText18.Wrap( -1 )
        self.m_staticText18.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer4.Add( self.m_staticText18, 0, wx.ALL, 5 )

        self.dns_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.dns_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer4.Add( self.dns_txt, 0, wx.ALL, 5 )

        self.m_staticText19 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Gateway:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText19.Wrap( -1 )
        self.m_staticText19.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer4.Add( self.m_staticText19, 0, wx.ALL, 5 )

        self.gateway_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.gateway_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer4.Add( self.gateway_txt, 0, wx.ALL, 5 )

        self.m_staticText20 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Subnet:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText20.Wrap( -1 )
        self.m_staticText20.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer4.Add( self.m_staticText20, 0, wx.ALL, 5 )

        self.subnet_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, u"255.255.255.0", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.subnet_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer4.Add( self.subnet_txt, 0, wx.ALL, 5 )

        self.m_staticText21 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Wi-Fi SSID:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText21.Wrap( -1 )
        self.m_staticText21.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer4.Add( self.m_staticText21, 0, wx.ALL, 5 )

        self.wifi_ssid_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.wifi_ssid_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer4.Add( self.wifi_ssid_txt, 0, wx.ALL, 5 )

        self.m_staticText22 = wx.StaticText( self.m_panel7, wx.ID_ANY, u"Password:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText22.Wrap( -1 )
        self.m_staticText22.SetMinSize( wx.Size( 60,-1 ) )

        fgSizer4.Add( self.m_staticText22, 0, wx.ALL, 5 )

        self.wifi_pwd_txt = wx.TextCtrl( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PASSWORD )
        self.wifi_pwd_txt.SetMinSize( wx.Size( 180,-1 ) )

        fgSizer4.Add( self.wifi_pwd_txt, 0, wx.ALL, 5 )

        self.m_staticText24 = wx.StaticText( self.m_panel7, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText24.Wrap( -1 )
        fgSizer4.Add( self.m_staticText24, 0, wx.ALL, 5 )


        bSizer4.Add( fgSizer4, 1, wx.EXPAND, 5 )

        gSizer2 = wx.GridSizer( 0, 2, 0, 0 )

        self.m_button4 = wx.Button( self.m_panel7, wx.ID_ANY, u"Restore Defaults", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button4.SetMinSize( wx.Size( 150,30 ) )

        gSizer2.Add( self.m_button4, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.m_button5 = wx.Button( self.m_panel7, wx.ID_ANY, u"Save Changes", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button5.SetMinSize( wx.Size( 150,30 ) )

        gSizer2.Add( self.m_button5, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer4.Add( gSizer2, 1, wx.EXPAND, 5 )


        self.m_panel7.SetSizer( bSizer4 )
        self.m_panel7.Layout()
        bSizer4.Fit( self.m_panel7 )
        self.m_listbook2.AddPage( self.m_panel7, u"Communications", False )
        m_listbook2Bitmap = wx.Bitmap( os.path.join(current_dir, "..", "images", "comm.png"), wx.BITMAP_TYPE_ANY )
        if ( m_listbook2Bitmap.IsOk() ):
            m_listbook2Images.Add( m_listbook2Bitmap )
            self.m_listbook2.SetPageImage( m_listbook2Index, m_listbook2Index )
            m_listbook2Index += 1


        bSizer2.Add( self.m_listbook2, 1, wx.EXPAND |wx.ALL, 0 )


        self.SetSizer( bSizer2 )
        self.Layout()

        self.Centre( wx.BOTH )

        self.loadSettings()

    def __del__( self ):
        pass

    def reloadComboChoices(self, event):
         self.com_port_combo.Clear()
         self.com_port_combo_choices = {comport.description:comport.device for comport in serial.tools.list_ports.comports()}
         self.com_port_combo.SetItems(list(self.com_port_combo_choices.keys()))

    def onUIChange(self, e):
        # Update Comms
        if (self.check_modbus_serial.GetValue() == False):
            self.serial_iface_combo.Enable(False)
            self.baud_rate_combo.Enable(False)
            self.slaveid_txt.Enable(False)
            self.txpin_txt.Enable(False)
        elif (self.check_modbus_serial.GetValue() == True):
            self.serial_iface_combo.Enable(True)
            self.baud_rate_combo.Enable(True)
            self.slaveid_txt.Enable(True)
            self.txpin_txt.Enable(True)

        if (self.check_compile.GetValue() == False):
            self.com_port_combo.Enable(True)
            self.upload_button.SetLabel("Transfer to PLC")
        elif (self.check_compile.GetValue() == True):
            self.com_port_combo.Enable(False)
            self.upload_button.SetLabel("Compile")
        
        if (self.check_modbus_tcp.GetValue() == False):
            self.tcp_iface_combo.Enable(False)
            self.mac_txt.Enable(False)
            self.ip_txt.Enable(False)
            self.dns_txt.Enable(False)
            self.gateway_txt.Enable(False)
            self.subnet_txt.Enable(False)
            self.wifi_ssid_txt.Enable(False)
            self.wifi_pwd_txt.Enable(False)
        elif (self.check_modbus_tcp.GetValue() == True):
            self.tcp_iface_combo.Enable(True)
            self.mac_txt.Enable(True)
            self.ip_txt.Enable(True)
            self.dns_txt.Enable(True)
            self.gateway_txt.Enable(True)
            self.subnet_txt.Enable(True)
            if (self.tcp_iface_combo.GetValue() == u"Ethernet"):
                self.wifi_ssid_txt.Enable(False)
                self.wifi_pwd_txt.Enable(False)
            elif (self.tcp_iface_combo.GetValue() == u"WiFi"):
                self.wifi_ssid_txt.Enable(True)
                self.wifi_pwd_txt.Enable(True)

        #Update IOs
        board_type = self.board_type_combo.GetValue().split(" [")[0] #remove the trailing [version] on board name
        board_din = self.hals[board_type]['user_din']
        board_ain = self.hals[board_type]['user_ain']
        board_dout = self.hals[board_type]['user_dout']
        board_aout = self.hals[board_type]['user_aout']
        
        self.din_txt.SetValue(str(board_din))
        self.ain_txt.SetValue(str(board_ain))
        self.dout_txt.SetValue(str(board_dout))
        self.aout_txt.SetValue(str(board_aout))

    def restoreIODefaults(self, event):
        board_type = self.board_type_combo.GetValue().split(" [")[0] #remove the trailing [version] on board name
        self.hals[board_type]['user_din'] = self.hals[board_type]['default_din']
        self.hals[board_type]['user_ain'] = self.hals[board_type]['default_ain']
        self.hals[board_type]['user_dout'] = self.hals[board_type]['default_dout']
        self.hals[board_type]['user_aout'] = self.hals[board_type]['default_aout']
        self.saveHals()
        self.onUIChange(None)

    def saveIO(self, event):
        board_type = self.board_type_combo.GetValue().split(" [")[0] #remove the trailing [version] on board name
        self.hals[board_type]['user_din'] = str(self.din_txt.GetValue())
        self.hals[board_type]['user_ain'] = str(self.ain_txt.GetValue())
        self.hals[board_type]['user_dout'] = str(self.dout_txt.GetValue())
        self.hals[board_type]['user_aout'] = str(self.aout_txt.GetValue())
        self.saveHals()

    def startBuilder(self):

        # Get platform and source_file from hals
        board_type = self.board_type_combo.GetValue().split(" [")[0] #remove the trailing [version] on board name
        platform = self.hals[board_type]['platform']
        source = self.hals[board_type]['source']
        
        self.generateDefinitionsFile()

        port = "None" #invalid port
        if (self.check_compile.GetValue() == True):
            port = None
        elif self.com_port_combo.GetValue() in self.com_port_combo_choices:
            port = self.com_port_combo_choices[self.com_port_combo.GetValue()]
        
        compiler_thread = threading.Thread(target=builder.build, args=(self.plc_program, platform, source, port, self.output_text, self.update_subsystem))
        compiler_thread.start()
        compiler_thread.join()
        wx.CallAfter(self.upload_button.Enable, True)   
        if (self.update_subsystem):
            self.update_subsystem = False
            self.last_update = time.time()
        self.saveSettings()


    def OnUpload(self, event):
        self.upload_button.Enable(False)
        builder_thread = threading.Thread(target=self.startBuilder)
        builder_thread.start()
    
    def generateDefinitionsFile(self):

        if platform.system() == 'Windows':
            base_path = 'editor\\arduino\\examples\\Baremetal\\'
        else:
            base_path = 'editor/arduino/examples/Baremetal/'
        
        #Store program MD5 on target
        define_file = '//Program MD5\n'
        define_file += '#define PROGRAM_MD5 "' + str(self.md5) + '"\n'

        #Generate Communication Config defines
        define_file += '//Comms configurations\n'

        define_file += '#define MBSERIAL_IFACE ' + str(self.serial_iface_combo.GetValue()) + '\n'
        define_file += '#define MBSERIAL_BAUD ' + str(self.baud_rate_combo.GetValue()) + '\n'
        define_file += '#define MBSERIAL_SLAVE ' + str(self.slaveid_txt.GetValue()) + '\n'
        define_file += '#define MBTCP_MAC ' + str(self.mac_txt.GetValue()) + '\n'
        define_file += '#define MBTCP_IP ' + str(self.ip_txt.GetValue()).replace('.',',') + '\n'
        define_file += '#define MBTCP_DNS ' + str(self.dns_txt.GetValue()).replace('.',',') + '\n'
        define_file += '#define MBTCP_GATEWAY ' + str(self.gateway_txt.GetValue()).replace('.',',') + '\n'
        define_file += '#define MBTCP_SUBNET ' + str(self.subnet_txt.GetValue()).replace('.',',') + '\n'
        define_file += '#define MBTCP_SSID "' + str(self.wifi_ssid_txt.GetValue()) + '"\n'
        define_file += '#define MBTCP_PWD "' + str(self.wifi_pwd_txt.GetValue()) + '"\n'

        if (self.check_modbus_serial.GetValue() == True):
            define_file += '#define MBSERIAL\n'
            define_file += '#define MODBUS_ENABLED\n'
        
        if (self.txpin_txt.GetValue() != '-1'):
            define_file += '#define MBSERIAL_TXPIN ' + str(self.txpin_txt.GetValue()) + '\n'
            
        if (self.check_modbus_tcp.GetValue() == True):
            define_file += '#define MBTCP\n'
            define_file += '#define MODBUS_ENABLED\n'
            if (self.tcp_iface_combo.GetValue() == u"Ethernet"):
                define_file += '#define MBTCP_ETHERNET\n'
            elif (self.tcp_iface_combo.GetValue() == u'WiFi'):
                define_file += '#define MBTCP_WIFI\n'

        #Generate IO Config defines
        define_file += '\n\n//IO Config\n'
        define_file += '#define PINMASK_DIN ' + str(self.din_txt.GetValue()) + '\n'
        define_file += '#define PINMASK_AIN ' + str(self.ain_txt.GetValue()) + '\n'
        define_file += '#define PINMASK_DOUT ' + str(self.dout_txt.GetValue()) + '\n'
        define_file += '#define PINMASK_AOUT ' + str(self.aout_txt.GetValue()) + '\n'
        define_file += '#define NUM_DISCRETE_INPUT ' + str(len(str(self.din_txt.GetValue()).split(','))) + '\n'
        define_file += '#define NUM_ANALOG_INPUT ' + str(len(str(self.ain_txt.GetValue()).split(','))) + '\n'
        define_file += '#define NUM_DISCRETE_OUTPUT ' + str(len(str(self.dout_txt.GetValue()).split(','))) + '\n'
        define_file += '#define NUM_ANALOG_OUTPUT ' + str(len(str(self.aout_txt.GetValue()).split(','))) + '\n'
        
        # Get define from hals
        board_type = self.board_type_combo.GetValue().split(" [")[0]
        if 'define' in self.hals[board_type]:
            define_file += '#define '+ self.hals[board_type]['define'] +'\n'
        
        define_file += '\n\n//Arduino Libraries\n'

        #Generate Arduino Libraries defines
        if (self.plc_program.find('DS18B20;') > 0) or (self.plc_program.find('DS18B20_2_OUT;') > 0) or (self.plc_program.find('DS18B20_3_OUT;') > 0) or (self.plc_program.find('DS18B20_4_OUT;') > 0) or (self.plc_program.find('DS18B20_5_OUT;') > 0):
            define_file += '#define USE_DS18B20_BLOCK\n'
        if (self.plc_program.find('P1AM_INIT;') > 0):
            define_file += '#define USE_P1AM_BLOCKS\n'
        if (self.plc_program.find('CLOUD_BEGIN;') > 0):
            define_file += '#define USE_CLOUD_BLOCKS\n'
        if (self.plc_program.find('MQTT_CONNECT;') > 0) or (self.plc_program.find('MQTT_CONNECT_AUTH;') > 0):
            define_file += '#define USE_MQTT_BLOCKS\n'
        if (self.plc_program.find('ARDUINOCAN_CONF;') > 0):
            define_file += '#define USE_ARDUINOCAN_BLOCK\n'
        if (self.plc_program.find('ARDUINOCAN_WRITE;') > 0):
            define_file += '#define USE_ARDUINOCAN_BLOCK\n'
        if (self.plc_program.find('ARDUINOCAN_WRITE_WORD;') > 0):
            define_file += '#define USE_ARDUINOCAN_BLOCK\n'
        if (self.plc_program.find('ARDUINOCAN_READ;') > 0):
            define_file += '#define USE_ARDUINOCAN_BLOCK\n'

        #Generate Arduino Extension (sketch) define
        if self.arduino_sketch != None:
            define_file += '#define USE_ARDUINO_SKETCH\n'
            define_file += '#define ARDUINO_PLATFORM\n'
            #Copy the sketch contents to the .h file
            f = open(os.path.join(base_path, 'ext', 'arduino_sketch.h'), 'w')
            f.write(self.arduino_sketch)

        #Write file to disk
        f = open(base_path+'defines.h', 'w')
        f.write(define_file)
        f.flush()
        f.close()

    def saveSettings(self):
        settings = {}
        settings['board_type'] = self.board_type_combo.GetValue()
        settings['com_port'] = self.com_port_combo.GetValue()
        settings['mb_serial'] = self.check_modbus_serial.GetValue()
        settings['serial_iface'] = self.serial_iface_combo.GetValue()
        settings['baud'] = self.baud_rate_combo.GetValue()
        settings['slaveid'] = self.slaveid_txt.GetValue()
        settings['txpin'] = self.txpin_txt.GetValue()
        settings['mb_tcp'] = self.check_modbus_tcp.GetValue()
        settings['tcp_iface'] = self.tcp_iface_combo.GetValue()
        settings['mac'] = self.mac_txt.GetValue()
        settings['ip'] = self.ip_txt.GetValue()
        settings['dns'] = self.dns_txt.GetValue()
        settings['gateway'] = self.gateway_txt.GetValue()
        settings['subnet'] = self.subnet_txt.GetValue()
        settings['ssid'] = self.wifi_ssid_txt.GetValue()
        settings['pwd'] = self.wifi_pwd_txt.GetValue()
        settings['last_update'] = self.last_update

        #write settings to disk
        jsonStr = json.dumps(settings)
        if platform.system() == 'Windows':
            base_path = 'editor\\arduino\\examples\\Baremetal\\'
        else:
            base_path = 'editor/arduino/examples/Baremetal/'
        f = open(base_path+'settings.json', 'w')
        f.write(jsonStr)
        f.flush()
        f.close()


    def loadSettings(self):
        #read settings from disk
        if platform.system() == 'Windows':
            base_path = 'editor\\arduino\\examples\\Baremetal\\'
        else:
            base_path = 'editor/arduino/examples/Baremetal/'
        if (os.path.exists(base_path+'settings.json')):
            f = open(base_path+'settings.json', 'r')
            jsonStr = f.read()
            f.close()

            settings = json.loads(jsonStr)

            #Check if should update subsystem
            if ('last_update' in settings.keys()):
                self.last_update = settings['last_update']
                if (time.time() - float(self.last_update) > 604800.0): #604800 is the number of seconds in a week (7 days)
                    self.update_subsystem = True
                    self.last_update = time.time()
                else:
                    self.update_subsystem = False
            else:
                self.update_subsystem = True
                self.last_update = time.time()

            wx.CallAfter(self.board_type_combo.SetValue, settings['board_type'])
            wx.CallAfter(self.com_port_combo.SetValue, settings['com_port'])
            wx.CallAfter(self.check_modbus_serial.SetValue, settings['mb_serial'])
            wx.CallAfter(self.serial_iface_combo.SetValue, settings['serial_iface'])
            wx.CallAfter(self.baud_rate_combo.SetValue, settings['baud'])
            wx.CallAfter(self.slaveid_txt.SetValue, settings['slaveid'])
            wx.CallAfter(self.txpin_txt.SetValue, settings['txpin'])
            wx.CallAfter(self.check_modbus_tcp.SetValue, settings['mb_tcp'])
            wx.CallAfter(self.tcp_iface_combo.SetValue, settings['tcp_iface'])
            wx.CallAfter(self.mac_txt.SetValue, settings['mac'])
            wx.CallAfter(self.ip_txt.SetValue, settings['ip'])
            wx.CallAfter(self.dns_txt.SetValue, settings['dns'])
            wx.CallAfter(self.gateway_txt.SetValue, settings['gateway'])
            wx.CallAfter(self.subnet_txt.SetValue, settings['subnet'])
            wx.CallAfter(self.wifi_ssid_txt.SetValue, settings['ssid'])
            wx.CallAfter(self.wifi_pwd_txt.SetValue, settings['pwd'])

            wx.CallAfter(self.onUIChange, None)
    
    def loadHals(self):
        # load hals list from json file, or construct it
        if platform.system() == 'Windows':
            jfile = 'editor\\arduino\\examples\\Baremetal\\hals.json'
        else:
            jfile = 'editor/arduino/examples/Baremetal/hals.json'
        
        f = open(jfile, 'r')
        jsonStr = f.read()
        f.close()
        self.hals = json.loads(jsonStr)

    def saveHals(self):
        jsonStr = json.dumps(self.hals)
        if platform.system() == 'Windows':
            jfile = 'editor\\arduino\\examples\\Baremetal\\hals.json'
        else:
            jfile = 'editor/arduino/examples/Baremetal/hals.json'
        f = open(jfile, 'w')
        f.write(jsonStr)
        f.flush()
        f.close()
