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
from future.builtins import round
from six.moves import xrange

from graphics.GraphicCommons import *
from graphics.DebugDataConsumer import DebugDataConsumer
from plcopen.structures import *


# -------------------------------------------------------------------------------
#                         Ladder Diagram PowerRail
# -------------------------------------------------------------------------------


class LD_PowerRail(Graphic_Element):
    """
    Class that implements the graphic representation of a power rail
    """

    # Create a new power rail
    def __init__(self, parent, type, id=None, connectors=1):
        Graphic_Element.__init__(self, parent)
        self.Type = None
        self.Connectors = []
        self.RealConnectors = None
        self.Id = id
        self.Extensions = [LD_LINE_SIZE // 2, LD_LINE_SIZE // 2]
        self.SetType(type, connectors)

    def Flush(self):
        for connector in self.Connectors:
            connector.Flush()
        self.Connectors = []

    # Make a clone of this LD_PowerRail
    def Clone(self, parent, id=None, pos=None):
        powerrail = LD_PowerRail(parent, self.Type, id)
        powerrail.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            powerrail.SetPosition(pos.x, pos.y)
        else:
            powerrail.SetPosition(self.Pos.x, self.Pos.y)
        powerrail.Connectors = []
        for connector in self.Connectors:
            powerrail.Connectors.append(connector.Clone(powerrail))
        return powerrail

    def GetConnectorTranslation(self, element):
        return dict(zip([connector for connector in self.Connectors],
                        [connector for connector in element.Connectors]))

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        for connector in self.Connectors:
            rect = rect.Union(connector.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            for connector in self.Connectors:
                if connector.IsConnected():
                    rect = rect.Union(connector.GetConnectedRedrawRect(movex, movey))
        return rect

    # Forbids to change the power rail size
    def SetSize(self, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.SetSize(self, width, height)
        else:
            Graphic_Element.SetSize(self, LD_POWERRAIL_WIDTH, height)
        self.RefreshConnectors()

    # Forbids to select a power rail
    def HitTest(self, pt, connectors=True):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            return Graphic_Element.HitTest(self, pt, connectors) or self.TestConnector(pt, exclude=False) is not None
        return False

    # Forbids to select a power rail
    def IsInSelection(self, rect):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            return Graphic_Element.IsInSelection(self, rect)
        return False

    # Deletes this power rail by calling the appropriate method
    def Delete(self):
        self.Parent.DeletePowerRail(self)

    # Unconnect all connectors
    def Clean(self):
        for connector in self.Connectors:
            connector.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Refresh the power rail bounding box
    def RefreshBoundingBox(self):
        self.BoundingBox = wx.Rect(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)

    # Refresh the power rail size
    def RefreshSize(self):
        self.Size = wx.Size(LD_POWERRAIL_WIDTH, max(LD_LINE_SIZE * len(self.Connectors), self.Size[1]))
        self.RefreshBoundingBox()

    # Returns the block minimum size
    def GetMinSize(self, default=False):
        height = (LD_LINE_SIZE * (len(self.Connectors) - 1)
                  if default else 0)
        return LD_POWERRAIL_WIDTH, height + self.Extensions[0] + self.Extensions[1]

    # Add a connector or a blank to this power rail at the last place
    def AddConnector(self):
        self.InsertConnector(len(self.Connectors))

    # Add a connector or a blank to this power rail at the place given
    def InsertConnector(self, idx):
        if self.Type == LEFTRAIL:
            connector = Connector(self, "", "BOOL", wx.Point(self.Size[0], 0), EAST)
        elif self.Type == RIGHTRAIL:
            connector = Connector(self, "", "BOOL", wx.Point(0, 0), WEST)
        self.Connectors.insert(idx, connector)
        self.RefreshSize()
        self.RefreshConnectors()

    # Moves the divergence connector given
    def MoveConnector(self, connector, movey):
        position = connector.GetRelPosition()
        connector.SetPosition(wx.Point(position.x, position.y + movey))
        miny = self.Size[1]
        maxy = 0
        for connect in self.Connectors:
            connect_pos = connect.GetRelPosition()
            miny = min(miny, connect_pos.y - self.Extensions[0])
            maxy = max(maxy, connect_pos.y - self.Extensions[0])
        min_pos = self.Pos.y + miny
        self.Pos.y = min(min_pos, self.Pos.y)
        if min_pos == self.Pos.y:
            for connect in self.Connectors:
                connect_pos = connect.GetRelPosition()
                connect.SetPosition(wx.Point(connect_pos.x, connect_pos.y - miny))
        self.Connectors.sort(lambda x, y: cmp(x.Pos.y, y.Pos.y))
        maxy = 0
        for connect in self.Connectors:
            connect_pos = connect.GetRelPosition()
            maxy = max(maxy, connect_pos.y)
        self.Size[1] = max(maxy + self.Extensions[1], self.Size[1])
        connector.MoveConnected()
        self.RefreshBoundingBox()

    # Returns the index in connectors list for the connector given
    def GetConnectorIndex(self, connector):
        if connector in self.Connectors:
            return self.Connectors.index(connector)
        return None

    # Delete the connector or blank from connectors list at the index given
    def DeleteConnector(self, idx):
        self.Connectors.pop(idx)
        self.RefreshConnectors()
        self.RefreshSize()

    # Refresh the positions of the power rail connectors
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        height = self.Size[1] - self.Extensions[0] - self.Extensions[1]
        interval = height / max(len(self.Connectors) - 1, 1)
        for i, connector in enumerate(self.Connectors):
            if self.RealConnectors:
                position = self.Extensions[0] + int(round(self.RealConnectors[i] * height))
            else:
                position = self.Extensions[0] + int(round(i * interval))
            if scaling is not None:
                position = round((self.Pos.y + position) / scaling[1]) * scaling[1] - self.Pos.y
            if self.Type == LEFTRAIL:
                connector.SetPosition(wx.Point(self.Size[0], position))
            elif self.Type == RIGHTRAIL:
                connector.SetPosition(wx.Point(0, position))
        self.RefreshConnected()

    # Refresh the position of wires connected to power rail
    def RefreshConnected(self, exclude=None):
        for connector in self.Connectors:
            connector.MoveConnected(exclude)

    # Returns the power rail connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test each connector if it exists
            for connector in self.Connectors:
                if name == connector.GetName():
                    return connector
        return self.FindNearestConnector(position, [connector for connector in self.Connectors if connector is not None])

    # Returns all the power rail connectors
    def GetConnectors(self):
        connectors = [connector for connector in self.Connectors if connector]
        if self.Type == LEFTRAIL:
            return {"inputs": [], "outputs": connectors}
        else:
            return {"inputs": connectors, "outputs": []}

    # Test if point given is on one of the power rail connectors
    def TestConnector(self, pt, direction=None, exclude=True):
        for connector in self.Connectors:
            if connector.TestPoint(pt, direction, exclude):
                return connector
        return None

    # Returns the power rail type
    def SetType(self, type, connectors):
        if type != self.Type or len(self.Connectors) != connectors:
            # Create a connector or a blank according to 'connectors' and add it in
            # the connectors list
            self.Type = type
            self.Clean()
            self.Connectors = []
            for dummy in xrange(connectors):
                self.AddConnector()
            self.RefreshSize()

    # Returns the power rail type
    def GetType(self):
        return self.Type

    # Method called when a LeftDown event have been generated
    def OnLeftDown(self, event, dc, scaling):
        self.RealConnectors = []
        height = self.Size[1] - self.Extensions[0] - self.Extensions[1]
        if height > 0:
            for connector in self.Connectors:
                position = connector.GetRelPosition()
                self.RealConnectors.append(max(0., min((position.y - self.Extensions[0]) / height, 1.)))
        elif len(self.Connectors) > 1:
            self.RealConnectors = map(lambda x: x * 1 / (len(self.Connectors) - 1), xrange(len(self.Connectors)))
        else:
            self.RealConnectors = [0.5]
        Graphic_Element.OnLeftDown(self, event, dc, scaling)

    # Method called when a LeftUp event have been generated
    def OnLeftUp(self, event, dc, scaling):
        Graphic_Element.OnLeftUp(self, event, dc, scaling)
        self.RealConnectors = None

    # Method called when a LeftDown event have been generated
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

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the powerrail properties
        self.Parent.EditPowerRailContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_CONNECTOR and self.Dragging and self.oldPos:
            wires = handle.GetWires()
            if len(wires) == 1:
                if handle == wires[0][0].StartConnected:
                    block = wires[0][0].EndConnected.GetParentBlock()
                else:
                    block = wires[0][0].StartConnected.GetParentBlock()
                block.RefreshModel(False)
            Graphic_Element.OnRightUp(self, event, dc, scaling)
        else:
            self.Parent.PopupDefaultMenu()

    def Resize(self, x, y, width, height):
        self.Move(x, y)
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            self.SetSize(width, height)
        else:
            self.SetSize(LD_POWERRAIL_WIDTH, height)

    # Refreshes the powerrail state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        handle_type, handle = self.Handle
        # A connector has been handled
        if handle_type == HANDLE_CONNECTOR:
            movey = max(-self.BoundingBox.y, movey)
            if scaling is not None:
                position = handle.GetRelPosition()
                movey = round((self.Pos.y + position.y + movey) / scaling[1]) * scaling[1] - self.Pos.y - position.y
            self.MoveConnector(handle, movey)
            return 0, movey
        elif self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)
        return 0, 0

    # Refreshes the power rail model
    def RefreshModel(self, move=True):
        self.Parent.RefreshPowerRailModel(self)
        # If power rail has moved and power rail is of type LEFT, refresh the model
        # of wires connected to connectors
        if move and self.Type == LEFTRAIL:
            for connector in self.Connectors:
                connector.RefreshWires()

    # Draws power rail
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.BLACK_BRUSH)
        # Draw a rectangle with the power rail size
        if self.Type == LEFTRAIL:
            dc.DrawRectangle(self.Pos.x + self.Size[0] - LD_POWERRAIL_WIDTH, self.Pos.y, LD_POWERRAIL_WIDTH + 1, self.Size[1] + 1)
        else:
            dc.DrawRectangle(self.Pos.x, self.Pos.y, LD_POWERRAIL_WIDTH + 1, self.Size[1] + 1)
        # Draw connectors
        for connector in self.Connectors:
            connector.Draw(dc)


# -------------------------------------------------------------------------------
#                         Ladder Diagram Contact
# -------------------------------------------------------------------------------


class LD_Contact(Graphic_Element, DebugDataConsumer):
    """
    Class that implements the graphic representation of a contact
    """

    # Create a new contact
    def __init__(self, parent, type, name, id=None):
        Graphic_Element.__init__(self, parent)
        DebugDataConsumer.__init__(self)
        self.Type = type
        self.Name = name
        self.Id = id
        self.Size = wx.Size(LD_ELEMENT_SIZE[0], LD_ELEMENT_SIZE[1])
        self.Highlights = {}
        # Create an input and output connector
        self.Input = Connector(self, "", "BOOL", wx.Point(0, self.Size[1] // 2 + 1), WEST)
        self.Output = Connector(self, "", "BOOL", wx.Point(self.Size[0], self.Size[1] // 2 + 1), EAST)
        self.PreviousValue = False
        self.PreviousSpreading = False
        self.RefreshNameSize()
        self.RefreshTypeSize()

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None
        if self.Output is not None:
            self.Output.Flush()
            self.Output = None

    def SetForced(self, forced):
        if self.Forced != forced:
            self.Forced = forced
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)

    def SetValue(self, value):
        if self.Type == CONTACT_RISING:
            refresh = self.Value and not self.PreviousValue
        elif self.Type == CONTACT_FALLING:
            refresh = not self.Value and self.PreviousValue
        else:
            refresh = False
        self.PreviousValue = self.Value
        self.Value = value
        if self.Value != self.PreviousValue or refresh:
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)
            self.SpreadCurrent()

    def SpreadCurrent(self):
        if self.Parent.Debug:
            if self.Value is None:
                self.Value = False
            spreading = self.Input.ReceivingCurrent()
            if self.Type == CONTACT_NORMAL:
                spreading &= self.Value
            elif self.Type == CONTACT_REVERSE:
                spreading &= not self.Value
            elif self.Type == CONTACT_RISING:
                spreading &= self.Value and not self.PreviousValue
            elif self.Type == CONTACT_FALLING:
                spreading &= not self.Value and self.PreviousValue
            else:
                spreading = False
            if spreading and not self.PreviousSpreading:
                self.Output.SpreadCurrent(True)
            elif not spreading and self.PreviousSpreading:
                self.Output.SpreadCurrent(False)
            self.PreviousSpreading = spreading

    # Make a clone of this LD_Contact
    def Clone(self, parent, id=None, pos=None):
        contact = LD_Contact(parent, self.Type, self.Name, id)
        contact.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            contact.SetPosition(pos.x, pos.y)
        else:
            contact.SetPosition(self.Pos.x, self.Pos.y)
        contact.Input = self.Input.Clone(contact)
        contact.Output = self.Output.Clone(contact)
        return contact

    def GetConnectorTranslation(self, element):
        return {self.Input: element.Input, self.Output: element.Output}

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        rect = rect.Union(self.Input.GetRedrawRect(movex, movey))
        rect = rect.Union(self.Output.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            if self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
            if self.Output.IsConnected():
                rect = rect.Union(self.Output.GetConnectedRedrawRect(movex, movey))
        return rect

    def ProcessDragging(self, movex, movey, event, scaling):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            movex = movey = 0
        return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling, height_fac=2)

    # Forbids to change the contact size
    def SetSize(self, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.SetSize(self, width, height)
            self.RefreshConnectors()

    # Delete this contact by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteContact(self)

    # Unconnect input and output
    def Clean(self):
        self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        self.Output.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Refresh the size of text for name
    def RefreshNameSize(self):
        if self.Name != "":
            self.NameSize = self.Parent.GetTextExtent(self.Name)
        else:
            self.NameSize = 0, 0

    # Refresh the size of text for type
    def RefreshTypeSize(self):
        typetext = ""
        if self.Type == CONTACT_REVERSE:
            typetext = "/"
        elif self.Type == CONTACT_RISING:
            typetext = "P"
        elif self.Type == CONTACT_FALLING:
            typetext = "N"
        if typetext != "":
            self.TypeSize = self.Parent.GetTextExtent(typetext)
        else:
            self.TypeSize = 0, 0

    # Refresh the contact bounding box
    def RefreshBoundingBox(self):
        # Calculate the size of the name outside the contact
        text_width, text_height = self.Parent.GetTextExtent(self.Name)
        # Calculate the bounding box size
        if self.Name != "":
            bbx_x = self.Pos.x - max(0, (text_width - self.Size[0]) // 2)
            bbx_width = max(self.Size[0], text_width)
            bbx_y = self.Pos.y - (text_height + 2)
            bbx_height = self.Size[1] + (text_height + 2)
        else:
            bbx_x = self.Pos.x
            bbx_width = self.Size[0]
            bbx_y = self.Pos.y
            bbx_height = self.Size[1]
        self.BoundingBox = wx.Rect(bbx_x, bbx_y, bbx_width + 1, bbx_height + 1)

    # Returns the block minimum size
    def GetMinSize(self):
        return LD_ELEMENT_SIZE

    # Refresh the position of wire connected to contact
    def RefreshConnected(self, exclude=None):
        self.Input.MoveConnected(exclude)
        self.Output.MoveConnected(exclude)

    # Returns the contact connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test input and output connector
            # if name == self.Input.GetName():
            #    return self.Input
            if name == self.Output.GetName():
                return self.Output
        return self.FindNearestConnector(position, [self.Input, self.Output])

    # Returns input and output contact connectors
    def GetConnectors(self):
        return {"inputs": [self.Input], "outputs": [self.Output]}

    # Test if point given is on contact input or output connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector
        if self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        # Test output connector
        if self.Output.TestPoint(pt, direction, exclude):
            return self.Output
        return None

    # Refresh the positions of the block connectors
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        position = self.Size[1] // 2 + 1
        if scaling is not None:
            position = round((self.Pos.y + position) / scaling[1]) * scaling[1] - self.Pos.y
        self.Input.SetPosition(wx.Point(0, position))
        self.Output.SetPosition(wx.Point(self.Size[0], position))
        self.RefreshConnected()

    # Changes the contact name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    # Returns the contact name
    def GetName(self):
        return self.Name

    # Changes the contact type
    def SetType(self, type):
        self.Type = type
        self.RefreshTypeSize()

    # Returns the contact type
    def GetType(self):
        return self.Type

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the contact properties
        self.Parent.EditContactContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the default menu
        self.Parent.PopupDefaultMenu()

    # Refreshes the contact model
    def RefreshModel(self, move=True):
        self.Parent.RefreshContactModel(self)
        # If contact has moved, refresh the model of wires connected to output
        if move:
            self.Output.RefreshWires()

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        dc.SetPen(MiterPen(HIGHLIGHTCOLOR))
        dc.SetBrush(wx.Brush(HIGHLIGHTCOLOR))
        dc.SetLogicalFunction(wx.AND)
        # Draw two rectangles for representing the contact
        left_left = (self.Pos.x - 1) * scalex - 2
        right_left = (self.Pos.x + self.Size[0] - 2) * scalex - 2
        top = (self.Pos.y - 1) * scaley - 2
        width = 4 * scalex + 5
        height = (self.Size[1] + 3) * scaley + 5

        dc.DrawRectangle(left_left, top, width, height)
        dc.DrawRectangle(right_left, top, width, height)
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Adds an highlight to the connection
    def AddHighlight(self, infos, start, end, highlight_type):
        highlights = self.Highlights.setdefault(infos[0], [])
        if infos[0] == "reference":
            if start[0] == 0 and end[0] == 0:
                AddHighlight(highlights, (start, end, highlight_type))
        else:
            AddHighlight(highlights, ((0, 0), (0, 1), highlight_type))

    # Removes an highlight from the connection
    def RemoveHighlight(self, infos, start, end, highlight_type):
        highlights = self.Highlights.get(infos[0], [])
        if RemoveHighlight(highlights, (start, end, highlight_type)) and len(highlights) == 0:
            self.Highlights.pop(infos[0])

    # Removes all the highlights of one particular type from the connection
    def ClearHighlight(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = {}
        else:
            highlight_items = self.Highlights.items()
            for name, highlights in highlight_items:
                highlights = ClearHighlights(highlights, highlight_type)
                if len(highlights) == 0:
                    self.Highlights.pop(name)

    # Draws contact
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value is not None:
            if self.Type == CONTACT_NORMAL and self.Value or \
               self.Type == CONTACT_REVERSE and not self.Value or \
               self.Type == CONTACT_RISING and self.Value and not self.PreviousValue or \
               self.Type == CONTACT_RISING and not self.Value and self.PreviousValue:
                if self.Forced:
                    dc.SetPen(MiterPen(wx.CYAN))
                else:
                    dc.SetPen(MiterPen(wx.GREEN))
            elif self.Forced:
                dc.SetPen(MiterPen(wx.BLUE))
            else:
                dc.SetPen(MiterPen(wx.BLACK))
        else:
            dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.BLACK_BRUSH)

        # Compiling contact type modifier symbol
        typetext = ""
        if self.Type == CONTACT_REVERSE:
            typetext = "/"
        elif self.Type == CONTACT_RISING:
            typetext = "P"
        elif self.Type == CONTACT_FALLING:
            typetext = "N"

        if getattr(dc, "printing", False):
            name_size = dc.GetTextExtent(self.Name)
            if typetext != "":
                type_size = dc.GetTextExtent(typetext)
        else:
            name_size = self.NameSize
            if typetext != "":
                type_size = self.TypeSize

        # Draw two rectangles for representing the contact
        dc.DrawRectangle(self.Pos.x, self.Pos.y, 2, self.Size[1] + 1)
        dc.DrawRectangle(self.Pos.x + self.Size[0] - 1, self.Pos.y, 2, self.Size[1] + 1)
        # Draw contact name
        name_pos = (self.Pos.x + (self.Size[0] - name_size[0]) // 2,
                    self.Pos.y - (name_size[1] + 2))
        dc.DrawText(self.Name, name_pos[0], name_pos[1])
        # Draw the modifier symbol in the middle of contact
        if typetext != "":
            type_pos = (self.Pos.x + (self.Size[0] - type_size[0]) // 2 + 1,
                        self.Pos.y + (self.Size[1] - type_size[1]) // 2)
            dc.DrawText(typetext, type_pos[0], type_pos[1])
        # Draw input and output connectors
        self.Input.Draw(dc)
        self.Output.Draw(dc)

        if not getattr(dc, "printing", False):
            for name, highlights in self.Highlights.iteritems():
                if name == "reference":
                    DrawHighlightedText(dc, self.Name, highlights, name_pos[0], name_pos[1])
                elif typetext != "":
                    DrawHighlightedText(dc, typetext, highlights, type_pos[0], type_pos[1])


# -------------------------------------------------------------------------------
#                         Ladder Diagram Coil
# -------------------------------------------------------------------------------


class LD_Coil(Graphic_Element):
    """
    Class that implements the graphic representation of a coil
    """

    # Create a new coil
    def __init__(self, parent, type, name, id=None):
        Graphic_Element.__init__(self, parent)
        self.Type = type
        self.Name = name
        self.Id = id
        self.Size = wx.Size(LD_ELEMENT_SIZE[0], LD_ELEMENT_SIZE[1])
        self.Highlights = {}
        # Create an input and output connector
        self.Input = Connector(self, "", "BOOL", wx.Point(0, self.Size[1] // 2 + 1), WEST)
        self.Output = Connector(self, "", "BOOL", wx.Point(self.Size[0], self.Size[1] // 2 + 1), EAST)
        self.Value = None
        self.PreviousValue = False
        self.RefreshNameSize()
        self.RefreshTypeSize()

    def Flush(self):
        if self.Input is not None:
            self.Input.Flush()
            self.Input = None
        if self.Output is not None:
            self.Output.Flush()
            self.Output = None

    def SpreadCurrent(self):
        if self.Parent.Debug:
            self.PreviousValue = self.Value
            self.Value = self.Input.ReceivingCurrent()
            if self.Value and not self.PreviousValue:
                self.Output.SpreadCurrent(True)
            elif not self.Value and self.PreviousValue:
                self.Output.SpreadCurrent(False)
            if self.Value != self.PreviousValue and self.Visible:
                self.Parent.ElementNeedRefresh(self)

    # Make a clone of this LD_Coil
    def Clone(self, parent, id=None, pos=None):
        coil = LD_Coil(parent, self.Type, self.Name, id)
        coil.SetSize(self.Size[0], self.Size[1])
        if pos is not None:
            coil.SetPosition(pos.x, pos.y)
        else:
            coil.SetPosition(self.Pos.x, self.Pos.y)
        coil.Input = self.Input.Clone(coil)
        coil.Output = self.Output.Clone(coil)
        return coil

    def GetConnectorTranslation(self, element):
        return {self.Input: element.Input, self.Output: element.Output}

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        rect = rect.Union(self.Input.GetRedrawRect(movex, movey))
        rect = rect.Union(self.Output.GetRedrawRect(movex, movey))
        if movex != 0 or movey != 0:
            if self.Input.IsConnected():
                rect = rect.Union(self.Input.GetConnectedRedrawRect(movex, movey))
            if self.Output.IsConnected():
                rect = rect.Union(self.Output.GetConnectedRedrawRect(movex, movey))
        return rect

    def ProcessDragging(self, movex, movey, event, scaling):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE:
            movex = movey = 0
        return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling, height_fac=2)

    # Forbids to change the Coil size
    def SetSize(self, width, height):
        if self.Parent.GetDrawingMode() == FREEDRAWING_MODE:
            Graphic_Element.SetSize(self, width, height)
            self.RefreshConnectors()

    # Delete this coil by calling the appropriate method
    def Delete(self):
        self.Parent.DeleteCoil(self)

    # Unconnect input and output
    def Clean(self):
        self.Input.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)
        self.Output.UnConnect(delete=self.Parent.GetDrawingMode() == FREEDRAWING_MODE)

    # Refresh the size of text for name
    def RefreshNameSize(self):
        if self.Name != "":
            self.NameSize = self.Parent.GetTextExtent(self.Name)
        else:
            self.NameSize = 0, 0

    # Refresh the size of text for type
    def RefreshTypeSize(self):
        typetext = ""
        if self.Type == COIL_REVERSE:
            typetext = "/"
        elif self.Type == COIL_SET:
            typetext = "S"
        elif self.Type == COIL_RESET:
            typetext = "R"
        elif self.Type == COIL_RISING:
            typetext = "P"
        elif self.Type == COIL_FALLING:
            typetext = "N"
        if typetext != "":
            self.TypeSize = self.Parent.GetTextExtent(typetext)
        else:
            self.TypeSize = 0, 0

    # Refresh the coil bounding box
    def RefreshBoundingBox(self):
        # Calculate the size of the name outside the coil
        text_width, text_height = self.Parent.GetTextExtent(self.Name)
        # Calculate the bounding box size
        if self.Name != "":
            bbx_x = self.Pos.x - max(0, (text_width - self.Size[0]) // 2)
            bbx_width = max(self.Size[0], text_width)
            bbx_y = self.Pos.y - (text_height + 2)
            bbx_height = self.Size[1] + (text_height + 2)
        else:
            bbx_x = self.Pos.x
            bbx_width = self.Size[0]
            bbx_y = self.Pos.y
            bbx_height = self.Size[1]
        self.BoundingBox = wx.Rect(bbx_x, bbx_y, bbx_width + 1, bbx_height + 1)

    # Returns the block minimum size
    def GetMinSize(self):
        return LD_ELEMENT_SIZE

    # Refresh the position of wire connected to coil
    def RefreshConnected(self, exclude=None):
        self.Input.MoveConnected(exclude)
        self.Output.MoveConnected(exclude)

    # Returns the coil connector that starts with the point given if it exists
    def GetConnector(self, position, name=None):
        # if a name is given
        if name is not None:
            # Test input and output connector
            # if self.Input and name == self.Input.GetName():
            #    return self.Input
            if self.Output and name == self.Output.GetName():
                return self.Output
        return self.FindNearestConnector(position, [self.Input, self.Output])

    # Returns input and output coil connectors
    def GetConnectors(self):
        return {"inputs": [self.Input], "outputs": [self.Output]}

    # Test if point given is on coil input or output connector
    def TestConnector(self, pt, direction=None, exclude=True):
        # Test input connector
        if self.Input.TestPoint(pt, direction, exclude):
            return self.Input
        # Test output connector
        if self.Output.TestPoint(pt, direction, exclude):
            return self.Output
        return None

    # Refresh the positions of the block connectors
    def RefreshConnectors(self):
        scaling = self.Parent.GetScaling()
        position = self.Size[1] // 2 + 1
        if scaling is not None:
            position = round((self.Pos.y + position) / scaling[1]) * scaling[1] - self.Pos.y
        self.Input.SetPosition(wx.Point(0, position))
        self.Output.SetPosition(wx.Point(self.Size[0], position))
        self.RefreshConnected()

    # Changes the coil name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    # Returns the coil name
    def GetName(self):
        return self.Name

    # Changes the coil type
    def SetType(self, type):
        self.Type = type
        self.RefreshTypeSize()

    # Returns the coil type
    def GetType(self):
        return self.Type

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the coil properties
        self.Parent.EditCoilContent(self)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the default menu
        self.Parent.PopupDefaultMenu()

    # Refreshes the coil model
    def RefreshModel(self, move=True):
        self.Parent.RefreshCoilModel(self)
        # If coil has moved, refresh the model of wires connected to output
        if move:
            self.Output.RefreshWires()

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        dc.SetPen(MiterPen(HIGHLIGHTCOLOR, (3 * scalex + 5), wx.SOLID))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.AND)
        # Draw a two circle arcs for representing the coil
        dc.DrawEllipticArc(round(self.Pos.x * scalex),
                           round((self.Pos.y - int(self.Size[1] * (sqrt(2) - 1.) / 2.) + 1) * scaley),
                           round(self.Size[0] * scalex),
                           round((int(self.Size[1] * sqrt(2)) - 1) * scaley),
                           135, 225)
        dc.DrawEllipticArc(round(self.Pos.x * scalex),
                           round((self.Pos.y - int(self.Size[1] * (sqrt(2) - 1.) / 2.) + 1) * scaley),
                           round(self.Size[0] * scalex),
                           round((int(self.Size[1] * sqrt(2)) - 1) * scaley),
                           -45, 45)
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Adds an highlight to the connection
    def AddHighlight(self, infos, start, end, highlight_type):
        highlights = self.Highlights.setdefault(infos[0], [])
        if infos[0] == "reference":
            if start[0] == 0 and end[0] == 0:
                AddHighlight(highlights, (start, end, highlight_type))
        else:
            AddHighlight(highlights, ((0, 0), (0, 1), highlight_type))

    # Removes an highlight from the connection
    def RemoveHighlight(self, infos, start, end, highlight_type):
        highlights = self.Highlights.get(infos[0], [])
        if RemoveHighlight(highlights, (start, end, highlight_type)) and len(highlights) == 0:
            self.Highlights.pop(infos[0])

    # Removes all the highlights of one particular type from the connection
    def ClearHighlight(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = {}
        else:
            highlight_items = self.Highlights.items()
            for name, highlights in highlight_items:
                highlights = ClearHighlights(highlights, highlight_type)
                if len(highlights) == 0:
                    self.Highlights.pop(name)

    # Draws coil
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if self.Value is not None and self.Value:
            dc.SetPen(MiterPen(wx.GREEN, 2, wx.SOLID))
        else:
            dc.SetPen(MiterPen(wx.BLACK, 2, wx.SOLID))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        # Compiling coil type modifier symbol
        typetext = ""
        if self.Type == COIL_REVERSE:
            typetext = "/"
        elif self.Type == COIL_SET:
            typetext = "S"
        elif self.Type == COIL_RESET:
            typetext = "R"
        elif self.Type == COIL_RISING:
            typetext = "P"
        elif self.Type == COIL_FALLING:
            typetext = "N"

        if getattr(dc, "printing", False) and not isinstance(dc, wx.PostScriptDC):
            # Draw an clipped ellipse for representing the coil
            clipping_box = dc.GetClippingBox()
            dc.SetClippingRegion(self.Pos.x - 1, self.Pos.y, self.Size[0] + 2, self.Size[1] + 1)
            dc.DrawEllipse(self.Pos.x, self.Pos.y - int(self.Size[1] * (sqrt(2) - 1.) / 2.) + 1, self.Size[0], int(self.Size[1] * sqrt(2)) - 1)
            dc.DestroyClippingRegion()
            if clipping_box != (0, 0, 0, 0):
                dc.SetClippingRegion(*clipping_box)
            name_size = dc.GetTextExtent(self.Name)
            if typetext != "":
                type_size = dc.GetTextExtent(typetext)
        else:
            # Draw a two ellipse arcs for representing the coil
            dc.DrawEllipticArc(self.Pos.x, self.Pos.y - int(self.Size[1] * (sqrt(2) - 1.) / 2.) + 1, self.Size[0], int(self.Size[1] * sqrt(2)) - 1, 135, 225)
            dc.DrawEllipticArc(self.Pos.x, self.Pos.y - int(self.Size[1] * (sqrt(2) - 1.) / 2.) + 1, self.Size[0], int(self.Size[1] * sqrt(2)) - 1, -45, 45)
            # Draw a point to avoid hole in left arc
            if not getattr(dc, "printing", False):
                if self.Value is not None and self.Value:
                    dc.SetPen(MiterPen(wx.GREEN))
                else:
                    dc.SetPen(MiterPen(wx.BLACK))
                dc.DrawPoint(self.Pos.x + 1, self.Pos.y + self.Size[1] // 2 + 1)
            name_size = self.NameSize
            if typetext != "":
                type_size = self.TypeSize

        # Draw coil name
        name_pos = (self.Pos.x + (self.Size[0] - name_size[0]) // 2,
                    self.Pos.y - (name_size[1] + 2))
        dc.DrawText(self.Name, name_pos[0], name_pos[1])
        # Draw the modifier symbol in the middle of coil
        if typetext != "":
            type_pos = (self.Pos.x + (self.Size[0] - type_size[0]) // 2 + 1,
                        self.Pos.y + (self.Size[1] - type_size[1]) // 2)
            dc.DrawText(typetext, type_pos[0], type_pos[1])
        # Draw input and output connectors
        self.Input.Draw(dc)
        self.Output.Draw(dc)

        if not getattr(dc, "printing", False):
            for name, highlights in self.Highlights.iteritems():
                if name == "reference":
                    DrawHighlightedText(dc, self.Name, highlights, name_pos[0], name_pos[1])
                elif typetext != "":
                    DrawHighlightedText(dc, typetext, highlights, type_pos[0], type_pos[1])
