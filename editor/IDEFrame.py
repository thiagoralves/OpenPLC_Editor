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
import sys
import base64
from future.builtins import \
    round, \
    str as text

import wx
import wx.grid
import wx.aui
from six.moves import cPickle, xrange

from editors.EditorPanel import EditorPanel
from editors.SFCViewer import SFC_Viewer
from editors.LDViewer import LD_Viewer
from editors.TextViewer import TextViewer
from editors.Viewer import Viewer, ZOOM_FACTORS
from editors.ResourceEditor import ConfigurationEditor, ResourceEditor
from editors.DataTypeEditor import DataTypeEditor
from PLCControler import *
from controls import CustomTree, LibraryPanel, PouInstanceVariablesPanel, SearchResultPanel
from controls.DebugVariablePanel import DebugVariablePanel
from dialogs import ProjectDialog, PouDialog, PouTransitionDialog, PouActionDialog, FindInPouDialog, SearchInProjectDialog
from util.BitmapLibrary import GetBitmap
from plcopen.types_enums import *

# Define PLCOpenEditor controls id
[
    ID_PLCOPENEDITOR, ID_PLCOPENEDITORLEFTNOTEBOOK,
    ID_PLCOPENEDITORBOTTOMNOTEBOOK, ID_PLCOPENEDITORRIGHTNOTEBOOK,
    ID_PLCOPENEDITORPROJECTTREE, ID_PLCOPENEDITORMAINSPLITTER,
    ID_PLCOPENEDITORSECONDSPLITTER, ID_PLCOPENEDITORTHIRDSPLITTER,
    ID_PLCOPENEDITORLIBRARYPANEL, ID_PLCOPENEDITORLIBRARYSEARCHCTRL,
    ID_PLCOPENEDITORLIBRARYTREE, ID_PLCOPENEDITORLIBRARYCOMMENT,
    ID_PLCOPENEDITORTABSOPENED, ID_PLCOPENEDITORTABSOPENED,
    ID_PLCOPENEDITOREDITORMENUTOOLBAR, ID_PLCOPENEDITOREDITORTOOLBAR,
    ID_PLCOPENEDITORPROJECTPANEL,
] = [wx.NewId() for _init_ctrls in range(17)]

# Define PLCOpenEditor EditMenu extra items id
[
    ID_PLCOPENEDITOREDITMENUENABLEUNDOREDO, ID_PLCOPENEDITOREDITMENUADDDATATYPE,
    ID_PLCOPENEDITOREDITMENUADDFUNCTION, ID_PLCOPENEDITOREDITMENUADDFUNCTIONBLOCK,
    ID_PLCOPENEDITOREDITMENUADDPROGRAM, ID_PLCOPENEDITOREDITMENUADDCONFIGURATION,
    ID_PLCOPENEDITOREDITMENUFINDNEXT, ID_PLCOPENEDITOREDITMENUFINDPREVIOUS,
    ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT, ID_PLCOPENEDITOREDITMENUADDRESOURCE
] = [wx.NewId() for _init_coll_EditMenu_Items in range(10)]

# Define PLCOpenEditor DisplayMenu extra items id
[
    ID_PLCOPENEDITORDISPLAYMENURESETPERSPECTIVE,
    ID_PLCOPENEDITORDISPLAYMENUSWITCHPERSPECTIVE,
    ID_PLCOPENEDITORDISPLAYMENUFULLSCREEN,
] = [wx.NewId() for _init_coll_DisplayMenu_Items in range(3)]

# -------------------------------------------------------------------------------
#                            EditorToolBar definitions
# -------------------------------------------------------------------------------

# Define PLCOpenEditor Toolbar items id
[
    ID_PLCOPENEDITOREDITORTOOLBARSELECTION, ID_PLCOPENEDITOREDITORTOOLBARCOMMENT,
    ID_PLCOPENEDITOREDITORTOOLBARVARIABLE, ID_PLCOPENEDITOREDITORTOOLBARBLOCK,
    ID_PLCOPENEDITOREDITORTOOLBARCONNECTION, ID_PLCOPENEDITOREDITORTOOLBARWIRE,
    ID_PLCOPENEDITOREDITORTOOLBARPOWERRAIL, ID_PLCOPENEDITOREDITORTOOLBARRUNG,
    ID_PLCOPENEDITOREDITORTOOLBARCOIL, ID_PLCOPENEDITOREDITORTOOLBARCONTACT,
    ID_PLCOPENEDITOREDITORTOOLBARBRANCH, ID_PLCOPENEDITOREDITORTOOLBARINITIALSTEP,
    ID_PLCOPENEDITOREDITORTOOLBARSTEP, ID_PLCOPENEDITOREDITORTOOLBARTRANSITION,
    ID_PLCOPENEDITOREDITORTOOLBARACTIONBLOCK, ID_PLCOPENEDITOREDITORTOOLBARDIVERGENCE,
    ID_PLCOPENEDITOREDITORTOOLBARJUMP, ID_PLCOPENEDITOREDITORTOOLBARMOTION,
] = [wx.NewId() for _init_coll_DefaultEditorToolBar_Items in range(18)]


# -------------------------------------------------------------------------------
#                               Helper Functions
# -------------------------------------------------------------------------------


def EncodeFileSystemPath(path, use_base64=True):
    path = path.encode(sys.getfilesystemencoding())
    if use_base64:
        return base64.encodestring(path)
    return path


def DecodeFileSystemPath(path, is_base64=True):
    if is_base64:
        path = base64.decodestring(path)
    return text(path, sys.getfilesystemencoding())


def AppendMenu(parent, help, id, kind, text):
    parent.Append(help=help, id=id, kind=kind, text=text)


[
    TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU, PROJECTTREE,
    POUINSTANCEVARIABLESPANEL, LIBRARYTREE, SCALING, PAGETITLES
] = range(10)


def GetShortcutKeyCallbackFunction(viewer_function):
    def ShortcutKeyFunction(self, event):
        control = self.FindFocus()
        if control is not None and control.GetName() in ["Viewer", "TextViewer"]:
            getattr(control.ParentWindow, viewer_function)()
        elif isinstance(control, wx.stc.StyledTextCtrl):
            getattr(control, viewer_function)()
        elif isinstance(control, wx.TextCtrl):
            control.ProcessEvent(event)
    return ShortcutKeyFunction


def GetDeleteElementFunction(remove_function, parent_type=None, check_function=None):
    def DeleteElementFunction(self, selected):
        name = self.ProjectTree.GetItemText(selected)
        if check_function is None or check_function(name):
            if parent_type is not None:
                item_infos = self.ProjectTree.GetPyData(selected)
                parent_name = item_infos["tagname"].split("::")[1]
                remove_function(self.Controler, parent_name, name)
            else:
                remove_function(self.Controler, name)
    return DeleteElementFunction


if wx.Platform == '__WXMSW__':
    TAB_BORDER = 6
    NOTEBOOK_BORDER = 6
else:
    TAB_BORDER = 7
    NOTEBOOK_BORDER = 2


def SimplifyTabLayout(tabs, rect):
    for tab in tabs:
        if tab["pos"][0] == rect.x:
            others = [t for t in tabs if t != tab]
            others.sort(lambda x, y: cmp(x["pos"][0], y["pos"][0]))
            for other in others:
                if other["pos"][1] == tab["pos"][1] and \
                   other["size"][1] == tab["size"][1] and \
                   other["pos"][0] == tab["pos"][0] + tab["size"][0] + TAB_BORDER:

                    tab["size"] = (tab["size"][0] + other["size"][0] + TAB_BORDER, tab["size"][1])
                    tab["pages"].extend(other["pages"])
                    tabs.remove(other)

                    if tab["size"][0] == rect.width:
                        return True

        elif tab["pos"][1] == rect.y:
            others = [t for t in tabs if t != tab]
            others.sort(lambda x, y: cmp(x["pos"][1], y["pos"][1]))
            for other in others:
                if other["pos"][0] == tab["pos"][0] and \
                   other["size"][0] == tab["size"][0] and \
                   other["pos"][1] == tab["pos"][1] + tab["size"][1] + TAB_BORDER:

                    tab["size"] = (tab["size"][0], tab["size"][1] + other["size"][1] + TAB_BORDER)
                    tab["pages"].extend(other["pages"])
                    tabs.remove(other)

                    if tab["size"][1] == rect.height:
                        return True
    return False


def ComputeTabsLayout(tabs, rect):
    if len(tabs) == 0:
        return tabs
    if len(tabs) == 1:
        return tabs[0]
    split = None
    split_id = None
    for idx, tab in enumerate(tabs):
        if len(tab["pages"]) == 0:
            raise ValueError("Not possible")
        if tab["size"][0] == rect.width:
            if tab["pos"][1] == rect.y:
                split = (wx.TOP, tab["size"][1] / rect.height)
                split_rect = wx.Rect(rect.x, rect.y + tab["size"][1] + TAB_BORDER,
                                     rect.width, rect.height - tab["size"][1] - TAB_BORDER)
            elif tab["pos"][1] == rect.height + 1 - tab["size"][1]:
                split = (wx.BOTTOM, 1.0 - tab["size"][1] / rect.height)
                split_rect = wx.Rect(rect.x, rect.y,
                                     rect.width, rect.height - tab["size"][1] - TAB_BORDER)
            split_id = idx
            break
        elif tab["size"][1] == rect.height:
            if tab["pos"][0] == rect.x:
                split = (wx.LEFT, tab["size"][0] / rect.width)
                split_rect = wx.Rect(rect.x + tab["size"][0] + TAB_BORDER, rect.y,
                                     rect.width - tab["size"][0] - TAB_BORDER, rect.height)
            elif tab["pos"][0] == rect.width + 1 - tab["size"][0]:
                split = (wx.RIGHT, 1.0 - tab["size"][0] / rect.width)
                split_rect = wx.Rect(rect.x, rect.y,
                                     rect.width - tab["size"][0] - TAB_BORDER, rect.height)
            split_id = idx
            break
    if split is not None:
        split_tab = tabs.pop(split_id)
        return {"split": split,
                "tab": split_tab,
                "others": ComputeTabsLayout(tabs, split_rect)}
    else:
        if SimplifyTabLayout(tabs, rect):
            return ComputeTabsLayout(tabs, rect)
    return tabs


class IDEFrame(wx.Frame):
    """IDEFrame Base Class"""

    def InitEditorToolbarItems(self):
        """
        Initialize dictionary with lists of elements that need to be shown
        if POU in particular programming language is edited.
        """
        # Define behaviour of each Toolbar item according to current POU body type
        # Informations meaning are in this order:
        #  - Item is toggled
        #  - PLCOpenEditor mode where item is displayed (could be more then one)
        #  - Item id
        #  - Item callback function name
        #  - Item icon filename
        #  - Item tooltip text
        self.EditorToolBarItems = {
            "FBD":   [(True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARMOTION, "OnMotionTool",
                       "move", _("Move the view")),
                      (True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCOMMENT, "OnCommentTool",
                       "add_comment", _("Create a new comment")),
                      (True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARVARIABLE, "OnVariableTool",
                       "add_variable", _("Create a new variable")),
                      (True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARBLOCK, "OnBlockTool",
                       "add_block", _("Create a new block")),
                      (True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCONNECTION, "OnConnectionTool",
                       "add_connection", _("Create a new connection"))],
            "LD":    [(True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARMOTION, "OnMotionTool",
                       "move", _("Move the view")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCOMMENT, "OnCommentTool",
                       "add_comment", _("Create a new comment")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARPOWERRAIL, "OnPowerRailTool",
                       "add_powerrail", _("Create a new power rail")),
                      (False, DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARRUNG, "OnRungTool",
                       "add_rung", _("Create a new rung")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCOIL, "OnCoilTool",
                       "add_coil", _("Create a new coil")),
                      (False, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCONTACT, "OnContactTool",
                       "add_contact", _("Create a new contact")),
                      (False, DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARBRANCH, "OnBranchTool",
                       "add_branch", _("Create a new branch")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARVARIABLE, "OnVariableTool",
                       "add_variable", _("Create a new variable")),
                      (False, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARBLOCK, "OnBlockTool",
                       "add_block", _("Create a new block")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCONNECTION, "OnConnectionTool",
                       "add_connection", _("Create a new connection"))],
            "SFC":   [(True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARMOTION, "OnMotionTool",
                       "move", _("Move the view")),
                      (True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCOMMENT, "OnCommentTool",
                       "add_comment", _("Create a new comment")),
                      (True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARINITIALSTEP, "OnInitialStepTool",
                       "add_initial_step", _("Create a new initial step")),
                      (False, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARSTEP, "OnStepTool",
                       "add_step", _("Create a new step")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARTRANSITION, "OnTransitionTool",
                       "add_transition", _("Create a new transition")),
                      (False, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARACTIONBLOCK, "OnActionBlockTool",
                       "add_action", _("Create a new action block")),
                      (False, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARDIVERGENCE, "OnDivergenceTool",
                       "add_divergence", _("Create a new divergence")),
                      (False, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARJUMP, "OnJumpTool",
                       "add_jump", _("Create a new jump")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARVARIABLE, "OnVariableTool",
                       "add_variable", _("Create a new variable")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARBLOCK, "OnBlockTool",
                       "add_block", _("Create a new block")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCONNECTION, "OnConnectionTool",
                       "add_connection", _("Create a new connection")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARPOWERRAIL, "OnPowerRailTool",
                       "add_powerrail", _("Create a new power rail")),
                      (True, FREEDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARCONTACT, "OnContactTool",
                       "add_contact", _("Create a new contact"))],
            "ST":    [],
            "IL":    [],
            "debug": [(True, FREEDRAWING_MODE | DRIVENDRAWING_MODE,
                       ID_PLCOPENEDITOREDITORTOOLBARMOTION, "OnMotionTool",
                       "move", _("Move the view"))],
        }

    def _init_coll_MenuBar_Menus(self, parent):
        parent.Append(menu=self.FileMenu, title=_(u'&File'))
        parent.Append(menu=self.EditMenu, title=_(u'&Edit'))
        parent.Append(menu=self.DisplayMenu, title=_(u'&Display'))
        parent.Append(menu=self.HelpMenu, title=_(u'&Help'))

    def _init_coll_FileMenu_Items(self, parent):
        pass

    def _init_coll_AddMenu_Items(self, parent, add_config=True):
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUADDDATATYPE,
                   kind=wx.ITEM_NORMAL, text=_(u'&Data Type'))
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUADDFUNCTION,
                   kind=wx.ITEM_NORMAL, text=_(u'&Function'))
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUADDFUNCTIONBLOCK,
                   kind=wx.ITEM_NORMAL, text=_(u'Function &Block'))
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUADDPROGRAM,
                   kind=wx.ITEM_NORMAL, text=_(u'&Program'))
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUADDRESOURCE,
                   kind=wx.ITEM_NORMAL, text=_(u'&Resource'))
        if add_config:
            AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUADDCONFIGURATION,
                       kind=wx.ITEM_NORMAL, text=_(u'&Configuration'))

    def _init_coll_EditMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_UNDO,
                   kind=wx.ITEM_NORMAL, text=_(u'Undo') + '\tCTRL+Z')
        AppendMenu(parent, help='', id=wx.ID_REDO,
                   kind=wx.ITEM_NORMAL, text=_(u'Redo') + '\tCTRL+Y')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_CUT,
                   kind=wx.ITEM_NORMAL, text=_(u'Cut') + '\tCTRL+X')
        AppendMenu(parent, help='', id=wx.ID_COPY,
                   kind=wx.ITEM_NORMAL, text=_(u'Copy') + '\tCTRL+C')
        AppendMenu(parent, help='', id=wx.ID_PASTE,
                   kind=wx.ITEM_NORMAL, text=_(u'Paste') + '\tCTRL+V')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_FIND,
                   kind=wx.ITEM_NORMAL, text=_(u'Find') + '\tCTRL+F')
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUFINDNEXT,
                   kind=wx.ITEM_NORMAL, text=_(u'Find Next') + '\tCTRL+K')
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUFINDPREVIOUS,
                   kind=wx.ITEM_NORMAL, text=_(u'Find Previous') + '\tCTRL+SHIFT+K')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT,
                   kind=wx.ITEM_NORMAL, text=_(u'Search in Project') + '\tCTRL+SHIFT+F')
        parent.AppendSeparator()
        add_menu = wx.Menu(title='')
        self._init_coll_AddMenu_Items(add_menu)
        parent.AppendMenu(wx.ID_ADD, _(u"&Add Element"), add_menu)
        AppendMenu(parent, help='', id=wx.ID_SELECTALL,
                   kind=wx.ITEM_NORMAL, text=_(u'Select All') + '\tCTRL+A')
        AppendMenu(parent, help='', id=wx.ID_DELETE,
                   kind=wx.ITEM_NORMAL, text=_(u'&Delete'))
        self.Bind(wx.EVT_MENU, self.OnUndoMenu, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU, self.OnRedoMenu, id=wx.ID_REDO)
        # self.Bind(wx.EVT_MENU, self.OnEnableUndoRedoMenu, id=ID_PLCOPENEDITOREDITMENUENABLEUNDOREDO)
        self.Bind(wx.EVT_MENU, self.OnCutMenu, id=wx.ID_CUT)
        self.Bind(wx.EVT_MENU, self.OnCopyMenu, id=wx.ID_COPY)
        self.Bind(wx.EVT_MENU, self.OnPasteMenu, id=wx.ID_PASTE)
        self.Bind(wx.EVT_MENU, self.OnFindMenu, id=wx.ID_FIND)
        self.Bind(wx.EVT_MENU, self.OnFindNextMenu,
                  id=ID_PLCOPENEDITOREDITMENUFINDNEXT)
        self.Bind(wx.EVT_MENU, self.OnFindPreviousMenu,
                  id=ID_PLCOPENEDITOREDITMENUFINDPREVIOUS)
        self.Bind(wx.EVT_MENU, self.OnSearchInProjectMenu,
                  id=ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT)
        self.Bind(wx.EVT_MENU, self.OnAddDataTypeMenu,
                  id=ID_PLCOPENEDITOREDITMENUADDDATATYPE)
        self.Bind(wx.EVT_MENU, self.GenerateAddPouFunction("function"),
                  id=ID_PLCOPENEDITOREDITMENUADDFUNCTION)
        self.Bind(wx.EVT_MENU, self.GenerateAddPouFunction("functionBlock"),
                  id=ID_PLCOPENEDITOREDITMENUADDFUNCTIONBLOCK)
        self.Bind(wx.EVT_MENU, self.GenerateAddPouFunction("program"),
                  id=ID_PLCOPENEDITOREDITMENUADDPROGRAM)
        self.Bind(wx.EVT_MENU, self.AddResourceMenu,
                  id=ID_PLCOPENEDITOREDITMENUADDRESOURCE)
        self.Bind(wx.EVT_MENU, self.OnAddConfigurationMenu,
                  id=ID_PLCOPENEDITOREDITMENUADDCONFIGURATION)
        self.Bind(wx.EVT_MENU, self.OnSelectAllMenu, id=wx.ID_SELECTALL)
        self.Bind(wx.EVT_MENU, self.OnDeleteMenu, id=wx.ID_DELETE)

        self.AddToMenuToolBar([(wx.ID_UNDO, "undo", _(u'Undo'), None),
                               (wx.ID_REDO, "redo", _(u'Redo'), None),
                               None,
                               (wx.ID_CUT, "cut", _(u'Cut'), None),
                               (wx.ID_COPY, "copy", _(u'Copy'), None),
                               (wx.ID_PASTE, "paste", _(u'Paste'), None),
                               None,
                               (ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT, "find", _(u'Search in Project'), None),
                               (ID_PLCOPENEDITORDISPLAYMENUFULLSCREEN, "fullscreen", _(u'Toggle fullscreen mode'), None)])

    def _init_coll_DisplayMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_REFRESH,
                   kind=wx.ITEM_NORMAL, text=_(u'Refresh') + '\tCTRL+R')
        if self.EnableDebug:
            AppendMenu(parent, help='', id=wx.ID_CLEAR,
                       kind=wx.ITEM_NORMAL, text=_(u'Clear Errors') + '\tCTRL+K')
        parent.AppendSeparator()
        zoommenu = wx.Menu(title='')
        parent.AppendMenu(wx.ID_ZOOM_FIT, _("Zoom"), zoommenu)
        for idx, value in enumerate(ZOOM_FACTORS):
            new_id = wx.NewId()
            AppendMenu(zoommenu, help='', id=new_id,
                       kind=wx.ITEM_RADIO, text=str(int(round(value * 100))) + "%")
            self.Bind(wx.EVT_MENU, self.GenerateZoomFunction(idx), id=new_id)

        parent.AppendSeparator()
        AppendMenu(parent, help='', id=ID_PLCOPENEDITORDISPLAYMENUSWITCHPERSPECTIVE,
                   kind=wx.ITEM_NORMAL, text=_(u'Switch perspective') + '\tF12')
        self.Bind(wx.EVT_MENU, self.SwitchPerspective, id=ID_PLCOPENEDITORDISPLAYMENUSWITCHPERSPECTIVE)

        AppendMenu(parent, help='', id=ID_PLCOPENEDITORDISPLAYMENUFULLSCREEN,
                   kind=wx.ITEM_NORMAL, text=_(u'Full screen') + '\tShift-F12')
        self.Bind(wx.EVT_MENU, self.SwitchFullScrMode, id=ID_PLCOPENEDITORDISPLAYMENUFULLSCREEN)

        AppendMenu(parent, help='', id=ID_PLCOPENEDITORDISPLAYMENURESETPERSPECTIVE,
                   kind=wx.ITEM_NORMAL, text=_(u'Reset Perspective'))
        self.Bind(wx.EVT_MENU, self.OnResetPerspective, id=ID_PLCOPENEDITORDISPLAYMENURESETPERSPECTIVE)

        self.Bind(wx.EVT_MENU, self.OnRefreshMenu, id=wx.ID_REFRESH)
        if self.EnableDebug:
            self.Bind(wx.EVT_MENU, self.OnClearErrorsMenu, id=wx.ID_CLEAR)

    def _init_coll_HelpMenu_Items(self, parent):
        pass

    def _init_utils(self):
        self.MenuBar = wx.MenuBar()

        self.FileMenu = wx.Menu(title='')
        self.EditMenu = wx.Menu(title='')
        self.DisplayMenu = wx.Menu(title='')
        self.HelpMenu = wx.Menu(title='')

        self._init_coll_MenuBar_Menus(self.MenuBar)
        self._init_coll_FileMenu_Items(self.FileMenu)
        self._init_coll_EditMenu_Items(self.EditMenu)
        self._init_coll_DisplayMenu_Items(self.DisplayMenu)
        self._init_coll_HelpMenu_Items(self.HelpMenu)

    def _init_icon(self, parent):
        if self.icon:
            self.SetIcon(self.icon)
        elif parent and parent.icon:
            self.SetIcon(parent.icon)

    def _init_ctrls(self, prnt):
        self._init_icon(prnt)
        self.SetClientSize(wx.Size(1000, 600))
        self.Bind(wx.EVT_ACTIVATE, self.OnActivated)

        self.TabsImageList = wx.ImageList(31, 16)
        self.TabsImageListIndexes = {}

        # -----------------------------------------------------------------------
        #                          Creating main structure
        # -----------------------------------------------------------------------

        self.AUIManager = wx.aui.AuiManager(self)
        self.AUIManager.SetDockSizeConstraint(0.5, 0.5)
        self.Panes = {}

        self.LeftNoteBook = wx.aui.AuiNotebook(
            self, ID_PLCOPENEDITORLEFTNOTEBOOK,
            style=(wx.aui.AUI_NB_TOP |
                   wx.aui.AUI_NB_TAB_SPLIT |
                   wx.aui.AUI_NB_TAB_MOVE |
                   wx.aui.AUI_NB_SCROLL_BUTTONS |
                   wx.aui.AUI_NB_TAB_EXTERNAL_MOVE))
        self.LeftNoteBook.Bind(wx.aui.EVT_AUINOTEBOOK_ALLOW_DND,
                               self.OnAllowNotebookDnD)
        self.AUIManager.AddPane(
            self.LeftNoteBook,
            wx.aui.AuiPaneInfo().Name("ProjectPane").Left().Layer(1).
            BestSize(wx.Size(300, 500)).CloseButton(False))

        self.BottomNoteBook = wx.aui.AuiNotebook(
            self, ID_PLCOPENEDITORBOTTOMNOTEBOOK,
            style=(wx.aui.AUI_NB_TOP |
                   wx.aui.AUI_NB_TAB_SPLIT |
                   wx.aui.AUI_NB_TAB_MOVE |
                   wx.aui.AUI_NB_SCROLL_BUTTONS |
                   wx.aui.AUI_NB_TAB_EXTERNAL_MOVE))
        self.BottomNoteBook.Bind(wx.aui.EVT_AUINOTEBOOK_ALLOW_DND,
                                 self.OnAllowNotebookDnD)
        self.AUIManager.AddPane(
            self.BottomNoteBook,
            wx.aui.AuiPaneInfo().Name("ResultPane").Bottom().Layer(0).
            BestSize(wx.Size(800, 300)).CloseButton(False))

        self.RightNoteBook = wx.aui.AuiNotebook(
            self, ID_PLCOPENEDITORRIGHTNOTEBOOK,
            style=(wx.aui.AUI_NB_TOP |
                   wx.aui.AUI_NB_TAB_SPLIT |
                   wx.aui.AUI_NB_TAB_MOVE |
                   wx.aui.AUI_NB_SCROLL_BUTTONS |
                   wx.aui.AUI_NB_TAB_EXTERNAL_MOVE))
        self.RightNoteBook.Bind(wx.aui.EVT_AUINOTEBOOK_ALLOW_DND,
                                self.OnAllowNotebookDnD)
        self.AUIManager.AddPane(
            self.RightNoteBook,
            wx.aui.AuiPaneInfo().Name("LibraryPane").Right().Layer(0).
            BestSize(wx.Size(250, 400)).CloseButton(False))

        self.TabsOpened = wx.aui.AuiNotebook(
            self, ID_PLCOPENEDITORTABSOPENED,
            style=(wx.aui.AUI_NB_DEFAULT_STYLE |
                   wx.aui.AUI_NB_WINDOWLIST_BUTTON))
        self.TabsOpened.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING,
                             self.OnPouSelectedChanging)
        self.TabsOpened.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED,
                             self.OnPouSelectedChanged)
        self.TabsOpened.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE,
                             self.OnPageClose)
        self.TabsOpened.Bind(wx.aui.EVT_AUINOTEBOOK_END_DRAG,
                             self.OnPageDragged)
        self.AUIManager.AddPane(self.TabsOpened,
                                wx.aui.AuiPaneInfo().CentrePane().Name("TabsPane"))

        # -----------------------------------------------------------------------
        #                    Creating PLCopen Project Types Tree
        # -----------------------------------------------------------------------

        self.MainTabs = {}

        self.ProjectPanel = wx.SplitterWindow(
            id=ID_PLCOPENEDITORPROJECTPANEL,
            name='ProjectPanel', parent=self.LeftNoteBook, point=wx.Point(0, 0),
            size=wx.Size(0, 0), style=wx.SP_3D)

        self.ProjectTree = CustomTree(id=ID_PLCOPENEDITORPROJECTTREE,
                                      name='ProjectTree',
                                      parent=self.ProjectPanel,
                                      pos=wx.Point(0, 0), size=wx.Size(0, 0),
                                      style=wx.SUNKEN_BORDER,
                                      agwStyle=(wx.TR_HAS_BUTTONS |
                                                wx.TR_SINGLE |
                                                wx.TR_EDIT_LABELS))
        self.ProjectTree.SetBackgroundBitmap(GetBitmap("custom_tree_background"),
                                             wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM)
        add_menu = wx.Menu()
        self._init_coll_AddMenu_Items(add_menu)
        self.ProjectTree.SetAddMenu(add_menu)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnProjectTreeRightUp,
                  id=ID_PLCOPENEDITORPROJECTTREE)
        self.ProjectTree.Bind(wx.EVT_LEFT_UP, self.OnProjectTreeLeftUp)
        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.OnProjectTreeItemChanging,
                  id=ID_PLCOPENEDITORPROJECTTREE)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnProjectTreeBeginDrag,
                  id=ID_PLCOPENEDITORPROJECTTREE)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnProjectTreeItemBeginEdit,
                  id=ID_PLCOPENEDITORPROJECTTREE)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnProjectTreeItemEndEdit,
                  id=ID_PLCOPENEDITORPROJECTTREE)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnProjectTreeItemActivated,
                  id=ID_PLCOPENEDITORPROJECTTREE)
        self.ProjectTree.Bind(wx.EVT_MOTION, self.OnProjectTreeMotion)

        # -----------------------------------------------------------------------
        #        Creating PLCopen Project POU Instance Variables Panel
        # -----------------------------------------------------------------------

        self.PouInstanceVariablesPanel = PouInstanceVariablesPanel(self.ProjectPanel, self, self.Controler, self.EnableDebug)

        self.MainTabs["ProjectPanel"] = (self.ProjectPanel, _("Project"))
        self.LeftNoteBook.AddPage(*self.MainTabs["ProjectPanel"])

        self.ProjectPanel.SplitHorizontally(self.ProjectTree, self.PouInstanceVariablesPanel, 300)

        # -----------------------------------------------------------------------
        #                            Creating Tool Bar
        # -----------------------------------------------------------------------

        MenuToolBar = wx.ToolBar(self, ID_PLCOPENEDITOREDITORMENUTOOLBAR,
                                 wx.DefaultPosition, wx.DefaultSize,
                                 wx.TB_FLAT | wx.TB_NODIVIDER | wx.NO_BORDER)
        MenuToolBar.SetToolBitmapSize(wx.Size(25, 25))
        MenuToolBar.Realize()
        self.Panes["MenuToolBar"] = MenuToolBar
        self.AUIManager.AddPane(MenuToolBar, wx.aui.AuiPaneInfo().
                                Name("MenuToolBar").Caption(_("Menu ToolBar")).
                                ToolbarPane().Top().
                                LeftDockable(False).RightDockable(False))

        EditorToolBar = wx.ToolBar(self, ID_PLCOPENEDITOREDITORTOOLBAR,
                                   wx.DefaultPosition, wx.DefaultSize,
                                   wx.TB_FLAT | wx.TB_NODIVIDER | wx.NO_BORDER)
        EditorToolBar.SetToolBitmapSize(wx.Size(25, 25))
        EditorToolBar.AddRadioTool(ID_PLCOPENEDITOREDITORTOOLBARSELECTION,
                                   GetBitmap("select"),
                                   wx.NullBitmap,
                                   _("Select an object"))
        EditorToolBar.Realize()
        self.Panes["EditorToolBar"] = EditorToolBar
        self.AUIManager.AddPane(EditorToolBar, wx.aui.AuiPaneInfo().
                                Name("EditorToolBar").Caption(_("Editor ToolBar")).
                                ToolbarPane().Top().Position(1).
                                LeftDockable(False).RightDockable(False))

        self.Bind(wx.EVT_MENU, self.OnSelectionTool,
                  id=ID_PLCOPENEDITOREDITORTOOLBARSELECTION)

        # -----------------------------------------------------------------------
        #                            Creating Search Panel
        # -----------------------------------------------------------------------

        self.SearchResultPanel = SearchResultPanel(self.BottomNoteBook, self)
        self.MainTabs["SearchResultPanel"] = (self.SearchResultPanel, _("Search"))
        self.BottomNoteBook.AddPage(*self.MainTabs["SearchResultPanel"])

        # -----------------------------------------------------------------------
        #                            Creating Library Panel
        # -----------------------------------------------------------------------

        self.LibraryPanel = LibraryPanel(self, True)
        self.MainTabs["LibraryPanel"] = (self.LibraryPanel, _("Library"))
        self.RightNoteBook.AddPage(*self.MainTabs["LibraryPanel"])

        self._init_utils()
        self.SetMenuBar(self.MenuBar)

        if self.EnableDebug:
            self.DebugVariablePanel = DebugVariablePanel(self.RightNoteBook, self.Controler, self)
            self.MainTabs["DebugVariablePanel"] = (self.DebugVariablePanel, _("Debugger"))
            self.RightNoteBook.AddPage(*self.MainTabs["DebugVariablePanel"])

        self.AUIManager.Update()

    def __init__(self, parent, enable_debug=False):
        wx.Frame.__init__(self, id=ID_PLCOPENEDITOR, name='IDEFrame',
                          parent=parent, pos=wx.DefaultPosition,
                          size=wx.Size(1000, 600),
                          style=wx.DEFAULT_FRAME_STYLE)

        self.UNEDITABLE_NAMES_DICT = dict([(_(n), n) for n in UNEDITABLE_NAMES])

        self.Controler = None
        self.Config = wx.ConfigBase.Get()
        self.EnableDebug = enable_debug

        self.InitEditorToolbarItems()
        self._init_ctrls(parent)

        # Define Tree item icon list
        self.TreeImageList = wx.ImageList(16, 16)
        self.TreeImageDict = {}

        # Icons for languages
        for language in LANGUAGES:
            self.TreeImageDict[language] = self.TreeImageList.Add(GetBitmap(language))

        # Icons for other items
        for imgname, itemtype in [
                # editables
                ("PROJECT",        ITEM_PROJECT),
                # ("POU",          ITEM_POU),
                # ("VARIABLE",     ITEM_VARIABLE),
                ("TRANSITION",     ITEM_TRANSITION),
                ("ACTION",         ITEM_ACTION),
                ("CONFIGURATION",  ITEM_CONFIGURATION),
                ("RESOURCE",       ITEM_RESOURCE),
                ("DATATYPE",       ITEM_DATATYPE),
                # uneditables
                ("DATATYPES",      ITEM_DATATYPES),
                ("FUNCTION",       ITEM_FUNCTION),
                ("FUNCTIONBLOCK",  ITEM_FUNCTIONBLOCK),
                ("PROGRAM",        ITEM_PROGRAM),
                ("VAR_LOCAL",      ITEM_VAR_LOCAL),
                ("VAR_LOCAL",      ITEM_VAR_GLOBAL),
                ("VAR_LOCAL",      ITEM_VAR_EXTERNAL),
                ("VAR_LOCAL",      ITEM_VAR_TEMP),
                ("VAR_INPUT",      ITEM_VAR_INPUT),
                ("VAR_OUTPUT",     ITEM_VAR_OUTPUT),
                ("VAR_INOUT",      ITEM_VAR_INOUT),
                ("TRANSITIONS",    ITEM_TRANSITIONS),
                ("ACTIONS",        ITEM_ACTIONS),
                ("CONFIGURATIONS", ITEM_CONFIGURATIONS),
                ("RESOURCES",      ITEM_RESOURCES),
                ("PROPERTIES",     ITEM_PROPERTIES)]:
            self.TreeImageDict[itemtype] = self.TreeImageList.Add(GetBitmap(imgname))

        # Assign icon list to TreeCtrls
        self.ProjectTree.SetImageList(self.TreeImageList)
        self.PouInstanceVariablesPanel.SetTreeImageList(self.TreeImageList)

        self.CurrentEditorToolBar = []
        self.CurrentMenu = None
        self.SelectedItem = None
        self.LastToolTipItem = None
        self.SearchParams = None
        self.Highlights = {}
        self.DrawingMode = FREEDRAWING_MODE
        # self.DrawingMode = DRIVENDRAWING_MODE
        self.AuiTabCtrl = []

        # Save default perspective
        notebooks = {}
        for notebook, entry_name in [(self.LeftNoteBook, "leftnotebook"),
                                     (self.BottomNoteBook, "bottomnotebook"),
                                     (self.RightNoteBook, "rightnotebook")]:
            notebooks[entry_name] = self.SaveTabLayout(notebook)
        self.DefaultPerspective = {
            "perspective": self.AUIManager.SavePerspective(),
            "notebooks": notebooks,
        }

        # Initialize Printing configuring elements
        self.PrintData = wx.PrintData()
        self.PrintData.SetPaperId(wx.PAPER_A4)
        self.PrintData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        self.PageSetupData = wx.PageSetupDialogData(self.PrintData)
        self.PageSetupData.SetMarginTopLeft(wx.Point(10, 15))
        self.PageSetupData.SetMarginBottomRight(wx.Point(10, 20))

        self.SetRefreshFunctions()
        self.SetDeleteFunctions()

        wx.CallAfter(self.InitFindDialog)

    def __del__(self):
        self.FindDialog.Destroy()

    def InitFindDialog(self):
        self.FindDialog = FindInPouDialog(self)
        self.FindDialog.Hide()

    def Show(self):
        wx.Frame.Show(self)
        wx.CallAfter(self.RestoreLastState)

    def OnActivated(self, event):
        if event.GetActive():
            wx.CallAfter(self._Refresh, TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)
        event.Skip()

    def SelectTab(self, tab):
        for notebook in [self.LeftNoteBook, self.BottomNoteBook, self.RightNoteBook]:
            idx = notebook.GetPageIndex(tab)
            if idx != wx.NOT_FOUND and idx != notebook.GetSelection():
                notebook.SetSelection(idx)
                return

    # -------------------------------------------------------------------------------
    #                Saving and restoring frame organization functions
    # -------------------------------------------------------------------------------

    def GetTabInfos(self, tab):
        for page_name, (page_ref, _page_title) in self.MainTabs.iteritems():
            if page_ref == tab:
                return ("main", page_name)
        return None

    def SaveTabLayout(self, notebook):
        tabs = []
        for child in notebook.GetChildren():
            if isinstance(child, wx.aui.AuiTabCtrl):
                if child.GetPageCount() > 0:
                    pos = child.GetPosition()
                    tab = {"pos": (pos.x, pos.y), "pages": []}
                    tab_size = child.GetSize()
                    for page_idx in xrange(child.GetPageCount()):
                        page = child.GetWindowFromIdx(page_idx)
                        if "size" not in tab:
                            tab["size"] = (tab_size[0], tab_size[1] + page.GetSize()[1])
                        tab_infos = self.GetTabInfos(page)
                        if tab_infos is not None:
                            tab["pages"].append((tab_infos, page_idx == child.GetActivePage()))
                    tabs.append(tab)
        tabs.sort(lambda x, y: cmp(x["pos"], y["pos"]))
        size = notebook.GetSize()
        return ComputeTabsLayout(tabs, wx.Rect(1, 1, size[0] - NOTEBOOK_BORDER, size[1] - NOTEBOOK_BORDER))

    def LoadTab(self, notebook, page_infos):
        if page_infos[0] == "main":
            infos = self.MainTabs.get(page_infos[1])
            if infos is not None:
                page_ref, page_title = infos
                notebook.AddPage(page_ref, page_title)
                return notebook.GetPageIndex(page_ref)
        elif page_infos[0] == "editor":
            tagname = page_infos[1]
            page_ref = self.EditProjectElement(GetElementType(tagname), tagname)
            if page_ref is not None:
                page_ref.RefreshView()
                return notebook.GetPageIndex(page_ref)
        elif page_infos[0] == "debug":
            instance_path = page_infos[1]
            instance_infos = self.Controler.GetInstanceInfos(instance_path, self.EnableDebug)
            if instance_infos is not None:
                return notebook.GetPageIndex(self.OpenDebugViewer(instance_infos["class"], instance_path, instance_infos["type"]))
        return None

    def LoadTabLayout(self, notebook, tabs, mode="all", first_index=None):
        if isinstance(tabs, list):
            if len(tabs) == 0:
                return
            raise ValueError("Not supported")

        if "split" in tabs:
            self.LoadTabLayout(notebook, tabs["others"])

            split_dir, _split_ratio = tabs["split"]
            first_index = self.LoadTabLayout(notebook, tabs["tab"], mode="first")
            notebook.Split(first_index, split_dir)
            self.LoadTabLayout(notebook, tabs["tab"], mode="others", first_index=first_index)

        elif mode == "first":
            return self.LoadTab(notebook, tabs["pages"][0][0])
        else:
            selected = first_index
            if mode == "others":
                add_tabs = tabs["pages"][1:]
            else:
                add_tabs = tabs["pages"]
            for page_infos, page_selected in add_tabs:
                page_idx = self.LoadTab(notebook, page_infos)
                if page_selected:
                    selected = page_idx
            if selected is not None:
                wx.CallAfter(notebook.SetSelection, selected)

    def ResetPerspective(self):
        if self.DefaultPerspective is not None:
            self.AUIManager.LoadPerspective(self.DefaultPerspective["perspective"])

            for notebook in [self.LeftNoteBook, self.BottomNoteBook, self.RightNoteBook]:
                for dummy in xrange(notebook.GetPageCount()):
                    notebook.RemovePage(0)

            notebooks = self.DefaultPerspective["notebooks"]
            for notebook, entry_name in [(self.LeftNoteBook, "leftnotebook"),
                                         (self.BottomNoteBook, "bottomnotebook"),
                                         (self.RightNoteBook, "rightnotebook")]:
                self.LoadTabLayout(notebook, notebooks.get(entry_name))

            self._Refresh(EDITORTOOLBAR)

    def RestoreLastState(self):
        frame_size = None
        if self.Config.HasEntry("framesize"):
            frame_size = cPickle.loads(str(self.Config.Read("framesize")))

        if frame_size is None:
            self.Maximize()
        else:
            self.SetClientSize(frame_size)

    def SaveLastState(self):
        if not self.IsMaximized():
            self.Config.Write("framesize", cPickle.dumps(self.GetClientSize()))
        elif self.Config.HasEntry("framesize"):
            self.Config.DeleteEntry("framesize")

        self.Config.Flush()

    # -------------------------------------------------------------------------------
    #                               General Functions
    # -------------------------------------------------------------------------------

    def SetRefreshFunctions(self):
        self.RefreshFunctions = {
            TITLE: self.RefreshTitle,
            EDITORTOOLBAR: self.RefreshEditorToolBar,
            FILEMENU: self.RefreshFileMenu,
            EDITMENU: self.RefreshEditMenu,
            DISPLAYMENU: self.RefreshDisplayMenu,
            PROJECTTREE: self.RefreshProjectTree,
            POUINSTANCEVARIABLESPANEL: self.RefreshPouInstanceVariablesPanel,
            LIBRARYTREE: self.RefreshLibraryPanel,
            SCALING: self.RefreshScaling,
            PAGETITLES: self.RefreshPageTitles}

    def _Refresh(self, *elements):
        """Call Editor refresh functions.

        :param elements: List of elements to refresh.
        """
        try:
            for element in elements:
                self.RefreshFunctions[element]()
        except wx.PyDeadObjectError:
            # ignore exceptions caused by refresh while quitting
            pass

    def OnPageClose(self, event):
        """Callback function when AUINotebook Page closed with CloseButton

        :param event: AUINotebook Event.
        """
        selected = self.TabsOpened.GetSelection()
        if selected > -1:
            window = self.TabsOpened.GetPage(selected)

            if window.CheckSaveBeforeClosing():

                # Refresh all window elements that have changed
                wx.CallAfter(self._Refresh, TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)
                wx.CallAfter(self.RefreshTabCtrlEvent)
                wx.CallAfter(self.CloseFindInPouDialog)
                event.Skip()
            else:
                event.Veto()

    def GetCopyBuffer(self, primary_selection=False):
        data = None
        if primary_selection and wx.Platform == '__WXMSW__':
            return data
        else:
            wx.TheClipboard.UsePrimarySelection(primary_selection)

        if not wx.TheClipboard.IsOpened():
            dataobj = wx.TextDataObject()
            if wx.TheClipboard.Open():
                success = False
                try:
                    success = wx.TheClipboard.GetData(dataobj)
                except wx._core.PyAssertionError:
                    pass
                wx.TheClipboard.Close()
                if success:
                    data = dataobj.GetText()
        return data

    def SetCopyBuffer(self, text, primary_selection=False):
        if primary_selection and wx.Platform == '__WXMSW__':
            return
        else:
            wx.TheClipboard.UsePrimarySelection(primary_selection)
        if not wx.TheClipboard.IsOpened():
            data = wx.TextDataObject()
            data.SetText(text)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data)
                wx.TheClipboard.Flush()
                wx.TheClipboard.Close()
        wx.CallAfter(self.RefreshEditMenu)

    def GetDrawingMode(self):
        return self.DrawingMode

    def RefreshScaling(self):
        for i in xrange(self.TabsOpened.GetPageCount()):
            editor = self.TabsOpened.GetPage(i)
            editor.RefreshScaling()

    def EditProjectSettings(self):
        old_values = self.Controler.GetProjectProperties()
        dialog = ProjectDialog(self)
        dialog.SetValues(old_values)
        if dialog.ShowModal() == wx.ID_OK:
            new_values = dialog.GetValues()
            new_values["creationDateTime"] = old_values["creationDateTime"]
            if new_values != old_values:
                self.Controler.SetProjectProperties(None, new_values)
                self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU,
                              PROJECTTREE, POUINSTANCEVARIABLESPANEL, SCALING)
        dialog.Destroy()

    # -------------------------------------------------------------------------------
    #                            Notebook Unified Functions
    # -------------------------------------------------------------------------------

    def AddPage(self, window, text):
        """Function that add a tab in Notebook, calling refresh for tab DClick event
        for wx.aui.AUINotebook.

        :param window: Panel to display in tab.
        :param text: title for the tab ctrl.
        """
        self.TabsOpened.AddPage(window, text)
        self.RefreshTabCtrlEvent()

    def DeletePage(self, window):
        for idx in xrange(self.TabsOpened.GetPageCount()):
            if self.TabsOpened.GetPage(idx) == window:
                self.TabsOpened.DeletePage(idx)
                self.RefreshTabCtrlEvent()
                return

    def DeleteAllPages(self):
        """Function that fix difference in deleting all tabs between
        wx.Notebook and wx.aui.AUINotebook.
        """
        for dummy in xrange(self.TabsOpened.GetPageCount()):
            self.TabsOpened.DeletePage(0)
        self.RefreshTabCtrlEvent()

    def SetPageBitmap(self, idx, bitmap):
        """Function that fix difference in setting picture on tab between
        wx.Notebook and wx.aui.AUINotebook.

        :param idx: Tab index.
        :param bitmap: wx.Bitmap to define on tab.
        :returns: True if operation succeeded
        """
        return self.TabsOpened.SetPageBitmap(idx, bitmap)

    # -------------------------------------------------------------------------------
    #                         Dialog Message Functions
    # -------------------------------------------------------------------------------

    def ShowErrorMessage(self, message):
        """Function displaying an Error dialog in editor.

        :param message: The message to display.
        """
        dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def CheckSaveBeforeClosing(self, title=_("Close Project")):
        """Function displaying an question dialog if project is not saved"

        :returns: False if closing cancelled.
        """
        if not self.Controler.ProjectIsSaved():
            dialog = wx.MessageDialog(self, _("There are changes, do you want to save?"), title, wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = dialog.ShowModal()
            dialog.Destroy()
            if answer == wx.ID_YES:
                self.SaveProject()
            elif answer == wx.ID_CANCEL:
                return False

        for idx in xrange(self.TabsOpened.GetPageCount()):
            window = self.TabsOpened.GetPage(idx)
            if not window.CheckSaveBeforeClosing():
                return False

        return True

    # -------------------------------------------------------------------------------
    #                            File Menu Functions
    # -------------------------------------------------------------------------------

    def RefreshFileMenu(self):
        pass

    def ResetView(self):
        self.DeleteAllPages()
        self.ProjectTree.DeleteAllItems()
        self.ProjectTree.Enable(False)
        self.PouInstanceVariablesPanel.ResetView()
        self.LibraryPanel.ResetTree()
        self.LibraryPanel.SetController(None)
        if self.EnableDebug:
            self.DebugVariablePanel.ResetView()
        self.Controler = None

    def OnCloseTabMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected >= 0:
            self.TabsOpened.DeletePage(selected)
            if self.TabsOpened.GetPageCount() > 0:
                new_index = min(selected, self.TabsOpened.GetPageCount() - 1)
                self.TabsOpened.SetSelection(new_index)
        # Refresh all window elements that have changed
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)
        self.RefreshTabCtrlEvent()

    def OnPageSetupMenu(self, event):
        dialog = wx.PageSetupDialog(self, self.PageSetupData)
        if dialog.ShowModal() == wx.ID_OK:
            self.PageSetupData = wx.PageSetupDialogData(dialog.GetPageSetupData())
            self.PrintData = wx.PrintData(self.PageSetupData.GetPrintData())
        dialog.Destroy()

    def OnPreviewMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            data = wx.PrintDialogData(self.PrintData)
            properties = self.Controler.GetProjectProperties(window.IsDebugging())
            page_size = map(int, properties["pageSize"])
            margins = (self.PageSetupData.GetMarginTopLeft(), self.PageSetupData.GetMarginBottomRight())
            printout = GraphicPrintout(window, page_size, margins, True)
            printout2 = GraphicPrintout(window, page_size, margins, True)
            preview = wx.PrintPreview(printout, printout2, data)

            if preview.Ok():
                preview_frame = wx.PreviewFrame(preview, self, _("Print preview"), style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)

                preview_frame.Initialize()

                preview_canvas = preview.GetCanvas()
                preview_canvas.SetMinSize(preview_canvas.GetVirtualSize())
                preview_frame.Fit()

                preview_frame.Show(True)

    def OnPrintMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            dialog_data = wx.PrintDialogData(self.PrintData)
            dialog_data.SetToPage(1)
            properties = self.Controler.GetProjectProperties(window.IsDebugging())
            page_size = map(int, properties["pageSize"])
            margins = (self.PageSetupData.GetMarginTopLeft(), self.PageSetupData.GetMarginBottomRight())
            printer = wx.Printer(dialog_data)
            printout = GraphicPrintout(window, page_size, margins)

            if not printer.Print(self, printout, True) and printer.GetLastError() != wx.PRINTER_CANCELLED:
                self.ShowErrorMessage(_("There was a problem printing.\nPerhaps your current printer is not set correctly?"))
            printout.Destroy()

    def OnPropertiesMenu(self, event):
        self.EditProjectSettings()

    def OnQuitMenu(self, event):
        self.Close()

    # -------------------------------------------------------------------------------
    #                            Edit Menu Functions
    # -------------------------------------------------------------------------------

    def RefreshEditMenu(self):
        MenuToolBar = self.Panes["MenuToolBar"]
        if self.Controler is not None:
            selected = self.TabsOpened.GetSelection()
            if selected > -1:
                window = self.TabsOpened.GetPage(selected)
                undo, redo = window.GetBufferState()
            else:
                undo, redo = self.Controler.GetBufferState()
            self.EditMenu.Enable(wx.ID_UNDO, undo)
            MenuToolBar.EnableTool(wx.ID_UNDO, undo)
            self.EditMenu.Enable(wx.ID_REDO, redo)
            MenuToolBar.EnableTool(wx.ID_REDO, redo)
            # self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUENABLEUNDOREDO, True)
            # self.EditMenu.Check(ID_PLCOPENEDITOREDITMENUENABLEUNDOREDO,
            #                self.Controler.IsProjectBufferEnabled())
            self.EditMenu.Enable(wx.ID_FIND, selected > -1)
            self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUFINDNEXT,
                                 selected > -1 and self.SearchParams is not None)
            self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUFINDPREVIOUS,
                                 selected > -1 and self.SearchParams is not None)
            self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT, True)
            MenuToolBar.EnableTool(ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT, True)
            self.EditMenu.Enable(wx.ID_ADD, True)
            self.EditMenu.Enable(wx.ID_DELETE, True)
            if self.TabsOpened.GetPageCount() > 0:
                self.EditMenu.Enable(wx.ID_CUT, True)
                MenuToolBar.EnableTool(wx.ID_CUT, True)
                self.EditMenu.Enable(wx.ID_COPY, True)
                MenuToolBar.EnableTool(wx.ID_COPY, True)
                if self.GetCopyBuffer() is not None:
                    self.EditMenu.Enable(wx.ID_PASTE, True)
                    MenuToolBar.EnableTool(wx.ID_PASTE, True)
                else:
                    self.EditMenu.Enable(wx.ID_PASTE, False)
                    MenuToolBar.EnableTool(wx.ID_PASTE, False)
                self.EditMenu.Enable(wx.ID_SELECTALL, True)
            else:
                self.EditMenu.Enable(wx.ID_CUT, False)
                MenuToolBar.EnableTool(wx.ID_CUT, False)
                self.EditMenu.Enable(wx.ID_COPY, False)
                MenuToolBar.EnableTool(wx.ID_COPY, False)
                self.EditMenu.Enable(wx.ID_PASTE, False)
                MenuToolBar.EnableTool(wx.ID_PASTE, False)
                self.EditMenu.Enable(wx.ID_SELECTALL, False)
        else:
            self.EditMenu.Enable(wx.ID_UNDO, False)
            MenuToolBar.EnableTool(wx.ID_UNDO, False)
            self.EditMenu.Enable(wx.ID_REDO, False)
            MenuToolBar.EnableTool(wx.ID_REDO, False)
            # self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUENABLEUNDOREDO, False)
            self.EditMenu.Enable(wx.ID_CUT, False)
            MenuToolBar.EnableTool(wx.ID_CUT, False)
            self.EditMenu.Enable(wx.ID_COPY, False)
            MenuToolBar.EnableTool(wx.ID_COPY, False)
            self.EditMenu.Enable(wx.ID_PASTE, False)
            MenuToolBar.EnableTool(wx.ID_PASTE, False)
            self.EditMenu.Enable(wx.ID_SELECTALL, False)
            self.EditMenu.Enable(wx.ID_FIND, False)
            self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUFINDNEXT, False)
            self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUFINDPREVIOUS, False)
            self.EditMenu.Enable(ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT, False)
            MenuToolBar.EnableTool(ID_PLCOPENEDITOREDITMENUSEARCHINPROJECT, False)
            self.EditMenu.Enable(wx.ID_ADD, False)
            self.EditMenu.Enable(wx.ID_DELETE, False)

    def CloseTabsWithoutModel(self, refresh=True):
        idxs = range(self.TabsOpened.GetPageCount())
        idxs.reverse()
        for idx in idxs:
            window = self.TabsOpened.GetPage(idx)
            if window.HasNoModel():
                self.TabsOpened.DeletePage(idx)
        if refresh:
            self.RefreshEditor()

    def OnUndoMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            window.Undo()
        else:
            self.Controler.LoadPrevious()
        self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE,
                      SCALING, PAGETITLES)

    def OnRedoMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            window.Redo()
        else:
            self.Controler.LoadNext()
        self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE,
                      SCALING, PAGETITLES)

    def OnEnableUndoRedoMenu(self, event):
        self.Controler.EnableProjectBuffer(event.IsChecked())
        self.RefreshEditMenu()

    OnCutMenu = GetShortcutKeyCallbackFunction("Cut")
    OnCopyMenu = GetShortcutKeyCallbackFunction("Copy")
    OnPasteMenu = GetShortcutKeyCallbackFunction("Paste")

    def OnSelectAllMenu(self, event):
        control = self.FindFocus()
        if control is not None and control.GetName() == "Viewer":
            control.Parent.SelectAll()
        elif isinstance(control, wx.stc.StyledTextCtrl):
            control.SelectAll()
        elif isinstance(control, wx.TextCtrl):
            control.SetSelection(0, control.GetLastPosition())
        elif isinstance(control, wx.ComboBox):
            control.SetMark(0, control.GetLastPosition() + 1)

    def SetDeleteFunctions(self):
        self.DeleteFunctions = {
            ITEM_DATATYPE: GetDeleteElementFunction(
                PLCControler.ProjectRemoveDataType,
                check_function=self.CheckDataTypeIsUsedBeforeDeletion),
            ITEM_POU: GetDeleteElementFunction(
                PLCControler.ProjectRemovePou,
                check_function=self.CheckPouIsUsedBeforeDeletion),
            ITEM_TRANSITION: GetDeleteElementFunction(
                PLCControler.ProjectRemovePouTransition, ITEM_POU),
            ITEM_ACTION: GetDeleteElementFunction(
                PLCControler.ProjectRemovePouAction, ITEM_POU),
            ITEM_CONFIGURATION: GetDeleteElementFunction(
                PLCControler.ProjectRemoveConfiguration),
            ITEM_RESOURCE: GetDeleteElementFunction(
                PLCControler.ProjectRemoveConfigurationResource, ITEM_CONFIGURATION)
        }

    def OnDeleteMenu(self, event):
        window = self.FindFocus()
        if window == self.ProjectTree or window is None:
            selected = self.ProjectTree.GetSelection()
            if selected is not None and selected.IsOk():
                function = self.DeleteFunctions.get(self.ProjectTree.GetPyData(selected)["type"], None)
                if function is not None:
                    function(self, selected)
                    self.CloseTabsWithoutModel()
                    self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, PROJECTTREE,
                                  POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        elif isinstance(window, (Viewer, TextViewer)):
            event = wx.KeyEvent(wx.EVT_CHAR._getEvtType())
            event.m_keyCode = wx.WXK_DELETE
            window.ProcessEvent(event)

    def OnFindMenu(self, event):
        if not self.FindDialog.IsShown():
            self.FindDialog.Show()
            self.FindDialog.FindPattern.SetFocus()

    def CloseFindInPouDialog(self):
        selected = self.TabsOpened.GetSelection()
        if selected == -1 and self.FindDialog.IsShown():
            self.FindDialog.Hide()

    def OnFindNextMenu(self, event):
        self.FindInPou(1)

    def OnFindPreviousMenu(self, event):
        self.FindInPou(-1)

    def FindInPou(self, direction, search_params=None):
        if search_params is not None:
            self.SearchParams = search_params
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            window.Find(direction, self.SearchParams)

    def OnSearchInProjectMenu(self, event):
        dialog = SearchInProjectDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            criteria = dialog.GetCriteria()
            if len(criteria) > 0:
                result = self.Controler.SearchInProject(criteria)
                self.ClearSearchResults()
                self.SearchResultPanel.SetSearchResults(criteria, result)
                self.SelectTab(self.SearchResultPanel)

    # -------------------------------------------------------------------------------
    #                             Display Menu Functions
    # -------------------------------------------------------------------------------

    def RefreshDisplayMenu(self):
        if self.Controler is not None:
            if self.TabsOpened.GetPageCount() > 0:
                self.DisplayMenu.Enable(wx.ID_REFRESH, True)
                selected = self.TabsOpened.GetSelection()
                if selected != -1:
                    window = self.TabsOpened.GetPage(selected)
                    if isinstance(window, Viewer):
                        self.DisplayMenu.Enable(wx.ID_ZOOM_FIT, True)
                        zoommenu = self.DisplayMenu.FindItemById(wx.ID_ZOOM_FIT).GetSubMenu()
                        zoomitem = zoommenu.FindItemByPosition(window.GetScale())
                        zoomitem.Check(True)
                    else:
                        self.DisplayMenu.Enable(wx.ID_ZOOM_FIT, False)
                else:
                    self.DisplayMenu.Enable(wx.ID_ZOOM_FIT, False)
            else:
                self.DisplayMenu.Enable(wx.ID_REFRESH, False)
                self.DisplayMenu.Enable(wx.ID_ZOOM_FIT, False)
            if self.EnableDebug:
                self.DisplayMenu.Enable(wx.ID_CLEAR, True)
        else:
            self.DisplayMenu.Enable(wx.ID_REFRESH, False)
            if self.EnableDebug:
                self.DisplayMenu.Enable(wx.ID_CLEAR, False)
            self.DisplayMenu.Enable(wx.ID_ZOOM_FIT, False)

    def OnRefreshMenu(self, event):
        self.RefreshEditor()

    def OnClearErrorsMenu(self, event):
        self.ClearErrors()

    def GenerateZoomFunction(self, idx):
        def ZoomFunction(event):
            selected = self.TabsOpened.GetSelection()
            if selected != -1:
                window = self.TabsOpened.GetPage(selected)
                window.SetScale(idx)
                window.RefreshVisibleElements()
                window.RefreshScrollBars()
            event.Skip()
        return ZoomFunction

    def OnResetPerspective(self, event):
        self.ResetPerspective()

    # -------------------------------------------------------------------------------
    #                      Project Editor Panels Management Functions
    # -------------------------------------------------------------------------------

    def OnPageDragged(self, event):
        wx.CallAfter(self.RefreshTabCtrlEvent)
        event.Skip()

    def OnAllowNotebookDnD(self, event):
        event.Allow()

    def RefreshTabCtrlEvent(self):
        auitabctrl = []
        for child in self.TabsOpened.GetChildren():
            if isinstance(child, wx.aui.AuiTabCtrl):
                auitabctrl.append(child)
                if child not in self.AuiTabCtrl:
                    child.Bind(wx.EVT_LEFT_DCLICK, self.GetTabsOpenedDClickFunction(child))
        self.AuiTabCtrl = auitabctrl
        if self.TabsOpened.GetPageCount() == 0:
            pane = self.AUIManager.GetPane(self.TabsOpened)
            if pane.IsMaximized():
                self.AUIManager.RestorePane(pane)
            self.AUIManager.Update()

    def EnsureTabVisible(self, tab):
        notebook = tab.GetParent()
        notebook.SetSelection(notebook.GetPageIndex(tab))

    def OnPouSelectedChanging(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected >= 0:
            window = self.TabsOpened.GetPage(selected)
            if not window.IsDebugging():
                window.ResetBuffer()
        event.Skip()

    def OnPouSelectedChanged(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected >= 0:
            window = self.TabsOpened.GetPage(selected)
            tagname = window.GetTagName()
            if not window.IsDebugging():
                self.SelectProjectTreeItem(tagname)
                self.PouInstanceVariablesPanel.SetPouType(tagname)
                window.RefreshView()
                self.EnsureTabVisible(self.LibraryPanel)
            else:
                instance_path = window.GetInstancePath()
                if tagname == "":
                    instance_path = instance_path.rsplit(".", 1)[0]
                    tagname = self.Controler.GetPouInstanceTagName(instance_path, self.EnableDebug)
                self.EnsureTabVisible(self.DebugVariablePanel)
                wx.CallAfter(self.PouInstanceVariablesPanel.SetPouType, tagname, instance_path)
        wx.CallAfter(self._Refresh, FILEMENU, EDITMENU, DISPLAYMENU, EDITORTOOLBAR)
        event.Skip()

    def RefreshEditor(self):
        selected = self.TabsOpened.GetSelection()
        if selected >= 0:
            window = self.TabsOpened.GetPage(selected)
            tagname = window.GetTagName()
            if not window.IsDebugging():
                self.SelectProjectTreeItem(tagname)
                self.PouInstanceVariablesPanel.SetPouType(tagname)
            else:
                instance_path = window.GetInstancePath()
                if tagname == "":
                    instance_path = instance_path.rsplit(".", 1)[0]
                    tagname = self.Controler.GetPouInstanceTagName(instance_path, self.EnableDebug)
                self.PouInstanceVariablesPanel.SetPouType(tagname, instance_path)
            for child in self.TabsOpened.GetChildren():
                if isinstance(child, wx.aui.AuiTabCtrl):
                    active_page = child.GetActivePage()
                    if active_page >= 0:
                        window = child.GetWindowFromIdx(active_page)
                        window.RefreshView()
            self._Refresh(FILEMENU, EDITMENU, DISPLAYMENU, EDITORTOOLBAR)

    def RefreshEditorNames(self, old_tagname, new_tagname):
        for i in xrange(self.TabsOpened.GetPageCount()):
            editor = self.TabsOpened.GetPage(i)
            if editor.GetTagName() == old_tagname:
                editor.SetTagName(new_tagname)

    def IsOpened(self, tagname):
        for idx in xrange(self.TabsOpened.GetPageCount()):
            if self.TabsOpened.GetPage(idx).IsViewing(tagname):
                return idx
        return None

    def RefreshPageTitles(self):
        for idx in xrange(self.TabsOpened.GetPageCount()):
            window = self.TabsOpened.GetPage(idx)
            icon = window.GetIcon()
            if icon is not None:
                self.SetPageBitmap(idx, icon)
            self.TabsOpened.SetPageText(idx, window.GetTitle())

    def GetTabsOpenedDClickFunction(self, tabctrl):
        def OnTabsOpenedDClick(event):
            pos = event.GetPosition()
            if tabctrl.TabHitTest(pos.x, pos.y, None):
                self.SwitchPerspective(event)
            event.Skip()
        return OnTabsOpenedDClick

    def SwitchPerspective(self, evt):
        pane = self.AUIManager.GetPane(self.TabsOpened)
        if pane.IsMaximized():
            self.AUIManager.RestorePane(pane)
        else:
            self.AUIManager.MaximizePane(pane)
        self.AUIManager.Update()

    def SwitchFullScrMode(self, evt):
        show = not self.IsFullScreen()
        self.ShowFullScreen(show)

    # -------------------------------------------------------------------------------
    #                         Types Tree Management Functions
    # -------------------------------------------------------------------------------

    def RefreshProjectTree(self):
        # Extract current selected item tagname
        selected = self.ProjectTree.GetSelection()
        if selected is not None and selected.IsOk():
            item_infos = self.ProjectTree.GetPyData(selected)
            tagname = item_infos.get("tagname", None)
        else:
            tagname = None

        # Refresh treectrl items according to project infos
        if self.Controler:
            infos = self.Controler.GetProjectInfos()
            root = self.ProjectTree.GetRootItem()
            if root is None or not root.IsOk():
                root = self.ProjectTree.AddRoot(infos["name"])
            self.GenerateProjectTreeBranch(root, infos)
            self.ProjectTree.Expand(root)

        # Select new item corresponding to previous selected item
        if tagname is not None:
            self.SelectProjectTreeItem(tagname)

    def GenerateProjectTreeBranch(self, root, infos, item_alone=False):
        to_delete = []
        item_name = infos["name"]
        if infos["type"] in ITEMS_UNEDITABLE:
            if len(infos["values"]) == 1:
                return self.GenerateProjectTreeBranch(root, infos["values"][0], True)
            item_name = _(item_name)
        self.ProjectTree.SetItemText(root, item_name)
        self.ProjectTree.SetPyData(root, infos)
        highlight_colours = self.Highlights.get(infos.get("tagname", None), (wx.Colour(255, 255, 255, 0), wx.BLACK))
        self.ProjectTree.SetItemBackgroundColour(root, highlight_colours[0])
        self.ProjectTree.SetItemTextColour(root, highlight_colours[1])
        self.ProjectTree.SetItemExtraImage(root, None)
        if infos["type"] == ITEM_POU:
            self.ProjectTree.SetItemImage(
                root, self.TreeImageDict[self.Controler.GetPouBodyType(infos["name"])])
            if item_alone:
                self.ProjectTree.SetItemExtraImage(root, self.Controler.GetPouType(infos["name"]))
        elif "icon" in infos and infos["icon"] is not None:
            icon_name = infos["icon"]
            if icon_name not in self.TreeImageDict:
                self.TreeImageDict[icon_name] = self.TreeImageList.Add(GetBitmap(icon_name))
            self.ProjectTree.SetItemImage(root, self.TreeImageDict[icon_name])
        elif infos["type"] in self.TreeImageDict:
            self.ProjectTree.SetItemImage(root, self.TreeImageDict[infos["type"]])

        item, root_cookie = self.ProjectTree.GetFirstChild(root)
        for values in infos["values"]:
            if values["type"] not in ITEMS_UNEDITABLE or len(values["values"]) > 0:
                if item is None or not item.IsOk():
                    item = self.ProjectTree.AppendItem(root, "")
                    item, root_cookie = self.ProjectTree.GetNextChild(root, root_cookie)
                self.GenerateProjectTreeBranch(item, values)
                item, root_cookie = self.ProjectTree.GetNextChild(root, root_cookie)
        while item is not None and item.IsOk():
            to_delete.append(item)
            item, root_cookie = self.ProjectTree.GetNextChild(root, root_cookie)
        for item in to_delete:
            self.ProjectTree.Delete(item)

    TagNamePartsItemTypes = {
        "D": [ITEM_DATATYPE],
        "P": [ITEM_POU],
        "T": [ITEM_POU, ITEM_TRANSITION],
        "A": [ITEM_POU, ITEM_ACTION],
        "C": [ITEM_CONFIGURATION],
        "R": [ITEM_CONFIGURATION, ITEM_RESOURCE]}

    def SelectProjectTreeItem(self, tagname):
        result = False
        if self.ProjectTree is not None:
            root = self.ProjectTree.GetRootItem()
            if root is not None and root.IsOk():
                words = tagname.split("::")
                result = self.RecursiveProjectTreeItemSelection(
                    root, zip(words[1:], self.TagNamePartsItemTypes.get(words[0], [])))
        return result

    def RecursiveProjectTreeItemSelection(self, root, items):
        found = False
        item, root_cookie = self.ProjectTree.GetFirstChild(root)
        while item is not None and item.IsOk() and not found:
            item_infos = self.ProjectTree.GetPyData(item)
            if (item_infos["name"].split(":")[-1].strip(), item_infos["type"]) == items[0]:
                if len(items) == 1:
                    self.SelectedItem = item
                    self.ProjectTree.SelectItem(item)
                    self.ResetSelectedItem()
                    return True
                else:
                    found = self.RecursiveProjectTreeItemSelection(item, items[1:])
            else:
                found = self.RecursiveProjectTreeItemSelection(item, items)
            item, root_cookie = self.ProjectTree.GetNextChild(root, root_cookie)
        return found

    def ResetSelectedItem(self):
        self.SelectedItem = None

    def OnProjectTreeBeginDrag(self, event):
        selected_item = (self.SelectedItem
                         if self.SelectedItem is not None
                         else event.GetItem())
        if selected_item.IsOk() and self.ProjectTree.GetPyData(selected_item)["type"] == ITEM_POU:
            block_name = self.ProjectTree.GetItemText(selected_item)
            block_type = self.Controler.GetPouType(block_name)
            if block_type != "program":
                data = wx.TextDataObject(str((block_name, block_type, "")))
                dragSource = wx.DropSource(self.ProjectTree)
                dragSource.SetData(data)
                dragSource.DoDragDrop()
            self.ResetSelectedItem()

    def OnProjectTreeItemBeginEdit(self, event):
        selected = event.GetItem()
        if self.ProjectTree.GetPyData(selected)["type"] in ITEMS_UNEDITABLE:
            event.Veto()
        else:
            event.Skip()

    def OnProjectTreeItemEndEdit(self, event):
        message = None
        abort = False
        new_name = event.GetLabel()
        if new_name != "":
            if not TestIdentifier(new_name):
                message = _("\"%s\" is not a valid identifier!") % new_name
            elif new_name.upper() in IEC_KEYWORDS:
                message = _("\"%s\" is a keyword. It can't be used!") % new_name
            else:
                item = event.GetItem()
                old_name = self.ProjectTree.GetItemText(item)
                item_infos = self.ProjectTree.GetPyData(item)
                if item_infos["type"] == ITEM_PROJECT:
                    self.Controler.SetProjectProperties(name=new_name)
                elif item_infos["type"] == ITEM_DATATYPE:
                    if new_name.upper() in [name.upper() for name in self.Controler.GetProjectDataTypeNames() if name != old_name]:
                        message = _("\"%s\" data type already exists!") % new_name
                        abort = True
                    if not abort:
                        self.Controler.ChangeDataTypeName(old_name, new_name)
                        self.RefreshEditorNames(ComputeDataTypeName(old_name),
                                                ComputeDataTypeName(new_name))
                        self.RefreshPageTitles()
                elif item_infos["type"] == ITEM_POU:
                    if new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames() if name != old_name]:
                        message = _("\"%s\" pou already exists!") % new_name
                        abort = True
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouVariableNames()]:
                        messageDialog = wx.MessageDialog(self, _("A POU has an element named \"%s\". This could cause a conflict. Do you wish to continue?") % new_name, _("Error"), wx.YES_NO | wx.ICON_QUESTION)
                        if messageDialog.ShowModal() == wx.ID_NO:
                            abort = True
                        messageDialog.Destroy()
                    if not abort:
                        self.Controler.ChangePouName(old_name, new_name)
                        self.RefreshEditorNames(ComputePouName(old_name),
                                                ComputePouName(new_name))
                        self.RefreshLibraryPanel()
                        self.RefreshPageTitles()
                elif item_infos["type"] == ITEM_TRANSITION:
                    pou_item = self.ProjectTree.GetItemParent(event.GetItem())
                    pou_name = self.ProjectTree.GetItemText(pou_item)
                    if new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames()]:
                        message = _("A POU named \"%s\" already exists!") % new_name
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouVariableNames(pou_name) if name != old_name]:
                        message = _("A variable with \"%s\" as name already exists in this pou!") % new_name
                    else:
                        words = item_infos["tagname"].split("::")
                        self.Controler.ChangePouTransitionName(words[1], old_name, new_name)
                        self.RefreshEditorNames(ComputePouTransitionName(words[1], old_name),
                                                ComputePouTransitionName(words[1], new_name))
                        self.RefreshPageTitles()
                elif item_infos["type"] == ITEM_ACTION:
                    pou_item = self.ProjectTree.GetItemParent(event.GetItem())
                    pou_name = self.ProjectTree.GetItemText(pou_item)
                    if new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames()]:
                        message = _("A POU named \"%s\" already exists!") % new_name
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouVariableNames(pou_name) if name != old_name]:
                        message = _("A variable with \"%s\" as name already exists in this pou!") % new_name
                    else:
                        words = item_infos["tagname"].split("::")
                        self.Controler.ChangePouActionName(words[1], old_name, new_name)
                        self.RefreshEditorNames(ComputePouActionName(words[1], old_name),
                                                ComputePouActionName(words[1], new_name))
                        self.RefreshPageTitles()
                elif item_infos["type"] == ITEM_CONFIGURATION:
                    if new_name.upper() in [name.upper() for name in self.Controler.GetProjectConfigNames() if name != old_name]:
                        message = _("\"%s\" config already exists!") % new_name
                        abort = True
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames()]:
                        messageDialog = wx.MessageDialog(self, _("There is a POU named \"%s\". This could cause a conflict. Do you wish to continue?") % new_name, _("Error"), wx.YES_NO | wx.ICON_QUESTION)
                        if messageDialog.ShowModal() == wx.ID_NO:
                            abort = True
                        messageDialog.Destroy()
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouVariableNames()]:
                        messageDialog = wx.MessageDialog(self, _("A POU has an element named \"%s\". This could cause a conflict. Do you wish to continue?") % new_name, _("Error"), wx.YES_NO | wx.ICON_QUESTION)
                        if messageDialog.ShowModal() == wx.ID_NO:
                            abort = True
                        messageDialog.Destroy()
                    if not abort:
                        self.Controler.ChangeConfigurationName(old_name, new_name)
                        self.RefreshEditorNames(ComputeConfigurationName(old_name),
                                                ComputeConfigurationName(new_name))
                        self.RefreshPageTitles()
                elif item_infos["type"] == ITEM_RESOURCE:
                    if new_name.upper() in [name.upper() for name in self.Controler.GetProjectConfigNames()]:
                        message = _("\"%s\" config already exists!") % new_name
                        abort = True
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames()]:
                        messageDialog = wx.MessageDialog(self, _("There is a POU named \"%s\". This could cause a conflict. Do you wish to continue?") % new_name, _("Error"), wx.YES_NO | wx.ICON_QUESTION)
                        if messageDialog.ShowModal() == wx.ID_NO:
                            abort = True
                        messageDialog.Destroy()
                    elif new_name.upper() in [name.upper() for name in self.Controler.GetProjectPouVariableNames()]:
                        messageDialog = wx.MessageDialog(self, _("A POU has an element named \"%s\". This could cause a conflict. Do you wish to continue?") % new_name, _("Error"), wx.YES_NO | wx.ICON_QUESTION)
                        if messageDialog.ShowModal() == wx.ID_NO:
                            abort = True
                        messageDialog.Destroy()
                    if not abort:
                        words = item_infos["tagname"].split("::")
                        self.Controler.ChangeConfigurationResourceName(words[1], old_name, new_name)
                        self.RefreshEditorNames(ComputeConfigurationResourceName(words[1], old_name),
                                                ComputeConfigurationResourceName(words[1], new_name))
                        self.RefreshPageTitles()
            if message or abort:
                if message:
                    self.ShowErrorMessage(message)
                event.Veto()
            else:
                wx.CallAfter(self.RefreshProjectTree)
                self.RefreshEditor()
                self._Refresh(TITLE, FILEMENU, EDITMENU)
                event.Skip()

    def OnProjectTreeItemActivated(self, event):
        selected = event.GetItem()
        item_infos = self.ProjectTree.GetPyData(selected)
        if item_infos["type"] == ITEM_PROJECT:
            self.EditProjectSettings()
        else:
            if item_infos["type"] in [ITEM_DATATYPE, ITEM_POU,
                                      ITEM_CONFIGURATION, ITEM_RESOURCE,
                                      ITEM_TRANSITION, ITEM_ACTION]:
                self.EditProjectElement(item_infos["type"], item_infos["tagname"])
            event.Skip()

    def ProjectTreeItemSelect(self, select_item):
        if select_item is not None and select_item.IsOk():
            item_infos = self.ProjectTree.GetPyData(select_item)
            if item_infos["type"] in [ITEM_DATATYPE, ITEM_POU,
                                      ITEM_CONFIGURATION, ITEM_RESOURCE,
                                      ITEM_TRANSITION, ITEM_ACTION]:
                self.EditProjectElement(item_infos["type"], item_infos["tagname"], True)
                self.PouInstanceVariablesPanel.SetPouType(item_infos["tagname"])

    def OnProjectTreeLeftUp(self, event):
        if self.SelectedItem is not None:
            self.ProjectTree.SelectItem(self.SelectedItem)
            self.ProjectTreeItemSelect(self.SelectedItem)
            self.ResetSelectedItem()
        event.Skip()

    def OnProjectTreeMotion(self, event):
        if not event.Dragging():
            pt = wx.Point(event.GetX(), event.GetY())
            item, flags = self.ProjectTree.HitTest(pt)
            if item is not None and item.IsOk() and flags & wx.TREE_HITTEST_ONITEMLABEL:
                item_infos = self.ProjectTree.GetPyData(item)
                if item != self.LastToolTipItem and self.LastToolTipItem is not None:
                    self.ProjectTree.SetToolTip(None)
                    self.LastToolTipItem = None
                if self.LastToolTipItem != item and \
                   item_infos["type"] in [ITEM_POU, ITEM_TRANSITION, ITEM_ACTION]:
                    bodytype = self.Controler.GetEditedElementBodyType(
                        item_infos["tagname"])
                    if item_infos["type"] == ITEM_POU:
                        block_type = {
                            "program": _("Program"),
                            "functionBlock": _("Function Block"),
                            "function": _("Function")
                        }[self.Controler.GetPouType(item_infos["name"])]
                    elif item_infos["type"] == ITEM_TRANSITION:
                        block_type = "Transition"
                    else:
                        block_type = "Action"
                    self.LastToolTipItem = item
                    wx.CallAfter(self.ProjectTree.SetToolTipString,
                                 "%s : %s : %s" % (
                                     block_type, bodytype, item_infos["name"]))
            elif self.LastToolTipItem is not None:
                self.ProjectTree.SetToolTip(None)
                self.LastToolTipItem = None
        event.Skip()

    def OnProjectTreeItemChanging(self, event):
        if self.ProjectTree.GetPyData(event.GetItem())["type"] not in ITEMS_UNEDITABLE and self.SelectedItem is None:
            self.SelectedItem = event.GetItem()
            event.Veto()
        else:
            event.Skip()

    def GetProjectElementWindow(self, element, tagname):
        new_window = None
        if self.Controler.GetEditedElement(tagname) is not None:
            new_window = None
            if element == ITEM_CONFIGURATION:
                new_window = ConfigurationEditor(self.TabsOpened, tagname, self, self.Controler)
                new_window.SetIcon(GetBitmap("CONFIGURATION"))
            elif element == ITEM_RESOURCE:
                new_window = ResourceEditor(self.TabsOpened, tagname, self, self.Controler)
                new_window.SetIcon(GetBitmap("RESOURCE"))
            elif element in [ITEM_POU, ITEM_TRANSITION, ITEM_ACTION]:
                bodytype = self.Controler.GetEditedElementBodyType(tagname)
                if bodytype == "FBD":
                    new_window = Viewer(self.TabsOpened, tagname, self, self.Controler)
                    new_window.RefreshScaling(False)
                elif bodytype == "LD":
                    new_window = LD_Viewer(self.TabsOpened, tagname, self, self.Controler)
                    new_window.RefreshScaling(False)
                elif bodytype == "SFC":
                    new_window = SFC_Viewer(self.TabsOpened, tagname, self, self.Controler)
                    new_window.RefreshScaling(False)
                else:
                    new_window = TextViewer(self.TabsOpened, tagname, self, self.Controler)
                    new_window.SetTextSyntax(bodytype)
                    if bodytype == "IL":
                        new_window.SetKeywords(IL_KEYWORDS)
                    else:
                        new_window.SetKeywords(ST_KEYWORDS)
                if element == ITEM_POU:
                    pou_type = self.Controler.GetEditedElementType(tagname)[1].upper()
                    icon = GetBitmap(pou_type, bodytype)
                elif element == ITEM_TRANSITION:
                    icon = GetBitmap("TRANSITION", bodytype)
                elif element == ITEM_ACTION:
                    icon = GetBitmap("ACTION", bodytype)
                new_window.SetIcon(icon)
            elif element == ITEM_DATATYPE:
                new_window = DataTypeEditor(self.TabsOpened, tagname, self, self.Controler)
                new_window.SetIcon(GetBitmap("DATATYPE"))
        return new_window

    def EditProjectElement(self, element, tagname, onlyopened=False):
        openedidx = self.IsOpened(tagname)
        if openedidx is not None:
            old_selected = self.TabsOpened.GetSelection()
            if old_selected != openedidx:
                if old_selected >= 0:
                    self.TabsOpened.GetPage(old_selected).ResetBuffer()
                self.TabsOpened.SetSelection(openedidx)
            self._Refresh(FILEMENU, EDITMENU, EDITORTOOLBAR, PAGETITLES)
        elif not onlyopened:
            if isinstance(element, EditorPanel):
                new_window = element
            else:
                new_window = self.GetProjectElementWindow(element, tagname)

            if new_window is not None:
                self.AddPage(new_window, "")
                openedidx = self.IsOpened(tagname)
                old_selected = self.TabsOpened.GetSelection()
                if old_selected != openedidx:
                    if old_selected >= 0:
                        self.TabsOpened.GetPage(old_selected).ResetBuffer()
                for i in xrange(self.TabsOpened.GetPageCount()):
                    window = self.TabsOpened.GetPage(i)
                    if window == new_window:
                        self.TabsOpened.SetSelection(i)
                        window.SetFocus()
                self.RefreshPageTitles()
            return new_window

    def OnProjectTreeRightUp(self, event):
        item = event.GetItem()
        self.ProjectTree.SelectItem(item)
        self.ProjectTreeItemSelect(item)
        name = self.ProjectTree.GetItemText(item)
        item_infos = self.ProjectTree.GetPyData(item)

        menu = None
        if item_infos["type"] in ITEMS_UNEDITABLE + [ITEM_PROJECT]:
            if item_infos["type"] == ITEM_PROJECT:
                name = "Project"
            else:
                name = self.UNEDITABLE_NAMES_DICT[name]

            if name == "Data Types":
                menu = wx.Menu(title='')
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add DataType"))
                self.Bind(wx.EVT_MENU, self.OnAddDataTypeMenu, id=new_id)

            elif name in ["Functions", "Function Blocks", "Programs", "Project"]:
                menu = wx.Menu(title='')

                if name != "Project":
                    new_id = wx.NewId()
                    AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add POU"))
                    self.Bind(wx.EVT_MENU, self.GenerateAddPouFunction({"Functions": "function", "Function Blocks": "functionBlock", "Programs": "program"}[name]), id=new_id)

                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Paste POU"))
                self.Bind(wx.EVT_MENU, self.OnPastePou, id=new_id)
                if self.GetCopyBuffer() is None:
                    menu.Enable(new_id, False)

            elif name == "Configurations":
                menu = wx.Menu(title='')
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Configuration"))
                self.Bind(wx.EVT_MENU, self.OnAddConfigurationMenu, id=new_id)

            elif name == "Transitions":
                menu = wx.Menu(title='')
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Transition"))
                parent = self.ProjectTree.GetItemParent(item)
                parent_type = self.ProjectTree.GetPyData(parent)["type"]
                while parent_type != ITEM_POU:
                    parent = self.ProjectTree.GetItemParent(parent)
                    parent_type = self.ProjectTree.GetPyData(parent)["type"]
                self.Bind(wx.EVT_MENU, self.GenerateAddTransitionFunction(self.ProjectTree.GetItemText(parent)), id=new_id)

            elif name == "Actions":
                menu = wx.Menu(title='')
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Action"))
                parent = self.ProjectTree.GetItemParent(item)
                parent_type = self.ProjectTree.GetPyData(parent)["type"]
                while parent_type != ITEM_POU:
                    parent = self.ProjectTree.GetItemParent(parent)
                    parent_type = self.ProjectTree.GetPyData(parent)["type"]
                self.Bind(wx.EVT_MENU, self.GenerateAddActionFunction(self.ProjectTree.GetItemText(parent)), id=new_id)

            elif name == "Resources":
                menu = wx.Menu(title='')
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Resource"))
                parent = self.ProjectTree.GetItemParent(item)
                parent_type = self.ProjectTree.GetPyData(parent)["type"]
                while parent_type not in [ITEM_CONFIGURATION, ITEM_PROJECT]:
                    parent = self.ProjectTree.GetItemParent(parent)
                    parent_type = self.ProjectTree.GetPyData(parent)["type"]
                parent_name = None
                if parent_type == ITEM_PROJECT:
                    config_names = self.Controler.GetProjectConfigNames()
                    if len(config_names) > 0:
                        parent_name = config_names[0]
                else:
                    parent_name = self.ProjectTree.GetItemText(parent)
                if parent_name is not None:
                    self.Bind(wx.EVT_MENU, self.GenerateAddResourceFunction(parent_name), id=new_id)

        else:
            if item_infos["type"] == ITEM_POU:
                menu = wx.Menu(title='')
                if self.Controler.GetPouBodyType(name) == "SFC":
                    new_id = wx.NewId()
                    AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Transition"))
                    self.Bind(wx.EVT_MENU, self.GenerateAddTransitionFunction(name), id=new_id)
                    new_id = wx.NewId()
                    AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Action"))
                    self.Bind(wx.EVT_MENU, self.GenerateAddActionFunction(name), id=new_id)
                    menu.AppendSeparator()

                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Copy POU"))
                self.Bind(wx.EVT_MENU, self.OnCopyPou, id=new_id)

                pou_type = self.Controler.GetPouType(name)
                if pou_type in ["function", "functionBlock"]:
                    change_menu = wx.Menu(title='')
                    if pou_type == "function":
                        new_id = wx.NewId()
                        AppendMenu(change_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Function Block"))
                        self.Bind(wx.EVT_MENU, self.GenerateChangePouTypeFunction(name, "functionBlock"), id=new_id)
                    new_id = wx.NewId()
                    AppendMenu(change_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Program"))
                    self.Bind(wx.EVT_MENU, self.GenerateChangePouTypeFunction(name, "program"), id=new_id)
                    menu.AppendMenu(wx.NewId(), _("Change POU Type To"), change_menu)
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Rename"))
                self.Bind(wx.EVT_MENU, self.OnRenamePouMenu, id=new_id)

            elif item_infos["type"] == ITEM_CONFIGURATION:
                menu = wx.Menu(title='')
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Add Resource"))
                self.Bind(wx.EVT_MENU, self.GenerateAddResourceFunction(name), id=new_id)

            elif item_infos["type"] in [ITEM_DATATYPE, ITEM_TRANSITION, ITEM_ACTION, ITEM_RESOURCE]:
                menu = wx.Menu(title='')

            if menu is not None:
                new_id = wx.NewId()
                AppendMenu(menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Delete"))
                self.Bind(wx.EVT_MENU, self.OnDeleteMenu, id=new_id)

        if menu is not None:
            self.FindFocus().PopupMenu(menu)
            menu.Destroy()

        self.ResetSelectedItem()

        event.Skip()

    # -------------------------------------------------------------------------------
    #                         Instances Tree Management Functions
    # -------------------------------------------------------------------------------

    def GetTreeImage(self, var_class):
        return self.TreeImageDict[var_class]

    def RefreshPouInstanceVariablesPanel(self):
        self.PouInstanceVariablesPanel.RefreshView()

    def OpenDebugViewer(self, instance_category, instance_path, instance_type):
        openedidx = self.IsOpened(instance_path)
        new_window = None
        if openedidx is not None:
            old_selected = self.TabsOpened.GetSelection()
            if old_selected != openedidx:
                if old_selected >= 0:
                    self.TabsOpened.GetPage(old_selected).ResetBuffer()
                self.TabsOpened.SetSelection(openedidx)

        elif instance_category in ITEMS_VARIABLE:
            if self.Controler.IsNumType(instance_type, True):
                self.AddDebugVariable(instance_path, True)

        else:
            bodytype = self.Controler.GetEditedElementBodyType(instance_type, True)
            if bodytype == "FBD":
                new_window = Viewer(self.TabsOpened, instance_type, self, self.Controler, True, instance_path)
                new_window.RefreshScaling(False)
            elif bodytype == "LD":
                new_window = LD_Viewer(self.TabsOpened, instance_type, self, self.Controler, True, instance_path)
                new_window.RefreshScaling(False)
            elif bodytype == "SFC":
                new_window = SFC_Viewer(self.TabsOpened, instance_type, self, self.Controler, True, instance_path)
                new_window.RefreshScaling(False)
            else:
                new_window = TextViewer(self.TabsOpened, instance_type, self, self.Controler, True, instance_path)
                new_window.SetTextSyntax(bodytype)
                if bodytype == "IL":
                    new_window.SetKeywords(IL_KEYWORDS)
                else:
                    new_window.SetKeywords(ST_KEYWORDS)

            if new_window is not None:
                if instance_category in [ITEM_FUNCTIONBLOCK, ITEM_PROGRAM]:
                    pou_type = self.Controler.GetEditedElementType(instance_type, True)[1].upper()
                    icon = GetBitmap(pou_type, bodytype)
                elif instance_category == ITEM_TRANSITION:
                    icon = GetBitmap("TRANSITION", bodytype)
                elif instance_category == ITEM_ACTION:
                    icon = GetBitmap("ACTION", bodytype)

        if new_window is not None:
            new_window.SetIcon(icon)
            self.AddPage(new_window, "")
            new_window.RefreshView()
            new_window.SetFocus()
            self.RefreshPageTitles()
        return new_window

    def ResetGraphicViewers(self):
        if self.EnableDebug:
            self.DebugVariablePanel.ResetGraphicsValues()

    def CloseObsoleteDebugTabs(self):
        if self.EnableDebug:
            idxs = range(self.TabsOpened.GetPageCount())
            idxs.reverse()
            for idx in idxs:
                editor = self.TabsOpened.GetPage(idx)
                if isinstance(editor, Viewer) and editor.IsDebugging():
                    instance_infos = self.Controler.GetInstanceInfos(editor.GetInstancePath(), self.EnableDebug)
                    if instance_infos is None:
                        self.TabsOpened.DeletePage(idx)
                    else:
                        editor.SubscribeAllDataConsumers()
                elif editor.IsDebugging() and hasattr(editor, 'SubscribeAllDataConsumers'):
                    editor.SubscribeAllDataConsumers()
            self.DebugVariablePanel.SubscribeAllDataConsumers()

    def AddDebugVariable(self, iec_path, force=False, graph=False):
        if self.EnableDebug:
            self.DebugVariablePanel.InsertValue(iec_path, force=force, graph=graph)
            self.EnsureTabVisible(self.DebugVariablePanel)

    # -------------------------------------------------------------------------------
    #                         Library Panel Management Function
    # -------------------------------------------------------------------------------

    def RefreshLibraryPanel(self):
        self.LibraryPanel.RefreshTree()

    # -------------------------------------------------------------------------------
    #                          ToolBars Management Functions
    # -------------------------------------------------------------------------------

    def AddToMenuToolBar(self, items):
        MenuToolBar = self.Panes["MenuToolBar"]
        if MenuToolBar.GetToolsCount() > 0:
            MenuToolBar.AddSeparator()
        for toolbar_item in items:
            if toolbar_item is None:
                MenuToolBar.AddSeparator()
            else:
                id, bitmap, help, callback = toolbar_item
                MenuToolBar.AddSimpleTool(id=id, shortHelpString=help, bitmap=GetBitmap(bitmap))
                if callback is not None:
                    self.Bind(wx.EVT_TOOL, callback, id=id)
        MenuToolBar.Realize()
        self.AUIManager.GetPane("MenuToolBar").BestSize(MenuToolBar.GetBestSize())

    def ResetEditorToolBar(self):
        EditorToolBar = self.Panes["EditorToolBar"]

        for item in self.CurrentEditorToolBar:
            self.Unbind(wx.EVT_MENU, id=item)

            if EditorToolBar:
                EditorToolBar.DeleteTool(item)

        if EditorToolBar:
            EditorToolBar.Realize()
            self.AUIManager.GetPane("EditorToolBar").BestSize(EditorToolBar.GetBestSize())
            self.AUIManager.GetPane("EditorToolBar").Hide()
            self.AUIManager.Update()

    def RefreshEditorToolBar(self):
        selected = self.TabsOpened.GetSelection()
        menu = None
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            if isinstance(window, (Viewer, TextViewer)):
                if not window.IsDebugging():
                    menu = self.Controler.GetEditedElementBodyType(window.GetTagName())
                else:
                    menu = "debug"
        if menu is not None and menu != self.CurrentMenu:
            self.ResetEditorToolBar()
            self.CurrentMenu = menu
            self.CurrentEditorToolBar = []
            EditorToolBar = self.Panes["EditorToolBar"]
            if EditorToolBar:
                for radio, modes, id, method, picture, help in self.EditorToolBarItems[menu]:
                    if modes & self.DrawingMode:
                        if radio or self.DrawingMode == FREEDRAWING_MODE:
                            EditorToolBar.AddRadioTool(id, GetBitmap(picture), wx.NullBitmap, help)
                        else:
                            EditorToolBar.AddSimpleTool(id, GetBitmap(picture), help)
                        self.Bind(wx.EVT_MENU, getattr(self, method), id=id)
                        self.CurrentEditorToolBar.append(id)
                EditorToolBar.Realize()
                self.AUIManager.GetPane("EditorToolBar").Show()
                self.AUIManager.Update()
                self.AUIManager.GetPane("EditorToolBar").BestSize(EditorToolBar.GetBestSize())
                self.AUIManager.Update()
        elif menu is None:
            self.ResetEditorToolBar()
            self.CurrentMenu = menu
        self.ResetCurrentMode()

    # -------------------------------------------------------------------------------
    #                           EditorToolBar Items Functions
    # -------------------------------------------------------------------------------

    def ResetCurrentMode(self):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            window.SetMode(MODE_SELECTION)
        EditorToolBar = self.Panes["EditorToolBar"]
        if EditorToolBar:
            EditorToolBar.ToggleTool(ID_PLCOPENEDITOREDITORTOOLBARSELECTION, False)
            EditorToolBar.ToggleTool(ID_PLCOPENEDITOREDITORTOOLBARSELECTION, True)

    def ResetToolToggle(self, id):
        tool = self.Panes["EditorToolBar"].FindById(id)
        tool.SetToggle(False)

    def OnSelectionTool(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_SELECTION)

    def OnMotionTool(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_MOTION)

    def OnCommentTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARCOMMENT)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_COMMENT)

    def OnVariableTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARVARIABLE)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_VARIABLE)

    def OnBlockTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARBLOCK)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_BLOCK)

    def OnConnectionTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARCONNECTION)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_CONNECTION)

    def OnPowerRailTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARPOWERRAIL)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_POWERRAIL)

    def OnRungTool(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).AddLadderRung()
        event.Skip()

    def OnCoilTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARCOIL)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_COIL)
        event.Skip()

    def OnContactTool(self, event):
        if self.DrawingMode == FREEDRAWING_MODE:
            self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARCONTACT)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            if self.DrawingMode == FREEDRAWING_MODE:
                self.TabsOpened.GetPage(selected).SetMode(MODE_CONTACT)
            else:
                self.TabsOpened.GetPage(selected).AddLadderContact()

    def OnBranchTool(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).AddLadderBranch()

    def OnInitialStepTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARINITIALSTEP)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_INITIALSTEP)

    def OnStepTool(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARSTEP)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            if self.GetDrawingMode() == FREEDRAWING_MODE:
                self.TabsOpened.GetPage(selected).SetMode(MODE_STEP)
            else:
                self.TabsOpened.GetPage(selected).AddStep()

    def OnActionBlockTool(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARACTIONBLOCK)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            if self.GetDrawingMode() == FREEDRAWING_MODE:
                self.TabsOpened.GetPage(selected).SetMode(MODE_ACTION)
            else:
                self.TabsOpened.GetPage(selected).AddStepAction()

    def OnTransitionTool(self, event):
        self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARTRANSITION)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            self.TabsOpened.GetPage(selected).SetMode(MODE_TRANSITION)

    def OnDivergenceTool(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARDIVERGENCE)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            if self.GetDrawingMode() == FREEDRAWING_MODE:
                self.TabsOpened.GetPage(selected).SetMode(MODE_DIVERGENCE)
            else:
                self.TabsOpened.GetPage(selected).AddDivergence()

    def OnJumpTool(self, event):
        if self.GetDrawingMode() == FREEDRAWING_MODE:
            self.ResetToolToggle(ID_PLCOPENEDITOREDITORTOOLBARJUMP)
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            if self.GetDrawingMode() == FREEDRAWING_MODE:
                self.TabsOpened.GetPage(selected).SetMode(MODE_JUMP)
            else:
                self.TabsOpened.GetPage(selected).AddJump()

    # -------------------------------------------------------------------------------
    #                         Add Project Elements Functions
    # -------------------------------------------------------------------------------

    def OnAddNewProject(self, event):
        # Asks user to create main program after creating new project
        AddProgramDialog = self.GenerateAddPouFunction('program', True)
        # Checks that user created main program
        if AddProgramDialog(event):
            self.Controler.SetProjectDefaultConfiguration()

    def OnAddDataTypeMenu(self, event):
        tagname = self.Controler.ProjectAddDataType()
        if tagname is not None:
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE)
            self.EditProjectElement(ITEM_DATATYPE, tagname)

    def GenerateAddPouFunction(self, pou_type, type_readonly=False):
        def OnAddPouMenu(event):
            dialog = PouDialog(self, pou_type, type_readonly)
            dialog.SetPouNames(self.Controler.GetProjectPouNames())
            dialog.SetPouElementNames(self.Controler.GetProjectPouVariableNames())
            dialog.SetValues({"pouName": self.Controler.GenerateNewName(None, None, "%s%%d" % pou_type)})
            pou_created = False
            if dialog.ShowModal() == wx.ID_OK:
                values = dialog.GetValues()
                tagname = self.Controler.ProjectAddPou(values["pouName"], values["pouType"], values["language"])
                if tagname is not None:
                    self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, LIBRARYTREE)
                    self.EditProjectElement(ITEM_POU, tagname)
                    dialog.Destroy()
                    pou_created = True
            dialog.Destroy()
            return pou_created
        return OnAddPouMenu

    def GenerateAddTransitionFunction(self, pou_name):
        def OnAddTransitionMenu(event):
            dialog = PouTransitionDialog(self)
            dialog.SetPouNames(self.Controler.GetProjectPouNames())
            dialog.SetPouElementNames(self.Controler.GetProjectPouVariableNames(pou_name))
            dialog.SetValues({"transitionName": self.Controler.GenerateNewName(None, None, "transition%d")})
            if dialog.ShowModal() == wx.ID_OK:
                values = dialog.GetValues()
                tagname = self.Controler.ProjectAddPouTransition(pou_name, values["transitionName"], values["language"])
                if tagname is not None:
                    self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE)
                    self.EditProjectElement(ITEM_TRANSITION, tagname)
            dialog.Destroy()
        return OnAddTransitionMenu

    def GenerateAddActionFunction(self, pou_name):
        def OnAddActionMenu(event):
            dialog = PouActionDialog(self)
            dialog.SetPouNames(self.Controler.GetProjectPouNames())
            dialog.SetPouElementNames(self.Controler.GetProjectPouVariableNames(pou_name))
            dialog.SetValues({"actionName": self.Controler.GenerateNewName(None, None, "action%d")})
            if dialog.ShowModal() == wx.ID_OK:
                values = dialog.GetValues()
                tagname = self.Controler.ProjectAddPouAction(pou_name, values["actionName"], values["language"])
                if tagname is not None:
                    self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE)
                    self.EditProjectElement(ITEM_ACTION, tagname)
            dialog.Destroy()
        return OnAddActionMenu

    def OnAddConfigurationMenu(self, event):
        tagname = self.Controler.ProjectAddConfiguration()
        if tagname is not None:
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL)
            self.EditProjectElement(ITEM_CONFIGURATION, tagname)

    def AddResourceMenu(self, event):
        config_names = self.Controler.GetProjectConfigNames()
        if len(config_names) > 0:
            tagname = self.Controler.ProjectAddConfigurationResource(config_names[0])
            if tagname is not None:
                self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL)
                self.EditProjectElement(ITEM_RESOURCE, tagname)

    def GenerateAddResourceFunction(self, config_name):
        def OnAddResourceMenu(event):
            tagname = self.Controler.ProjectAddConfigurationResource(config_name)
            if tagname is not None:
                self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL)
                self.EditProjectElement(ITEM_RESOURCE, tagname)
        return OnAddResourceMenu

    def GenerateChangePouTypeFunction(self, name, new_type):
        def OnChangePouTypeMenu(event):
            selected = self.ProjectTree.GetSelection()
            if self.ProjectTree.GetPyData(selected)["type"] == ITEM_POU:
                self.Controler.ProjectChangePouType(name, new_type)
                self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, PROJECTTREE, LIBRARYTREE)
        return OnChangePouTypeMenu

    def OnCopyPou(self, event):
        selected = self.ProjectTree.GetSelection()
        pou_name = self.ProjectTree.GetItemText(selected)

        pou_xml = self.Controler.GetPouXml(pou_name)
        if pou_xml is not None:
            self.SetCopyBuffer(pou_xml)
            self._Refresh(EDITMENU)

    def OnPastePou(self, event):
        selected = self.ProjectTree.GetSelection()

        if self.ProjectTree.GetPyData(selected)["type"] != ITEM_PROJECT:
            pou_type = self.ProjectTree.GetItemText(selected)
            pou_type = self.UNEDITABLE_NAMES_DICT[pou_type]  # one of 'Functions', 'Function Blocks' or 'Programs'
            pou_type = {'Functions': 'function', 'Function Blocks': 'functionBlock', 'Programs': 'program'}[pou_type]
        else:
            pou_type = None

        pou_xml = self.GetCopyBuffer()

        result = self.Controler.PastePou(pou_type, pou_xml)

        if not isinstance(result, tuple):
            self.ShowErrorMessage(result)
        else:
            self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, PROJECTTREE, LIBRARYTREE)
            self.EditProjectElement(ITEM_POU, result[0])

    # -------------------------------------------------------------------------------
    #                        Remove Project Elements Functions
    # -------------------------------------------------------------------------------

    def CheckElementIsUsedBeforeDeletion(self, check_function, title, name):
        if not check_function(name):
            return True

        dialog = wx.MessageDialog(
            self,
            _("\"%s\" is used by one or more POUs. Do you wish to continue?") % name,
            title, wx.YES_NO | wx.ICON_QUESTION)
        answer = dialog.ShowModal()
        dialog.Destroy()
        return answer == wx.ID_YES

    def CheckDataTypeIsUsedBeforeDeletion(self, name):
        return self.CheckElementIsUsedBeforeDeletion(
            self.Controler.DataTypeIsUsed,
            _("Remove Datatype"), name)

    def CheckPouIsUsedBeforeDeletion(self, name):
        return self.CheckElementIsUsedBeforeDeletion(
            self.Controler.PouIsUsed,
            _("Remove Pou"), name)

    def OnRemoveDataTypeMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        if self.ProjectTree.GetPyData(selected)["type"] == ITEM_DATATYPE:
            name = self.ProjectTree.GetItemText(selected)
            if self.CheckDataTypeIsUsedBeforeDeletion(name):
                self.Controler.ProjectRemoveDataType(name)
                tagname = ComputeDataTypeName(name)
                idx = self.IsOpened(tagname)
                if idx is not None:
                    self.TabsOpened.DeletePage(idx)
                self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, PROJECTTREE)

    def OnRenamePouMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        if self.ProjectTree.GetPyData(selected)["type"] == ITEM_POU:
            wx.CallAfter(self.ProjectTree.EditLabel, selected)

    def OnRemovePouMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        if self.ProjectTree.GetPyData(selected)["type"] == ITEM_POU:
            name = self.ProjectTree.GetItemText(selected)
            if self.CheckPouIsUsedBeforeDeletion(name):
                self.Controler.ProjectRemovePou(name)
                tagname = ComputePouName(name)
                idx = self.IsOpened(tagname)
                if idx is not None:
                    self.TabsOpened.DeletePage(idx)
                self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)

    def OnRemoveTransitionMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        item_infos = self.ProjectTree.GetPyData(selected)
        if item_infos["type"] == ITEM_TRANSITION:
            transition = self.ProjectTree.GetItemText(selected)
            pou_name = item_infos["tagname"].split("::")[1]
            self.Controler.ProjectRemovePouTransition(pou_name, transition)
            tagname = ComputePouTransitionName(pou_name, transition)
            idx = self.IsOpened(tagname)
            if idx is not None:
                self.TabsOpened.DeletePage(idx)
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE)

    def OnRemoveActionMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        item_infos = self.ProjectTree.GetPyData(selected)
        if item_infos["type"] == ITEM_ACTION:
            action = self.ProjectTree.GetItemText(selected)
            pou_name = item_infos["tagname"].split("::")[1]
            self.Controler.ProjectRemovePouAction(pou_name, action)
            tagname = ComputePouActionName(pou_name, action)
            idx = self.IsOpened(tagname)
            if idx is not None:
                self.TabsOpened.DeletePage(idx)
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE)

    def OnRemoveConfigurationMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        if self.ProjectTree.GetPyData(selected)["type"] == ITEM_CONFIGURATION:
            name = self.ProjectTree.GetItemText(selected)
            self.Controler.ProjectRemoveConfiguration(name)
            tagname = ComputeConfigurationName(name)
            idx = self.IsOpened(tagname)
            if idx is not None:
                self.TabsOpened.DeletePage(idx)
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL)

    def OnRemoveResourceMenu(self, event):
        selected = self.ProjectTree.GetSelection()
        item_infos = self.ProjectTree.GetPyData(selected)
        if item_infos["type"] == ITEM_RESOURCE:
            resource = self.ProjectTree.GetItemText(selected)
            config_name = item_infos["tagname"].split("::")[1]
            self.Controler.ProjectRemoveConfigurationResource(config_name, resource)
            tagname = ComputeConfigurationResourceName(config_name, selected)
            idx = self.IsOpened(tagname)
            if idx is not None:
                self.TabsOpened.DeletePage(idx)
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL)

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def ShowHighlight(self, infos, start, end, highlight_type):
        self.SelectProjectTreeItem(infos[0])
        if infos[1] == "name":
            self.Highlights[infos[0]] = highlight_type
            self.RefreshProjectTree()
            self.ProjectTree.Unselect()
        else:
            self.EditProjectElement(GetElementType(infos[0]), infos[0])
            selected = self.TabsOpened.GetSelection()
            if selected != -1:
                viewer = self.TabsOpened.GetPage(selected)
                viewer.AddHighlight(infos[1:], start, end, highlight_type)

    def ShowError(self, infos, start, end):
        self.ShowHighlight(infos, start, end, ERROR_HIGHLIGHT)

    def ShowSearchResult(self, infos, start, end):
        self.ShowHighlight(infos, start, end, SEARCH_RESULT_HIGHLIGHT)

    def ClearHighlights(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = {}
        else:
            self.Highlights = dict([(name, highlight) for name, highlight in self.Highlights.iteritems() if highlight != highlight_type])
        self.RefreshProjectTree()
        for i in xrange(self.TabsOpened.GetPageCount()):
            viewer = self.TabsOpened.GetPage(i)
            viewer.ClearHighlights(highlight_type)

    def ClearErrors(self):
        self.ClearHighlights(ERROR_HIGHLIGHT)

    def ClearSearchResults(self):
        self.ClearHighlights(SEARCH_RESULT_HIGHLIGHT)

# -------------------------------------------------------------------------------
#                               Viewer Printout
# -------------------------------------------------------------------------------


def UPPER_DIV(x, y):
    return (x // y) + {True: 0, False: 1}[(x % y) == 0]


class GraphicPrintout(wx.Printout):
    def __init__(self, viewer, page_size, margins, preview=False):
        wx.Printout.__init__(self)
        self.Viewer = viewer
        self.PageSize = page_size
        if self.PageSize[0] == 0 or self.PageSize[1] == 0:
            self.PageSize = (1050, 1485)
        self.Preview = preview
        self.Margins = margins
        self.FontSize = 5
        self.TextMargin = 3

        maxx, maxy = viewer.GetMaxSize()
        self.PageGrid = (UPPER_DIV(maxx, self.PageSize[0]),
                         UPPER_DIV(maxy, self.PageSize[1]))

    def GetPageNumber(self):
        return self.PageGrid[0] * self.PageGrid[1]

    def HasPage(self, page):
        return page <= self.GetPageNumber()

    def GetPageInfo(self):
        page_number = self.GetPageNumber()
        return (1, page_number, 1, page_number)

    def OnBeginDocument(self, startPage, endPage):
        dc = self.GetDC()
        if not self.Preview and isinstance(dc, wx.PostScriptDC):
            dc.SetResolution(720)
        super(GraphicPrintout, self).OnBeginDocument(startPage, endPage)

    def OnPrintPage(self, page):
        dc = self.GetDC()
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        dc.SetUserScale(1.0, 1.0)
        dc.SetDeviceOrigin(0, 0)
        dc.printing = not self.Preview

        # Get the size of the DC in pixels
        ppiPrinterX, ppiPrinterY = self.GetPPIPrinter()
        pw, ph = self.GetPageSizePixels()
        dw, dh = dc.GetSizeTuple()
        Xscale = (dw * ppiPrinterX) / (pw * 25.4)
        Yscale = (dh * ppiPrinterY) / (ph * 25.4)

        fontsize = self.FontSize * Yscale

        margin_left = self.Margins[0].x * Xscale
        margin_top = self.Margins[0].y * Yscale
        area_width = dw - self.Margins[1].x * Xscale - margin_left
        area_height = dh - self.Margins[1].y * Yscale - margin_top

        dc.SetPen(MiterPen(wx.BLACK))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(margin_left, margin_top, area_width, area_height)

        dc.SetFont(wx.Font(fontsize, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        dc.SetTextForeground(wx.BLACK)
        block_name = " - ".join(self.Viewer.GetTagName().split("::")[1:])
        _text_width, text_height = dc.GetTextExtent(block_name)
        dc.DrawText(block_name, margin_left, margin_top - text_height - self.TextMargin)
        dc.DrawText(_("Page: %d") % page, margin_left, margin_top + area_height + self.TextMargin)

        # Calculate the position on the DC for centering the graphic
        posX = area_width * ((page - 1) % self.PageGrid[0])
        posY = area_height * ((page - 1) // self.PageGrid[0])

        scaleX = area_width / self.PageSize[0]
        scaleY = area_height / self.PageSize[1]
        scale = min(scaleX, scaleY)

        # Set the scale and origin
        dc.SetDeviceOrigin(-posX + margin_left, -posY + margin_top)
        dc.SetClippingRegion(posX, posY, self.PageSize[0] * scale, self.PageSize[1] * scale)
        dc.SetUserScale(scale, scale)

        self.Viewer.DoDrawing(dc, True)

        return True
