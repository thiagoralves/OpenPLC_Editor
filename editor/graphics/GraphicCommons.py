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
from math import *
from future.builtins import round
from six import string_types
from six.moves import xrange

import wx
from graphics.ToolTipProducer import ToolTipProducer
from graphics.DebugDataConsumer import DebugDataConsumer

# -------------------------------------------------------------------------------
#                               Common constants
#
#            Definition of constants for dimensions of graphic elements
# -------------------------------------------------------------------------------

# FBD and SFC constants
MIN_MOVE = 5                            # Minimum move before starting a element dragging
CONNECTOR_SIZE = 8                      # Size of connectors
BLOCK_LINE_SIZE = 20                    # Minimum size of each line in a block
HANDLE_SIZE = 6                         # Size of the squares for handles
ANCHOR_DISTANCE = 5                     # Distance where wire is automativally attached to a connector
POINT_RADIUS = 2                        # Radius of the point of wire ends
MIN_SEGMENT_SIZE = 2                    # Minimum size of the endling segments of a wire

# LD constants
LD_LINE_SIZE = 40                       # Distance between two lines in a ladder rung
LD_ELEMENT_SIZE = (21, 15)              # Size (width, height) of a ladder element (contact or coil)
LD_WIRE_SIZE = 30                       # Size of a wire between two contact
LD_WIRECOIL_SIZE = 70                   # Size of a wire between a coil and a contact
LD_POWERRAIL_WIDTH = 3                  # Width of a Powerrail
LD_OFFSET = (10, 10)                    # Distance (x, y) between each comment and rung of the ladder
LD_COMMENT_DEFAULTSIZE = (600, 40)      # Size (width, height) of a comment box

# SFC constants
SFC_STEP_DEFAULT_SIZE = (40, 30)        # Default size of a SFC step
SFC_TRANSITION_SIZE = (20, 2)           # Size of a SFC transition
SFC_DEFAULT_SEQUENCE_INTERVAL = 40      # Default size of the interval between two divergence branches
SFC_SIMULTANEOUS_SEQUENCE_EXTRA = 20    # Size of extra lines for simultaneous divergence and convergence
SFC_JUMP_SIZE = (12, 13)                # Size of a SFC jump to step
SFC_WIRE_MIN_SIZE = 25                  # Size of a wire between two elements
SFC_ACTION_MIN_SIZE = (100, 30)         # Minimum size of an action block line

# Type definition constants for graphic elements
[INPUT, OUTPUT, INOUT] = range(3)
[CONNECTOR, CONTINUATION] = range(2)
[LEFTRAIL, RIGHTRAIL] = range(2)
[CONTACT_NORMAL, CONTACT_REVERSE, CONTACT_RISING, CONTACT_FALLING] = range(4)
[COIL_NORMAL, COIL_REVERSE, COIL_SET, COIL_RESET, COIL_RISING, COIL_FALLING] = range(6)
[SELECTION_DIVERGENCE, SELECTION_CONVERGENCE, SIMULTANEOUS_DIVERGENCE, SIMULTANEOUS_CONVERGENCE] = range(4)

# Constants for defining the type of dragging that has been selected
[HANDLE_MOVE, HANDLE_RESIZE, HANDLE_POINT, HANDLE_SEGMENT, HANDLE_CONNECTOR] = range(5)

# List of value for resize handle that are valid
VALID_HANDLES = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 2), (3, 1), (2, 1)]

# Contants for defining the direction of a connector
[EAST, NORTH, WEST, SOUTH] = [(1, 0), (0, -1), (-1, 0), (0, 1)]

# Contants for defining which mode is selected for each view
[MODE_SELECTION, MODE_BLOCK, MODE_VARIABLE, MODE_CONNECTION, MODE_COMMENT,
 MODE_COIL, MODE_CONTACT, MODE_POWERRAIL, MODE_INITIALSTEP, MODE_STEP,
 MODE_TRANSITION, MODE_DIVERGENCE, MODE_JUMP, MODE_ACTION, MODE_MOTION] = range(15)

# Contants for defining alignment types for graphic group
[ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT, ALIGN_TOP, ALIGN_MIDDLE, ALIGN_BOTTOM] = range(6)

# Contants for defining which drawing mode is selected for app
[FREEDRAWING_MODE, DRIVENDRAWING_MODE] = [1, 2]

# Color for Highlighting
HIGHLIGHTCOLOR = wx.CYAN

# Define highlight types
ERROR_HIGHLIGHT = (wx.Colour(255, 255, 0), wx.RED)
SEARCH_RESULT_HIGHLIGHT = (wx.Colour(255, 165, 0), wx.WHITE)

# Define highlight refresh inhibition period in second
REFRESH_HIGHLIGHT_PERIOD = 0.1

HANDLE_CURSORS = {
    (1, 1): 2,
    (3, 3): 2,
    (1, 3): 3,
    (3, 1): 3,
    (1, 2): 4,
    (3, 2): 4,
    (2, 1): 5,
    (2, 3): 5
}


def round_scaling(x, n, constraint=0):
    fraction = x / n
    if constraint == -1:
        xround = int(fraction)
    else:
        xround = round(fraction)
        if constraint == 1 and xround < fraction:
            xround += 1
    return int(xround * n)


# -------------------------------------------------------------------------------
# Basic vector operations for calculate wire points
# -------------------------------------------------------------------------------

def vector(p1, p2, normal=True):
    """
    Create a vector from two points and define if vector must be normal
    """
    vector = (p2.x - p1.x, p2.y - p1.y)
    if normal:
        return normalize(vector)
    return vector


def norm(v):
    """
    Calculate the norm of a given vector
    """
    return sqrt(v[0] * v[0] + v[1] * v[1])


def normalize(v):
    """
    Normalize a given vector
    """
    v_norm = norm(v)
    # Verifie if it is not a null vector
    if v_norm > 0:
        return (v[0] / v_norm, v[1] / v_norm)
    else:
        return v


def is_null_vector(v):
    """
    Calculate the scalar product of two vectors
    """
    return v == (0, 0)


def add_vectors(v1, v2):
    """
    Calculate the scalar product of two vectors
    """
    return (v1[0] + v2[0], v1[1] + v2[1])


def product(v1, v2):
    """
    Calculate the scalar product of two vectors
    """
    return v1[0] * v2[0] + v1[1] * v2[1]


def GetScaledEventPosition(event, dc, scaling):
    """
    Function that calculates the nearest point of the grid defined by scaling for the given point
    """
    pos = event.GetLogicalPosition(dc)
    if scaling:
        pos.x = round(pos.x / scaling[0]) * scaling[0]
        pos.y = round(pos.y / scaling[1]) * scaling[1]
    return pos


def DirectionChoice(v_base, v_target, dir_target):
    """
    Function that choose a direction during the wire points generation
    """
    dir_product = product(v_base, v_target)
    if dir_product < 0:
        return (-v_base[0], -v_base[1])
    elif dir_product == 0 and product(v_base, dir_target) != 0:
        return dir_target
    return v_base


def MiterPen(colour, width=1, style=wx.SOLID):
    pen = wx.Pen(colour, width, style)
    pen.SetJoin(wx.JOIN_MITER)
    pen.SetCap(wx.CAP_PROJECTING)
    return pen


# -------------------------------------------------------------------------------
#                    Helpers for highlighting text
# -------------------------------------------------------------------------------


def AddHighlight(highlights, infos):
    RemoveHighlight(highlights, infos)
    highlights.append(infos)


def RemoveHighlight(highlights, infos):
    if infos in highlights:
        highlights.remove(infos)
        return True
    return False


def ClearHighlights(highlights, highlight_type=None):
    if highlight_type is not None:
        return [highlight for highlight in highlights if highlight[2] != highlight_type]
    return []


def DrawHighlightedText(dc, text, highlights, x, y):
    current_pen = dc.GetPen()
    dc.SetPen(wx.TRANSPARENT_PEN)
    for start, end, highlight_type in highlights:
        dc.SetBrush(wx.Brush(highlight_type[0]))
        offset_width, _offset_height = dc.GetTextExtent(text[:start[1]])
        part = text[start[1]:end[1] + 1]
        part_width, part_height = dc.GetTextExtent(part)
        dc.DrawRectangle(x + offset_width, y, part_width, part_height)
        dc.SetTextForeground(highlight_type[1])
        dc.DrawText(part, x + offset_width, y)
    dc.SetPen(current_pen)
    dc.SetTextForeground(wx.BLACK)


# -------------------------------------------------------------------------------
#                           Graphic element base class
# -------------------------------------------------------------------------------


class Graphic_Element(ToolTipProducer):
    """
    Class that implements a generic graphic element
    """

    # Create a new graphic element
    def __init__(self, parent, id=None):
        ToolTipProducer.__init__(self, parent)
        self.Parent = parent
        self.Id = id
        self.oldPos = None
        self.StartPos = None
        self.CurrentDrag = None
        self.Handle = (None, None)
        self.Dragging = False
        self.Selected = False
        self.Highlighted = False
        self.Pos = wx.Point(0, 0)
        self.Size = wx.Size(0, 0)
        self.BoundingBox = wx.Rect(0, 0, 0, 0)
        self.Visible = False

    def GetDefinition(self):
        return [self.Id], []

    def TestVisible(self, screen):
        self.Visible = self.Selected or self.GetRedrawRect().Intersects(screen)

    def IsVisible(self):
        return self.Visible

    def SpreadCurrent(self):
        pass

    def GetConnectorTranslation(self, element):
        return {}

    def FindNearestConnector(self, position, connectors):
        distances = []
        for connector in connectors:
            connector_pos = connector.GetRelPosition()
            distances.append((sqrt((self.Pos.x + connector_pos.x - position.x) ** 2 +
                                   (self.Pos.y + connector_pos.y - position.y) ** 2),
                              connector))
        distances.sort()
        if len(distances) > 0:
            return distances[0][1]
        return None

    def IsOfType(self, type, reference):
        return self.Parent.IsOfType(type, reference)

    def IsEndType(self, type):
        return self.Parent.IsEndType(type)

    def GetDragging(self):
        return self.Dragging

    # Make a clone of this element
    def Clone(self, parent):
        return Graphic_Element(parent, self.Id)

    # Changes the block position
    def SetPosition(self, x, y):
        self.Pos.x = x
        self.Pos.y = y
        self.RefreshConnected()
        self.RefreshBoundingBox()

    # Returns the block position
    def GetPosition(self):
        return self.Pos.x, self.Pos.y

    # Changes the element size
    def SetSize(self, width, height):
        self.Size.SetWidth(width)
        self.Size.SetHeight(height)
        self.RefreshConnectors()
        self.RefreshBoundingBox()

    # Returns the element size
    def GetSize(self):
        return self.Size.GetWidth(), self.Size.GetHeight()

    # Returns the minimum element size
    def GetMinSize(self):
        return 0, 0

    # Set size of the element to the minimum size
    def SetBestSize(self, scaling, x_factor=0.5, y_factor=0.5):
        width, height = self.GetSize()
        posx, posy = self.GetPosition()
        min_width, min_height = self.GetMinSize()
        if width < min_width:
            self.Pos.x = max(0, self.Pos.x - (width - min_width) * x_factor)
            width = min_width
        if height < min_height:
            self.Pos.y = max(0, self.Pos.y - (height - min_height) * y_factor)
            height = min_height
        if scaling is not None:
            self.Pos.x = round_scaling(self.Pos.x, scaling[0])
            self.Pos.y = round_scaling(self.Pos.y, scaling[1])
            width = round_scaling(width, scaling[0], 1)
            height = round_scaling(height, scaling[1], 1)
        self.SetSize(width, height)
        return self.Pos.x - posx, self.Pos.y - posy

    # Refresh the element connectors position
    def RefreshConnectors(self):
        pass

    # Refresh the position of wires connected to element inputs and outputs
    def RefreshConnected(self, exclude=None):
        pass

    # Change the parent
    def SetParent(self, parent):
        self.Parent = parent

    # Override this method for defining the method to call for deleting this element
    def Delete(self):
        pass

    # Returns the Id
    def GetId(self):
        return self.Id

    # Returns if the point given is in the bounding box
    def HitTest(self, pt, connectors=True):
        if connectors:
            rect = self.BoundingBox
        else:
            rect = wx.Rect(self.Pos.x, self.Pos.y, self.Size[0], self.Size[1])
        return rect.InsideXY(pt.x, pt.y)

    # Returns if the point given is in the bounding box
    def IsInSelection(self, rect):
        return rect.InsideXY(self.BoundingBox.x, self.BoundingBox.y) and rect.InsideXY(self.BoundingBox.x + self.BoundingBox.width, self.BoundingBox.y + self.BoundingBox.height)

    # Override this method for refreshing the bounding box
    def RefreshBoundingBox(self):
        pass

    # Returns the bounding box
    def GetBoundingBox(self):
        return self.BoundingBox

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        scalex, scaley = self.Parent.GetViewScale()
        rect = wx.Rect()
        rect.x = self.BoundingBox.x - int(HANDLE_SIZE / scalex) - 3 - abs(movex)
        rect.y = self.BoundingBox.y - int(HANDLE_SIZE / scaley) - 3 - abs(movey)
        rect.width = self.BoundingBox.width + 2 * (int(HANDLE_SIZE / scalex) + abs(movex) + 1) + 4
        rect.height = self.BoundingBox.height + 2 * (int(HANDLE_SIZE / scaley) + abs(movey) + 1) + 4
        return rect

    def Refresh(self, rect=None):
        if self.Visible:
            if rect is not None:
                self.Parent.RefreshRect(self.Parent.GetScrolledRect(rect), False)
            else:
                self.Parent.RefreshRect(self.Parent.GetScrolledRect(self.GetRedrawRect()), False)

    # Change the variable that indicates if this element is selected
    def SetSelected(self, selected):
        self.Selected = selected
        self.Refresh()

    # Change the variable that indicates if this element is highlighted
    def SetHighlighted(self, highlighted):
        self.Highlighted = highlighted
        self.Refresh()

    # Test if the point is on a handle of this element
    def TestHandle(self, event):
        dc = self.Parent.GetLogicalDC()
        scalex, scaley = dc.GetUserScale()
        pos = event.GetPosition()
        pt = wx.Point(*self.Parent.CalcUnscrolledPosition(pos.x, pos.y))

        left = (self.BoundingBox.x - 2) * scalex - HANDLE_SIZE
        center = (self.BoundingBox.x + self.BoundingBox.width // 2) * scalex - HANDLE_SIZE // 2
        right = (self.BoundingBox.x + self.BoundingBox.width + 2) * scalex

        top = (self.BoundingBox.y - 2) * scaley - HANDLE_SIZE
        middle = (self.BoundingBox.y + self.BoundingBox.height / 2) * scaley - HANDLE_SIZE // 2
        bottom = (self.BoundingBox.y + self.BoundingBox.height + 2) * scaley

        extern_rect = wx.Rect(left, top, right + HANDLE_SIZE - left, bottom + HANDLE_SIZE - top)
        intern_rect = wx.Rect(left + HANDLE_SIZE, top + HANDLE_SIZE, right - left - HANDLE_SIZE, bottom - top - HANDLE_SIZE)

        # Verify that this element is selected
        if self.Selected and extern_rect.InsideXY(pt.x, pt.y) and not intern_rect.InsideXY(pt.x, pt.y):
            # Find if point is on a handle horizontally
            if left <= pt.x < left + HANDLE_SIZE:
                handle_x = 1
            elif center <= pt.x < center + HANDLE_SIZE:
                handle_x = 2
            elif right <= pt.x < right + HANDLE_SIZE:
                handle_x = 3
            else:
                handle_x = 0
            # Find if point is on a handle vertically
            if top <= pt.y < top + HANDLE_SIZE:
                handle_y = 1
            elif middle <= pt.y < middle + HANDLE_SIZE:
                handle_y = 2
            elif bottom <= pt.y < bottom + HANDLE_SIZE:
                handle_y = 3
            else:
                handle_y = 0
            # Verify that the result is valid
            if (handle_x, handle_y) in VALID_HANDLES:
                return handle_x, handle_y
        return 0, 0

    # Method called when a LeftDown event have been generated
    def OnLeftDown(self, event, dc, scaling):
        # Test if an handle have been clicked
        handle = self.TestHandle(event)
        # Find which type of handle have been clicked,
        # Save a resize event and change the cursor
        cursor = HANDLE_CURSORS.get(handle, 1)
        wx.CallAfter(self.Parent.SetCurrentCursor, cursor)
        if cursor > 1:
            self.Handle = (HANDLE_RESIZE, handle)
        else:
            self.Handle = (HANDLE_MOVE, None)
            self.SetSelected(False)
        # Initializes the last position
        self.oldPos = GetScaledEventPosition(event, dc, scaling)
        self.StartPos = wx.Point(self.Pos.x, self.Pos.y)
        self.CurrentDrag = wx.Point(0, 0)

    # Method called when a LeftUp event have been generated
    def OnLeftUp(self, event, dc, scaling):
        # If a dragging have been initiated
        if self.Dragging and self.oldPos:
            self.RefreshModel()
            self.Parent.RefreshBuffer()
        wx.CallAfter(self.Parent.SetCurrentCursor, 0)
        self.SetSelected(True)
        self.oldPos = None

    # Method called when a RightDown event have been generated
    def OnRightDown(self, event, dc, scaling):
        pass

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        if self.Dragging and self.oldPos:
            self.RefreshModel()
            self.Parent.RefreshBuffer()
        wx.CallAfter(self.Parent.SetCurrentCursor, 0)
        self.SetSelected(True)
        self.oldPos = None
        if self.Parent.Debug:
            self.Parent.PopupForceMenu()

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        pass

    # Method called when a Motion event have been generated
    def OnMotion(self, event, dc, scaling):
        # If the cursor is dragging and the element have been clicked
        if event.Dragging() and self.oldPos:
            # Calculate the movement of cursor
            pos = GetScaledEventPosition(event, dc, scaling)
            movex = pos.x - self.oldPos.x
            movey = pos.y - self.oldPos.y
            # If movement is greater than MIN_MOVE then a dragging is initiated
            if not self.Dragging and (abs(movex) > MIN_MOVE or abs(movey) > MIN_MOVE):
                self.Dragging = True
            # If a dragging have been initiated, refreshes the element state
            if self.Dragging:
                dragx, dragy = self.ProcessDragging(movex, movey, event, scaling)
                if event.ControlDown() and self.Handle[0] == HANDLE_MOVE:
                    self.oldPos.x = self.StartPos.x + self.CurrentDrag.x
                    self.oldPos.y = self.StartPos.y + self.CurrentDrag.y
                else:
                    self.oldPos.x += dragx
                    self.oldPos.y += dragy
                return dragx, dragy
            return movex, movey
        # If cursor just pass over the element, changes the cursor if it is on a handle
        else:
            pos = event.GetLogicalPosition(dc)
            handle = self.TestHandle(event)
            # Find which type of handle have been clicked,
            # Save a resize event and change the cursor
            cursor = HANDLE_CURSORS.get(handle, 0)
            wx.CallAfter(self.Parent.SetCurrentCursor, cursor)
            return 0, 0

    # Moves the element
    def Move(self, dx, dy, exclude=None):
        self.Pos.x += max(-self.BoundingBox.x, dx)
        self.Pos.y += max(-self.BoundingBox.y, dy)
        self.RefreshConnected(exclude)
        self.RefreshBoundingBox()

    # Resizes the element from position and size given
    def Resize(self, x, y, width, height):
        self.Move(x, y)
        self.SetSize(width, height)

    # Refreshes the element state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling, width_fac=1, height_fac=1):
        handle_type, handle = self.Handle
        # If it is a resize handle, calculate the values from resizing
        if handle_type == HANDLE_RESIZE:
            if scaling is not None:
                scaling = (scaling[0] * width_fac, scaling[1] * height_fac)
            x = y = start_x = start_y = 0
            width, height = start_width, start_height = self.GetSize()
            if handle[0] == 1:
                movex = max(-self.BoundingBox.x, movex)
                if scaling is not None:
                    movex = -(round_scaling(width - movex, scaling[0]) - width)
                x = movex
                if event.ShiftDown():
                    width -= 2 * movex
                else:
                    width -= movex
            elif handle[0] == 3:
                if scaling is not None:
                    movex = round_scaling(width + movex, scaling[0]) - width
                if event.ShiftDown():
                    movex = min(self.BoundingBox.x, movex)
                    x = -movex
                    width += 2 * movex
                else:
                    width += movex
            if handle[1] == 1:
                movey = max(-self.BoundingBox.y, movey)
                if scaling is not None:
                    movey = -(round_scaling(height - movey, scaling[1]) - height)
                y = movey
                if event.ShiftDown():
                    height -= 2 * movey
                else:
                    height -= movey
            elif handle[1] == 3:
                if scaling is not None:
                    movey = round_scaling(height + movey, scaling[1]) - height
                if event.ShiftDown():
                    movey = min(self.BoundingBox.y, movey)
                    y = -movey
                    height += 2 * movey
                else:
                    height += movey
            # Verify that new size is not lesser than minimum
            min_width, min_height = self.GetMinSize()
            if handle[0] != 2 and (width >= min_width or width > self.Size[0]):
                start_x = x
                start_width = width
            else:
                movex = 0
            if handle[1] != 2 and (height >= min_height or height > self.Size[1]):
                start_y = y
                start_height = height
            else:
                movey = 0
            if movex != 0 or movey != 0:
                self.Resize(start_x, start_y, start_width, start_height)
            return movex, movey
        # If it is a move handle, Move this element
        elif handle_type == HANDLE_MOVE:
            movex = max(-self.BoundingBox.x, movex)
            movey = max(-self.BoundingBox.y, movey)
            if scaling is not None:
                movex = round_scaling(self.Pos.x + movex, scaling[0]) - self.Pos.x
                movey = round_scaling(self.Pos.y + movey, scaling[1]) - self.Pos.y
            if event.ControlDown():
                self.CurrentDrag.x = self.CurrentDrag.x + movex
                self.CurrentDrag.y = self.CurrentDrag.y + movey
                if abs(self.CurrentDrag.x) > abs(self.CurrentDrag.y):
                    movex = self.StartPos.x + self.CurrentDrag.x - self.Pos.x
                    movey = self.StartPos.y - self.Pos.y
                else:
                    movex = self.StartPos.x - self.Pos.x
                    movey = self.StartPos.y + self.CurrentDrag.y - self.Pos.y
            self.Move(movex, movey)
            return movex, movey
        return 0, 0

    # Override this method for defining the method to call for adding an highlight to this element
    def AddHighlight(self, infos, start, end, highlight_type):
        pass

    # Override this method for defining the method to call for removing an highlight from this element
    def RemoveHighlight(self, infos, start, end, highlight_type):
        pass

    # Override this method for defining the method to call for removing all the highlights of one particular type from this element
    def ClearHighlight(self, highlight_type=None):
        pass

    # Override this method for defining the method to call for refreshing the model of this element
    def RefreshModel(self, move=True):
        pass

    # Draws the highlightment of this element if it is highlighted (can be overwritten)
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        dc.SetPen(MiterPen(HIGHLIGHTCOLOR))
        dc.SetBrush(wx.Brush(HIGHLIGHTCOLOR))
        dc.SetLogicalFunction(wx.AND)
        dc.DrawRectangle(int(round((self.Pos.x - 1) * scalex)) - 2,
                         int(round((self.Pos.y - 1) * scaley)) - 2,
                         int(round((self.Size.width + 3) * scalex)) + 5,
                         int(round((self.Size.height + 3) * scaley)) + 5)
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Draws the handles of this element if it is selected
    def Draw(self, dc):
        if not getattr(dc, "printing", False):
            if self.Highlighted:
                self.DrawHighlightment(dc)
            if self.Selected:
                scalex, scaley = dc.GetUserScale()
                dc.SetUserScale(1, 1)
                dc.SetPen(MiterPen(wx.BLACK))
                dc.SetBrush(wx.BLACK_BRUSH)

                left = (self.BoundingBox.x - 2) * scalex - HANDLE_SIZE
                center = (self.BoundingBox.x + self.BoundingBox.width // 2) * scalex - HANDLE_SIZE // 2
                right = (self.BoundingBox.x + self.BoundingBox.width + 2) * scalex

                top = (self.BoundingBox.y - 2) * scaley - HANDLE_SIZE
                middle = (self.BoundingBox.y + self.BoundingBox.height // 2) * scaley - HANDLE_SIZE // 2
                bottom = (self.BoundingBox.y + self.BoundingBox.height + 2) * scaley

                for x, y in [(left, top), (center, top), (right, top),
                             (left, middle), (right, middle),
                             (left, bottom), (center, bottom), (right, bottom)]:
                    dc.DrawRectangle(x, y, HANDLE_SIZE, HANDLE_SIZE)

                dc.SetUserScale(scalex, scaley)


# -------------------------------------------------------------------------------
#                           Group of graphic elements
# -------------------------------------------------------------------------------


class Graphic_Group(Graphic_Element):
    """
    Class that implements a group of graphic elements
    """

    # Create a new group of graphic elements
    def __init__(self, parent):
        Graphic_Element.__init__(self, parent)
        self.Elements = []
        self.RefreshWireExclusion()
        self.RefreshBoundingBox()

    # Destructor
    def __del__(self):
        self.Elements = []

    def GetDefinition(self):
        blocks = []
        wires = []
        for element in self.Elements:
            block, wire = element.GetDefinition()
            blocks.extend(block)
            wires.extend(wire)
        return blocks, wires

    # Make a clone of this element
    def Clone(self, parent, pos=None):
        group = Graphic_Group(parent)
        connectors = {}
        exclude_names = {}
        wires = []
        if pos is not None:
            dx, dy = pos.x - self.BoundingBox.x, pos.y - self.BoundingBox.y
        for element in self.Elements:
            if isinstance(element, Wire):
                wires.append(element)
            else:
                if pos is not None:
                    x, y = element.GetPosition()
                    new_pos = wx.Point(x + dx, y + dy)
                    newid = parent.GetNewId()
                    if parent.IsNamedElement(element):
                        name = parent.GenerateNewName(element, exclude_names)
                        exclude_names[name.upper()] = True
                        new_element = element.Clone(parent, newid, name, pos=new_pos)
                    else:
                        new_element = element.Clone(parent, newid, pos=new_pos)
                    new_element.SetBestSize(parent.Scaling)
                else:
                    new_element = element.Clone(parent)
                connectors.update(element.GetConnectorTranslation(new_element))
                group.SelectElement(new_element)
        for element in wires:
            if pos is not None:
                new_wire = element.Clone(parent, connectors, dx, dy)
            else:
                new_wire = element.Clone(parent, connectors)
            if new_wire is not None:
                if pos is not None:
                    parent.AddWire(new_wire)
                group.SelectElement(new_wire)
        if pos is not None:
            for element in group.Elements:
                if not isinstance(element, Wire):
                    parent.AddBlockInModel(element)
        return group

    def CanAddBlocks(self, parent):
        valid = True
        for element in self.Elements:
            if not isinstance(element, Wire):
                valid &= parent.CanAddElement(element)
        return valid

    def IsVisible(self):
        for element in self.Elements:
            if element.IsVisible():
                return True
        return False

    # Refresh the list of wire excluded
    def RefreshWireExclusion(self):
        self.WireExcluded = []
        for element in self.Elements:
            if isinstance(element, Wire):
                startblock = element.StartConnected.GetParentBlock()
                endblock = element.EndConnected.GetParentBlock()
                if startblock in self.Elements and endblock in self.Elements:
                    self.WireExcluded.append(element)

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = None
        for element in self.Elements:
            if rect is None:
                rect = element.GetRedrawRect(movex, movey)
            else:
                rect = rect.Union(element.GetRedrawRect(movex, movey))
        return rect

    # Clean this group of elements
    def Clean(self):
        # Clean all the elements of the group
        for element in self.Elements:
            element.Clean()

    # Delete this group of elements
    def Delete(self):
        # Delete all the elements of the group
        for element in self.Elements:
            element.Delete()
        self.WireExcluded = []

    # Returns if the point given is in the bounding box of one of the elements of this group
    def HitTest(self, pt, connectors=True):
        result = False
        for element in self.Elements:
            result |= element.HitTest(pt, connectors)
        return result

    # Returns if the element given is in this group
    def IsElementIn(self, element):
        return element in self.Elements

    # Change the elements of the group
    def SetElements(self, elements):
        self.Elements = elements
        self.RefreshWireExclusion()
        self.RefreshBoundingBox()

    # Returns the elements of the group
    def GetElements(self):
        return self.Elements

    # Align the group elements
    def AlignElements(self, horizontally, vertically):
        minx = self.BoundingBox.x + self.BoundingBox.width
        miny = self.BoundingBox.y + self.BoundingBox.height
        maxx = self.BoundingBox.x
        maxy = self.BoundingBox.y
        for element in self.Elements:
            if not isinstance(element, Wire):
                posx, posy = element.GetPosition()
                width, height = element.GetSize()
                minx = min(minx, posx)
                miny = min(miny, posy)
                maxx = max(maxx, posx + width)
                maxy = max(maxy, posy + height)
        for element in self.Elements:
            if not isinstance(element, Wire):
                posx, posy = element.GetPosition()
                width, height = element.GetSize()
                movex = movey = 0
                if horizontally == ALIGN_LEFT:
                    movex = minx - posx
                elif horizontally == ALIGN_CENTER:
                    movex = (maxx + minx - width) // 2 - posx
                elif horizontally == ALIGN_RIGHT:
                    movex = maxx - width - posx
                if vertically == ALIGN_TOP:
                    movey = miny - posy
                elif vertically == ALIGN_MIDDLE:
                    movey = (maxy + miny - height) // 2 - posy
                elif vertically == ALIGN_BOTTOM:
                    movey = maxy - height - posy
                if movex != 0 or movey != 0:
                    element.Move(movex, movey)
                    element.RefreshModel()
        self.RefreshBoundingBox()

    # Add the given element to the group of elements
    def AddElement(self, element):
        self.Elements.append(element)

    # Remove or select the given element if it is or not in the group
    def SelectElement(self, element):
        if element in self.Elements:
            self.Elements.remove(element)
        else:
            self.Elements.append(element)
        self.RefreshWireExclusion()
        self.RefreshBoundingBox()

    # Move this group of elements
    def Move(self, movex, movey):
        movex = max(-self.BoundingBox.x, movex)
        movey = max(-self.BoundingBox.y, movey)
        # Move all the elements of the group
        for element in self.Elements:
            if not isinstance(element, Wire):
                element.Move(movex, movey, self.WireExcluded)
            elif element in self.WireExcluded:
                element.Move(movex, movey, True)
        self.RefreshBoundingBox()

    # Refreshes the bounding box of this group of elements
    def RefreshBoundingBox(self):
        if len(self.Elements) > 0:
            bbox = self.Elements[0].GetBoundingBox()
            minx, miny = bbox.x, bbox.y
            maxx = bbox.x + bbox.width
            maxy = bbox.y + bbox.height
            for element in self.Elements[1:]:
                bbox = element.GetBoundingBox()
                minx = min(minx, bbox.x)
                miny = min(miny, bbox.y)
                maxx = max(maxx, bbox.x + bbox.width)
                maxy = max(maxy, bbox.y + bbox.height)
            self.BoundingBox = wx.Rect(minx, miny, maxx - minx, maxy - miny)
        else:
            self.BoundingBox = wx.Rect(0, 0, 0, 0)
        self.Pos = wx.Point(self.BoundingBox.x, self.BoundingBox.y)
        self.Size = wx.Size(self.BoundingBox.width, self.BoundingBox.height)

    # Forbids to change the group position
    def SetPosition(self, x, y):
        pass

    # Returns the position of this group
    def GetPosition(self, exclude_wires=False):
        if exclude_wires:
            posx = posy = None
            for element in self.Elements:
                if not isinstance(element, Wire) or element in self.WireExcluded:
                    bbox = element.GetBoundingBox()
                    if posx is None and posy is None:
                        posx, posy = bbox.x, bbox.y
                    else:
                        posx = min(posx, bbox.x)
                        posy = min(posy, bbox.y)
            if posx is None and posy is None:
                return 0, 0
            return posx, posy
        return self.BoundingBox.x, self.BoundingBox.y

    # Forbids to change the group size
    def SetSize(self, width, height):
        pass

    # Returns the size of this group
    def GetSize(self):
        return self.BoundingBox.width, self.BoundingBox.height

    # Set size of the group elements to their minimum size
    def SetBestSize(self, scaling):
        max_movex = max_movey = 0
        for element in self.Elements:
            movex, movey = element.SetBestSize(scaling)
            max_movex = max(max_movex, movex)
            max_movey = max(max_movey, movey)
        return max_movex, max_movey

    # Refreshes the group elements to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        handle_type, _handle = self.Handle
        # If it is a move handle, Move this group elements
        if handle_type == HANDLE_MOVE:
            movex = max(-self.BoundingBox.x, movex)
            movey = max(-self.BoundingBox.y, movey)
            if scaling is not None:
                movex = round_scaling(movex, scaling[0])
                movey = round_scaling(movey, scaling[1])
            if event.ControlDown():
                self.CurrentDrag.x = self.CurrentDrag.x + movex
                self.CurrentDrag.y = self.CurrentDrag.y + movey
                posx, posy = self.GetPosition(True)
                if abs(self.CurrentDrag.x) > abs(self.CurrentDrag.y):
                    movex = self.StartPos.x + self.CurrentDrag.x - posx
                    movey = self.StartPos.y - posy
                else:
                    movex = self.StartPos.x - posx
                    movey = self.StartPos.y + self.CurrentDrag.y - posy
            self.Move(movex, movey)
            return movex, movey
        return 0, 0

    # Change the variable that indicates if this element is highlighted
    def SetHighlighted(self, highlighted):
        for element in self.Elements:
            element.SetHighlighted(highlighted)

    def HighlightPoint(self, pos):
        for element in self.Elements:
            if isinstance(element, Wire):
                element.HighlightPoint(pos)

    # Method called when a LeftDown event have been generated
    def OnLeftDown(self, event, dc, scaling):
        Graphic_Element.OnLeftDown(self, event, dc, scaling)
        self.StartPos = wx.Point(*self.GetPosition(True))
        for element in self.Elements:
            element.Handle = self.Handle

    # Change the variable that indicates if the elemente is selected
    def SetSelected(self, selected):
        for element in self.Elements:
            element.SetSelected(selected)

    # Method called when a RightUp event has been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the menu with special items for a group
        self.Parent.PopupGroupMenu()

    # Refreshes the model of all the elements of this group
    def RefreshModel(self, move=True):
        for element in self.Elements:
            element.RefreshModel(move)

    # Draws the handles of this element if it is selected
    def Draw(self, dc):
        for element in self.Elements:
            element.Draw(dc)


# -------------------------------------------------------------------------------
#                         Connector for all types of blocks
# -------------------------------------------------------------------------------


class Connector(DebugDataConsumer, ToolTipProducer):
    """
    Class that implements a connector for any type of block
    """

    # Create a new connector
    def __init__(self, parent, name, type, position, direction, negated=False, edge="none", onlyone=False):
        DebugDataConsumer.__init__(self)
        ToolTipProducer.__init__(self, parent.Parent)
        self.ParentBlock = parent
        self.Name = name
        self.Type = type
        self.Pos = position
        self.Direction = direction
        self.Wires = []
        if self.ParentBlock.IsOfType("BOOL", type):
            self.Negated = negated
            self.Edge = edge
        else:
            self.Negated = False
            self.Edge = "none"
        self.OneConnected = onlyone
        self.Valid = True
        self.Value = None
        self.Forced = False
        self.ValueSize = None
        self.ComputedValue = None
        self.Selected = False
        self.Highlights = []
        self.RefreshNameSize()

    def Flush(self):
        self.ParentBlock = None
        for wire, _handle in self.Wires:
            wire.Flush()
        self.Wires = []

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        parent_pos = self.ParentBlock.GetPosition()
        x = min(parent_pos[0] + self.Pos.x, parent_pos[0] + self.Pos.x + self.Direction[0] * CONNECTOR_SIZE)
        y = min(parent_pos[1] + self.Pos.y, parent_pos[1] + self.Pos.y + self.Direction[1] * CONNECTOR_SIZE)
        has_modifier = self.Negated or self.Edge != "none"
        if self.Direction[0] == 0:
            width = 10 if has_modifier else 5
        else:
            width = CONNECTOR_SIZE
            if self.Edge == "rising" and self.Direction[0] == 1:
                x -= 5
                width += 5
        if self.Direction[1] == 0:
            height = 10 if has_modifier else 5
        else:
            height = CONNECTOR_SIZE
            if self.Edge == "rising" and self.Direction[1] == 1:
                y -= 5
                height += 5
        rect = wx.Rect(x - abs(movex), y - abs(movey), width + 2 * abs(movex), height + 2 * abs(movey))
        if self.ValueSize is None and isinstance(self.ComputedValue, string_types):
            self.ValueSize = self.ParentBlock.Parent.GetMiniTextExtent(self.ComputedValue)
        if self.ValueSize is not None:
            width, height = self.ValueSize
            rect = rect.Union(
                wx.Rect(
                    parent_pos[0] + self.Pos.x + CONNECTOR_SIZE * self.Direction[0] +
                    width * (self.Direction[0] - 1) // 2,
                    parent_pos[1] + self.Pos.y + CONNECTOR_SIZE * self.Direction[1] +
                    height * (self.Direction[1] - 1),
                    width, height))
        return rect

    # Change the connector selection
    def SetSelected(self, selected):
        self.Selected = selected

    # Make a clone of the connector
    def Clone(self, parent=None):
        if parent is None:
            parent = self.ParentBlock
        return Connector(parent, self.Name, self.Type, wx.Point(self.Pos[0], self.Pos[1]),
                         self.Direction, self.Negated)

    # Returns the connector parent block
    def GetParentBlock(self):
        return self.ParentBlock

    # Returns the connector type
    def GetType(self, raw=False):
        if self.ParentBlock.IsEndType(self.Type) or raw:
            return self.Type
        elif (self.Negated or self.Edge != "none") and self.ParentBlock.IsOfType("BOOL", self.Type):
            return "BOOL"
        else:
            return self.ParentBlock.GetConnectionResultType(self, self.Type)

    # Returns the connector type
    def GetConnectedType(self):
        if self.ParentBlock.IsEndType(self.Type):
            return self.Type
        elif len(self.Wires) == 1:
            return self.Wires[0][0].GetOtherConnectedType(self.Wires[0][1])
        return self.Type

    # Returns the connector type
    def GetConnectedRedrawRect(self, movex, movey):
        rect = None
        for wire, _handle in self.Wires:
            if rect is None:
                rect = wire.GetRedrawRect()
            else:
                rect = rect.Union(wire.GetRedrawRect())
        return rect

    # Returns if connector type is compatible with type given
    def IsCompatible(self, type):
        reference = self.GetType()
        return self.ParentBlock.IsOfType(type, reference) or self.ParentBlock.IsOfType(reference, type)

    # Changes the connector name
    def SetType(self, type):
        self.Type = type
        for wire, _handle in self.Wires:
            wire.SetValid(wire.IsConnectedCompatible())

    # Returns the connector name
    def GetName(self):
        return self.Name

    # Changes the connector name
    def SetName(self, name):
        self.Name = name
        self.RefreshNameSize()

    def SetForced(self, forced):
        if self.Forced != forced:
            self.Forced = forced
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)

    def GetComputedValue(self):
        if self.Value is not None and self.Value != "undefined" and not isinstance(self.Value, bool):
            return self.Value
        return None

    def GetToolTipValue(self):
        return self.GetComputedValue()

    def SetValue(self, value):
        if self.Value != value:
            self.Value = value
            computed_value = self.GetComputedValue()
            if computed_value is not None:
                self.ComputedValue = computed_value
                self.SetToolTipText(self.ComputedValue)
                if len(self.ComputedValue) > 4:
                    self.ComputedValue = self.ComputedValue[:4] + "..."
            self.ValueSize = None
            if self.ParentBlock.Visible:
                self.ParentBlock.Parent.ElementNeedRefresh(self)

    def RefreshForced(self):
        self.Forced = False
        for wire, _handle in self.Wires:
            self.Forced |= wire.IsForced()

    def RefreshValue(self):
        self.Value = self.ReceivingCurrent()

    def RefreshValid(self):
        self.Valid = True
        for wire, _handle in self.Wires:
            self.Valid &= wire.GetValid()

    def ReceivingCurrent(self):
        current = False
        for wire, _handle in self.Wires:
            value = wire.GetValue()
            if current != "undefined" and isinstance(value, bool):
                current |= wire.GetValue()
            elif value == "undefined":
                current = "undefined"
        return current

    def SpreadCurrent(self, spreading):
        for wire, _handle in self.Wires:
            wire.SetValue(spreading)

    # Changes the connector name size
    def RefreshNameSize(self):
        if self.Name != "":
            self.NameSize = self.ParentBlock.Parent.GetTextExtent(self.Name)
        else:
            self.NameSize = 0, 0

    # Returns the connector name size
    def GetNameSize(self):
        return self.NameSize

    # Returns the wires connected to the connector
    def GetWires(self):
        return self.Wires

    # Returns the parent block Id
    def GetBlockId(self):
        return self.ParentBlock.GetId()

    # Returns the connector relative position
    def GetRelPosition(self):
        return self.Pos

    # Returns the connector absolute position
    def GetPosition(self, size=True):
        parent_pos = self.ParentBlock.GetPosition()
        # If the position of the end of the connector is asked
        if size:
            x = parent_pos[0] + self.Pos.x + self.Direction[0] * CONNECTOR_SIZE
            y = parent_pos[1] + self.Pos.y + self.Direction[1] * CONNECTOR_SIZE
        else:
            x = parent_pos[0] + self.Pos.x
            y = parent_pos[1] + self.Pos.y
        return wx.Point(x, y)

    # Change the connector relative position
    def SetPosition(self, pos):
        self.Pos = pos

    # Returns the connector direction
    def GetDirection(self):
        return self.Direction

    # Change the connector direction
    def SetDirection(self, direction):
        self.Direction = direction

    # Connect a wire to this connector at the last place
    def Connect(self, wire, refresh=True):
        self.InsertConnect(len(self.Wires), wire, refresh)

    # Connect a wire to this connector at the place given
    def InsertConnect(self, idx, wire, refresh=True):
        if wire not in self.Wires:
            self.Wires.insert(idx, wire)
            if wire[1] == 0:
                wire[0].ConnectStartPoint(None, self)
            else:
                wire[0].ConnectEndPoint(None, self)
            if refresh:
                self.ParentBlock.RefreshModel(False)

    # Returns the index of the wire given in the list of connected
    def GetWireIndex(self, wire):
        for i, (tmp_wire, _handle) in enumerate(self.Wires):
            if tmp_wire == wire:
                return i
        return None

    # Unconnect a wire or all wires connected to the connector
    def UnConnect(self, wire=None, unconnect=True, delete=False):
        i = 0
        found = False
        while i < len(self.Wires) and not found:
            if not wire or self.Wires[i][0] == wire:
                # If Unconnect haven't been called from a wire, disconnect the connector in the wire
                if unconnect:
                    if self.Wires[i][1] == 0:
                        self.Wires[i][0].UnConnectStartPoint(delete)
                    else:
                        self.Wires[i][0].UnConnectEndPoint(delete)
                # Remove wire from connected
                if wire:
                    self.Wires.pop(i)
                    found = True
            i += 1
        # If no wire defined, unconnect all wires
        if not wire:
            self.Wires = []
        if not delete:
            self.RefreshValid()
            self.ParentBlock.RefreshModel(False)

    # Returns if connector has one or more wire connected
    def IsConnected(self):
        return len(self.Wires) > 0

    # Move the wires connected
    def MoveConnected(self, exclude=None):
        if len(self.Wires) > 0:
            # Calculate the new position of the end point
            parent_pos = self.ParentBlock.GetPosition()
            x = parent_pos[0] + self.Pos.x + self.Direction[0] * CONNECTOR_SIZE
            y = parent_pos[1] + self.Pos.y + self.Direction[1] * CONNECTOR_SIZE
            # Move the corresponding point on all the wires connected
            for wire, index in self.Wires:
                if (exclude is None) or (wire not in exclude):
                    if index == 0:
                        wire.MoveStartPoint(wx.Point(x, y))
                    else:
                        wire.MoveEndPoint(wx.Point(x, y))

    # Refreshes the model of all the wires connected
    def RefreshWires(self):
        for wire in self.Wires:
            wire[0].RefreshModel()

    # Refreshes the parent block model
    def RefreshParentBlock(self):
        self.ParentBlock.RefreshModel(False)

    # Highlight the parent block
    def HighlightParentBlock(self, highlight):
        self.ParentBlock.SetHighlighted(highlight)
        self.ParentBlock.Refresh()

    # Returns all the blocks connected to this connector
    def GetConnectedBlocks(self):
        blocks = []
        for wire, handle in self.Wires:
            # Get other connector connected to each wire
            if handle == 0:
                connector = wire.GetEndConnected()
            else:
                connector = wire.GetStartConnected()
            # Get parent block for this connector
            if connector:
                block = connector.GetParentBlock()
                if block not in blocks:
                    blocks.append(block)
        return blocks

    # Returns the connector negated property
    def IsNegated(self):
        return self.Negated

    # Changes the connector negated property
    def SetNegated(self, negated):
        if self.ParentBlock.IsOfType("BOOL", self.Type):
            self.Negated = negated
            self.Edge = "none"

    # Returns the connector edge property
    def GetEdge(self):
        return self.Edge

    # Changes the connector edge property
    def SetEdge(self, edge):
        if self.ParentBlock.IsOfType("BOOL", self.Type):
            self.Edge = edge
            self.Negated = False

    # assume that pointer is already inside of this connector
    def ConnectionAvailable(self, direction=None, exclude=True):
        wire_nums = len(self.Wires)

        connector_free = (wire_nums <= 0)
        connector_max_used = ((wire_nums > 0) and self.OneConnected)
        if (self.Parent.CurrentLanguage in ["SFC", "LD"]) and (self.Type == "BOOL"):
            connector_max_used = False

        # connector is available for new connection
        connect = connector_free or not connector_max_used
        return connect, connector_max_used

    # Tests if the point given is near from the end point of this connector
    def TestPoint(self, pt, direction=None, exclude=True):
        inside = False
        check_point = (not exclude) and (direction is None or self.Direction == direction)

        if check_point:
            # Calculate a square around the end point of this connector
            parent_pos = self.ParentBlock.GetPosition()
            x = parent_pos[0] + self.Pos.x + self.Direction[0] * CONNECTOR_SIZE - ANCHOR_DISTANCE
            y = parent_pos[1] + self.Pos.y + self.Direction[1] * CONNECTOR_SIZE - ANCHOR_DISTANCE
            width = ANCHOR_DISTANCE * 2 + abs(self.Direction[0]) * CONNECTOR_SIZE
            height = ANCHOR_DISTANCE * 2 + abs(self.Direction[1]) * CONNECTOR_SIZE
            rect = wx.Rect(x, y, width, height)
            inside = rect.InsideXY(pt.x, pt.y)

        return inside

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        pen = MiterPen(HIGHLIGHTCOLOR, 2 * scalex + 5)
        pen.SetCap(wx.CAP_BUTT)
        dc.SetPen(pen)
        dc.SetBrush(wx.Brush(HIGHLIGHTCOLOR))
        dc.SetLogicalFunction(wx.AND)
        parent_pos = self.ParentBlock.GetPosition()
        xstart = parent_pos[0] + self.Pos.x
        ystart = parent_pos[1] + self.Pos.y
        if self.Direction[0] < 0:
            xstart += 1
        if self.Direction[1] < 0:
            ystart += 1
        xend = xstart + CONNECTOR_SIZE * self.Direction[0]
        yend = ystart + CONNECTOR_SIZE * self.Direction[1]
        dc.DrawLine(round((xstart + self.Direction[0]) * scalex), round((ystart + self.Direction[1]) * scaley),
                    round(xend * scalex), round(yend * scaley))
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Adds an highlight to the connector
    def AddHighlight(self, infos, start, end, highlight_type):
        if highlight_type == ERROR_HIGHLIGHT:
            for wire, _handle in self.Wires:
                wire.SetValid(False)
        AddHighlight(self.Highlights, (start, end, highlight_type))

    # Removes an highlight from the connector
    def RemoveHighlight(self, infos, start, end, highlight_type):
        error = False
        highlights = []
        for highlight in self.Highlights:
            if highlight != (start, end, highlight_type):
                highlights.append(highlight)
                error |= highlight == ERROR_HIGHLIGHT
        self.Highlights = highlights
        if not error:
            for wire, _handle in self.Wires:
                wire.SetValid(wire.IsConnectedCompatible())

    # Removes all the highlights of one particular type from the connector
    def ClearHighlight(self, highlight_type=None):
        error = False
        if highlight_type is None:
            self.Highlights = []
        else:
            highlights = []
            for highlight in self.Highlights:
                if highlight[2] != highlight_type:
                    highlights.append(highlight)
                    error |= highlight == ERROR_HIGHLIGHT
            self.Highlights = highlights
        if not error:
            for wire, _handle in self.Wires:
                wire.SetValid(wire.IsConnectedCompatible())

    # Draws the connector
    def Draw(self, dc):
        if self.Selected:
            dc.SetPen(MiterPen(wx.BLUE, 3))
            dc.SetBrush(wx.WHITE_BRUSH)
        # elif len(self.Highlights) > 0:
        #    dc.SetPen(MiterPen(self.Highlights[-1][1]))
        #    dc.SetBrush(wx.Brush(self.Highlights[-1][0]))
        else:
            if not self.Valid:
                dc.SetPen(MiterPen(wx.RED))
            elif isinstance(self.Value, bool) and self.Value:
                if self.Forced:
                    dc.SetPen(MiterPen(wx.CYAN))
                else:
                    dc.SetPen(MiterPen(wx.GREEN))
            elif self.Value == "undefined":
                dc.SetPen(MiterPen(wx.NamedColour("orange")))
            elif self.Forced:
                dc.SetPen(MiterPen(wx.BLUE))
            else:
                dc.SetPen(MiterPen(wx.BLACK))
            dc.SetBrush(wx.WHITE_BRUSH)
        parent_pos = self.ParentBlock.GetPosition()

        if getattr(dc, "printing", False):
            name_size = dc.GetTextExtent(self.Name)
        else:
            name_size = self.NameSize

        if self.Negated:
            # If connector is negated, draw a circle
            xcenter = parent_pos[0] + self.Pos.x + (CONNECTOR_SIZE * self.Direction[0]) // 2
            ycenter = parent_pos[1] + self.Pos.y + (CONNECTOR_SIZE * self.Direction[1]) // 2
            dc.DrawCircle(xcenter, ycenter, CONNECTOR_SIZE // 2)
        else:
            xstart = parent_pos[0] + self.Pos.x
            ystart = parent_pos[1] + self.Pos.y
            if self.Edge == "rising":
                # If connector has a rising edge, draw a right arrow
                dc.DrawLine(xstart, ystart, xstart - 4, ystart - 4)
                dc.DrawLine(xstart, ystart, xstart - 4, ystart + 4)
            elif self.Edge == "falling":
                # If connector has a falling edge, draw a left arrow
                dc.DrawLine(xstart, ystart, xstart + 4, ystart - 4)
                dc.DrawLine(xstart, ystart, xstart + 4, ystart + 4)
            if self.Direction[0] < 0:
                xstart += 1
            if self.Direction[1] < 0:
                ystart += 1
            if self.Selected:
                xend = xstart + (CONNECTOR_SIZE - 2) * self.Direction[0]
                yend = ystart + (CONNECTOR_SIZE - 2) * self.Direction[1]
                dc.DrawLine(xstart + 2 * self.Direction[0], ystart + 2 * self.Direction[1], xend, yend)
            else:
                xend = xstart + CONNECTOR_SIZE * self.Direction[0]
                yend = ystart + CONNECTOR_SIZE * self.Direction[1]
                dc.DrawLine(xstart + self.Direction[0], ystart + self.Direction[1], xend, yend)
        if self.Direction[0] != 0:
            ytext = parent_pos[1] + self.Pos.y - name_size[1] // 2
            if self.Direction[0] < 0:
                xtext = parent_pos[0] + self.Pos.x + 5
            else:
                xtext = parent_pos[0] + self.Pos.x - (name_size[0] + 5)
        if self.Direction[1] != 0:
            xtext = parent_pos[0] + self.Pos.x - name_size[0] // 2
            if self.Direction[1] < 0:
                ytext = parent_pos[1] + self.Pos.y + 5
            else:
                ytext = parent_pos[1] + self.Pos.y - (name_size[1] + 5)
        # Draw the text
        dc.DrawText(self.Name, xtext, ytext)
        if not getattr(dc, "printing", False):
            DrawHighlightedText(dc, self.Name, self.Highlights, xtext, ytext)

        if self.Value is not None and not isinstance(self.Value, bool) and self.Value != "undefined":
            dc.SetFont(self.ParentBlock.Parent.GetMiniFont())
            dc.SetTextForeground(wx.NamedColour("purple"))
            if self.ValueSize is None and isinstance(self.ComputedValue, string_types):
                self.ValueSize = self.ParentBlock.Parent.GetMiniTextExtent(self.ComputedValue)
            if self.ValueSize is not None:
                width, height = self.ValueSize
                dc.DrawText(self.ComputedValue,
                            parent_pos[0] + self.Pos.x + CONNECTOR_SIZE * self.Direction[0] +
                            width * (self.Direction[0] - 1) // 2,
                            parent_pos[1] + self.Pos.y + CONNECTOR_SIZE * self.Direction[1] +
                            height * (self.Direction[1] - 1))
            dc.SetFont(self.ParentBlock.Parent.GetFont())
            dc.SetTextForeground(wx.BLACK)


# -------------------------------------------------------------------------------
#                           Common Wire Element
# -------------------------------------------------------------------------------


class Wire(Graphic_Element, DebugDataConsumer):
    """
    Class that implements a wire for connecting two blocks
    """

    # Create a new wire
    def __init__(self, parent, start=None, end=None):
        Graphic_Element.__init__(self, parent)
        DebugDataConsumer.__init__(self)
        self.StartPoint = start
        self.EndPoint = end
        self.StartConnected = None
        self.EndConnected = None
        # If the start and end points are defined, calculate the wire
        if start and end:
            self.ResetPoints()
            self.GeneratePoints()
        else:
            self.Points = []
            self.Segments = []
        self.SelectedSegment = None
        self.Valid = True
        self.Modifier = "none"
        self.PreviousValue = None
        self.ValueSize = None
        self.ComputedValue = None
        self.OverStart = False
        self.OverEnd = False
        self.ComputingType = False
        self.Font = parent.GetMiniFont()
        self.ErrHighlight = False

    def GetDefinition(self):
        if self.StartConnected is not None and self.EndConnected is not None:
            startblock = self.StartConnected.GetParentBlock()
            endblock = self.EndConnected.GetParentBlock()
            return [], [(startblock.GetId(), endblock.GetId())]
        return [], []

    def Flush(self):
        self.StartConnected = None
        self.EndConnected = None

    # Returns the RedrawRect
    def GetRedrawRect(self, movex=0, movey=0):
        rect = Graphic_Element.GetRedrawRect(self, movex, movey)
        if self.StartConnected:
            rect = rect.Union(self.StartConnected.GetRedrawRect(movex, movey))
        if self.EndConnected:
            rect = rect.Union(self.EndConnected.GetRedrawRect(movex, movey))
        if self.ValueSize is None and isinstance(self.ComputedValue, string_types):
            self.ValueSize = self.Parent.GetMiniTextExtent(self.ComputedValue)
        if self.ValueSize is not None:
            width, height = self.ValueSize
            if self.BoundingBox[2] > width * 4 or self.BoundingBox[3] > height * 4:
                x = self.Points[0].x + width * self.StartPoint[1][0] // 2
                y = self.Points[0].y + height * (self.StartPoint[1][1] - 1)
                rect = rect.Union(wx.Rect(x, y, width, height))
                x = self.Points[-1].x + width * self.EndPoint[1][0] // 2
                y = self.Points[-1].y + height * (self.EndPoint[1][1] - 1)
                rect = rect.Union(wx.Rect(x, y, width, height))
            else:
                middle = len(self.Segments) // 2 + len(self.Segments) % 2 - 1
                x = (self.Points[middle].x + self.Points[middle + 1].x - width) // 2
                if self.BoundingBox[3] > height and self.Segments[middle] in [NORTH, SOUTH]:
                    y = (self.Points[middle].y + self.Points[middle + 1].y - height) // 2
                else:
                    y = self.Points[middle].y - height
                rect = rect.Union(wx.Rect(x, y, width, height))
        return rect

    def Clone(self, parent, connectors=None, dx=0, dy=0):
        connectors = {} if connectors is None else connectors
        start_connector = connectors.get(self.StartConnected, None)
        end_connector = connectors.get(self.EndConnected, None)
        if start_connector is not None and end_connector is not None:
            wire = Wire(parent)
            wire.SetPoints([(point.x + dx, point.y + dy) for point in self.Points])
            start_connector.Connect((wire, 0), False)
            end_connector.Connect((wire, -1), False)
            wire.ConnectStartPoint(start_connector.GetPosition(), start_connector)
            wire.ConnectEndPoint(end_connector.GetPosition(), end_connector)
            return wire
        return None

    # Forbids to change the wire position
    def SetPosition(self, x, y):
        pass

    # Forbids to change the wire size
    def SetSize(self, width, height):
        pass

    # Moves and Resizes the element for fitting scaling
    def SetBestSize(self, scaling):
        if scaling is not None:
            movex_max = movey_max = 0
            for idx, point in enumerate(self.Points):
                if 0 < idx < len(self.Points) - 1:
                    movex = round_scaling(point.x, scaling[0]) - point.x
                    movey = round_scaling(point.y, scaling[1]) - point.y
                    if idx == 1:
                        if self.Segments[0][0] == 0:
                            movex = 0
                        elif (point.x + movex - self.Points[0].x) * self.Segments[0][0] < MIN_SEGMENT_SIZE:
                            movex = round_scaling(self.Points[0].x + MIN_SEGMENT_SIZE * self.Segments[0][0], scaling[0], self.Segments[0][0]) - point.x
                        if self.Segments[0][1] == 0:
                            movey = 0
                        elif (point.y + movey - self.Points[0].y) * self.Segments[0][1] < MIN_SEGMENT_SIZE:
                            movey = round_scaling(self.Points[0].y + MIN_SEGMENT_SIZE * self.Segments[0][1], scaling[0], self.Segments[0][1]) - point.y
                    elif idx == len(self.Points) - 2:
                        if self.Segments[-1][0] == 0:
                            movex = 0
                        elif (self.Points[-1].x - (point.x + movex)) * self.Segments[-1][0] < MIN_SEGMENT_SIZE:
                            movex = round_scaling(self.Points[-1].x + MIN_SEGMENT_SIZE * self.Segments[0][0], scaling[0], self.Segments[0][0]) - point.x
                        if self.Segments[-1][1] == 0:
                            movey = 0
                        elif (self.Points[-1].y - (point.y + movey)) * self.Segments[-1][1] < MIN_SEGMENT_SIZE:
                            movey = round_scaling(self.Points[-1].y - MIN_SEGMENT_SIZE * self.Segments[-1][1], scaling[1], -self.Segments[-1][1]) - point.y
                    movex_max = max(movex_max, movex)
                    movey_max = max(movey_max, movey)
                    point.x += movex
                    point.y += movey
            return movex_max, movey_max
        return 0, 0

    # Returns connector to which start point is connected
    def GetStartConnected(self):
        return self.StartConnected

    # Returns connector to which start point is connected
    def GetStartConnectedType(self):
        if self.StartConnected and not self.ComputingType:
            self.ComputingType = True
            computed_type = self.StartConnected.GetType()
            self.ComputingType = False
            return computed_type
        return None

    # Returns connector to which end point is connected
    def GetEndConnected(self):
        return self.EndConnected

    # Returns connector to which end point is connected
    def GetEndConnectedType(self):
        if self.EndConnected and not self.ComputingType:
            self.ComputingType = True
            computed_type = self.EndConnected.GetType()
            self.ComputingType = False
            return computed_type
        return None

    def GetConnectionDirection(self):
        if self.StartConnected is None and self.EndConnected is None:
            return None
        elif self.StartConnected is not None and self.EndConnected is None:
            return (-self.StartPoint[1][0], -self.StartPoint[1][1])
        elif self.StartConnected is None and self.EndConnected is not None:
            return self.EndPoint
        elif self.Handle is not None:
            handle_type, handle = self.Handle
            # A point has been handled
            if handle_type == HANDLE_POINT:
                if handle == 0:
                    return self.EndPoint
                else:
                    return (-self.StartPoint[1][0], -self.StartPoint[1][1])
        return None

    def GetOtherConnected(self, connector):
        if self.StartConnected == connector:
            return self.EndConnected
        else:
            return self.StartConnected

    def GetOtherConnectedType(self, handle):
        if handle == 0:
            return self.GetEndConnectedType()
        else:
            return self.GetStartConnectedType()

    def IsConnectedCompatible(self):
        if self.StartConnected:
            return self.StartConnected.IsCompatible(self.GetEndConnectedType())
        elif self.EndConnected:
            return True
        return False

    def SetForced(self, forced):
        if self.Forced != forced:
            self.Forced = forced
            if self.StartConnected:
                self.StartConnected.RefreshForced()
            if self.EndConnected:
                self.EndConnected.RefreshForced()
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)

    def GetComputedValue(self):
        if self.Value is not None and self.Value != "undefined" and not isinstance(self.Value, bool):
            return self.Value
        return None

    def GetToolTipValue(self):
        return self.GetComputedValue()

    def SetModifier(self, modifier):
        self.Modifier = modifier

    def SetValue(self, value):
        if self.Modifier == "rising":
            value, self.PreviousValue = value and not self.PreviousValue, value
        elif self.Modifier == "falling":
            value, self.PreviousValue = not value and self.PreviousValue, value
        elif self.Modifier == "negated":
            value = not value
        if self.Value != value:
            self.Value = value
            computed_value = self.GetComputedValue()
            if computed_value is not None:
                self.ComputedValue = computed_value
                self.SetToolTipText(self.ComputedValue)
                if len(self.ComputedValue) > 4:
                    self.ComputedValue = self.ComputedValue[:4] + "..."
            self.ValueSize = None
            if self.StartConnected:
                self.StartConnected.RefreshValue()
            if self.EndConnected:
                self.EndConnected.RefreshValue()
            if self.Visible:
                self.Parent.ElementNeedRefresh(self)
            if isinstance(value, bool) and self.StartConnected is not None:
                block = self.StartConnected.GetParentBlock()
                block.SpreadCurrent()

    # Unconnect the start and end points
    def Clean(self):
        if self.StartConnected:
            self.UnConnectStartPoint()
        if self.EndConnected:
            self.UnConnectEndPoint()

    # Delete this wire by calling the corresponding method
    def Delete(self):
        self.Parent.DeleteWire(self)

    # Select a segment and not the whole wire. It's useful for Ladder Diagram
    def SetSelectedSegment(self, segment):
        # The last segment is indicated
        if segment == -1:
            segment = len(self.Segments) - 1
        # The selected segment is reinitialised
        if segment is None:
            if self.StartConnected:
                self.StartConnected.SetSelected(False)
            if self.EndConnected:
                self.EndConnected.SetSelected(False)
        # The segment selected is the first
        elif segment == 0:
            if self.StartConnected:
                self.StartConnected.SetSelected(True)
            if self.EndConnected:
                # There is only one segment
                if len(self.Segments) == 1:
                    self.EndConnected.SetSelected(True)
                else:
                    self.EndConnected.SetSelected(False)
        # The segment selected is the last
        elif segment == len(self.Segments) - 1:
            if self.StartConnected:
                self.StartConnected.SetSelected(False)
            if self.EndConnected:
                self.EndConnected.SetSelected(True)
        self.SelectedSegment = segment
        self.Refresh()

    def SetValid(self, valid):
        self.Valid = valid
        if self.StartConnected:
            self.StartConnected.RefreshValid()
        if self.EndConnected:
            self.EndConnected.RefreshValid()

    def GetValid(self):
        return self.Valid

    # Reinitialize the wire points
    def ResetPoints(self):
        if self.StartPoint and self.EndPoint:
            self.Points = [self.StartPoint[0], self.EndPoint[0]]
            self.Segments = [self.StartPoint[1]]
        else:
            self.Points = []
            self.Segments = []

    # Refresh the wire bounding box
    def RefreshBoundingBox(self):
        if len(self.Points) > 0:
            # If startpoint or endpoint is connected, save the point radius
            start_radius = end_radius = 0
            if not self.StartConnected:
                start_radius = POINT_RADIUS
            if not self.EndConnected:
                end_radius = POINT_RADIUS
            # Initialize minimum and maximum from the first point
            minx, minbbxx = self.Points[0].x, self.Points[0].x - start_radius
            maxx, maxbbxx = self.Points[0].x, self.Points[0].x + start_radius
            miny, minbbxy = self.Points[0].y, self.Points[0].y - start_radius
            maxy, maxbbxy = self.Points[0].y, self.Points[0].y + start_radius
            # Actualize minimum and maximum with the other points
            for point in self.Points[1:-1]:
                minx, minbbxx = min(minx, point.x), min(minbbxx, point.x)
                maxx, maxbbxx = max(maxx, point.x), max(maxbbxx, point.x)
                miny, minbbxy = min(miny, point.y), min(minbbxy, point.y)
                maxy, maxbbxy = max(maxy, point.y), max(maxbbxy, point.y)
            if len(self.Points) > 1:
                minx, minbbxx = min(minx, self.Points[-1].x), min(minbbxx, self.Points[-1].x - end_radius)
                maxx, maxbbxx = max(maxx, self.Points[-1].x), max(maxbbxx, self.Points[-1].x + end_radius)
                miny, minbbxy = min(miny, self.Points[-1].y), min(minbbxy, self.Points[-1].y - end_radius)
                maxy, maxbbxy = max(maxy, self.Points[-1].y), max(maxbbxy, self.Points[-1].y + end_radius)
            self.Pos.x, self.Pos.y = minx, miny
            self.Size = wx.Size(maxx - minx, maxy - miny)
            self.BoundingBox = wx.Rect(minbbxx, minbbxy, maxbbxx - minbbxx + 1, maxbbxy - minbbxy + 1)

    # Refresh the realpoints that permits to keep the proportionality in wire during resizing
    def RefreshRealPoints(self):
        if len(self.Points) > 0:
            self.RealPoints = []
            # Calculate float relative position of each point with the minimum point
            for point in self.Points:
                self.RealPoints.append([float(point.x - self.Pos.x), float(point.y - self.Pos.y)])

    # Returns the wire minimum size
    def GetMinSize(self):
        width = 1
        height = 1
        dir_product = product(self.StartPoint[1], self.EndPoint[1])
        # The directions are opposed
        if dir_product < 0:
            if self.StartPoint[0] != 0:
                width = MIN_SEGMENT_SIZE * 2
            if self.StartPoint[1] != 0:
                height = MIN_SEGMENT_SIZE * 2
        # The directions are the same
        elif dir_product > 0:
            if self.StartPoint[0] != 0:
                width = MIN_SEGMENT_SIZE
            if self.StartPoint[1] != 0:
                height = MIN_SEGMENT_SIZE
        # The directions are perpendiculars
        else:
            width = MIN_SEGMENT_SIZE
            height = MIN_SEGMENT_SIZE
        return width + 1, height + 1

    # Returns if the point given is on one of the wire segments
    def HitTest(self, pt, connectors=True):
        test = False
        for i in xrange(len(self.Points) - 1):
            rect = wx.Rect(0, 0, 0, 0)
            if i == 0 and self.StartConnected is not None:
                x1 = self.Points[i].x - self.Segments[0][0] * CONNECTOR_SIZE
                y1 = self.Points[i].y - self.Segments[0][1] * CONNECTOR_SIZE
            else:
                x1, y1 = self.Points[i].x, self.Points[i].y
            if i == len(self.Points) - 2 and self.EndConnected is not None:
                x2 = self.Points[i + 1].x + self.Segments[-1][0] * CONNECTOR_SIZE
                y2 = self.Points[i + 1].y + self.Segments[-1][1] * CONNECTOR_SIZE
            else:
                x2, y2 = self.Points[i + 1].x, self.Points[i + 1].y
            # Calculate a rectangle around the segment
            rect = wx.Rect(min(x1, x2) - ANCHOR_DISTANCE, min(y1, y2) - ANCHOR_DISTANCE,
                           abs(x1 - x2) + 2 * ANCHOR_DISTANCE, abs(y1 - y2) + 2 * ANCHOR_DISTANCE)
            test |= rect.InsideXY(pt.x, pt.y)
        return test

    # Returns the wire start or end point if the point given is on one of them
    def TestPoint(self, pt):
        # Test the wire start point
        rect = wx.Rect(self.Points[0].x - ANCHOR_DISTANCE, self.Points[0].y - ANCHOR_DISTANCE,
                       2 * ANCHOR_DISTANCE, 2 * ANCHOR_DISTANCE)
        if rect.InsideXY(pt.x, pt.y):
            return 0
        # Test the wire end point
        if len(self.Points) > 1:
            rect = wx.Rect(self.Points[-1].x - ANCHOR_DISTANCE, self.Points[-1].y - ANCHOR_DISTANCE,
                           2 * ANCHOR_DISTANCE, 2 * ANCHOR_DISTANCE)
            if rect.InsideXY(pt.x, pt.y):
                return -1
        return None

    # Returns the wire segment if the point given is on it
    def TestSegment(self, pt, all=False):
        for i in xrange(len(self.Segments)):
            # If wire is not in a Ladder Diagram, first and last segments are excluded
            if all or 0 < i < len(self.Segments) - 1:
                x1, y1 = self.Points[i].x, self.Points[i].y
                x2, y2 = self.Points[i + 1].x, self.Points[i + 1].y
                # Calculate a rectangle around the segment
                rect = wx.Rect(min(x1, x2) - ANCHOR_DISTANCE, min(y1, y2) - ANCHOR_DISTANCE,
                               abs(x1 - x2) + 2 * ANCHOR_DISTANCE, abs(y1 - y2) + 2 * ANCHOR_DISTANCE)
                if rect.InsideXY(pt.x, pt.y):
                    return i, self.Segments[i]
        return None

    # Define the wire points
    def SetPoints(self, points, verify=True):
        if len(points) > 1:
            self.Points = [wx.Point(x, y) for x, y in points]
            # Calculate the start and end directions
            self.StartPoint = [None, vector(self.Points[0], self.Points[1])]
            self.EndPoint = [None, vector(self.Points[-1], self.Points[-2])]
            # Calculate the start and end points
            self.StartPoint[0] = wx.Point(self.Points[0].x + CONNECTOR_SIZE * self.StartPoint[1][0],
                                          self.Points[0].y + CONNECTOR_SIZE * self.StartPoint[1][1])
            self.EndPoint[0] = wx.Point(self.Points[-1].x + CONNECTOR_SIZE * self.EndPoint[1][0],
                                        self.Points[-1].y + CONNECTOR_SIZE * self.EndPoint[1][1])
            self.Points[0] = self.StartPoint[0]
            self.Points[-1] = self.EndPoint[0]
            # Calculate the segments directions
            self.Segments = []
            i = 0
            while i < len(self.Points) - 1:
                if verify and 0 < i < len(self.Points) - 2 and \
                   self.Points[i] == self.Points[i + 1] and \
                   self.Segments[-1] == vector(self.Points[i + 1], self.Points[i + 2]):
                    for dummy in xrange(2):
                        self.Points.pop(i)
                else:
                    segment = vector(self.Points[i], self.Points[i + 1])
                    if is_null_vector(segment) and i > 0:
                        segment = (self.Segments[-1][1], self.Segments[-1][0])
                    if i < len(self.Points) - 2:
                        next = vector(self.Points[i + 1], self.Points[i + 2])
                        if next == segment or is_null_vector(add_vectors(segment, next)):
                            self.Points.insert(i + 1, wx.Point(self.Points[i + 1].x, self.Points[i + 1].y))
                    self.Segments.append(segment)
                    i += 1
            self.RefreshBoundingBox()
            self.RefreshRealPoints()

    # Returns the position of the point indicated
    def GetPoint(self, index):
        if index < len(self.Points):
            return self.Points[index].x, self.Points[index].y
        return None

    # Returns a list of the position of all wire points
    def GetPoints(self, invert=False):
        points = self.VerifyPoints()
        points[0] = wx.Point(points[0].x - CONNECTOR_SIZE * self.StartPoint[1][0],
                             points[0].y - CONNECTOR_SIZE * self.StartPoint[1][1])
        points[-1] = wx.Point(points[-1].x - CONNECTOR_SIZE * self.EndPoint[1][0],
                              points[-1].y - CONNECTOR_SIZE * self.EndPoint[1][1])
        # An inversion of the list is asked
        if invert:
            points.reverse()
        return points

    # Returns the position of the two selected segment points
    def GetSelectedSegmentPoints(self):
        if self.SelectedSegment is not None and len(self.Points) > 1:
            return self.Points[self.SelectedSegment:self.SelectedSegment + 2]
        return []

    # Returns if the selected segment is the first and/or the last of the wire
    def GetSelectedSegmentConnections(self):
        if self.SelectedSegment is not None and len(self.Points) > 1:
            return self.SelectedSegment == 0, self.SelectedSegment == len(self.Segments) - 1
        return (True, True)

    # Returns the connectors on which the wire is connected
    def GetConnected(self):
        connected = []
        if self.StartConnected and self.StartPoint[1] == WEST:
            connected.append(self.StartConnected)
        if self.EndConnected and self.EndPoint[1] == WEST:
            connected.append(self.EndConnected)
        return connected

    # Returns the id of the block connected to the first or the last wire point
    def GetConnectedInfos(self, index):
        if index == 0 and self.StartConnected:
            return self.StartConnected.GetBlockId(), self.StartConnected.GetName()
        elif index == -1 and self.EndConnected:
            return self.EndConnected.GetBlockId(), self.EndConnected.GetName()
        return None

    # Update the wire points position by keeping at most possible the current positions
    def GeneratePoints(self, realpoints=True):
        i = 0
        # Calculate the start enad end points with the minimum segment size in the right direction
        end = wx.Point(self.EndPoint[0].x + self.EndPoint[1][0] * MIN_SEGMENT_SIZE,
                       self.EndPoint[0].y + self.EndPoint[1][1] * MIN_SEGMENT_SIZE)
        start = wx.Point(self.StartPoint[0].x + self.StartPoint[1][0] * MIN_SEGMENT_SIZE,
                         self.StartPoint[0].y + self.StartPoint[1][1] * MIN_SEGMENT_SIZE)
        # Evaluate the point till it's the last
        while i < len(self.Points) - 1:
            # The next point is the last
            if i + 1 == len(self.Points) - 1:
                # Calculate the direction from current point to end point
                v_end = vector(self.Points[i], end)
                # The current point is the first
                if i == 0:
                    # If the end point is not in the start direction, a point is added
                    if v_end != self.Segments[0] or v_end == self.EndPoint[1]:
                        self.Points.insert(1, wx.Point(start.x, start.y))
                        self.Segments.insert(1, DirectionChoice(
                            (self.Segments[0][1],
                             self.Segments[0][0]), v_end, self.EndPoint[1]))
                # The current point is the second
                elif i == 1:
                    # The previous direction and the target direction are mainly opposed, a point is added
                    if product(v_end, self.Segments[0]) < 0:
                        self.Points.insert(2, wx.Point(self.Points[1].x, self.Points[1].y))
                        self.Segments.insert(2, DirectionChoice(
                            (self.Segments[1][1],
                             self.Segments[1][0]), v_end, self.EndPoint[1]))
                    # The previous direction and the end direction are the same or they are
                    # perpendiculars and the end direction points towards current segment
                    elif product(self.Segments[0], self.EndPoint[1]) >= 0 and product(self.Segments[1], self.EndPoint[1]) <= 0:
                        # Current point and end point are aligned
                        if self.Segments[0][0] != 0:
                            self.Points[1].x = end.x
                        if self.Segments[0][1] != 0:
                            self.Points[1].y = end.y
                        # If the previous direction and the end direction are the same, a point is added
                        if product(self.Segments[0], self.EndPoint[1]) > 0:
                            self.Points.insert(2, wx.Point(self.Points[1].x, self.Points[1].y))
                            self.Segments.insert(2, DirectionChoice(
                                (self.Segments[1][1],
                                 self.Segments[1][0]), v_end, self.EndPoint[1]))
                    else:
                        # Current point is positioned in the middle of start point
                        # and end point on the current direction and a point is added
                        if self.Segments[0][0] != 0:
                            self.Points[1].x = (end.x + start.x) // 2
                        if self.Segments[0][1] != 0:
                            self.Points[1].y = (end.y + start.y) // 2
                        self.Points.insert(2, wx.Point(self.Points[1].x, self.Points[1].y))
                        self.Segments.insert(2, DirectionChoice(
                            (self.Segments[1][1],
                             self.Segments[1][0]), v_end, self.EndPoint[1]))
                else:
                    # The previous direction and the end direction are perpendiculars
                    if product(self.Segments[i - 1], self.EndPoint[1]) == 0:
                        # The target direction and the end direction aren't mainly the same
                        if product(v_end, self.EndPoint[1]) <= 0:
                            # Current point and end point are aligned
                            if self.Segments[i - 1][0] != 0:
                                self.Points[i].x = end.x
                            if self.Segments[i - 1][1] != 0:
                                self.Points[i].y = end.y
                            # Previous direction is updated from the new point
                            if product(vector(self.Points[i - 1], self.Points[i]), self.Segments[i - 1]) < 0:
                                self.Segments[i - 1] = (-self.Segments[i - 1][0], -self.Segments[i - 1][1])
                        else:
                            test = True
                            # If the current point is the third, test if the second
                            # point can be aligned with the end point
                            if i == 2:
                                test_point = wx.Point(self.Points[1].x, self.Points[1].y)
                                if self.Segments[1][0] != 0:
                                    test_point.y = end.y
                                if self.Segments[1][1] != 0:
                                    test_point.x = end.x
                                vector_test = vector(self.Points[0], test_point, False)
                                test = norm(vector_test) > MIN_SEGMENT_SIZE and product(self.Segments[0], vector_test) > 0
                            # The previous point can be aligned
                            if test:
                                self.Points[i].x, self.Points[i].y = end.x, end.y
                                if self.Segments[i - 1][0] != 0:
                                    self.Points[i - 1].y = end.y
                                if self.Segments[i - 1][1] != 0:
                                    self.Points[i - 1].x = end.x
                                self.Segments[i] = (-self.EndPoint[1][0], -self.EndPoint[1][1])
                            else:
                                # Current point is positioned in the middle of previous point
                                # and end point on the current direction and a point is added
                                if self.Segments[1][0] != 0:
                                    self.Points[2].x = (self.Points[1].x + end.x) // 2
                                if self.Segments[1][1] != 0:
                                    self.Points[2].y = (self.Points[1].y + end.y) // 2
                                self.Points.insert(3, wx.Point(self.Points[2].x, self.Points[2].y))
                                self.Segments.insert(
                                    3,
                                    DirectionChoice((self.Segments[2][1],
                                                     self.Segments[2][0]),
                                                    v_end,
                                                    self.EndPoint[1]))
                    else:
                        # Current point is aligned with end point
                        if self.Segments[i - 1][0] != 0:
                            self.Points[i].x = end.x
                        if self.Segments[i - 1][1] != 0:
                            self.Points[i].y = end.y
                        # Previous direction is updated from the new point
                        if product(vector(self.Points[i - 1], self.Points[i]), self.Segments[i - 1]) < 0:
                            self.Segments[i - 1] = (-self.Segments[i - 1][0], -self.Segments[i - 1][1])
                        # If previous direction and end direction are opposed
                        if product(self.Segments[i - 1], self.EndPoint[1]) < 0:
                            # Current point is positioned in the middle of previous point
                            # and end point on the current direction
                            if self.Segments[i - 1][0] != 0:
                                self.Points[i].x = (end.x + self.Points[i - 1].x) // 2
                            if self.Segments[i - 1][1] != 0:
                                self.Points[i].y = (end.y + self.Points[i - 1].y) // 2
                        # A point is added
                        self.Points.insert(i + 1, wx.Point(self.Points[i].x, self.Points[i].y))
                        self.Segments.insert(
                            i + 1,
                            DirectionChoice((self.Segments[i][1],
                                             self.Segments[i][0]), v_end, self.EndPoint[1]))
            else:
                # Current point is the first, and second is not mainly in the first direction
                if i == 0 and product(vector(start, self.Points[1]), self.Segments[0]) < 0:
                    # If first and second directions aren't perpendiculars, a point is added
                    if product(self.Segments[0], self.Segments[1]) != 0:
                        self.Points.insert(1, wx.Point(start.x, start.y))
                        self.Segments.insert(
                            1,
                            DirectionChoice((self.Segments[0][1],
                                             self.Segments[0][0]),
                                            vector(start, self.Points[1]),
                                            self.Segments[1]))
                    else:
                        self.Points[1].x, self.Points[1].y = start.x, start.y
                else:
                    # Next point is aligned with current point
                    if self.Segments[i][0] != 0:
                        self.Points[i + 1].y = self.Points[i].y
                    if self.Segments[i][1] != 0:
                        self.Points[i + 1].x = self.Points[i].x
                    # Current direction is updated from the new point
                    if product(vector(self.Points[i], self.Points[i + 1]), self.Segments[i]) < 0:
                        self.Segments[i] = (-self.Segments[i][0], -self.Segments[i][1])
            i += 1
        self.RefreshBoundingBox()
        if realpoints:
            self.RefreshRealPoints()

    # Verify that two consecutive points haven't the same position
    def VerifyPoints(self):
        points = [point for point in self.Points]
        segments = [segment for segment in self.Segments]
        i = 1
        while i < len(points) - 1:
            if points[i] == points[i + 1] and segments[i - 1] == segments[i + 1]:
                for dummy in xrange(2):
                    points.pop(i)
                    segments.pop(i)
            else:
                i += 1
        # If the wire isn't in a Ladder Diagram, save the new point list
        if self.Parent.__class__.__name__ != "LD_Viewer":
            self.Points = [point for point in points]
            self.Segments = [segment for segment in segments]
            self.RefreshBoundingBox()
            self.RefreshRealPoints()
        return points

    # Moves all the wire points except the first and the last if they are connected
    def Move(self, dx, dy, endpoints=False):
        for i, point in enumerate(self.Points):
            if endpoints or not (i == 0 and self.StartConnected) and not (i == len(self.Points) - 1 and self.EndConnected):
                point.x += dx
                point.y += dy
        self.StartPoint[0] = self.Points[0]
        self.EndPoint[0] = self.Points[-1]
        self.GeneratePoints()

    # Resize the wire from position and size given
    def Resize(self, x, y, width, height):
        if len(self.Points) > 1:
            # Calculate the new position of each point for testing the new size
            minx, miny = self.Pos.x, self.Pos.y
            lastwidth, lastheight = self.Size.width, self.Size.height
            for i, point in enumerate(self.RealPoints):
                # If start or end point is connected, it's not calculate
                if not (i == 0 and self.StartConnected) and not (i == len(self.Points) - 1 and self.EndConnected):
                    if i == 0:
                        dir = self.StartPoint[1]
                    elif i == len(self.Points) - 1:
                        dir = self.EndPoint[1]
                    else:
                        dir = (0, 0)
                    pointx = max(-dir[0] * MIN_SEGMENT_SIZE, min(int(round(point[0] * width / max(lastwidth, 1))),
                                                                 width - dir[0] * MIN_SEGMENT_SIZE))
                    pointy = max(-dir[1] * MIN_SEGMENT_SIZE, min(int(round(point[1] * height / max(lastheight, 1))),
                                                                 height - dir[1] * MIN_SEGMENT_SIZE))
                    self.Points[i] = wx.Point(minx + x + pointx, miny + y + pointy)
            self.StartPoint[0] = self.Points[0]
            self.EndPoint[0] = self.Points[-1]
            self.GeneratePoints(False)
            # Test if the wire position or size have changed
            if x != 0 and minx == self.Pos.x:
                x = 0
                width = lastwidth
            if y != 0 and miny == self.Pos.y:
                y = 0
                height = lastwidth
            if width != lastwidth and lastwidth == self.Size.width:
                width = lastwidth
            if height != lastheight and lastheight == self.Size.height:
                height = lastheight
            # Calculate the real points from the new size, it's important for
            # keeping a proportionality in the points position with the size
            # during a resize dragging
            for i, point in enumerate(self.RealPoints):
                if not (i == 0 and self.StartConnected) and not (i == len(self.Points) - 1 and self.EndConnected):
                    point[0] = point[0] * width / max(lastwidth, 1)
                    point[1] = point[1] * height / max(lastheight, 1)
            # Calculate the correct position of the points from real points
            for i, point in enumerate(self.RealPoints):
                if not (i == 0 and self.StartConnected) and not (i == len(self.Points) - 1 and self.EndConnected):
                    if i == 0:
                        dir = self.StartPoint[1]
                    elif i == len(self.Points) - 1:
                        dir = self.EndPoint[1]
                    else:
                        dir = (0, 0)
                    realpointx = max(-dir[0] * MIN_SEGMENT_SIZE,
                                     min(int(round(point[0])),
                                         width - dir[0] * MIN_SEGMENT_SIZE))
                    realpointy = max(-dir[1] * MIN_SEGMENT_SIZE,
                                     min(int(round(point[1])),
                                         height - dir[1] * MIN_SEGMENT_SIZE))
                    self.Points[i] = wx.Point(minx + x + realpointx, miny + y + realpointy)
            self.StartPoint[0] = self.Points[0]
            self.EndPoint[0] = self.Points[-1]
            self.GeneratePoints(False)

    # Moves the wire start point and update the wire points
    def MoveStartPoint(self, point):
        if len(self.Points) > 1:
            self.StartPoint[0] = point
            self.Points[0] = point
            self.GeneratePoints()

    # Changes the wire start direction and update the wire points
    def SetStartPointDirection(self, dir):
        if len(self.Points) > 1:
            self.StartPoint[1] = dir
            self.Segments[0] = dir
            self.GeneratePoints()

    # Rotates the wire start direction by an angle of 90 degrees anticlockwise
    def RotateStartPoint(self):
        self.SetStartPointDirection((self.StartPoint[1][1], -self.StartPoint[1][0]))

    # Connects wire start point to the connector given and moves wire start point
    # to given point
    def ConnectStartPoint(self, point, connector):
        if point:
            self.MoveStartPoint(point)
        self.StartConnected = connector
        self.RefreshBoundingBox()

    # Unconnects wire start point
    def UnConnectStartPoint(self, delete=False):
        if delete:
            self.StartConnected = None
            self.Delete()
        elif self.StartConnected:
            self.StartConnected.UnConnect(self, unconnect=False)
            self.StartConnected = None
            self.RefreshBoundingBox()

    # Moves the wire end point and update the wire points
    def MoveEndPoint(self, point):
        if len(self.Points) > 1:
            self.EndPoint[0] = point
            self.Points[-1] = point
            self.GeneratePoints()

    # Changes the wire end direction and update the wire points
    def SetEndPointDirection(self, dir):
        if len(self.Points) > 1:
            self.EndPoint[1] = dir
            self.GeneratePoints()

    # Rotates the wire end direction by an angle of 90 degrees anticlockwise
    def RotateEndPoint(self):
        self.SetEndPointDirection((self.EndPoint[1][1], -self.EndPoint[1][0]))

    # Connects wire end point to the connector given and moves wire end point
    # to given point
    def ConnectEndPoint(self, point, connector):
        if point:
            self.MoveEndPoint(point)
        self.EndConnected = connector
        self.RefreshBoundingBox()

    # Unconnects wire end point
    def UnConnectEndPoint(self, delete=False):
        if delete:
            self.EndConnected = None
            self.Delete()
        elif self.EndConnected:
            self.EndConnected.UnConnect(self, unconnect=False)
            self.EndConnected = None
            self.RefreshBoundingBox()

    # Moves the wire segment given by its index
    def MoveSegment(self, idx, movex, movey, scaling):
        if 0 < idx < len(self.Segments) - 1:
            if self.Segments[idx] in (NORTH, SOUTH):
                start_x = self.Points[idx].x
                if scaling is not None:
                    movex = round_scaling(self.Points[idx].x + movex, scaling[0]) - self.Points[idx].x
                    if idx == 1 and (self.Points[1].x + movex - self.Points[0].x) * self.Segments[0][0] < MIN_SEGMENT_SIZE:
                        movex = round_scaling(self.Points[0].x + MIN_SEGMENT_SIZE * self.Segments[0][0], scaling[0], self.Segments[0][0]) - self.Points[idx].x
                    elif idx == len(self.Segments) - 2 and (self.Points[-1].x - (self.Points[-2].x + movex)) * self.Segments[-1][0] < MIN_SEGMENT_SIZE:
                        movex = round_scaling(self.Points[-1].x - MIN_SEGMENT_SIZE * self.Segments[-1][0], scaling[0], -self.Segments[-1][0]) - self.Points[idx].x
                self.Points[idx].x += movex
                self.Points[idx + 1].x += movex
                self.GeneratePoints()
                if start_x != self.Points[idx].x:
                    return self.Points[idx].x - start_x, 0
            elif self.Segments[idx] in (EAST, WEST):
                start_y = self.Points[idx].y
                if scaling is not None:
                    movey = round_scaling(self.Points[idx].y + movey, scaling[1]) - self.Points[idx].y
                    if idx == 1 and (self.Points[1].y + movey - self.Points[0].y) * self.Segments[0][1] < MIN_SEGMENT_SIZE:
                        movex = round_scaling(self.Points[0].y + MIN_SEGMENT_SIZE * self.Segments[0][1], scaling[0], self.Segments[0][1]) - self.Points[idx].y
                    elif idx == len(self.Segments) - 2 and (self.Points[-1].y - (self.Points[-2].y + movey)) * self.Segments[-1][1] < MIN_SEGMENT_SIZE:
                        movey = round_scaling(self.Points[idx].y - MIN_SEGMENT_SIZE * self.Segments[-1][1], scaling[1], -self.Segments[-1][1]) - self.Points[idx].y
                self.Points[idx].y += movey
                self.Points[idx + 1].y += movey
                self.GeneratePoints()
                if start_y != self.Points[idx].y:
                    return 0, self.Points[idx].y - start_y
        return 0, 0

    # Adds two points in the middle of the handled segment
    def AddSegment(self):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_SEGMENT:
            segment, dir = handle
            if len(self.Segments) > 1:
                pointx = self.Points[segment].x
                pointy = self.Points[segment].y
                if dir[0] != 0:
                    pointx = (self.Points[segment].x + self.Points[segment + 1].x) // 2
                if dir[1] != 0:
                    pointy = (self.Points[segment].y + self.Points[segment + 1].y) // 2
                self.Points.insert(segment + 1, wx.Point(pointx, pointy))
                self.Segments.insert(segment + 1, (dir[1], dir[0]))
                self.Points.insert(segment + 2, wx.Point(pointx, pointy))
                self.Segments.insert(segment + 2, dir)
            else:
                p1x = p2x = self.Points[segment].x
                p1y = p2y = self.Points[segment].y
                if dir[0] != 0:
                    p1x = (2 * self.Points[segment].x + self.Points[segment + 1].x) // 3
                    p2x = (self.Points[segment].x + 2 * self.Points[segment + 1].x) // 3
                if dir[1] != 0:
                    p1y = (2 * self.Points[segment].y + self.Points[segment + 1].y) // 3
                    p2y = (self.Points[segment].y + 2 * self.Points[segment + 1].y) // 3
                self.Points.insert(segment + 1, wx.Point(p1x, p1y))
                self.Segments.insert(segment + 1, (dir[1], dir[0]))
                self.Points.insert(segment + 2, wx.Point(p1x, p1y))
                self.Segments.insert(segment + 2, dir)
                self.Points.insert(segment + 3, wx.Point(p2x, p2y))
                self.Segments.insert(segment + 3, (dir[1], dir[0]))
                self.Points.insert(segment + 4, wx.Point(p2x, p2y))
                self.Segments.insert(segment + 4, dir)
            self.GeneratePoints()

    # Delete the handled segment by removing the two segment points
    def DeleteSegment(self):
        handle_type, handle = self.Handle
        if handle_type == HANDLE_SEGMENT:
            segment, _dir = handle
            for dummy in xrange(2):
                self.Points.pop(segment)
                self.Segments.pop(segment)
            self.GeneratePoints()
            self.RefreshModel()

    # Method called when a LeftDown event have been generated
    def OnLeftDown(self, event, dc, scaling):
        pos = GetScaledEventPosition(event, dc, scaling)
        # Test if a point have been handled
        # result = self.TestPoint(pos)
        # if result != None:
        #    self.Handle = (HANDLE_POINT, result)
        #    wx.CallAfter(self.Parent.SetCurrentCursor, 1)
        # else:
        # Test if a segment have been handled
        result = self.TestSegment(pos)
        if result is not None:
            if result[1] in (NORTH, SOUTH):
                wx.CallAfter(self.Parent.SetCurrentCursor, 4)
            elif result[1] in (EAST, WEST):
                wx.CallAfter(self.Parent.SetCurrentCursor, 5)
            self.Handle = (HANDLE_SEGMENT, result)
        # Execute the default method for a graphic element
        else:
            Graphic_Element.OnLeftDown(self, event, dc, scaling)
        self.oldPos = pos

    # Method called when a RightUp event has been generated
    def OnRightUp(self, event, dc, scaling):
        pos = GetScaledEventPosition(event, dc, scaling)
        # Test if a segment has been handled
        result = self.TestSegment(pos, True)
        if result is not None:
            self.Handle = (HANDLE_SEGMENT, result)
            # Popup the menu with special items for a wire
            self.Parent.PopupWireMenu(0 < result[0] < len(self.Segments) - 1)
        else:
            # Execute the default method for a graphic element
            Graphic_Element.OnRightUp(self, event, dc, scaling)

    # Method called when a LeftDClick event has been generated
    def OnLeftDClick(self, event, dc, scaling):
        rect = self.GetRedrawRect()
        if event.ControlDown():
            direction = (self.StartPoint[1], self.EndPoint[1])
            if direction in [(EAST, WEST), (WEST, EAST)]:
                avgy = (self.StartPoint[0].y + self.EndPoint[0].y) // 2
                if scaling is not None:
                    avgy = round(avgy / scaling[1]) * scaling[1]
                if self.StartConnected is not None:
                    movey = avgy - self.StartPoint[0].y
                    startblock = self.StartConnected.GetParentBlock()
                    startblock.Move(0, movey)
                    startblock.RefreshModel()
                    rect.Union(startblock.GetRedrawRect(0, movey))
                else:
                    self.MoveStartPoint(wx.Point(self.StartPoint[0].x, avgy))
                if self.EndConnected is not None:
                    movey = avgy - self.EndPoint[0].y
                    endblock = self.EndConnected.GetParentBlock()
                    endblock.Move(0, movey)
                    endblock.RefreshModel()
                    rect.Union(endblock.GetRedrawRect(0, movey))
                else:
                    self.MoveEndPoint(wx.Point(self.EndPoint[0].x, avgy))
                self.Parent.RefreshBuffer()
            elif direction in [(NORTH, SOUTH), (SOUTH, NORTH)]:
                avgx = (self.StartPoint[0].x + self.EndPoint[0].x) // 2
                if scaling is not None:
                    avgx = round(avgx / scaling[0]) * scaling[0]
                if self.StartConnected is not None:
                    movex = avgx - self.StartPoint[0].x
                    startblock = self.StartConnected.GetParentBlock()
                    startblock.Move(movex, 0)
                    startblock.RefreshModel()
                    rect.Union(startblock.GetRedrawRect(movex, 0))
                else:
                    self.MoveStartPoint(wx.Point(avgx, self.StartPoint[0].y))
                if self.EndConnected is not None:
                    movex = avgx - self.EndPoint[0].x
                    endblock = self.EndConnected.GetParentBlock()
                    endblock.Move(movex, 0)
                    endblock.RefreshModel()
                    rect.Union(endblock.GetRedrawRect(movex, 0))
                else:
                    self.MoveEndPoint(wx.Point(avgx, self.EndPoint[0].y))
                self.Parent.RefreshBuffer()
        else:
            self.ResetPoints()
            self.GeneratePoints()
            self.RefreshModel()
            self.Parent.RefreshBuffer()
        rect.Union(self.GetRedrawRect())
        self.Parent.RefreshRect(self.Parent.GetScrolledRect(rect), False)

    # Method called when a Motion event has been generated
    def OnMotion(self, event, dc, scaling):
        pos = GetScaledEventPosition(event, dc, scaling)
        if not event.Dragging():
            # Test if a segment has been handled
            result = self.TestSegment(pos)
            if result:
                if result[1] in (NORTH, SOUTH):
                    wx.CallAfter(self.Parent.SetCurrentCursor, 4)
                elif result[1] in (EAST, WEST):
                    wx.CallAfter(self.Parent.SetCurrentCursor, 5)
                return 0, 0
            else:
                # Execute the default method for a graphic element
                return Graphic_Element.OnMotion(self, event, dc, scaling)
        else:
            # Execute the default method for a graphic element
            return Graphic_Element.OnMotion(self, event, dc, scaling)

    # Refreshes the wire state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        handle_type, handle = self.Handle
        # A point has been handled
        if handle_type == HANDLE_POINT:
            movex = max(-self.Points[handle].x + POINT_RADIUS, movex)
            movey = max(-self.Points[handle].y + POINT_RADIUS, movey)
            if scaling is not None:
                movex = round_scaling(self.Points[handle].x + movex, scaling[0]) - self.Points[handle].x
                movey = round_scaling(self.Points[handle].y + movey, scaling[1]) - self.Points[handle].y
            # Try to connect point to a connector
            new_pos = wx.Point(self.Points[handle].x + movex, self.Points[handle].y + movey)
            connector = self.Parent.FindBlockConnector(new_pos, self.GetConnectionDirection())
            if connector:
                if handle == 0 and self.EndConnected != connector:
                    connector.HighlightParentBlock(True)
                    connector.Connect((self, handle))
                    self.SetStartPointDirection(connector.GetDirection())
                    self.ConnectStartPoint(connector.GetPosition(), connector)
                    pos = connector.GetPosition()
                    movex = pos.x - self.oldPos.x
                    movey = pos.y - self.oldPos.y
                    if not connector.IsCompatible(self.GetEndConnectedType()):
                        self.SetValid(False)
                    self.Dragging = False
                elif handle != 0 and self.StartConnected != connector:
                    connector.HighlightParentBlock(True)
                    connector.Connect((self, handle))
                    self.SetEndPointDirection(connector.GetDirection())
                    self.ConnectEndPoint(connector.GetPosition(), connector)
                    pos = connector.GetPosition()
                    movex = pos.x - self.oldPos.x
                    movey = pos.y - self.oldPos.y
                    if not connector.IsCompatible(self.GetStartConnectedType()):
                        self.SetValid(False)
                    self.Dragging = False
                elif handle == 0:
                    self.MoveStartPoint(new_pos)
                else:
                    self.MoveEndPoint(new_pos)
            # If there is no connector, move the point
            elif handle == 0:
                self.SetValid(True)
                if self.StartConnected:
                    self.StartConnected.HighlightParentBlock(False)
                    self.UnConnectStartPoint()
                self.MoveStartPoint(new_pos)
            else:
                self.SetValid(True)
                if self.EndConnected:
                    self.EndConnected.HighlightParentBlock(False)
                    self.UnConnectEndPoint()
                self.MoveEndPoint(new_pos)
            return movex, movey
        # A segment has been handled, move a segment
        elif handle_type == HANDLE_SEGMENT:
            return self.MoveSegment(handle[0], movex, movey, scaling)
        # Execute the default method for a graphic element
        else:
            return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)

    # Refreshes the wire model
    def RefreshModel(self, move=True):
        if self.StartConnected and self.StartPoint[1] in [WEST, NORTH]:
            self.StartConnected.RefreshParentBlock()
        if self.EndConnected and self.EndPoint[1] in [WEST, NORTH]:
            self.EndConnected.RefreshParentBlock()

    # Change the variable that indicates if this element is highlighted
    def SetHighlighted(self, highlighted):
        self.Highlighted = highlighted
        if not highlighted:
            self.OverStart = False
            self.OverEnd = False
        self.Refresh()

    def HighlightPoint(self, pos):
        start, end = self.OverStart, self.OverEnd
        self.OverStart = False
        self.OverEnd = False
        # Test if a point has been handled
        result = self.TestPoint(pos)
        if result is not None:
            if result == 0 and self.StartConnected is not None:
                self.OverStart = True
            elif result != 0 and self.EndConnected is not None:
                self.OverEnd = True
        if start != self.OverStart or end != self.OverEnd:
            self.Refresh()

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        # If user trying to connect wire with wrong input, highlight will become red.
        if self.ErrHighlight and not self.EndConnected:
            highlightcolor = wx.RED
        else:
            highlightcolor = HIGHLIGHTCOLOR
        dc.SetPen(MiterPen(highlightcolor, (2 * scalex + 5)))
        dc.SetBrush(wx.Brush(highlightcolor))
        dc.SetLogicalFunction(wx.AND)
        # Draw the start and end points if they are not connected or the mouse is over them
        if len(self.Points) > 0 and (not self.StartConnected or self.OverStart):
            dc.DrawCircle(round(self.Points[0].x * scalex),
                          round(self.Points[0].y * scaley),
                          (POINT_RADIUS + 1) * scalex + 2)
        if len(self.Points) > 1 and (not self.EndConnected or self.OverEnd):
            dc.DrawCircle(self.Points[-1].x * scalex, self.Points[-1].y * scaley, (POINT_RADIUS + 1) * scalex + 2)
        # Draw the wire lines and the last point (it seems that DrawLines stop before the last point)
        if len(self.Points) > 1:
            points = [wx.Point(round((self.Points[0].x - self.Segments[0][0]) * scalex),
                               round((self.Points[0].y - self.Segments[0][1]) * scaley))]
            points.extend([wx.Point(round(point.x * scalex), round(point.y * scaley)) for point in self.Points[1:-1]])
            points.append(wx.Point(round((self.Points[-1].x + self.Segments[-1][0]) * scalex),
                                   round((self.Points[-1].y + self.Segments[-1][1]) * scaley)))
        else:
            points = []
        dc.DrawLines(points)
        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

        if self.StartConnected is not None:
            self.StartConnected.DrawHighlightment(dc)
            self.StartConnected.Draw(dc)
        if self.EndConnected is not None:
            self.EndConnected.DrawHighlightment(dc)
            self.EndConnected.Draw(dc)

    # Draws the wire lines and points
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        if not self.Valid:
            dc.SetPen(MiterPen(wx.RED))
            dc.SetBrush(wx.RED_BRUSH)
        elif isinstance(self.Value, bool) and self.Value:
            if self.Forced:
                dc.SetPen(MiterPen(wx.CYAN))
                dc.SetBrush(wx.CYAN_BRUSH)
            else:
                dc.SetPen(MiterPen(wx.GREEN))
                dc.SetBrush(wx.GREEN_BRUSH)
        elif self.Value == "undefined":
            dc.SetPen(MiterPen(wx.NamedColour("orange")))
            dc.SetBrush(wx.Brush(wx.NamedColour("orange")))
        elif self.Forced:
            dc.SetPen(MiterPen(wx.BLUE))
            dc.SetBrush(wx.BLUE_BRUSH)
        else:
            dc.SetPen(MiterPen(wx.BLACK))
            dc.SetBrush(wx.BLACK_BRUSH)
        # Draw the start and end points if they are not connected or the mouse is over them
        if len(self.Points) > 0 and (not self.StartConnected or self.OverStart):
            dc.DrawCircle(self.Points[0].x, self.Points[0].y, POINT_RADIUS)
        if len(self.Points) > 1 and (not self.EndConnected or self.OverEnd):
            dc.DrawCircle(self.Points[-1].x, self.Points[-1].y, POINT_RADIUS)
        # Draw the wire lines and the last point (it seems that DrawLines stop before the last point)
        if len(self.Points) > 1:
            points = [wx.Point(self.Points[0].x - self.Segments[0][0], self.Points[0].y - self.Segments[0][1])]
            points.extend([point for point in self.Points[1:-1]])
            points.append(wx.Point(self.Points[-1].x + self.Segments[-1][0], self.Points[-1].y + self.Segments[-1][1]))
        else:
            points = []
        dc.DrawLines(points)
        # Draw the segment selected in red
        if not getattr(dc, "printing", False) and self.SelectedSegment is not None:
            dc.SetPen(MiterPen(wx.BLUE, 3))
            if self.SelectedSegment == len(self.Segments) - 1:
                end = 0
            else:
                end = 1
            dc.DrawLine(self.Points[self.SelectedSegment].x - 1, self.Points[self.SelectedSegment].y,
                        self.Points[self.SelectedSegment + 1].x + end, self.Points[self.SelectedSegment + 1].y)
        if self.Value is not None and not isinstance(self.Value, bool) and self.Value != "undefined":
            dc.SetFont(self.Parent.GetMiniFont())
            dc.SetTextForeground(wx.NamedColour("purple"))
            if self.ValueSize is None and isinstance(self.ComputedValue, string_types):
                self.ValueSize = self.Parent.GetMiniTextExtent(self.ComputedValue)
            if self.ValueSize is not None:
                width, height = self.ValueSize
                if self.BoundingBox[2] > width * 4 or self.BoundingBox[3] > height * 4:
                    x = self.Points[0].x + width * (self.StartPoint[1][0] - 1) // 2
                    y = self.Points[0].y + height * (self.StartPoint[1][1] - 1)
                    dc.DrawText(self.ComputedValue, x, y)
                    x = self.Points[-1].x + width * (self.EndPoint[1][0] - 1) // 2
                    y = self.Points[-1].y + height * (self.EndPoint[1][1] - 1)
                    dc.DrawText(self.ComputedValue, x, y)
                else:
                    middle = len(self.Segments) // 2 + len(self.Segments) % 2 - 1
                    x = (self.Points[middle].x + self.Points[middle + 1].x - width) // 2
                    if self.BoundingBox[3] > height and self.Segments[middle] in [NORTH, SOUTH]:
                        y = (self.Points[middle].y + self.Points[middle + 1].y - height) // 2
                    else:
                        y = self.Points[middle].y - height
                    dc.DrawText(self.ComputedValue, x, y)
            dc.SetFont(self.Parent.GetFont())
            dc.SetTextForeground(wx.BLACK)


# -------------------------------------------------------------------------------
#                           Graphic comment element
# -------------------------------------------------------------------------------


def FilterHighlightsByRow(highlights, row, length):
    _highlights = []
    for start, end, highlight_type in highlights:
        if start[0] <= row and end[0] >= row:
            if start[0] < row:
                start = (row, 0)
            if end[0] > row:
                end = (row, length)
            _highlights.append((start, end, highlight_type))
    return _highlights


def FilterHighlightsByColumn(highlights, start_col, end_col):
    _highlights = []
    for start, end, highlight_type in highlights:
        if end[1] > start_col and start[1] < end_col:
            start = (start[0], max(start[1], start_col) - start_col)
            end = (end[0], min(end[1], end_col) - start_col)
            _highlights.append((start, end, highlight_type))
    return _highlights


class Comment(Graphic_Element):
    """
    Class that implements a comment
    """

    # Create a new comment
    def __init__(self, parent, content, id=None):
        Graphic_Element.__init__(self, parent)
        self.Id = id
        self.Content = content
        self.Pos = wx.Point(0, 0)
        self.Size = wx.Size(0, 0)
        self.Highlights = []

    # Make a clone of this comment
    def Clone(self, parent, id=None, pos=None):
        comment = Comment(parent, self.Content, id)
        if pos is not None:
            comment.SetPosition(pos.x, pos.y)
        comment.SetSize(self.Size[0], self.Size[1])
        return comment

    # Method for keeping compatibility with others
    def Clean(self):
        pass

    # Delete this comment by calling the corresponding method
    def Delete(self):
        self.Parent.DeleteComment(self)

    # Refresh the comment bounding box
    def RefreshBoundingBox(self):
        self.BoundingBox = wx.Rect(self.Pos.x, self.Pos.y, self.Size[0] + 1, self.Size[1] + 1)

    # Changes the comment size
    def SetSize(self, width, height):
        self.Size.SetWidth(width)
        self.Size.SetHeight(height)
        self.RefreshBoundingBox()

    # Returns the comment size
    def GetSize(self):
        return self.Size.GetWidth(), self.Size.GetHeight()

    # Returns the comment minimum size
    def GetMinSize(self):
        dc = wx.ClientDC(self.Parent)
        min_width = 0
        min_height = 0
        # The comment minimum size is the maximum size of words in the content
        for line in self.Content.splitlines():
            for word in line.split(" "):
                wordwidth, wordheight = dc.GetTextExtent(word)
                min_width = max(min_width, wordwidth)
                min_height = max(min_height, wordheight)
        return min_width + 20, min_height + 20

    # Changes the comment position
    def SetPosition(self, x, y):
        self.Pos.x = x
        self.Pos.y = y
        self.RefreshBoundingBox()

    # Changes the comment content
    def SetContent(self, content):
        self.Content = content
        min_width, min_height = self.GetMinSize()
        self.Size[0] = max(self.Size[0], min_width)
        self.Size[1] = max(self.Size[1], min_height)
        self.RefreshBoundingBox()

    # Returns the comment content
    def GetContent(self):
        return self.Content

    # Returns the comment position
    def GetPosition(self):
        return self.Pos.x, self.Pos.y

    # Moves the comment
    def Move(self, dx, dy, connected=True):
        self.Pos.x += dx
        self.Pos.y += dy
        self.RefreshBoundingBox()

    # Resizes the comment with the position and the size given
    def Resize(self, x, y, width, height):
        self.Move(x, y)
        self.SetSize(width, height)

    # Method called when a RightUp event have been generated
    def OnRightUp(self, event, dc, scaling):
        # Popup the default menu
        self.Parent.PopupDefaultMenu()

    # Refreshes the wire state according to move defined and handle selected
    def ProcessDragging(self, movex, movey, event, scaling):
        if self.Parent.GetDrawingMode() != FREEDRAWING_MODE and self.Parent.CurrentLanguage == "LD":
            movex = movey = 0
        return Graphic_Element.ProcessDragging(self, movex, movey, event, scaling)

    # Refreshes the comment model
    def RefreshModel(self, move=True):
        self.Parent.RefreshCommentModel(self)

    # Method called when a LeftDClick event have been generated
    def OnLeftDClick(self, event, dc, scaling):
        # Edit the comment content
        self.Parent.EditCommentContent(self)

    # Adds an highlight to the comment
    def AddHighlight(self, infos, start, end, highlight_type):
        if infos[0] == "content":
            AddHighlight(self.Highlights, (start, end, highlight_type))

    # Removes an highlight from the comment
    def RemoveHighlight(self, infos, start, end, highlight_type):
        RemoveHighlight(self.Highlights, (start, end, highlight_type))

    # Removes all the highlights of one particular type from the comment
    def ClearHighlight(self, highlight_type=None):
        self.Highlights = ClearHighlights(self.Highlights, highlight_type)

    # Draws the highlightment of this element if it is highlighted
    def DrawHighlightment(self, dc):
        scalex, scaley = dc.GetUserScale()
        dc.SetUserScale(1, 1)
        dc.SetPen(MiterPen(HIGHLIGHTCOLOR))
        dc.SetBrush(wx.Brush(HIGHLIGHTCOLOR))
        dc.SetLogicalFunction(wx.AND)

        left = (self.Pos.x - 1) * scalex - 2
        right = (self.Pos.x + self.Size[0] + 1) * scalex + 2
        top = (self.Pos.y - 1) * scaley - 2
        bottom = (self.Pos.y + self.Size[1] + 1) * scaley + 2
        angle_top = (self.Pos.x + self.Size[0] - 9) * scalex + 2
        angle_right = (self.Pos.y + 9) * scaley - 2

        polygon = [wx.Point(left, top), wx.Point(angle_top, top),
                   wx.Point(right, angle_right), wx.Point(right, bottom),
                   wx.Point(left, bottom)]
        dc.DrawPolygon(polygon)

        dc.SetLogicalFunction(wx.COPY)
        dc.SetUserScale(scalex, scaley)

    # Draws the comment and its content
    def Draw(self, dc):
        Graphic_Element.Draw(self, dc)
        dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.WHITE_BRUSH)
        # Draws the comment shape
        polygon = [wx.Point(self.Pos.x, self.Pos.y),
                   wx.Point(self.Pos.x + self.Size[0] - 10, self.Pos.y),
                   wx.Point(self.Pos.x + self.Size[0], self.Pos.y + 10),
                   wx.Point(self.Pos.x + self.Size[0], self.Pos.y + self.Size[1]),
                   wx.Point(self.Pos.x, self.Pos.y + self.Size[1])]
        dc.DrawPolygon(polygon)

        # dc.SetBrush call is workaround for the issue with wx.PrinterDC
        # with wxPython 3.0 on GNU/Linux (don't remove it)
        dc.SetBrush(wx.WHITE_BRUSH)
        lines = [wx.Point(self.Pos.x + self.Size[0] - 10, self.Pos.y),
                 wx.Point(self.Pos.x + self.Size[0] - 10, self.Pos.y + 10),
                 wx.Point(self.Pos.x + self.Size[0], self.Pos.y + 10)]
        dc.DrawLines(lines)

        # Draws the comment content
        y = self.Pos.y + 10
        for idx, line in enumerate(self.Content.splitlines()):
            first = True
            linetext = ""
            words = line.split(" ")
            if not getattr(dc, "printing", False):
                highlights = FilterHighlightsByRow(self.Highlights, idx, len(line))
                highlights_offset = 0
            for i, word in enumerate(words):
                if first:
                    text = word
                else:
                    text = linetext + " " + word
                wordwidth, wordheight = dc.GetTextExtent(text)
                if y + wordheight > self.Pos.y + self.Size[1] - 10:
                    break
                if wordwidth < self.Size[0] - 20:
                    if i < len(words) - 1:
                        linetext = text
                        first = False
                    else:
                        dc.DrawText(text, self.Pos.x + 10, y)
                        if not getattr(dc, "printing", False):
                            DrawHighlightedText(dc, text, FilterHighlightsByColumn(highlights, highlights_offset, highlights_offset + len(text)), self.Pos.x + 10, y)
                            highlights_offset += len(text) + 1
                        y += wordheight + 5
                else:
                    if not first:
                        dc.DrawText(linetext, self.Pos.x + 10, y)
                        if not getattr(dc, "printing", False):
                            DrawHighlightedText(dc, linetext, FilterHighlightsByColumn(highlights, highlights_offset, highlights_offset + len(linetext)), self.Pos.x + 10, y)
                            highlights_offset += len(linetext) + 1
                    if first or i == len(words) - 1:
                        if not first:
                            y += wordheight + 5
                            if y + wordheight > self.Pos.y + self.Size[1] - 10:
                                break
                        dc.DrawText(word, self.Pos.x + 10, y)
                        if not getattr(dc, "printing", False):
                            DrawHighlightedText(dc, word, FilterHighlightsByColumn(highlights, highlights_offset, highlights_offset + len(word)), self.Pos.x + 10, y)
                            highlights_offset += len(word) + 1
                    else:
                        linetext = word
                    y += wordheight + 5
            if y + wordheight > self.Pos.y + self.Size[1] - 10:
                break
