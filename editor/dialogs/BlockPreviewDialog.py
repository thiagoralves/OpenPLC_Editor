#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2013: Edouard TISSERANT and Laurent BESSARD
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
from __future__ import division
import wx

from plcopen.structures import TestIdentifier, IEC_KEYWORDS
from graphics.GraphicCommons import FREEDRAWING_MODE

# -------------------------------------------------------------------------------
#                    Dialog with preview for graphic block
# -------------------------------------------------------------------------------


class BlockPreviewDialog(wx.Dialog):
    """
    Class that implements a generic dialog containing a preview panel for displaying
    graphic created by dialog
    """

    def __init__(self, parent, controller, tagname, title):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        @param title: Title of dialog frame
        """
        wx.Dialog.__init__(self, parent, title=title)

        # Save reference to
        self.Controller = controller
        self.TagName = tagname

        # Label for preview
        self.PreviewLabel = wx.StaticText(self, label=_('Preview:'))

        # Create Preview panel
        self.Preview = wx.Panel(self, style=wx.SIMPLE_BORDER)
        self.Preview.SetBackgroundColour(wx.WHITE)

        # Add function to preview panel so that it answers to graphic elements
        # like Viewer
        setattr(self.Preview, "GetDrawingMode", lambda: FREEDRAWING_MODE)
        setattr(self.Preview, "GetScaling", lambda: None)
        setattr(self.Preview, "GetBlockType", controller.GetBlockType)
        setattr(self.Preview, "IsOfType", controller.IsOfType)

        # Bind paint event on Preview panel
        self.Preview.Bind(wx.EVT_PAINT, self.OnPaint)

        # Add default dialog buttons sizer
        self.ButtonSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL | wx.CENTRE)
        self.Bind(wx.EVT_BUTTON, self.OnOK,
                  self.ButtonSizer.GetAffirmativeButton())

        self.Element = None            # Graphic element to display in preview
        self.MinElementSize = None     # Graphic element minimal size

        # Variable containing the graphic element name when dialog is opened
        self.DefaultElementName = None
        self.Fit()

        # List of variables defined in POU {var_name: (var_class, var_type),...}
        self.VariableList = {}

    def __del__(self):
        """
        Destructor
        """
        # Remove reference to project controller
        self.Controller = None

    def _init_sizers(self,
                     main_rows, main_growable_row,
                     left_rows, left_growable_row,
                     right_rows, right_growable_row):
        """
        Initialize common sizers
        @param main_rows: Number of rows in main sizer
        @param main_growable_row: Row that is growable in main sizer, None if no
        row is growable
        @param left_rows: Number of rows in left grid sizer
        @param left_growable_row: Row that is growable in left grid sizer, None
        if no row is growable
        @param right_rows: Number of rows in right grid sizer
        @param right_growable_row: Row that is growable in right grid sizer,
        None if no row is growable
        """
        # Create dialog main sizer
        self.MainSizer = wx.FlexGridSizer(cols=1, hgap=0,
                                          rows=main_rows, vgap=10)
        self.MainSizer.AddGrowableCol(0)
        if main_growable_row is not None:
            self.MainSizer.AddGrowableRow(main_growable_row)

        # Create a sizer for dividing parameters in two columns
        self.ColumnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.MainSizer.AddSizer(self.ColumnSizer, border=20,
                                flag=wx.GROW | wx.TOP | wx.LEFT | wx.RIGHT)

        # Create a sizer for left column
        self.LeftGridSizer = wx.FlexGridSizer(cols=1, hgap=0,
                                              rows=left_rows, vgap=5)
        self.LeftGridSizer.AddGrowableCol(0)
        if left_growable_row is not None:
            self.LeftGridSizer.AddGrowableRow(left_growable_row)
        self.ColumnSizer.AddSizer(self.LeftGridSizer, 1, border=5,
                                  flag=wx.GROW | wx.RIGHT | wx.EXPAND)

        # Create a sizer for right column
        self.RightGridSizer = wx.FlexGridSizer(cols=1, hgap=0,
                                               rows=right_rows, vgap=0)
        self.RightGridSizer.AddGrowableCol(0)
        if right_growable_row is not None:
            self.RightGridSizer.AddGrowableRow(right_growable_row)
        self.ColumnSizer.AddSizer(self.RightGridSizer, 1, border=5,
                                  flag=wx.GROW | wx.LEFT)

        self.SetSizer(self.MainSizer)

    def SetMinElementSize(self, size):
        """
        Define minimal graphic element size
        @param size: Tuple containing minimal size (width, height)
        """
        self.MinElementSize = size

    def GetMinElementSize(self):
        """
        Get minimal graphic element size
        @return: Tuple containing minimal size (width, height) or None if no
        element defined
        May be overridden by inherited classes
        """
        if self.Element is None:
            return None

        return self.Element.GetMinSize()

    def SetPreviewFont(self, font):
        """
        Set font of Preview panel
        @param font: wx.Font object containing font style
        """
        self.Preview.SetFont(font)

    def RefreshVariableList(self):
        """
        Extract list of variables defined in POU
        """
        # Get list of variables defined in POU
        self.VariableList = {
            var.Name: (var.Class, var.Type)
            for var in self.Controller.GetEditedElementInterfaceVars(self.TagName)
            if var.Edit}

        # Add POU name to variable list if POU is a function
        returntype = self.Controller.GetEditedElementInterfaceReturnType(self.TagName)
        if returntype is not None:
            self.VariableList[
                self.Controller.GetEditedElementName(self.TagName)] = \
                 ("Output", returntype)

        # Add POU name if POU is a transition
        words = self.TagName.split("::")
        if words[0] == "T":
            self.VariableList[words[2]] = ("Output", "BOOL")

    def TestElementName(self, element_name):
        """
        Test displayed graphic element name
        @param element_name: Graphic element name
        """
        # Variable containing error message format
        message_format = None
        # Get graphic element name in upper case
        uppercase_element_name = element_name.upper()

        # Test if graphic element name is a valid identifier
        if not TestIdentifier(element_name):
            message_format = _("\"%s\" is not a valid identifier!")

        # Test that graphic element name isn't a keyword
        elif uppercase_element_name in IEC_KEYWORDS:
            message_format = _("\"%s\" is a keyword. It can't be used!")

        # Test that graphic element name isn't a POU name
        elif uppercase_element_name in self.Controller.GetProjectPouNames():
            message_format = _("\"%s\" pou already exists!")

        # Test that graphic element name isn't already used in POU by a variable
        # or another graphic element
        elif ((self.DefaultElementName is None or
               self.DefaultElementName.upper() != uppercase_element_name) and
              uppercase_element_name in self.Controller.GetEditedElementVariables(self.TagName)):
            message_format = _("\"%s\" element for this pou already exists!")

        # If an error have been identify, show error message dialog
        if message_format is not None:
            self.ShowErrorMessage(message_format % element_name)
            # Test failed
            return False

        # Test succeed
        return True

    def ShowErrorMessage(self, message):
        """
        Show an error message dialog over this dialog
        @param message: Error message to display
        """
        dialog = wx.MessageDialog(self, message,
                                  _("Error"),
                                  wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def OnOK(self, event):
        """
        Called when dialog OK button is pressed
        Need to be overridden by inherited classes to check that dialog values
        are valid
        @param event: wx.Event from OK button
        """
        # Close dialog
        self.EndModal(wx.ID_OK)

    def RefreshPreview(self):
        """Triggers EVT_PAINT event to refresh UI"""
        #self.Refresh()
        self.DrawPreview()

    def DrawPreview(self):
        """
        Refresh preview panel of graphic element
        May be overridden by inherited classes
        """
        # Init preview panel paint device context
        dc = wx.ClientDC(self.Preview)
        dc.SetFont(self.Preview.GetFont())
        dc.Clear()

        # Return immediately if no graphic element defined
        if self.Element is None:
            return

        # Calculate block size according to graphic element min size due to its
        # parameters and graphic element min size defined
        min_width, min_height = self.GetMinElementSize()
        width = max(self.MinElementSize[0], min_width)
        height = max(self.MinElementSize[1], min_height)
        self.Element.SetSize(width, height)

        # Get element position and bounding box to center in preview
        posx, posy = self.Element.GetPosition()
        bbox = self.Element.GetBoundingBox()

        # Get Preview panel size
        client_size = self.Preview.GetClientSize()

        # If graphic element is too big to be displayed in preview panel,
        # calculate preview panel scale so that graphic element fit inside
        k = 1.1 if (bbox.width * 1.1 > client_size.width or
                    bbox.height * 1.1 > client_size.height) \
            else 1.0
        scale = (max(bbox.width / client_size.width,
                     bbox.height / client_size.height) * k)
        dc.SetUserScale(1.0 / scale, 1.0 / scale)

        # Center graphic element in preview panel
        x = int(client_size.width * scale - bbox.width) // 2 + posx - bbox.x
        y = int(client_size.height * scale - bbox.height) // 2 + posy - bbox.y
        self.Element.SetPosition(x, y)

        # Draw graphic element
        self.Element.Draw(dc)

    def OnPaint(self, event):
        """
        Called when Preview panel need to be redraw
        @param event: wx.PaintEvent
        """
        self.DrawPreview()
        event.Skip()
