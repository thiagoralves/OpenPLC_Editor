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

from editors.Viewer import *


def ExtractNextBlocks(block, block_list):
    current_list = [block]
    while len(current_list) > 0:
        next_list = []
        for current in current_list:
            connectors = current.GetConnectors()
            input_connectors = []
            if isinstance(current, LD_PowerRail) and current.GetType() == RIGHTRAIL:
                input_connectors = connectors
            else:
                if "inputs" in connectors:
                    input_connectors = connectors["inputs"]
                if "input" in connectors:
                    input_connectors = [connectors["input"]]
            for connector in input_connectors:
                for wire, _handle in connector.GetWires():
                    next = wire.EndConnected.GetParentBlock()
                    if not isinstance(next, LD_PowerRail) and next not in block_list:
                        block_list.append(next)
                        next_list.append(next)
        current_list = next_list


def CalcBranchSize(elements, stops):
    branch_size = 0
    stop_list = stops
    for stop in stops:
        ExtractNextBlocks(stop, stop_list)
    element_tree = {}
    for element in elements:
        if element not in element_tree:
            element_tree[element] = {"parents": ["start"], "children": [], "weight": None}
            GenerateTree(element, element_tree, stop_list)
        elif element_tree[element]:
            element_tree[element]["parents"].append("start")
    remove_stops = {"start": [], "stop": []}
    for element, values in element_tree.items():
        if "stop" in values["children"]:
            removed = []
            for child in values["children"]:
                if child != "stop":
                    # if child in elements:
                    #     RemoveElement(child, element_tree)
                    #     removed.append(child)
                    if "start" in element_tree[child]["parents"]:
                        if element not in remove_stops["stop"]:
                            remove_stops["stop"].append(element)
                        if child not in remove_stops["start"]:
                            remove_stops["start"].append(child)
            for child in removed:
                values["children"].remove(child)
    for element in remove_stops["start"]:
        element_tree[element]["parents"].remove("start")
    for element in remove_stops["stop"]:
        element_tree[element]["children"].remove("stop")
    for element, values in element_tree.items():
        if values and "stop" in values["children"]:
            CalcWeight(element, element_tree)
            if values["weight"]:
                branch_size += values["weight"]
            else:
                return 1
    return branch_size


def RemoveElement(remove, element_tree):
    if remove in element_tree and element_tree[remove]:
        for child in element_tree[remove]["children"]:
            if child != "stop":
                RemoveElement(child, element_tree)
        element_tree.pop(remove)
#        element_tree[remove] = None


def GenerateTree(element, element_tree, stop_list):
    if element in element_tree:
        connectors = element.GetConnectors()
        input_connectors = []
        if isinstance(element, LD_PowerRail) and element.GetType() == RIGHTRAIL:
            input_connectors = connectors
        else:
            if "inputs" in connectors:
                input_connectors = connectors["inputs"]
            if "input" in connectors:
                input_connectors = [connectors["input"]]
        for connector in input_connectors:
            for wire, _handle in connector.GetWires():
                next = wire.EndConnected.GetParentBlock()
                if isinstance(next, LD_PowerRail) and next.GetType() == LEFTRAIL or next in stop_list:
                    # for remove in element_tree[element]["children"]:
                    #     RemoveElement(remove, element_tree)
                    # element_tree[element]["children"] = ["stop"]
                    element_tree[element]["children"].append("stop")
                # elif element_tree[element]["children"] == ["stop"]:
                #     element_tree[next] = None
                elif next not in element_tree or element_tree[next]:
                    element_tree[element]["children"].append(next)
                    if next in element_tree:
                        element_tree[next]["parents"].append(element)
                    else:
                        element_tree[next] = {"parents": [element], "children": [], "weight": None}
                        GenerateTree(next, element_tree, stop_list)


def CalcWeight(element, element_tree):
    weight = 0
    parts = None
    if element in element_tree:
        for parent in element_tree[element]["parents"]:
            if parent == "start":
                weight += 1
            elif parent in element_tree:
                if not parts:
                    parts = len(element_tree[parent]["children"])
                else:
                    parts = min(parts, len(element_tree[parent]["children"]))
                if not element_tree[parent]["weight"]:
                    CalcWeight(parent, element_tree)
                if element_tree[parent]["weight"]:
                    weight += element_tree[parent]["weight"]
                else:
                    element_tree[element]["weight"] = None
                    return
            else:
                element_tree[element]["weight"] = None
                return
        if not parts:
            parts = 1
        element_tree[element]["weight"] = max(1, weight // parts)


# -------------------------------------------------------------------------------
#                     Ladder Diagram Graphic elements Viewer class
# -------------------------------------------------------------------------------


class LD_Viewer(Viewer):
    """
    Class derived from Viewer class that implements a Viewer of Ladder Diagram
    """

    def __init__(self, parent, tagname, window, controler, debug=False, instancepath=""):
        Viewer.__init__(self, parent, tagname, window, controler, debug, instancepath)
        self.Rungs = []
        self.RungComments = []
        self.CurrentLanguage = "LD"

    # -------------------------------------------------------------------------------
    #                          Refresh functions
    # -------------------------------------------------------------------------------

    def ResetView(self):
        self.Rungs = []
        self.RungComments = []
        Viewer.ResetView(self)

    def RefreshView(self, variablepanel=True, selection=None):
        Viewer.RefreshView(self, variablepanel, selection)
        if self.GetDrawingMode() != FREEDRAWING_MODE:
            for i, rung in enumerate(self.Rungs):
                bbox = rung.GetBoundingBox()
                if i < len(self.RungComments):
                    if self.RungComments[i]:
                        pos = self.RungComments[i].GetPosition()
                        if pos[1] > bbox.y:
                            self.RungComments.insert(i, None)
                else:
                    self.RungComments.insert(i, None)

    def loadInstance(self, instance, ids, selection):
        Viewer.loadInstance(self, instance, ids, selection)
        if self.GetDrawingMode() != FREEDRAWING_MODE:
            if instance["type"] == "leftPowerRail":
                element = self.FindElementById(instance["id"])
                rung = Graphic_Group(self)
                rung.SelectElement(element)
                self.Rungs.append(rung)
            elif instance["type"] == "rightPowerRail":
                rungs = []
                for connector in instance["inputs"]:
                    for link in connector["links"]:
                        connected = self.FindElementById(link["refLocalId"])
                        rung = self.FindRung(connected)
                        if rung not in rungs:
                            rungs.append(rung)
                if len(rungs) > 1:
                    raise ValueError(
                        _("Ladder element with id %d is on more than one rung.")
                        % instance["id"])

                element = self.FindElementById(instance["id"])
                element_connectors = element.GetConnectors()
                self.Rungs[rungs[0]].SelectElement(element)
                for connector in element_connectors["inputs"]:
                    for wire, _num in connector.GetWires():
                        self.Rungs[rungs[0]].SelectElement(wire)
                wx.CallAfter(self.RefreshPosition, element)
            elif instance["type"] in ["contact", "coil"]:
                rungs = []
                for link in instance["inputs"][0]["links"]:
                    connected = self.FindElementById(link["refLocalId"])
                    rung = self.FindRung(connected)
                    if rung not in rungs:
                        rungs.append(rung)
                if len(rungs) > 1:
                    raise ValueError(
                        _("Ladder element with id %d is on more than one rung.")
                        % instance["id"])

                element = self.FindElementById(instance["id"])
                element_connectors = element.GetConnectors()
                self.Rungs[rungs[0]].SelectElement(element)
                for wire, _num in element_connectors["inputs"][0].GetWires():
                    self.Rungs[rungs[0]].SelectElement(wire)
                wx.CallAfter(self.RefreshPosition, element)
            elif instance["type"] == "comment":
                element = self.FindElementById(instance["id"])
                pos = element.GetPosition()
                i = 0
                inserted = False
                while i < len(self.RungComments) and not inserted:
                    ipos = self.RungComments[i].GetPosition()
                    if pos[1] < ipos[1]:
                        self.RungComments.insert(i, element)
                        inserted = True
                    i += 1
                if not inserted:
                    self.RungComments.append(element)

    # -------------------------------------------------------------------------------
    #                          Search Element functions
    # -------------------------------------------------------------------------------

    def FindRung(self, element):
        for i, rung in enumerate(self.Rungs):
            if rung.IsElementIn(element):
                return i
        return None

    def FindElement(self, event, exclude_group=False, connectors=True):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            return Viewer.FindElement(self, event, exclude_group, connectors)

        dc = self.GetLogicalDC()
        pos = event.GetLogicalPosition(dc)
        if self.SelectedElement and not isinstance(self.SelectedElement, (Graphic_Group, Wire)):
            if self.SelectedElement.HitTest(pos, connectors) or self.SelectedElement.TestHandle(pos) != (0, 0):
                return self.SelectedElement
        elements = []
        for element in self.GetElements(sort_wires=True):
            if element.HitTest(pos, connectors) or element.TestHandle(event) != (0, 0):
                elements.append(element)
        if len(elements) == 1:
            return elements[0]
        elif len(elements) > 1:
            group = Graphic_Group(self)
            for element in elements:
                if self.IsBlock(element):
                    return element
                group.SelectElement(element)
            return group
        return None

    def SearchElements(self, bbox):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            return Viewer.SearchElements(self, bbox)

        elements = []
        for element in self.Blocks.values() + self.Comments.values():
            if element.IsInSelection(bbox):
                elements.append(element)
        return elements

    # -------------------------------------------------------------------------------
    #                          Mouse event functions
    # -------------------------------------------------------------------------------

    def OnViewerLeftDown(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.OnViewerLeftDown(self, event)
        elif self.Mode == MODE_SELECTION:
            element = self.FindElement(event)
            if self.SelectedElement:
                if not isinstance(self.SelectedElement, Graphic_Group):
                    if self.SelectedElement != element:
                        if self.IsWire(self.SelectedElement):
                            self.SelectedElement.SetSelectedSegment(None)
                        else:
                            self.SelectedElement.SetSelected(False)
                    else:
                        self.SelectedElement = None
                elif element and isinstance(element, Graphic_Group):
                    if self.SelectedElement.GetElements() != element.GetElements():
                        for elt in self.SelectedElement.GetElements():
                            if self.IsWire(elt):
                                elt.SetSelectedSegment(None)
                        self.SelectedElement.SetSelected(False)
                        self.SelectedElement = None
                else:
                    for elt in self.SelectedElement.GetElements():
                        if self.IsWire(elt):
                            elt.SetSelectedSegment(None)
                    self.SelectedElement.SetSelected(False)
                    self.SelectedElement = None
            if element:
                self.SelectedElement = element
                self.SelectedElement.OnLeftDown(event, self.GetLogicalDC(), self.Scaling)
                self.SelectedElement.Refresh()
            else:
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
        elif self.Mode == MODE_SELECTION and self.SelectedElement:
            dc = self.GetLogicalDC()
            if not isinstance(self.SelectedElement, Graphic_Group):
                if self.IsWire(self.SelectedElement):
                    result = self.SelectedElement.TestSegment(event.GetLogicalPosition(dc), True)
                    if result and result[1] in [EAST, WEST]:
                        self.SelectedElement.SetSelectedSegment(result[0])
                else:
                    self.SelectedElement.OnLeftUp(event, dc, self.Scaling)
            else:
                for element in self.SelectedElement.GetElements():
                    if self.IsWire(element):
                        result = element.TestSegment(event.GetLogicalPosition(dc), True)
                        if result and result[1] in [EAST, WEST]:
                            element.SetSelectedSegment(result[0])
                    else:
                        element.OnLeftUp(event, dc, self.Scaling)
            self.SelectedElement.Refresh()
            wx.CallAfter(self.SetCurrentCursor, 0)
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
            if keycode == wx.WXK_DELETE and self.SelectedElement:
                if self.IsBlock(self.SelectedElement):
                    self.SelectedElement.Delete()
                elif self.IsWire(self.SelectedElement):
                    self.DeleteWire(self.SelectedElement)
                elif isinstance(self.SelectedElement, Graphic_Group):
                    all_wires = True
                    for element in self.SelectedElement.GetElements():
                        all_wires &= self.IsWire(element)
                    if all_wires:
                        self.DeleteWire(self.SelectedElement)
                    else:
                        self.SelectedElement.Delete()
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.Refresh(False)
            elif keycode == wx.WXK_LEFT:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(0, ypos)
                elif event.ControlDown():
                    self.Scroll(max(0, xpos - 1), ypos)
            elif keycode == wx.WXK_RIGHT:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(xmax, ypos)
                elif event.ControlDown():
                    self.Scroll(min(xpos + 1, xmax), ypos)
            elif keycode == wx.WXK_UP:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(xpos, 0)
                elif event.ControlDown():
                    self.Scroll(xpos, max(0, ypos - 1))
            elif keycode == wx.WXK_DOWN:
                if event.ControlDown() and event.ShiftDown():
                    self.Scroll(xpos, ymax)
                elif event.ControlDown():
                    self.Scroll(xpos, min(ypos + 1, ymax))
            else:
                event.Skip()

    # -------------------------------------------------------------------------------
    #                  Model adding functions from Drop Target
    # -------------------------------------------------------------------------------

    def AddVariableBlock(self, x, y, scaling, var_class, var_name, var_type):
        if var_type == "BOOL":
            id = self.GetNewId()
            if var_class == INPUT:
                contact = LD_Contact(self, CONTACT_NORMAL, var_name, id)
                width, height = contact.GetMinSize()
                if scaling is not None:
                    x = round(x / scaling[0]) * scaling[0]
                    y = round(y / scaling[1]) * scaling[1]
                    width = round(width / scaling[0] + 0.5) * scaling[0]
                    height = round(height / scaling[1] + 0.5) * scaling[1]
                contact.SetPosition(x, y)
                contact.SetSize(width, height)
                self.AddBlock(contact)
                self.Controler.AddEditedElementContact(self.GetTagName(), id)
                self.RefreshContactModel(contact)
            else:
                coil = LD_Coil(self, COIL_NORMAL, var_name, id)
                width, height = coil.GetMinSize()
                if scaling is not None:
                    x = round(x / scaling[0]) * scaling[0]
                    y = round(y / scaling[1]) * scaling[1]
                    width = round(width / scaling[0] + 0.5) * scaling[0]
                    height = round(height / scaling[1] + 0.5) * scaling[1]
                coil.SetPosition(x, y)
                coil.SetSize(width, height)
                self.AddBlock(coil)
                self.Controler.AddEditedElementCoil(self.GetTagName(), id)
                self.RefreshCoilModel(coil)
            self.RefreshBuffer()
            self.RefreshScrollBars()
            self.RefreshVisibleElements()
            self.Refresh(False)
        else:
            Viewer.AddVariableBlock(self, x, y, scaling, var_class, var_name, var_type)

    # -------------------------------------------------------------------------------
    #                          Adding element functions
    # -------------------------------------------------------------------------------

    def AddLadderRung(self):
        dialog = LDElementDialog(self.ParentWindow, self.Controler, self.TagName, "coil")
        dialog.SetPreviewFont(self.GetFont())
        varlist = []
        vars = self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug)
        if vars:
            for var in vars:
                if var.Class != "Input" and var.Type == "BOOL":
                    varlist.append(var.Name)
        returntype = self.Controler.GetEditedElementInterfaceReturnType(self.TagName, debug=self.Debug)
        if returntype == "BOOL":
            varlist.append(self.Controler.GetEditedElementName(self.TagName))
        dialog.SetVariables(varlist)
        dialog.SetValues({"name": "", "type": COIL_NORMAL})
        if dialog.ShowModal() == wx.ID_OK:
            values = dialog.GetValues()
            startx, starty = LD_OFFSET[0], 0
            if len(self.Rungs) > 0:
                bbox = self.Rungs[-1].GetBoundingBox()
                starty = bbox.y + bbox.height
            starty += LD_OFFSET[1]
            rung = Graphic_Group(self)

            # Create comment
            id = self.GetNewId()
            comment = Comment(self, _("Comment"), id)
            comment.SetPosition(startx, starty)
            comment.SetSize(LD_COMMENT_DEFAULTSIZE[0], LD_COMMENT_DEFAULTSIZE[1])
            self.AddComment(comment)
            self.RungComments.append(comment)
            self.Controler.AddEditedElementComment(self.TagName, id)
            self.RefreshCommentModel(comment)
            starty += LD_COMMENT_DEFAULTSIZE[1] + LD_OFFSET[1]

            # Create LeftPowerRail
            id = self.GetNewId()
            leftpowerrail = LD_PowerRail(self, LEFTRAIL, id)
            leftpowerrail.SetPosition(startx, starty)
            leftpowerrail_connectors = leftpowerrail.GetConnectors()
            self.AddBlock(leftpowerrail)
            rung.SelectElement(leftpowerrail)
            self.Controler.AddEditedElementPowerRail(self.TagName, id, LEFTRAIL)
            self.RefreshPowerRailModel(leftpowerrail)

            # Create Coil
            id = self.GetNewId()
            coil = LD_Coil(self, values["type"], values["name"], id)
            coil.SetPosition(startx, starty + (LD_LINE_SIZE - LD_ELEMENT_SIZE[1]) // 2)
            coil_connectors = coil.GetConnectors()
            self.AddBlock(coil)
            rung.SelectElement(coil)
            self.Controler.AddEditedElementCoil(self.TagName, id)

            # Create Wire between LeftPowerRail and Coil
            wire = Wire(self)
            start_connector = coil_connectors["inputs"][0]
            end_connector = leftpowerrail_connectors["outputs"][0]
            start_connector.Connect((wire, 0), False)
            end_connector.Connect((wire, -1), False)
            wire.ConnectStartPoint(None, start_connector)
            wire.ConnectEndPoint(None, end_connector)
            self.AddWire(wire)
            rung.SelectElement(wire)

            # Create RightPowerRail
            id = self.GetNewId()
            rightpowerrail = LD_PowerRail(self, RIGHTRAIL, id)
            rightpowerrail.SetPosition(startx, starty)
            rightpowerrail_connectors = rightpowerrail.GetConnectors()
            self.AddBlock(rightpowerrail)
            rung.SelectElement(rightpowerrail)
            self.Controler.AddEditedElementPowerRail(self.TagName, id, RIGHTRAIL)

            # Create Wire between LeftPowerRail and Coil
            wire = Wire(self)
            start_connector = rightpowerrail_connectors["inputs"][0]
            end_connector = coil_connectors["outputs"][0]
            start_connector.Connect((wire, 0), False)
            end_connector.Connect((wire, -1), False)
            wire.ConnectStartPoint(None, start_connector)
            wire.ConnectEndPoint(None, end_connector)
            self.AddWire(wire)
            rung.SelectElement(wire)
            self.RefreshPosition(coil)
            self.Rungs.append(rung)
            self.RefreshBuffer()
            self.RefreshScrollBars()
            self.RefreshVisibleElements()
            self.Refresh(False)

    def AddLadderContact(self):
        wires = []
        if self.IsWire(self.SelectedElement):
            left_element = self.SelectedElement.EndConnected
            if not isinstance(left_element.GetParentBlock(), LD_Coil):
                wires.append(self.SelectedElement)
        elif self.SelectedElement and isinstance(self.SelectedElement, Graphic_Group):
            if False not in [self.IsWire(element) for element in self.SelectedElement.GetElements()]:
                for element in self.SelectedElement.GetElements():
                    wires.append(element)
        if len(wires) > 0:
            dialog = LDElementDialog(self.ParentWindow, self.Controler, self.TagName, "contact")
            dialog.SetPreviewFont(self.GetFont())
            varlist = []
            vars = self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug)
            if vars:
                for var in vars:
                    if var.Class != "Output" and var.Type == "BOOL":
                        varlist.append(var.Name)
            dialog.SetVariables(varlist)
            dialog.SetValues({"name": "", "type": CONTACT_NORMAL})
            if dialog.ShowModal() == wx.ID_OK:
                values = dialog.GetValues()
                points = wires[0].GetSelectedSegmentPoints()
                id = self.GetNewId()
                contact = LD_Contact(self, values["type"], values["name"], id)
                contact.SetPosition(0, points[0].y - (LD_ELEMENT_SIZE[1] + 1) // 2)
                self.AddBlock(contact)
                self.Controler.AddEditedElementContact(self.TagName, id)
                rungindex = self.FindRung(wires[0])
                rung = self.Rungs[rungindex]
                old_bbox = rung.GetBoundingBox()
                rung.SelectElement(contact)
                connectors = contact.GetConnectors()
                left_elements = []
                right_elements = []
                left_index = []
                right_index = []
                for wire in wires:
                    if wire.EndConnected not in left_elements:
                        left_elements.append(wire.EndConnected)
                        left_index.append(wire.EndConnected.GetWireIndex(wire))
                    else:
                        idx = left_elements.index(wire.EndConnected)
                        left_index[idx] = min(left_index[idx], wire.EndConnected.GetWireIndex(wire))
                    if wire.StartConnected not in right_elements:
                        right_elements.append(wire.StartConnected)
                        right_index.append(wire.StartConnected.GetWireIndex(wire))
                    else:
                        idx = right_elements.index(wire.StartConnected)
                        right_index[idx] = min(right_index[idx], wire.StartConnected.GetWireIndex(wire))
                    wire.SetSelectedSegment(None)
                    wire.Clean()
                    rung.SelectElement(wire)
                    self.RemoveWire(wire)
                wires = []
                right_wires = []
                for i, left_element in enumerate(left_elements):
                    wire = Wire(self)
                    wires.append(wire)
                    connectors["inputs"][0].Connect((wire, 0), False)
                    left_element.InsertConnect(left_index[i], (wire, -1), False)
                    wire.ConnectStartPoint(None, connectors["inputs"][0])
                    wire.ConnectEndPoint(None, left_element)
                for i, right_element in enumerate(right_elements):
                    wire = Wire(self)
                    wires.append(wire)
                    right_wires.append(wire)
                    right_element.InsertConnect(right_index[i], (wire, 0), False)
                    connectors["outputs"][0].Connect((wire, -1), False)
                    wire.ConnectStartPoint(None, right_element)
                    wire.ConnectEndPoint(None, connectors["outputs"][0])
                right_wires.reverse()
                for wire in wires:
                    self.AddWire(wire)
                    rung.SelectElement(wire)
                self.RefreshPosition(contact)
                if len(right_wires) > 1:
                    group = Graphic_Group(self)
                    group.SetSelected(False)
                    for wire in right_wires:
                        wire.SetSelectedSegment(-1)
                        group.SelectElement(wire)
                    self.SelectedElement = group
                else:
                    right_wires[0].SetSelectedSegment(-1)
                    self.SelectedElement = right_wires[0]
                rung.RefreshBoundingBox()
                new_bbox = rung.GetBoundingBox()
                self.RefreshRungs(new_bbox.height - old_bbox.height, rungindex + 1)
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.RefreshVisibleElements()
                self.Refresh(False)
        else:
            message = wx.MessageDialog(self, _("You must select the wire where a contact should be added!"), _("Error"), wx.OK | wx.ICON_ERROR)
            message.ShowModal()
            message.Destroy()

    def AddLadderBranch(self):
        blocks = []
        if self.IsBlock(self.SelectedElement):
            blocks = [self.SelectedElement]
        elif isinstance(self.SelectedElement, Graphic_Group):
            elements = self.SelectedElement.GetElements()
            for element in elements:
                blocks.append(element)
        if len(blocks) > 0:
            blocks_infos = []
            left_elements = []
            left_index = []
            right_elements = []
            right_index = []
            for block in blocks:
                connectors = block.GetConnectors()
                block_infos = {"lefts": [], "rights": []}
                block_infos.update(connectors)
                for connector in block_infos["inputs"]:
                    for wire, _handle in connector.GetWires():
                        found = False
                        for infos in blocks_infos:
                            if wire.EndConnected in infos["outputs"]:
                                for left_element in infos["lefts"]:
                                    if left_element not in block_infos["lefts"]:
                                        block_infos["lefts"].append(left_element)
                                found = True
                        if not found and wire.EndConnected not in block_infos["lefts"]:
                            block_infos["lefts"].append(wire.EndConnected)
                            if wire.EndConnected not in left_elements:
                                left_elements.append(wire.EndConnected)
                                left_index.append(wire.EndConnected.GetWireIndex(wire))
                            else:
                                index = left_elements.index(wire.EndConnected)
                                left_index[index] = max(left_index[index], wire.EndConnected.GetWireIndex(wire))
                for connector in block_infos["outputs"]:
                    for wire, _handle in connector.GetWires():
                        found = False
                        for infos in blocks_infos:
                            if wire.StartConnected in infos["inputs"]:
                                for right_element in infos["rights"]:
                                    if right_element not in block_infos["rights"]:
                                        block_infos["rights"].append(right_element)
                                found = True
                        if not found and wire.StartConnected not in block_infos["rights"]:
                            block_infos["rights"].append(wire.StartConnected)
                            if wire.StartConnected not in right_elements:
                                right_elements.append(wire.StartConnected)
                                right_index.append(wire.StartConnected.GetWireIndex(wire))
                            else:
                                index = right_elements.index(wire.StartConnected)
                                right_index[index] = max(right_index[index], wire.StartConnected.GetWireIndex(wire))
                for connector in block_infos["inputs"]:
                    for infos in blocks_infos:
                        if connector in infos["rights"]:
                            infos["rights"].remove(connector)
                            if connector in right_elements:
                                index = right_elements.index(connector)
                                right_elements.pop(index)
                                right_index.pop(index)
                            for right_element in block_infos["rights"]:
                                if right_element not in infos["rights"]:
                                    infos["rights"].append(right_element)
                for connector in block_infos["outputs"]:
                    for infos in blocks_infos:
                        if connector in infos["lefts"]:
                            infos["lefts"].remove(connector)
                            if connector in left_elements:
                                index = left_elements.index(connector)
                                left_elements.pop(index)
                                left_index.pop(index)
                            for left_element in block_infos["lefts"]:
                                if left_element not in infos["lefts"]:
                                    infos["lefts"].append(left_element)
                blocks_infos.append(block_infos)
            for infos in blocks_infos:
                left_elements = [element for element in infos["lefts"]]
                for left_element in left_elements:
                    if isinstance(left_element.GetParentBlock(), LD_PowerRail):
                        infos["lefts"].remove(left_element)
                        if "LD_PowerRail" not in infos["lefts"]:
                            infos["lefts"].append("LD_PowerRail")
                right_elements = [element for element in infos["rights"]]
                for right_element in right_elements:
                    if isinstance(right_element.GetParentBlock(), LD_PowerRail):
                        infos["rights"].remove(right_element)
                        if "LD_PowerRail" not in infos["rights"]:
                            infos["rights"].append("LD_PowerRail")
                infos["lefts"].sort()
                infos["rights"].sort()
            lefts = blocks_infos[0]["lefts"]
            rights = blocks_infos[0]["rights"]
            good = True
            for infos in blocks_infos[1:]:
                good &= infos["lefts"] == lefts
                good &= infos["rights"] == rights
            if good:
                rungindex = self.FindRung(blocks[0])
                rung = self.Rungs[rungindex]
                old_bbox = rung.GetBoundingBox()
                left_powerrail = True
                right_powerrail = True
                for element in left_elements:
                    left_powerrail &= isinstance(element.GetParentBlock(), LD_PowerRail)
                for element in right_elements:
                    right_powerrail &= isinstance(element.GetParentBlock(), LD_PowerRail)
                if not left_powerrail or not right_powerrail:
                    wires = []
                    if left_powerrail:
                        powerrail = left_elements[0].GetParentBlock()
                        index = 0
                        for left_element in left_elements:
                            index = max(index, powerrail.GetConnectorIndex(left_element))
                        powerrail.InsertConnector(index + 1)
                        powerrail.RefreshModel()
                        connectors = powerrail.GetConnectors()
                        right_elements.reverse()
                        for i, right_element in enumerate(right_elements):
                            new_wire = Wire(self)
                            wires.append(new_wire)
                            right_element.InsertConnect(right_index[i] + 1, (new_wire, 0), False)
                            connectors["outputs"][index + 1].Connect((new_wire, -1), False)
                            new_wire.ConnectStartPoint(None, right_element)
                            new_wire.ConnectEndPoint(None, connectors["outputs"][index + 1])
                        right_elements.reverse()
                    elif right_powerrail:
                        dialog = LDElementDialog(self.ParentWindow, self.Controleur, self.TagName, "coil")
                        dialog.SetPreviewFont(self.GetFont())
                        varlist = []
                        vars = self.Controler.GetEditedElementInterfaceVars(self.TagName, debug=self.Debug)
                        if vars:
                            for var in vars:
                                if var.Class != "Input" and var.Type == "BOOL":
                                    varlist.append(var.Name)
                        returntype = self.Controler.GetEditedElementInterfaceReturnType(self.TagName, debug=self.Debug)
                        if returntype == "BOOL":
                            varlist.append(self.Controler.GetEditedElementName(self.TagName))
                        dialog.SetVariables(varlist)
                        dialog.SetValues({"name": "", "type": COIL_NORMAL})
                        if dialog.ShowModal() == wx.ID_OK:
                            values = dialog.GetValues()
                            powerrail = right_elements[0].GetParentBlock()
                            index = 0
                            for right_element in right_elements:
                                index = max(index, powerrail.GetConnectorIndex(right_element))
                            powerrail.InsertConnector(index + 1)
                            powerrail.RefreshModel()
                            connectors = powerrail.GetConnectors()

                            # Create Coil
                            id = self.GetNewId()
                            coil = LD_Coil(self, values["type"], values["name"], id)
                            pos = blocks[0].GetPosition()
                            coil.SetPosition(pos[0], pos[1] + LD_LINE_SIZE)
                            self.AddBlock(coil)
                            rung.SelectElement(coil)
                            self.Controler.AddEditedElementCoil(self.TagName, id)
                            coil_connectors = coil.GetConnectors()

                            # Create Wire between LeftPowerRail and Coil
                            wire = Wire(self)
                            connectors["inputs"][index + 1].Connect((wire, 0), False)
                            coil_connectors["outputs"][0].Connect((wire, -1), False)
                            wire.ConnectStartPoint(None, connectors["inputs"][index + 1])
                            wire.ConnectEndPoint(None, coil_connectors["outputs"][0])
                            self.AddWire(wire)
                            rung.SelectElement(wire)
                            left_elements.reverse()

                            for i, left_element in enumerate(left_elements):
                                # Create Wire between LeftPowerRail and Coil
                                new_wire = Wire(self)
                                wires.append(new_wire)
                                coil_connectors["inputs"][0].Connect((new_wire, 0), False)
                                left_element.InsertConnect(left_index[i] + 1, (new_wire, -1), False)
                                new_wire.ConnectStartPoint(None, coil_connectors["inputs"][0])
                                new_wire.ConnectEndPoint(None, left_element)

                            self.RefreshPosition(coil)
                    else:
                        left_elements.reverse()
                        right_elements.reverse()
                        for i, left_element in enumerate(left_elements):
                            for j, right_element in enumerate(right_elements):
                                exist = False
                                for wire, _handle in right_element.GetWires():
                                    exist |= wire.EndConnected == left_element
                                if not exist:
                                    new_wire = Wire(self)
                                    wires.append(new_wire)
                                    right_element.InsertConnect(right_index[j] + 1, (new_wire, 0), False)
                                    left_element.InsertConnect(left_index[i] + 1, (new_wire, -1), False)
                                    new_wire.ConnectStartPoint(None, right_element)
                                    new_wire.ConnectEndPoint(None, left_element)
                    wires.reverse()
                    for wire in wires:
                        self.AddWire(wire)
                        rung.SelectElement(wire)
                    right_elements.reverse()
                for block in blocks:
                    self.RefreshPosition(block)
                for right_element in right_elements:
                    self.RefreshPosition(right_element.GetParentBlock())
                self.SelectedElement.RefreshBoundingBox()
                rung.RefreshBoundingBox()
                new_bbox = rung.GetBoundingBox()
                self.RefreshRungs(new_bbox.height - old_bbox.height, rungindex + 1)
                self.RefreshBuffer()
                self.RefreshScrollBars()
                self.RefreshVisibleElements()
                self.Refresh(False)
            else:
                message = wx.MessageDialog(self, _("The group of block must be coherent!"), _("Error"), wx.OK | wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
        else:
            message = wx.MessageDialog(self, _("You must select the block or group of blocks around which a branch should be added!"), _("Error"), wx.OK | wx.ICON_ERROR)
            message.ShowModal()
            message.Destroy()

    def AddLadderBlock(self):
        message = wx.MessageDialog(self, _("This option isn't available yet!"), _("Warning"), wx.OK | wx.ICON_EXCLAMATION)
        message.ShowModal()
        message.Destroy()

    # -------------------------------------------------------------------------------
    #                          Delete element functions
    # -------------------------------------------------------------------------------

    def DeleteContact(self, contact):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteContact(self, contact)
        else:
            rungindex = self.FindRung(contact)
            rung = self.Rungs[rungindex]
            old_bbox = rung.GetBoundingBox()
            connectors = contact.GetConnectors()
            input_wires = [wire for wire, _handle in connectors["inputs"][0].GetWires()]
            output_wires = [wire for wire, _handle in connectors["outputs"][0].GetWires()]
            left_elements = [(wire.EndConnected, wire.EndConnected.GetWireIndex(wire)) for wire in input_wires]
            right_elements = [(wire.StartConnected, wire.StartConnected.GetWireIndex(wire)) for wire in output_wires]
            for wire in input_wires:
                wire.Clean()
                rung.SelectElement(wire)
                self.RemoveWire(wire)
            for wire in output_wires:
                wire.Clean()
                rung.SelectElement(wire)
                self.RemoveWire(wire)
            rung.SelectElement(contact)
            contact.Clean()
            left_elements.reverse()
            right_elements.reverse()
            powerrail = len(left_elements) == 1 and isinstance(left_elements[0][0].GetParentBlock(), LD_PowerRail)
            for left_element, left_index in left_elements:
                for right_element, right_index in right_elements:
                    wire_removed = []
                    for wire, _handle in right_element.GetWires():
                        if wire.EndConnected == left_element:
                            wire_removed.append(wire)
                        elif isinstance(wire.EndConnected.GetParentBlock(), LD_PowerRail) and powerrail:
                            left_powerrail = wire.EndConnected.GetParentBlock()
                            index = left_powerrail.GetConnectorIndex(wire.EndConnected)
                            left_powerrail.DeleteConnector(index)
                            wire_removed.append(wire)
                    for wire in wire_removed:
                        wire.Clean()
                        self.RemoveWire(wire)
                        rung.SelectElement(wire)
            wires = []
            for left_element, left_index in left_elements:
                for right_element, right_index in right_elements:
                    wire = Wire(self)
                    wires.append(wire)
                    right_element.InsertConnect(right_index, (wire, 0), False)
                    left_element.InsertConnect(left_index, (wire, -1), False)
                    wire.ConnectStartPoint(None, right_element)
                    wire.ConnectEndPoint(None, left_element)
            wires.reverse()
            for wire in wires:
                self.AddWire(wire)
                rung.SelectElement(wire)
            right_elements.reverse()
            for right_element, right_index in right_elements:
                self.RefreshPosition(right_element.GetParentBlock())
            self.RemoveBlock(contact)
            self.Controler.RemoveEditedElementInstance(self.TagName, contact.GetId())
            rung.RefreshBoundingBox()
            new_bbox = rung.GetBoundingBox()
            self.RefreshRungs(new_bbox.height - old_bbox.height, rungindex + 1)
            self.SelectedElement = None

    def RecursiveDeletion(self, element, rung):
        connectors = element.GetConnectors()
        input_wires = [wire for wire, _handle in connectors["inputs"][0].GetWires()]
        left_elements = [wire.EndConnected for wire in input_wires]
        rung.SelectElement(element)
        element.Clean()
        for wire in input_wires:
            wire.Clean()
            self.RemoveWire(wire)
            rung.SelectElement(wire)
        self.RemoveBlock(element)
        self.Controler.RemoveEditedElementInstance(self.TagName, element.GetId())
        for left_element in left_elements:
            block = left_element.GetParentBlock()
            if len(left_element.GetWires()) == 0:
                self.RecursiveDeletion(block, rung)
            else:
                self.RefreshPosition(block)

    def DeleteCoil(self, coil):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteContact(self, coil)
        else:
            rungindex = self.FindRung(coil)
            rung = self.Rungs[rungindex]
            old_bbox = rung.GetBoundingBox()
            nbcoils = 0
            for element in rung.GetElements():
                if isinstance(element, LD_Coil):
                    nbcoils += 1
            if nbcoils > 1:
                connectors = coil.GetConnectors()
                output_wires = [wire for wire, _handle in connectors["outputs"][0].GetWires()]
                right_elements = [wire.StartConnected for wire in output_wires]
                for wire in output_wires:
                    wire.Clean()
                    self.Wires.remove(wire)
                    self.Elements.remove(wire)
                    rung.SelectElement(wire)
                for right_element in right_elements:
                    right_block = right_element.GetParentBlock()
                    if isinstance(right_block, LD_PowerRail):
                        if len(right_element.GetWires()) == 0:
                            index = right_block.GetConnectorIndex(right_element)
                            right_block.DeleteConnector(index)
                            powerrail_connectors = right_block.GetConnectors()
                            for connector in powerrail_connectors["inputs"]:
                                for wire, _handle in connector.GetWires():
                                    block = wire.EndConnected.GetParentBlock()
                                    endpoint = wire.EndConnected.GetPosition(False)
                                    startpoint = connector.GetPosition(False)
                                    block.Move(0, startpoint.y - endpoint.y)
                                    self.RefreshPosition(block)
                self.RecursiveDeletion(coil, rung)
            else:
                for element in rung.GetElements():
                    if self.IsWire(element):
                        element.Clean()
                        self.RemoveWire(element)
                for element in rung.GetElements():
                    if self.IsBlock(element):
                        self.Controler.RemoveEditedElementInstance(self.TagName, element.GetId())
                        self.RemoveBlock(element)
                self.Controler.RemoveEditedElementInstance(self.TagName, self.Comments[rungindex].GetId())
                self.RemoveComment(self.RungComments[rungindex])
                self.RungComments.pop(rungindex)
                self.Rungs.pop(rungindex)
                if rungindex < len(self.Rungs):
                    next_bbox = self.Rungs[rungindex].GetBoundingBox()
                    self.RefreshRungs(old_bbox.y - next_bbox.y, rungindex)
            self.SelectedElement = None

    def DeleteWire(self, wire):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.DeleteWire(self, wire)
        else:
            wires = []
            left_elements = []
            right_elements = []
            if self.IsWire(wire):
                wires = [wire]
            elif isinstance(wire, Graphic_Group):
                for element in wire.GetElements():
                    if self.IsWire(element):
                        wires.append(element)
                    else:
                        wires = []
                        break
            if len(wires) > 0:
                rungindex = self.FindRung(wires[0])
                rung = self.Rungs[rungindex]
                old_bbox = rung.GetBoundingBox()
                for w in wires:
                    connections = w.GetSelectedSegmentConnections()
                    left_block = w.EndConnected.GetParentBlock()
                    if w.EndConnected not in left_elements:
                        left_elements.append(w.EndConnected)
                    if w.StartConnected not in right_elements:
                        right_elements.append(w.StartConnected)
                    if connections == (False, False) or connections == (False, True) and isinstance(left_block, LD_PowerRail):
                        w.Clean()
                        self.RemoveWire(w)
                        rung.SelectElement(w)
                for left_element in left_elements:
                    left_block = left_element.GetParentBlock()
                    if isinstance(left_block, LD_PowerRail):
                        if len(left_element.GetWires()) == 0:
                            index = left_block.GetConnectorIndex(left_element)
                            left_block.DeleteConnector(index)
                    else:
                        connectors = left_block.GetConnectors()
                        for connector in connectors["outputs"]:
                            for lwire, _handle in connector.GetWires():
                                self.RefreshPosition(lwire.StartConnected.GetParentBlock())
                for right_element in right_elements:
                    self.RefreshPosition(right_element.GetParentBlock())
                rung.RefreshBoundingBox()
                new_bbox = rung.GetBoundingBox()
                self.RefreshRungs(new_bbox.height - old_bbox.height, rungindex + 1)
                self.SelectedElement = None

    # -------------------------------------------------------------------------------
    #                        Refresh element position functions
    # -------------------------------------------------------------------------------

    def RefreshPosition(self, element, recursive=True):
        # If element is LeftPowerRail, no need to update position
        if isinstance(element, LD_PowerRail) and element.GetType() == LEFTRAIL:
            element.RefreshModel()
            return

        # Extract max position of the elements connected to input
        connectors = element.GetConnectors()
        position = element.GetPosition()
        maxx = 0
        onlyone = []
        for connector in connectors["inputs"]:
            onlyone.append(len(connector.GetWires()) == 1)
            for wire, _handle in connector.GetWires():
                onlyone[-1] &= len(wire.EndConnected.GetWires()) == 1
                leftblock = wire.EndConnected.GetParentBlock()
                pos = leftblock.GetPosition()
                size = leftblock.GetSize()
                maxx = max(maxx, pos[0] + size[0])

        # Refresh position of element
        if isinstance(element, LD_Coil):
            interval = LD_WIRECOIL_SIZE
        else:
            interval = LD_WIRE_SIZE
        if False in onlyone:
            interval += LD_WIRE_SIZE
        movex = maxx + interval - position[0]
        element.Move(movex, 0)
        position = element.GetPosition()

        # Extract blocks connected to inputs
        blocks = []
        for i, connector in enumerate(connectors["inputs"]):
            for j, (wire, _handle) in enumerate(connector.GetWires()):
                blocks.append(wire.EndConnected.GetParentBlock())

        for i, connector in enumerate(connectors["inputs"]):
            startpoint = connector.GetPosition(False)
            previous_blocks = []
            block_list = []
            start_offset = 0
            if not onlyone[i]:
                middlepoint = maxx + LD_WIRE_SIZE
            for j, (wire, _handle) in enumerate(connector.GetWires()):
                block = wire.EndConnected.GetParentBlock()
                if isinstance(element, LD_PowerRail):
                    pos = block.GetPosition()
                    size = leftblock.GetSize()
                    movex = position[0] - LD_WIRE_SIZE - size[0] - pos[0]
                    block.Move(movex, 0)
                endpoint = wire.EndConnected.GetPosition(False)
                if j == 0:
                    if not onlyone[i] and wire.EndConnected.GetWireIndex(wire) > 0:
                        start_offset = endpoint.y - startpoint.y
                    offset = start_offset
                else:
                    offset = start_offset + LD_LINE_SIZE * CalcBranchSize(previous_blocks, blocks)
                if block in block_list:
                    wires = wire.EndConnected.GetWires()
                    endmiddlepoint = wires[0][0].StartConnected.GetPosition(False)[0] - LD_WIRE_SIZE
                    points = [startpoint, wx.Point(middlepoint, startpoint.y),
                              wx.Point(middlepoint, startpoint.y + offset),
                              wx.Point(endmiddlepoint, startpoint.y + offset),
                              wx.Point(endmiddlepoint, endpoint.y), endpoint]
                else:
                    if startpoint.y + offset != endpoint.y:
                        if isinstance(element, LD_PowerRail):
                            element.MoveConnector(connector, startpoint.y - endpoint.y)
                        elif isinstance(block, LD_PowerRail):
                            block.MoveConnector(wire.EndConnected, startpoint.y - endpoint.y)
                        else:
                            block.Move(0, startpoint.y + offset - endpoint.y)
                            self.RefreshPosition(block, False)
                        endpoint = wire.EndConnected.GetPosition(False)
                    if not onlyone[i]:
                        points = [startpoint, wx.Point(middlepoint, startpoint.y),
                                  wx.Point(middlepoint, endpoint.y), endpoint]
                    else:
                        points = [startpoint, endpoint]
                wire.SetPoints(points, False)
                previous_blocks.append(block)
                blocks.remove(block)
                ExtractNextBlocks(block, block_list)

        element.RefreshModel(False)
        if recursive:
            for connector in connectors["outputs"]:
                for wire, _handle in connector.GetWires():
                    self.RefreshPosition(wire.StartConnected.GetParentBlock())

    def RefreshRungs(self, movey, fromidx):
        if movey != 0:
            for i in xrange(fromidx, len(self.Rungs)):
                self.RungComments[i].Move(0, movey)
                self.RungComments[i].RefreshModel()
                self.Rungs[i].Move(0, movey)
                for element in self.Rungs[i].GetElements():
                    if self.IsBlock(element):
                        self.RefreshPosition(element)

    # -------------------------------------------------------------------------------
    #                          Edit element content functions
    # -------------------------------------------------------------------------------

    def EditPowerRailContent(self, powerrail):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            Viewer.EditPowerRailContent(self, powerrail)
