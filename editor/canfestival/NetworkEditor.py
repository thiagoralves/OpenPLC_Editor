#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import
import wx

from networkeditortemplate import NetworkEditorTemplate
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor

[
    ID_NETWORKEDITOR,
] = [wx.NewId() for _init_ctrls in range(1)]

[
    ID_NETWORKEDITORCONFNODEMENUADDSLAVE,
    ID_NETWORKEDITORCONFNODEMENUREMOVESLAVE,
    ID_NETWORKEDITORCONFNODEMENUMASTER,
] = [wx.NewId() for _init_coll_ConfNodeMenu_Items in range(3)]

[
    ID_NETWORKEDITORMASTERMENUNODEINFOS, ID_NETWORKEDITORMASTERMENUDS301PROFILE,
    ID_NETWORKEDITORMASTERMENUDS302PROFILE, ID_NETWORKEDITORMASTERMENUDSOTHERPROFILE,
    ID_NETWORKEDITORMASTERMENUADD,
] = [wx.NewId() for _init_coll_MasterMenu_Items in range(5)]

[
    ID_NETWORKEDITORADDMENUSDOSERVER, ID_NETWORKEDITORADDMENUSDOCLIENT,
    ID_NETWORKEDITORADDMENUPDOTRANSMIT, ID_NETWORKEDITORADDMENUPDORECEIVE,
    ID_NETWORKEDITORADDMENUMAPVARIABLE, ID_NETWORKEDITORADDMENUUSERTYPE,
] = [wx.NewId() for _init_coll_AddMenu_Items in range(6)]


class NetworkEditor(ConfTreeNodeEditor, NetworkEditorTemplate):

    ID = ID_NETWORKEDITOR
    CONFNODEEDITOR_TABS = [
        (_("CANOpen network"), "_create_NetworkEditor")]

    def _create_NetworkEditor(self, prnt):
        self.NetworkEditor = wx.Panel(
            id=-1, parent=prnt, pos=wx.Point(0, 0),
            size=wx.Size(0, 0), style=wx.TAB_TRAVERSAL)

        NetworkEditorTemplate._init_ctrls(self, self.NetworkEditor)

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=1, vgap=0)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)

        main_sizer.AddWindow(self.NetworkNodes, 0, border=5, flag=wx.GROW | wx.ALL)

        self.NetworkEditor.SetSizer(main_sizer)

        return self.NetworkEditor

    def __init__(self, parent, controler, window):
        ConfTreeNodeEditor.__init__(self, parent, controler, window)
        NetworkEditorTemplate.__init__(self, controler, window, False)

        self.RefreshNetworkNodes()
        self.RefreshBufferState()

    def __del__(self):
        self.Controler.OnCloseEditor(self)

    def GetConfNodeMenuItems(self):
        add_menu = [(wx.ITEM_NORMAL, (_('SDO Server'), ID_NETWORKEDITORADDMENUSDOSERVER, '', self.OnAddSDOServerMenu)),
                    (wx.ITEM_NORMAL, (_('SDO Client'), ID_NETWORKEDITORADDMENUSDOCLIENT, '', self.OnAddSDOClientMenu)),
                    (wx.ITEM_NORMAL, (_('PDO Transmit'), ID_NETWORKEDITORADDMENUPDOTRANSMIT, '', self.OnAddPDOTransmitMenu)),
                    (wx.ITEM_NORMAL, (_('PDO Receive'), ID_NETWORKEDITORADDMENUPDORECEIVE, '', self.OnAddPDOReceiveMenu)),
                    (wx.ITEM_NORMAL, (_('Map Variable'), ID_NETWORKEDITORADDMENUMAPVARIABLE, '', self.OnAddMapVariableMenu)),
                    (wx.ITEM_NORMAL, (_('User Type'), ID_NETWORKEDITORADDMENUUSERTYPE, '', self.OnAddUserTypeMenu))]

        profile = self.Manager.GetCurrentProfileName()
        if profile not in ("None", "DS-301"):
            other_profile_text = _("%s Profile") % profile
            add_menu.append((wx.ITEM_SEPARATOR, None))
            for text, _indexes in self.Manager.GetCurrentSpecificMenu():
                add_menu.append((wx.ITEM_NORMAL, (text, wx.NewId(), '', self.GetProfileCallBack(text))))
        else:
            other_profile_text = _('Other Profile')

        master_menu = [(wx.ITEM_NORMAL, (_('DS-301 Profile'), ID_NETWORKEDITORMASTERMENUDS301PROFILE, '', self.OnCommunicationMenu)),
                       (wx.ITEM_NORMAL, (_('DS-302 Profile'), ID_NETWORKEDITORMASTERMENUDS302PROFILE, '', self.OnOtherCommunicationMenu)),
                       (wx.ITEM_NORMAL, (other_profile_text, ID_NETWORKEDITORMASTERMENUDSOTHERPROFILE, '', self.OnEditProfileMenu)),
                       (wx.ITEM_SEPARATOR, None),
                       (add_menu, (_('Add'), ID_NETWORKEDITORMASTERMENUADD))]

        return [(wx.ITEM_NORMAL, (_('Add slave'), ID_NETWORKEDITORCONFNODEMENUADDSLAVE, '', self.OnAddSlaveMenu)),
                (wx.ITEM_NORMAL, (_('Remove slave'), ID_NETWORKEDITORCONFNODEMENUREMOVESLAVE, '', self.OnRemoveSlaveMenu)),
                (wx.ITEM_SEPARATOR, None),
                (master_menu, (_('Master'), ID_NETWORKEDITORCONFNODEMENUMASTER))]

    def RefreshMainMenu(self):
        pass

    def RefreshConfNodeMenu(self, confnode_menu):
        confnode_menu.Enable(ID_NETWORKEDITORCONFNODEMENUMASTER, self.NetworkNodes.GetSelection() == 0)

    def RefreshView(self):
        ConfTreeNodeEditor.RefreshView(self)
        self.RefreshCurrentIndexList()

    def RefreshBufferState(self):
        NetworkEditorTemplate.RefreshBufferState(self)
        self.ParentWindow.RefreshTitle()
        self.ParentWindow.RefreshFileMenu()
        self.ParentWindow.RefreshEditMenu()
        self.ParentWindow.RefreshPageTitles()

    def OnNodeSelectedChanged(self, event):
        NetworkEditorTemplate.OnNodeSelectedChanged(self, event)
        wx.CallAfter(self.ParentWindow.RefreshEditMenu)
