from __future__ import absolute_import
import re
import datetime
import threading
import serial.tools.list_ports
from builtins import str as text
from arduino import builder

import wx
import wx.xrc

import time
import os
import json
import time
import glob

# -------------------------------------------------------------------------------
#                            Arduino Upload Dialog
# -------------------------------------------------------------------------------

class ArduinoUploadDialog(wx.Dialog):
    """Dialog to configure upload parameters"""

    def __init__(self, parent, st_code):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param st_code: Compiled PLC program as ST code.
        """
        self.plc_program = st_code
        self.last_update = 0
        self.update_subsystem = True

        if os.name == 'nt':
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Upload to Arduino Board", pos = wx.DefaultPosition, size = wx.Size( 400,640 ), style = wx.DEFAULT_DIALOG_STYLE )
        else:
            wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Upload to Arduino Board", pos = wx.DefaultPosition, size = wx.Size( 480,820 ), style = wx.DEFAULT_DIALOG_STYLE )

        # load Hals automatically and initialize the board_type_comboChoices
        self.loadHals()
        board_type_comboChoices = []
        for board in self.hals:
            board_type_comboChoices.append(board)
        board_type_comboChoices.sort()

        self.SetSizeHintsSz( wx.Size( -1,-1 ), wx.DefaultSize )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer1.SetFlexibleDirection( wx.HORIZONTAL )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.board_type_lbl = wx.StaticText( self, wx.ID_ANY, u"Board Type:", wx.Point( -1,-1 ), wx.Size( 65,-1 ), wx.ALIGN_LEFT )
        self.board_type_lbl.Wrap( -1 )
        fgSizer1.Add( self.board_type_lbl, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        self.board_type_combo = wx.ComboBox( self, wx.ID_ANY, u"Uno", wx.DefaultPosition, wx.Size( 300,-1 ), board_type_comboChoices, wx.CB_READONLY )
        self.board_type_combo.SetSelection( 0 )
        fgSizer1.Add( self.board_type_combo, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.mode_lbl = wx.StaticText( self, wx.ID_ANY, u"Mode:", wx.DefaultPosition, wx.Size( 65,-1 ), 0)
        self.mode_lbl.Wrap( -1 )
        fgSizer1.Add( self.mode_lbl, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        self.check_compile = wx.CheckBox( self, wx.ID_ANY, u"Compile Only", wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer1.Add( self.check_compile, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        self.check_compile.Bind(wx.EVT_CHECKBOX, self.onUIChange)
        

        self.com_port_lbl = wx.StaticText( self, wx.ID_ANY, u"COM Port:", wx.DefaultPosition, wx.Size( 65,-1 ), 0 )
        self.com_port_lbl.Wrap( -1 )
        fgSizer1.Add( self.com_port_lbl, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        com_port_comboChoices = [comport.device for comport in serial.tools.list_ports.comports()]
        self.com_port_combo = wx.ComboBox( self, wx.ID_ANY, u"COM1", wx.DefaultPosition, wx.Size( 300,-1 ), com_port_comboChoices, wx.CB_READONLY )
        self.com_port_combo.SetSelection( 0 )
        fgSizer1.Add( self.com_port_combo, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        bSizer2.Add( fgSizer1, 0, wx.EXPAND|wx.TOP, 5 )

        self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer2.Add( self.m_staticline1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 10 )

        self.check_modbus_serial = wx.CheckBox( self, wx.ID_ANY, u"Enable Modbus RTU (Serial)", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.check_modbus_serial, 0, wx.ALL, 10 )
        self.check_modbus_serial.Bind(wx.EVT_CHECKBOX, self.onUIChange)

        fgSizer2 = wx.FlexGridSizer( 0, 4, 0, 0 )
        fgSizer2.SetFlexibleDirection( wx.BOTH )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"Interface:", wx.DefaultPosition, wx.Size( 65,-1 ), 0 )
        self.m_staticText5.Wrap( -1 )
        fgSizer2.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        serial_iface_comboChoices = [ u"Serial", u"Serial1", u"Serial2", u"Serial3" ]
        self.serial_iface_combo = wx.ComboBox( self, wx.ID_ANY, u"Serial", wx.DefaultPosition, wx.Size( 108,-1 ), serial_iface_comboChoices, wx.CB_READONLY )
        self.serial_iface_combo.SetSelection( 0 )
        fgSizer2.Add( self.serial_iface_combo, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5 )

        self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Baud:", wx.DefaultPosition, wx.Size( 60,-1 ), 0 )
        self.m_staticText6.Wrap( -1 )
        fgSizer2.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        baud_rate_comboChoices = [ u"9600", u"14400", u"19200", u"38400", u"57600", u"115200" ]
        self.baud_rate_combo = wx.ComboBox( self, wx.ID_ANY, u"115200", wx.DefaultPosition, wx.Size( 108,-1 ), baud_rate_comboChoices, wx.CB_READONLY )
        self.baud_rate_combo.SetSelection( 5 )
        fgSizer2.Add( self.baud_rate_combo, 0, wx.ALL, 5 )

        self.m_staticText51 = wx.StaticText( self, wx.ID_ANY, u"Slave ID:", wx.DefaultPosition, wx.Size( 65,-1 ), 0 )
        self.m_staticText51.Wrap( -1 )
        fgSizer2.Add( self.m_staticText51, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.LEFT, 10 )

        self.slaveid_txt = wx.TextCtrl( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.Size( 105,-1 ), 0 )
        fgSizer2.Add( self.slaveid_txt, 0, wx.ALL, 5 )

        self.m_staticText61 = wx.StaticText( self, wx.ID_ANY, u"Tx Pin:", wx.DefaultPosition, wx.Size( 60,-1 ), 0 )
        self.m_staticText61.Wrap( -1 )
        fgSizer2.Add( self.m_staticText61, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.LEFT, 10 )

        self.txpin_txt = wx.TextCtrl( self, wx.ID_ANY, u"-1", wx.DefaultPosition, wx.Size( 105,-1 ), 0 )
        fgSizer2.Add( self.txpin_txt, 0, wx.ALL, 5 )

        bSizer2.Add( fgSizer2, 0, wx.EXPAND, 5 )

        self.m_staticline11 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer2.Add( self.m_staticline11, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 10 )

        self.check_modbus_tcp = wx.CheckBox( self, wx.ID_ANY, u"Enable Modbus TCP", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2.Add( self.check_modbus_tcp, 0, wx.ALL, 10 )
        self.check_modbus_tcp.Bind(wx.EVT_CHECKBOX, self.onUIChange)

        fgSizer3 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer3.SetFlexibleDirection( wx.BOTH )
        fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"Interface:", wx.DefaultPosition, wx.Size( 65,-1 ), 0 )
        self.m_staticText9.Wrap( -1 )
        fgSizer3.Add( self.m_staticText9, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        tcp_iface_comboChoices = [ u"Ethernet", u"WiFi" ]
        self.tcp_iface_combo = wx.ComboBox( self, wx.ID_ANY, u"Ethernet", wx.DefaultPosition, wx.Size( 300,-1 ), tcp_iface_comboChoices, wx.CB_READONLY )
        self.tcp_iface_combo.SetSelection( 0 )
        fgSizer3.Add( self.tcp_iface_combo, 0, wx.ALL, 5 )
        self.tcp_iface_combo.Enable(False)
        self.tcp_iface_combo.Bind(wx.EVT_COMBOBOX, self.onUIChange)

        self.m_staticText91 = wx.StaticText( self, wx.ID_ANY, u"MAC:", wx.DefaultPosition, wx.Size( 65,-1 ), 0 )
        self.m_staticText91.Wrap( -1 )
        fgSizer3.Add( self.m_staticText91, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        self.mac_txt = wx.TextCtrl( self, wx.ID_ANY, u"0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD", wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
        fgSizer3.Add( self.mac_txt, 0, wx.ALL, 5 )
        self.mac_txt.Enable(False)

        bSizer2.Add( fgSizer3, 0, wx.EXPAND, 5 )

        fgSizer5 = wx.FlexGridSizer( 0, 4, 0, 5 )
        fgSizer5.SetFlexibleDirection( wx.BOTH )
        fgSizer5.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText111 = wx.StaticText( self, wx.ID_ANY, u"IP:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText111.Wrap( -1 )
        fgSizer5.Add( self.m_staticText111, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        self.ip_txt = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer5.Add( self.ip_txt, 0, wx.ALL, 5 )
        self.ip_txt.Enable(False)

        self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"DNS:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText12.Wrap( -1 )
        fgSizer5.Add( self.m_staticText12, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.dns_txt = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 118,-1 ), 0 )
        fgSizer5.Add( self.dns_txt, 0, wx.ALL, 5 )
        self.dns_txt.Enable(False)

        self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"Gateway:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText13.Wrap( -1 )
        fgSizer5.Add( self.m_staticText13, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        self.gateway_txt = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer5.Add( self.gateway_txt, 0, wx.ALL, 5 )
        self.gateway_txt.Enable(False)

        self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"Subnet:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText14.Wrap( -1 )
        fgSizer5.Add( self.m_staticText14, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.subnet_txt = wx.TextCtrl( self, wx.ID_ANY, u"255.255.255.0", wx.DefaultPosition, wx.Size( 118,-1 ), 0 )
        fgSizer5.Add( self.subnet_txt, 0, wx.ALL, 5 )
        self.subnet_txt.Enable(False)

        self.m_staticText10 = wx.StaticText( self, wx.ID_ANY, u"Wi-Fi SSID:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText10.Wrap( -1 )
        fgSizer5.Add( self.m_staticText10, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10 )

        self.wifi_ssid_txt = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        fgSizer5.Add( self.wifi_ssid_txt, 0, wx.ALL|wx.EXPAND, 5 )
        self.wifi_ssid_txt.Enable(False)

        self.m_staticText11 = wx.StaticText( self, wx.ID_ANY, u"Password:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11.Wrap( -1 )
        fgSizer5.Add( self.m_staticText11, 0, wx.ALIGN_CENTER_VERTICAL, 5 )

        self.wifi_pwd_txt = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 118,-1 ), wx.TE_PASSWORD )
        fgSizer5.Add( self.wifi_pwd_txt, 0, wx.ALL, 5 )
        self.wifi_pwd_txt.Enable(False)


        bSizer2.Add( fgSizer5, 0, wx.EXPAND, 5 )

        self.output_lbl = wx.StaticText( self, wx.ID_ANY, u"Compilation output:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.output_lbl.Wrap( -1 )
        bSizer2.Add( self.output_lbl, 0, wx.BOTTOM|wx.LEFT|wx.TOP, 10 )

        self.output_text = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.VSCROLL )
        self.output_text.SetFont( wx.Font( 8, 75, 90, 90, False, "Consolas" ) )
        self.output_text.SetForegroundColour( wx.Colour( 255, 255, 255 ) )
        self.output_text.SetBackgroundColour( wx.Colour( 0, 0, 0 ) )
        self.output_text.SetMinSize( wx.Size( -1,75 ) )

        bSizer2.Add( self.output_text, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10 )

        gSizer3 = wx.GridSizer( 0, 2, 0, 0 )

        gSizer3.SetMinSize( wx.Size( -1,45 ) ) 
        self.upload_button = wx.Button( self, wx.ID_ANY, u"Upload", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        gSizer3.Add( self.upload_button, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL|wx.EXPAND, 5 )
        self.upload_button.Bind(wx.EVT_BUTTON, self.OnUpload)

        self.cancel_button = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        gSizer3.Add( self.cancel_button, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL|wx.EXPAND, 5 )
        self.cancel_button.Bind(wx.EVT_BUTTON, self.OnCancel)


        bSizer2.Add( gSizer3, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 5 )


        self.SetSizer( bSizer2 )
        self.Layout()

        self.Centre( wx.BOTH )

        self.loadSettings()

    def __del__( self ):
        pass

    def onUIChange(self, e):
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
            self.upload_button.SetLabel("Upload")
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

    def OnCancel(self, event):
        self.EndModal(wx.ID_OK)

    def startBuilder(self):

        # Get platform and source_file from hals
        board_type = self.board_type_combo.GetValue()
        platform = self.hals[board_type]['platform']
        source = self.hals[board_type]['source']
        
        self.generateDefinitionsFile()

        port = self.com_port_combo.GetValue()
        if (self.check_compile.GetValue() == True):
            port = None
        
        compiler_thread = threading.Thread(target=builder.build, args=(self.plc_program, platform, source, port, self.output_text, self.update_subsystem))
        compiler_thread.start()
        compiler_thread.join()
        wx.CallAfter(self.upload_button.Enable, True)
        wx.CallAfter(self.cancel_button.Enable, True)        
        if (self.update_subsystem):
            self.update_subsystem = False
            self.last_update = time.time()
        self.saveSettings()


    def OnUpload(self, event):
        self.upload_button.Enable(False)
        self.cancel_button.Enable(False)
        builder_thread = threading.Thread(target=self.startBuilder)
        builder_thread.start()
    
    def generateDefinitionsFile(self):
        #Generate Communication Config defines
        define_file = '//Comms configurations\n'

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
        
        # Get define from hals
        if 'define' in self.hals[self.board_type_combo.GetValue()]:
            define_file += '#define '+ self.hals[self.board_type_combo.GetValue()]['define'] +'\n'
        
        define_file += '\n\n//Arduino Libraries\n'

        #Generate Arduino Libraries defines
        if (self.plc_program.find('DS18B20;') > 0) or (self.plc_program.find('DS18B20_2_OUT;') > 0) or (self.plc_program.find('DS18B20_3_OUT;') > 0) or (self.plc_program.find('DS18B20_4_OUT;') > 0) or (self.plc_program.find('DS18B20_5_OUT;') > 0):
            define_file += '#define USE_DS18B20_BLOCK\n'
        if (self.plc_program.find('P1AM_INIT;') > 0):
            define_file += '#define USE_P1AM_BLOCKS\n'
        if (self.plc_program.find('CLOUD_BEGIN;') > 0):
            define_file += '#define USE_CLOUD_BLOCKS\n'

        #Write file to disk
        if (os.name == 'nt'):
            base_path = 'editor\\arduino\\examples\\Baremetal\\'
        else:
            base_path = 'editor/arduino/examples/Baremetal/'
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
        if (os.name == 'nt'):
            base_path = 'editor\\arduino\\examples\\Baremetal\\'
        else:
            base_path = 'editor/arduino/examples/Baremetal/'
        f = open(base_path+'settings.json', 'w')
        f.write(jsonStr)
        f.flush()
        f.close()


    def loadSettings(self):
        #read settings from disk
        if (os.name == 'nt'):
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
        if (os.name == 'nt'):
            jfile = 'editor\\arduino\\examples\\Baremetal\\hals.json'
        else:
            jfile = 'editor/arduino/examples/Baremetal/hals.json'
        
        f = open(jfile, 'r')
        jsonStr = f.read()
        f.close()
        self.hals = json.loads(jsonStr)
