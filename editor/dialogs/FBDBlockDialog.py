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
import re

import wx

from graphics.FBD_Objects import FBD_Block
from controls.LibraryPanel import LibraryPanel
from dialogs.BlockPreviewDialog import BlockPreviewDialog

# -------------------------------------------------------------------------------
#                                    Helpers
# -------------------------------------------------------------------------------


def GetBlockTypeDefaultNameModel(blocktype):
    return re.compile("%s[0-9]+" % blocktype if blocktype is not None else ".*")

# -------------------------------------------------------------------------------
#                         Set Block Parameters Dialog
# -------------------------------------------------------------------------------


class FBDBlockDialog(BlockPreviewDialog):
    """
    Class that implements a dialog for defining parameters of a FBD block graphic
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
                                    title=_('Block Properties'))

        # Init common sizers
        self._init_sizers(2, 0, 1, 0, 3, 2)

        # Create static box around library panel
        type_staticbox = wx.StaticBox(self, label=_('Type:'))
        left_staticboxsizer = wx.StaticBoxSizer(type_staticbox, wx.VERTICAL)
        self.LeftGridSizer.AddSizer(left_staticboxsizer, border=5, flag=wx.GROW)

        # Create Library panel and add it to static box
        self.LibraryPanel = LibraryPanel(self)
        self.LibraryPanel.SetInitialSize(wx.Size(-1, 400))

        # Set function to call when selection in Library panel changed
        setattr(self.LibraryPanel, "_OnTreeItemSelected",
                self.OnLibraryTreeItemSelected)
        left_staticboxsizer.AddWindow(self.LibraryPanel, 1, border=5,
                                      flag=wx.GROW | wx.TOP)

        # Create sizer for other block parameters
        top_right_gridsizer = wx.FlexGridSizer(cols=2, hgap=0, rows=4, vgap=5)
        top_right_gridsizer.AddGrowableCol(1)
        self.RightGridSizer.AddSizer(top_right_gridsizer, flag=wx.GROW)

        # Create label for block name
        name_label = wx.StaticText(self, label=_('Name:'))
        top_right_gridsizer.AddWindow(name_label,
                                      flag=wx.ALIGN_CENTER_VERTICAL)

        # Create text control for defining block name
        self.BlockName = wx.TextCtrl(self)
        self.Bind(wx.EVT_TEXT, self.OnNameChanged, self.BlockName)
        top_right_gridsizer.AddWindow(self.BlockName, flag=wx.GROW)

        # Create label for extended block input number
        inputs_label = wx.StaticText(self, label=_('Inputs:'))
        top_right_gridsizer.AddWindow(inputs_label,
                                      flag=wx.ALIGN_CENTER_VERTICAL)

        # Create spin control for defining extended block input number
        self.Inputs = wx.SpinCtrl(self, min=2, max=20,
                                  style=wx.SP_ARROW_KEYS)
        self.Bind(wx.EVT_SPINCTRL, self.OnInputsChanged, self.Inputs)
        top_right_gridsizer.AddWindow(self.Inputs, flag=wx.GROW)

        # Create label for block execution order
        execution_order_label = wx.StaticText(self,
                                              label=_('Execution Order:'))
        top_right_gridsizer.AddWindow(execution_order_label,
                                      flag=wx.ALIGN_CENTER_VERTICAL)

        # Create spin control for defining block execution order
        self.ExecutionOrder = wx.SpinCtrl(self, min=0, style=wx.SP_ARROW_KEYS)
        self.Bind(wx.EVT_SPINCTRL, self.OnExecutionOrderChanged,
                  self.ExecutionOrder)
        top_right_gridsizer.AddWindow(self.ExecutionOrder, flag=wx.GROW)

        # Create label for block execution control
        execution_control_label = wx.StaticText(self,
                                                label=_('Execution Control:'))
        top_right_gridsizer.AddWindow(execution_control_label,
                                      flag=wx.ALIGN_CENTER_VERTICAL)

        # Create check box to enable block execution control
        self.ExecutionControl = wx.CheckBox(self)
        self.Bind(wx.EVT_CHECKBOX, self.OnExecutionOrderChanged,
                  self.ExecutionControl)
        top_right_gridsizer.AddWindow(self.ExecutionControl, flag=wx.GROW)

        # Add preview panel and associated label to sizers
        self.RightGridSizer.AddWindow(self.PreviewLabel, flag=wx.GROW)
        self.RightGridSizer.AddWindow(self.Preview, flag=wx.GROW)

        # Add buttons sizer to sizers
        self.MainSizer.AddSizer(self.ButtonSizer, border=20,
                                flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        # Dictionary containing correspondence between parameter exchanged and
        # control to fill with parameter value
        self.ParamsControl = {
            "extension": self.Inputs,
            "executionOrder": self.ExecutionOrder,
            "executionControl": self.ExecutionControl
        }

        # Init controls value and sensibility
        self.BlockName.SetValue("")
        self.BlockName.Enable(False)
        self.Inputs.Enable(False)

        # Variable containing last name typed
        self.CurrentBlockName = None

        # Refresh Library panel values
        self.LibraryPanel.SetBlockList(controller.GetBlockTypes(tagname))
        self.Fit()
        self.LibraryPanel.SetFocus()

    def SetValues(self, values):
        """
        Set default block parameters
        @param values: Block parameters values
        """
        # Extract block type defined in parameters
        blocktype = values.get("type", None)

        # Select block type in library panel
        if blocktype is not None:
            self.LibraryPanel.SelectTreeItem(blocktype,
                                             values.get("inputs", None))

        # Define regular expression for determine if block name is block
        # default name
        default_name_model = GetBlockTypeDefaultNameModel(blocktype)

        # For each parameters defined, set corresponding control value
        for name, value in values.items():

            # Parameter is block name
            if name == "name":
                if value != "":
                    # Set default graphic element name for testing
                    self.DefaultElementName = value

                    # Test if block name is type default block name and save
                    # block name if not (name have been typed by user)
                    if default_name_model.match(value) is None:
                        self.CurrentBlockName = value

                self.BlockName.ChangeValue(value)

            # Set value of other controls
            else:
                control = self.ParamsControl.get(name, None)
                if control is not None:
                    control.SetValue(value)

        # Refresh preview panel
        self.RefreshPreview()

    def GetValues(self):
        """
        Return block parameters defined in dialog
        @return: {parameter_name: parameter_value,...}
        """
        values = self.LibraryPanel.GetSelectedBlock()
        if self.BlockName.IsEnabled() and self.BlockName.GetValue() != "":
            values["name"] = self.BlockName.GetValue()
        values["width"], values["height"] = self.Element.GetSize()
        values.update({
            name: control.GetValue()
            for name, control in self.ParamsControl.iteritems()})
        return values

    def OnOK(self, event):
        """
        Called when dialog OK button is pressed
        Test if parameters defined are valid
        @param event: wx.Event from OK button
        """
        message = None

        # Get block type selected
        selected = self.LibraryPanel.GetSelectedBlock()

        # Get block type name and if block is a function block
        block_name = self.BlockName.GetValue()
        name_enabled = self.BlockName.IsEnabled()

        # Test that a type has been selected for block
        if selected is None:
            message = _("Form isn't complete. Valid block type must be selected!")

        # Test, if block is a function block, that a name have been defined
        elif name_enabled and block_name == "":
            message = _("Form isn't complete. Name must be filled!")

        # Show error message if an error is detected
        if message is not None:
            self.ShowErrorMessage(message)

        # Test block name validity if necessary
        elif not name_enabled or self.TestElementName(block_name):
            # Call BlockPreviewDialog function
            BlockPreviewDialog.OnOK(self, event)

    def OnLibraryTreeItemSelected(self, event):
        """
        Called when block type selected in library panel
        @param event: wx.TreeEvent
        """
        # Get type selected in library panel
        values = self.LibraryPanel.GetSelectedBlock()

        # Get block type informations
        blocktype = (self.Controller.GetBlockType(values["type"],
                                                  values["inputs"])
                     if values is not None else None)

        # Set input number spin control according to block type informations
        if blocktype is not None:
            self.Inputs.SetValue(len(blocktype["inputs"]))
            self.Inputs.Enable(blocktype["extensible"])
        else:
            self.Inputs.SetValue(2)
            self.Inputs.Enable(False)

        # Update block name with default value if block type is a function and
        # current block name wasn't typed by user
        if blocktype is not None and blocktype["type"] != "function":
            self.BlockName.Enable(True)

            if self.CurrentBlockName is None:
                # Generate new block name according to block type, taking
                # default element name if it was already a default name for this
                # block type
                default_name_model = GetBlockTypeDefaultNameModel(values["type"])
                block_name = (
                    self.DefaultElementName
                    if (self.DefaultElementName is not None and
                        default_name_model.match(self.DefaultElementName))
                    else self.Controller.GenerateNewName(
                        self.TagName, None, values["type"]+"%d", 0))
            else:
                block_name = self.CurrentBlockName

            self.BlockName.ChangeValue(block_name)
        else:
            self.BlockName.Enable(False)
            self.BlockName.ChangeValue("")

        # Refresh preview panel
        self.RefreshPreview()

    def OnNameChanged(self, event):
        """
        Called when block name value changed
        @param event: wx.TextEvent
        """
        if self.BlockName.IsEnabled():
            # Save block name typed by user
            self.CurrentBlockName = self.BlockName.GetValue()
            self.RefreshPreview()
        event.Skip()

    def OnInputsChanged(self, event):
        """
        Called when block inputs number changed
        @param event: wx.SpinEvent
        """
        if self.Inputs.IsEnabled():
            self.RefreshPreview()
        event.Skip()

    def OnExecutionOrderChanged(self, event):
        """
        Called when block execution order value changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()

    def OnExecutionControlChanged(self, event):
        """
        Called when block execution control value changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()

    def RefreshPreview(self):
        """
        Refresh preview panel of graphic element
        Override BlockPreviewDialog function
        """
        # Get type selected in library panel
        values = self.LibraryPanel.GetSelectedBlock()

        # If a block type is selected in library panel
        if values is not None:
            # Set graphic element displayed, creating a FBD block element
            self.Element = FBD_Block(
                self.Preview, values["type"],
                (self.BlockName.GetValue() if self.BlockName.IsEnabled() else ""),
                extension=self.Inputs.GetValue(),
                inputs=values["inputs"],
                executionControl=self.ExecutionControl.GetValue(),
                executionOrder=self.ExecutionOrder.GetValue())

        # Reset graphic element displayed
        else:
            self.Element = None

        # Call BlockPreviewDialog function
        BlockPreviewDialog.RefreshPreview(self)
