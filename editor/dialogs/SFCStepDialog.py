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

from graphics.SFC_Objects import SFC_Step
from dialogs.BlockPreviewDialog import BlockPreviewDialog

# -------------------------------------------------------------------------------
#                         Set SFC Step Parameters Dialog
# -------------------------------------------------------------------------------


class SFCStepDialog(BlockPreviewDialog):
    """
    Class that implements a dialog for defining parameters of a SFC step graphic
    element
    """

    def __init__(self, parent, controller, tagname, initial=False):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        @param initial: True if step is initial (default: False)
        """
        BlockPreviewDialog.__init__(self, parent, controller, tagname,
                                    title=_('Edit Step'))

        # Init common sizers
        self._init_sizers(2, 0, 6, None, 2, 1)

        # Create label for SFC step name
        name_label = wx.StaticText(self, label=_('Name:'))
        self.LeftGridSizer.AddWindow(name_label, flag=wx.GROW)

        # Create text control for defining SFC step name
        self.StepName = wx.TextCtrl(self)
        self.Bind(wx.EVT_TEXT, self.OnNameChanged, self.StepName)
        self.LeftGridSizer.AddWindow(self.StepName, flag=wx.GROW)

        # Create label for SFC step connectors
        connectors_label = wx.StaticText(self, label=_('Connectors:'))
        self.LeftGridSizer.AddWindow(connectors_label, flag=wx.GROW)

        # Create check boxes for defining connectors available on SFC step
        self.ConnectorsCheckBox = {}
        for name, label in [("input", _("Input")),
                            ("output", _("Output")),
                            ("action", _("Action"))]:
            check_box = wx.CheckBox(self, label=label)
            if name == "output" or (name == "input" and not initial):
                check_box.SetValue(True)
            self.Bind(wx.EVT_CHECKBOX, self.OnConnectorsChanged, check_box)
            self.LeftGridSizer.AddWindow(check_box, flag=wx.GROW)
            self.ConnectorsCheckBox[name] = check_box

        # Add preview panel and associated label to sizers
        self.RightGridSizer.AddWindow(self.PreviewLabel, flag=wx.GROW)
        self.RightGridSizer.AddWindow(self.Preview, flag=wx.GROW)

        # Add buttons sizer to sizers
        self.MainSizer.AddSizer(
            self.ButtonSizer, border=20,
            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        # Save flag that indicates that step is initial
        self.Initial = initial

        # Set default name for step
        self.StepName.ChangeValue(controller.GenerateNewName(
            tagname, None, "Step%d", 0))

        self.Fit()

        # Step name text control is default control having keyboard focus
        self.StepName.SetFocus()

    def SetValues(self, values):
        """
        Set default block parameters
        @param values: Block parameters values
        """
        # For each parameters defined, set corresponding control value
        for name, value in values.items():

            # Parameter is step name
            if name == "name":
                self.StepName.ChangeValue(value)

            # Set value of other controls
            else:
                control = self.ConnectorsCheckBox.get(name, None)
                if control is not None:
                    control.SetValue(value)

        # Refresh preview panel
        self.RefreshPreview()

    def GetValues(self):
        """
        Return step parameters defined in dialog
        @return: {parameter_name: parameter_value,...}
        """
        values = {"name": self.StepName.GetValue()}
        values.update({
            name: control.IsChecked()
            for name, control in self.ConnectorsCheckBox.iteritems()})
        values["width"], values["height"] = self.Element.GetSize()
        return values

    def OnOK(self, event):
        """
        Called when dialog OK button is pressed
        Test if step name defined is valid
        @param event: wx.Event from OK button
        """
        message = None

        # Get step name typed by user
        step_name = self.StepName.GetValue()

        # Test that a name have been defined
        if step_name == "":
            message = _("Form isn't complete. Name must be filled!")

        # If an error have been identify, show error message dialog
        if message is not None:
            self.ShowErrorMessage(message)

        # Test step name validity
        elif self.TestElementName(step_name):
            # Call BlockPreviewDialog function
            BlockPreviewDialog.OnOK(self, event)

    def OnConnectorsChanged(self, event):
        """
        Called when a step connector value changed
        @param event: wx.CheckBoxEvent
        """
        self.RefreshPreview()
        event.Skip()

    def OnNameChanged(self, event):
        """
        Called when step name value changed
        @param event: wx.TextEvent
        """
        self.RefreshPreview()
        event.Skip()

    def RefreshPreview(self):
        """
        Refresh preview panel of graphic element
        Override BlockPreviewDialog function
        """
        # Set graphic element displayed, creating a SFC step element
        self.Element = SFC_Step(self.Preview,
                                self.StepName.GetValue(),
                                self.Initial)

        # Update connectors of SFC step element according to check boxes value
        for name, control in self.ConnectorsCheckBox.iteritems():
            if control.IsChecked():
                getattr(self.Element, "Add" + name.capitalize())()
            else:
                getattr(self.Element, "Remove" + name.capitalize())()

        # Call BlockPreviewDialog function
        BlockPreviewDialog.RefreshPreview(self)
