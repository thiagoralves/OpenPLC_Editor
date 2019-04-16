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
from functools import reduce

import wx
import wx.lib.buttons
import wx.lib.agw.customtreectrl as CT

from PLCControler import *
from util.BitmapLibrary import GetBitmap
from plcopen.types_enums import GetElementType


def GenerateName(infos):
    if infos[0] in ["input", "output", "value"]:
        return "%s %d:" % (infos[0], infos[1])
    elif infos[0] == "range":
        return "%s %d %s" % (infos[0], infos[1], infos[2])
    elif infos[0] == "struct":
        return "element %d %s" % (infos[1], infos[2])
    return "%s:" % infos[0]


# -------------------------------------------------------------------------------
#                            Search Result Panel
# -------------------------------------------------------------------------------


[
    ID_SEARCHRESULTPANEL, ID_SEARCHRESULTPANELHEADERLABEL,
    ID_SEARCHRESULTPANELSEARCHRESULTSTREE, ID_SEARCHRESULTPANELRESETBUTTON,
] = [wx.NewId() for _init_ctrls in range(4)]


class SearchResultPanel(wx.Panel):

    def _init_coll_MainSizer_Items(self, parent):
        parent.AddSizer(self.HeaderSizer, 0, border=0, flag=wx.GROW)
        parent.AddWindow(self.SearchResultsTree, 1, border=0, flag=wx.GROW)

    def _init_coll_MainSizer_Growables(self, parent):
        parent.AddGrowableCol(0)
        parent.AddGrowableRow(1)

    def _init_coll_HeaderSizer_Items(self, parent):
        parent.AddWindow(self.HeaderLabel, 1, border=5, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        parent.AddWindow(self.ResetButton, 0, border=0, flag=0)

    def _init_coll_HeaderSizer_Growables(self, parent):
        parent.AddGrowableCol(0)

    def _init_sizers(self):
        self.MainSizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
        self.HeaderSizer = wx.BoxSizer(wx.HORIZONTAL)

        self._init_coll_MainSizer_Items(self.MainSizer)
        self._init_coll_MainSizer_Growables(self.MainSizer)
        self._init_coll_HeaderSizer_Items(self.HeaderSizer)

        self.SetSizer(self.MainSizer)

    def _init_ctrls(self, prnt):
        self.HeaderLabel = wx.StaticText(id=ID_SEARCHRESULTPANELHEADERLABEL,
                                         name='HeaderLabel', parent=self,
                                         pos=wx.Point(0, 0), size=wx.Size(0, 17), style=0)

        search_results_tree_style = CT.TR_HAS_BUTTONS | CT.TR_NO_LINES | CT.TR_HAS_VARIABLE_ROW_HEIGHT
        self.SearchResultsTree = CT.CustomTreeCtrl(id=ID_SEARCHRESULTPANELSEARCHRESULTSTREE,
                                                   name="SearchResultsTree", parent=self,
                                                   pos=wx.Point(0, 0), style=search_results_tree_style)
        if wx.VERSION >= (2, 8, 11):
            self.SearchResultsTree.SetAGWWindowStyleFlag(search_results_tree_style)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnSearchResultsTreeItemActivated,
                  id=ID_SEARCHRESULTPANELSEARCHRESULTSTREE)

        self.ResetButton = wx.lib.buttons.GenBitmapButton(
            self, bitmap=GetBitmap("reset"),
            size=wx.Size(28, 28), style=wx.NO_BORDER)
        self.ResetButton.SetToolTipString(_("Reset search result"))
        self.Bind(wx.EVT_BUTTON, self.OnResetButton, self.ResetButton)

        self._init_sizers()

    def __init__(self, parent, window):
        wx.Panel.__init__(self, id=ID_SEARCHRESULTPANEL,
                          name='SearchResultPanel', parent=parent,
                          pos=wx.Point(0, 0),
                          size=wx.Size(0, 0), style=wx.TAB_TRAVERSAL)

        self.ParentWindow = window

        self._init_ctrls(parent)

        # Define Tree item icon list
        self.TreeImageList = wx.ImageList(16, 16)
        self.TreeImageDict = {}

        # Icons for other items
        for imgname, itemtype in [
                # editables
                ("PROJECT",        ITEM_PROJECT),
                ("TRANSITION",     ITEM_TRANSITION),
                ("ACTION",         ITEM_ACTION),
                ("CONFIGURATION",  ITEM_CONFIGURATION),
                ("RESOURCE",       ITEM_RESOURCE),
                ("DATATYPE",       ITEM_DATATYPE),
                ("ACTION",         "action_block"),
                ("IL",             "IL"),
                ("ST",             "ST"),
                ("FILE",           ITEM_CONFNODE)]:
            self.TreeImageDict[itemtype] = self.TreeImageList.Add(GetBitmap(imgname))

        for itemtype in ["function", "functionBlock", "program",
                         "comment", "block", "io_variable",
                         "connector", "contact", "coil",
                         "step", "transition", "jump",
                         "var_local", "var_input",
                         "var_inout", "var_output"]:
            self.TreeImageDict[itemtype] = self.TreeImageList.Add(GetBitmap(itemtype.upper()))

        # Assign icon list to TreeCtrl
        self.SearchResultsTree.SetImageList(self.TreeImageList)

        self.ResetSearchResults()

    def SetSearchResults(self, criteria, search_results):
        self.Criteria = criteria
        self.SearchResults = {}
        self.ElementsOrder = []

        for infos, start, end, text in search_results:
            if infos[0] not in self.ElementsOrder:
                self.ElementsOrder.append(infos[0])

            results = self.SearchResults.setdefault(infos[0], [])
            results.append((infos, start, end, text))

        self.RefreshView()

    def ResetSearchResults(self):
        self.Criteria = None
        self.ElementsOrder = []
        self.SearchResults = {}
        self.RefreshView()

    def RefreshView(self):
        self.SearchResultsTree.DeleteAllItems()
        if self.Criteria is None:
            self.SearchResultsTree.AddRoot("")
            root = self.SearchResultsTree.GetRootItem()
            root.SetHilight(False)
            self.HeaderLabel.SetLabel(_("No search results available."))
            self.ResetButton.Enable(False)
        else:
            matches_number = 0
            search_results_tree_infos = {
                "name": _("Project '%s':") % self.ParentWindow.Controler.GetProjectName(),
                "type": ITEM_PROJECT,
                "data": None,
                "text": None,
                "matches": None,
            }
            search_results_tree_children = search_results_tree_infos.setdefault("children", [])
            for tagname in self.ElementsOrder:
                results = self.SearchResults.get(tagname, [])
                matches_number += len(results)

                words = tagname.split("::")

                element_type = GetElementType(tagname)
                if element_type == ITEM_POU:
                    element_type = self.ParentWindow.Controler.GetPouType(words[1])

                element_infos = {"name": words[-1],
                                 "type": element_type,
                                 "data": tagname,
                                 "text": None,
                                 "matches": len(results)}

                children = element_infos.setdefault("children", [])
                for infos, start, end, text in results:
                    if len(words) == 1:  # CTN match
                        child_name = {"body": str(start[0])+":",
                                      "var_inout": _("Variable:")}[infos[1]]
                        child_type = {"body": ITEM_CONFNODE,
                                      "var_inout": "var_inout"}[infos[1]]
                    elif infos[1] == "name" or element_type == ITEM_DATATYPE:
                        child_name = GenerateName(infos[1:])
                        child_type = element_type
                    else:
                        if element_type == ITEM_RESOURCE:
                            child_type = element_type
                        else:
                            child_type = infos[1]
                        if child_type == "name":
                            child_name = "name"
                        elif child_type == "body":
                            child_name = "body"
                            if element_type == ITEM_TRANSITION:
                                child_type = self.ParentWindow.Controler.GetTransitionBodyType(words[1], words[2])
                            elif element_type == ITEM_ACTION:
                                child_type = self.ParentWindow.Controler.GetActionBodyType(words[1], words[2])
                            else:
                                child_type = self.ParentWindow.Controler.GetPouBodyType(words[1])
                        else:
                            child_name = GenerateName(infos[3:])
                    child_infos = {
                        "name": child_name,
                        "type": child_type,
                        "data": (infos, start, end, None),
                        "text": text,
                        "matches": 1,
                        "children": [],
                    }
                    children.append(child_infos)

                # not Project node
                if len(words) > 2:
                    for _element_infos in search_results_tree_children:
                        if _element_infos["name"] == words[1]:
                            _element_infos["matches"] += len(children)
                            _element_infos["children"].append(element_infos)
                            break
                    if element_type == ITEM_RESOURCE:
                        search_results_tree_children.append(element_infos)
                else:  # Project node or CTN
                    search_results_tree_children.append(element_infos)

            if matches_number < 2:
                header_format = _("'{a1}' - {a2} match in project")
            else:
                header_format = _("'{a1}' - {a2} matches in project")

            self.HeaderLabel.SetLabel(header_format.format(a1=self.Criteria["find_pattern"], a2=matches_number))
            self.ResetButton.Enable(True)

            if matches_number > 0:
                root = self.SearchResultsTree.GetRootItem()
                if root is None:
                    root = self.SearchResultsTree.AddRoot(search_results_tree_infos["name"])
                self.GenerateSearchResultsTreeBranch(root, search_results_tree_infos)
                self.SearchResultsTree.Expand(root)

    def GetTextCtrlClickFunction(self, item):
        def OnTextCtrlClick(event):
            self.SearchResultsTree.SelectItem(item)
            event.Skip()
        return OnTextCtrlClick

    def GetTextCtrlDClickFunction(self, item):
        def OnTextCtrlDClick(event):
            self.ShowSearchResults(item)
            event.Skip()
        return OnTextCtrlDClick

    def GenerateSearchResultsTreeBranch(self, root, infos):
        if infos["name"] == "body":
            item_name = "%d:" % infos["data"][1][0]
        else:
            item_name = infos["name"]

        self.SearchResultsTree.SetItemText(root, item_name)
        self.SearchResultsTree.SetPyData(root, infos["data"])
        self.SearchResultsTree.SetItemBackgroundColour(root, wx.WHITE)
        self.SearchResultsTree.SetItemTextColour(root, wx.BLACK)
        if infos["type"] is not None:
            if infos["type"] == ITEM_POU:
                self.SearchResultsTree.SetItemImage(root, self.TreeImageDict[self.ParentWindow.Controler.GetPouType(infos["name"])])
            else:
                self.SearchResultsTree.SetItemImage(root, self.TreeImageDict[infos["type"]])

        text = None
        if infos["text"] is not None:
            text = infos["text"]
            start, end = infos["data"][1:3]
            text_lines = infos["text"].splitlines()
            start_idx = start[1]
            end_idx = reduce(lambda x, y: x + y, map(lambda x: len(x) + 1, text_lines[:end[0] - start[0]]), end[1] + 1)
            style = wx.TextAttr(wx.BLACK, wx.Colour(206, 204, 247))
        elif infos["type"] is not None and infos["matches"] > 1:
            text = _("(%d matches)") % infos["matches"]
            start_idx, end_idx = 0, len(text)
            style = wx.TextAttr(wx.Colour(0, 127, 174))

        if text is not None:
            text_ctrl_style = wx.BORDER_NONE | wx.TE_READONLY | wx.TE_RICH2
            if wx.Platform != '__WXMSW__' or len(text.splitlines()) > 1:
                text_ctrl_style |= wx.TE_MULTILINE | wx.TE_NO_VSCROLL
            text_ctrl = wx.TextCtrl(id=-1, parent=self.SearchResultsTree, pos=wx.Point(0, 0),
                                    value=text, style=text_ctrl_style)
            width, height = text_ctrl.GetTextExtent(text)
            text_ctrl.SetClientSize(wx.Size(width + 1, height))
            text_ctrl.SetBackgroundColour(self.SearchResultsTree.GetBackgroundColour())
            text_ctrl.Bind(wx.EVT_LEFT_DOWN, self.GetTextCtrlClickFunction(root))
            text_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.GetTextCtrlDClickFunction(root))
            text_ctrl.SetInsertionPoint(0)
            text_ctrl.SetStyle(start_idx, end_idx, style)
            self.SearchResultsTree.SetItemWindow(root, text_ctrl)

        item, root_cookie = self.SearchResultsTree.GetFirstChild(root)
        for child in infos["children"]:
            if item is None:
                item = self.SearchResultsTree.AppendItem(root, "")
                item, root_cookie = self.SearchResultsTree.GetNextChild(root, root_cookie)
            self.GenerateSearchResultsTreeBranch(item, child)
            item, root_cookie = self.SearchResultsTree.GetNextChild(root, root_cookie)

    def ShowSearchResults(self, item):
        data = self.SearchResultsTree.GetPyData(item)
        if isinstance(data, tuple):
            search_results = [data]
        else:
            search_results = self.SearchResults.get(data, [])
        self.ParentWindow.ClearHighlights(SEARCH_RESULT_HIGHLIGHT)
        for infos, start, end, _text in search_results:
            self.ParentWindow.ShowSearchResult(infos, start, end)

    def OnSearchResultsTreeItemActivated(self, event):
        self.ShowSearchResults(event.GetItem())
        event.Skip()

    def OnResetButton(self, event):
        self.ResetSearchResults()
        self.ParentWindow.ClearSearchResults()
        event.Skip()
