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

# -------------------------------------------------------------------------------
#                                 Helpers
# -------------------------------------------------------------------------------


[CATEGORY, BLOCK] = range(2)


# -------------------------------------------------------------------------------
#                              Library Panel
# -------------------------------------------------------------------------------


class LibraryPanel(wx.Panel):
    """
    Class that implements a panel displaying a tree containing an hierarchical list
    of functions and function blocks available in project an a search control for
    quickly find one functions or function blocks in this list and a text control
    displaying informations about selected functions or function blocks
    """

    def __init__(self, parent, enable_drag=False):
        """
        Constructor
        @param parent: Parent wx.Window of LibraryPanel
        @param enable_drag: Flag indicating that function or function block can
        be drag'n drop from LibraryPanel (default: False)
        """
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)

        # Define LibraryPanel main sizer
        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)

        # Add SearchCtrl to main sizer
        self.SearchCtrl = wx.SearchCtrl(self)
        # Add a button with a magnifying glass, essentially to show that this
        # control is for searching in tree
        self.SearchCtrl.ShowSearchButton(True)
        self.Bind(wx.EVT_TEXT, self.OnSearchCtrlChanged, self.SearchCtrl)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN,
                  self.OnSearchButtonClick, self.SearchCtrl)
        # Bind keyboard event on SearchCtrl text control to catch UP and DOWN
        # for search previous and next occurrence

        # This protects from fail to start when no children[0] available (possible for wxPython 3.0)
        if self.SearchCtrl.GetChildren():
            search_textctrl = self.SearchCtrl.GetChildren()[0]
            search_textctrl.Bind(wx.EVT_CHAR, self.OnKeyDown)

        main_sizer.AddWindow(self.SearchCtrl, flag=wx.GROW)

        # Add Splitter window for tree and block comment to main sizer
        splitter_window = wx.SplitterWindow(self)
        splitter_window.SetSashGravity(1.0)
        main_sizer.AddWindow(splitter_window, flag=wx.GROW)

        # Add TreeCtrl for functions and function blocks library in splitter
        # window
        self.Tree = wx.TreeCtrl(splitter_window,
                                size=wx.Size(0, 0),
                                style=(wx.TR_HAS_BUTTONS |
                                       wx.TR_SINGLE |
                                       wx.SUNKEN_BORDER |
                                       wx.TR_HIDE_ROOT |
                                       wx.TR_LINES_AT_ROOT))
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeItemSelected, self.Tree)
        self.Tree.Bind(wx.EVT_CHAR, self.OnKeyDown)
        # If drag'n drop is enabled, bind event generated when a drag begins on
        # tree to start a drag'n drop
        if enable_drag:
            self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnTreeBeginDrag, self.Tree)

        # Add TextCtrl for function and function block informations
        self.Comment = wx.TextCtrl(splitter_window, size=wx.Size(0, 80),
                                   style=wx.TE_READONLY | wx.TE_MULTILINE)

        splitter_window.SplitHorizontally(self.Tree, self.Comment, -80)

        self.SetSizer(main_sizer)

        # Reference to the project controller
        self.Controller = None

        # Variable storing functions and function blocks library to display
        self.BlockList = None

    def __del__(self):
        """
        Destructor
        """
        # Remove reference to project controller
        self.Controller = None

    def SetController(self, controller):
        """
        Set reference to project controller
        @param controller: Reference to project controller
        """
        self.Controller = controller

    def SetBlockList(self, blocklist):
        """
        Set function and function block library to display in TreeCtrl
        @param blocklist: Function and function block library
        """
        # Save functions and function blocks library
        self.BlockList = blocklist
        # Refresh TreeCtrl values
        self.RefreshTree()

    def SetFocus(self):
        """
        Called to give focus to LibraryPanel
        Override wx.Window SetFocus method
        """
        # Give focus to SearchCtrl
        self.SearchCtrl.SetFocus()

    def ResetTree(self):
        """
        Reset LibraryPanel values displayed in controls
        """
        # Clear SearchCtrl, TreeCtrl and TextCtrl
        self.SearchCtrl.SetValue("")
        self.Tree.DeleteAllItems()
        self.Comment.SetValue("")

    def RefreshTree(self):
        """
        Refresh LibraryPanel values displayed in controls
        """
        # Get function and function blocks library
        blocktypes = self.BlockList
        if blocktypes is None and self.Controller is not None:
            # Get library from project controller if not defined
            blocktypes = self.Controller.GetBlockTypes()

        # Refresh TreeCtrl values if a library is defined
        if blocktypes is not None:
            # List that will contain tree items to be deleted when TreeCtrl
            # will be refreshed
            items_to_delete = []

            # Get current selected item for selected it when values refreshed
            selected_item = self.Tree.GetSelection()
            selected_pydata = (self.Tree.GetPyData(selected_item)
                               if (selected_item.IsOk() and
                                   selected_item != self.Tree.GetRootItem())
                               else None)
            # Don't save selected item if it is a category
            selected_infos = ((self.Tree.GetItemText(selected_item),
                               selected_pydata["inputs"])
                              if (selected_pydata is not None and
                                  selected_pydata["type"] == BLOCK)
                              else (None, None))

            # Get TreeCtrl root item (hidden)
            root = self.Tree.GetRootItem()
            if not root.IsOk():
                # Create root if not present
                root = self.Tree.AddRoot("")

            # Iterate over functions and function blocks library categories and
            # add a tree item to root item for each of them

            # Get first child under root item
            category_item, root_cookie = self.Tree.GetFirstChild(root)
            for category in blocktypes:
                # Store category name in a local variable to prevent script
                # extracting translated strings for gettext to consider "name"
                # to be translated
                category_name = category["name"]

                # Tree item already exists, set item label
                if category_item.IsOk():
                    self.Tree.SetItemText(category_item, _(category_name))

                # Tree item doesn't exist, add new one to root
                else:
                    category_item = self.Tree.AppendItem(root, _(category_name))
                    # On Windows, needs to get next child of root to have a
                    # reference to the newly added tree item
                    if wx.Platform != '__WXMSW__':
                        category_item, root_cookie = \
                            self.Tree.GetNextChild(root, root_cookie)

                # Set data associated to tree item (only save that item is a
                # category)
                self.Tree.SetPyData(category_item, {"type": CATEGORY})

                # Iterate over functions and function blocks defined in library
                # category add a tree item to category tree item for each of
                # them

                # Get first child under category tree item
                blocktype_item, category_cookie = \
                    self.Tree.GetFirstChild(category_item)
                for blocktype in category["list"]:

                    # Tree item already exists, set item label
                    if blocktype_item.IsOk():
                        self.Tree.SetItemText(blocktype_item, blocktype["name"])

                    # Tree item doesn't exist, add new one to category item
                    else:
                        blocktype_item = self.Tree.AppendItem(
                            category_item, blocktype["name"])
                        # See comment when adding category
                        if wx.Platform != '__WXMSW__':
                            blocktype_item, category_cookie = \
                                self.Tree.GetNextChild(category_item,
                                                       category_cookie)

                    # Define data to associate to block tree item
                    comment = blocktype["comment"]
                    block_data = {
                        "type":       BLOCK,
                        "block_type": blocktype["type"],
                        "inputs":     tuple([type
                                             for _name, type, _modifier
                                             in blocktype["inputs"]]),
                        "extension":  (len(blocktype["inputs"])
                                       if blocktype["extensible"] else None),
                        "comment":    _(comment) + blocktype.get("usage", "")
                    }
                    self.Tree.SetPyData(blocktype_item, block_data)

                    # Select block tree item in tree if it corresponds to
                    # previously selected one
                    if selected_infos == (blocktype["name"],
                                          blocktype["inputs"]):
                        self.Tree.SelectItem(blocktype_item)

                        # Update TextCtrl value
                        self.Comment.SetValue(block_data["comment"])

                    # Get next block tree item under category tree item
                    blocktype_item, category_cookie = \
                        self.Tree.GetNextChild(category_item, category_cookie)

                # Add every remaining tree item under category tree item after
                # updating all block items to the list of items to delete
                while blocktype_item.IsOk():
                    items_to_delete.append(blocktype_item)
                    blocktype_item, category_cookie = \
                        self.Tree.GetNextChild(category_item, category_cookie)

                # Get next category tree item under root item
                category_item, root_cookie = \
                    self.Tree.GetNextChild(root, root_cookie)

            # Add every remaining tree item under root item after updating all
            # category items to the list of items to delete
            while category_item.IsOk():
                items_to_delete.append(category_item)
                category_item, root_cookie = \
                    self.Tree.GetNextChild(root, root_cookie)

            # Remove all items in list of items to delete from TreeCtrl
            for item in items_to_delete:
                self.Tree.Delete(item)

    def GetSelectedBlock(self):
        """
        Get selected block informations
        @return: {"type": block_type_name, "inputs": [input_type,...]} or None
        if no block selected
        """
        # Get selected item associated data in tree
        selected_item = self.Tree.GetSelection()
        selected_pydata = (self.Tree.GetPyData(selected_item)
                           if (selected_item.IsOk() and
                               selected_item != self.Tree.GetRootItem())
                           else None)

        # Return value is None if selected tree item is root or a category
        return ({"type": self.Tree.GetItemText(selected_item),
                 "inputs": selected_pydata["inputs"]}
                if (selected_pydata is not None and
                    selected_pydata["type"] == BLOCK)
                else None)

    def SelectTreeItem(self, name, inputs):
        """
        Select Tree item corresponding to block informations given
        @param name: Block type name
        @param inputs: List of block inputs type [input_type,...]
        """
        # Find tree item corresponding to block informations
        item = self.FindTreeItem(self.Tree.GetRootItem(), name, inputs)
        if item is not None and item.IsOk():
            # Select tree item found
            self.Tree.SelectItem(item)
            self.Tree.EnsureVisible(item)

    def FindTreeItem(self, item, name, inputs=None):
        """
        Find Tree item corresponding to block informations given
        Function is recursive
        @param item: Item to test
        @param name: Block type name
        @param inputs: List of block inputs type [input_type,...]
        """
        # Return immediately if item isn't valid
        if not item.IsOk():
            return None

        # Get data associated to item to test
        item_pydata = self.Tree.GetPyData(item)
        if item_pydata is not None and item_pydata["type"] == BLOCK:
            # Only test item corresponding to block

            # Test if block inputs type are the same than those given
            type_inputs = item_pydata.get("inputs", None)
            type_extension = item_pydata.get("extension", None)
            if inputs is not None and type_inputs is not None:
                same_inputs = reduce(
                    lambda x, y: x and y,
                    map(
                        lambda x: x[0] == x[1] or x[0] == 'ANY' or x[1] == 'ANY',
                        zip(type_inputs,
                            (inputs[:type_extension]
                             if type_extension is not None
                             else inputs))),
                    True)
            else:
                same_inputs = True

            # Return item if  block data corresponds to informations given
            if self.Tree.GetItemText(item) == name and same_inputs:
                return item

        # Test item children if item doesn't correspond
        child, child_cookie = self.Tree.GetFirstChild(item)
        while child.IsOk():
            result = self.FindTreeItem(child, name, inputs)
            if result:
                return result
            child, child_cookie = self.Tree.GetNextChild(item, child_cookie)

        return None

    def SearchInTree(self, value, mode="first"):
        """
        Search in Tree and select item that name contains string given
        @param value: String contained in block name to find
        @param mode: Search mode ('first', 'previous' or 'next')
        (default: 'first')
        @return: True if an item was found
        """
        # Return immediately if root isn't valid
        root = self.Tree.GetRootItem()
        if not root.IsOk():
            return False

        # Set function to navigate in Tree item sibling according to search
        # mode defined
        sibling_function = (self.Tree.GetPrevSibling
                            if mode == "previous"
                            else self.Tree.GetNextSibling)

        # Get current selected item (for next and previous mode)
        item = self.Tree.GetSelection()
        if not item.IsOk() or mode == "first":
            item, _item_cookie = self.Tree.GetFirstChild(root)
            selected = None
        else:
            selected = item

        # Navigate through tree items until one matching found or reach tree
        # starting or ending
        while item.IsOk():

            # Get item data to get item type
            item_pydata = self.Tree.GetPyData(item)

            # Item is a block category
            if (item == root) or item_pydata["type"] == CATEGORY:

                # Get category first or last child according to search mode
                # defined
                child = (self.Tree.GetLastChild(item)
                         if mode == "previous"
                         else self.Tree.GetFirstChild(item)[0])

                # If category has no child, go to sibling category
                item = (child if child.IsOk() else sibling_function(item))

            # Item is a block
            else:

                # Extract item block name
                name = self.Tree.GetItemText(item)
                # Test if block name contains string given
                if name.upper().find(value.upper()) != -1 and item != selected:
                    # Select block and collapse all categories other than block
                    # category
                    child, child_cookie = self.Tree.GetFirstChild(root)
                    while child.IsOk():
                        self.Tree.CollapseAllChildren(child)
                        child, child_cookie = self.Tree.GetNextChild(root, child_cookie)
                    self.Tree.SelectItem(item)
                    self.Tree.EnsureVisible(item)
                    return True

                # Go to next item sibling if block not found
                next = sibling_function(item)

                # If category has no other child, go to next category sibling
                item = (next
                        if next.IsOk()
                        else sibling_function(self.Tree.GetItemParent(item)))

        return False

    def OnSearchCtrlChanged(self, event):
        """
        Called when SearchCtrl text control value changed
        @param event: TextCtrl change event
        """
        # Search for block containing SearchCtrl value in 'first' mode
        self.SearchInTree(self.SearchCtrl.GetValue())
        event.Skip()

    def OnSearchButtonClick(self, event):
        """
        Called when SearchCtrl search button was clicked
        @param event: Button clicked event
        """
        # Search for block containing SearchCtrl value in 'next' mode
        self.SearchInTree(self.SearchCtrl.GetValue(), "next")
        event.Skip()

    def OnTreeItemSelected(self, event):
        """
        Called when tree item is selected
        @param event: wx.TreeEvent
        """
        # Update TextCtrl value with block selected usage
        item_pydata = self.Tree.GetPyData(event.GetItem())
        self.Comment.SetValue(
            item_pydata["comment"]
            if item_pydata is not None and item_pydata["type"] == BLOCK
            else "")

        # Call extra function defined when tree item is selected
        if getattr(self, "_OnTreeItemSelected", None) is not None:
            self._OnTreeItemSelected(event)

        event.Skip()

    def OnTreeBeginDrag(self, event):
        """
        Called when a drag is started in tree
        @param event: wx.TreeEvent
        """
        selected_item = event.GetItem()
        item_pydata = self.Tree.GetPyData(selected_item)

        # Item dragged is a block
        if item_pydata is not None and item_pydata["type"] == BLOCK:
            # Start a drag'n drop
            data = wx.TextDataObject(str(
                (self.Tree.GetItemText(selected_item),
                 item_pydata["block_type"],
                 "",
                 item_pydata["inputs"])))
            dragSource = wx.DropSource(self.Tree)
            dragSource.SetData(data)
            dragSource.DoDragDrop()

    def OnKeyDown(self, event):
        """
        Called when key is pressed in SearchCtrl text control
        @param event: wx.KeyEvent
        """
        # Get event keycode and value in SearchCtrl
        keycode = event.GetKeyCode()
        search_value = self.SearchCtrl.GetValue()

        # Up key was pressed and SearchCtrl isn't empty, search for block in
        # 'previous' mode
        if keycode == wx.WXK_UP and search_value != "":
            self.SearchInTree(search_value, "previous")

        # Down key was pressed and SearchCtrl isn't empty, search for block in
        # 'next' mode
        elif keycode == wx.WXK_DOWN and search_value != "":
            self.SearchInTree(search_value, "next")

        # Handle key normally
        else:
            event.Skip()
