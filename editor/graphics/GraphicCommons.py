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


# 


from math import *

import wx

# from future.builtins import round


# from six import str
# -------------------------------------------------------------------------------
#                               Common constants
#
#            Definition of constants for dimensions of graphic elements
# -------------------------------------------------------------------------------

# FBD and SFC constants
MIN_MOVE = 5  # Minimum move before starting a element dragging
CONNECTOR_SIZE = 8  # Size of connectors
BLOCK_LINE_SIZE = 20  # Minimum size of each line in a block
HANDLE_SIZE = 6  # Size of the squares for handles
ANCHOR_DISTANCE = 5  # Distance where wire is automativally attached to a connector
POINT_RADIUS = 2  # Radius of the point of wire ends
MIN_SEGMENT_SIZE = 2  # Minimum size of the endling segments of a wire

# LD constants
LD_LINE_SIZE = 40  # Distance between two lines in a ladder rung
LD_ELEMENT_SIZE = (21, 15)  # Size (width, height) of a ladder element (contact or coil)
LD_WIRE_SIZE = 30  # Size of a wire between two contact
LD_WIRECOIL_SIZE = 70  # Size of a wire between a coil and a contact
LD_POWERRAIL_WIDTH = 3  # Width of a Powerrail
LD_OFFSET = (10, 10)  # Distance (x, y) between each comment and rung of the ladder
LD_COMMENT_DEFAULTSIZE = (600, 40)  # Size (width, height) of a comment box

# SFC constants
SFC_STEP_DEFAULT_SIZE = (40, 30)  # Default size of a SFC step
SFC_TRANSITION_SIZE = (20, 2)  # Size of a SFC transition
SFC_DEFAULT_SEQUENCE_INTERVAL = 40  # Default size of the interval between two divergence branches
SFC_SIMULTANEOUS_SEQUENCE_EXTRA = 20  # Size of extra lines for simultaneous divergence and convergence
SFC_JUMP_SIZE = (12, 13)  # Size of a SFC jump to step
SFC_WIRE_MIN_SIZE = 25  # Size of a wire between two elements
SFC_ACTION_MIN_SIZE = (100, 30)  # Minimum size of an action block line

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
HCOLOR = {'ERROR1': wx.Colour(255, 255, 0), "ERROR2": wx.RED, "S1": wx.Colour(255, 165, 0), "S2": wx.WHITE}
ERROR_HIGHLIGHT = ('ERROR1', "ERROR2")
SEARCH_RESULT_HIGHLIGHT = ("S1", "S2")

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
        dc.SetBrush(wx.Brush(HCOLOR[highlight_type[0]]))
        offset_width, _offset_height = dc.GetTextExtent(text[:start[1]])
        part = text[start[1]:end[1] + 1]
        part_width, part_height = dc.GetTextExtent(part)
        dc.DrawRectangle(x + offset_width, y, part_width, part_height)
        dc.SetTextForeground(HCOLOR[highlight_type[1]])
        dc.DrawText(part, x + offset_width, y)
    dc.SetPen(current_pen)
    dc.SetTextForeground(wx.BLACK)

# -------------------------------------------------------------------------------
#                           Graphic element base class
# -------------------------------------------------------------------------------
