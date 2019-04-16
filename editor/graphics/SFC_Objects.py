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
from future.builtins import round

import wx
from six.moves import xrange

from graphics.GraphicCommons import *
from graphics.DebugDataConsumer import DebugDataConsumer
from plcopen.structures import *


def GetWireSize(block):
    if isinstance(block, SFC_Step):
        return SFC_WIRE_MIN_SIZE + block.GetActionExtraLineNumber() * SFC_ACTION_MIN_SIZE[1]
    else:
        return SFC_WIRE_MIN_SIZE

# -------------------------------------------------------------------------------
#                         Sequencial Function Chart Step
# -------------------------------------------------------------------------------


class SFC_Step(Graphic_Element, DebugDataConsumer):
    """
    Class that implements the graphic representation of a step
    """

    # Create a new step
    def __init__(self, parent, name, initial=False, id=None):
        Graphic_Element.__init__(self, parent)
        DebugDataConsumer.__init__(self)
        self.SetName(name)
        self.Initial = initial
        self.Id = id
        self.Highlights = []
        self.Size = wx.Size(SFC_STEP_DEFAULT_SIZE[0], SFC_STEP_DEFAULT_SIZE[1])
        # Create an input and output connector
        if not self.Initial:
            self.Input = Connector(self, "", None, wx.Point(self.Size[0] // 2, 0), NORTH)
        else:
            self.Input = None
        self.Output = None
        self.Action = None
        self.PreviousValue = None
        self.PreviousSpreading = False

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None
        if self.Output is not None:
            self.Output.Flush()
            self.Output = None
        if self.Action is not None:
            self.Action.Flush()
            self.Action = None

    def SetForced(self, forced):
        if self.Forced != forced:
            self.Forced = forced
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)

    def SetValue(self, value):
        self.PreviousValue = self.Value
        self.Value = value
        if self.Value != self.PreviousValue:
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)
            self.SpreadCurrent()

    def SpreadCurrent(self):
        if self.Parent.Debug:
            spreading = self.Value
            if spreading and not self.PreviousSpreading:
                if self.Output is not None:
                    self.Output.SpreadCurrent(True)
                if self.Action is not None:
                    self.Action.SpreadCurrent(True)
            elif not spreading and self.PreviousSpreading:
                if self.Output is not None:
                    self.Output.SpreadCurrent(False)
                if self.Action is not None:
                    self.Action.SpreadCurrent(False)
            self.PreviousSpreading = spreading

    # Make a clone of this SFC_Step
    def Clone(self, parent, id=None, name="Step", pos=None):
        step = SFC_Step(parent, name, self.Initial, id)
        step.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            step.SetPosition(pos.x, pos.y)
        else:
            step.SetPosition(self.Pos.x, self.Pos.y)
        if self.Input:
            step.Input = self.Input.Clone(step)
        if self.Output:
            step.Output = self.Output.Clone(step)
        if self.Action:
            step.Action = self.Action.Clone(step)
        return step

    def GetConnectorTranslation(self, element):
        connectors = {}
        if self.Input is not None:
            connectors[self.Input] = element.Input
        if self.Output is not None:
            connectors[self.Output] = element.Output
        if self.Action is not None:
            connectors[self.Action] = element.Action
        return connectors

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if self.Input:
            rect = rect.Union(self.Input.GetRedrawRect(movex, movey))
        if self.Output:
            rect = rect.Union(self.Output.GetRedrawRect(movex, movey))
        if self.Action:
            rect = rect.Union(self.Action.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            if self.Input and self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
            if self.Output and self.Output.IsConnected():
                rect = rect.Union(self.Output.GetConnectedRedrawRect(movex, movey))
            if self.Action and self.Action.IsConnected():
                rect = rect.Union(self.Action.GetConnectedRedrawRect(movex, movey))
        return rect

    # Delete this step by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteStep(self)

    # Unconnect input and output
    def Clean(self):
        if self.Input:
            self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        if self.Output:
            self.Output.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        if self.Action:
            self.Action.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Refresh the size of text for name
    def RefreshNameSize(self):
        self.NameSize = self.Parent.GetTextExtent(self.Name)

    # Add output connector to step
    def AddInput(self):
        if not self.Input:
            self.Input = Connector(self, "", None, wx.Point(self.Size[0] // 2, 0), NORTH)
            self.RefreshBoundingBox()

    # Remove output connector from step
    def RemoveInput(self):
        if self.Input:
            self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
            self.Input = None
            self.RefreshBoundingBox()

    # Add output connector to step
    def AddOutput(self):
        if not self.Output:
            self.Output = Connector(self, "", None, wx.Point(self.Size[0] // 2, self.Size[1]), SOUTH, onlyone=True)
            self.RefreshBoundingBox()

    # Remove output connector from step
    def RemoveOutput(self):
        if self.Output:
            self.Output.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
            self.Output = None
            self.RefreshBoundingBox()

    # Add action connector to step
    def AddAction(self):
        if not self.Action:
            self.Action = Connector(self, "", None, wx.Point(self.Size[0], self.Size[1] // 2), EAST, onlyone=True)
            self.RefreshBoundingBox()

    # Remove action connector from step
    def RemoveAction(self):
        if self.Action:
            self.Action.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
            self.Action = None
            self.RefreshBoundingBox()

    # Refresh the step bounding box
    def RefreshBoundingBox(self):
        # TODO: check and remove dead coded
        #
        # Calculate the bounding box size
        # if self.Action:
        #     bbx_width = self.Size[0] + CONNECTOR_SIZE
        # else:
        #     bbx_width = self.Size[0]
        # if self.Initial:
        #     bbx_y = self.Pos.y
        #     bbx_height = self.Size[1]
        #     if self.Output:
        #         bbx_height += CONNECTOR_SIZE
        # else:
        #     bbx_y = self.Pos.y - CONNECTOR_SIZE
        #     bbx_height = self.Size[1] + CONNECTOR_SIZE
        #     if self.Output:
        #         bbx_height += CONNECTOR_SIZE
        # self.BoundingBox = wx.Rect(self.Pos.x, bbx_y, bbx_width + 1, bbx_height + 1)
        self.BoundingBox = wx.Rect(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)

    # Refresh the positions of the step connectors
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        horizontal_pos = self.Size[0] // 2
        vertical_pos = self.Size[1] // 2
        if scaling is not None:
            horizontal_pos = round((self.Pos.x + horizontal_pos) / scaling[0]) * scaling[0] - self.Pos.x
            vertical_pos = round((self.Pos.y + vertical_pos) / scaling[1]) * scaling[1] - self.Pos.y
        # Update input position if it exists
        if self.Input:
            self.Input.SetPosition(wx.Point(horizontal_pos, 0))
        # Update output position
        if self.Output:
            self.Output.SetPosition(wx.Point(horizontal_pos, self.Size[1]))
        # Update action position if it exists
        if self.Action:
            self.Action.SetPosition(wx.Point(self.Size[0], vertical_pos))
        self.RefreshConnected()

    # Refresh the position of wires connected to step
    def RefreshConnected(self, exclude=None):
        if self.Input:
            self.Input.MoveConnected(exclude)
        if self.Output:
            self.Output.MoveConnected(exclude)
        if self.Action:
            self.Action.MoveConnected(exclude)

    # Returns the step connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test input, output and action connector if they exists
            # if self.Input and name == self.Input.GetName():
            #    return self.Input
            if self.Output and name == self.Output.GetName():
                return self.Output
            if self.Action and name == self.Action.GetName():
                return self.Action
        connectors = []
        # Test input connector if it exists
        if self.Input:
            connectors.append(self.Input)
        # Test output connector if it exists
        if self.Output:
            connectors.append(self.Output)
        # Test action connector if it exists
        if self.Action:
            connectors.append(self.Action)
        return self.FindNearestConnector(position, connectors)

    # Returns action step connector
    def GetActionConnector(self):
        return self.Action

    # Returns input and output step connectors
    def GetConnectors(self):
        connectors = {"inputs": [], "outputs": []}
        if self.Input:
            connectors["inputs"].append(self.Input)
        if self.Output:
            connectors["outputs"].append(self.Output)
        return connectors

    # Test if point given is on step input or output connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector if it exists
        if self.Input and self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        # Test output connector
        if self.Output and self.Output.TestPoint(pt, direction, exclude):
            return self.Output
        # Test action connector
        if self.Action and self.Action.TestPoint(pt, direction, exclude):
            return self.Action
        return None

    # Changes the step name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    # Returns the step name
    def GetName(self):
        return self.Name

    # Returns the step initial property
    def GetInitial(self):
        return self.Initial

    # Returns the connector connected to input
    def GetPreviousConnector(self):
        if self.Input:
            wires = self.Input.GetWires()
            if len(wires) == 1:
                return wires[0][0].GetOtherConnected(self.Input)
        return None

    # Returns the connector connected to output
    def GetNextConnector(self):
        if self.Output:
            wires = self.Output.GetWires()
            if len(wires) == 1:
                return wires[0][0].GetOtherConnected(self.Output)
        return None

    # Returns the connector connected to action
    def GetActionConnected(self):
        if self.Action:
            wires = self.Action.GetWires()
            if len(wires) == 1:
                return wires[0][0].GetOtherConnected(self.Action)
        return None

    # Returns the number of action line
    def GetActionExtraLineNumber(self):
        if self.Action:
            wires = self.Action.GetWires()
            if len(wires) != 1:
                return 0
            action_block = wires[0][0].GetOtherConnected(self.Action).GetParentBlock()
            return max(0, action_block.GetLineNumber() - 1)
        return 0

    # Returns the step minimum size
    def GetMinSize(self):
        text_width, text_height = self.Parent.GetTextExtent(self.Name)
        if self.Initial:
            return text_width + 14, text_height + 14
        else:
            return text_width + 10, text_height + 10

    # Updates the step size
    def UpdateSize(self, width, height):
        diffx = self.Size.GetWidth() // 2 - width // 2
        diffy = height - self.Size.GetHeight()
        self.Move(diffx, 0)
        Graphic_Element.SetSize(self, width, height)
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            self.RefreshConnected()
        else:
            self.RefreshOutputPosition((0, diffy))

    # Align input element with this step
    def RefreshInputPosition(self):
        if self.Input:
            current_pos = self.Input.GetPosition(False)
            input = self.GetPreviousConnector()
            if input:
                input_pos = input.GetPosition(False)
                diffx = current_pos.x - input_pos.x
                input_block = input.GetParentBlock()
                if isinstance(input_block, SFC_Divergence):
                    input_block.MoveConnector(input, diffx)
                else:
                    if isinstance(input_block, SFC_Step):
                        input_block.MoveActionBlock((diffx, 0))
                    input_block.Move(diffx, 0)
                    input_block.RefreshInputPosition()

    # Align output element with this step
    def RefreshOutputPosition(self, move=None):
        if self.Output:
            wires = self.Output.GetWires()
            if len(wires) != 1:
                return
            current_pos = self.Output.GetPosition(False)
            output = wires[0][0].GetOtherConnected(self.Output)
            output_pos = output.GetPosition(False)
            diffx = current_pos.x - output_pos.x
            output_block = output.GetParentBlock()
            wire_size = SFC_WIRE_MIN_SIZE + self.GetActionExtraLineNumber() * SFC_ACTION_MIN_SIZE[1]
            diffy = wire_size - output_pos.y + current_pos.y
            if diffy != 0:
                if isinstance(output_block, SFC_Step):
                    output_block.MoveActionBlock((diffx, diffy))
                wires[0][0].SetPoints([wx.Point(current_pos.x, current_pos.y + wire_size),
                                       wx.Point(current_pos.x, current_pos.y)])
                if not isinstance(output_block, SFC_Divergence) or output_block.GetConnectors()["inputs"].index(output) == 0:
                    output_block.Move(diffx, diffy, self.Parent.Wires)
                    output_block.RefreshOutputPosition((diffx, diffy))
                else:
                    output_block.RefreshPosition()
            elif move:
                if isinstance(output_block, SFC_Step):
                    output_block.MoveActionBlock(move)
                wires[0][0].Move(move[0], move[1], True)
                if not isinstance(output_block, SFC_Divergence) or output_block.GetConnectors()["inputs"].index(output) == 0:
                    output_block.Move(move[0], move[1], self.Parent.Wires)
                    output_block.RefreshOutputPosition(move)
                else:
                    output_block.RefreshPosition()
            elif isinstance(output_block, SFC_Divergence):
                output_block.MoveConnector(output, diffx)
            else:
                if isinstance(output_block, SFC_Step):
                    output_block.MoveActionBlock((diffx, 0))
                output_block.Move(diffx, 0)
                output_block.RefreshOutputPosition()

    # Refresh action element with this step
    def MoveActionBlock(self, move):
        if self.Action:
            wires = self.Action.GetWires()
            if len(wires) != 1:
                return
            action_block = wires[0][0].GetOtherConnected(self.Action).GetParentBlock()
            action_block.Move(move[0], move[1], self.Parent.Wires)
            wires[0][0].Move(move[0], move[1], True)

    # Resize the divergence from position and size given
    def Resize(self, x, y, width, height):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            self.UpdateSize(width, height)
        else:
            Graphic_Element.Resize(self, x, y, width, height)

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the step properties
        self.Parent.EditStepContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the menu with special items for a step
        self.Parent.PopupDefaultMenu()

    # Refreshes the step state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        handle_type, _handle = self.Handle
        if handle_type == HANDLE_MOVE:
            movex = max(-self.BoundingBox.x, movex)
            movey = max(-self.BoundingBox.y, movey)
            if scaling is not None:
                movex = round((self.Pos.x + movex) / scaling[0]) * scaling[0] - self.Pos.x
                movey = round((self.Pos.y + movey) / scaling[1]) * scaling[1] - self.Pos.y
            if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
                self.Move(movex, movey)
                self.RefreshConnected()
                return movex, movey
            elif self.Initial:
                self.MoveActionBlock((movex, movey))
                self.Move(movex, movey, self.Parent.Wires)
                self.RefreshOutputPosition((movex, movey))
                return movex, movey
            else:
                self.MoveActionBlock((movex, 0))
                self.Move(movex, 0)
                self.RefreshInputPosition()
                self.RefreshOutputPosition()
                return movex, 0
        else:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)

    # Refresh input element model
    def RefreshInputModel(self):
        if self.Input:
            input = self.GetPreviousConnector()
            if input:
                input_block = input.GetParentBlock()
                input_block.RefreshModel(False)
                if not isinstance(input_block, SFC_Divergence):
                    input_block.RefreshInputModel()

    # Refresh output element model
    def RefreshOutputModel(self, move=False):
        if self.Output:
            output = self.GetNextConnector()
            if output:
                output_block = output.GetParentBlock()
                output_block.RefreshModel(False)
                if not isinstance(output_block, SFC_Divergence) or move:
                    output_block.RefreshOutputModel(move)

    # Refreshes the step model
    def RefreshModel(self, move=True):
        self.Parent.RefreshStepModel(self)
        if self.Action:
            action = self.GetActionConnected()
            if action:
                action_block = action.GetParentBlock()
                action_block.RefreshModel(False)
        # If step has moved, refresh the model of wires connected to output
        if move:
            if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
                self.RefreshInputModel()
                self.RefreshOutputModel(self.Initial)
            elif self.Output:
                self.Output.RefreshWires()

    # Adds an highlight to the connection
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "name" and start[0] == 0 and end[0] == 0:
            AddHighlight(self.Highlights, (start, end, highlight_type))

    # Removes an highlight from the connection
    def RemoveHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "name":
            RemoveHighlight(self.Highlights, (start, end, highlight_type))

    # Removes all the highlights of one particular type from the connection
    def ClearHighlight(self, highlight_type=None):
        ClearHighlights(self.Highlights, highlight_type)

    # Draws step
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value:
            if self.Forced:
                dc.SetPen(MiterPen(wx.CYAN))
            else:
                dc.SetPen(MiterPen(wx.GREEN))
        elif self.Forced:
            dc.SetPen(MiterPen(wx.BLUE))
        else:
            dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.WHITE_BRUSH)

        if getattr(dc, "printing", False):
            name_size = dc.GetTextExtent(self.Name)
        else:
            name_size = self.NameSize

        # Draw two rectangles for representing the step
        dc.DrawRectangle(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)
        if self.Initial:
            dc.DrawRectangle(self.Pos.x + 2, self.Pos.y + 2, self.Size[0] - 3, self.Size[1] - 3)
        # Draw step name
        name_pos = (self.Pos.x + (self.Size[0] - name_size[0]) // 2,
                    self.Pos.y + (self.Size[1] - name_size[1]) // 2)
        dc.DrawText(self.Name, name_pos[0], name_pos[1])
        # Draw input and output connectors
        if self.Input:
            self.Input.Draw(dc)
        if self.Output:
            self.Output.Draw(dc)
        if self.Action:
            self.Action.Draw(dc)

        if not getattr(dc, "printing", False):
            DrawHighlightedText(dc, self.Name, self.Highlights, name_pos[0], name_pos[1])


# -------------------------------------------------------------------------------
#                       Sequencial Function Chart Transition
# -------------------------------------------------------------------------------


class SFC_Transition(Graphic_Element, DebugDataConsumer):
    """
    Class that implements the graphic representation of a transition
    """

    # Create a new transition
    def __init__(self, parent, type="reference", condition=None, priority=0, id=None):
        Graphic_Element.__init__(self, parent)
        DebugDataConsumer.__init__(self)
        self.Type = None
        self.Id = id
        self.Priority = 0
        self.Size = wx.Size(SFC_TRANSITION_SIZE[0], SFC_TRANSITION_SIZE[1])
        # Create an input and output connector
        self.Input = Connector(self,  "", None, wx.Point(self.Size[0] // 2, 0),            NORTH, onlyone=True)
        self.Output = Connector(self, "", None, wx.Point(self.Size[0] // 2, self.Size[1]), SOUTH, onlyone=True)
        self.SetType(type, condition)
        self.SetPriority(priority)
        self.Highlights = {}
        self.PreviousValue = None
        self.PreviousSpreading = False

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None
        if self.Output is not None:
            self.Output.Flush()
            self.Output = None
        if self.Type == "connection" and self.Condition is not None:
            self.Condition.Flush()
            self.Condition = None

    def SetForced(self, forced):
        if self.Forced != forced:
            self.Forced = forced
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)

    def SetValue(self, value):
        self.PreviousValue = self.Value
        self.Value = value
        if self.Value != self.PreviousValue:
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)
            self.SpreadCurrent()

    def SpreadCurrent(self):
        if self.Parent.Debug:
            if self.Value is None:
                self.Value = False
            spreading = self.Input.ReceivingCurrent() & self.Value
            if spreading and not self.PreviousSpreading:
                self.Output.SpreadCurrent(True)
            elif not spreading and self.PreviousSpreading:
                self.Output.SpreadCurrent(False)
            self.PreviousSpreading = spreading

    # Make a clone of this SFC_Transition
    def Clone(self, parent, id=None, pos=None):
        transition = SFC_Transition(parent, self.Type, self.Condition, self.Priority, id)
        transition.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            transition.SetPosition(pos.x, pos.y)
        else:
            transition.SetPosition(self.Pos.x, self.Pos.y)
        transition.Input = self.Input.Clone(transition)
        transition.Output = self.Output.Clone(transition)
        if self.Type == "connection":
            transition.Condition = self.Condition.Clone(transition)
        return transition

    def GetConnectorTranslation(self, element):
        connectors = {self.Input: element.Input, self.Output: element.Output}
        if self.Type == "connection" and self.Condition is not None:
            connectors[self.Condition] = element.Condition
        return connectors

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if self.Input:
            rect = rect.Union(self.Input.GetRedrawRect(movex, movey))
        if self.Output:
            rect = rect.Union(self.Output.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            if self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
            if self.Output.IsConnected():
                rect = rect.Union(self.Output.GetConnectedRedrawRect(movex, movey))
            if self.Type == "connection" and self.Condition.IsConnected():
                rect = rect.Union(self.Condition.GetConnectedRedrawRect(movex, movey))
        return rect

    # Forbids to change the transition size
    def SetSize(self, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.SetSize(self, width, height)

    # Forbids to resize the transition
    def Resize(self, x, y, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.Resize(self, x, y, width, height)

    # Refresh the size of text for name
    def RefreshConditionSize(self):
        if self.Type != "connection":
            if self.Condition != "":
                self.ConditionSize = self.Parent.GetTextExtent(self.Condition)
            else:
                self.ConditionSize = self.Parent.GetTextExtent("Transition")

    # Refresh the size of text for name
    def RefreshPrioritySize(self):
        if self.Priority != "":
            self.PrioritySize = self.Parent.GetTextExtent(str(self.Priority))
        else:
            self.PrioritySize = None

    # Delete this transition by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteTransition(self)

    # Unconnect input and output
    def Clean(self):
        self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        self.Output.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        if self.Type == "connection":
            self.Condition.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Returns if the point given is in the bounding box
    def HitTest(self, pt, connectors=True):
        if self.Type != "connection":
            # Calculate the bounding box of the condition outside the transition
            text_width, text_height = self.ConditionSize
            text_bbx = wx.Rect(self.Pos.x + self.Size[0] + 5,
                               self.Pos.y + (self.Size[1] - text_height) // 2,
                               text_width,
                               text_height)
            test_text = text_bbx.InsideXY(pt.x, pt.y)
        else:
            test_text = False
        return test_text or Graphic_Element.HitTest(self, pt, connectors)

    # Refresh the transition bounding box
    def RefreshBoundingBox(self):
        bbx_x, bbx_y, bbx_width, bbx_height = self.Pos.x, self.Pos.y, self.Size[0], self.Size[1]
        if self.Priority != 0:
            bbx_y = self.Pos.y - self.PrioritySize[1] - 2
            bbx_width = max(self.Size[0], self.PrioritySize[0])
            bbx_height = self.Size[1] + self.PrioritySize[1] + 2
        if self.Type == "connection":
            bbx_x = self.Pos.x - CONNECTOR_SIZE
            bbx_width = bbx_width + CONNECTOR_SIZE
        else:
            text_width, text_height = self.ConditionSize
            # Calculate the bounding box size
            bbx_width = max(bbx_width, self.Size[0] + 5 + text_width)
            bbx_y = min(bbx_y, self.Pos.y - max(0, (text_height - self.Size[1]) // 2))
            bbx_height = max(bbx_height, self.Pos.y - bbx_y + (self.Size[1] + text_height) // 2)
        self.BoundingBox = wx.Rect(bbx_x, bbx_y, bbx_width + 1, bbx_height + 1)

    # Returns the connector connected to input
    def GetPreviousConnector(self):
        wires = self.Input.GetWires()
        if len(wires) == 1:
            return wires[0][0].GetOtherConnected(self.Input)
        return None

    # Returns the connector connected to output
    def GetNextConnector(self):
        wires = self.Output.GetWires()
        if len(wires) == 1:
            return wires[0][0].GetOtherConnected(self.Output)
        return None

    # Refresh the positions of the transition connectors
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        horizontal_pos = self.Size[0] // 2
        vertical_pos = self.Size[1] // 2
        if scaling is not None:
            horizontal_pos = round((self.Pos.x + horizontal_pos) / scaling[0]) * scaling[0] - self.Pos.x
            vertical_pos = round((self.Pos.y + vertical_pos) / scaling[1]) * scaling[1] - self.Pos.y
        # Update input position
        self.Input.SetPosition(wx.Point(horizontal_pos, 0))
        # Update output position
        self.Output.SetPosition(wx.Point(horizontal_pos, self.Size[1]))
        if self.Type == "connection":
            self.Condition.SetPosition(wx.Point(0, vertical_pos))
        self.RefreshConnected()

    # Refresh the position of the wires connected to transition
    def RefreshConnected(self, exclude=None):
        self.Input.MoveConnected(exclude)
        self.Output.MoveConnected(exclude)
        if self.Type == "connection":
            self.Condition.MoveConnected(exclude)

    # Returns the transition connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test input and output connector
            # if name == self.Input.GetName():
            #    return self.Input
            if name == self.Output.GetName():
                return self.Output
            if self.Type == "connection" and name == self.Condition.GetName():
                return self.Condition
        connectors = [self.Input, self.Output]
        if self.Type == "connection":
            connectors.append(self.Condition)
        return self.FindNearestConnector(position, connectors)

    # Returns the transition condition connector
    def GetConditionConnector(self):
        if self.Type == "connection":
            return self.Condition
        return None

    # Returns input and output transition connectors
    def GetConnectors(self):
        return {"inputs": [self.Input], "outputs": [self.Output]}

    # Test if point given is on transition input or output connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector
        if self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        # Test output connector
        if self.Output.TestPoint(pt, direction, exclude):
            return self.Output
        # Test condition connector
        if self.Type == "connection" and self.Condition.TestPoint(pt, direction, exclude):
            return self.Condition
        return None

    # Changes the transition type
    def SetType(self, type, condition=None):
        if self.Type != type:
            if self.Type == "connection":
                self.Condition.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
            self.Type = type
            if type == "connection":
                self.Condition = Connector(self, "", "BOOL", wx.Point(0, self.Size[1] // 2), WEST)
            else:
                if condition is None:
                    condition = ""
                self.Condition = condition
                self.RefreshConditionSize()
        elif self.Type != "connection":
            if condition is None:
                condition = ""
            self.Condition = condition
            self.RefreshConditionSize()
        self.RefreshBoundingBox()

    # Returns the transition type
    def GetType(self):
        return self.Type

    # Changes the transition priority
    def SetPriority(self, priority):
        self.Priority = priority
        self.RefreshPrioritySize()
        self.RefreshBoundingBox()

    # Returns the transition type
    def GetPriority(self):
        return self.Priority

    # Returns the transition condition
    def GetCondition(self):
        if self.Type != "connection":
            return self.Condition
        return None

    # Returns the transition minimum size
    def GetMinSize(self):
        return SFC_TRANSITION_SIZE

    # Align input element with this step
    def RefreshInputPosition(self):
        current_pos = self.Input.GetPosition(False)
        input = self.GetPreviousConnector()
        if input:
            input_pos = input.GetPosition(False)
            diffx = current_pos.x - input_pos.x
            input_block = input.GetParentBlock()
            if isinstance(input_block, SFC_Divergence):
                input_block.MoveConnector(input, diffx)
            else:
                if isinstance(input_block, SFC_Step):
                    input_block.MoveActionBlock((diffx, 0))
                input_block.Move(diffx, 0)
                input_block.RefreshInputPosition()

    # Align output element with this step
    def RefreshOutputPosition(self, move=None):
        wires = self.Output.GetWires()
        if len(wires) != 1:
            return
        current_pos = self.Output.GetPosition(False)
        output = wires[0][0].GetOtherConnected(self.Output)
        output_pos = output.GetPosition(False)
        diffx = current_pos.x - output_pos.x
        output_block = output.GetParentBlock()
        if move:
            if isinstance(output_block, SFC_Step):
                output_block.MoveActionBlock(move)
            wires[0][0].Move(move[0], move[1], True)
            if not isinstance(output_block, SFC_Divergence) or output_block.GetConnectors()["inputs"].index(output) == 0:
                output_block.Move(move[0], move[1], self.Parent.Wires)
                output_block.RefreshOutputPosition(move)
            else:
                output_block.RefreshPosition()
        elif isinstance(output_block, SFC_Divergence):
            output_block.MoveConnector(output, diffx)
        else:
            if isinstance(output_block, SFC_Step):
                output_block.MoveActionBlock((diffx, 0))
            output_block.Move(diffx, 0)
            output_block.RefreshOutputPosition()

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the transition properties
        self.Parent.EditTransitionContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the menu with special items for a step
        self.Parent.PopupDefaultMenu()

    # Refreshes the transition state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            movex = max(-self.BoundingBox.x, movex)
            if scaling is not None:
                movex = round((self.Pos.x + movex) / scaling[0]) * scaling[0] - self.Pos.x
            self.Move(movex, 0)
            self.RefreshInputPosition()
            self.RefreshOutputPosition()
            return movex, 0
        else:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling, width_fac=2, height_fac=2)

    # Refresh input element model
    def RefreshInputModel(self):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            input = self.GetPreviousConnector()
            if input:
                input_block = input.GetParentBlock()
                input_block.RefreshModel(False)
                if not isinstance(input_block, SFC_Divergence):
                    input_block.RefreshInputModel()

    # Refresh output element model
    def RefreshOutputModel(self, move=False):
        output = self.GetNextConnector()
        if output:
            output_block = output.GetParentBlock()
            output_block.RefreshModel(False)
            if not isinstance(output_block, SFC_Divergence) or move:
                output_block.RefreshOutputModel(move)

    # Refreshes the transition model
    def RefreshModel(self, move=True):
        self.Parent.RefreshTransitionModel(self)
        # If transition has moved, refresh the model of wires connected to output
        if move:
            if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
                self.RefreshInputModel()
                self.RefreshOutputModel()
            else:
                self.Output.RefreshWires()

    # Adds an highlight to the block
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] in ["reference", "inline", "priority"] and start[0] == 0 and end[0] == 0:
            highlights = self.Highlights.setdefault(infos[0], [])
            AddHighlight(highlights, (start, end, highlight_type))

    # Removes an highlight from the block
    def RemoveHighlight(self, infos, start, end, highlight_type):
        if infos[0] in ["reference", "inline", "priority"]:
            highlights = self.Highlights.get(infos[0], [])
            if RemoveHighlight(highlights, (start, end, highlight_type)) and len(highlights) == 0:
                self.Highlights.pop(infos[0])

    # Removes all the highlights of one particular type from the block
    def ClearHighlight(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = {}
        else:
            highlight_items = self.Highlights.items()
            for name, highlights in highlight_items:
                highlights = ClearHighlights(highlights, highlight_type)
                if len(highlights) == 0:
                    self.Highlights.pop(name)

    # Draws transition
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value:
            if self.Forced:
                dc.SetPen(MiterPen(wx.CYAN))
                dc.SetBrush(wx.CYAN_BRUSH)
            else:
                dc.SetPen(MiterPen(wx.GREEN))
                dc.SetBrush(wx.GREEN_BRUSH)
        elif self.Forced:
            dc.SetPen(MiterPen(wx.BLUE))
            dc.SetBrush(wx.BLUE_BRUSH)
        else:
            dc.SetPen(MiterPen(wx.BLACK))
            dc.SetBrush(wx.BLACK_BRUSH)

        if getattr(dc, "printing", False):
            if self.Type != "connection":
                condition_size = dc.GetTextExtent(self.Condition)
            if self.Priority != 0:
                priority_size = dc.GetTextExtent(str(self.Priority))
        else:
            if self.Type != "connection":
                condition_size = self.ConditionSize
            if self.Priority != 0:
                priority_size = self.PrioritySize

        # Draw plain rectangle for representing the transition
        dc.DrawRectangle(self.Pos.x,
                         self.Pos.y + (self.Size[1] - SFC_TRANSITION_SIZE[1]) // 2,
                         self.Size[0] + 1,
                         SFC_TRANSITION_SIZE[1] + 1)
        vertical_line_x = self.Input.GetPosition()[0]
        dc.DrawLine(vertical_line_x, self.Pos.y, vertical_line_x, self.Pos.y + self.Size[1] + 1)
        # Draw transition condition
        if self.Type != "connection":
            if self.Condition != "":
                condition = self.Condition
            else:
                condition = "Transition"
            condition_pos = (self.Pos.x + self.Size[0] + 5,
                             self.Pos.y + (self.Size[1] - condition_size[1]) // 2)
            dc.DrawText(condition, condition_pos[0], condition_pos[1])
        # Draw priority number
        if self.Priority != 0:
            priority_pos = (self.Pos.x, self.Pos.y - priority_size[1] - 2)
            dc.DrawText(str(self.Priority), priority_pos[0], priority_pos[1])
        # Draw input and output connectors
        self.Input.Draw(dc)
        self.Output.Draw(dc)
        if self.Type == "connection":
            self.Condition.Draw(dc)

        if not getattr(dc, "printing", False):
            for name, highlights in self.Highlights.iteritems():
                if name == "priority":
                    DrawHighlightedText(dc, str(self.Priority), highlights, priority_pos[0], priority_pos[1])
                else:
                    DrawHighlightedText(dc, condition, highlights, condition_pos[0], condition_pos[1])


# -------------------------------------------------------------------------------
#                Sequencial Function Chart Divergence and Convergence
# -------------------------------------------------------------------------------


class SFC_Divergence(Graphic_Element):
    """
    Class that implements the graphic representation of a divergence or convergence,
    selection or simultaneous
    """

    # Create a new divergence
    def __init__(self, parent, type, number=2, id=None):
        Graphic_Element.__init__(self, parent)
        self.Type = type
        self.Id = id
        self.RealConnectors = None
        number = max(2, number)
        self.Size = wx.Size((number - 1) * SFC_DEFAULT_SEQUENCE_INTERVAL, self.GetMinSize()[1])
        # Create an input and output connector
        if self.Type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
            self.Inputs = [Connector(self, "", None, wx.Point(self.Size[0] // 2, 0), NORTH, onlyone=True)]
            self.Outputs = []
            for i in xrange(number):
                self.Outputs.append(Connector(self, "", None, wx.Point(i * SFC_DEFAULT_SEQUENCE_INTERVAL, self.Size[1]), SOUTH, onlyone=True))
        elif self.Type in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            self.Inputs = []
            for i in xrange(number):
                self.Inputs.append(Connector(self, "", None, wx.Point(i * SFC_DEFAULT_SEQUENCE_INTERVAL, 0), NORTH, onlyone=True))
            self.Outputs = [Connector(self, "", None, wx.Point(self.Size[0] // 2, self.Size[1]), SOUTH, onlyone=True)]
        self.Value = None
        self.PreviousValue = None

    def Flush(self):
        for input in self.Inputs:
            input.Flush()
        self.Inputs = []
        for output in self.Outputs:
            output.Flush()
        self.Outputs = []

    def SpreadCurrent(self):
        if self.Parent.Debug:
            self.PreviousValue = self.Value
            if self.Type == SELECTION_CONVERGENCE:
                self.Value = False
                for input in self.Inputs:
                    self.Value |= input.ReceivingCurrent()
            elif self.Type == SIMULTANEOUS_CONVERGENCE:
                self.Value = True
                for input in self.Inputs:
                    self.Value &= input.ReceivingCurrent()
            elif self.Type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
                self.Value = self.Inputs[0].ReceivingCurrent()
            else:
                self.Value = False
            if self.Value and not self.PreviousValue:
                if self.Visible:
                    self.Parent.ElementNeedRefresh(self)
                for output in self.Outputs:
                    output.SpreadCurrent(True)
            elif not self.Value and self.PreviousValue:
                if self.Visible:
                    self.Parent.ElementNeedRefresh(self)
                for output in self.Outputs:
                    output.SpreadCurrent(False)

    # Make a clone of this SFC_Divergence
    def Clone(self, parent, id=None, pos=None):
        divergence = SFC_Divergence(parent, self.Type, max(len(self.Inputs), len(self.Outputs)), id)
        divergence.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            divergence.SetPosition(pos.x, pos.y)
        else:
            divergence.SetPosition(self.Pos.x, self.Pos.y)
        divergence.Inputs = [input.Clone(divergence) for input in self.Inputs]
        divergence.Outputs = [output.Clone(divergence) for output in self.Outputs]
        return divergence

    def GetConnectorTranslation(self, element):
        return dict(zip(self.Inputs + self.Outputs, element.Inputs + element.Outputs))

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if movex != 0 or movey != 0:
            for input in self.Inputs:
                if input.IsConnected():
                    rect = rect.Union(input.GetConnectedRedrawRect(movex, movey))
            for output in self.Outputs:
                if output.IsConnected():
                    rect = rect.Union(output.GetConnectedRedrawRect(movex, movey))
        return rect

    # Forbids to resize the divergence
    def Resize(self, x, y, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.Resize(self, x, 0, width, self.GetMinSize()[1])

    # Delete this divergence by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteDivergence(self)

    # Returns the divergence type
    def GetType(self):
        return self.Type

    # Unconnect input and output
    def Clean(self):
        for input in self.Inputs:
            input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        for output in self.Outputs:
            output.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Add a branch to the divergence
    def AddBranch(self):
        if self.Type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
            maxx = 0
            for output in self.Outputs:
                pos = output.GetRelPosition()
                maxx = max(maxx, pos.x)
            connector = Connector(self, "", None, wx.Point(maxx + SFC_DEFAULT_SEQUENCE_INTERVAL, self.Size[1]), SOUTH, onlyone=True)
            self.Outputs.append(connector)
            self.MoveConnector(connector, 0)
        elif self.Type in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            maxx = 0
            for input in self.Inputs:
                pos = input.GetRelPosition()
                maxx = max(maxx, pos.x)
            connector = Connector(self, "", None, wx.Point(maxx + SFC_DEFAULT_SEQUENCE_INTERVAL, 0), NORTH, onlyone=True)
            self.Inputs.append(connector)
            self.MoveConnector(connector, SFC_DEFAULT_SEQUENCE_INTERVAL)

    # Remove a branch from the divergence
    def RemoveBranch(self, connector):
        if self.Type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
            if connector in self.Outputs and len(self.Outputs) > 2:
                self.Outputs.remove(connector)
                self.MoveConnector(self.Outputs[0], 0)
        elif self.Type in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            if connector in self.Inputs and len(self.Inputs) > 2:
                self.Inputs.remove(connector)
                self.MoveConnector(self.Inputs[0], 0)

    # Remove the handled branch from the divergence
    def RemoveHandledBranch(self):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_CONNECTOR:
            handle.UnConnect(delete=True)
            self.RemoveBranch(handle)

    # Return the number of branches for the divergence
    def GetBranchNumber(self):
        if self.Type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
            return len(self.Outputs)
        elif self.Type in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            return len(self.Inputs)

    # Returns if the point given is in the bounding box
    def HitTest(self, pt, connectors=True):
        return self.BoundingBox.InsideXY(pt.x, pt.y) or self.TestConnector(pt, exclude=False) is not None

    # Refresh the divergence bounding box
    def RefreshBoundingBox(self):
        if self.Type in [SELECTION_DIVERGENCE, SELECTION_CONVERGENCE]:
            self.BoundingBox = wx.Rect(self.Pos.x,       self.Pos.y,
                                       self.Size[0] + 1, self.Size[1] + 1)
        elif self.Type in [SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            self.BoundingBox = wx.Rect(
                self.Pos.x - SFC_SIMULTANEOUS_SEQUENCE_EXTRA,           self.Pos.y,
                self.Size[0] + 2 * SFC_SIMULTANEOUS_SEQUENCE_EXTRA + 1, self.Size[1] + 1)

    # Refresh the position of wires connected to divergence
    def RefreshConnected(self, exclude=None):
        for input in self.Inputs:
            input.MoveConnected(exclude)
        for output in self.Outputs:
            output.MoveConnected(exclude)

    # Moves the divergence connector given
    def MoveConnector(self, connector, movex):
        position = connector.GetRelPosition()
        connector.SetPosition(wx.Point(position.x + movex, position.y))
        minx = self.Size[0]
        maxx = 0
        for input in self.Inputs:
            input_pos = input.GetRelPosition()
            minx = min(minx, input_pos.x)
            maxx = max(maxx, input_pos.x)
        for output in self.Outputs:
            output_pos = output.GetRelPosition()
            minx = min(minx, output_pos.x)
            maxx = max(maxx, output_pos.x)
        if minx != 0:
            for input in self.Inputs:
                input_pos = input.GetRelPosition()
                input.SetPosition(wx.Point(input_pos.x - minx, input_pos.y))
            for output in self.Outputs:
                output_pos = output.GetRelPosition()
                output.SetPosition(wx.Point(output_pos.x - minx, output_pos.y))
        self.Inputs.sort(lambda x, y: cmp(x.Pos.x, y.Pos.x))
        self.Outputs.sort(lambda x, y: cmp(x.Pos.x, y.Pos.x))
        self.Pos.x += minx
        self.Size[0] = maxx - minx
        connector.MoveConnected()
        self.RefreshBoundingBox()

    # Returns the divergence connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test each input and output connector
            # for input in self.Inputs:
            #    if name == input.GetName():
            #        return input
            for output in self.Outputs:
                if name == output.GetName():
                    return output
        return self.FindNearestConnector(position, self.Inputs + self.Outputs)

    # Returns input and output divergence connectors
    def GetConnectors(self):
        return {"inputs": self.Inputs, "outputs": self.Outputs}

    # Test if point given is on divergence input or output connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector
        for input in self.Inputs:
            if input.TestPoint(pt, direction, exclude):
                return input
        # Test output connector
        for output in self.Outputs:
            if output.TestPoint(pt, direction, exclude):
                return output
        return None

    # Changes the divergence size
    def SetSize(self, width, height):
        height = self.GetMinSize()[1]
        for i, input in enumerate(self.Inputs):
            position = input.GetRelPosition()
            if self.RealConnectors:
                input.SetPosition(wx.Point(int(round(self.RealConnectors["Inputs"][i] * width)), 0))
            else:
                input.SetPosition(wx.Point(int(round(position.x*width / self.Size[0])), 0))
            input.MoveConnected()
        for i, output in enumerate(self.Outputs):
            position = output.GetRelPosition()
            if self.RealConnectors:
                output.SetPosition(wx.Point(int(round(self.RealConnectors["Outputs"][i] * width)), height))
            else:
                output.SetPosition(wx.Point(int(round(position.x*width / self.Size[0])), height))
            output.MoveConnected()
        self.Size = wx.Size(width, height)
        self.RefreshBoundingBox()

    # Returns the divergence minimum size
    def GetMinSize(self, default=False):
        width = 0
        if default:
            if self.Type in [SELECTION_DIVERGENCE, SIMULTANEOUS_DIVERGENCE]:
                width = (len(self.Outputs) - 1) * SFC_DEFAULT_SEQUENCE_INTERVAL
            elif self.Type in [SELECTION_CONVERGENCE, SIMULTANEOUS_CONVERGENCE]:
                width = (len(self.Inputs) - 1) * SFC_DEFAULT_SEQUENCE_INTERVAL
        if self.Type in [SELECTION_DIVERGENCE, SELECTION_CONVERGENCE]:
            return width, 1
        elif self.Type in [SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            return width, 3
        return 0, 0

    # Refresh the position of the block connected to connector
    def RefreshConnectedPosition(self, connector):
        wires = connector.GetWires()
        if len(wires) != 1:
            return
        current_pos = connector.GetPosition(False)
        next = wires[0][0].GetOtherConnected(connector)
        next_pos = next.GetPosition(False)
        diffx = current_pos.x - next_pos.x
        next_block = next.GetParentBlock()
        if isinstance(next_block, SFC_Divergence):
            next_block.MoveConnector(next, diffx)
        else:
            next_block.Move(diffx, 0)
            if connector in self.Inputs:
                next_block.RefreshInputPosition()
            else:
                next_block.RefreshOutputPosition()

    # Refresh the position of this divergence
    def RefreshPosition(self):
        y = 0
        for input in self.Inputs:
            wires = input.GetWires()
            if len(wires) != 1:
                return
            previous = wires[0][0].GetOtherConnected(input)
            previous_pos = previous.GetPosition(False)
            y = max(y, previous_pos.y + GetWireSize(previous.GetParentBlock()))
        diffy = y - self.Pos.y
        if diffy != 0:
            self.Move(0, diffy, self.Parent.Wires)
            self.RefreshOutputPosition((0, diffy))
        for input in self.Inputs:
            input.MoveConnected()

    # Align output element with this divergence
    def RefreshOutputPosition(self, move=None):
        if move:
            for output_connector in self.Outputs:
                wires = output_connector.GetWires()
                if len(wires) != 1:
                    return
                output = wires[0][0].GetOtherConnected(self.Output)
                output_block = output.GetParentBlock()
                if isinstance(output_block, SFC_Step):
                    output_block.MoveActionBlock(move)
                wires[0][0].Move(move[0], move[1], True)
                if not isinstance(output_block, SFC_Divergence) or output_block.GetConnectors()["inputs"].index(output) == 0:
                    output_block.Move(move[0], move[1], self.Parent.Wires)
                    output_block.RefreshOutputPosition(move)

    # Method called when a LeftDown event have been generated
    def OnLeftDown(self, event, dc, scaling):
        self.RealConnectors = {"Inputs": [], "Outputs": []}
        for input in self.Inputs:
            position = input.GetRelPosition()
            self.RealConnectors["Inputs"].append(position.x / self.Size[0])
        for output in self.Outputs:
            position = output.GetRelPosition()
            self.RealConnectors["Outputs"].append(position.x / self.Size[0])
        Graphic_Element.OnLeftDown(self, event, dc, scaling)

    # Method called when a LeftUp event have been generated
    def OnLeftUp(self, event, dc, scaling):
        Graphic_Element.OnLeftUp(self, event, dc, scaling)
        self.RealConnectors = None

    # Method called when a RightDown event have been generated
    def OnRightDown(self, event, dc, scaling):
        pos = GetScaledEventPosition(event, dc, scaling)
        # Test if a connector have been handled
        connector = self.TestConnector(pos, exclude=False)
        if connector:
            self.Handle = (HANDLE_CONNECTOR, connector)
            wx.CallAfter(self.Parent.SetCurrentCursor, 1)
            self.Selected = False
            # Initializes the last position
            self.oldPos = GetScaledEventPosition(event, dc, scaling)
        else:
            Graphic_Element.OnRightDown(self, event, dc, scaling)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        pos = GetScaledEventPosition(event, dc, scaling)
        handle_type, handle = self.Handle
        if handle_type == HANDLE_CONNECTOR and self.Dragging and self.oldPos:
            wires = handle.GetWires()
            if len(wires) == 1:
                block = wires[0][0].GetOtherConnected(handle).GetParentBlock()
                block.RefreshModel(False)
                if not isinstance(block, SFC_Divergence):
                    if handle in self.Inputs:
                        block.RefreshInputModel()
                    else:
                        block.RefreshOutputModel()
            Graphic_Element.OnRightUp(self, event, dc, scaling)
        else:
            # Popup the menu with special items for a block and a connector if one is handled
            connector = self.TestConnector(pos, exclude=False)
            if connector:
                self.Handle = (HANDLE_CONNECTOR, connector)
                self.Parent.PopupDivergenceMenu(True)
            else:
                # Popup the divergence menu without delete branch
                self.Parent.PopupDivergenceMenu(False)

    # Refreshes the divergence state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        handle_type, handle = self.Handle
        # A connector has been handled
        if handle_type == HANDLE_CONNECTOR:
            movex = max(-self.BoundingBox.x, movex)
            if scaling is not None:
                movex = round((self.Pos.x + movex) / scaling[0]) * scaling[0] - self.Pos.x
            self.MoveConnector(handle, movex)
            if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
                self.RefreshConnectedPosition(handle)
            return movex, 0
        elif self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)
        return 0, 0

    # Refresh output element model
    def RefreshOutputModel(self, move=False):
        if move and self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            for output in self.Outputs:
                wires = output.GetWires()
                if len(wires) != 1:
                    return
                output_block = wires[0][0].GetOtherConnected(output).GetParentBlock()
                output_block.RefreshModel(False)
                if not isinstance(output_block, SFC_Divergence) or move:
                    output_block.RefreshOutputModel(move)

    # Refreshes the divergence model
    def RefreshModel(self, move=True):
        self.Parent.RefreshDivergenceModel(self)
        # If divergence has moved, refresh the model of wires connected to outputs
        if move:
            if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
                self.RefreshOutputModel()
            else:
                for output in self.Outputs:
                    output.RefreshWires()

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        dc.SetPen(MiterPen(HIGHLIGHTCOLOR))
        dc.SetBrush(wx.Brush(HIGHLIGHTCOLOR))
        dc.SetLogicalFunction(wx.AND)
        # Draw two rectangles for representing the contact
        posx = self.Pos.x
        width = self.Size[0]
        if self.Type in [SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            posx -= SFC_SIMULTANEOUS_SEQUENCE_EXTRA
            width += SFC_SIMULTANEOUS_SEQUENCE_EXTRA * 2
        dc.DrawRectangle(int(round((posx - 1) * scalex)) - 2,
                         int(round((self.Pos.y - 1) * scaley)) - 2,
                         int(round((width + 3) * scalex)) + 5,
                         int(round((self.Size.height + 3) * scaley)) + 5)
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Draws divergence
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value:
            dc.SetPen(MiterPen(wx.GREEN))
            dc.SetBrush(wx.GREEN_BRUSH)
        else:
            dc.SetPen(MiterPen(wx.BLACK))
            dc.SetBrush(wx.BLACK_BRUSH)
        # Draw plain rectangle for representing the divergence
        if self.Type in [SELECTION_DIVERGENCE, SELECTION_CONVERGENCE]:
            dc.DrawRectangle(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)
        elif self.Type in [SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE]:
            dc.DrawLine(self.Pos.x - SFC_SIMULTANEOUS_SEQUENCE_EXTRA, self.Pos.y,
                        self.Pos.x + self.Size[0] + SFC_SIMULTANEOUS_SEQUENCE_EXTRA + 1, self.Pos.y)
            dc.DrawLine(self.Pos.x - SFC_SIMULTANEOUS_SEQUENCE_EXTRA, self.Pos.y + self.Size[1],
                        self.Pos.x + self.Size[0] + SFC_SIMULTANEOUS_SEQUENCE_EXTRA + 1, self.Pos.y + self.Size[1])
        # Draw inputs and outputs connectors
        for input in self.Inputs:
            input.Draw(dc)
        for output in self.Outputs:
            output.Draw(dc)


# -------------------------------------------------------------------------------
#                   Sequencial Function Chart Jump to Step
# -------------------------------------------------------------------------------


class SFC_Jump(Graphic_Element):
    """
    Class that implements the graphic representation of a jump to step
    """

    # Create a new jump
    def __init__(self, parent, target, id=None):
        Graphic_Element.__init__(self, parent)
        self.SetTarget(target)
        self.Id = id
        self.Size = wx.Size(SFC_JUMP_SIZE[0], SFC_JUMP_SIZE[1])
        self.Highlights = []
        # Create an input and output connector
        self.Input = Connector(self, "", None, wx.Point(self.Size[0] // 2, 0), NORTH, onlyone=True)
        self.Value = None
        self.PreviousValue = None

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None

    def SpreadCurrent(self):
        if self.Parent.Debug:
            self.PreviousValue = self.Value
            self.Value = self.Input.ReceivingCurrent()
            if self.Value != self.PreviousValue and self.Visible:
                self.Parent.ElementNeedRefresh(self)

    # Make a clone of this SFC_Jump
    def Clone(self, parent, id=None, pos=None):
        jump = SFC_Jump(parent, self.Target, id)
        jump.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            jump.SetPosition(pos.x, pos.y)
        else:
            jump.SetPosition(self.Pos.x, self.Pos.y)
        jump.Input = self.Input.Clone(jump)
        return jump

    def GetConnectorTranslation(self, element):
        return {self.Input: element.Input}

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if self.Input:
            rect = rect.Union(self.Input.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            if self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
        return rect

    # Forbids to change the jump size
    def SetSize(self, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.SetSize(self, width, height)

    # Forbids to resize jump
    def Resize(self, x, y, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.Resize(self, x, y, width, height)

    # Delete this jump by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteJump(self)

    # Unconnect input
    def Clean(self):
        self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Refresh the size of text for target
    def RefreshTargetSize(self):
        self.TargetSize = self.Parent.GetTextExtent(self.Target)

    # Returns if the point given is in the bounding box
    def HitTest(self, pt, connectors=True):
        # Calculate the bounding box of the condition outside the transition
        text_width, text_height = self.TargetSize
        text_bbx = wx.Rect(self.Pos.x + self.Size[0] + 2,
                           self.Pos.y + (self.Size[1] - text_height) // 2,
                           text_width,
                           text_height)
        return text_bbx.InsideXY(pt.x, pt.y) or Graphic_Element.HitTest(self, pt, connectors)

    # Refresh the jump bounding box
    def RefreshBoundingBox(self):
        text_width, _text_height = self.Parent.GetTextExtent(self.Target)
        # Calculate the bounding box size
        bbx_width = self.Size[0] + 2 + text_width
        self.BoundingBox = wx.Rect(self.Pos.x,    self.Pos.y - CONNECTOR_SIZE,
                                   bbx_width + 1, self.Size[1] + CONNECTOR_SIZE + 1)

    # Returns the connector connected to input
    def GetPreviousConnector(self):
        wires = self.Input.GetWires()
        if len(wires) == 1:
            return wires[0][0].GetOtherConnected(self.Input)
        return None

    # Refresh the element connectors position
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        horizontal_pos = self.Size[0] // 2
        if scaling is not None:
            horizontal_pos = round((self.Pos.x + horizontal_pos) / scaling[0]) * scaling[0] - self.Pos.x
        self.Input.SetPosition(wx.Point(horizontal_pos, 0))
        self.RefreshConnected()

    # Refresh the position of wires connected to jump
    def RefreshConnected(self, exclude=None):
        if self.Input:
            self.Input.MoveConnected(exclude)

    # Returns input jump connector
    def GetConnector(self, position=None, name=None):
        return self.Input

    # Returns all the jump connectors
    def GetConnectors(self):
        return {"inputs": [self.Input], "outputs": []}

    # Test if point given is on jump input connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector
        if self.Input and self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        return None

    # Changes the jump target
    def SetTarget(self, target):
        self.Target = target
        self.RefreshTargetSize()
        self.RefreshBoundingBox()

    # Returns the jump target
    def GetTarget(self):
        return self.Target

    # Returns the jump minimum size
    def GetMinSize(self):
        return SFC_JUMP_SIZE

    # Align input element with this jump
    def RefreshInputPosition(self):
        if self.Input:
            current_pos = self.Input.GetPosition(False)
            input = self.GetPreviousConnector()
            if input:
                input_pos = input.GetPosition(False)
                diffx = current_pos.x - input_pos.x
                input_block = input.GetParentBlock()
                if isinstance(input_block, SFC_Divergence):
                    input_block.MoveConnector(input, diffx)
                else:
                    if isinstance(input_block, SFC_Step):
                        input_block.MoveActionBlock((diffx, 0))
                    input_block.Move(diffx, 0)
                    input_block.RefreshInputPosition()

    # Can't align output element, because there is no output
    def RefreshOutputPosition(self, move=None):
        pass

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the jump properties
        self.Parent.EditJumpContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the default menu
        self.Parent.PopupDefaultMenu()

    # Refreshes the jump state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            movex = max(-self.BoundingBox.x, movex)
            if scaling is not None:
                movex = round((self.Pos.x + movex) / scaling[0]) * scaling[0] - self.Pos.x
            self.Move(movex, 0)
            self.RefreshInputPosition()
            return movex, 0
        else:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling, width_fac=2)

    # Refresh input element model
    def RefreshInputModel(self):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            input = self.GetPreviousConnector()
            if input:
                input_block = input.GetParentBlock()
                input_block.RefreshModel(False)
                if not isinstance(input_block, SFC_Divergence):
                    input_block.RefreshInputModel()

    # Refresh output element model
    def RefreshOutputModel(self, move=False):
        pass

    # Refreshes the jump model
    def RefreshModel(self, move=True):
        self.Parent.RefreshJumpModel(self)
        if move:
            if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
                self.RefreshInputModel()

    # Adds an highlight to the variable
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "target" and start[0] == 0 and end[0] == 0:
            AddHighlight(self.Highlights, (start, end, highlight_type))

    # Removes an highlight from the variable
    def RemoveHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "target":
            RemoveHighlight(self.Highlights, (start, end, highlight_type))

    # Removes all the highlights of one particular type from the variable
    def ClearHighlight(self, highlight_type=None):
        ClearHighlights(self.Highlights, highlight_type)

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        dc.SetPen(MiterPen(HIGHLIGHTCOLOR))
        dc.SetBrush(wx.Brush(HIGHLIGHTCOLOR))
        dc.SetLogicalFunction(wx.AND)
        points = [wx.Point(int(round((self.Pos.x - 2) * scalex)) - 3,
                           int(round((self.Pos.y - 2) * scaley)) - 2),
                  wx.Point(int(round((self.Pos.x + self.Size[0] + 2) * scalex)) + 4,
                           int(round((self.Pos.y - 2) * scaley)) - 2),
                  wx.Point(int(round((self.Pos.x + self.Size[0] / 2) * scalex)),
                           int(round((self.Pos.y + self.Size[1] + 3) * scaley)) + 4)]
        dc.DrawPolygon(points)
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Draws divergence
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value:
            dc.SetPen(MiterPen(wx.GREEN))
            dc.SetBrush(wx.GREEN_BRUSH)
        else:
            dc.SetPen(MiterPen(wx.BLACK))
            dc.SetBrush(wx.BLACK_BRUSH)

        if getattr(dc, "printing", False):
            target_size = dc.GetTextExtent(self.Target)
        else:
            target_size = self.TargetSize

        # Draw plain rectangle for representing the divergence
        dc.DrawLine(self.Pos.x + self.Size[0] // 2, self.Pos.y, self.Pos.x + self.Size[0] // 2, self.Pos.y + self.Size[1])
        points = [wx.Point(self.Pos.x, self.Pos.y),
                  wx.Point(self.Pos.x + self.Size[0] // 2, self.Pos.y + self.Size[1] // 3),
                  wx.Point(self.Pos.x + self.Size[0], self.Pos.y),
                  wx.Point(self.Pos.x + self.Size[0] // 2, self.Pos.y + self.Size[1])]
        dc.DrawPolygon(points)
        target_pos = (self.Pos.x + self.Size[0] + 2,
                      self.Pos.y + (self.Size[1] - target_size[1]) // 2)
        dc.DrawText(self.Target, target_pos[0], target_pos[1])
        # Draw input connector
        if self.Input:
            self.Input.Draw(dc)

        if not getattr(dc, "printing", False):
            DrawHighlightedText(dc, self.Target, self.Highlights, target_pos[0], target_pos[1])


# -------------------------------------------------------------------------------
#                   Sequencial Function Chart Action Block
# -------------------------------------------------------------------------------


class SFC_ActionBlock(Graphic_Element):
    """
    Class that implements the graphic representation of an action block
    """

    # Create a new action block
    def __init__(self, parent, actions=None, id=None):
        Graphic_Element.__init__(self, parent)
        self.Id = id
        self.Size = wx.Size(SFC_ACTION_MIN_SIZE[0], SFC_ACTION_MIN_SIZE[1])
        self.MinSize = wx.Size(SFC_ACTION_MIN_SIZE[0], SFC_ACTION_MIN_SIZE[1])
        self.Highlights = {}
        # Create an input and output connector
        self.Input = Connector(self, "", None, wx.Point(0, SFC_ACTION_MIN_SIZE[1] // 2), WEST, onlyone=True)
        self.SetActions(actions)
        self.Value = None
        self.PreviousValue = None

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None

    def SpreadCurrent(self):
        if self.Parent.Debug:
            self.PreviousValue = self.Value
            self.Value = self.Input.ReceivingCurrent()
            if self.Value != self.PreviousValue and self.Visible:
                self.Parent.ElementNeedRefresh(self)

    # Make a clone of this SFC_ActionBlock
    def Clone(self, parent, id=None, pos=None):
        actions = [action.copy() for action in self.Actions]
        action_block = SFC_ActionBlock(parent, actions, id)
        action_block.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            action_block.SetPosition(pos.x, pos.y)
        else:
            action_block.SetPosition(self.Pos.x, self.Pos.y)
        action_block.Input = self.Input.Clone(action_block)
        return action_block

    def GetConnectorTranslation(self, element):
        return {self.Input: element.Input}

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if self.Input:
            rect = rect.Union(self.Input.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            if self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
        return rect

    # Returns the number of action lines
    def GetLineNumber(self):
        return len(self.Actions)

    def GetLineSize(self):
        if len(self.Actions) > 0:
            return self.Size[1] // len(self.Actions)
        else:
            return SFC_ACTION_MIN_SIZE[1]

    # Forbids to resize the action block
    def Resize(self, x, y, width, height):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            if x == 0:
                self.SetSize(width, self.Size[1])
        else:
            Graphic_Element.Resize(self, x, y, width, height)

    # Delete this action block by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteActionBlock(self)

    # Unconnect input and output
    def Clean(self):
        self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Refresh the action block bounding box
    def RefreshBoundingBox(self):
        self.BoundingBox = wx.Rect(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)

    # Refresh the position of wires connected to action block
    def RefreshConnected(self, exclude=None):
        self.Input.MoveConnected(exclude)

    # Returns input action block connector
    def GetConnector(self, position=None, name=None):
        return self.Input

    # Returns all the action block connectors
    def GetConnectors(self):
        return {"inputs": [self.Input], "outputs": []}

    # Test if point given is on action block input connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector
        if self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        return None

    # Refresh the element connectors position
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        vertical_pos = SFC_ACTION_MIN_SIZE[1] // 2
        if scaling is not None:
            vertical_pos = round((self.Pos.y + vertical_pos) / scaling[1]) * scaling[1] - self.Pos.y
        self.Input.SetPosition(wx.Point(0, vertical_pos))
        self.RefreshConnected()

    # Changes the action block actions
    def SetActions(self, actions=None):
        actions = [] if actions is None else actions
        self.Actions = actions
        self.ColSize = [0, 0, 0]
        min_height = 0
        for action in self.Actions:
            width, height = self.Parent.GetTextExtent(
                action.qualifier if action.qualifier != "" else "N")
            self.ColSize[0] = max(self.ColSize[0], width + 10)
            row_height = height
            if action.duration != "":
                width, height = self.Parent.GetTextExtent(action.duration)
                row_height = max(row_height, height)
                self.ColSize[0] = max(self.ColSize[0], width + 10)
            width, height = self.Parent.GetTextExtent(action.value)
            row_height = max(row_height, height)
            self.ColSize[1] = max(self.ColSize[1], width + 10)
            if action.indicator != "":
                width, height = self.Parent.GetTextExtent(action.indicator)
                row_height = max(row_height, height)
                self.ColSize[2] = max(self.ColSize[2], width + 10)
            min_height += row_height + 5
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            self.Size = wx.Size(self.ColSize[0] + self.ColSize[1] + self.ColSize[2], max(min_height, SFC_ACTION_MIN_SIZE[1], self.Size[1]))
            self.MinSize = max(self.ColSize[0] + self.ColSize[1] + self.ColSize[2],
                               SFC_ACTION_MIN_SIZE[0]), max(SFC_ACTION_MIN_SIZE[1], min_height)
            self.RefreshBoundingBox()
        else:
            self.Size = wx.Size(max(self.ColSize[0] + self.ColSize[1] + self.ColSize[2],
                                    SFC_ACTION_MIN_SIZE[0]),
                                len(self.Actions) * SFC_ACTION_MIN_SIZE[1])
            self.MinSize = max(self.ColSize[0] + self.ColSize[1] + self.ColSize[2],
                               SFC_ACTION_MIN_SIZE[0]), len(self.Actions) * SFC_ACTION_MIN_SIZE[1]
            self.RefreshBoundingBox()
            if self.Input is not None:
                wires = self.Input.GetWires()
                if len(wires) == 1:
                    input_block = wires[0][0].GetOtherConnected(self.Input).GetParentBlock()
                    input_block.RefreshOutputPosition()
                    input_block.RefreshOutputModel(True)

    # Returns the action block actions
    def GetActions(self):
        return self.Actions

    # Returns the action block minimum size
    def GetMinSize(self):
        return self.MinSize

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the action block properties
        self.Parent.EditActionBlockContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the default menu
        self.Parent.PopupDefaultMenu()

    # Refreshes the action block state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            handle_type, _handle = self.Handle
            if handle_type == HANDLE_MOVE:
                movex = max(-self.BoundingBox.x, movex)
                if scaling is not None:
                    movex = round((self.Pos.x + movex) / scaling[0]) * scaling[0] - self.Pos.x
                wires = self.Input.GetWires()
                if len(wires) == 1:
                    input_pos = wires[0][0].GetOtherConnected(self.Input).GetPosition(False)
                    if self.Pos.x - input_pos.x + movex >= SFC_WIRE_MIN_SIZE:
                        self.Move(movex, 0)
                        return movex, 0
                return 0, 0
            else:
                return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)
        else:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)

    # Refreshes the action block model
    def RefreshModel(self, move=True):
        self.Parent.RefreshActionBlockModel(self)

    # Adds an highlight to the variable
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "action" and infos[1] < len(self.Actions):
            action_highlights = self.Highlights.setdefault(infos[1], {})
            attribute_highlights = action_highlights.setdefault(infos[2], [])
            AddHighlight(attribute_highlights, (start, end, highlight_type))

    # Removes an highlight from the block
    def RemoveHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "action" and infos[1] < len(self.Actions):
            action_highlights = self.Highlights.get(infos[1], {})
            attribute_highlights = action_highlights.setdefault(infos[2], [])
            if RemoveHighlight(attribute_highlights, (start, end, highlight_type)) and len(attribute_highlights) == 0:
                action_highlights.pop(infos[2])
                if len(action_highlights) == 0:
                    self.Highlights.pop(infos[1])

    # Removes all the highlights of one particular type from the block
    def ClearHighlight(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = {}
        else:
            highlight_items = self.Highlights.items()
            for number, action_highlights in highlight_items:
                action_highlight_items = action_highlights.items()
                for name, attribute_highlights in action_highlight_items:
                    attribute_highlights = ClearHighlights(attribute_highlights, highlight_type)
                    if len(attribute_highlights) == 0:
                        action_highlights.pop(name)
                if len(action_highlights) == 0:
                    self.Highlights.pop(number)

    # Draws divergence
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value:
            dc.SetPen(MiterPen(wx.GREEN))
        else:
            dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.WHITE_BRUSH)
        colsize = [self.ColSize[0], self.Size[0] - self.ColSize[0] - self.ColSize[2], self.ColSize[2]]
        # Draw plain rectangle for representing the action block
        dc.DrawRectangle(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)
        dc.DrawLine(self.Pos.x + colsize[0], self.Pos.y,
                    self.Pos.x + colsize[0], self.Pos.y + self.Size[1])
        dc.DrawLine(self.Pos.x + colsize[0] + colsize[1], self.Pos.y,
                    self.Pos.x + colsize[0] + colsize[1], self.Pos.y + self.Size[1])
        line_size = self.GetLineSize()
        for i, action in enumerate(self.Actions):
            if i != 0:
                dc.DrawLine(self.Pos.x, self.Pos.y + i * line_size,
                            self.Pos.x + self.Size[0], self.Pos.y + i * line_size)
            qualifier_size = dc.GetTextExtent(action.qualifier)
            if action.duration != "":
                qualifier_pos = (self.Pos.x + (colsize[0] - qualifier_size[0]) // 2,
                                 self.Pos.y + i * line_size + line_size // 2 - qualifier_size[1])
                duration_size = dc.GetTextExtent(action.duration)
                duration_pos = (self.Pos.x + (colsize[0] - duration_size[0]) // 2,
                                self.Pos.y + i * line_size + line_size // 2)
                dc.DrawText(action.duration, duration_pos[0], duration_pos[1])
            else:
                qualifier_pos = (self.Pos.x + (colsize[0] - qualifier_size[0]) // 2,
                                 self.Pos.y + i * line_size + (line_size - qualifier_size[1]) // 2)
            dc.DrawText(action.qualifier, qualifier_pos[0], qualifier_pos[1])
            content_size = dc.GetTextExtent(action.value)
            content_pos = (self.Pos.x + colsize[0] + (colsize[1] - content_size[0]) // 2,
                           self.Pos.y + i * line_size + (line_size - content_size[1]) // 2)
            dc.DrawText(action.value, content_pos[0], content_pos[1])
            if action.indicator != "":
                indicator_size = dc.GetTextExtent(action.indicator)
                indicator_pos = (self.Pos.x + colsize[0] + colsize[1] + (colsize[2] - indicator_size[0]) // 2,
                                 self.Pos.y + i * line_size + (line_size - indicator_size[1]) // 2)
                dc.DrawText(action.indicator, indicator_pos[0], indicator_pos[1])

            if not getattr(dc, "printing", False):
                action_highlights = self.Highlights.get(i, {})
                for name, attribute_highlights in action_highlights.iteritems():
                    if name == "qualifier":
                        DrawHighlightedText(dc, action.qualifier, attribute_highlights, qualifier_pos[0], qualifier_pos[1])
                    elif name == "duration":
                        DrawHighlightedText(dc, action.duration, attribute_highlights, duration_pos[0], duration_pos[1])
                    elif name in ["reference", "inline"]:
                        DrawHighlightedText(dc, action.value, attribute_highlights, content_pos[0], content_pos[1])
                    elif name == "indicator":
                        DrawHighlightedText(dc, action.indicator, attribute_highlights, indicator_pos[0], indicator_pos[1])

        # Draw input connector
        self.Input.Draw(dc)
