#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov <andrej.skvortzov@gmail.com>
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

from graphics.GraphicCommons import LEFTRAIL, RIGHTRAIL
from graphics.LD_Objects import LD_PowerRail
from dialogs.BlockPreviewDialog import BlockPreviewDialog

# -------------------------------------------------------------------------------
#                    Set Ladder Power Rail Parameters Dialog
# -------------------------------------------------------------------------------


class LDPowerRailDialog(BlockPreviewDialog):
    """
    Class that implements a dialog for defining parameters of a power rail graphic
    element
    """
    def __init__(self, parent, controller, tagname):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        """
        BlockPreviewDialog.__init__(self, parent, controller, tagname,
                                    title=_('Power Rail Properties'))

        # Init common sizers
        self._init_sizers(2, 0, 5, None, 2, 1)

        # Create label for connection type
        type_label = wx.StaticText(self, label=_('Type:'))
        self.LeftGridSizer.AddWindow(type_label, flag=wx.GROW)

        # Create radio buttons for selecting power rail type
        self.TypeRadioButtons = {}
        first = True
        for type, label in [(LEFTRAIL, _('Left PowerRail')),
                            (RIGHTRAIL, _('Right PowerRail'))]:
            radio_button = wx.RadioButton(self, label=label,
                                          style=(wx.RB_GROUP if first else 0))
            radio_button.SetValue(first)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnTypeChanged, radio_button)
            self.LeftGridSizer.AddWindow(radio_button, flag=wx.GROW)
            self.TypeRadioButtons[type] = radio_button
            first = False

        # Create label for power rail pin number
        pin_number_label = wx.StaticText(self, label=_('Pin number:'))
        self.LeftGridSizer.AddWindow(pin_number_label, flag=wx.GROW)

        # Create spin control for defining power rail pin number
        self.PinNumber = wx.SpinCtrl(self, min=1, max=50,
                                     style=wx.SP_ARROW_KEYS)
        self.PinNumber.SetValue(1)
        self.Bind(wx.EVT_SPINCTRL, self.OnPinNumberChanged, self.PinNumber)
        self.LeftGridSizer.AddWindow(self.PinNumber, flag=wx.GROW)

        # Add preview panel and associated label to sizers
        self.RightGridSizer.AddWindow(self.PreviewLabel, flag=wx.GROW)
        self.RightGridSizer.AddWindow(self.Preview, flag=wx.GROW)

        # Add buttons sizer to sizers
        self.MainSizer.AddSizer(
            self.ButtonSizer, border=20,
            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        self.Fit()

        # Left Power Rail radio button is default control having keyboard focus
        self.TypeRadioButtons[LEFTRAIL].SetFocus()

    def GetMinElementSize(self):
        """
        Get minimal graphic element size
        @return: Tuple containing minimal size (width, height) or None if no
        element defined
        """
        return self.Element.GetMinSize(True)

    def GetPowerRailType(self):
        """
        Return type selected for power rail
        @return: Type selected (LEFTRAIL or RIGHTRAIL)
        """
        return (LEFTRAIL
                if self.TypeRadioButtons[LEFTRAIL].GetValue()
                else RIGHTRAIL)

    def SetValues(self, values):
        """
        Set default power rail parameters
        @param values: Power rail parameters values
        """
        # For each parameters defined, set corresponding control value
        for name, value in values.items():

            # Parameter is power rail type
            if name == "type":
                self.TypeRadioButtons[value].SetValue(True)

            # Parameter is power rail pin number
            elif name == "pin_number":
                self.PinNumber.SetValue(value)

    def GetValues(self):
        """
        Return power rail parameters defined in dialog
        @return: {parameter_name: parameter_value,...}
        """
        values = {
            "type": self.GetPowerRailType(),
            "pin_number": self.PinNumber.GetValue()}
        values["width"], values["height"] = self.Element.GetSize()
        return values

    def OnTypeChanged(self, event):
        """
        Called when power rail type changed
        @param event: wx.RadioButtonEvent
        """
        self.RefreshPreview()
        event.Skip()

    def OnPinNumberChanged(self, event):
        """
        Called when power rail pin number value changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()

    def DrawPreview(self):
        """
        Refresh preview panel of graphic element
        Override BlockPreviewDialog function
        """

        # Set graphic element displayed, creating a power rail element
        self.Element = LD_PowerRail(self.Preview,
                                    self.GetPowerRailType(),
                                    connectors=self.PinNumber.GetValue())

        return BlockPreviewDialog.DrawPreview(self)
