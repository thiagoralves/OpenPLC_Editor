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
from six.moves import xrange

from graphics.GraphicCommons import *
from plcopen.structures import *


# -------------------------------------------------------------------------------
#                         Function Block Diagram Block
# -------------------------------------------------------------------------------


def TestConnectorName(name, block_type):
    return name in ["OUT", "MN", "MX"] or name.startswith("IN") and (block_type, name) != ("EXPT", "IN2")


class FBD_Block(Graphic_Element):
    """
    Class that implements the graphic representation of a function block
    """

    # Create a new block
    def __init__(self, parent, type, name, id=None, extension=0, inputs=None, connectors=None, executionControl=False, executionOrder=0):
        Graphic_Element.__init__(self, parent)
        self.Type = None
        self.Description = None
        self.Extension = None
        self.ExecutionControl = False
        self.Id = id
        self.SetName(name)
        self.SetExecutionOrder(executionOrder)
        self.Inputs = []
        self.Outputs = []
        self.Colour = wx.BLACK
        self.Pen = MiterPen(wx.BLACK)
        self.SetType(type, extension, inputs, connectors, executionControl)
        self.Highlights = {}

    # Make a clone of this FBD_Block
    def Clone(self, parent, id=None, name="", pos=None):
        if self.Name != "" and name == "":
            name = self.Name
        block = FBD_Block(parent, self.Type, name, id, self.Extension)
        block.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            block.SetPosition(pos.x, pos.y)
        else:
            block.SetPosition(self.Pos.x, self.Pos.y)
        block.Inputs = [input.Clone(block) for input in self.Inputs]
        block.Outputs = [output.Clone(block) for output in self.Outputs]
        return block

    def GetConnectorTranslation(self, element):
        return dict(zip(self.Inputs + self.Outputs, element.Inputs + element.Outputs))

    def Flush(self):
        for input in self.Inputs:
            input.Flush()
        self.Inputs = []
        for output in self.Outputs:
            output.Flush()
        self.Outputs = []

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

    # Delete this block by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteBlock(self)

    # Unconnect all inputs and outputs
    def Clean(self):
        for input in self.Inputs:
            input.UnConnect(delete=True)
        for output in self.Outputs:
            output.UnConnect(delete=True)

    # Refresh the size of text for name
    def RefreshNameSize(self):
        self.NameSize = self.Parent.GetTextExtent(self.Name)

    # Refresh the size of text for execution order
    def RefreshExecutionOrderSize(self):
        self.ExecutionOrderSize = self.Parent.GetTextExtent(str(self.ExecutionOrder))

    # Returns if the point given is in the bounding box
    def HitTest(self, pt, connectors=True):
        if self.Name != "":
            test_text = self.GetTextBoundingBox().InsideXY(pt.x, pt.y)
        else:
            test_text = False
        test_block = self.GetBlockBoundingBox(connectors).InsideXY(pt.x, pt.y)
        return test_text or test_block

    # Returns the bounding box of the name outside the block
    def GetTextBoundingBox(self):
        # Calculate the size of the name outside the block
        text_width, text_height = self.NameSize
        return wx.Rect(self.Pos.x + (self.Size[0] - text_width) // 2,
                       self.Pos.y - (text_height + 2),
                       text_width,
                       text_height)

    # Returns the bounding box of function block without name outside
    def GetBlockBoundingBox(self, connectors=True):
        bbx_x, bbx_y = self.Pos.x, self.Pos.y
        bbx_width, bbx_height = self.Size
        if connectors:
            bbx_x -= min(1, len(self.Inputs)) * CONNECTOR_SIZE
            bbx_width += (min(1, len(self.Inputs)) + min(1, len(self.Outputs))) * CONNECTOR_SIZE
        if self.ExecutionOrder != 0:
            bbx_x = min(bbx_x, self.Pos.x + self.Size[0] - self.ExecutionOrderSize[0])
            bbx_width = max(bbx_width, bbx_width + self.Pos.x + self.ExecutionOrderSize[0] - bbx_x - self.Size[0])
            bbx_height = bbx_height + (self.ExecutionOrderSize[1] + 2)
        return wx.Rect(bbx_x, bbx_y, bbx_width + 1, bbx_height + 1)

    # Refresh the block bounding box
    def RefreshBoundingBox(self):
        self.BoundingBox = self.GetBlockBoundingBox()
        if self.Name != "":
            self.BoundingBox.Union(self.GetTextBoundingBox())

    # Refresh the positions of the block connectors
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        # Calculate the size for the connector lines
        lines = max(len(self.Inputs), len(self.Outputs))
        if lines > 0:
            linesize = max((self.Size[1] - BLOCK_LINE_SIZE) // lines, BLOCK_LINE_SIZE)
            # Update inputs and outputs positions
            position = BLOCK_LINE_SIZE + linesize // 2
            for i in xrange(lines):
                if scaling is not None:
                    ypos = round_scaling(self.Pos.y + position, scaling[1]) - self.Pos.y
                else:
                    ypos = position
                if i < len(self.Inputs):
                    self.Inputs[i].SetPosition(wx.Point(0, ypos))
                if i < len(self.Outputs):
                    self.Outputs[i].SetPosition(wx.Point(self.Size[0], ypos))
                position += linesize
        self.RefreshConnected()

    # Refresh the positions of wires connected to inputs and outputs
    def RefreshConnected(self, exclude=None):
        for input in self.Inputs:
            input.MoveConnected(exclude)
        for output in self.Outputs:
            output.MoveConnected(exclude)

    # Returns the block connector that starts with the point given if it exists
    def GetConnector(self, position, output_name=None, input_name=None):
        if input_name is not None:
            # Test each input connector
            for input in self.Inputs:
                if input_name == input.GetName():
                    return input
        if output_name is not None:
            # Test each output connector
            for output in self.Outputs:
                if output_name == output.GetName():
                    return output
        if input_name is None and output_name is None:
            return self.FindNearestConnector(position, self.Inputs + self.Outputs)
        return None

    def GetInputTypes(self):
        return tuple([input.GetType(True) for input in self.Inputs if input.GetName() != "EN"])

    def SetOutputValues(self, values):
        for output in self.Outputs:
            output.SetValue(values.get(output.getName(), None))

    def GetConnectionResultType(self, connector, connectortype):
        if not TestConnectorName(connector.GetName(), self.Type):
            return connectortype
        resulttype = connectortype
        for input in self.Inputs:
            if input != connector and input.GetType(True) == "ANY" and TestConnectorName(input.GetName(), self.Type):
                inputtype = input.GetConnectedType()
                if resulttype is None or inputtype is not None and self.IsOfType(inputtype, resulttype):
                    resulttype = inputtype
        for output in self.Outputs:
            if output != connector and output.GetType(True) == "ANY" and TestConnectorName(output.GetName(), self.Type):
                outputtype = output.GetConnectedType()
                if resulttype is None or outputtype is not None and self.IsOfType(outputtype, resulttype):
                    resulttype = outputtype
        return resulttype

    # Returns all the block connectors
    def GetConnectors(self):
        return {"inputs": self.Inputs, "outputs": self.Outputs}

    # Test if point given is on one of the block connectors
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test each input connector
        for input in self.Inputs:
            if input.TestPoint(pt, direction, exclude):
                return input
        # Test each output connector
        for output in self.Outputs:
            if output.TestPoint(pt, direction, exclude):
                return output
        return None

    # Changes the block type
    def SetType(self, type, extension, inputs=None, connectors=None, executionControl=False):
        if type != self.Type or self.Extension != extension or executionControl != self.ExecutionControl:
            if type != self.Type:
                self.Type = type
                self.TypeSize = self.Parent.GetTextExtent(self.Type)
            self.Extension = extension
            self.ExecutionControl = executionControl
            # Find the block definition from type given and create the corresponding
            # inputs and outputs
            blocktype = self.Parent.GetBlockType(type, inputs)
            if blocktype:
                self.Colour = wx.BLACK
                inputs = [input for input in blocktype["inputs"]]
                outputs = [output for output in blocktype["outputs"]]
                if blocktype["extensible"]:
                    start = int(inputs[-1][0].replace("IN", ""))
                    for dummy in xrange(self.Extension - len(blocktype["inputs"])):
                        start += 1
                        inputs.append(("IN%d" % start, inputs[-1][1], inputs[-1][2]))
                comment = blocktype["comment"]
                self.Description = _(comment) + blocktype.get("usage", "")
            else:
                self.Colour = wx.RED
                connectors = {} if connectors is None else connectors
                inputs = connectors.get("inputs", [])
                outputs = connectors.get("outputs", [])
                self.Description = None
            if self.ExecutionControl:
                inputs.insert(0,  ("EN",   "BOOL", "none"))
                outputs.insert(0, ("ENO",  "BOOL", "none"))
            self.Pen = MiterPen(self.Colour)

            # Extract the inputs properties and create or modify the corresponding connector
            input_connectors = []
            for input_name, input_type, input_modifier in inputs:
                connector = Connector(self, input_name, input_type, wx.Point(0, 0), WEST, onlyone=True)
                if input_modifier == "negated":
                    connector.SetNegated(True)
                elif input_modifier != "none":
                    connector.SetEdge(input_modifier)
                for input in self.Inputs:
                    if input.GetName() == input_name:
                        wires = input.GetWires()[:]
                        input.UnConnect()
                        for wire in wires:
                            connector.Connect(wire)
                        break
                input_connectors.append(connector)
            for input in self.Inputs:
                input.UnConnect(delete=True)
            self.Inputs = input_connectors

            # Extract the outputs properties and create or modify the corresponding connector
            output_connectors = []
            for output_name, output_type, output_modifier in outputs:
                connector = Connector(self, output_name, output_type, wx.Point(0, 0), EAST)
                if output_modifier == "negated":
                    connector.SetNegated(True)
                elif output_modifier != "none":
                    connector.SetEdge(output_modifier)
                for output in self.Outputs:
                    if output.GetName() == output_name:
                        wires = output.GetWires()[:]
                        output.UnConnect()
                        for wire in wires:
                            connector.Connect(wire)
                        break
                output_connectors.append(connector)
            for output in self.Outputs:
                output.UnConnect(delete=True)
            self.Outputs = output_connectors

            self.RefreshMinSize()
            self.RefreshConnectors()
            for output in self.Outputs:
                output.RefreshWires()
            self.RefreshBoundingBox()

    # Returns the block type
    def GetType(self):
        return self.Type

    # Changes the block name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    # Returs the block name
    def GetName(self):
        return self.Name

    # Changes the extension name
    def SetExtension(self, extension):
        self.Extension = extension

    # Returs the extension name
    def GetExtension(self):
        return self.Extension

    # Changes the execution order
    def SetExecutionOrder(self, executionOrder):
        self.ExecutionOrder = executionOrder
        self.RefreshExecutionOrderSize()

    # Returs the execution order
    def GetExecutionOrder(self):
        return self.ExecutionOrder

    # Returs the execution order
    def GetExecutionControl(self):
        return self.ExecutionControl

    # Refresh the block minimum size
    def RefreshMinSize(self):
        # Calculate the inputs maximum width
        max_input = 0
        for input in self.Inputs:
            w, _h = input.GetNameSize()
            max_input = max(max_input, w)
        # Calculate the outputs maximum width
        max_output = 0
        for output in self.Outputs:
            w, _h = output.GetNameSize()
            max_output = max(max_output, w)
        width = max(self.TypeSize[0] + 10, max_input + max_output + 15)
        height = (max(len(self.Inputs), len(self.Outputs)) + 1) * BLOCK_LINE_SIZE
        self.MinSize = width, height

    # Returns the block minimum size
    def GetMinSize(self):
        return self.MinSize

    # Changes the negated property of the connector handled
    def SetConnectorNegated(self, negated):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_CONNECTOR:
            handle.SetNegated(negated)
            self.RefreshModel(False)

    # Changes the edge property of the connector handled
    def SetConnectorEdge(self, edge):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_CONNECTOR:
            handle.SetEdge(edge)
            self.RefreshModel(False)

#    # Method called when a Motion event have been generated
#    def OnMotion(self, event, dc, scaling):
#        if not event.Dragging():
#            pos = event.GetLogicalPosition(dc)
#            for input in self.Inputs:
#                rect = input.GetRedrawRect()
#                if rect.InsideXY(pos.x, pos.y):
#                    print "Find input"
#                    tip = wx.TipWindow(self.Parent, "Test")
#                    tip.SetBoundingRect(rect)
#        return Graphic_Element.OnMotion(self, event, dc, scaling)

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the block properties
        self.Parent.EditBlockContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        pos = GetScaledEventPosition(event, dc, scaling)
        # Popup the menu with special items for a block and a connector if one is handled
        connector = self.TestConnector(pos, exclude=False)
        if connector:
            self.Handle = (HANDLE_CONNECTOR, connector)
            self.Parent.PopupBlockMenu(connector)
        else:
            self.Parent.PopupBlockMenu()

    # Refreshes the block model
    def RefreshModel(self, move=True):
        self.Parent.RefreshBlockModel(self)
        # If block has moved, refresh the model of wires connected to outputs
        if move:
            for output in self.Outputs:
                output.RefreshWires()

    def GetToolTipValue(self):
        return self.Description

    # Adds an highlight to the block
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] in ["type", "name"] and start[0] == 0 and end[0] == 0:
            highlights = self.Highlights.setdefault(infos[0], [])
            AddHighlight(highlights, (start, end, highlight_type))
        elif infos[0] == "input" and infos[1] < len(self.Inputs):
            self.Inputs[infos[1]].AddHighlight(infos[2:], start, end, highlight_type)
        elif infos[0] == "output" and infos[1] < len(self.Outputs):
            self.Outputs[infos[1]].AddHighlight(infos[2:], start, end, highlight_type)

    # Removes an highlight from the block
    def RemoveHighlight(self, infos, start, end, highlight_type):
        if infos[0] in ["type", "name"]:
            highlights = self.Highlights.get(infos[0], [])
            if RemoveHighlight(highlights, (start, end, highlight_type)) and len(highlights) == 0:
                self.Highlights.pop(infos[0])
        elif infos[0] == "input" and infos[1] < len(self.Inputs):
            self.Inputs[infos[1]].RemoveHighlight(infos[2:], start, end, highlight_type)
        elif infos[0] == "output" and infos[1] < len(self.Outputs):
            self.Outputs[infos[1]].RemoveHighlight(infos[2:], start, end, highlight_type)

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
        for input in self.Inputs:
            input.ClearHighlights(highlight_type)
        for output in self.Outputs:
            output.ClearHighlights(highlight_type)

    # Draws block
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        dc.SetPen(self.Pen)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetTextForeground(self.Colour)

        if getattr(dc, "printing", False):
            name_size = dc.GetTextExtent(self.Name)
            type_size = dc.GetTextExtent(self.Type)
            executionorder_size = dc.GetTextExtent(str(self.ExecutionOrder))
        else:
            name_size = self.NameSize
            type_size = self.TypeSize
            executionorder_size = self.ExecutionOrderSize

        # Draw a rectangle with the block size
        dc.DrawRectangle(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)
        # Draw block name and block type
        name_pos = (self.Pos.x + (self.Size[0] - name_size[0]) // 2,
                    self.Pos.y - (name_size[1] + 2))
        type_pos = (self.Pos.x + (self.Size[0] - type_size[0]) // 2,
                    self.Pos.y + 5)
        dc.DrawText(self.Name, name_pos[0], name_pos[1])
        dc.DrawText(self.Type, type_pos[0], type_pos[1])
        # Draw inputs and outputs connectors
        for input in self.Inputs:
            input.Draw(dc)
        for output in self.Outputs:
            output.Draw(dc)
        if self.ExecutionOrder != 0:
            # Draw block execution order
            dc.DrawText(str(self.ExecutionOrder), self.Pos.x + self.Size[0] - executionorder_size[0],
                        self.Pos.y + self.Size[1] + 2)

        if not getattr(dc, "printing", False):
            DrawHighlightedText(dc, self.Name, self.Highlights.get("name", []), name_pos[0], name_pos[1])
            DrawHighlightedText(dc, self.Type, self.Highlights.get("type", []), type_pos[0], type_pos[1])


# -------------------------------------------------------------------------------
#                        Function Block Diagram Variable
# -------------------------------------------------------------------------------


class FBD_Variable(Graphic_Element):
    """
    Class that implements the graphic representation of a variable
    """

    # Create a new variable
    def __init__(self, parent, type, name, value_type, id=None, executionOrder=0):
        Graphic_Element.__init__(self, parent)
        self.Type = None
        self.ValueType = None
        self.Id = id
        self.SetName(name)
        self.SetExecutionOrder(executionOrder)
        self.Input = None
        self.Output = None
        self.SetType(type, value_type)
        self.Highlights = []

    # Make a clone of this FBD_Variable
    def Clone(self, parent, id=None, pos=None):
        variable = FBD_Variable(parent, self.Type, self.Name, self.ValueType, id)
        variable.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            variable.SetPosition(pos.x, pos.y)
        else:
            variable.SetPosition(self.Pos.x, self.Pos.y)
        if self.Input:
            variable.Input = self.Input.Clone(variable)
        if self.Output:
            variable.Output = self.Output.Clone(variable)
        return variable

    def GetConnectorTranslation(self, element):
        connectors = {}
        if self.Input is not None:
            connectors[self.Input] = element.Input
        if self.Output is not None:
            connectors[self.Output] = element.Output
        return connectors

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None
        if self.Output is not None:
            self.Output.Flush()
            self.Output = None

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if movex != 0 or movey != 0:
            if self.Input and self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
            if self.Output and self.Output.IsConnected():
                rect = rect.Union(self.Output.GetConnectedRedrawRect(movex, movey))
        return rect

    # Unconnect connector
    def Clean(self):
        if self.Input:
            self.Input.UnConnect(delete=True)
        if self.Output:
            self.Output.UnConnect(delete=True)

    # Delete this variable by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteVariable(self)

    # Refresh the size of text for name
    def RefreshNameSize(self):
        self.NameSize = self.Parent.GetTextExtent(self.Name)

    # Refresh the size of text for execution order
    def RefreshExecutionOrderSize(self):
        self.ExecutionOrderSize = self.Parent.GetTextExtent(str(self.ExecutionOrder))

    # Refresh the variable bounding box
    def RefreshBoundingBox(self):
        if self.Type in (OUTPUT, INOUT):
            bbx_x = self.Pos.x - CONNECTOR_SIZE
        else:
            bbx_x = self.Pos.x
        if self.Type == INOUT:
            bbx_width = self.Size[0] + 2 * CONNECTOR_SIZE
        else:
            bbx_width = self.Size[0] + CONNECTOR_SIZE
        bbx_x = min(bbx_x, self.Pos.x + (self.Size[0] - self.NameSize[0]) // 2)
        bbx_width = max(bbx_width, self.NameSize[0])
        bbx_height = self.Size[1]
        if self.ExecutionOrder != 0:
            bbx_x = min(bbx_x, self.Pos.x + self.Size[0] - self.ExecutionOrderSize[0])
            bbx_width = max(bbx_width, bbx_width + self.Pos.x + self.ExecutionOrderSize[0] - bbx_x - self.Size[0])
            bbx_height = bbx_height + (self.ExecutionOrderSize[1] + 2)
        self.BoundingBox = wx.Rect(bbx_x, self.Pos.y, bbx_width + 1, bbx_height + 1)

    # Refresh the position of the variable connector
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        if scaling is not None:
            position = round_scaling(self.Pos.y + self.Size[1] // 2, scaling[1]) - self.Pos.y
        else:
            position = self.Size[1] // 2
        if self.Input:
            self.Input.SetPosition(wx.Point(0, position))
        if self.Output:
            self.Output.SetPosition(wx.Point(self.Size[0], position))
        self.RefreshConnected()

    # Refresh the position of wires connected to connector
    def RefreshConnected(self, exclude=None):
        if self.Input:
            self.Input.MoveConnected(exclude)
        if self.Output:
            self.Output.MoveConnected(exclude)

    # Test if point given is on the variable connector
    def TestConnector(self, pt, direction=None, exclude=True):
        if self.Input and self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        if self.Output and self.Output.TestPoint(pt, direction, exclude):
            return self.Output
        return None

    # Returns the block connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test input and output connector if they exists
            # if self.Input and name == self.Input.GetName():
            #    return self.Input
            if self.Output and name == self.Output.GetName():
                return self.Output
        connectors = []
        # Test input connector if it exists
        if self.Input:
            connectors.append(self.Input)
        # Test output connector if it exists
        if self.Output:
            connectors.append(self.Output)
        return self.FindNearestConnector(position, connectors)

    # Returns all the block connectors
    def GetConnectors(self):
        connectors = {"inputs": [], "outputs": []}
        if self.Input:
            connectors["inputs"].append(self.Input)
        if self.Output:
            connectors["outputs"].append(self.Output)
        return connectors

    # Changes the negated property of the variable connector if handled
    def SetConnectorNegated(self, negated):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_CONNECTOR:
            handle.SetNegated(negated)
            self.RefreshModel(False)

    # Changes the variable type
    def SetType(self, type, value_type):
        if type != self.Type:
            self.Type = type
            # Create an input or output connector according to variable type
            if self.Type != INPUT:
                if self.Input is None:
                    self.Input = Connector(self, "", value_type, wx.Point(0, 0), WEST, onlyone=True)
            elif self.Input:
                self.Input.UnConnect(delete=True)
                self.Input = None
            if self.Type != OUTPUT:
                if self.Output is None:
                    self.Output = Connector(self, "", value_type, wx.Point(0, 0), EAST)
            elif self.Output:
                self.Output.UnConnect(delete=True)
                self.Output = None
            self.RefreshConnectors()
            self.RefreshBoundingBox()
        elif value_type != self.ValueType:
            if self.Input:
                self.Input.SetType(value_type)
            if self.Output:
                self.Output.SetType(value_type)

    # Returns the variable type
    def GetType(self):
        return self.Type

    # Returns the variable value type
    def GetValueType(self):
        return self.ValueType

    # Changes the variable name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    # Returns the variable name
    def GetName(self):
        return self.Name

    # Changes the execution order
    def SetExecutionOrder(self, executionOrder):
        self.ExecutionOrder = executionOrder
        self.RefreshExecutionOrderSize()

    # Returs the execution order
    def GetExecutionOrder(self):
        return self.ExecutionOrder

    # Returns the variable minimum size
    def GetMinSize(self):
        return self.NameSize[0] + 10, self.NameSize[1] + 10

    # Set size of the variable to the minimum size
    def SetBestSize(self, scaling):
        if self.Type == INPUT:
            return Graphic_Element.SetBestSize(self, scaling, x_factor=1.)
        elif self.Type == OUTPUT:
            return Graphic_Element.SetBestSize(self, scaling, x_factor=0.)
        else:
            return Graphic_Element.SetBestSize(self, scaling)

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        if event.ControlDown():
            # Change variable type
            types = [INPUT, OUTPUT, INOUT]
            self.Parent.ChangeVariableType(
                self, types[(types.index(self.Type) + 1) % len(types)])
        else:
            # Edit the variable properties
            self.Parent.EditVariableContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        self.Parent.PopupVariableMenu()

    # Refreshes the variable model
    def RefreshModel(self, move=True):
        self.Parent.RefreshVariableModel(self)
        # If variable has moved and variable is not of type OUTPUT, refresh the model
        # of wires connected to output connector
        if move and self.Type != OUTPUT:
            if self.Output:
                self.Output.RefreshWires()

    # Adds an highlight to the variable
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "expression" and start[0] == 0 and end[0] == 0:
            AddHighlight(self.Highlights, (start, end, highlight_type))

    # Removes an highlight from the variable
    def RemoveHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "expression":
            RemoveHighlight(self.Highlights, (start, end, highlight_type))

    # Removes all the highlights of one particular type from the variable
    def ClearHighlight(self, highlight_type=None):
        ClearHighlights(self.Highlights, highlight_type)

    # Draws variable
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.WHITE_BRUSH)

        if getattr(dc, "printing", False):
            name_size = dc.GetTextExtent(self.Name)
            executionorder_size = dc.GetTextExtent(str(self.ExecutionOrder))
        else:
            name_size = self.NameSize
            executionorder_size = self.ExecutionOrderSize

        text_pos = (self.Pos.x + (self.Size[0] - name_size[0]) // 2,
                    self.Pos.y + (self.Size[1] - name_size[1]) // 2)
        # Draw a rectangle with the variable size
        dc.DrawRectangle(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)
        # Draw variable name
        dc.DrawText(self.Name, text_pos[0], text_pos[1])
        # Draw connectors
        if self.Input:
            self.Input.Draw(dc)
        if self.Output:
            self.Output.Draw(dc)
        if self.ExecutionOrder != 0:
            # Draw variable execution order
            dc.DrawText(str(self.ExecutionOrder), self.Pos.x + self.Size[0] - executionorder_size[0],
                        self.Pos.y + self.Size[1] + 2)
        if not getattr(dc, "printing", False):
            DrawHighlightedText(dc, self.Name, self.Highlights, text_pos[0], text_pos[1])


# -------------------------------------------------------------------------------
#                        Function Block Diagram Connector
# -------------------------------------------------------------------------------


class FBD_Connector(Graphic_Element):
    """
    Class that implements the graphic representation of a connection
    """

    # Create a new connection
    def __init__(self, parent, type, name, id=None):
        Graphic_Element.__init__(self, parent)
        self.Type = type
        self.Id = id
        self.SetName(name)
        self.Pos = wx.Point(0, 0)
        self.Size = wx.Size(0, 0)
        self.Highlights = []
        # Create an input or output connector according to connection type
        if self.Type == CONNECTOR:
            self.Connector = Connector(self, "", "ANY", wx.Point(0, 0), WEST, onlyone=True)
        else:
            self.Connector = Connector(self, "", "ANY", wx.Point(0, 0), EAST)
        self.RefreshConnectors()
        self.RefreshNameSize()

    def Flush(self):
        if self.Connector:
            self.Connector.Flush()
            self.Connector = None

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if movex != 0 or movey != 0:
            if self.Connector and self.Connector.IsConnected():
                rect = rect.Union(self.Connector.GetConnectedRedrawRect(movex, movey))
        return rect

    # Make a clone of this FBD_Connector
    def Clone(self, parent, id=None, pos=None):
        connection = FBD_Connector(parent, self.Type, self.Name, id)
        connection.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            connection.SetPosition(pos.x, pos.y)
        else:
            connection.SetPosition(self.Pos.x, self.Pos.y)
        connection.Connector = self.Connector.Clone(connection)
        return connection

    def GetConnectorTranslation(self, element):
        return {self.Connector: element.Connector}

    # Unconnect connector
    def Clean(self):
        if self.Connector:
            self.Connector.UnConnect(delete=True)

    # Delete this connection by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteConnection(self)

    # Refresh the size of text for name
    def RefreshNameSize(self):
        self.NameSize = self.Parent.GetTextExtent(self.Name)

    # Refresh the connection bounding box
    def RefreshBoundingBox(self):
        if self.Type == CONNECTOR:
            bbx_x = self.Pos.x - CONNECTOR_SIZE
        else:
            bbx_x = self.Pos.x
        bbx_width = self.Size[0] + CONNECTOR_SIZE
        self.BoundingBox = wx.Rect(bbx_x, self.Pos.y, bbx_width, self.Size[1])

    # Refresh the position of the connection connector
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        if scaling is not None:
            position = round_scaling(self.Pos.y + self.Size[1] // 2, scaling[1]) - self.Pos.y
        else:
            position = self.Size[1] // 2
        if self.Type == CONNECTOR:
            self.Connector.SetPosition(wx.Point(0, position))
        else:
            self.Connector.SetPosition(wx.Point(self.Size[0], position))
        self.RefreshConnected()

    # Refresh the position of wires connected to connector
    def RefreshConnected(self, exclude=None):
        if self.Connector:
            self.Connector.MoveConnected(exclude)

    # Test if point given is on the connection connector
    def TestConnector(self, pt, direction=None, exclude=True):
        if self.Connector and self.Connector.TestPoint(pt, direction, exclude):
            return self.Connector
        return None

    # Returns the connection connector
    def GetConnector(self, position=None, name=None):
        return self.Connector

        # Returns all the block connectors
    def GetConnectors(self):
        connectors = {"inputs": [], "outputs": []}
        if self.Type == CONNECTOR:
            connectors["inputs"].append(self.Connector)
        else:
            connectors["outputs"].append(self.Connector)
        return connectors

    def SpreadCurrent(self):
        if self.Type == CONNECTOR:
            continuations = self.Parent.GetContinuationByName(self.Name)
            if continuations is not None:
                value = self.Connector.ReceivingCurrent()
                for cont in continuations:
                    cont.Connector.SpreadCurrent(value)

    # Changes the variable type
    def SetType(self, type):
        if type != self.Type:
            self.Type = type
            self.Clean()
            # Create an input or output connector according to connection type
            if self.Type == CONNECTOR:
                self.Connector = Connector(self, "", "ANY", wx.Point(0, 0), WEST, onlyone=True)
            else:
                self.Connector = Connector(self, "", "ANY", wx.Point(0, 0), EAST)
            self.RefreshConnectors()
            self.RefreshBoundingBox()

    # Returns the connection type
    def GetType(self):
        return self.Type

    def GetConnectionResultType(self, connector, connectortype):
        if self.Type == CONTINUATION:
            connector = self.Parent.GetConnectorByName(self.Name)
            if connector is not None:
                return connector.Connector.GetConnectedType()
        return connectortype

    # Changes the connection name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    # Returns the connection name
    def GetName(self):
        return self.Name

    # Set size of the variable to the minimum size
    def SetBestSize(self, scaling):
        if self.Type == CONTINUATION:
            return Graphic_Element.SetBestSize(self, scaling, x_factor=1.)
        else:
            return Graphic_Element.SetBestSize(self, scaling, x_factor=0.)

    # Returns the connection minimum size
    def GetMinSize(self):
        text_width, text_height = self.NameSize
        if text_height % 2 == 1:
            text_height += 1
        return text_width + text_height + 20, text_height + 10

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        if event.ControlDown():
            # Change connection type
            if self.Type == CONNECTOR:
                self.Parent.ChangeConnectionType(self, CONTINUATION)
            else:
                self.Parent.ChangeConnectionType(self, CONNECTOR)
        else:
            # Edit the connection properties
            self.Parent.EditConnectionContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the default menu
        self.Parent.PopupConnectionMenu()

    # Refreshes the connection model
    def RefreshModel(self, move=True):
        self.Parent.RefreshConnectionModel(self)
        # If connection has moved and connection is of type CONTINUATION, refresh
        # the model of wires connected to connector
        if move and self.Type == CONTINUATION:
            if self.Connector:
                self.Connector.RefreshWires()

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

    # Draws connection
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.WHITE_BRUSH)

        if getattr(dc, "printing", False):
            name_size = dc.GetTextExtent(self.Name)
        else:
            name_size = self.NameSize

        # Draw a rectangle with the connection size with arrows inside
        dc.DrawRectangle(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)
        arrowsize = min(self.Size[1] // 2, (self.Size[0] - name_size[0] - 10) // 2)
        dc.DrawLine(self.Pos.x, self.Pos.y, self.Pos.x + arrowsize,
                    self.Pos.y + self.Size[1] // 2)
        dc.DrawLine(self.Pos.x + arrowsize, self.Pos.y + self.Size[1] // 2,
                    self.Pos.x, self.Pos.y + self.Size[1])
        dc.DrawLine(self.Pos.x + self.Size[0] - arrowsize, self.Pos.y,
                    self.Pos.x + self.Size[0], self.Pos.y + self.Size[1] // 2)
        dc.DrawLine(self.Pos.x + self.Size[0], self.Pos.y + self.Size[1] // 2,
                    self.Pos.x + self.Size[0] - arrowsize, self.Pos.y + self.Size[1])
        # Draw connection name
        text_pos = (self.Pos.x + (self.Size[0] - name_size[0]) // 2,
                    self.Pos.y + (self.Size[1] - name_size[1]) // 2)
        dc.DrawText(self.Name, text_pos[0], text_pos[1])
        # Draw connector
        if self.Connector:
            self.Connector.Draw(dc)

        if not getattr(dc, "printing", False):
            DrawHighlightedText(dc, self.Name, self.Highlights, text_pos[0], text_pos[1])
