#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2016: Andrey Skvortsov <andrej.skvortzov@gmail.com>
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


import os
import pickle
import sys
import shutil
import time
import signal
from time import time as gettime
from threading import Lock, Timer, current_thread
import platform as os_platform

import wx.lib.buttons
import wx.lib.statbmp
import wx.stc
import wx.adv


import version
from editors.EditorPanel import EditorPanel
from editors.Viewer import Viewer
from editors.TextViewer import TextViewer
from editors.ResourceEditor import ConfigurationEditor, ResourceEditor
from editors.DataTypeEditor import DataTypeEditor
from util.paths import Bpath
from util.MiniTextControler import MiniTextControler
from util.BitmapLibrary import GetBitmap
from controls.LogViewer import LogViewer
from controls.CustomStyledTextCtrl import CustomStyledTextCtrl
from controls import EnhancedStatusBar as esb
from dialogs.AboutDialog import ShowAboutDialog

from plcopen.types_enums import \
    ComputeConfigurationName, \
    LOCATION_CONFNODE, \
    LOCATION_MODULE, \
    LOCATION_GROUP, \
    LOCATION_VAR_INPUT, \
    LOCATION_VAR_OUTPUT, \
    LOCATION_VAR_MEMORY, \
    ITEM_PROJECT, \
    ITEM_RESOURCE, \
    ITEM_CONFNODE

from ProjectController import ProjectController, GetAddMenuItems, MATIEC_ERROR_MODEL

from IDEFrame import \
    TITLE,\
    EDITORTOOLBAR,\
    FILEMENU,\
    EDITMENU,\
    DISPLAYMENU,\
    PROJECTTREE,\
    POUINSTANCEVARIABLESPANEL,\
    LIBRARYTREE,\
    PAGETITLES,\
    IDEFrame, \
    EncodeFileSystemPath, \
    DecodeFileSystemPath

from LocalRuntimeMixin import LocalRuntimeMixin

# Define OpenPLC Editor FileMenu extra items id
[
    ID_OPENPLCFILEMENUUPDATE
] = [wx.NewId() for _init_coll_FileMenu_Items in range(1)]


def AppendMenu(parent, help, id, kind, text):
    return parent.Append(wx.MenuItem(helpString=help, id=id, kind=kind, text=text))

MAX_RECENT_PROJECTS = 9


if wx.Platform == '__WXMSW__':
    faces = {
        'mono': 'Courier New',
        'size': 8,
    }
else:
    faces = {
        'mono': 'FreeMono',
        'size': 10,
    }


MainThread = current_thread().ident
REFRESH_PERIOD = 0.1


class LogPseudoFile(object):
    """ Base class for file like objects to facilitate StdOut for the Shell."""
    def __init__(self, output, risecall, logf):
        self.red_white = 1
        self.red_yellow = 2
        self.black_white = wx.stc.STC_STYLE_DEFAULT
        self.output = output
        self.risecall = risecall
        # to prevent rapid fire on rising log panel
        self.rising_timer = 0
        self.StackLock = Lock()
        self.YieldLock = Lock()
        self.RefreshLock = Lock()
        self.TimerAccessLock = Lock()
        self.stack = []
        self.LastRefreshTime = gettime()
        self.LastRefreshTimer = None
        self.refreshPending = False
        self.logf = logf

    def write(self, s, style=None):
        if self.logf is not None:
            self.logf.write(s)
            self.logf.flush()
        self.StackLock.acquire()
        self.stack.append((s, style))
        self.StackLock.release()
        current_time = gettime()
        with self.TimerAccessLock:
            if self.LastRefreshTimer is not None:
                self.LastRefreshTimer.cancel()
                self.LastRefreshTimer = None
        elapsed = current_time - self.LastRefreshTime
        if elapsed > REFRESH_PERIOD:
            self._should_write()
        else:
            with self.TimerAccessLock:
                if self.LastRefreshTimer is None:
                    self.LastRefreshTimer = Timer(REFRESH_PERIOD - elapsed, self._timer_expired)
                    self.LastRefreshTimer.start()

    def _timer_expired(self):
        self._should_write()
        with self.TimerAccessLock:
            self.LastRefreshTimer = None

    def _should_write(self):
        if MainThread == current_thread().ident:
            app = wx.GetApp()
            if app is not None:
                self._write()
                if self.YieldLock.acquire(0):
                    app.Yield()
                    self.YieldLock.release()
        else:
            with self.RefreshLock:
                if not self.refreshPending:
                    self.refreshPending = True
                    wx.CallAfter(self._write)

    def _write(self):
        if self.output:
            with self.RefreshLock:
                self.output.Freeze()
                self.output.AnnotationClearAll()
                self.StackLock.acquire()
                for s, style in self.stack:
                    if style is None:
                        style = self.black_white
                    if style != self.black_white:
                        self.output.StartStyling(self.output.GetLength())

                    # Temporary deactivate read only mode on StyledTextCtrl for
                    # adding text. It seems that text modifications, even
                    # programmatically, are disabled in StyledTextCtrl when read
                    # only is active
                    start_pos = self.output.GetLength()
                    self.output.SetReadOnly(False)
                    self.output.AppendText(s)
                    self.output.SetReadOnly(True)
                    text_len = self.output.GetLength() - start_pos

                    if style != self.black_white:
                        self.output.SetStyling(text_len, style)
                self.stack = []
                self.StackLock.release()
                self.output.ScrollToEnd()
                self.output.Thaw()
                self.LastRefreshTime = gettime()
                newtime = time.time()
                if newtime - self.rising_timer > 1:
                    self.risecall(self.output)
                self.rising_timer = newtime
                self.refreshPending = False


    def write_warning(self, s):
        self.write(s, self.red_white)

    def write_error(self, s):
        self.write(s, self.red_yellow)

    def flush(self):
        # Temporary deactivate read only mode on StyledTextCtrl for clearing
        # text. It seems that text modifications, even programmatically, are
        # disabled in StyledTextCtrl when read only is active
        self.output.SetReadOnly(False)
        self.output.SetText("")
        self.output.SetReadOnly(True)

    def isatty(self):
        return False

    def progress(self, text):
        l = max(self.output.GetLineCount()-2, 0)
        self.output.AnnotationSetText(l, text)
        self.output.AnnotationSetVisible(wx.stc.STC_ANNOTATION_BOXED)
        self.output.AnnotationSetStyle(l, self.black_white)
        if self.YieldLock.acquire(0):
            app = wx.GetApp()
            app.Yield()
            self.YieldLock.release()


ID_FILEMENURECENTPROJECTS = wx.NewIdRef()


class Beremiz(IDEFrame, LocalRuntimeMixin):

    def _init_utils(self):
        self.ConfNodeMenu = wx.Menu(title='')
        self.RecentProjectsMenu = wx.Menu(title='')
        self.TutorialsProjectsMenu = wx.Menu(title='')

        IDEFrame._init_utils(self)

    def _init_coll_FileMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_NEW,
                   kind=wx.ITEM_NORMAL, text=_('New') + '\tCTRL+N')
        AppendMenu(parent, help='', id=wx.ID_OPEN,
                   kind=wx.ITEM_NORMAL, text=_('Open') + '\tCTRL+O')
        self.RecentProjectsMenuItem = parent.AppendSubMenu(self.RecentProjectsMenu, _("&Recent Projects"))
        parent.AppendSeparator()
        parent.AppendSubMenu(self.TutorialsProjectsMenu, _("&Tutorials and Examples"))

        examples_dir = Bpath("examples")
        project_list = sorted(os.listdir(examples_dir))

        for idx, dirname  in enumerate(project_list):
            text = '&%d: %s' % (idx + 1, dirname)

            item = self.TutorialsProjectsMenu.Append(wx.ID_ANY, text, '')

            projectpath = os.path.join(examples_dir, dirname)

            def OpenExemple(event, projectpath=projectpath):
                if self.CTR is not None and not self.CheckSaveBeforeClosing():
                    return

                self.OpenProject(projectpath)
                if not self.CTR.CheckProjectPathPerm():
                    self.ResetView()

            self.Bind(wx.EVT_MENU, OpenExemple, item)
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_SAVE,
                   kind=wx.ITEM_NORMAL, text=_('Save') + '\tCTRL+S')
        AppendMenu(parent, help='', id=wx.ID_SAVEAS,
                   kind=wx.ITEM_NORMAL, text=_('Save as') + '\tCTRL+SHIFT+S')
        AppendMenu(parent, help='', id=wx.ID_CLOSE,
                   kind=wx.ITEM_NORMAL, text=_('Close Tab') + '\tCTRL+W')
        AppendMenu(parent, help='', id=wx.ID_CLOSE_ALL,
                   kind=wx.ITEM_NORMAL, text=_('Close Project') + '\tCTRL+SHIFT+W')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_PAGE_SETUP,
                   kind=wx.ITEM_NORMAL, text=_('Page Setup') + '\tCTRL+ALT+P')
        AppendMenu(parent, help='', id=wx.ID_PREVIEW,
                   kind=wx.ITEM_NORMAL, text=_('Preview') + '\tCTRL+SHIFT+P')
        AppendMenu(parent, help='', id=wx.ID_PRINT,
                   kind=wx.ITEM_NORMAL, text=_('Print') + '\tCTRL+P')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=ID_OPENPLCFILEMENUUPDATE,
                   kind=wx.ITEM_NORMAL, text=_(u'Check for updates...') + '\tCTRL+U')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_EXIT,
                   kind=wx.ITEM_NORMAL, text=_('Quit') + '\tCTRL+Q')

        self.Bind(wx.EVT_MENU, self.OnNewProjectMenu, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenProjectMenu, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectMenu, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectAsMenu, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnCloseTabMenu, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.OnCloseProjectMenu, id=wx.ID_CLOSE_ALL)
        self.Bind(wx.EVT_MENU, self.OnPageSetupMenu, id=wx.ID_PAGE_SETUP)
        self.Bind(wx.EVT_MENU, self.OnPreviewMenu, id=wx.ID_PREVIEW)
        self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=wx.ID_PRINT)
        self.Bind(wx.EVT_MENU, self.OnUpdateMenu, id=ID_OPENPLCFILEMENUUPDATE)
        self.Bind(wx.EVT_MENU, self.OnQuitMenu, id=wx.ID_EXIT)

        self.AddToMenuToolBar([(wx.ID_NEW, "new", _('New'), None),
                               (wx.ID_OPEN, "open", _('Open'), None),
                               (wx.ID_SAVE, "save", _('Save'), None),
                               (wx.ID_SAVEAS, "saveas", _('Save As...'), None),
                               (wx.ID_PRINT, "print", _('Print'), None)])

    def _RecursiveAddMenuItems(self, menu, items):
        for name, text, helpstr, children in items:
            if len(children) > 0:
                new_menu = wx.Menu(title='')
                menu.AppendSubMenu(new_menu, text)
                self._RecursiveAddMenuItems(new_menu, children)
            else:
                item = menu.Append(wx.MenuItem(text=text, helpString=helpstr, kind=wx.ITEM_NORMAL, id=wx.ID_ANY))
                self.Bind(wx.EVT_MENU, self.GetAddConfNodeFunction(name), item)

    def _init_coll_AddMenu_Items(self, parent):
        IDEFrame._init_coll_AddMenu_Items(self, parent, False)
        self._RecursiveAddMenuItems(parent, GetAddMenuItems())

    def _init_coll_HelpMenu_Items(self, parent):
        def handler(event):
            return wx.MessageBox(
                version.GetCommunityHelpMsg(),
                _('Community support'),
                wx.OK | wx.ICON_INFORMATION)

        item = parent.Append(wx.ID_ANY, _('Community support'), '')
        self.Bind(wx.EVT_MENU, handler, item)

        parent.Append(wx.MenuItem(helpString='', id=wx.ID_ABOUT,
                      kind=wx.ITEM_NORMAL, text=_('About')))
        self.Bind(wx.EVT_MENU, self.OnAboutMenu, id=wx.ID_ABOUT)

    def _init_coll_ConnectionStatusBar_Fields(self, parent):
        parent.SetFieldsCount(3)

        parent.SetStatusText(i=0, text='')
        parent.SetStatusText(i=1, text='')
        parent.SetStatusText(i=2, text='')

        parent.SetStatusWidths([-1, 300, 200])

    def _init_ctrls(self, prnt):
        IDEFrame._init_ctrls(self, prnt)

        self.EditMenuSize = self.EditMenu.GetMenuItemCount()

        inspectorID = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self.OnOpenWidgetInspector, id=inspectorID)
        accels = [wx.AcceleratorEntry(wx.ACCEL_CTRL | wx.ACCEL_ALT, ord('I'), inspectorID)]

        self.methodLock = Lock()

        for method, shortcut in [("Stop",     wx.WXK_F4),
                                 ("Run",      wx.WXK_F5),
                                 ("Transfer", wx.WXK_F6),
                                 ("Connect",  wx.WXK_F7),
                                 ("Clean",    wx.WXK_F9),
                                 ("Build",    wx.WXK_F11)]:
            def OnMethodGen(obj, meth):
                def OnMethod(evt):
                    if obj.CTR is not None:
                        if obj.methodLock.acquire(False):
                            obj.CTR.CallMethod('_'+meth)
                            obj.methodLock.release()
                            wx.CallAfter(obj.RefreshStatusToolBar)
                        else:
                            # Postpone call if one of method already running
                            # can happen because of long method using log, 
                            # itself calling wx.Yield
                            wx.CallLater(50, OnMethod, evt)
                return OnMethod
            newid = wx.NewIdRef()
            self.Bind(wx.EVT_MENU, OnMethodGen(self, method), id=newid)
            accels += [wx.AcceleratorEntry(wx.ACCEL_NORMAL, shortcut, newid)]

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

        self.LogConsole = CustomStyledTextCtrl(
            name='LogConsole', parent=self.BottomNoteBook, pos=wx.Point(0, 0),
            size=wx.Size(0, 0))
        self.LogConsole.Bind(wx.EVT_SET_FOCUS, self.OnLogConsoleFocusChanged)
        self.LogConsole.Bind(wx.EVT_KILL_FOCUS, self.OnLogConsoleFocusChanged)
        self.LogConsole.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnLogConsoleUpdateUI)
        self.LogConsole.SetReadOnly(True)
        self.LogConsole.SetWrapMode(wx.stc.STC_WRAP_CHAR)

        # Define Log Console styles
        self.LogConsole.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "face:%(mono)s,size:%(size)d" % faces)
        self.LogConsole.StyleClearAll()
        self.LogConsole.StyleSetSpec(1, "face:%(mono)s,fore:#FF0000,size:%(size)d" % faces)
        self.LogConsole.StyleSetSpec(2, "face:%(mono)s,fore:#FF0000,back:#FFFF00,size:%(size)d" % faces)

        # Define Log Console markers
        self.LogConsole.SetMarginSensitive(1, True)
        self.LogConsole.SetMarginType(1, wx.stc.STC_MARGIN_SYMBOL)
        self.LogConsole.MarkerDefine(0, wx.stc.STC_MARK_CIRCLE, "BLACK", "RED")

        self.LogConsole.SetModEventMask(wx.stc.STC_MOD_INSERTTEXT)
        self.LogConsole.SetCaretPeriod(0)

        self.LogConsole.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnLogConsoleMarginClick)
        self.LogConsole.Bind(wx.stc.EVT_STC_MODIFIED, self.OnLogConsoleModified)

        self.MainTabs["LogConsole"] = (self.LogConsole, _("Console"))
        self.BottomNoteBook.AddPage(*self.MainTabs["LogConsole"])
        # self.BottomNoteBook.Split(self.BottomNoteBook.GetPageIndex(self.LogConsole), wx.RIGHT)

        self.LogViewer = LogViewer(self.BottomNoteBook, self)
        self.MainTabs["LogViewer"] = (self.LogViewer, _("PLC Log"))
        self.BottomNoteBook.AddPage(*self.MainTabs["LogViewer"])
        # self.BottomNoteBook.Split(self.BottomNoteBook.GetPageIndex(self.LogViewer), wx.RIGHT)

        StatusToolBar = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                                   wx.TB_FLAT | wx.TB_HORIZONTAL | wx.NO_BORDER)
        StatusToolBar.SetToolBitmapSize(wx.Size(25, 25))
        StatusToolBar.Realize()
        self.Panes["StatusToolBar"] = StatusToolBar
        self.AUIManager.AddPane(StatusToolBar, wx.aui.AuiPaneInfo().
                                Name("StatusToolBar").Caption(_("Status ToolBar")).
                                ToolbarPane().Top().Position(1).
                                LeftDockable(False).RightDockable(False))

        self.AUIManager.Update()

        self.ConnectionStatusBar = esb.EnhancedStatusBar(self, style=wx.STB_SIZEGRIP)
        self._init_coll_ConnectionStatusBar_Fields(self.ConnectionStatusBar)
        self.ProgressStatusBar = wx.Gauge(self.ConnectionStatusBar, -1, range=100)
        self.ConnectionStatusBar.AddWidget(self.ProgressStatusBar, esb.ESB_EXACT_FIT, esb.ESB_EXACT_FIT, 2)
        self.ProgressStatusBar.Hide()
        self.SetStatusBar(self.ConnectionStatusBar)

    def __init_execute_path(self):
        if os.name == 'nt':
            # on windows, desktop shortcut launches Beremiz.py
            # with working dir set to mingw/bin.
            # then we prefix CWD to PATH in order to ensure that
            # commands invoked by build process by default are
            # found here.
            #os.environ["PATH"] = os.getcwd()+';'+os.environ["PATH"]
            os.environ["PATH"] = os.getcwd()+'\\mingw\\bin;'+os.environ["PATH"]

    def __init__(self, parent, projectOpen=None, buildpath=None, ctr=None, debug=True, logf=None):

        # Add beremiz's icon in top left corner of the frame
        if os_platform.system() == 'Windows':
            self.icon = wx.Icon(Bpath("images", "brz.ico"), wx.BITMAP_TYPE_ICO)
        elif os_platform.system() == 'Darwin':
            self.icon = wx.Icon(Bpath("images", "brz.ico"), wx.BITMAP_TYPE_ICO)
        else:
            self.icon = wx.Icon(Bpath("images", "brz.png"), wx.BITMAP_TYPE_ICO)
            
        self.__init_execute_path()

        IDEFrame.__init__(self, parent, debug)
        self.Log = LogPseudoFile(self.LogConsole, self.SelectTab, logf)

        LocalRuntimeMixin.__init__(self, self.Log)

        self.LastPanelSelected = None

        # Define Tree item icon list
        self.LocationImageList = wx.ImageList(16, 16)
        self.LocationImageDict = {}

        # Icons for location items
        for imgname, itemtype in [
                ("CONFIGURATION", LOCATION_CONFNODE),
                ("RESOURCE",      LOCATION_MODULE),
                ("PROGRAM",       LOCATION_GROUP),
                ("VAR_INPUT",     LOCATION_VAR_INPUT),
                ("VAR_OUTPUT",    LOCATION_VAR_OUTPUT),
                ("VAR_LOCAL",     LOCATION_VAR_MEMORY)]:
            self.LocationImageDict[itemtype] = self.LocationImageList.Add(GetBitmap(imgname))

        # Icons for other items
        for imgname, itemtype in [
                ("Extension", ITEM_CONFNODE)]:
            self.TreeImageDict[itemtype] = self.TreeImageList.Add(GetBitmap(imgname))

        if projectOpen is not None:
            projectOpen = DecodeFileSystemPath(projectOpen, False)

        if projectOpen is not None and os.path.isdir(projectOpen):
            self.CTR = ProjectController(self, self.Log)
            self.Controler = self.CTR
            result, _err = self.CTR.LoadProject(projectOpen, buildpath)
            if not result:
                self.LibraryPanel.SetController(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self.RefreshConfigRecentProjects(os.path.abspath(projectOpen))
                self.RefreshAfterLoad()
            else:
                self.ResetView()
                self.ShowErrorMessage(result)
        else:
            self.CTR = ctr
            self.Controler = ctr
            if ctr is not None:
                ctr.SetAppFrame(self, self.Log)
                self.LibraryPanel.SetController(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self.RefreshAfterLoad()
        if self.EnableDebug:
            self.DebugVariablePanel.SetDataProducer(self.CTR)

        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)
        self.RefreshAll()
        self.LogConsole.SetFocus()

        signal.signal(signal.SIGTERM,self.signalTERM_handler)

    def RefreshTitle(self):
        name = _("OpenPLC Editor")
        if self.CTR is not None:
            projectname = self.CTR.GetProjectName()
            if self.CTR.ProjectTestModified():
                projectname = "~%s~" % projectname
            self.SetTitle("%s - %s" % (name, projectname))
        else:
            self.SetTitle(name)

    def OnOpenWidgetInspector(self, evt):
        # Activate the widget inspection tool
        from wx.lib.inspection import InspectionTool
        if not InspectionTool().initialized:
            InspectionTool().Init()

        # Find a widget to be selected in the tree.  Use either the
        # one under the cursor, if any, or this frame.
        wnd = wx.FindWindowAtPointer()
        if not wnd:
            wnd = self
        InspectionTool().Show(wnd, True)

    def OnLogConsoleFocusChanged(self, event):
        self.RefreshEditMenu()
        event.Skip()

    def OnLogConsoleUpdateUI(self, event):
        if event.GetUpdated()==wx.stc.STC_UPDATE_SELECTION:
            self.SetCopyBuffer(self.LogConsole.GetSelectedText(), True)
        event.Skip()

    def OnLogConsoleMarginClick(self, event):
        line_idx = self.LogConsole.LineFromPosition(event.GetPosition())
        wx.CallAfter(self.SearchLineForError, self.LogConsole.GetLine(line_idx))
        event.Skip()

    def OnLogConsoleModified(self, event):
        line_idx = self.LogConsole.LineFromPosition(event.GetPosition())
        line = self.LogConsole.GetLine(line_idx)
        if line:
            result = MATIEC_ERROR_MODEL.match(line)
            if result is not None:
                self.LogConsole.MarkerAdd(line_idx, 0)
        event.Skip()

    def SearchLineForError(self, line):
        if self.CTR is not None:
            result = MATIEC_ERROR_MODEL.match(line)
            if result is not None:
                first_line, first_column, last_line, last_column, _error = result.groups()
                self.CTR.ShowError(self.Log,
                                   (int(first_line), int(first_column)),
                                   (int(last_line),  int(last_column)))

    def CheckSaveBeforeClosing(self, title=_("Close Project")):
        """Function displaying an Error dialog in PLCOpenEditor.

        :returns: False if closing cancelled.
        """
        if self.CTR.ProjectTestModified():
            dialog = wx.MessageDialog(self,
                                      _("There are changes, do you want to save?"),
                                      title,
                                      wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            answer = dialog.ShowModal()
            dialog.Destroy()
            if answer == wx.ID_YES:
                self.CTR.SaveProject()
            elif answer == wx.ID_CANCEL:
                return False

        for idx in range(self.TabsOpened.GetPageCount()):
            window = self.TabsOpened.GetPage(idx)
            if not window.CheckSaveBeforeClosing():
                return False

        return True

    def GetTabInfos(self, tab):
        if isinstance(tab, EditorPanel) and \
           not isinstance(tab, (Viewer,
                                TextViewer,
                                ResourceEditor,
                                ConfigurationEditor,
                                DataTypeEditor)):
            return ("confnode", tab.Controler.CTNFullName(), tab.GetTagName())
        elif (isinstance(tab, TextViewer) and
              (tab.Controler is None or isinstance(tab.Controler, MiniTextControler))):
            return ("confnode", None, tab.GetInstancePath())
        else:
            return IDEFrame.GetTabInfos(self, tab)

    def LoadTab(self, notebook, page_infos):
        if page_infos[0] == "confnode":
            if page_infos[1] is None:
                confnode = self.CTR
            else:
                confnode = self.CTR.GetChildByName(page_infos[1])
            return notebook.GetPageIndex(confnode._OpenView(*page_infos[2:]))
        else:
            return IDEFrame.LoadTab(self, notebook, page_infos)

    # Strange hack required by WAMP connector, using twisted.
    # Twisted reactor needs to be stopped only before quit,
    # since it cannot be restarted
    ToDoBeforeQuit = []

    def AddToDoBeforeQuit(self, Thing):
        self.ToDoBeforeQuit.append(Thing)

    def TryCloseFrame(self):
        if self.CTR is None or self.CheckSaveBeforeClosing(_("Close Application")):
            if self.CTR is not None:
                self.CTR.KillDebugThread()
                self.CTR._Disconnect()
            self.KillLocalRuntime()

            self.SaveLastState()

            for Thing in self.ToDoBeforeQuit:
                Thing()
            self.ToDoBeforeQuit = []

            return True
        return False

    def OnCloseFrame(self, event):
        if self.TryCloseFrame():
            self.LogConsole.Disconnect(-1, -1, wx.wxEVT_KILL_FOCUS)
            super(Beremiz, self).OnCloseFrame(event)
            event.Skip()
        else:
            # prevent event to continue, i.e. cancel closing
            event.Veto()

    def signalTERM_handler(self, sig, frame):
        print ("Signal TERM caught: kill local runtime and quit, no save")
        self.KillLocalRuntime()
        sys.exit()

    def RefreshFileMenu(self):
        self.RefreshRecentProjectsMenu()

        MenuToolBar = self.Panes["MenuToolBar"]
        if self.CTR is not None:
            selected = self.TabsOpened.GetSelection()
            if selected >= 0:
                window = self.TabsOpened.GetPage(selected)
                viewer_is_modified = window.IsModified()
                is_viewer = isinstance(window, Viewer)
            else:
                viewer_is_modified = is_viewer = False
            if self.TabsOpened.GetPageCount() > 0:
                self.FileMenu.Enable(wx.ID_CLOSE, True)
                if is_viewer:
                    self.FileMenu.Enable(wx.ID_PREVIEW, True)
                    self.FileMenu.Enable(wx.ID_PRINT, True)
                    MenuToolBar.EnableTool(wx.ID_PRINT, True)
                else:
                    self.FileMenu.Enable(wx.ID_PREVIEW, False)
                    self.FileMenu.Enable(wx.ID_PRINT, False)
                    MenuToolBar.EnableTool(wx.ID_PRINT, False)
            else:
                self.FileMenu.Enable(wx.ID_CLOSE, False)
                self.FileMenu.Enable(wx.ID_PREVIEW, False)
                self.FileMenu.Enable(wx.ID_PRINT, False)
                MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, True)
            project_modified = self.CTR.ProjectTestModified() or viewer_is_modified
            self.FileMenu.Enable(wx.ID_SAVE, project_modified)
            MenuToolBar.EnableTool(wx.ID_SAVE, project_modified)
            self.FileMenu.Enable(wx.ID_SAVEAS, True)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, True)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, True)
        else:
            self.FileMenu.Enable(wx.ID_CLOSE, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, False)
            self.FileMenu.Enable(wx.ID_PREVIEW, False)
            self.FileMenu.Enable(wx.ID_PRINT, False)
            MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_SAVE, False)
            MenuToolBar.EnableTool(wx.ID_SAVE, False)
            self.FileMenu.Enable(wx.ID_SAVEAS, False)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, False)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, False)

    def RefreshRecentProjectsMenu(self):
        try:
            recent_projects = list(map(DecodeFileSystemPath,
                                  self.GetConfigEntry("RecentProjects", [])))
        except Exception:
            recent_projects = []

        while self.RecentProjectsMenu.GetMenuItemCount() > 0:
            item = self.RecentProjectsMenu.FindItemByPosition(0)
            self.RecentProjectsMenu.Remove(item)

        self.RecentProjectsMenuItem.Enable(len(recent_projects) > 0)
        for idx, projectpath in enumerate(recent_projects):
            text = '&%d: %s' % (idx + 1, projectpath)

            item = self.RecentProjectsMenu.Append(wx.ID_ANY, text, '')
            self.Bind(wx.EVT_MENU, self.GenerateOpenRecentProjectFunction(projectpath), item)

    def GenerateOpenRecentProjectFunction(self, projectpath):
        def OpenRecentProject(event):
            if self.CTR is not None and not self.CheckSaveBeforeClosing():
                return

            self.OpenProject(projectpath)
        return OpenRecentProject

    def GenerateMenuRecursive(self, items, menu):
        for kind, infos in items:
            if isinstance(kind, list):
                text, id = infos
                submenu = wx.Menu('')
                self.GenerateMenuRecursive(kind, submenu)
                menu.AppendMenu(id, text, submenu)
            elif kind == wx.ITEM_SEPARATOR:
                menu.AppendSeparator()
            else:
                text, id, _help, callback = infos
                AppendMenu(menu, help='', id=id, kind=kind, text=text)
                if callback is not None:
                    self.Bind(wx.EVT_MENU, callback, id=id)

    def RefreshEditorToolBar(self):
        IDEFrame.RefreshEditorToolBar(self)
        self.AUIManager.GetPane("EditorToolBar").Position(2)
        self.AUIManager.GetPane("StatusToolBar").Position(1)
        self.AUIManager.Update()

    def RefreshStatusToolBar(self):
        StatusToolBar = self.Panes["StatusToolBar"]
        StatusToolBar.ClearTools()
        StatusToolBar.SetMinSize(StatusToolBar.GetToolBitmapSize())

        if self.CTR is not None:

            for confnode_method in self.CTR.StatusMethods:
                if "method" in confnode_method and confnode_method.get("shown", True):
                    tool = StatusToolBar.AddTool(
                        wx.ID_ANY, confnode_method["name"],
                        GetBitmap(confnode_method.get("bitmap", "Unknown")),
                        confnode_method["tooltip"])
                    self.Bind(wx.EVT_MENU, self.GetMenuCallBackFunction(confnode_method["method"]), tool)

            StatusToolBar.Realize()
            self.AUIManager.GetPane("StatusToolBar").BestSize(StatusToolBar.GetBestSize()).Show()
        else:
            self.AUIManager.GetPane("StatusToolBar").Hide()
        self.AUIManager.GetPane("EditorToolBar").Position(2)
        self.AUIManager.GetPane("StatusToolBar").Position(1)
        self.AUIManager.Update()

    def RefreshEditMenu(self):
        IDEFrame.RefreshEditMenu(self)
        if self.FindFocus() == self.LogConsole:
            self.EditMenu.Enable(wx.ID_COPY, True)
            self.Panes["MenuToolBar"].EnableTool(wx.ID_COPY, True)

        if self.CTR is not None:
            selected = self.TabsOpened.GetSelection()
            if selected >= 0:
                panel = self.TabsOpened.GetPage(selected)
            else:
                panel = None
            if panel != self.LastPanelSelected:
                for i in range(self.EditMenuSize, self.EditMenu.GetMenuItemCount()):
                    item = self.EditMenu.FindItemByPosition(self.EditMenuSize)
                    if item is not None:
                        if item.IsSeparator():
                            self.EditMenu.RemoveItem(item)
                        else:
                            self.EditMenu.Delete(item.GetId())
                self.LastPanelSelected = panel
                if panel is not None:
                    items = panel.GetConfNodeMenuItems()
                else:
                    items = []
                if len(items) > 0:
                    self.EditMenu.AppendSeparator()
                    self.GenerateMenuRecursive(items, self.EditMenu)
            if panel is not None:
                panel.RefreshConfNodeMenu(self.EditMenu)
        else:
            for i in range(self.EditMenuSize, self.EditMenu.GetMenuItemCount()):
                item = self.EditMenu.FindItemByPosition(i)
                if item is not None:
                    if item.IsSeparator():
                        self.EditMenu.RemoveItem(item)
                    else:
                        self.EditMenu.Delete(item.GetId())
            self.LastPanelSelected = None
        self.MenuBar.Refresh()

    def RefreshAll(self):
        self.RefreshStatusToolBar()

    def GetMenuCallBackFunction(self, method):
        """ Generate the callbackfunc for a given CTR method"""
        def OnMenu(event):
            # Disable button to prevent re-entrant call
            event.GetEventObject().Disable()
            # Call
            getattr(self.CTR, method)()
            # Re-enable button
            event.GetEventObject().Enable()
        return OnMenu

    def GetConfigEntry(self, entry_name, default):
        return pickle.loads(self.Config.Read(entry_name,
                                             pickle.dumps(default,
                                                          0).decode()).encode())

    def ResetConnectionStatusBar(self):
        for field in range(self.ConnectionStatusBar.GetFieldsCount()):
            self.ConnectionStatusBar.SetStatusText('', field)

    def ResetView(self):
        IDEFrame.ResetView(self)
        if self.CTR is not None:
            self.CTR.CloseProject()
        self.CTR = None
        self.Log.flush()
        if self.EnableDebug:
            self.DebugVariablePanel.SetDataProducer(None)
            self.ResetConnectionStatusBar()

    def RefreshConfigRecentProjects(self, projectpath, err=False):
        try:
            recent_projects = list(map(DecodeFileSystemPath,
                                  self.GetConfigEntry("RecentProjects", [])))
        except Exception:
            recent_projects = []
        if projectpath in recent_projects:
            recent_projects.remove(projectpath)
        if not err:
            recent_projects.insert(0, projectpath)
        self.Config.Write("RecentProjects",
                          pickle.dumps(
                              list(map(EncodeFileSystemPath,
                                       recent_projects[:MAX_RECENT_PROJECTS])),
                              0))
        self.Config.Flush()

    def ResetPerspective(self):
        IDEFrame.ResetPerspective(self)
        self.RefreshStatusToolBar()

    def OnNewProjectMenu(self, event):
        if self.CTR is not None and not self.CheckSaveBeforeClosing():
            return

        try:
            defaultpath = DecodeFileSystemPath(self.Config.Read("lastopenedfolder").encode())
        except Exception:
            defaultpath = os.path.expanduser("~")

        dialog = wx.DirDialog(self, _("Choose an empty directory for new project"), defaultpath)
        if dialog.ShowModal() == wx.ID_OK:
            projectpath = dialog.GetPath()
            self.Config.Write("lastopenedfolder",
                              EncodeFileSystemPath(os.path.dirname(projectpath)))
            self.Config.Flush()
            self.ResetView()
            ctr = ProjectController(self, self.Log)
            result = ctr.NewProject(projectpath)
            if not result:
                self.CTR = ctr
                self.Controler = self.CTR
                self.LibraryPanel.SetController(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self.RefreshConfigRecentProjects(projectpath)
                if self.EnableDebug:
                    self.DebugVariablePanel.SetDataProducer(self.CTR)
                self.RefreshAfterLoad()
                IDEFrame.OnAddNewProject(self, event)
            else:
                self.ResetView()
                self.ShowErrorMessage(result)
            self.RefreshAll()
            self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
        dialog.Destroy()

    def OnOpenProjectMenu(self, event):
        if self.CTR is not None and not self.CheckSaveBeforeClosing():
            return

        try:
            defaultpath = DecodeFileSystemPath(self.Config.Read("lastopenedfolder"))
        except Exception:
            defaultpath = os.path.expanduser("~")

        dialog = wx.DirDialog(self, _("Choose a project"), defaultpath,
                              style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        if dialog.ShowModal() == wx.ID_OK:
            self.OpenProject(dialog.GetPath())
        dialog.Destroy()

    def OpenProject(self, projectpath):
        if os.path.isdir(projectpath):
            self.Config.Write("lastopenedfolder",
                              EncodeFileSystemPath(os.path.dirname(projectpath)))
            self.Config.Flush()
            self.ResetView()
            self.CTR = ProjectController(self, self.Log)
            self.Controler = self.CTR
            result, err = self.CTR.LoadProject(projectpath)
            if not result:
                self.LibraryPanel.SetController(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                if self.EnableDebug:
                    self.DebugVariablePanel.SetDataProducer(self.CTR)
                self.RefreshAfterLoad()
            else:
                self.ResetView()
                self.ShowErrorMessage(result)
            self.RefreshAll()
            self.SearchResultPanel.ResetSearchResults()
        else:
            self.ShowErrorMessage(_("\"%s\" folder is not a valid Beremiz project\n") % projectpath)
            err = True
        self.RefreshConfigRecentProjects(projectpath, err)
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)

    def OnCloseProjectMenu(self, event):
        if self.CTR is not None and not self.CheckSaveBeforeClosing():
            return

        self.ResetView()
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
        self.RefreshAll()

    def RefreshAfterLoad(self):
        self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)

    def RefreshAfterSave(self):
        self.RefreshAll()
        self._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES)

    def OnSaveProjectMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            window.Save()
        if self.CTR is not None:
            self.CTR.SaveProject()
            self.RefreshAfterSave()

    def OnSaveProjectAsMenu(self, event):
        selected = self.TabsOpened.GetSelection()
        if selected != -1:
            window = self.TabsOpened.GetPage(selected)
            window.SaveAs()
        if self.CTR is not None:
            self.CTR.SaveProjectAs()
            self.RefreshAfterSave()
            self.RefreshConfigRecentProjects(self.CTR.ProjectPath)

    def OnQuitMenu(self, event):
        self.Close()

    def OnAboutMenu(self, event):
        info = wx.adv.AboutDialogInfo()
        info = version.GetAboutDialogInfo(info)

        ShowAboutDialog(self, info)

    def OnProjectTreeItemBeginEdit(self, event):
        selected = event.GetItem()
        if self.ProjectTree.GetItemData(selected)["type"] == ITEM_CONFNODE:
            event.Veto()
        else:
            IDEFrame.OnProjectTreeItemBeginEdit(self, event)

    def OnProjectTreeRightUp(self, event):
        item = event.GetItem()
        item_infos = self.ProjectTree.GetItemData(item)

        if item_infos["type"] == ITEM_CONFNODE:
            confnode_menu = wx.Menu(title='')

            confnode = item_infos["confnode"]
            if confnode is not None:
                menu_items = confnode.GetContextualMenuItems()
                if menu_items is not None:
                    for text, helpstr, callback in menu_items:
                        item = confnode_menu.Append(wx.ID_ANY, text, helpstr)
                        self.Bind(wx.EVT_MENU, callback, item)
                else:
                    for name, XSDClass, helpstr in confnode.CTNChildrenTypes:
                        if not hasattr(XSDClass, 'CTNMaxCount') or not confnode.Children.get(name) \
                                or len(confnode.Children[name]) < XSDClass.CTNMaxCount:
                            item = confnode_menu.Append(wx.ID_ANY, _("Add") + " " + name, helpstr)
                            self.Bind(wx.EVT_MENU, self.GetAddConfNodeFunction(name, confnode), item)
            item = confnode_menu.Append(wx.ID_ANY, _("Delete"))
            self.Bind(wx.EVT_MENU, self.GetDeleteMenuFunction(confnode), item)

            self.PopupMenu(confnode_menu)
            confnode_menu.Destroy()

            event.Skip()
        elif item_infos["type"] == ITEM_RESOURCE:
            # prevent last resource to be delted
            parent = self.ProjectTree.GetItemParent(item)
            parent_name = self.ProjectTree.GetItemText(parent)
            if parent_name == _("Resources"):
                IDEFrame.OnProjectTreeRightUp(self, event)
        else:
            IDEFrame.OnProjectTreeRightUp(self, event)

    def OnProjectTreeItemActivated(self, event):
        selected = event.GetItem()
        item_infos = self.ProjectTree.GetItemData(selected)
        if item_infos["type"] == ITEM_CONFNODE:
            item_infos["confnode"]._OpenView()
            event.Skip()
        elif item_infos["type"] == ITEM_PROJECT:
            self.CTR._OpenView()
        else:
            IDEFrame.OnProjectTreeItemActivated(self, event)

    def ProjectTreeItemSelect(self, select_item):
        if select_item is not None and select_item.IsOk():
            item_infos = self.ProjectTree.GetItemData(select_item)
            if item_infos["type"] == ITEM_CONFNODE:
                item_infos["confnode"]._OpenView(onlyopened=True)
            elif item_infos["type"] == ITEM_PROJECT:
                self.CTR._OpenView(onlyopened=True)
            else:
                IDEFrame.ProjectTreeItemSelect(self, select_item)

    def GetProjectElementWindow(self, element, tagname):
        is_a_CTN_tagname = len(tagname.split("::")) == 1
        if is_a_CTN_tagname:
            confnode = self.CTR.GetChildByName(tagname)
            return confnode.GetView()
        else:
            return IDEFrame.GetProjectElementWindow(self, element, tagname)

    def SelectProjectTreeItem(self, tagname):
        if self.ProjectTree is not None:
            root = self.ProjectTree.GetRootItem()
            if root.IsOk():
                words = tagname.split("::")
                if len(words) == 1:
                    if tagname == "Project":
                        self.SelectedItem = root
                        self.ProjectTree.SelectItem(root)
                        self.ResetSelectedItem()
                    else:
                        return self.RecursiveProjectTreeItemSelection(
                            root,
                            [(word, ITEM_CONFNODE) for word in tagname.split(".")])
                elif words[0] == "R":
                    return self.RecursiveProjectTreeItemSelection(root, [(words[2], ITEM_RESOURCE)])
                elif not os.path.exists(words[0]):
                    IDEFrame.SelectProjectTreeItem(self, tagname)

    def GetAddConfNodeFunction(self, name, confnode=None):
        def AddConfNodeMenuFunction(event):
            wx.CallAfter(self.AddConfNode, name, confnode)
        return AddConfNodeMenuFunction

    def GetDeleteMenuFunction(self, confnode):
        def DeleteMenuFunction(event):
            wx.CallAfter(self.DeleteConfNode, confnode)
        return DeleteMenuFunction

    def AddConfNode(self, ConfNodeType, confnode=None):
        if self.CTR.CheckProjectPathPerm():
            ConfNodeName = "%s_0" % ConfNodeType
            if confnode is not None:
                confnode.CTNAddChild(ConfNodeName, ConfNodeType)
            else:
                self.CTR.CTNAddChild(ConfNodeName, ConfNodeType)
            self._Refresh(TITLE, FILEMENU, PROJECTTREE)

    def DeleteConfNode(self, confnode):
        if self.CTR.CheckProjectPathPerm():
            dialog = wx.MessageDialog(
                self,
                _("Really delete node '%s'?") % confnode.CTNName(),
                _("Remove %s node") % confnode.CTNType,
                wx.YES_NO | wx.NO_DEFAULT)
            if dialog.ShowModal() == wx.ID_YES:
                confnode.CTNRemove()
                del confnode
                self._Refresh(TITLE, FILEMENU, PROJECTTREE)
            dialog.Destroy()

# -------------------------------------------------------------------------------
#                        Highlights showing functions
# -------------------------------------------------------------------------------

    def ShowHighlight(self, infos, start, end, highlight_type):
        config_name = self.Controler.GetProjectMainConfigurationName()
        if config_name is not None and infos[0] == ComputeConfigurationName(config_name):
            self.CTR._OpenView()
            selected = self.TabsOpened.GetSelection()
            if selected != -1:
                viewer = self.TabsOpened.GetPage(selected)
                viewer.AddHighlight(infos[1:], start, end, highlight_type)
        else:
            IDEFrame.ShowHighlight(self, infos, start, end, highlight_type)
