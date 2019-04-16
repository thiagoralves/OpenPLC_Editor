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

from graphics.GraphicCommons import INPUT, INOUT, OUTPUT
from graphics.FBD_Objects import FBD_Variable
from dialogs.BlockPreviewDialog import BlockPreviewDialog

# -------------------------------------------------------------------------------
#                                    Helpers
# -------------------------------------------------------------------------------


# -------------------------------------------------------------------------------
#                        Set Variable Parameters Dialog
# -------------------------------------------------------------------------------


class FBDVariableDialog(BlockPreviewDialog):
    """
    Class that implements a dialog for defining parameters of a FBD variable graphic
    element
    """

    def __init__(self, parent, controller, tagname, exclude_input=False):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        @param exclude_input: Exclude input from variable class selection
        """
        BlockPreviewDialog.__init__(self, parent, controller, tagname,
                                    title=_('Variable Properties'))

        # Dictionaries containing correspondence between variable block class and string
        # to be shown in Class combo box in both sense
        self.VARIABLE_CLASSES_DICT = {
            INPUT:  _("Input"),
            INOUT:  _("InOut"),
            OUTPUT: _("Output")
        }

        self.VARIABLE_CLASSES_DICT_REVERSE = dict(
            [(value, key) for key, value in self.VARIABLE_CLASSES_DICT.iteritems()])

        # Init common sizers
        self._init_sizers(4, 2, 4, None, 3, 2)

        # Create label for variable class
        class_label = wx.StaticText(self, label=_('Class:'))
        self.LeftGridSizer.AddWindow(class_label, flag=wx.GROW)

        # Create a combo box for defining variable class
        self.Class = wx.ComboBox(self, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnClassChanged, self.Class)
        self.LeftGridSizer.AddWindow(self.Class, flag=wx.GROW)

        # Create label for variable execution order
        execution_order_label = wx.StaticText(self,
                                              label=_('Execution Order:'))
        self.LeftGridSizer.AddWindow(execution_order_label, flag=wx.GROW)

        # Create spin control for defining variable execution order
        self.ExecutionOrder = wx.SpinCtrl(self, min=0, style=wx.SP_ARROW_KEYS)
        self.Bind(wx.EVT_SPINCTRL, self.OnExecutionOrderChanged,
                  self.ExecutionOrder)
        self.LeftGridSizer.AddWindow(self.ExecutionOrder, flag=wx.GROW)

        # Create label for variable expression
        name_label = wx.StaticText(self, label=_('Expression:'))
        self.RightGridSizer.AddWindow(name_label, border=5,
                                      flag=wx.GROW | wx.BOTTOM)

        # Create text control for defining variable expression
        self.Expression = wx.TextCtrl(self)
        self.Bind(wx.EVT_TEXT, self.OnExpressionChanged, self.Expression)
        self.RightGridSizer.AddWindow(self.Expression, flag=wx.GROW)

        # Create a list box to selected variable expression in the list of
        # variables defined in POU
        self.VariableName = wx.ListBox(self, size=wx.Size(-1, 120),
                                       style=wx.LB_SINGLE | wx.LB_SORT)
        self.Bind(wx.EVT_LISTBOX, self.OnNameChanged, self.VariableName)
        self.RightGridSizer.AddWindow(self.VariableName, border=4, flag=wx.GROW | wx.TOP)

        # Add preview panel and associated label to sizers
        self.MainSizer.AddWindow(self.PreviewLabel, border=20,
                                 flag=wx.GROW | wx.LEFT | wx.RIGHT)
        self.MainSizer.AddWindow(self.Preview, border=20,
                                 flag=wx.GROW | wx.LEFT | wx.RIGHT)

        # Add buttons sizer to sizers
        self.MainSizer.AddSizer(
            self.ButtonSizer, border=20,
            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        # Set options that can be selected in class combo box
        for var_class, choice in self.VARIABLE_CLASSES_DICT.iteritems():
            if not exclude_input or var_class != INPUT:
                self.Class.Append(choice)
        self.Class.SetSelection(0)

        # Extract list of variables defined in POU
        self.RefreshVariableList()

        # Refresh values in name list box
        self.RefreshNameList()

        self.Preview.SetInitialSize(wx.Size(-1, 60))
        self.Fit()

        # Class combo box is default control having keyboard focus
        self.Class.SetFocus()

    def RefreshNameList(self):
        """
        Called to refresh names in name list box
        """
        # Get variable class to select POU variable applicable
        var_class = self.VARIABLE_CLASSES_DICT_REVERSE[
            self.Class.GetStringSelection()]

        # Refresh names in name list box by selecting variables in POU variables
        # list that can be applied to variable class
        self.VariableName.Clear()
        for name, (var_type, _value_type) in self.VariableList.iteritems():
            if var_type != "Input" or var_class == INPUT:
                self.VariableName.Append(name)

        # Get variable expression and select corresponding value in name list
        # box if it exists
        selected = self.Expression.GetValue()
        if selected != "" and self.VariableName.FindString(selected) != wx.NOT_FOUND:
            self.VariableName.SetStringSelection(selected)
        else:
            self.VariableName.SetSelection(wx.NOT_FOUND)

        # Disable name list box if no name present inside
        self.VariableName.Enable(self.VariableName.GetCount() > 0)

    def SetValues(self, values):
        """
        Set default variable parameters
        @param values: Variable parameters values
        """

        # Get class parameter value
        var_class = values.get("class", None)
        if var_class is not None:
            # Set class selected in class combo box
            self.Class.SetStringSelection(self.VARIABLE_CLASSES_DICT[var_class])
            # Refresh names in name list box according to var class
            self.RefreshNameList()

        # For each parameters defined, set corresponding control value
        for name, value in values.items():

            # Parameter is variable expression
            if name == "expression":
                # Set expression text control value
                self.Expression.ChangeValue(value)
                # Select corresponding text in name list box if it exists
                if self.VariableName.FindString(value) != wx.NOT_FOUND:
                    self.VariableName.SetStringSelection(value)
                else:
                    self.VariableName.SetSelection(wx.NOT_FOUND)

            # Parameter is variable execution order
            elif name == "executionOrder":
                self.ExecutionOrder.SetValue(value)

        # Refresh preview panel
        self.RefreshPreview()
        self.Fit()

    def GetValues(self):
        """
        Return block parameters defined in dialog
        @return: {parameter_name: parameter_value,...}
        """
        expression = self.Expression.GetValue()
        values = {
            "class": self.VARIABLE_CLASSES_DICT_REVERSE[
                self.Class.GetStringSelection()],
            "expression": expression,
            "var_type": self.VariableList.get(expression, (None, None))[1],
            "executionOrder": self.ExecutionOrder.GetValue()}
        values["width"], values["height"] = self.Element.GetSize()
        return values

    def OnOK(self, event):
        """
        Called when dialog OK button is pressed
        Test if parameters defined are valid
        @param event: wx.Event from OK button
        """
        message = None

        # Test that an expression have been selected or typed by user
        value = self.Expression.GetValue()
        if value == "":
            message = _("At least a variable or an expression must be selected!")

        # Show error message if an error is detected
        if message is not None:
            self.ShowErrorMessage(message)

        else:
            # Call BlockPreviewDialog function
            BlockPreviewDialog.OnOK(self, event)

    def OnClassChanged(self, event):
        """
        Called when variable class value changed
        @param event: wx.ComboBoxEvent
        """
        # Refresh name list box values
        self.RefreshNameList()

        self.RefreshPreview()
        event.Skip()

    def OnNameChanged(self, event):
        """
        Called when name selected in name list box changed
        @param event: wx.ListBoxEvent
        """
        # Change expression test control value to the value selected in name
        # list box if value selected is valid
        if self.VariableName.GetSelection() != wx.NOT_FOUND:
            self.Expression.ChangeValue(self.VariableName.GetStringSelection())

        self.RefreshPreview()
        event.Skip()

    def OnExpressionChanged(self, event):
        """
        Called when expression text control is changed by user
        @param event: wx.ListBoxEvent
        """
        # Select the corresponding value in name list box if it exists
        self.VariableName.SetSelection(
            self.VariableName.FindString(self.Expression.GetValue()))

        self.RefreshPreview()
        event.Skip()

    def OnExecutionOrderChanged(self, event):
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
        # Get expression value to put in FBD variable element
        name = self.Expression.GetValue()

        # Set graphic element displayed, creating a FBD variable element
        self.Element = FBD_Variable(
            self.Preview,
            self.VARIABLE_CLASSES_DICT_REVERSE[self.Class.GetStringSelection()],
            name,
            self.VariableList.get(name, ("", ""))[1],
            executionOrder=self.ExecutionOrder.GetValue())

        # Call BlockPreviewDialog function
        BlockPreviewDialog.RefreshPreview(self)
