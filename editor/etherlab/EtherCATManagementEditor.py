#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
#
# Copyright (C) 2013: Real-Time & Embedded Systems (RTES) Lab., University of Seoul
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
from __future__ import division
import os
import string
from xml.dom import minidom

import wx
import wx.grid
import wx.gizmos
import wx.lib.buttons

# --------------------------------------------------------------------
from controls import CustomGrid, CustomTable
from runtime import PlcStatus
# --------------------------------------------------------------------

# ------------ for register management ---------------

from util.TranslationCatalogs import NoTranslate
# -------------------------------------------------------------


# ----------------------------- For Sync Manager Table -----------------------------------
def GetSyncManagersTableColnames():
    """
    Returns column names of SyncManager Table in Slave state panel.
    """
    _ = NoTranslate
    return ["#", _("Name"), _("Start Address"), _("Default Size"), _("Control Byte"), _("Enable")]


# -------------------------------------------------------------------------------
#                    Sync Managers Table
# -------------------------------------------------------------------------------
class SyncManagersTable(CustomTable):
    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            if col == 0:
                return row
            return self.data[row].get(self.GetColLabelValue(col, False), "")


# -------------------------------------------------------------------------------
#                    EtherCAT Management Treebook
# -------------------------------------------------------------------------------
class EtherCATManagementTreebook(wx.Treebook):
    def __init__(self, parent, controler, node_editor):
        """
        Constructor
        @param parent: Reference to the parent wx.ScrolledWindow object
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        @param node_editor: Reference to Beremiz frame
        """
        wx.Treebook.__init__(self, parent, -1, size=wx.DefaultSize, style=wx.BK_DEFAULT)
        self.parent = parent
        self.Controler = controler
        self.NodeEditor = node_editor

        self.EtherCATManagementClassObject = {}

        # fill EtherCAT Management Treebook
        panels = [
            ("Slave State",        SlaveStatePanelClass, []),
            ("SDO Management",     SDOPanelClass, []),
            ("PDO Monitoring",     PDOPanelClass, []),
            ("ESC Management",     EEPROMAccessPanel, [
                ("Smart View", SlaveSiiSmartView),
                ("Hex View", HexView)]),
            ("Register Access",     RegisterAccessPanel, [])
        ]
        for pname, pclass, subs in panels:
            self.AddPage(pclass(self, self.Controler), pname)
            for spname, spclass in subs:
                self.AddSubPage(spclass(self, self.Controler), spname)


# -------------------------------------------------------------------------------
#                    For SlaveState Panel
# -------------------------------------------------------------------------------
class SlaveStatePanelClass(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent EtherCATManagementTreebook class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1, (0, 0), size=wx.DefaultSize, style=wx.SUNKEN_BORDER)
        self.Controler = controler
        self.parent = parent

        # initialize SlaveStatePanel UI dictionaries
        self.StaticBoxDic = {}
        self.StaticTextDic = {}
        self.TextCtrlDic = {}
        self.ButtonDic = {}

        # iniitalize BoxSizer and FlexGridSizer
        self.SizerDic = {
            "SlaveState_main_sizer": wx.BoxSizer(wx.VERTICAL),
            "SlaveState_inner_main_sizer": wx.FlexGridSizer(cols=1, hgap=50, rows=3, vgap=10),
            "SlaveInfosDetailsInnerSizer": wx.FlexGridSizer(cols=4, hgap=10, rows=2, vgap=10),
            "SyncManagerInnerSizer": wx.FlexGridSizer(cols=1, hgap=5, rows=1, vgap=5),
            "SlaveState_sizer": wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10),
            "SlaveState_up_sizer": wx.FlexGridSizer(cols=4, hgap=10, rows=2, vgap=10),
            "SlaveState_down_sizer": wx.FlexGridSizer(cols=2, hgap=10, rows=1, vgap=10)}

        # initialize StaticBox and StaticBoxSizer
        for box_name, box_label in [
                ("SlaveInfosDetailsBox", "Slave Informations"),
                ("SyncManagerBox", "Sync Manager"),
                ("SlaveStateBox", "Slave State Transition && Monitoring")]:
            self.StaticBoxDic[box_name] = wx.StaticBox(self, label=_(box_label))
            self.SizerDic[box_name] = wx.StaticBoxSizer(self.StaticBoxDic[box_name])

        for statictext_name, statictext_label, textctrl_name in [
                ("VendorLabel", "Vendor:", "vendor"),
                ("ProductcodeLabel", "Product code:", "product_code"),
                ("RevisionnumberLabel", "Slave Count:", "revision_number"),
                ("PhysicsLabel", "Physics:", "physics")]:
            self.StaticTextDic[statictext_name] = wx.StaticText(self, label=_(statictext_label))
            self.TextCtrlDic[textctrl_name] = wx.TextCtrl(self, size=wx.Size(130, 24), style=wx.TE_READONLY)
            self.SizerDic["SlaveInfosDetailsInnerSizer"].AddMany([self.StaticTextDic[statictext_name],
                                                                  self.TextCtrlDic[textctrl_name]])

        self.SizerDic["SlaveInfosDetailsBox"].AddSizer(self.SizerDic["SlaveInfosDetailsInnerSizer"])

        self.SyncManagersGrid = CustomGrid(self, size=wx.Size(605, 155), style=wx.VSCROLL)

        self.SizerDic["SyncManagerInnerSizer"].Add(self.SyncManagersGrid)
        self.SizerDic["SyncManagerBox"].Add(self.SizerDic["SyncManagerInnerSizer"])

        buttons = [
            ("InitButton",   0, "INIT", "State Transition to \"Init\" State",     self.OnButtonClick, []),
            ("PreOPButton",  1, "PREOP", "State Transition to \"PreOP\" State",   self.OnButtonClick, [
                ("TargetStateLabel", "Target State:", "TargetState")]),
            ("SafeOPButton", 2, "SAFEOP", "State Transition to \"SafeOP\" State", self.OnButtonClick, []),
            ("OPButton",     3, "OP",  "State Transition to \"OP\" State",        self.OnButtonClick, [
                ("CurrentStateLabel", "Current State:", "CurrentState")])
        ]
        for button_name, button_id, button_label, button_tooltipstring, event_method, sub_item in buttons:
            self.ButtonDic[button_name] = wx.Button(self, id=button_id, label=_(button_label))
            self.ButtonDic[button_name].Bind(wx.EVT_BUTTON, event_method)
            self.ButtonDic[button_name].SetToolTipString(button_tooltipstring)
            self.SizerDic["SlaveState_up_sizer"].Add(self.ButtonDic[button_name])
            for statictext_name, statictext_label, textctrl_name in sub_item:
                self.StaticTextDic[statictext_name] = wx.StaticText(self, label=_(statictext_label))
                self.TextCtrlDic[textctrl_name] = wx.TextCtrl(self, size=wx.DefaultSize, style=wx.TE_READONLY)
                self.SizerDic["SlaveState_up_sizer"].AddMany([self.StaticTextDic[statictext_name],
                                                              self.TextCtrlDic[textctrl_name]])

        for button_name, button_label, button_tooltipstring, event_method in [
                ("StartTimerButton", "Start State Monitoring", "Slave State Update Restart", self.StartTimer),
                ("StopTimerButton", "Stop State Monitoring", "Slave State Update Stop", self.CurrentStateThreadStop)]:
            self.ButtonDic[button_name] = wx.Button(self, label=_(button_label))
            self.ButtonDic[button_name].Bind(wx.EVT_BUTTON, event_method)
            self.ButtonDic[button_name].SetToolTipString(button_tooltipstring)
            self.SizerDic["SlaveState_down_sizer"].Add(self.ButtonDic[button_name])

        self.SizerDic["SlaveState_sizer"].AddMany([self.SizerDic["SlaveState_up_sizer"],
                                                   self.SizerDic["SlaveState_down_sizer"]])

        self.SizerDic["SlaveStateBox"].Add(self.SizerDic["SlaveState_sizer"])

        self.SizerDic["SlaveState_inner_main_sizer"].AddMany([
            self.SizerDic["SlaveInfosDetailsBox"], self.SizerDic["SyncManagerBox"],
            self.SizerDic["SlaveStateBox"]])

        self.SizerDic["SlaveState_main_sizer"].Add(self.SizerDic["SlaveState_inner_main_sizer"])

        self.SetSizer(self.SizerDic["SlaveState_main_sizer"])

        # register a timer for periodic exectuion of slave state update (period: 1000 ms)
        self.Bind(wx.EVT_TIMER, self.GetCurrentState)

        self.CreateSyncManagerTable()

        self.Centre()

    def CreateSyncManagerTable(self):
        """
        Create grid for "SyncManager"
        """
        # declare Table object
        self.SyncManagersTable = SyncManagersTable(self, [], GetSyncManagersTableColnames())
        self.SyncManagersGrid.SetTable(self.SyncManagersTable)
        # set grid alignment attr. (CENTER)
        self.SyncManagersGridColAlignements = [wx.ALIGN_CENTRE, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE,
                                               wx.ALIGN_CENTRE, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE]
        # set grid size
        self.SyncManagersGridColSizes = [40, 150, 100, 100, 100, 100]
        self.SyncManagersGrid.SetRowLabelSize(0)
        for col in range(self.SyncManagersTable.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.SyncManagersGridColAlignements[col], wx.ALIGN_CENTRE)
            self.SyncManagersGrid.SetColAttr(col, attr)
            self.SyncManagersGrid.SetColMinimalWidth(col, self.SyncManagersGridColSizes[col])
            self.SyncManagersGrid.AutoSizeColumn(col, False)

        self.RefreshSlaveInfos()

    def RefreshSlaveInfos(self):
        """
        Fill data in "Slave Information" and "SyncManager"
        """
        slave_infos = self.Controler.GetSlaveInfos()
        sync_manager_section = ["vendor", "product_code", "revision_number", "physics"]
        if slave_infos is not None:
            # this method is same as "TextCtrl.SetValue"
            for textctrl_name in sync_manager_section:
                self.TextCtrlDic[textctrl_name].SetValue(slave_infos[textctrl_name])
            self.SyncManagersTable.SetData(slave_infos["sync_managers"])
            self.SyncManagersTable.ResetView(self.SyncManagersGrid)
        else:
            for textctrl_name in sync_manager_section:
                self.TextCtrlDic[textctrl_name].SetValue("")
            self.SyncManagersTable.SetData([])
            self.SyncManagersTable.ResetView(self.SyncManagersGrid)

    def OnButtonClick(self, event):
        """
        Event handler for slave state transition button click (Init, PreOP, SafeOP, OP button)
        @param event : wx.EVT_BUTTON object
        """
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            state_dic = ["INIT", "PREOP", "SAFEOP", "OP"]

            # If target state is one of {INIT, PREOP, SAFEOP}, request slave state transition immediately.
            if event.GetId() < 3:
                self.Controler.CommonMethod.RequestSlaveState(state_dic[event.GetId()])
                self.TextCtrlDic["TargetState"].SetValue(state_dic[event.GetId()])

            # If target state is OP, first check "PLC status".
            #  (1) If current PLC status is "Started", then request slave state transition
            #  (2) Otherwise, show error message and return
            else:
                status, _log_count = self.Controler.GetCTRoot()._connector.GetPLCstatus()
                if status == PlcStatus.Started:
                    self.Controler.CommonMethod.RequestSlaveState("OP")
                    self.TextCtrlDic["TargetState"].SetValue("OP")
                else:
                    self.Controler.CommonMethod.CreateErrorDialog(_("PLC is Not Started"))

    def GetCurrentState(self, event):
        """
        Timer event handler for periodic slave state monitoring (Default period: 1 sec = 1000 msec).
        @param event : wx.TIMER object
        """
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(True)
        if check_connect_flag:
            returnVal = self.Controler.CommonMethod.GetSlaveStateFromSlave()
            line = returnVal.split("\n")
            try:
                self.SetCurrentState(line[self.Controler.GetSlavePos()])
            except Exception:
                pass

    def SetCurrentState(self, line):
        """
        Show current slave state using the executiob result of "ethercat slaves" command.
        @param line : result of "ethercat slaves" command
        """
        state_array = ["INIT", "PREOP", "SAFEOP", "OP"]
        try:
            # parse the execution result of  "ethercat slaves" command
            # Result example : 0  0:0  PREOP  +  EL9800 (V4.30) (PIC24, SPI, ET1100)
            token = line.split("  ")
            if token[2] in state_array:
                self.TextCtrlDic["CurrentState"].SetValue(token[2])
        except Exception:
            pass

    def StartTimer(self, event):
        """
        Event handler for "Start State Monitoring" button.
          - start slave state monitoring thread
        @param event : wx.EVT_BUTTON object
        """
        self.SlaveStateThread = wx.Timer(self)
        # set timer period (1000 ms)
        self.SlaveStateThread.Start(1000)

    def CurrentStateThreadStop(self, event):
        """
        Event handler for "Stop State Monitoring" button.
          - stop slave state monitoring thread
        @param event : wx.EVT_BUTTON object
        """
        try:
            self.SlaveStateThread.Stop()
        except Exception:
            pass


# -------------------------------------------------------------------------------
#                    For SDO Management Panel
# -------------------------------------------------------------------------------
class SDOPanelClass(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent EtherCATManagementTreebook class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1)

        self.DatatypeDescription, self.CommunicationObject, self.ManufacturerSpecific, \
            self.ProfileSpecific, self.Reserved, self.AllSDOData = range(6)

        self.Controler = controler

        self.SDOManagementMainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SDOManagementInnerMainSizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10)

        self.SDOUpdate = wx.Button(self, label=_('update'))
        self.SDOUpdate.Bind(wx.EVT_BUTTON, self.SDOInfoUpdate)

        self.CallSDONoteBook = SDONoteBook(self, controler=self.Controler)
        self.SDOManagementInnerMainSizer.Add(self.SDOUpdate)
        self.SDOManagementInnerMainSizer.Add(self.CallSDONoteBook, wx.ALL | wx.EXPAND)

        self.SDOManagementMainSizer.Add(self.SDOManagementInnerMainSizer)

        self.SetSizer(self.SDOManagementMainSizer)

    def SDOInfoUpdate(self, event):
        """
        Evenet handler for SDO "update" button.
          - Load SDO data from current slave
        @param event : wx.EVT_BUTTON object
        """
        self.Controler.CommonMethod.SaveSDOData = []
        self.Controler.CommonMethod.ClearSDODataSet()
        self.SDOFlag = False

        # Check whether beremiz connected or not.
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            self.SDOs = self.Controler.CommonMethod.GetSlaveSDOFromSlave()
            # SDOFlag is "False", user click "Cancel" button
            self.SDOFlag = self.SDOParser()

            if self.SDOFlag:
                self.CallSDONoteBook.CreateNoteBook()
                self.Refresh()

    def SDOParser(self):
        """
        Parse SDO data set that obtain "SDOInfoUpdate" Method
        @return True or False
        """

        slaveSDO_progress = wx.ProgressDialog(_("Slave SDO Monitoring"), _("Now Uploading..."),
                                              maximum=len(self.SDOs.splitlines()),
                                              parent=self,
                                              style=wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME |
                                              wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME |
                                              wx.PD_AUTO_HIDE | wx.PD_SMOOTH)

        # If keep_going flag is False, SDOParser method is stop and return "False".
        keep_going = True
        count = 0

        # SDO data example
        # SDO 0x1000, "Device type"
        # 0x1000:00,r-r-r-,uint32,32 bit,"Device type",0x00020192, 131474
        for details_line in self.SDOs.splitlines():
            count += 1
            line_token = details_line.split("\"")
            # len(line_token[2]) case : SDO 0x1000, "Device type"
            if len(line_token[2]) == 0:
                title_name = line_token[1]
            # else case : 0x1000:00,r-r-r-,uint32,32 bit,"Device type",0x00020192, 131474
            else:
                # line_token = ['0x1000:00,r-r-r-,uint32,32 bit,', 'Device type', ',0x00020192, 131474']
                token_head, name, token_tail = line_token

                # token_head = ['0x1000:00', 'r-r-r-', 'uint32', '32 bit', '']
                token_head = token_head.split(",")
                ful_idx, access, type, size, _empty = token_head
                # ful_idx.split(":") = ['0x1000', '00']
                idx, sub_idx = ful_idx.split(":")

                # token_tail = ['', '0x00020192', '131474']
                token_tail = token_tail.split(",")
                try:
                    _empty, hex_val, _dec_val = token_tail

                # SDO data is not return "dec value"
                # line example :
                # 0x1702:01,rwr-r-,uint32,32 bit," 1st mapping", ----
                except Exception:
                    _empty, hex_val = token_tail

                name_after_check = self.StringTest(name)

                # convert hex type
                sub_idx = "0x" + sub_idx

                if type == "octet_string":
                    hex_val = ' ---- '

                # SResult of SlaveSDO data parsing. (data type : dictionary)
                self.Data = {'idx': idx.strip(), 'subIdx': sub_idx.strip(), 'access': access.strip(),
                             'type': type.strip(), 'size': size.strip(),  'name': name_after_check.strip("\""),
                             'value': hex_val.strip(), "category": title_name.strip("\"")}

                category_divide_value = [0x1000, 0x2000, 0x6000, 0xa000, 0xffff]

                for count in range(len(category_divide_value)):
                    if int(idx, 0) < category_divide_value[count]:
                        self.Controler.CommonMethod.SaveSDOData[count].append(self.Data)
                        break

                self.Controler.CommonMethod.SaveSDOData[self.AllSDOData].append(self.Data)

            if count >= len(self.SDOs.splitlines()) // 2:
                (keep_going, _skip) = slaveSDO_progress.Update(count, "Please waiting a moment!!")
            else:
                (keep_going, _skip) = slaveSDO_progress.Update(count)

            # If user click "Cancel" loop suspend immediately
            if not keep_going:
                break

        slaveSDO_progress.Destroy()
        return keep_going

    def StringTest(self, check_string):
        """
        Test value 'name' is alphanumeric
        @param check_string : input data for check
        @return result : output data after check
        """
        # string.printable is print this result
        # '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
        # !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r\x0b\x0c
        allow_range = string.printable
        result = check_string
        for i in range(0, len(check_string)):
            # string.isalnum() is check whether string is alphanumeric or not
            if check_string[len(check_string)-1-i:len(check_string)-i] in allow_range:
                result = check_string[:len(check_string) - i]
                break
        return result


# -------------------------------------------------------------------------------
#                    For SDO Notebook (divide category)
# -------------------------------------------------------------------------------
class SDONoteBook(wx.Notebook):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent SDOPanelClass class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Notebook.__init__(self, parent, id=-1, size=(850, 500))
        self.Controler = controler
        self.parent = parent

        self.CreateNoteBook()

    def CreateNoteBook(self):
        """
        Create each NoteBook page, divided SDO index
        According to EtherCAT Communication(03/2011), 158p
        """
        self.Data = []
        count = 1

        page_texts = [("all", self.parent.AllSDOData),
                      ("0x0000 - 0x0ff", self.parent.DatatypeDescription),
                      ("0x1000 - 0x1fff", self.parent.CommunicationObject),
                      ("0x2000 - 0x5fff", self.parent.ManufacturerSpecific),
                      ("0x6000 - 0x9fff", self.parent.ProfileSpecific),
                      ("0xa000 - 0xffff", self.parent.Reserved)]

        # page_tooltip_string = ["SDO Index 0x0000 - 0x0fff : Data Type Description",
        #                        "SDO Index 0x1000 - 0x1fff : Communication object",
        #                        "SDO Index 0x2000 - 0x5fff : Manufacturer specific",
        #                        "SDO Index 0x6000 - 0x9fff : Profile specific",
        #                        "SDO Index 0xa000 - 0xffff : Reserved",
        #                        "All SDO Object"]

        self.DeleteAllPages()

        for txt, count in page_texts:
            self.Data = self.Controler.CommonMethod.SaveSDOData[count]
            self.Win = SlaveSDOTable(self, self.Data)
            self.AddPage(self.Win, txt)


# -------------------------------------------------------------------------------
#                    For SDO Grid (fill index, subindex, etc...)
# -------------------------------------------------------------------------------
class SlaveSDOTable(wx.grid.Grid):
    def __init__(self, parent, data):
        """
        Constructor
        @param parent: Reference to the parent SDOPanelClass class
        @param data: SDO data after parsing "SDOParser" method
        """
        wx.grid.Grid.__init__(self, parent, -1, size=(830, 490),
                              style=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        self.Controler = parent.Controler
        self.parent = parent
        self.SDOFlag = True
        if data is None:
            self.SDOs = []
        else:
            self.SDOs = data

        self.CreateGrid(len(self.SDOs), 8)
        SDOCellSize = [(0, 65), (1, 65), (2, 50), (3, 55),
                       (4, 40), (5, 200), (6, 250), (7, 85)]

        for (index, size) in SDOCellSize:
            self.SetColSize(index, size)

        self.SetRowLabelSize(0)

        SDOTableLabel = [(0, "Index"), (1, "Subindex"), (2, "Access"),
                         (3, "Type"), (4, "Size"), (5, "Category"),
                         (6, "Name"), (7, "Value")]

        for (index, label) in SDOTableLabel:
            self.SetColLabelValue(index, label)
            self.SetColLabelAlignment(index, wx.ALIGN_CENTRE)

        attr = wx.grid.GridCellAttr()

        # for SDO download
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.SDOModifyDialog)

        for i in range(7):
            self.SetColAttr(i, attr)

        self.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        self.SetTableValue()

    def SetTableValue(self):
        """
        Cell is filled by new parsing data
        """
        sdo_list = ['idx', 'subIdx', 'access', 'type', 'size', 'category', 'name', 'value']
        for row_idx in range(len(self.SDOs)):
            for col_idx in range(len(self.SDOs[row_idx])):
                self.SetCellValue(row_idx, col_idx, self.SDOs[row_idx][sdo_list[col_idx]])
                self.SetReadOnly(row_idx, col_idx, True)
                if col_idx < 5:
                    self.SetCellAlignment(row_idx, col_idx, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

    def CheckSDODataAccess(self, row):
        """
        CheckSDODataAccess method is checking that access data has "w"
        Access field consist 6 char, if mean
           rw      rw     rw
        (preop) (safeop) (op)
        Example Access field : rwrwrw, rwrw--
        @param row : Selected cell by user
        @return Write_flag : If data has "w", flag is true
        """
        write_flag = False
        check = self.SDOs[row]['access']
        if check[1:2] == 'w':
            self.Controler.CommonMethod.Check_PREOP = True
            write_flag = True
        if check[3:4] == 'w':
            self.Controler.CommonMethod.Check_SAFEOP = True
            write_flag = True
        if check[5:] == 'w':
            self.Controler.CommonMethod.Check_OP = True
            write_flag = True

        return write_flag

    def DecideSDODownload(self, state):
        """
        compare current state and "access" field,
        result notify SDOModifyDialog method
        @param state : current slave state
        @return True or False
        """
        # Example of 'state' parameter : "0  0:0  PREOP  +  EL9800 (V4.30) (PIC24, SPI, ET1100)"
        state = state[self.Controler.GetSlavePos()].split("  ")[2]
        if state == "PREOP" and self.Controler.CommonMethod.Check_PREOP:
            return True
        elif state == "SAFEOP" and self.Controler.CommonMethod.Check_SAFEOP:
            return True
        elif state == "OP" and self.Controler.CommonMethod.Check_OP:
            return True

        return False

    def ClearStateFlag(self):
        """
        Initialize StateFlag
        StateFlag is notice SDOData access each slave state
        """
        self.Controler.CommonMethod.Check_PREOP = False
        self.Controler.CommonMethod.Check_SAFEOP = False
        self.Controler.CommonMethod.Check_OP = False

    def SDOModifyDialog(self, event):
        """
        Create dialog for SDO value modify
        if user enter data, perform command "ethercat download"
        @param event : wx.grid.EVT_GRID_CELL_LEFT_DCLICK object
        """
        self.ClearStateFlag()

        # CheckSDODataAccess is checking that OD(Object Dictionary) has "w"
        if event.GetCol() == 7 and self.CheckSDODataAccess(event.GetRow()):
            dlg = wx.TextEntryDialog(
                self,
                _("Enter hex or dec value (if enter dec value, it automatically conversed hex value)"),
                "SDOModifyDialog",
                style=wx.OK | wx.CANCEL)

            start_value = self.GetCellValue(event.GetRow(), event.GetCol())
            dlg.SetValue(start_value)

            if dlg.ShowModal() == wx.ID_OK:
                try:
                    int(dlg.GetValue(), 0)
                    # check "Access" field
                    if self.DecideSDODownload(self.Controler.CommonMethod.SlaveState[self.Controler.GetSlavePos()]):
                        # Request "SDODownload"
                        self.Controler.CommonMethod.SDODownload(
                            self.SDOs[event.GetRow()]['type'],
                            self.SDOs[event.GetRow()]['idx'],
                            self.SDOs[event.GetRow()]['subIdx'],
                            dlg.GetValue())

                        self.SetCellValue(event.GetRow(), event.GetCol(), hex(int(dlg.GetValue(), 0)))
                    else:
                        self.Controler.CommonMethod.CreateErrorDialog(_('You cannot SDO download this state'))
                # Error occured process of "int(variable)"
                # User input is not hex, dec value
                except ValueError:
                    self.Controler.CommonMethod.CreateErrorDialog(_('You can input only hex, dec value'))


# -------------------------------------------------------------------------------
#                 For PDO Monitoring Panel
# PDO Class UI  : Panel -> Choicebook (RxPDO, TxPDO) ->
#                 Notebook (PDO Index) -> Grid (PDO entry)
# -------------------------------------------------------------------------------
class PDOPanelClass(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent EtherCATManagementTreebook class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1)
        self.Controler = controler

        self.PDOMonitoringEditorMainSizer = wx.BoxSizer(wx.VERTICAL)
        self.PDOMonitoringEditorInnerMainSizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10)

        self.CallPDOChoicebook = PDOChoicebook(self, controler=self.Controler)
        self.PDOMonitoringEditorInnerMainSizer.Add(self.CallPDOChoicebook, wx.ALL)

        self.PDOMonitoringEditorMainSizer.Add(self.PDOMonitoringEditorInnerMainSizer)

        self.SetSizer(self.PDOMonitoringEditorMainSizer)

    def PDOInfoUpdate(self):
        """
        Call RequestPDOInfo method and create Choicebook
        """
        self.Controler.CommonMethod.RequestPDOInfo()
        self.CallPDOChoicebook.Destroy()
        self.CallPDOChoicebook = PDOChoicebook(self, controler=self.Controler)
        self.Refresh()


# -------------------------------------------------------------------------------
#                    For PDO Choicebook (divide Tx, Rx PDO)
# -------------------------------------------------------------------------------
class PDOChoicebook(wx.Choicebook):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent PDOPanelClass class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Choicebook.__init__(self, parent, id=-1, size=(500, 500), style=wx.CHB_DEFAULT)
        self.Controler = controler

        RxWin = PDONoteBook(self, controler=self.Controler, name="Rx")
        TxWin = PDONoteBook(self, controler=self.Controler, name="Tx")
        self.AddPage(RxWin, "RxPDO")
        self.AddPage(TxWin, "TxPDO")


# -------------------------------------------------------------------------------
#                    For PDO Notebook (divide PDO index)
# -------------------------------------------------------------------------------
class PDONoteBook(wx.Notebook):
    def __init__(self, parent, name, controler):
        """
        Constructor
        @param parent: Reference to the parent PDOChoicebook class
        @param name: identifier whether RxPDO or TxPDO
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Notebook.__init__(self, parent, id=-1, size=(640, 400))
        self.Controler = controler

        count = 0
        page_texts = []

        self.Controler.CommonMethod.RequestPDOInfo()

        if name == "Tx":
            # obtain pdo_info and pdo_entry
            # pdo_info include (PDO index, name, number of entry)
            pdo_info = self.Controler.CommonMethod.GetTxPDOCategory()
            pdo_entry = self.Controler.CommonMethod.GetTxPDOInfo()
            for tmp in pdo_info:
                title = str(hex(tmp['pdo_index']))
                page_texts.append(title)
        # RX PDO case
        else:
            pdo_info = self.Controler.CommonMethod.GetRxPDOCategory()
            pdo_entry = self.Controler.CommonMethod.GetRxPDOInfo()
            for tmp in pdo_info:
                title = str(hex(tmp['pdo_index']))
                page_texts.append(title)

        # Add page depending on the number of pdo_info
        for txt in page_texts:
            win = PDOEntryTable(self, pdo_info, pdo_entry, count)
            self.AddPage(win, txt)
            count += 1


# -------------------------------------------------------------------------------
#                    For PDO Grid (fill entry index, subindex etc...)
# -------------------------------------------------------------------------------
class PDOEntryTable(wx.grid.Grid):
    def __init__(self, parent, info, entry, count):
        """
        Constructor
        @param parent: Reference to the parent PDONoteBook class
        @param info : data structure including entry index, sub index, name, length, type
        @param entry : data structure including index, name, entry number
        @param count : page number
        """
        wx.grid.Grid.__init__(self, parent, -1, size=(500, 400), pos=wx.Point(0, 0),
                              style=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        self.Controler = parent.Controler

        self.PDOInfo = info
        self.PDOEntry = entry
        self.Count = count

        self.CreateGrid(self.PDOInfo[self.Count]['number_of_entry'], 5)
        self.SetColLabelSize(25)
        self.SetRowLabelSize(0)

        PDOTableLabel = [(0, "Index"), (1, "Subindex"), (2, "Length"),
                         (3, "Type"), (4, "Name")]

        for (index, label) in PDOTableLabel:
            self.SetColLabelValue(index, label)

        PDOCellSize = [(0, 45), (1, 65), (2, 55), (3, 40), (4, 300)]

        for (index, size) in PDOCellSize:
            self.SetColSize(index, size)
            self.SetColLabelAlignment(index, wx.ALIGN_LEFT)

        attr = wx.grid.GridCellAttr()

        for i in range(5):
            self.SetColAttr(i, attr)

        self.SetTableValue()

    def SetTableValue(self):
        """
        Cell is filled by new parsing data in XML
        """
        list_index = 0
        # number of entry
        for i in range(self.Count + 1):
            list_index += self.PDOInfo[i]['number_of_entry']

        start_value = list_index - self.PDOInfo[self.Count]['number_of_entry']

        pdo_list = ['entry_index', 'subindex', 'bitlen', 'type', 'name']
        for row_idx in range(self.PDOInfo[self.Count]['number_of_entry']):
            for col_idx in range(len(self.PDOEntry[row_idx])):
                # entry index is converted hex value.
                if col_idx == 0:
                    self.SetCellValue(row_idx, col_idx, hex(self.PDOEntry[start_value][pdo_list[col_idx]]))
                else:
                    self.SetCellValue(row_idx, col_idx, str(self.PDOEntry[start_value][pdo_list[col_idx]]))
                if col_idx != 4:
                    self.SetCellAlignment(row_idx, col_idx, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
                else:
                    self.SetCellAlignment(row_idx, col_idx, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
                self.SetReadOnly(row_idx, col_idx, True)
                self.SetRowSize(row_idx, 25)
            start_value += 1


# -------------------------------------------------------------------------------
#                    For EEPROM Access Main Panel
#                 (This class explain EEPROM Access)
# -------------------------------------------------------------------------------
class EEPROMAccessPanel(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent EtherCATManagementTreebook class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.FlexGridSizer(cols=1, hgap=20, rows=3, vgap=20)

        line = wx.StaticText(self, -1, "\n  EEPROM Access is composed to SmartView and HexView. \
                                              \n\n   - SmartView shows Config Data, Device Identity, Mailbox settings, etc. \
                                              \n\n   - HexView shows EEPROM's contents.")

        sizer.Add(line)

        self.SetSizer(sizer)


# -------------------------------------------------------------------------------
#                    For Smart View Panel
# -------------------------------------------------------------------------------
class SlaveSiiSmartView(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent EtherCATManagementTreebook class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.Controler = controler

        self.PDIType = {
            0: ['none', '00000000'],
            4: ['Digital I/O', '00000100'],
            5: ['SPI Slave', '00000101'],
            7: ['EtherCAT Bridge (port3)', '00000111'],
            8: ['uC async. 16bit', '00001000'],
            9: ['uC async. 8bit', '00001001'],
            10: ['uC sync. 16bit', '00001010'],
            11: ['uC sync. 8bit', '00001011'],
            16: ['32 Digtal Input and 0 Digital Output', '00010000'],
            17: ['24 Digtal Input and 8 Digital Output', '00010001'],
            18: ['16 Digtal Input and 16 Digital Output', '00010010'],
            19: ['8 Digtal Input and 24 Digital Output', '00010011'],
            20: ['0 Digtal Input and 32 Digital Output', '00010100'],
            128: ['On-chip bus', '11111111']
        }

        sizer = wx.FlexGridSizer(cols=1, hgap=5, rows=2, vgap=5)
        button_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=1, vgap=5)

        for button, mapping_method in [("Write EEPROM", self.WriteToEEPROM),
                                       ("Read EEPROM", self.ReadFromEEPROM)]:
            btn = wx.Button(self, -1, button, size=(150, 40))
            button_sizer.Add(btn, border=10, flag=wx.ALL)
            btn.Bind(wx.EVT_BUTTON, mapping_method)

        self.TreeListCtrl = SmartViewTreeListCtrl(self, self.Controler)

        sizer.Add(button_sizer, border=10, flag=wx.ALL)
        sizer.Add(self.TreeListCtrl, border=10, flag=wx.ALL)
        self.SetSizer(sizer)

        self.Create_SmartView()

    def Create_SmartView(self):
        """
        SmartView shows information based on XML as initial value.
        """
        self.Controler.CommonMethod.SmartViewInfosFromXML = self.Controler.CommonMethod.GetSmartViewInfos()
        self.SetXMLData()

    def WriteToEEPROM(self, event):
        """
        Open binary file (user select) and write the selected binary data to EEPROM
        @param event : wx.EVT_BUTTON object
        """
        # Check whether beremiz connected or not, and whether status is "Started" or not.
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            status, _log_count = self.Controler.GetCTRoot()._connector.GetPLCstatus()
            if status is not PlcStatus.Started:
                dialog = wx.FileDialog(self, _("Choose a binary file"), os.getcwd(), "",  _("bin files (*.bin)|*.bin"), wx.OPEN)

                if dialog.ShowModal() == wx.ID_OK:
                    filepath = dialog.GetPath()
                    try:
                        binfile = open(filepath, "rb")
                        self.SiiBinary = binfile.read()
                        dialog.Destroy()

                        self.Controler.CommonMethod.SiiWrite(self.SiiBinary)
                        # refresh data structure kept by master
                        self.Controler.CommonMethod.Rescan()
                        # save binary data as inner global data of beremiz
                        # for fast loading when slave plugin node is reopened.
                        self.Controler.CommonMethod.SiiData = self.SiiBinary
                        self.SetEEPROMData()
                    except Exception:
                        self.Controler.CommonMethod.CreateErrorDialog(_('The file does not exist!'))
                        dialog.Destroy()

    def ReadFromEEPROM(self, event):
        """
        Refresh displayed data based on slave EEPROM and save binary file through dialog
        @param event : wx.EVT_BUTTON object
        """
        # Check whether beremiz connected or not.
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            self.SiiBinary = self.Controler.CommonMethod.LoadData()
            self.SetEEPROMData()
            dialog = wx.FileDialog(self, _("Save as..."), os.getcwd(),
                                   "slave0.bin",  _("bin files (*.bin)|*.bin|All files|*.*"),
                                   wx.SAVE | wx.OVERWRITE_PROMPT)

            if dialog.ShowModal() == wx.ID_OK:
                filepath = dialog.GetPath()
                binfile = open(filepath, "wb")
                binfile.write(self.SiiBinary)
                binfile.close()

            dialog.Destroy()

    def SetXMLData(self):
        """
        Set data based on XML initially
        """
        # Config Data: EEPROM Size, PDI Type, Device Emulation
        # Find PDI Type in pdiType dictionary
        cnt_pdi_type = self.Controler.CommonMethod.SmartViewInfosFromXML["pdi_type"]
        for i in self.PDIType.keys():
            if cnt_pdi_type == i:
                cnt_pdi_type = self.PDIType[i][0]
                break
        #  Set Config Data
        for treelist, data in [("EEPROM Size (Bytes)",
                                str(self.Controler.CommonMethod.SmartViewInfosFromXML["eeprom_size"])),
                               ("PDI Type",
                                cnt_pdi_type),
                               ("Device Emulation",
                                self.Controler.CommonMethod.SmartViewInfosFromXML["device_emulation"])]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.ConfigData[treelist], data, 1)

        # Device Identity: Vendor ID, Product Code, Revision No., Serial No.
        #  Set Device Identity
        for treelist, data in [("Vendor ID", self.Controler.CommonMethod.SmartViewInfosFromXML["vendor_id"]),
                               ("Product Code", self.Controler.CommonMethod.SmartViewInfosFromXML["product_code"]),
                               ("Revision No.", self.Controler.CommonMethod.SmartViewInfosFromXML["revision_no"]),
                               ("Serial No.", self.Controler.CommonMethod.SmartViewInfosFromXML["serial_no"])]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.DeviceIdentity[treelist], data, 1)

        # Mailbox: Supported Mailbox, Bootstrap Configuration, Standard Configuration
        #  Set Mailbox
        for treelist, data in [("Supported Mailbox", self.Controler.CommonMethod.SmartViewInfosFromXML["supported_mailbox"]),
                               ("Bootstrap Configuration", ""),
                               ("Standard Configuration", "")]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.Mailbox[treelist], data, 1)
        #  Set Bootstrap Configuration: Receive Offset, Receive Size, Send Offset, Send Size
        for treelist, data in [("Receive Offset", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_bootstrapconf_outstart"]),
                               ("Receive Size", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_bootstrapconf_outlength"]),
                               ("Send Offset", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_bootstrapconf_instart"]),
                               ("Send Size", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_bootstrapconf_inlength"])]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.BootstrapConfig[treelist], data, 1)
        #  Set Standard Configuration: Receive Offset, Receive Size, Send Offset, Send Size
        for treelist, data in [("Receive Offset", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_standardconf_outstart"]),
                               ("Receive Size", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_standardconf_outlength"]),
                               ("Send Offset", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_standardconf_instart"]),
                               ("Send Size", self.Controler.CommonMethod.SmartViewInfosFromXML["mailbox_standardconf_inlength"])]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.StandardConfig[treelist], data, 1)

    def SetEEPROMData(self):
        """
        Set data based on slave EEPROM.
        """
        # sii_dict = { Parameter : (WordAddress, WordSize) }
        sii_dict = {
            'PDIControl':                          ('0', 1),
            'PDIConfiguration':                    ('1', 1),
            'PulseLengthOfSYNCSignals':            ('2', 1),
            'ExtendedPDIConfiguration':            ('3', 1),
            'ConfiguredStationAlias':              ('4', 1),
            'Checksum':                            ('7', 1),
            'VendorID':                            ('8', 2),
            'ProductCode':                         ('a', 2),
            'RevisionNumber':                      ('c', 2),
            'SerialNumber':                        ('e', 2),
            'Execution Delay':                     ('10', 1),
            'Port0Delay':                          ('11', 1),
            'Port1Delay':                          ('12', 1),
            'BootstrapReceiveMailboxOffset':       ('14', 1),
            'BootstrapReceiveMailboxSize':         ('15', 1),
            'BootstrapSendMailboxOffset':          ('16', 1),
            'BootstrapSendMailboxSize':            ('17', 1),
            'StandardReceiveMailboxOffset':        ('18', 1),
            'StandardReceiveMailboxSize':          ('19', 1),
            'StandardSendMailboxOffset':           ('1a', 1),
            'StandardSendMailboxSize':             ('1b', 1),
            'MailboxProtocol':                     ('1c', 1),
            'Size':                                ('3e', 1),
            'Version':                             ('3f', 1),
            'First Category Type/Vendor Specific': ('40', 1),
            'Following Category Word Size':        ('41', 1),
            'Category Data':                       ('42', 1),
        }

        # Config Data: EEPROM Size, PDI Type, Device Emulation
        # EEPROM's data in address '0x003f' is Size of EEPROM in KBit-1
        eeprom_size = str((int(self.GetWordAddressData(sii_dict.get('Size'), 10))+1)//8*1024)
        # Find PDI Type in pdiType dictionary
        cnt_pdi_type = int(self.GetWordAddressData(sii_dict.get('PDIControl'), 16).split('x')[1][2:4], 16)
        for i in self.PDIType.keys():
            if cnt_pdi_type == i:
                cnt_pdi_type = self.PDIType[i][0]
                break
        #  Get Device Emulation
        device_emulation = str(bool(int("{:0>16b}".format(int(self.GetWordAddressData(sii_dict.get('PDIControl'), 16), 16))[7])))
        #  Set Config Data
        for treelist, data in [("EEPROM Size (Bytes)", eeprom_size),
                               ("PDI Type", cnt_pdi_type),
                               ("Device Emulation", device_emulation)]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.ConfigData[treelist], data, 1)

        # Device Identity: Vendor ID, Product Code, Revision No., Serial No.
        #  Set Device Identity
        for treelist, data in [
                ("Vendor ID", self.GetWordAddressData(sii_dict.get('VendorID'), 16)),
                ("Product Code", self.GetWordAddressData(sii_dict.get('ProductCode'), 16)),
                ("Revision No.", self.GetWordAddressData(sii_dict.get('RevisionNumber'), 16)),
                ("Serial No.", self.GetWordAddressData(sii_dict.get('SerialNumber'), 16))]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.DeviceIdentity[treelist], data, 1)

        # Mailbox
        # EEORPOM's word address '1c' indicates supported mailbox protocol.
        # each value of mailbox protocol :
        # VoE(0x0020), SoE(0x0010), FoE(0x0008), CoE(0x0004), EoE(0x0002), AoE(0x0001)
        supported_mailbox = ""
        mailbox_protocol = ["VoE,  ", "SoE,  ", "FoE,  ", "CoE,  ", "EoE,  ", "AoE,  "]
        mailbox_data = "{:0>8b}".format(int(self.GetWordAddressData(sii_dict.get('MailboxProtocol'), 16), 16))
        for protocol in range(6):
            if mailbox_data[protocol+2] == '1':
                supported_mailbox += mailbox_protocol[protocol]
        supported_mailbox = supported_mailbox.strip(",  ")
        #  Set Mailbox
        for treelist, data in [("Supported Mailbox", supported_mailbox),
                               ("Bootstrap Configuration", ""),
                               ("Standard Configuration", "")]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.Mailbox[treelist], data, 1)
        #  Set Bootstrap Configuration: Receive Offset, Receive Size, Send Offset, Send Size
        for treelist, data in [
                ("Receive Offset", self.GetWordAddressData(sii_dict.get('BootstrapReceiveMailboxOffset'), 10)),
                ("Receive Size", self.GetWordAddressData(sii_dict.get('BootstrapReceiveMailboxSize'), 10)),
                ("Send Offset", self.GetWordAddressData(sii_dict.get('BootstrapSendMailboxOffset'), 10)),
                ("Send Size", self.GetWordAddressData(sii_dict.get('BootstrapSendMailboxSize'), 10))]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.BootstrapConfig[treelist], data, 1)
        #  Set Standard Configuration: Receive Offset, Receive Size, Send Offset, Send Size
        for treelist, data in [
                ("Receive Offset", self.GetWordAddressData(sii_dict.get('StandardReceiveMailboxOffset'), 10)),
                ("Receive Size", self.GetWordAddressData(sii_dict.get('StandardReceiveMailboxSize'), 10)),
                ("Send Offset", self.GetWordAddressData(sii_dict.get('StandardSendMailboxOffset'), 10)),
                ("Send Size", self.GetWordAddressData(sii_dict.get('StandardSendMailboxSize'), 10))]:
            self.TreeListCtrl.Tree.SetItemText(self.TreeListCtrl.StandardConfig[treelist], data, 1)

    def MakeStaticBoxSizer(self, boxlabel):
        """
        Make StaticBoxSizer
        @param boxlabel : label of box sizer
        @return sizer : the StaticBoxSizer labeled 'boxlabel'
        """
        box = wx.StaticBox(self, -1, boxlabel)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        return sizer

    def GetWordAddressData(self, dict_tuple, format):
        """
        This method converts word address data from EEPROM binary.
        @param dict_tuple : element of 'sii_dict' dictionary in SetEEPROMData()
        @param format : format of data. It can be 16(hex), 10(decimal) and 2(binary).
        @return formatted value
        """
        offset = int(str(dict_tuple[0]), 16) * 2
        length = int(str(dict_tuple[1]), 16) * 2
        list = []
        data = ''
        for index in range(length):
            hexdata = hex(ord(self.SiiBinary[offset + index]))[2:]
            list.append(hexdata.zfill(2))

        list.reverse()
        data = list[0:length]

        if format == 16:
            return '0x' + ''.join(data)
        elif format == 10:
            return str(int(str(''.join(data)), 16))
        elif format == 2:
            ''.join(data)


# -------------------------------------------------------------------------------
#                    For Smart View TreeListCtrl
# -------------------------------------------------------------------------------
class SmartViewTreeListCtrl(wx.Panel):
    def __init__(self, parent, Controler):
        """
        Constructor
        @param parent: Reference to the parent SlaveSiiSmartView class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """

        wx.Panel.__init__(self, parent, -1, size=(350, 500))

        self.Tree = wx.gizmos.TreeListCtrl(self, -1, size=(350, 500),
                                           style=(wx.TR_DEFAULT_STYLE |
                                                  wx.TR_FULL_ROW_HIGHLIGHT |
                                                  wx.TR_HIDE_ROOT |
                                                  wx.TR_COLUMN_LINES |
                                                  wx.TR_ROW_LINES))

        self.Tree.AddColumn("Description", width=200)
        self.Tree.AddColumn("Value", width=140)
        self.Tree.SetMainColumn(0)

        self.Root = self.Tree.AddRoot("")

        # Add item
        #  Level 1 nodes
        self.Level1Nodes = {}
        for lv1 in ["Config Data", "Device Identity", "Mailbox"]:
            self.Level1Nodes[lv1] = self.Tree.AppendItem(self.Root, lv1)

        #  Level 2 nodes
        #   Config Data
        self.ConfigData = {}
        for lv2 in ["EEPROM Size (Bytes)", "PDI Type", "Device Emulation"]:
            self.ConfigData[lv2] = self.Tree.AppendItem(self.Level1Nodes["Config Data"], lv2)
        #   Device Identity
        self.DeviceIdentity = {}
        for lv2 in ["Vendor ID", "Product Code", "Revision No.", "Serial No."]:
            self.DeviceIdentity[lv2] = self.Tree.AppendItem(self.Level1Nodes["Device Identity"], lv2)
        #   Mailbox
        self.Mailbox = {}
        for lv2 in ["Supported Mailbox", "Bootstrap Configuration", "Standard Configuration"]:
            self.Mailbox[lv2] = self.Tree.AppendItem(self.Level1Nodes["Mailbox"], lv2)

        #  Level 3 nodes
        #   Children of Bootstrap Configuration
        self.BootstrapConfig = {}
        for lv3 in ["Receive Offset", "Receive Size", "Send Offset", "Send Size"]:
            self.BootstrapConfig[lv3] = self.Tree.AppendItem(self.Mailbox["Bootstrap Configuration"], lv3)
        #   Children of Standard Configuration
        self.StandardConfig = {}
        for lv3 in ["Receive Offset", "Receive Size", "Send Offset", "Send Size"]:
            self.StandardConfig[lv3] = self.Tree.AppendItem(self.Mailbox["Standard Configuration"], lv3)

        # Expand Tree
        for tree in [self.Root,
                     self.Level1Nodes["Config Data"],
                     self.Level1Nodes["Device Identity"],
                     self.Level1Nodes["Mailbox"],
                     self.Mailbox["Bootstrap Configuration"],
                     self.Mailbox["Standard Configuration"]]:
            self.Tree.Expand(tree)


# -------------------------------------------------------------------------------
#                         For Hex View Panel
#            shows EEPROM binary as hex data and characters.
# -------------------------------------------------------------------------------
class HexView(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: Reference to the parent EtherCATManagementTreebook class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.Controler = controler

        self.HexRow = 8
        self.HexCol = 17

        self.HexViewSizer = {"view": wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10),
                             "siiButton": wx.BoxSizer()}
        self.HexViewButton = {}

        for key, evt_handler in [
                ("Sii Upload", self.OnButtonSiiUpload),
                ("Sii Download", self.OnButtonSiiDownload),
                ("Write to File", self.OnButtonWriteToBinFile),
                ("Read from File", self.OnButtonReadFromBinFile),
                ("XML to EEPROM Image", self.OnButtonXmlToEEPROMImg)]:
            self.HexViewButton[key] = wx.Button(self, -1, key)
            self.HexViewButton[key].Bind(wx.EVT_BUTTON, evt_handler)
            self.HexViewSizer["siiButton"].Add(self.HexViewButton[key])

        self.SiiBinary = self.Controler.CommonMethod.XmlToEeprom()
        self.HexCode, self.HexRow, self.HexCol = self.Controler.CommonMethod.HexRead(self.SiiBinary)
        self.SiiGrid = SiiGridTable(self, self.Controler, self.HexRow, self.HexCol)
        self.HexViewSizer["view"].AddMany([self.HexViewSizer["siiButton"], self.SiiGrid])
        self.SiiGrid.CreateGrid(self.HexRow, self.HexCol)
        self.SetSizer(self.HexViewSizer["view"])
        self.HexViewSizer["view"].FitInside(self.parent.parent)
        self.parent.parent.FitInside()
        self.SiiGrid.SetValue(self.HexCode)
        self.SiiGrid.Update()

    def UpdateSiiGridTable(self, row, col):
        """
        Destroy existing grid and recreate
        @param row, col : Hex View grid size
        """
        self.HexViewSizer["view"].Detach(self.SiiGrid)
        self.SiiGrid.Destroy()
        self.SiiGrid = SiiGridTable(self, self.Controler, row, col)
        self.HexViewSizer["view"].Add(self.SiiGrid)
        self.SiiGrid.CreateGrid(row, col)
        self.SetSizer(self.HexViewSizer["view"])
        self.HexViewSizer["view"].FitInside(self.parent.parent)
        self.parent.parent.FitInside()

    def OnButtonSiiUpload(self, event):
        """
        Load EEPROM data from slave and refresh Hex View grid
        Binded to 'Sii Upload' button.
        @param event : wx.EVT_BUTTON object
        """
        # Check whether beremiz connected or not.
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            # load from EEPROM data and parsing
            self.SiiBinary = self.Controler.CommonMethod.LoadData()
            self.HexCode, self.HexRow, self.HexCol = self.Controler.CommonMethod.HexRead(self.SiiBinary)
            self.UpdateSiiGridTable(self.HexRow, self.HexCol)
            self.SiiGrid.SetValue(self.HexCode)
            self.SiiGrid.Update()

    def OnButtonSiiDownload(self, event):
        """
        Write current EEPROM data to slave and refresh data structure kept by master
        Binded to 'Sii Download' button.
        @param event : wx.EVT_BUTTON object
        """
        # Check whether beremiz connected or not,
        # and whether status is "Started" or not.
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            status, _log_count = self.Controler.GetCTRoot()._connector.GetPLCstatus()
            if status is not PlcStatus.Started:
                self.Controler.CommonMethod.SiiWrite(self.SiiBinary)
                self.Controler.CommonMethod.Rescan()

    def OnButtonWriteToBinFile(self, event):
        """
        Save current EEPROM data to binary file through FileDialog
        Binded to 'Write to File' button.
        @param event : wx.EVT_BUTTON object
        """
        dialog = wx.FileDialog(self, _("Save as..."), os.getcwd(), "slave0.bin",
                               _("bin files (*.bin)|*.bin|All files|*.*"), wx.SAVE | wx.OVERWRITE_PROMPT)

        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            binfile = open(filepath, "wb")
            binfile.write(self.SiiBinary)
            binfile.close()

        dialog.Destroy()

    def OnButtonReadFromBinFile(self, event):
        """
        Load binary file through FileDialog
        Binded to 'Read from File' button.
        @param event : wx.EVT_BUTTON object
        """
        dialog = wx.FileDialog(self, _("Choose a binary file"), os.getcwd(), "",
                               _("bin files (*.bin)|*.bin"), wx.OPEN)

        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()

            try:
                binfile = open(filepath, "rb")
                self.SiiBinary = binfile.read()
                self.HexCode, self.HexRow, self.HexCol = self.Controler.CommonMethod.HexRead(self.SiiBinary)
                self.UpdateSiiGridTable(self.HexRow, self.HexCol)
                self.SiiGrid.SetValue(self.HexCode)
                self.SiiGrid.Update()
            except Exception:
                self.Controler.CommonMethod.CreateErrorDialog(_('The file does not exist!'))

        dialog.Destroy()

    def OnButtonXmlToEEPROMImg(self, event):
        """
        Create EEPROM data based XML data that current imported
        Binded to 'XML to EEPROM' button.
        @param event : wx.EVT_BUTTON object
        """
        self.SiiBinary = self.Controler.CommonMethod.XmlToEeprom()
        self.HexCode, self.HexRow, self.HexCol = self.Controler.CommonMethod.HexRead(self.SiiBinary)
        self.UpdateSiiGridTable(self.HexRow, self.HexCol)
        self.SiiGrid.SetValue(self.HexCode)
        self.SiiGrid.Update()


# -------------------------------------------------------------------------------
#                    For Hex View grid (fill hex data)
# -------------------------------------------------------------------------------
class SiiGridTable(wx.grid.Grid):
    def __init__(self, parent, controler, row, col):
        """
        Constructor
        @param parent: Reference to the parent HexView class
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        @param row, col: Hex View grid size
        """
        self.parent = parent
        self.Controler = controler
        self.Row = row
        self.Col = col

        wx.grid.Grid.__init__(self, parent, -1, size=(830, 450),
                              style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

    def SetValue(self, value):
        """
        Set data in the table
        @param value: EEPROM data list of which element is 1 Byte hex data
        """
        # set label name and size
        self.SetRowLabelSize(100)
        for col in range(self.Col):
            if col == 16:
                self.SetColLabelValue(16, "Text View")
                self.SetColSize(16, (self.GetSize().x-120)*4//20)
            else:
                self.SetColLabelValue(col, '%s' % col)
                self.SetColSize(col, (self.GetSize().x-120)//20)

        # set data into table
        row = col = 0
        for row_idx in value:
            col = 0
            self.SetRowLabelValue(row, "0x"+"{:0>4x}".format(row*(self.Col-1)))
            for hex in row_idx:
                self.SetCellValue(row, col, hex)

                if col == 16:
                    self.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
                else:
                    self.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTER)

                self.SetReadOnly(row, col, True)
                col = col + 1
            row = row + 1


# -------------------------------------------------------------------------------
#                    For Register Access Panel
# -------------------------------------------------------------------------------
class RegisterAccessPanel(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: EEPROMAccessPanel object
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        self.parent = parent
        self.Controler = controler
        self.__init_data()

        wx.Panel.__init__(self, parent, -1)

        sizer = wx.FlexGridSizer(cols=1, hgap=20, rows=2, vgap=5)
        button_sizer = wx.FlexGridSizer(cols=2, hgap=10, rows=1, vgap=10)

        self.ReloadButton = wx.Button(self, -1, "Reload")
        self.CompactViewCheckbox = wx.CheckBox(self, -1, "Compact View")
        self.RegisterNotebook = RegisterNotebook(self, self.Controler)

        button_sizer.AddMany([self.ReloadButton, self.CompactViewCheckbox])
        sizer.AddMany([button_sizer, self.RegisterNotebook])
        self.SetSizer(sizer)

        self.ReloadButton.Bind(wx.EVT_BUTTON, self.OnReloadButton)
        self.CompactViewCheckbox.Bind(wx.EVT_CHECKBOX, self.ToggleCompactViewCheckbox)

        for index in range(4):
            self.RegisterNotebook.RegPage[index].MainTable.CreateGrid(self.MainRow[index], self.MainCol)
            self.RegisterNotebook.RegPage[index].MainTable.SetValue(self, 0, index*512, (index+1)*512)

        # data default setting
        if self.Controler.CommonMethod.RegData == "":
            self.CompactViewCheckbox.Disable()
            for index in range(4):
                self.RegisterNotebook.RegPage[index].MainTable.SetValue(self, 0, index*512, (index+1)*512)
        else:  # If data was saved,
            self.BasicSetData()
            self.ParseData()
            for index in range(4):
                self.RegisterNotebook.RegPage[index].MainTable.SetValue(self, self.RegMonitorData, index*512, (index+1)*512)

    def __init_data(self):
        """
        Declare initial data.
        """
        # flag for compact view
        self.CompactFlag = False

        # main grid의 rows and cols
        self.MainRow = [512, 512, 512, 512]
        self.MainCol = 4

        # main grids' data range
        self.PageRange = []
        for index in range(4):
            self.PageRange.append([512*index, 512*(index+1)])

        #  Previous value of register data for register description configuration
        self.PreRegSpec = {"ESCType": "",
                           "FMMUNumber": "",
                           "SMNumber": "",
                           "PDIType": ""}

    def LoadData(self):
        """
        Get data from the register.
        """
        self.Controler.CommonMethod.RegData = ""
        # ethercat reg_read
        # ex : ethercat reg_read -p 0 0x0000 0x0001
        # return value : 0x11
        for index in range(4):
            self.Controler.CommonMethod.RegData = self.Controler.CommonMethod.RegData + " " + self.Controler.CommonMethod.RegRead("0x"+"{:0>4x}".format(index*1024), "0x0400")

        # store previous value
        # (ESC type, port number of FMMU, port number of SM, and PDI type))
        for reg_spec in ["ESCType", "FMMUNumber", "SMNumber", "PDIType"]:
            self.PreRegSpec[reg_spec] = self.Controler.CommonMethod.CrtRegSpec[reg_spec]

        # update registers' description
        # (ESC type, port number of FMMU, port number of SM, and PDI type)
        for reg_spec, address in [("ESCType", "0x0000"),
                                  ("FMMUNumber", "0x0004"),
                                  ("SMNumber", "0x0005"),
                                  ("PDIType", "0x0140")]:
            self.Controler.CommonMethod.CrtRegSpec[reg_spec] = self.Controler.CommonMethod.RegRead(address, "0x0001")

        # Enable compactView checkbox
        self.CompactViewCheckbox.Enable()

    def BasicSetData(self):
        """
        Get and save the description of registers.
        It's done by parsing register_information.xml.
        """
        # parse the above register's value
        # If the value is 0x12, the result is 12
        self.ESCType = self.Controler.CommonMethod.CrtRegSpec["ESCType"].split('x')[1]
        self.PDIType = self.Controler.CommonMethod.CrtRegSpec["PDIType"].split('x')[1]
        # If the value is 0x12, the result is 18 (It's converted to decimal value)
        self.FMMUNumber = int(self.Controler.CommonMethod.CrtRegSpec["FMMUNumber"], 16)
        self.SMNumber = int(self.Controler.CommonMethod.CrtRegSpec["SMNumber"], 16)

        # initialize description dictionary of register main table and register sub table.
        self.RegisterDescriptionDict = {}
        self.RegisterSubGridDict = {}

        # ./EthercatMaster/register_information.xml contains register description.
        if wx.Platform == '__WXMSW__':
            reg_info_file = open("../../EthercatMaster/register_information.xml", 'r')
        else:
            reg_info_file = open("./EthercatMaster/register_information.xml", 'r')
        reg_info_tree = minidom.parse(reg_info_file)
        reg_info_file.close()

        # parse register description
        for register_info in reg_info_tree.childNodes:
            for register in register_info.childNodes:
                if register.nodeType == reg_info_tree.ELEMENT_NODE and register.nodeName == "Register":
                    # If it depends on the property(ESC type, PDI type, FMMU number, SM number)
                    for property, type, value in [("esc", "type", self.ESCType),
                                                  ("pdi", "type", self.PDIType),
                                                  ("fmmu", "number", self.FMMUNumber),
                                                  ("sm", "number", self.SMNumber)]:
                        if property in register.attributes.keys():
                            if type == "type":
                                if register.attributes[property].value == value:
                                    self.GetRegisterInfo(reg_info_tree, register)
                                    break
                            else:  # type == "number"
                                if register.attributes[property].value < value:
                                    self.GetRegisterInfo(reg_info_tree, register)
                                    break
                        else:
                            self.GetRegisterInfo(reg_info_tree, register)
                            break

    def GetRegisterInfo(self, reg_info_tree, register):
        """
        Save the register's description into the dictionary.
        reg_info_tree is based on the register_information.xml.
        @param reg_info_tree: XML tree
        @param register: register which you want to get the description
        """
        # temporary variables for register main table idescription dictionary
        reg_index = ""
        reg_main_description = ""

        for data in register.childNodes:
            if data.nodeType == reg_info_tree.ELEMENT_NODE and data.nodeName == "Index":
                for index in data.childNodes:
                    reg_index = index.nodeValue
            if data.nodeType == reg_info_tree.ELEMENT_NODE and data.nodeName == "Description":
                for description in data.childNodes:
                    reg_main_description = description.nodeValue

            # Add description for register main table
            if reg_index != "" and reg_main_description != "":
                self.RegisterDescriptionDict[reg_index] = reg_main_description

            if data.nodeType == reg_info_tree.ELEMENT_NODE and data.nodeName == "Details":
                # declare register sub table description dictionary about this index
                self.RegisterSubGridDict[reg_index] = []

                for detail in data.childNodes:
                    if detail.nodeType == reg_info_tree.ELEMENT_NODE and detail.nodeName == "Detail":
                        # If it depends on the property(ESC type, PDI type, FMMU number, SM number)
                        for property, type, value in [("esc", "type", self.ESCType),
                                                      ("pdi", "type", self.PDIType),
                                                      ("fmmu", "number", self.FMMUNumber),
                                                      ("sm", "number", self.SMNumber)]:
                            if property in detail.attributes.keys():
                                if type == "type":
                                    if detail.attributes[property].value == value:
                                        self.GetRegisterDetailInfo(reg_info_tree, reg_index, detail)
                                        break
                                else:  # type == "number"
                                    if detail.attributes[property].value < value:
                                        self.GetRegisterDetailInfo(reg_info_tree, reg_index, detail)
                                        break
                            else:
                                self.GetRegisterDetailInfo(reg_info_tree, reg_index, detail)
                                break

    def GetRegisterDetailInfo(self, reg_info_tree, reg_index, detail):
        """
        Get the resgister's detailed description(for sub table) from the reg_info_tree.
        @param reg_info_tree: XML tree (register_information.xml)
        @param reg_index: index of the register
        @param detail: description of the register
        """
        # temporary variables for register sub table description dictionary
        # - It is initialized in every sub description
        reg_bit_range = ""
        reg_sub_description = ""
        reg_enum_dictionary = {}

        for detail_data in detail.childNodes:
            if detail_data.nodeType == reg_info_tree.ELEMENT_NODE and detail_data.nodeName == "Range":
                for range in detail_data.childNodes:
                    reg_bit_range = range.nodeValue
            if detail_data.nodeType == reg_info_tree.ELEMENT_NODE and detail_data.nodeName == "Description":
                for description in detail_data.childNodes:
                    reg_sub_description = description.nodeValue

            if detail_data.nodeType == reg_info_tree.ELEMENT_NODE and detail_data.nodeName == "Enum":
                for enum in detail_data.childNodes:
                    if enum.nodeType == reg_info_tree.ELEMENT_NODE and enum.nodeName == "item":

                        # temporary variables for a description of each value
                        # For example, if the bit is 1, it is 'enabled'('On', 'True', etc.),
                        # otherwise 'disabled'('Off', 'False', etc.).
                        reg_sub_value = ""
                        reg_sub_value_description = ""

                        for item in enum.childNodes:
                            if item.nodeType == reg_info_tree.ELEMENT_NODE and item.nodeName == "value":
                                for value in item.childNodes:
                                    reg_sub_value = value.nodeValue
                            if item.nodeType == reg_info_tree.ELEMENT_NODE and item.nodeName == "Description":
                                for description in item.childNodes:
                                    reg_sub_value_description = description.nodeValue

                            # Add a description of each value to register enum dictionary
                            if reg_sub_value != "" and reg_sub_value_description != "":
                                reg_enum_dictionary[reg_sub_value] = reg_sub_value_description

        # add a description to register sub table description dictionary
        if reg_bit_range != "" and reg_sub_description != "":
            self.RegisterSubGridDict[reg_index].append([reg_bit_range,
                                                        reg_sub_description,
                                                        reg_enum_dictionary])

    def ParseData(self):
        """
        Transform the data into dec, hex, string, and description
        """
        row_data = []
        self.RegMonitorData = []
        reg_word = ""

        reg_data = self.Controler.CommonMethod.RegData.split()

        # loop for register(0x0000:0x0fff)
        for address in range(0x1000):
            # arrange 2 Bytes of register data
            reg_word = reg_data[address].split('x')[1] + reg_word
            if (address % 2) == 1:
                # append address
                hex_address = "{:0>4x}".format(address-1)
                row_data.append(hex_address)

                # append description
                if hex_address in self.RegisterDescriptionDict:
                    row_data.append(self.RegisterDescriptionDict[hex_address])
                else:
                    row_data.append("")

                # append Decimal value
                row_data.append(str(int(reg_word, 16)))

                # append Hex value
                row_data.append('0x'+reg_word)

                # append ASCII value
                char_data = ""
                for iter in range(2):
                    if int(reg_word[iter*2:iter*2+2], 16) >= 32 and int(reg_word[iter*2:iter*2+2], 16) <= 126:
                        char_data = char_data + chr(int(reg_word[iter*2:iter*2+2], 16))
                    else:
                        char_data = char_data + "."
                row_data.append(char_data)

                self.RegMonitorData.append(row_data)
                reg_word = ""  # initialize regWord
                row_data = []

    def OnReloadButton(self, event):
        """
        Handle the click event of the 'Reload' button.
        Get the data from registers again, and update the table.
        @param event: wx.EVT_BUTTON object
        """
        # Check whether beremiz connected or not.
        check_connect_flag = self.Controler.CommonMethod.CheckConnect(False)
        if check_connect_flag:
            self.LoadData()
            self.BasicSetData()
            self.ParseData()
            # set data into UI
            if self.CompactFlag:
                self.ToggleCompactViewCheckbox(True)
            else:
                for index in range(4):
                    self.RegisterNotebook.RegPage[index].UpdateMainTable(self.MainRow[index], self.MainCol,
                                                                         self.PageRange[index][0], self.PageRange[index][1],
                                                                         self.RegMonitorData)

    def ToggleCompactViewCheckbox(self, event):
        """
        Handles the event of the 'Compact view' check box.
        If it's checked, show only the registers that have a description.
        If not, show all the registers.
        @param event: wx.EVT_CHECKBOX object
        """

        # If "Compact View" Checkbox is True
        # 'event' is argument of this method or event of checkbox.
        if event is True or event.GetEventObject().GetValue():
            self.CompactFlag = True

            reg_compact_data = []
            page_row = [0, 0, 0, 0]
            for index in range(4):
                self.PageRange[index] = [0, 0]

            for reg_row_data in self.RegMonitorData:
                if reg_row_data[1] != "":
                    # data structure for "compact view"
                    reg_compact_data.append(reg_row_data)
                    # count for each register notebooks' row
                    # It compare with register's address.
                    for index in range(4):
                        if int('0x'+reg_row_data[0], 16) < (index+1)*1024:
                            page_row[index] += 1
                            break

            # Setting tables' rows and cols, range for compact view
            for index in range(4):
                self.MainRow[index] = page_row[index]
                self.PageRange[index][1] = page_row[index]
                for iter in range(index):
                    self.PageRange[index][0] += page_row[iter]
                    self.PageRange[index][1] += page_row[iter]

            # Update table
            for index in range(4):
                self.RegisterNotebook.RegPage[index].UpdateMainTable(
                    self.MainRow[index],
                    self.MainCol,
                    self.PageRange[index][0],
                    self.PageRange[index][1],
                    reg_compact_data)

        # Compact View Checkbox is False
        else:
            self.CompactFlag = False
            # Setting original rows, cols and range
            self.MainRow = [512, 512, 512, 512]
            self.PageRange = []

            for index in range(4):
                self.PageRange.append([512*index, 512*(index+1)])

            # Update table
            for index in range(4):
                self.RegisterNotebook.RegPage[index].UpdateMainTable(
                    self.MainRow[index],
                    self.MainCol,
                    self.PageRange[index][0],
                    self.PageRange[index][1],
                    self.RegMonitorData)


# -------------------------------------------------------------------------------
#                    For Register Access Notebook (divide index range)
# -------------------------------------------------------------------------------
class RegisterNotebook(wx.Notebook):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: RegisterAccessPanel object
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Notebook.__init__(self, parent, id=-1)

        self.parent = parent
        self.Controler = controler

        # Initialize pages
        self.RegPage = []
        pages = 4
        for dummy in range(pages):
            self.RegPage.append(None)

        for index in range(pages):
            self.RegPage[index] = RegisterNotebookPanel(self, self.Controler,
                                                        parent.MainRow[index], parent.MainCol)
            self.AddPage(self.RegPage[index],
                         "0x"+"{:0>4x}".format(index*1024)+" - 0x"+"{:0>4x}".format((index+1)*1024-1))


# -------------------------------------------------------------------------------
#                    For Register Access Notebook Panel
#                  (Main UI : including main, sub table)
# -------------------------------------------------------------------------------
class RegisterNotebookPanel(wx.Panel):
    def __init__(self, parent, controler, row, col):
        """
        Constructor
        @param parent: RegisterAccessPanel object
        @param controler: _EthercatSlaveCTN class in EthercatSlave.py
        @param row, col: size of the table
        """
        wx.Panel.__init__(self, parent, -1)

        self.parent = parent
        self.Controler = controler
        self.Row = row
        self.Col = col
        sub_row = 0
        sub_col = 4

        self.Sizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=30)

        self.MainTable = RegisterMainTable(self, self.Row, self.Col, self.Controler)
        self.SubTable = RegisterSubTable(self, sub_row, sub_col)

        self.SubTable.CreateGrid(sub_row, sub_col)
        self.SubTable.SetValue(self, [])

        self.Sizer.AddMany([self.MainTable, self.SubTable])

        self.SetSizer(self.Sizer)

    def UpdateMainTable(self, row, col, low_index, high_index, data):
        """
        Updates main table.
        It's done by deleting the main table and creating it again.
        @param row, col: size of the table
        @param low_index: the lowest index of the page
        @param high_index: the highest index of the page
        @param data: data
        """
        self.MainTable.Destroy()
        self.MainTable = RegisterMainTable(self, row, col, self.Controler)
        self.Sizer.Detach(self.SubTable)
        self.Sizer.AddMany([self.MainTable, self.SubTable])
        self.SetSizer(self.Sizer)
        self.MainTable.CreateGrid(row, col)
        self.MainTable.SetValue(self, data, low_index, high_index)
        self.MainTable.Update()

    def UpdateSubTable(self, row, col, data):
        """
        Updates sub table.
        It's done by deleting the sub table and creating it again.
        @param row, col: size of the table
        @param data: data
        """
        self.SubTable.Destroy()
        self.SubTable = RegisterSubTable(self, row, col)
        self.Sizer.Detach(self.MainTable)
        self.Sizer.AddMany([self.MainTable, self.SubTable])
        self.Sizer.Layout()
        self.SetSizer(self.Sizer)
        self.SubTable.CreateGrid(row, col)
        self.SubTable.SetValue(self, data)
        self.SubTable.Update()


# -------------------------------------------------------------------------------
#                    For Register Access Notebook Panel (Main Table)
# -------------------------------------------------------------------------------
class RegisterMainTable(wx.grid.Grid):
    def __init__(self, parent, row, col, controler):
        """
            Constructor
            @param parent: RegisterNotebook object
            @param row, col: size of the table
            @param controler: _EthercatSlaveCTN class in EthercatSlave.py
            """
        self.parent = parent
        self.Data = {}
        self.Row = row
        self.Col = col
        self.Controler = controler
        self.RegisterAccessPanel = self.parent.parent.parent

        wx.grid.Grid.__init__(self, parent, -1, size=(820, 300),
                              style=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        for evt, mapping_method in [(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectCell),
                                    (wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectCell),
                                    (wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnRegModifyDialog)]:
            self.Bind(evt, mapping_method)

    def SetValue(self, parent, reg_monitor_data, low_index, high_index):
        """
            Set the RegMonitorData into the main table.
            @param parent: RegisterNotebook object
            @param reg_monitor_data: data
            @param low_index: the lowest index of the page
            @param high_index: the highest index of the page
            """
        self.RegMonitorData = reg_monitor_data

        # set label name and size
        register_maintable_label = [(0, "Description"), (1, "Dec"),
                                    (2, "Hex"), (3, "Char")]

        for (index, label) in register_maintable_label:
            self.SetColLabelValue(index, label)

        self.SetColSize(0, 200)

        # if reg_monitor_data is 0, it is initialization of register access.
        if reg_monitor_data == 0:
            return 0

        # set data into UI
        row = col = 0
        for row_index in reg_monitor_data[low_index:high_index]:
            col = 0
            self.SetRowLabelValue(row, row_index[0])
            for data_index in range(4):
                self.SetCellValue(row, col, row_index[data_index+1])
                self.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTER)
                self.SetReadOnly(row, col, True)
                col = col + 1
            row = row + 1

    def OnSelectCell(self, event):
        """
            Handles the event of the cell of the main table.
            @param event: wx.grid object (left click)
            """
        # if reg_monitor_data is 0, it is initialization of register access.
        if self.RegMonitorData == 0:
            event.Skip()
            return 0

        sub_row = 0
        sub_col = 4

        address = self.GetRowLabelValue(event.GetRow())

        reg_sub_grid_data = []

        BIT_RANGE, NAME, DESCRIPTIONS = range(3)

        # Check if this register's detail description is exist or not,
        # and create data structure for the detail description table ; sub grid
        if address in self.RegisterAccessPanel.RegisterSubGridDict:
            for element in self.RegisterAccessPanel.RegisterSubGridDict[address]:
                row_data = []
                row_data.append(element[BIT_RANGE])
                row_data.append(element[NAME])
                bin_data = "{:0>16b}".format(int(self.GetCellValue(event.GetRow(), 1)))
                value_range = element[BIT_RANGE].split('-')
                value = (bin_data[8:16][::-1]+bin_data[0:8][::-1])[int(value_range[0]):(int(value_range[-1])+1)][::-1]
                row_data.append(str(int(('0b'+str(value)), 2)))
                if value in element[DESCRIPTIONS]:
                    row_data.append(element[DESCRIPTIONS][value])
                else:
                    row_data.append('')
                reg_sub_grid_data.append(row_data)
                sub_row = sub_row + 1

        self.parent.UpdateSubTable(sub_row, sub_col, reg_sub_grid_data)
        # event.Skip() updates UI of selecting cell
        event.Skip()

    def OnRegModifyDialog(self, event):
        """
        Handle the event of the cell of the main table.
        Display the window where the user modifies the value of the cell.
        @param event: wx.grid object (double click)
            """
        # user can enter a value in case that user double-clicked 'Dec' or 'Hex' value.
        if event.GetCol() == 1 or event.GetCol() == 2:
            dlg = wx.TextEntryDialog(self, _("Enter hex(0xnnnn) or dec(n) value"),
                                     _("Register Modify Dialog"), style=wx.OK | wx.CANCEL)

            # Setting value in initial dialog value
            start_value = self.GetCellValue(event.GetRow(), event.GetCol())
            dlg.SetValue(start_value)

            if dlg.ShowModal() == wx.ID_OK:
                try:
                    # It int(input) success, this input is dev or hex value.
                    # Otherwise, it's error, so it goes except.
                    int(dlg.GetValue(), 0)

                    # reg_write
                    # ex) ethercat reg_write -p 0 -t uint16 0x0000 0x0000
                    return_val = self.Controler.CommonMethod.RegWrite('0x'+self.GetRowLabelValue(event.GetRow()), dlg.GetValue())

                    if len(return_val) == 0:
                        # set dec
                        self.SetCellValue(event.GetRow(), 1, str(int(dlg.GetValue(), 0)))
                        # set hex
                        hex_data = '0x'+"{:0>4x}".format(int(dlg.GetValue(), 0))
                        self.SetCellValue(event.GetRow(), 2, hex_data)
                        # set char
                        char_data = ""
                        # If hex_data is been able to convert to ascii code, append ascii code.
                        for iter in range(2):
                            if int(hex_data[(iter+1)*2:(iter+2)*2], 16) >= 32 and int(hex_data[(iter+1)*2:(iter+2)*2], 16) <= 126:
                                char_data = char_data + chr(int(hex_data[(iter+1)*2:(iter+2)*2], 16))
                            else:
                                char_data = char_data + "."

                        self.SetCellValue(event.GetRow(), 3, char_data)

                    else:
                        self.Controler.CommonMethod.CreateErrorDialog(_('You can\'t modify it. This register is read-only or it\'s not connected.'))

                except ValueError:
                    self.Controler.CommonMethod.CreateErrorDialog(_('You entered wrong value. You can enter dec or hex value only.'))


# -------------------------------------------------------------------------------
#                    For Register Access Notebook Panel (Sub Table)
# -------------------------------------------------------------------------------
class RegisterSubTable(wx.grid.Grid):
    def __init__(self, parent, row, col):
        """
         Constructor
         @param parent: RegisterNotebook object
         @param row, col: size of the table
        """
        self.parent = parent
        self.Data = {}
        self.Row = row
        self.Col = col

        wx.grid.Grid.__init__(self, parent, -1, size=(820, 150),
                              style=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

    def SetValue(self, parent, data):
        """
            Set the data into the subtable.
            @param parent: RegisterNotebook object
            @param data: data
            """
        # lset label name and size
        Register_SubTable_Label = [(0, "Bits"), (1, "Name"),
                                   (2, "Value"), (3, "Enum")]

        for (index, label) in Register_SubTable_Label:
            self.SetColLabelValue(index, label)

        self.SetColSize(1, 200)
        self.SetColSize(3, 200)

        # set data into table
        row = col = 0
        for rowData in data:
            col = 0
            for element in rowData:
                self.SetCellValue(row, col, element)
                self.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTER)
                self.SetReadOnly(row, col, True)
                col = col + 1
            row = row + 1


# -------------------------------------------------------------------------------
#                    For Master State Panel
# -------------------------------------------------------------------------------
class MasterStatePanelClass(wx.Panel):
    def __init__(self, parent, controler):
        """
        Constructor
        @param parent: wx.ScrollWindow object
        @Param controler: _EthercatSlaveCTN class in EthercatSlave.py
        """
        wx.Panel.__init__(self, parent, -1, (0, 0),
                          size=wx.DefaultSize, style=wx.SUNKEN_BORDER)
        self.Controler = controler
        self.parent = parent
        self.StaticBox = {}
        self.StaticText = {}
        self.TextCtrl = {}

        # ----------------------- Main Sizer and Update Button --------------------------------------------
        self.MasterStateSizer = {"main": wx.BoxSizer(wx.VERTICAL)}
        for key, attr in [
                ("innerMain",           [1, 10, 2, 10]),
                ("innerTopHalf",        [2, 10, 1, 10]),
                ("innerBottomHalf",     [2, 10, 1, 10]),
                ("innerMasterState",    [2, 10, 3, 10]),
                ("innerDeviceInfo",     [4, 10, 3, 10]),
                ("innerFrameInfo",      [4, 10, 5, 10])]:
            self.MasterStateSizer[key] = wx.FlexGridSizer(cols=attr[0], hgap=attr[1], rows=attr[2], vgap=attr[3])

        self.UpdateButton = wx.Button(self, label=_('Update'))
        self.UpdateButton.Bind(wx.EVT_BUTTON, self.OnButtonClick)

        for key, label in [
                ('masterState', 'EtherCAT Master State'),
                ('deviceInfo', 'Ethernet Network Card Information'),
                ('frameInfo', 'Network Frame Information')]:
            self.StaticBox[key] = wx.StaticBox(self, label=_(label))
            self.MasterStateSizer[key] = wx.StaticBoxSizer(self.StaticBox[key])

        # ----------------------- Master State -----------------------------------------------------------
        for key, label in [
                ('Phase', 'Phase:'),
                ('Active', 'Active:'),
                ('Slaves', 'Slave Count:')]:
            self.StaticText[key] = wx.StaticText(self, label=_(label))
            self.TextCtrl[key] = wx.TextCtrl(self, size=wx.Size(130, 24), style=wx.TE_READONLY)
            self.MasterStateSizer['innerMasterState'].AddMany([self.StaticText[key], self.TextCtrl[key]])

        self.MasterStateSizer['masterState'].AddSizer(self.MasterStateSizer['innerMasterState'])

        # ----------------------- Ethernet Network Card Information ---------------------------------------
        for key, label in [
                ('Main', 'MAC Address:'),
                ('Link', 'Link State:'),
                ('Tx frames', 'Tx Frames:'),
                ('Rx frames', 'Rx Frames:'),
                ('Lost frames', 'Lost Frames:')]:
            self.StaticText[key] = wx.StaticText(self, label=_(label))
            self.TextCtrl[key] = wx.TextCtrl(self, size=wx.Size(130, 24), style=wx.TE_READONLY)
            self.MasterStateSizer['innerDeviceInfo'].AddMany([self.StaticText[key], self.TextCtrl[key]])

        self.MasterStateSizer['deviceInfo'].AddSizer(self.MasterStateSizer['innerDeviceInfo'])

        # ----------------------- Network Frame Information -----------------------------------------------
        for key, label in [
                ('Tx frame rate [1/s]', 'Tx Frame Rate [1/s]:'),
                ('Rx frame rate [1/s]', 'Tx Rate [kByte/s]:'),
                ('Loss rate [1/s]', 'Loss Rate [1/s]:'),
                ('Frame loss [%]', 'Frame Loss [%]:')]:
            self.StaticText[key] = wx.StaticText(self, label=_(label))
            self.MasterStateSizer['innerFrameInfo'].Add(self.StaticText[key])
            self.TextCtrl[key] = {}
            for index in ['0', '1', '2']:
                self.TextCtrl[key][index] = wx.TextCtrl(self, size=wx.Size(130, 24), style=wx.TE_READONLY)
                self.MasterStateSizer['innerFrameInfo'].Add(self.TextCtrl[key][index])

        self.MasterStateSizer['frameInfo'].AddSizer(self.MasterStateSizer['innerFrameInfo'])

        # --------------------------------- Main Sizer ----------------------------------------------------
        for key, sub, in [
                ('innerTopHalf', ['masterState', 'deviceInfo']),
                ('innerBottomHalf', ['frameInfo']),
                ('innerMain', ['innerTopHalf', 'innerBottomHalf'])
        ]:
            for key2 in sub:
                self.MasterStateSizer[key].AddSizer(self.MasterStateSizer[key2])

        self.MasterStateSizer['main'].AddSizer(self.UpdateButton)
        self.MasterStateSizer['main'].AddSizer(self.MasterStateSizer['innerMain'])

        self.SetSizer(self.MasterStateSizer['main'])

    def OnButtonClick(self, event):
        """
        Handle the event of the 'Update' button.
        Update the data of the master state.
        @param event: wx.EVT_BUTTON object
        """
        if self.Controler.GetCTRoot()._connector is not None:
            self.MasterState = self.Controler.CommonMethod.GetMasterState()
            # Update each TextCtrl
            if self.MasterState:
                for key in self.TextCtrl:
                    if isinstance(self.TextCtrl[key], dict):
                        for index in self.TextCtrl[key]:
                            self.TextCtrl[key][index].SetValue(self.MasterState[key][int(index)])
                    else:
                        self.TextCtrl[key].SetValue(self.MasterState[key][0])
        else:
            self.Controler.CommonMethod.CreateErrorDialog(_('PLC not connected!'))
