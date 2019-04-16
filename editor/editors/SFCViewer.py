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
from __future__ import division

import wx

from editors.Viewer import *
from graphics.SFC_Objects import *
from graphics.GraphicCommons import SELECTION_DIVERGENCE, \
    SELECTION_CONVERGENCE, SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE, EAST, NORTH, WEST, SOUTH

SFC_Objects = (SFC_Step, SFC_ActionBlock, SFC_Transition, SFC_Divergence, SFC_Jump)


class SFC_Viewer(Viewer):

    SFC_StandardRules = {
        # The key of this dict is a block that user try to connect,
        # and the value is a list of blocks, that can be connected with the current block
        # and with directions of connection
        "SFC_Step": [("SFC_ActionBlock", EAST),
                     ("SFC_Transition", SOUTH),
                     (SELECTION_DIVERGENCE, SOUTH),
                     (SIMULTANEOUS_CONVERGENCE, SOUTH)],

        "SFC_ActionBlock": [("SFC_Step", EAST)],

        "SFC_Transition": [("SFC_Step", SOUTH),
                           (SELECTION_CONVERGENCE, SOUTH),
                           (SIMULTANEOUS_DIVERGENCE, SOUTH),
                           ("SFC_Jump", SOUTH),
                           ("FBD_Block", EAST),
                           ("FBD_Variable", EAST),
                           ("FBD_Connector", EAST),
                           ("LD_Contact", EAST),
                           ("LD_PowerRail", EAST),
                           ("LD_Coil", EAST)],

        SELECTION_DIVERGENCE: [("SFC_Transition", SOUTH)],

        SELECTION_CONVERGENCE: [("SFC_Step", SOUTH),
                                ("SFC_Jump", SOUTH)],

        SIMULTANEOUS_DIVERGENCE: [("SFC_Step", SOUTH)],

        SIMULTANEOUS_CONVERGENCE: [("SFC_Transition", SOUTH)],

        "SFC_Jump": [],

        "FBD_Block": [("SFC_Transition", WEST)],

        "FBD_Variable": [("SFC_Transition", WEST)],

        "FBD_Connector": [("SFC_Transition", WEST)],

        "LD_Contact": [("SFC_Transition", WEST)],

        "LD_PowerRail": [("SFC_Transition", WEST)],

        "LD_Coil": [("SFC_Transition", WEST)]
    }

    def __init__(self, parent, tagname, window, controler, debug=False, instancepath=""):
        Viewer.__init__(self, parent, tagname, window, controler, debug, instancepath)
        self.CurrentLanguage = "SFC"

    def ConnectConnectors(self, start, end):
        startpoint = [start.GetPosition(False), start.GetDirection()]
        endpoint = [end.GetPosition(False), end.GetDirection()]
        wire = Wire(self, startpoint, endpoint)
        self.AddWire(wire)
        start.Connect((wire, 0), False)
        end.Connect((wire, -1), False)
        wire.ConnectStartPoint(None, start)
        wire.ConnectEndPoint(None, end)
        return wire

    def CreateTransition(self, connector, next=None):
        previous = connector.GetParentBlock()
        id = self.GetNewId()
        transition = SFC_Transition(self, "reference", "", 0, id)
        pos = connector.GetPosition(False)
        transition.SetPosition(pos.x, pos.y + SFC_WIRE_MIN_SIZE)
        transition_connectors = transition.GetConnectors()
        wire = self.ConnectConnectors(transition_connectors["input"], connector)
        if isinstance(previous, SFC_Divergence):
            previous.RefreshConnectedPosition(connector)
        else:
            previous.RefreshOutputPosition()
        wire.SetPoints([wx.Point(pos.x, pos.y + GetWireSize(previous)), wx.Point(pos.x, pos.y)])
        self.AddBlock(transition)
        self.Controler.AddEditedElementTransition(self.TagName, id)
        self.RefreshTransitionModel(transition)
        if next:
            wire = self.ConnectConnectors(next, transition_connectors["output"])
            pos = transition_connectors["output"].GetPosition(False)
            next_block = next.GetParentBlock()
            next_pos = next.GetPosition(False)
            transition.RefreshOutputPosition((0, pos.y + SFC_WIRE_MIN_SIZE - next_pos.y))
            wire.SetPoints([wx.Point(pos.x, pos.y + SFC_WIRE_MIN_SIZE), wx.Point(pos.x, pos.y)])
            if isinstance(next_block, SFC_Divergence):
                next_block.RefreshPosition()
            transition.RefreshOutputModel(True)
        return transition

    def RemoveTransition(self, transition):
        connectors = transition.GetConnectors()
        input_wires = connectors["input"].GetWires()
        if len(input_wires) != 1:
            return
        input_wire = input_wires[0][0]
        previous = input_wire.EndConnected
        input_wire.Clean()
        self.RemoveWire(input_wire)
        output_wires = connectors["output"].GetWires()
        if len(output_wires) != 1:
            return
        output_wire = output_wires[0][0]
        next = output_wire.StartConnected
        output_wire.Clean()
        self.RemoveWire(output_wire)
        transition.Clean()
        self.RemoveBlock(transition)
        self.Controler.RemoveEditedElementInstance(self.TagName, transition.GetId())
        wire = self.ConnectConnectors(next, previous)
        return wire

    def CreateStep(self, name, connector, next=None):
        previous = connector.GetParentBlock()
        id = self.GetNewId()
        step = SFC_Step(self, name, False, id)
        if next:
            step.AddOutput()
        min_width, min_height = step.GetMinSize()
        pos = connector.GetPosition(False)
        step.SetPosition(pos.x, pos.y + SFC_WIRE_MIN_SIZE)
        step.SetSize(min_width, min_height)
        step_connectors = step.GetConnectors()
        wire = self.ConnectConnectors(step_connectors["input"], connector)
        if isinstance(previous, SFC_Divergence):
            previous.RefreshConnectedPosition(connector)
        else:
            previous.RefreshOutputPosition()
        wire.SetPoints([wx.Point(pos.x, pos.y + GetWireSize(previous)), wx.Point(pos.x, pos.y)])
        self.AddBlock(step)
        self.Controler.AddEditedElementStep(self.TagName, id)
        self.RefreshStepModel(step)
        if next:
            wire = self.ConnectConnectors(next, step_connectors["output"])
            pos = step_connectors["output"].GetPosition(False)
            next_block = next.GetParentBlock()
            next_pos = next.GetPosition(False)
            step.RefreshOutputPosition((0, pos.y + SFC_WIRE_MIN_SIZE - next_pos.y))
            wire.SetPoints([wx.Point(pos.x, pos.y + SFC_WIRE_MIN_SIZE), wx.Point(pos.x, pos.y)])
            if isinstance(next_block, SFC_Divergence):
                next_block.RefreshPosition()
            step.RefreshOutputModel(True)
        return step

    def RemoveStep(self, step):
        connectors = step.GetConnectors()
        if connectors["input"]:
            input_wires = connectors["input"].GetWires()
            if len(input_wires) != 1:
                return
            input_wire = input_wires[0][0]
            previous = input_wire.EndConnected
            input_wire.Clean()
            self.RemoveWire(input_wire)
        else:
            previous = None
        if connectors["output"]:
            output_wires = connectors["output"].GetWires()
            if len(output_wires) != 1:
                return
            output_wire = output_wires[0][0]
            next = output_wire.StartConnected
            output_wire.Clean()
            self.RemoveWire(output_wire)
        else:
            next = None
        action = step.GetActionConnected()
        if action:
            self.DeleteActionBlock(action.GetParentBlock())
        step.Clean()
        self.RemoveBlock(step)
        self.Controler.RemoveEditedElementInstance(self.TagName, step.GetId())
        if next and previous:
            wire = self.ConnectConnectors(next, previous)
            return wire
        else:
            return None

    # -------------------------------------------------------------------------------
    #                          Mouse event functions
    # -------------------------------------------------------------------------------

    def OnViewerLeftDown(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnViewerLeftDown(self, event)
        elif self.Mode == MODE_SELECTION:
            if event.ShiftDown() and not event.ControlDown() and self.SelectedElement is not None:
                element = self.FindElement(event, True)
                if element and not self.IsWire(element):
                    if isinstance(self.SelectedElement, Graphic_Group):
                        self.SelectedElement.SelectElement(element)
                    else:
                        group = Graphic_Group(self)
                        self.SelectedElement.SetSelected(False)
                        group.SelectElement(self.SelectedElement)
                        group.SelectElement(element)
                        self.SelectedElement = group
                    elements = self.SelectedElement.GetElements()
                    if len(elements) == 0:
                        self.SelectedElement = element
                    elif len(elements) == 1:
                        self.SelectedElement = elements[0]
                    self.SelectedElement.SetSelected(True)
            else:
                element = self.FindElement(event)
                if self.SelectedElement and self.SelectedElement != element:
                    if self.IsWire(self.SelectedElement):
                        self.SelectedElement.SetSelectedSegment(None)
                    else:
                        self.SelectedElement.SetSelected(False)
                    self.SelectedElement = None
                if element:
                    self.SelectedElement = element
                    self.SelectedElement.OnLeftDown(event, self.GetLogicalDC(), self.Scaling)
                    self.SelectedElement.Refresh()
                else:
                    self.rubberBand.Reset()
                    self.rubberBand.OnLeftDown(event, self.GetLogicalDC(), self.Scaling)
        elif self.Mode == MODE_COMMENT:
            self.rubberBand.Reset()
            self.rubberBand.OnLeftDown(event, self.GetLogicalDC(), self.Scaling)
        event.Skip()

    def OnViewerLeftUp(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnViewerLeftUp(self, event)
        elif self.rubberBand.IsShown():
            if self.Mode == MODE_SELECTION:
                elements = self.SearchElements(self.rubberBand.GetCurrentExtent())
                self.rubberBand.OnLeftUp(event, self.GetLogicalDC(), self.Scaling)
                if len(elements) > 0:
                    self.SelectedElement = Graphic_Group(self)
                    self.SelectedElement.SetElements(elements)
                    self.SelectedElement.SetSelected(True)
            elif self.Mode == MODE_COMMENT:
                bbox = self.rubberBand.GetCurrentExtent()
                self.rubberBand.OnLeftUp(event, self.GetLogicalDC(), self.Scaling)
                wx.CallAfter(self.AddComment, bbox)
        elif self.Mode == MODE_INITIALSTEP:
            wx.CallAfter(self.AddInitialStep, GetScaledEventPosition(event, self.GetLogicalDC(), self.Scaling))
        elif self.Mode == MODE_SELECTION and self.SelectedElement:
            if self.IsWire(self.SelectedElement):
                self.SelectedElement.SetSelectedSegment(0)
            else:
                self.SelectedElement.OnLeftUp(event, self.GetLogicalDC(), self.Scaling)
                self.SelectedElement.Refresh()
            wx.CallAfter(self.SetCurrentCursor, 0)
        #
        # FIXME:
        # This code was forgotten by commit
        # 9c74d00ce93e from plcopeneditor_history repository
        # 'Last bugs on block and wire moving, resizing with cursor fixed'
        #
        # elif self.Mode == MODE_WIRE and self.SelectedElement:
        #     self.SelectedElement.ResetPoints()
        #     self.SelectedElement.OnMotion(event, self.GetLogicalDC(), self.Scaling)
        #     self.SelectedElement.GeneratePoints()
        #     self.SelectedElement.RefreshModel()
        #     self.SelectedElement.SetSelected(True)
        event.Skip()

    def OnViewerRightUp(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnViewerRightUp(self, event)
        else:
            element = self.FindElement(event)
            if element:
                if self.SelectedElement and self.SelectedElement != element:
                    self.SelectedElement.SetSelected(False)
                self.SelectedElement = element
                if self.IsWire(self.SelectedElement):
                    self.SelectedElement.SetSelectedSegment(0)
                else:
                    self.SelectedElement.SetSelected(True)
                    self.SelectedElement.OnRightUp(event, self.GetLogicalDC(), self.Scaling)
                    self.SelectedElement.Refresh()
                wx.CallAfter(self.SetCurrentCursor, 0)
        event.Skip()

    def OnViewerLeftDClick(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnViewerLeftDClick(self, event)
        elif self.Mode == MODE_SELECTION and self.SelectedElement:
            self.SelectedElement.OnLeftDClick(event, self.GetLogicalDC(), self.Scaling)
            self.Refresh(False)
        event.Skip()

    def OnViewerMotion(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnViewerMotion(self, event)
        else:
            if self.rubberBand.IsShown():
                self.rubberBand.OnMotion(event, self.GetLogicalDC(), self.Scaling)
            elif self.Mode == MODE_SELECTION and self.SelectedElement:
                if not self.IsWire(self.SelectedElement) and not isinstance(self.SelectedElement, Graphic_Group):
                    self.SelectedElement.OnMotion(event, self.GetLogicalDC(), self.Scaling)
                    self.SelectedElement.Refresh()
            #
            # FIXME:
            # This code was forgotten by commit
            # 9c74d00ce93e from plcopeneditor_history repository
            # 'Last bugs on block and wire moving, resizing with cursor fixed'
            #
            # elif self.Mode == MODE_WIRE and self.SelectedElement:
            #     self.SelectedElement.ResetPoints()
            #     self.SelectedElement.OnMotion(event, self.GetLogicalDC(), self.Scaling)
            #     self.SelectedElement.GeneratePoints()
            #     self.SelectedElement.Refresh()
            self.UpdateScrollPos(event)
        event.Skip()

    def GetBlockName(self, block):
        blockName = block.__class__.__name__
        if blockName == "SFC_Divergence":
            blockName = block.Type
        return blockName

    # This method check the IEC 61131-3 compatibility between two SFC blocks
    def BlockCompatibility(self, startblock=None, endblock=None, direction=None):
        if startblock is not None and endblock is not None and \
           (isinstance(startblock, SFC_Objects) or isinstance(endblock, SFC_Objects)):
            # Full "SFC_StandardRules" table would be symmetrical and
            # to avoid duplicate records and minimize the table only upper part is defined.
            if direction == SOUTH or direction == EAST:
                startblock, endblock = endblock, startblock
            start = self.GetBlockName(startblock)
            end = self.GetBlockName(endblock)
            for val in self.SFC_StandardRules[start]:
                if end in val:
                    return True
            return False
        return True

    # -------------------------------------------------------------------------------
    #                          Keyboard event functions
    # -------------------------------------------------------------------------------

    def OnChar(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnChar(self, event)
        else:
            xpos, ypos = self.GetScrollPos(wx.HORIZONTAL), self.GetScrollPos(wx.VERTICAL)
            xmax = self.GetScrollRange(wx.HORIZONTAL) - self.GetScrollThumb(wx.HORIZONTAL)
            ymax = self.GetScrollRange(wx.VERTICAL) - self.GetScrollThumb(wx.VERTICAL)
            keycode = event.GetKeyCode()
            if self.Scaling:
                scaling = self.Scaling
            else:
                scaling = (8, 8)
            if keycode == wx.WXK_DELETE and self.SelectedElement:
                self.SelectedElement.Delete()
                self.SelectedElement = None
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)
            elif keycode == wx.WXK_LEFT:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(0, ypos)
                elif event.ControlDown():
                    event.Skip()
                elif self.SelectedElement:
                    self.SelectedElement.Move(-scaling[0], 0)
                    self.SelectedElement.RefreshModel()
                    self.RefreshBuffer()
                    self.RefreshScrollBars()
                    self.RefreshRect(self.GetScrolledRect(self.SelectedElement.GetRedrawRect(-scaling[0], 0)), False)
            elif keycode == wx.WXK_RIGHT:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(xmax, ypos)
                elif event.ControlDown():
                    event.Skip()
                elif self.SelectedElement:
                    self.SelectedElement.Move(scaling[0], 0)
                    self.SelectedElement.RefreshModel()
                    self.RefreshBuffer()
                    self.RefreshScrollBars()
                    self.RefreshRect(self.GetScrolledRect(self.SelectedElement.GetRedrawRect(scaling[0], 0)), False)
            elif keycode == wx.WXK_UP:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(xpos, 0)
                elif event.ControlDown():
                    event.Skip()
                elif self.SelectedElement:
                    self.SelectedElement.Move(0, -scaling[1])
                    self.SelectedElement.RefreshModel()
                    self.RefreshBuffer()
                    self.RefreshScrollBars()
                    self.RefreshRect(self.GetScrolledRect(self.SelectedElement.GetRedrawRect(0, -scaling[1])), False)
            elif keycode == wx.WXK_DOWN:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(xpos, ymax)
                elif event.ControlDown():
                    event.Skip()
                elif self.SelectedElement:
                    self.SelectedElement.Move(0, scaling[1])
                    self.SelectedElement.RefreshModel()
                    self.RefreshBuffer()
                    self.RefreshScrollBars()
                    self.RefreshRect(self.GetScrolledRect(self.SelectedElement.GetRedrawRect(0, scaling[1])), False)
            else:
                event.Skip()

    # -------------------------------------------------------------------------------
    #                          Adding element functions
    # -------------------------------------------------------------------------------

    def AddInitialStep(self, pos):
        dialog = SFCStepNameDialog(self.ParentWindow, _("Please enter step name"), _("Add a new initial step"), "", wx.OK | wx.CANCEL)
        dialog.SetPouNames(self.Controler.GetProjectPouNames(self.Debug))
        dialog.SetVariables(self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug))
        dialog.SetStepNames([block.GetName() for block in self.Blocks if isinstance(block, SFC_Step)])
        if dialog.ShowModal() == wx.ID_OK:
            id = self.GetNewId()
            name = dialog.GetValue()
            step = SFC_Step(self, name, True, id)
            min_width, min_height = step.GetMinSize()
            step.SetPosition(pos.x, pos.y)
            width, height = step.GetSize()
            step.SetSize(max(min_width, width), max(min_height, height))
            self.AddBlock(step)
            self.Controler.AddEditedElementStep(self.TagName, id)
            self.RefreshStepModel(step)
            self.RefreshBuffer()
            self.RefreshScrollBars()
            self.Refresh(False)
        dialog.Destroy()

    def AddStep(self):
        if self.SelectedElement in self.Wires or isinstance(self.SelectedElement, SFC_Step):
            dialog = SFCStepNameDialog(self.ParentWindow, _("Add a new step"), _("Please enter step name"), "", wx.OK | wx.CANCEL)
            dialog.SetPouNames(self.Controler.GetProjectPouNames(self.Debug))
            dialog.SetVariables(self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug))
            dialog.SetStepNames([block.GetName() for block in self.Blocks if isinstance(block, SFC_Step)])
            if dialog.ShowModal() == wx.ID_OK:
                name = dialog.GetValue()
                if self.IsWire(self.SelectedElement):
                    self.SelectedElement.SetSelectedSegment(None)
                    previous = self.SelectedElement.EndConnected
                    next = self.SelectedElement.StartConnected
                    self.SelectedElement.Clean()
                    self.RemoveWire(self.SelectedElement)
                else:
                    connectors = self.SelectedElement.GetConnectors()
                    if connectors["output"]:
                        previous = connectors["output"]
                        wires = previous.GetWires()
                        if len(wires) != 1:
                            return
                        wire = wires[0][0]
                        next = wire.StartConnected
                        wire.Clean()
                        self.RemoveWire(wire)
                    else:
                        self.SelectedElement.AddOutput()
                        connectors = self.SelectedElement.GetConnectors()
                        self.RefreshStepModel(self.SelectedElement)
                        previous = connectors["output"]
                        next = None
                previous_block = previous.GetParentBlock()
                if isinstance(previous_block, SFC_Step) or isinstance(previous_block, SFC_Divergence) and previous_block.GetType() in [SELECTION_DIVERGENCE, SELECTION_CONVERGENCE]:
                    transition = self.CreateTransition(previous)
                    transition_connectors = transition.GetConnectors()
                    step = self.CreateStep(name, transition_connectors["output"], next)
                else:
                    step = self.CreateStep(name, previous)
                    step.AddOutput()
                    step.RefreshModel()
                    step_connectors = step.GetConnectors()
                    transition = self.CreateTransition(step_connectors["output"], next)
                if self.IsWire(self.SelectedElement):
                    self.SelectedElement = wire
                    self.SelectedElement.SetSelectedSegment(0)
                else:
                    self.SelectedElement.SetSelected(False)
                    self.SelectedElement = step
                    self.SelectedElement.SetSelected(True)
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)
            dialog.Destroy()

    def AddStepAction(self):
        if isinstance(self.SelectedElement, SFC_Step):
            connectors = self.SelectedElement.GetConnectors()
            if not connectors["action"]:
                dialog = ActionBlockDialog(self.ParentWindow)
                dialog.SetQualifierList(self.Controler.GetQualifierTypes())
                dialog.SetActionList(self.Controler.GetEditedElementActions(self.TagName, self.Debug))
                dialog.SetVariableList(self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug))
                if dialog.ShowModal() == wx.ID_OK:
                    actions = dialog.GetValues()
                    self.SelectedElement.AddAction()
                    self.RefreshStepModel(self.SelectedElement)
                    connectors = self.SelectedElement.GetConnectors()
                    pos = connectors["action"].GetPosition(False)
                    id = self.GetNewId()
                    actionblock = SFC_ActionBlock(self, [], id)
                    actionblock.SetPosition(pos.x + SFC_WIRE_MIN_SIZE, pos.y - SFC_STEP_DEFAULT_SIZE[1] // 2)
                    actionblock_connector = actionblock.GetConnector()
                    wire = self.ConnectConnectors(actionblock_connector, connectors["action"])
                    wire.SetPoints([wx.Point(pos.x + SFC_WIRE_MIN_SIZE, pos.y), wx.Point(pos.x, pos.y)])
                    actionblock.SetActions(actions)
                    self.AddBlock(actionblock)
                    self.Controler.AddEditedElementActionBlock(self.TagName, id)
                    self.RefreshActionBlockModel(actionblock)
                    self.RefreshBuffer()
                    self.RefreshScrollBars()
                    self.Refresh(False)
                dialog.Destroy()

    def AddDivergence(self):
        if self.SelectedElement in self.Wires or isinstance(self.SelectedElement, (Graphic_Group, SFC_Step)):
            dialog = SFCDivergenceDialog(self.ParentWindow, self.Controler, self.TagName)
            dialog.SetPreviewFont(self.GetFont())
            if dialog.ShowModal() == wx.ID_OK:
                value = dialog.GetValues()
                if value["type"] == SELECTION_DIVERGENCE:
                    if self.SelectedElement in self.Wires and isinstance(self.SelectedElement.EndConnected.GetParentBlock(), SFC_Step):
                        self.SelectedElement.SetSelectedSegment(None)
                        previous = self.SelectedElement.EndConnected
                        next = self.SelectedElement.StartConnected
                        self.SelectedElement.Clean()
                        self.RemoveWire(self.SelectedElement)
                        self.SelectedElement = None
                    elif isinstance(self.SelectedElement, SFC_Step):
                        connectors = self.SelectedElement.GetConnectors()
                        if connectors["output"]:
                            previous = connectors["output"]
                            wires = previous.GetWires()
                            if len(wires) != 1:
                                return
                            wire = wires[0][0]
                            next = wire.StartConnected
                            wire.Clean()
                            self.RemoveWire(wire)
                        else:
                            self.SelectedElement.AddOutput()
                            connectors = self.SelectedElement.GetConnectors()
                            self.RefreshStepModel(self.SelectedElement)
                            previous = connectors["output"]
                            next = None
                    else:
                        return
                    id = self.GetNewId()
                    divergence = SFC_Divergence(self, SELECTION_DIVERGENCE, value["number"], id)
                    pos = previous.GetPosition(False)
                    previous_block = previous.GetParentBlock()
                    wire_size = GetWireSize(previous_block)
                    divergence.SetPosition(pos.x, pos.y + wire_size)
                    divergence_connectors = divergence.GetConnectors()
                    wire = self.ConnectConnectors(divergence_connectors["inputs"][0], previous)
                    previous_block.RefreshOutputPosition()
                    wire.SetPoints([wx.Point(pos.x, pos.y + wire_size), wx.Point(pos.x, pos.y)])
                    self.AddBlock(divergence)
                    self.Controler.AddEditedElementDivergence(self.TagName, id, value["type"])
                    self.RefreshDivergenceModel(divergence)
                    for _index, connector in enumerate(divergence_connectors["outputs"]):
                        if next:
                            wire = self.ConnectConnectors(next, connector)
                            pos = connector.GetPosition(False)
                            next_pos = next.GetPosition(False)
                            next_block = next.GetParentBlock()
                            divergence.RefreshOutputPosition((0, pos.y + SFC_WIRE_MIN_SIZE - next_pos.y))
                            divergence.RefreshConnectedPosition(connector)
                            wire.SetPoints([wx.Point(pos.x, pos.y + SFC_WIRE_MIN_SIZE), wx.Point(pos.x, pos.y)])
                            next_block.RefreshModel()
                            next = None
                        else:
                            transition = self.CreateTransition(connector)
                            transition_connectors = transition.GetConnectors()
                            _step = self.CreateStep("Step", transition_connectors["output"])
                elif value["type"] == SIMULTANEOUS_DIVERGENCE:
                    if self.SelectedElement in self.Wires and isinstance(self.SelectedElement.EndConnected.GetParentBlock(), SFC_Transition):
                        self.SelectedElement.SetSelectedSegment(None)
                        previous = self.SelectedElement.EndConnected
                        next = self.SelectedElement.StartConnected
                        self.SelectedElement.Clean()
                        self.RemoveWire(self.SelectedElement)
                        self.SelectedElement = None
                    elif isinstance(self.SelectedElement, SFC_Step):
                        connectors = self.SelectedElement.GetConnectors()
                        if connectors["output"]:
                            previous = connectors["output"]
                            wires = previous.GetWires()
                            if len(wires) != 1:
                                return
                            wire = wires[0][0]
                            next = wire.StartConnected
                            wire.Clean()
                            self.RemoveWire(wire)
                        else:
                            self.SelectedElement.AddOutput()
                            connectors = self.SelectedElement.GetConnectors()
                            self.RefreshStepModel(self.SelectedElement)
                            previous = connectors["output"]
                            next = None
                        transition = self.CreateTransition(previous)
                        transition_connectors = transition.GetConnectors()
                        previous = transition_connectors["output"]
                    else:
                        return
                    id = self.GetNewId()
                    divergence = SFC_Divergence(self, SIMULTANEOUS_DIVERGENCE, value["number"], id)
                    pos = previous.GetPosition(False)
                    previous_block = previous.GetParentBlock()
                    wire_size = GetWireSize(previous_block)
                    divergence.SetPosition(pos.x, pos.y + wire_size)
                    divergence_connectors = divergence.GetConnectors()
                    wire = self.ConnectConnectors(divergence_connectors["inputs"][0], previous)
                    previous_block.RefreshOutputPosition()
                    wire.SetPoints([wx.Point(pos.x, pos.y + wire_size), wx.Point(pos.x, pos.y)])
                    self.AddBlock(divergence)
                    self.Controler.AddEditedElementDivergence(self.TagName, id, value["type"])
                    self.RefreshDivergenceModel(divergence)
                    for _index, connector in enumerate(divergence_connectors["outputs"]):
                        if next:
                            wire = self.ConnectConnectors(next, connector)
                            pos = connector.GetPosition(False)
                            next_pos = next.GetPosition(False)
                            next_block = next.GetParentBlock()
                            divergence.RefreshOutputPosition((0, pos.y + SFC_WIRE_MIN_SIZE - next_pos.y))
                            divergence.RefreshConnectedPosition(connector)
                            wire.SetPoints([wx.Point(pos.x, pos.y + SFC_WIRE_MIN_SIZE), wx.Point(pos.x, pos.y)])
                            next_block.RefreshModel()
                            next = None
                        else:
                            _step = self.CreateStep("Step", connector)
                elif isinstance(self.SelectedElement, Graphic_Group) and len(self.SelectedElement.GetElements()) > 1:
                    next = None
                    for element in self.SelectedElement.GetElements():
                        connectors = element.GetConnectors()
                        if not isinstance(element, SFC_Step) or connectors["output"] and next:
                            return
                        elif connectors["output"] and not next:
                            wires = connectors["output"].GetWires()
                            if len(wires) != 1:
                                return
                            if value["type"] == SELECTION_CONVERGENCE:
                                transition = wires[0][0].StartConnected.GetParentBlock()
                                transition_connectors = transition.GetConnectors()
                                wires = transition_connectors["output"].GetWires()
                                if len(wires) != 1:
                                    return
                            wire = wires[0][0]
                            next = wire.StartConnected
                            wire.Clean()
                            self.RemoveWire(wire)
                    inputs = []
                    for input in self.SelectedElement.GetElements():
                        input_connectors = input.GetConnectors()
                        if not input_connectors["output"]:
                            input.AddOutput()
                            input.RefreshModel()
                            input_connectors = input.GetConnectors()
                            if value["type"] == SELECTION_CONVERGENCE:
                                transition = self.CreateTransition(input_connectors["output"])
                                transition_connectors = transition.GetConnectors()
                                inputs.append(transition_connectors["output"])
                            else:
                                inputs.append(input_connectors["output"])
                        elif value["type"] == SELECTION_CONVERGENCE:
                            wires = input_connectors["output"].GetWires()
                            transition = wires[0][0].StartConnected.GetParentBlock()
                            transition_connectors = transition.GetConnectors()
                            inputs.append(transition_connectors["output"])
                        else:
                            inputs.append(input_connectors["output"])
                    id = self.GetNewId()
                    divergence = SFC_Divergence(self, value["type"], len(inputs), id)
                    pos = inputs[0].GetPosition(False)
                    divergence.SetPosition(pos.x, pos.y + SFC_WIRE_MIN_SIZE)
                    divergence_connectors = divergence.GetConnectors()
                    for i, input in enumerate(inputs):
                        pos = input.GetPosition(False)
                        wire = self.ConnectConnectors(divergence_connectors["inputs"][i], input)
                        wire_size = GetWireSize(input)
                        wire.SetPoints([wx.Point(pos.x, pos.y + wire_size), wx.Point(pos.x, pos.y)])
                        input_block = input.GetParentBlock()
                        input_block.RefreshOutputPosition()
                    divergence.RefreshPosition()
                    pos = divergence_connectors["outputs"][0].GetRelPosition()
                    divergence.MoveConnector(divergence_connectors["outputs"][0], - pos.x)
                    self.AddBlock(divergence)
                    self.Controler.AddEditedElementDivergence(self.TagName, id, value["type"])
                    self.RefreshDivergenceModel(divergence)
                    if next:
                        wire = self.ConnectConnectors(next, divergence_connectors["outputs"][0])
                        pos = divergence_connectors["outputs"][0].GetPosition(False)
                        next_pos = next.GetPosition(False)
                        next_block = next.GetParentBlock()
                        divergence.RefreshOutputPosition((0, pos.y + SFC_WIRE_MIN_SIZE - next_pos.y))
                        divergence.RefreshConnectedPosition(divergence_connectors["outputs"][0])
                        wire.SetPoints([wx.Point(pos.x, pos.y + SFC_WIRE_MIN_SIZE), wx.Point(pos.x, pos.y)])
                        next_block.RefreshModel()
                    else:
                        if value["type"] == SELECTION_CONVERGENCE:
                            previous = divergence_connectors["outputs"][0]
                        else:
                            transition = self.CreateTransition(divergence_connectors["outputs"][0])
                            transition_connectors = transition.GetConnectors()
                            previous = transition_connectors["output"]
                        self.CreateStep("Step", previous)
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)
            dialog.Destroy()

    def AddDivergenceBranch(self, divergence):
        if isinstance(divergence, SFC_Divergence):
            if self.GetDrawingMode() == FREEDRAWING_MODE:
                divergence.AddBranch()
                self.RefreshDivergenceModel(divergence)
            else:
                type = divergence.GetType()
                if type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
                    divergence.AddBranch()
                    divergence_connectors = divergence.GetConnectors()
                    if type == SELECTION_DIVERGENCE:
                        transition = self.CreateTransition(divergence_connectors["outputs"][-1])
                        transition_connectors = transition.GetConnectors()
                        previous = transition_connectors["output"]
                    else:
                        previous = divergence_connectors["outputs"][-1]
                    _step = self.CreateStep("Step", previous)
            self.RefreshBuffer()
            self.RefreshScrollBars()
            self.Refresh(False)

    def RemoveDivergenceBranch(self, divergence):
        if isinstance(divergence, SFC_Divergence):
            if self.GetDrawingMode() == FREEDRAWING_MODE:
                divergence.RemoveHandledBranch()
                self.RefreshDivergenceModel(divergence)
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)

    def AddJump(self):
        if isinstance(self.SelectedElement, SFC_Step) and not self.SelectedElement.Output:
            choices = []
            for block in self.Blocks:
                if isinstance(block, SFC_Step):
                    choices.append(block.GetName())
            dialog = wx.SingleChoiceDialog(self.ParentWindow,
                                           _("Add a new jump"),
                                           _("Please choose a target"),
                                           choices,
                                           wx.DEFAULT_DIALOG_STYLE | wx.OK | wx.CANCEL)
            if dialog.ShowModal() == wx.ID_OK:
                value = dialog.GetStringSelection()
                self.SelectedElement.AddOutput()
                self.RefreshStepModel(self.SelectedElement)
                step_connectors = self.SelectedElement.GetConnectors()
                transition = self.CreateTransition(step_connectors["output"])
                transition_connectors = transition.GetConnectors()
                id = self.GetNewId()
                jump = SFC_Jump(self, value, id)
                pos = transition_connectors["output"].GetPosition(False)
                jump.SetPosition(pos.x, pos.y + SFC_WIRE_MIN_SIZE)
                self.AddBlock(jump)
                self.Controler.AddEditedElementJump(self.TagName, id)
                jump_connector = jump.GetConnector()
                wire = self.ConnectConnectors(jump_connector, transition_connectors["output"])
                transition.RefreshOutputPosition()
                wire.SetPoints([wx.Point(pos.x, pos.y + SFC_WIRE_MIN_SIZE), wx.Point(pos.x, pos.y)])
                self.RefreshJumpModel(jump)
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)
            dialog.Destroy()

    def EditStepContent(self, step):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.EditStepContent(self, step)
        else:
            dialog = SFCStepNameDialog(self.ParentWindow, _("Edit step name"), _("Please enter step name"), step.GetName(), wx.OK | wx.CANCEL)
            dialog.SetPouNames(self.Controler.GetProjectPouNames(self.Debug))
            dialog.SetVariables(self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug))
            dialog.SetStepNames([block.GetName() for block in self.Blocks if isinstance(block, SFC_Step) and block.GetName() != step.GetName()])
            if dialog.ShowModal() == wx.ID_OK:
                value = dialog.GetValue()
                step.SetName(value)
                min_size = step.GetMinSize()
                size = step.GetSize()
                step.UpdateSize(max(min_size[0], size[0]), max(min_size[1], size[1]))
                step.RefreshModel()
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)
            dialog.Destroy()

    # -------------------------------------------------------------------------------
    #                          Delete element functions
    # -------------------------------------------------------------------------------

    def DeleteStep(self, step):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteStep(self, step)
        else:
            step_connectors = step.GetConnectors()
            if not step.GetInitial() or not step_connectors["output"]:
                previous = step.GetPreviousConnector()
                if previous:
                    previous_block = previous.GetParentBlock()
                else:
                    previous_block = None
                next = step.GetNextConnector()
                if next:
                    next_block = next.GetParentBlock()
                else:
                    next_block = None
                if isinstance(next_block, SFC_Transition):
                    self.RemoveTransition(next_block)
                    next = step.GetNextConnector()
                    if next:
                        next_block = next.GetParentBlock()
                    else:
                        next_block = None
                elif isinstance(previous_block, SFC_Transition):
                    self.RemoveTransition(previous_block)
                    previous = step.GetPreviousConnector()
                    if previous:
                        previous_block = previous.GetParentBlock()
                    else:
                        previous_block = None
                wire = self.RemoveStep(step)
                self.SelectedElement = None
                if next_block:
                    if isinstance(next_block, SFC_Divergence) and next_block.GetType() == SIMULTANEOUS_CONVERGENCE and isinstance(previous_block, SFC_Divergence) and previous_block.GetType() == SIMULTANEOUS_DIVERGENCE:
                        wire.Clean()
                        self.RemoveWire(wire)
                        next_block.RemoveBranch(next)
                        if next_block.GetBranchNumber() < 2:
                            self.DeleteDivergence(next_block)
                        else:
                            next_block.RefreshModel()
                        previous_block.RemoveBranch(previous)
                        if previous_block.GetBranchNumber() < 2:
                            self.DeleteDivergence(previous_block)
                        else:
                            previous_block.RefreshModel()
                    else:
                        pos = previous.GetPosition(False)
                        next_pos = next.GetPosition(False)
                        wire_size = GetWireSize(previous_block)
                        previous_block.RefreshOutputPosition((0, pos.y + wire_size - next_pos.y))
                        wire.SetPoints([wx.Point(pos.x, pos.y + wire_size), wx.Point(pos.x, pos.y)])
                        if isinstance(next_block, SFC_Divergence):
                            next_block.RefreshPosition()
                        previous_block.RefreshOutputModel(True)
                else:
                    if isinstance(previous_block, SFC_Step):
                        previous_block.RemoveOutput()
                        self.RefreshStepModel(previous_block)
                    elif isinstance(previous_block, SFC_Divergence):
                        if previous_block.GetType() in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
                            self.DeleteDivergence(previous_block)
                        else:
                            previous_block.RemoveBranch(previous)
                            if previous_block.GetBranchNumber() < 2:
                                self.DeleteDivergence(previous_block)
                            else:
                                self.RefreshDivergenceModel(previous_block)

    def DeleteTransition(self, transition):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteTransition(self, transition)
        else:
            previous = transition.GetPreviousConnector()
            previous_block = previous.GetParentBlock()
            next = transition.GetNextConnector()
            next_block = next.GetParentBlock()
            if isinstance(previous_block, SFC_Divergence) and previous_block.GetType() == SELECTION_DIVERGENCE and isinstance(next_block, SFC_Divergence) and next_block.GetType() == SELECTION_CONVERGENCE:
                wires = previous.GetWires()
                if len(wires) != 1:
                    return
                wire = wires[0][0]
                wire.Clean()
                self.RemoveWire(wire)
                wires = next.GetWires()
                if len(wires) != 1:
                    return
                wire = wires[0][0]
                wire.Clean()
                self.RemoveWire(wire)
                transition.Clean()
                self.RemoveBlock(transition)
                self.Controler.RemoveEditedElementInstance(self.TagName, transition.GetId())
                previous_block.RemoveBranch(previous)
                if previous_block.GetBranchNumber() < 2:
                    self.DeleteDivergence(previous_block)
                else:
                    self.RefreshDivergenceModel(previous_block)
                next_block.RemoveBranch(next)
                if next_block.GetBranchNumber() < 2:
                    self.DeleteDivergence(next_block)
                else:
                    self.RefreshDivergenceModel(next_block)

    def DeleteDivergence(self, divergence):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteDivergence(self, divergence)
        else:
            connectors = divergence.GetConnectors()
            type = divergence.GetType()
            if type in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
                wires = connectors["outputs"][0].GetWires()
                if len(wires) > 1:
                    return
                elif len(wires) == 1:
                    next = wires[0][0].StartConnected
                    next_block = next.GetParentBlock()
                    wire = wires[0][0]
                    wire.Clean()
                    self.RemoveWire(wire)
                else:
                    next = None
                    next_block = None
                for index, connector in enumerate(connectors["inputs"]):
                    if next and index == 0:
                        wires = connector.GetWires()
                        wire = wires[0][0]
                        previous = wires[0][0].EndConnected
                        wire.Clean()
                        self.RemoveWire(wire)
                    else:
                        if type == SELECTION_CONVERGENCE:
                            wires = connector.GetWires()
                            previous_block = wires[0][0].EndConnected.GetParentBlock()
                            self.RemoveTransition(previous_block)
                        wires = connector.GetWires()
                        wire = wires[0][0]
                        previous_connector = wire.EndConnected
                        previous_block = previous_connector.GetParentBlock()
                        wire.Clean()
                        self.RemoveWire(wire)
                        if isinstance(previous_block, SFC_Step):
                            previous_block.RemoveOutput()
                            self.RefreshStepModel(previous_block)
                        elif isinstance(previous_block, SFC_Divergence):
                            if previous_block.GetType() in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
                                previous_block.RemoveBranch(previous_connector)
                                if previous_block.GetBranchNumber() < 2:
                                    self.DeleteDivergence(previous_block)
                                else:
                                    self.RefreshDivergenceModel(previous_block)
                            else:
                                self.DeleteDivergence(previous_block)
                divergence.Clean()
                self.RemoveBlock(divergence)
                self.Controler.RemoveEditedElementInstance(self.TagName, divergence.GetId())
                if next:
                    wire = self.ConnectConnectors(next, previous)
                    previous_block = previous.GetParentBlock()
                    previous_pos = previous.GetPosition(False)
                    next_pos = next.GetPosition(False)
                    wire_size = GetWireSize(previous_block)
                    previous_block.RefreshOutputPosition((0, previous_pos.y + wire_size - next_pos.y))
                    wire.SetPoints([wx.Point(previous_pos.x, previous_pos.y + wire_size),
                                    wx.Point(previous_pos.x, previous_pos.y)])
                    if isinstance(next_block, SFC_Divergence):
                        next_block.RefreshPosition()
                    previous_block.RefreshOutputModel(True)
            elif divergence.GetBranchNumber() == 1:
                wires = connectors["inputs"][0].GetWires()
                if len(wires) != 1:
                    return
                wire = wires[0][0]
                previous = wire.EndConnected
                previous_block = previous.GetParentBlock()
                wire.Clean()
                self.RemoveWire(wire)
                wires = connectors["outputs"][0].GetWires()
                if len(wires) != 1:
                    return
                wire = wires[0][0]
                next = wire.StartConnected
                next_block = next.GetParentBlock()
                wire.Clean()
                self.RemoveWire(wire)
                divergence.Clean()
                self.RemoveBlock(divergence)
                self.Controler.RemoveEditedElementInstance(self.TagName, divergence.GetId())
                wire = self.ConnectConnectors(next, previous)
                previous_pos = previous.GetPosition(False)
                next_pos = next.GetPosition(False)
                wire_size = GetWireSize(previous_block)
                previous_block.RefreshOutputPosition((previous_pos.x - next_pos.x, previous_pos.y + wire_size - next_pos.y))
                wire.SetPoints([wx.Point(previous_pos.x, previous_pos.y + wire_size),
                                wx.Point(previous_pos.x, previous_pos.y)])
                if isinstance(next_block, SFC_Divergence):
                    next_block.RefreshPosition()
                previous_block.RefreshOutputModel(True)

    def DeleteJump(self, jump):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteJump(self, jump)
        else:
            previous = jump.GetPreviousConnector()
            previous_block = previous.GetParentBlock()
            if isinstance(previous_block, SFC_Transition):
                self.RemoveTransition(previous_block)
                previous = jump.GetPreviousConnector()
                if previous:
                    previous_block = previous.GetParentBlock()
                else:
                    previous_block = None
            wires = previous.GetWires()
            if len(wires) != 1:
                return
            wire = wires[0][0]
            wire.Clean()
            self.RemoveWire(wire)
            jump.Clean()
            self.RemoveBlock(jump)
            self.Controler.RemoveEditedElementInstance(self.TagName, jump.GetId())
            if isinstance(previous_block, SFC_Step):
                previous_block.RemoveOutput()
                self.RefreshStepModel(previous_block)
            elif isinstance(previous_block, SFC_Divergence):
                if previous_block.GetType() in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
                    self.DeleteDivergence(previous_block)
                else:
                    previous_block.RemoveBranch(previous)
                    if previous_block.GetBranchNumber() < 2:
                        self.DeleteDivergence(previous_block)
                    else:
                        previous_block.RefreshModel()

    def DeleteActionBlock(self, actionblock):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteActionBlock(self, actionblock)
        else:
            connector = actionblock.GetConnector()
            wires = connector.GetWires()
            if len(wires) != 1:
                return
            wire = wires[0][0]
            step = wire.EndConnected.GetParentBlock()
            wire.Clean()
            self.RemoveWire(wire)
            actionblock.Clean()
            self.RemoveBlock(actionblock)
            self.Controler.RemoveEditedElementInstance(self.TagName, actionblock.GetId())
            step.RemoveAction()
            self.RefreshStepModel(step)
            step.RefreshOutputPosition()
            step.RefreshOutputModel(True)

    def DeleteWire(self, wire):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteWire(self, wire)

    # -------------------------------------------------------------------------------
    #                          Model update functions
    # -------------------------------------------------------------------------------

    def RefreshBlockModel(self, block):
        blockid = block.GetId()
        infos = {}
        infos["type"] = block.GetType()
        infos["name"] = block.GetName()
        infos["x"], infos["y"] = block.GetPosition()
        infos["width"], infos["height"] = block.GetSize()
        infos["connectors"] = block.GetConnectors()
        self.Controler.SetEditedElementBlockInfos(self.TagName, blockid, infos)
