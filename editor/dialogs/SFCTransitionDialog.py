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

from graphics.SFC_Objects import SFC_Transition
from dialogs.BlockPreviewDialog import BlockPreviewDialog

# -------------------------------------------------------------------------------
#                        Set Transition Parameters Dialog
# -------------------------------------------------------------------------------


class SFCTransitionDialog(BlockPreviewDialog):
    """
    Class that implements a dialog for defining parameters of a transition graphic
    element
    """

    def __init__(self, parent, controller, tagname, connection=True):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        @param connection: True if transition value can be defined by a
        connection (default: True)
        """
        BlockPreviewDialog.__init__(self, parent, controller, tagname,
                                    title=_('Edit transition'))

        # Init common sizers
        self._init_sizers(2, 0, 8, None, 2, 1)

        # Create label for transition type
        type_label = wx.StaticText(self, label=_('Type:'))
        self.LeftGridSizer.AddWindow(type_label, flag=wx.GROW)

        # Create combo box for selecting reference value
        reference = wx.ComboBox(self, style=wx.CB_READONLY)
        reference.Append("")
        for transition in controller.GetEditedElementTransitions(tagname):
            reference.Append(transition)
        self.Bind(wx.EVT_COMBOBOX, self.OnReferenceChanged, reference)

        # Create Text control for defining inline value
        inline = wx.TextCtrl(self)
        self.Bind(wx.EVT_TEXT, self.OnInlineChanged, inline)

        # Create radio buttons for selecting power rail type
        self.TypeRadioButtons = {}
        first = True
        for type, label, control in [('reference', _('Reference'), reference),
                                     ('inline', _('Inline'), inline),
                                     ('connection', _('Connection'), None)]:
            radio_button = wx.RadioButton(self, label=label,
                                          style=(wx.RB_GROUP if first else 0))
            radio_button.SetValue(first)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnTypeChanged, radio_button)
            self.LeftGridSizer.AddWindow(radio_button, flag=wx.GROW)
            if control is not None:
                control.Enable(first)
                self.LeftGridSizer.AddWindow(control, flag=wx.GROW)
            self.TypeRadioButtons[type] = (radio_button, control)
            first = False

        # Create label for transition priority
        priority_label = wx.StaticText(self, label=_('Priority:'))
        self.LeftGridSizer.AddWindow(priority_label, flag=wx.GROW)

        # Create spin control for defining priority value
        self.Priority = wx.SpinCtrl(self, min=0, style=wx.SP_ARROW_KEYS)
        self.Bind(wx.EVT_TEXT, self.OnPriorityChanged, self.Priority)
        self.LeftGridSizer.AddWindow(self.Priority, flag=wx.GROW)

        # Add preview panel and associated label to sizers
        self.RightGridSizer.AddWindow(self.PreviewLabel, flag=wx.GROW)
        self.RightGridSizer.AddWindow(self.Preview, flag=wx.GROW)

        # Add buttons sizer to sizers
        self.MainSizer.AddSizer(
            self.ButtonSizer, border=20,
            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.Fit()

        # Reference radio button is default control having keyboard focus
        self.TypeRadioButtons["reference"][0].SetFocus()

    def GetTransitionType(self):
        """
        Return type selected for SFC transition and associated value
        @return: Type selected and associated value (None if no value)
        """
        # Go through radio buttons and return type and value associated to the
        # one that is selected
        for type, (radio, control) in self.TypeRadioButtons.iteritems():
            if radio.GetValue():
                if isinstance(control, wx.ComboBox):
                    return type, control.GetStringSelection()
                elif isinstance(control, wx.TextCtrl):
                    return type, control.GetValue()
                else:
                    return type, None
        return None, None

    def SetValues(self, values):
        """
        Set default SFC transition parameters
        @param values: Transition parameters values
        """
        # Extract transition value according to type
        type_value = values.get("value", None)

        # For each parameters defined, set corresponding control value
        for name, value in values.items():

            # Parameter is SFC transition priority
            if name == "priority":
                self.Priority.SetValue(values["priority"])

            # Parameter is SFC transition type
            elif name == "type":
                for type, (radio, control) in self.TypeRadioButtons.iteritems():
                    radio.SetValue(type == value)
                    if control is not None:
                        # Enable associated control to type and set value
                        control.Enable(type == value)
                        if type == value:
                            if isinstance(control, wx.ComboBox):
                                control.SetStringSelection(type_value)
                            elif isinstance(control, wx.TextCtrl):
                                control.ChangeValue(type_value)

        # Refresh preview panel
        self.RefreshPreview()

    def GetValues(self):
        """
        Return SFC transition parameters defined in dialog
        @return: {parameter_name: parameter_value,...}
        """
        values = {"priority": self.Priority.GetValue()}
        values["type"], values["value"] = self.GetTransitionType()
        values["width"], values["height"] = self.Element.GetSize()
        return values

    def OnOK(self, event):
        """
        Called when dialog OK button is pressed
        Test if parameters defined are valid
        @param event: wx.Event from OK button
        """
        message = None

        # Get transition type and value associated
        type, value = self.GetTransitionType()

        # Test that value associated to type is defined
        if type != "connection" and value == "":
            message = _("Form isn't complete. %s must be filled!") % type

        # Show error message if an error is detected
        if message is not None:
            self.ShowErrorMessage(message)

        else:
            # Call BlockPreviewDialog function
            BlockPreviewDialog.OnOK(self, event)

    def OnTypeChanged(self, event):
        """
        Called when transition type changed
        @param event: wx.RadioButtonEvent
        """
        # Refresh sensibility of control associated to transition types
        for _type, (radio, control) in self.TypeRadioButtons.iteritems():
            if control is not None:
                control.Enable(radio.GetValue())

        # Refresh preview panel
        self.RefreshPreview()
        event.Skip()

    def OnReferenceChanged(self, event):
        """
        Called when SFC transition reference value changed
        @param event: wx.ComboBoxEvent
        """
        self.RefreshPreview()
        event.Skip()

    def OnInlineChanged(self, event):
        """
        Called when SFC transition inline value changed
        @param event: wx.TextEvent
        """
        self.RefreshPreview()
        event.Skip()

    def OnPriorityChanged(self, event):
        """
        Called when block inputs number changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()

    def RefreshPreview(self):
        """
        Refresh preview panel of graphic element
        Override BlockPreviewDialog function
        """
        # Set graphic element displayed, creating a SFC transition
        self.Element = SFC_Transition(self.Preview)
        self.Element.SetType(*self.GetTransitionType())
        self.Element.SetPriority(self.Priority.GetValue())

        # Call BlockPreviewDialog function
        BlockPreviewDialog.RefreshPreview(self)
