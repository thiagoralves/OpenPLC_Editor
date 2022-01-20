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

from graphics.GraphicCommons import SELECTION_DIVERGENCE, \
    SELECTION_CONVERGENCE, SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE
from graphics.SFC_Objects import SFC_Divergence
from dialogs.BlockPreviewDialog import BlockPreviewDialog

# -------------------------------------------------------------------------------
#                         Create New Divergence Dialog
# -------------------------------------------------------------------------------


class SFCDivergenceDialog(BlockPreviewDialog):
    """
    Class that implements a dialog for defining parameters for creating a new
    divergence graphic element
    """

    def __init__(self, parent, controller, tagname, poss_div_types=None):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        @param poss_div_types: Types of divergence that will be available in the dialog window
        """
        BlockPreviewDialog.__init__(self, parent, controller, tagname,
                                    title=_('Create a new divergence or convergence'))

        # Init common sizers
        self._init_sizers(2, 0, 7, None, 2, 1)

        # Create label for divergence type
        type_label = wx.StaticText(self, label=_('Type:'))
        self.LeftGridSizer.AddWindow(type_label, flag=wx.GROW)

        # Create radio buttons for selecting divergence type
        divergence_buttons = [
            (SELECTION_DIVERGENCE, _('Selection Divergence')),
            (SELECTION_CONVERGENCE, _('Selection Convergence')),
            (SIMULTANEOUS_DIVERGENCE, _('Simultaneous Divergence')),
            (SIMULTANEOUS_CONVERGENCE, _('Simultaneous Convergence'))]
        poss_div_btns = []
        if poss_div_types is not None:
            for val in poss_div_types:
                poss_div_btns.append(divergence_buttons[val])
        else:
            poss_div_btns = divergence_buttons
        self.TypeRadioButtons = {}
        first = True
        focusbtn = None
        for type, label in poss_div_btns:
            radio_button = wx.RadioButton(self, label=label,
                                          style=(wx.RB_GROUP if first else 0))
            radio_button.SetValue(first)
            self.Bind(wx.EVT_RADIOBUTTON, self.OnTypeChanged, radio_button)
            self.LeftGridSizer.AddWindow(radio_button, flag=wx.GROW)
            self.TypeRadioButtons[type] = radio_button
            if first:
                focusbtn = type
            first = False

        # Create label for number of divergence sequences
        sequences_label = wx.StaticText(self,
                                        label=_('Number of sequences:'))
        self.LeftGridSizer.AddWindow(sequences_label, flag=wx.GROW)

        # Create spin control for defining number of divergence sequences
        self.Sequences = wx.SpinCtrl(self, min=2, max=20, initial=2)
        self.Bind(wx.EVT_SPINCTRL, self.OnSequencesChanged, self.Sequences)
        self.LeftGridSizer.AddWindow(self.Sequences, flag=wx.GROW)

        # Add preview panel and associated label to sizers
        self.RightGridSizer.AddWindow(self.PreviewLabel, flag=wx.GROW)
        self.RightGridSizer.AddWindow(self.Preview, flag=wx.GROW)

        # Add buttons sizer to sizers
        self.MainSizer.AddSizer(
            self.ButtonSizer, border=20,
            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.Fit()

        # Selection divergence radio button is default control having keyboard
        # focus
        self.TypeRadioButtons[focusbtn].SetFocus()

    def GetMinElementSize(self):
        """
        Get minimal graphic element size
        @return: Tuple containing minimal size (width, height) or None if no
        element defined
        """
        return self.Element.GetMinSize(True)

    def GetDivergenceType(self):
        """
        Return type selected for SFC divergence
        @return: Type selected (None if not found)
        """
        # Go through radio buttons and return type associated to the one that
        # is selected
        for type, control in self.TypeRadioButtons.iteritems():
            if control.GetValue():
                return type
        return None

    def GetValues(self):
        """
        Set default SFC divergence parameters
        @param values: Divergence parameters values
        """
        return {"type": self.GetDivergenceType(),
                "number": self.Sequences.GetValue()}

    def OnTypeChanged(self, event):
        """
        Called when SFC divergence type changed
        @param event: wx.RadioButtonEvent
        """
        self.RefreshPreview()
        event.Skip()

    def OnSequencesChanged(self, event):
        """
        Called when SFC divergence number of sequences changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()

    def RefreshPreview(self):
        """
        Refresh preview panel of graphic element
        Override BlockPreviewDialog function
        """
        # Set graphic element displayed, creating a SFC divergence
        self.Element = SFC_Divergence(self.Preview,
                                      self.GetDivergenceType(),
                                      self.Sequences.GetValue())

        # Call BlockPreviewDialog function
        BlockPreviewDialog.RefreshPreview(self)
