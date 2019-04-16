#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov
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
from __future__ import print_function
import os
import sys
import getopt

import wx

import version
import util.paths as paths
import util.ExceptionHandler
from util.misc import InstallLocalRessources
from docutil.docpdf import open_pdf
from IDEFrame import IDEFrame, AppendMenu
from IDEFrame import \
    TITLE, \
    EDITORTOOLBAR, \
    FILEMENU, \
    EDITMENU, \
    DISPLAYMENU, \
    PROJECTTREE, \
    POUINSTANCEVARIABLESPANEL, \
    LIBRARYTREE, \
    PAGETITLES, \
    DecodeFileSystemPath
from editors.Viewer import Viewer
from PLCControler import PLCControler
from dialogs import ProjectDialog
from dialogs.AboutDialog import ShowAboutDialog


# -------------------------------------------------------------------------------
#                            PLCOpenEditor Main Class
# -------------------------------------------------------------------------------

# Define PLCOpenEditor FileMenu extra items id
[
    ID_PLCOPENEDITORFILEMENUGENERATE,
    ID_PLCOPENEDITORFILEMENUGENERATEAS,
] = [wx.NewId() for _init_coll_FileMenu_Items in range(2)]


beremiz_dir = paths.AbsDir(__file__)


class PLCOpenEditor(IDEFrame):

    def _init_coll_FileMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_NEW,
                   kind=wx.ITEM_NORMAL, text=_(u'New') + '\tCTRL+N')
        AppendMenu(parent, help='', id=wx.ID_OPEN,
                   kind=wx.ITEM_NORMAL, text=_(u'Open') + '\tCTRL+O')
        AppendMenu(parent, help='', id=wx.ID_CLOSE,
                   kind=wx.ITEM_NORMAL, text=_(u'Close Tab') + '\tCTRL+W')
        AppendMenu(parent, help='', id=wx.ID_CLOSE_ALL,
                   kind=wx.ITEM_NORMAL, text=_(u'Close Project') + '\tCTRL+SHIFT+W')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_SAVE,
                   kind=wx.ITEM_NORMAL, text=_(u'Save') + '\tCTRL+S')
        AppendMenu(parent, help='', id=wx.ID_SAVEAS,
                   kind=wx.ITEM_NORMAL, text=_(u'Save As...') + '\tCTRL+SHIFT+S')
        AppendMenu(parent, help='', id=ID_PLCOPENEDITORFILEMENUGENERATE,
                   kind=wx.ITEM_NORMAL, text=_(u'Generate Program') + '\tCTRL+G')
        AppendMenu(parent, help='', id=ID_PLCOPENEDITORFILEMENUGENERATEAS,
                   kind=wx.ITEM_NORMAL, text=_(u'Generate Program As...') + '\tCTRL+SHIFT+G')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_PAGE_SETUP,
                   kind=wx.ITEM_NORMAL, text=_(u'Page Setup') + '\tCTRL+ALT+P')
        AppendMenu(parent, help='', id=wx.ID_PREVIEW,
                   kind=wx.ITEM_NORMAL, text=_(u'Preview') + '\tCTRL+SHIFT+P')
        AppendMenu(parent, help='', id=wx.ID_PRINT,
                   kind=wx.ITEM_NORMAL, text=_(u'Print') + '\tCTRL+P')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_PROPERTIES,
                   kind=wx.ITEM_NORMAL, text=_(u'&Properties'))
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_EXIT,
                   kind=wx.ITEM_NORMAL, text=_(u'Quit') + '\tCTRL+Q')

        self.Bind(wx.EVT_MENU, self.OnNewProjectMenu, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenProjectMenu, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnCloseTabMenu, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.OnCloseProjectMenu, id=wx.ID_CLOSE_ALL)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectMenu, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectAsMenu, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnGenerateProgramMenu,
                  id=ID_PLCOPENEDITORFILEMENUGENERATE)
        self.Bind(wx.EVT_MENU, self.OnGenerateProgramAsMenu,
                  id=ID_PLCOPENEDITORFILEMENUGENERATEAS)
        self.Bind(wx.EVT_MENU, self.OnPageSetupMenu, id=wx.ID_PAGE_SETUP)
        self.Bind(wx.EVT_MENU, self.OnPreviewMenu, id=wx.ID_PREVIEW)
        self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=wx.ID_PRINT)
        self.Bind(wx.EVT_MENU, self.OnPropertiesMenu, id=wx.ID_PROPERTIES)
        self.Bind(wx.EVT_MENU, self.OnQuitMenu, id=wx.ID_EXIT)

        self.AddToMenuToolBar([(wx.ID_NEW, "new", _(u'New'), None),
                               (wx.ID_OPEN, "open", _(u'Open'), None),
                               (wx.ID_SAVE, "save", _(u'Save'), None),
                               (wx.ID_SAVEAS, "saveas", _(u'Save As...'), None),
                               (wx.ID_PRINT, "print", _(u'Print'), None),
                               (ID_PLCOPENEDITORFILEMENUGENERATE, "Build", _(u'Generate Program'), None)])

    def _init_coll_HelpMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_HELP,
                   kind=wx.ITEM_NORMAL, text=_(u'PLCOpenEditor') + '\tF1')
        # AppendMenu(parent, help='', id=wx.ID_HELP_CONTENTS,
        #      kind=wx.ITEM_NORMAL, text=u'PLCOpen\tF2')
        # AppendMenu(parent, help='', id=wx.ID_HELP_CONTEXT,
        #      kind=wx.ITEM_NORMAL, text=u'IEC 61131-3\tF3')

        def handler(event):
            return wx.MessageBox(
                version.GetCommunityHelpMsg(),
                _(u'Community support'),
                wx.OK | wx.ICON_INFORMATION)

        id = wx.NewId()
        parent.Append(help='', id=id, kind=wx.ITEM_NORMAL, text=_(u'Community support'))
        self.Bind(wx.EVT_MENU, handler, id=id)

        AppendMenu(parent, help='', id=wx.ID_ABOUT,
                   kind=wx.ITEM_NORMAL, text=_(u'About'))
        self.Bind(wx.EVT_MENU, self.OnPLCOpenEditorMenu, id=wx.ID_HELP)
        # self.Bind(wx.EVT_MENU, self.OnPLCOpenMenu, id=wx.ID_HELP_CONTENTS)
        self.Bind(wx.EVT_MENU, self.OnAboutMenu, id=wx.ID_ABOUT)

    def __init__(self, parent, fileOpen=None):
        """ Constructor of the PLCOpenEditor class.

        :param parent: The parent window.
        :param fileOpen: The filepath to open if no controler defined (default: None).
        """
        self.icon = wx.Icon(os.path.join(beremiz_dir, "images", "poe.ico"), wx.BITMAP_TYPE_ICO)
        IDEFrame.__init__(self, parent)

        result = None

        # Open the filepath if defined
        if fileOpen is not None:
            fileOpen = DecodeFileSystemPath(fileOpen, False)
            if os.path.isfile(fileOpen):
                # Create a new controller
                controler = PLCControler()
                result = controler.OpenXMLFile(fileOpen)
                self.Controler = controler
                self.LibraryPanel.SetController(controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(controler)
                self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)

        # Define PLCOpenEditor icon
        self.SetIcon(self.icon)

        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)

        if result is not None:
            (num, line) = result
            self.ShowErrorMessage(_("PLC syntax error at line {a1}:\n{a2}").format(a1=num, a2=line))

    def OnCloseFrame(self, event):
        if self.Controler is None or self.CheckSaveBeforeClosing(_("Close Application")):
            self.AUIManager.UnInit()

            self.SaveLastState()

            event.Skip()
        else:
            event.Veto()

    def RefreshTitle(self):
        name = _("PLCOpenEditor")
        if self.Controler is not None:
            self.SetTitle("%s - %s" % (name, self.Controler.GetFilename()))
        else:
            self.SetTitle(name)

    # -------------------------------------------------------------------------------
    #                            File Menu Functions
    # -------------------------------------------------------------------------------

    def RefreshFileMenu(self):
        MenuToolBar = self.Panes["MenuToolBar"]
        if self.Controler is not None:
            selected = self.TabsOpened.GetSelection()
            if selected >= 0:
                graphic_viewer = isinstance(self.TabsOpened.GetPage(selected), Viewer)
            else:
                graphic_viewer = False
            if self.TabsOpened.GetPageCount() > 0:
                self.FileMenu.Enable(wx.ID_CLOSE, True)
                if graphic_viewer:
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
            project_modified = not self.Controler.ProjectIsSaved()
            self.FileMenu.Enable(wx.ID_SAVE, project_modified)
            MenuToolBar.EnableTool(wx.ID_SAVE, project_modified)
            self.FileMenu.Enable(wx.ID_PROPERTIES, True)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, True)
            self.FileMenu.Enable(wx.ID_SAVEAS, True)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, True)
            self.FileMenu.Enable(ID_PLCOPENEDITORFILEMENUGENERATE, True)
            MenuToolBar.EnableTool(ID_PLCOPENEDITORFILEMENUGENERATE, True)
            self.FileMenu.Enable(ID_PLCOPENEDITORFILEMENUGENERATEAS, True)
        else:
            self.FileMenu.Enable(wx.ID_CLOSE, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, False)
            self.FileMenu.Enable(wx.ID_PREVIEW, False)
            self.FileMenu.Enable(wx.ID_PRINT, False)
            MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_SAVE, False)
            MenuToolBar.EnableTool(wx.ID_SAVE, False)
            self.FileMenu.Enable(wx.ID_PROPERTIES, False)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, False)
            self.FileMenu.Enable(wx.ID_SAVEAS, False)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, False)
            self.FileMenu.Enable(ID_PLCOPENEDITORFILEMENUGENERATE, False)
            MenuToolBar.EnableTool(ID_PLCOPENEDITORFILEMENUGENERATE, False)
            self.FileMenu.Enable(ID_PLCOPENEDITORFILEMENUGENERATEAS, False)

    def OnNewProjectMenu(self, event):
        if self.Controler is not None and not self.CheckSaveBeforeClosing():
            return
        dialog = ProjectDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            properties = dialog.GetValues()
            self.ResetView()
            self.Controler = PLCControler()
            self.Controler.CreateNewProject(properties)
            self.LibraryPanel.SetController(self.Controler)
            self.ProjectTree.Enable(True)
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL,
                          LIBRARYTREE)

    def OnOpenProjectMenu(self, event):
        if self.Controler is not None and not self.CheckSaveBeforeClosing():
            return
        filepath = ""
        if self.Controler is not None:
            filepath = self.Controler.GetFilePath()
        if filepath != "":
            directory = os.path.dirname(filepath)
        else:
            directory = os.getcwd()

        result = None

        dialog = wx.FileDialog(self, _("Choose a file"), directory, "",  _("PLCOpen files (*.xml)|*.xml|All files|*.*"), wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            if os.path.isfile(filepath):
                self.ResetView()
                controler = PLCControler()
                result = controler.OpenXMLFile(filepath)
                self.Controler = controler
                self.LibraryPanel.SetController(controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(controler)
                self._Refresh(PROJECTTREE, LIBRARYTREE)
            self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
        dialog.Destroy()

        if result is not None:
            (num, line) = result
            self.ShowErrorMessage(_("PLC syntax error at line {a1}:\n{a2}").format(a1=num, a2=line))

    def OnCloseProjectMenu(self, event):
        if not self.CheckSaveBeforeClosing():
            return
        self.ResetView()
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)

    def OnSaveProjectMenu(self, event):
        self.SaveProject()

    def OnSaveProjectAsMenu(self, event):
        self.SaveProjectAs()

    def OnGenerateProgramMenu(self, event):
        result = self.Controler.GetProgramFilePath()
        if not result:
            self.GenerateProgramAs()
        else:
            self.GenerateProgram(result)

    def OnGenerateProgramAsMenu(self, event):
        self.GenerateProgramAs()

    def GenerateProgramAs(self):
        dialog = wx.FileDialog(self, _("Choose a file"), os.getcwd(), os.path.basename(self.Controler.GetProgramFilePath()),  _("ST files (*.st)|*.st|All files|*.*"), wx.SAVE | wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            self.GenerateProgram(dialog.GetPath())
        dialog.Destroy()

    def GenerateProgram(self, filepath=None):
        message_text = ""
        header, icon = _("Done"), wx.ICON_INFORMATION
        if os.path.isdir(os.path.dirname(filepath)):
            _program, errors, warnings = self.Controler.GenerateProgram(filepath)
            message_text += "".join([_("warning: %s\n") % warning for warning in warnings])
            if len(errors) > 0:
                message_text += "".join([_("error: %s\n") % error for error in errors])
                message_text += _("Can't generate program to file %s!") % filepath
                header, icon = _("Error"), wx.ICON_ERROR
            else:
                message_text += _("Program was successfully generated!")
        else:
            message_text += _("\"%s\" is not a valid folder!") % os.path.dirname(filepath)
            header, icon = _("Error"), wx.ICON_ERROR
        message = wx.MessageDialog(self, message_text, header, wx.OK | icon)
        message.ShowModal()
        message.Destroy()

    def OnPLCOpenEditorMenu(self, event):
        wx.MessageBox(_("No documentation available.\nComing soon."))

    def OnPLCOpenMenu(self, event):
        open_pdf(os.path.join(beremiz_dir, "plcopen", "TC6_XML_V101.pdf"))

    def OnAboutMenu(self, event):
        info = version.GetAboutDialogInfo()
        info.Name = "PLCOpenEditor"
        info.Description = _("PLCOpenEditor is part of Beremiz project.\n\n"
                             "Beremiz is an ") + info.Description
        info.Icon = wx.Icon(os.path.join(beremiz_dir, "images", "aboutlogo.png"), wx.BITMAP_TYPE_PNG)
        ShowAboutDialog(self, info)

    def SaveProject(self):
        result = self.Controler.SaveXMLFile()
        if not result:
            self.SaveProjectAs()
        else:
            self._Refresh(TITLE, FILEMENU, PAGETITLES)

    def SaveProjectAs(self):
        filepath = self.Controler.GetFilePath()
        if filepath != "":
            directory, filename = os.path.split(filepath)
        else:
            directory, filename = os.getcwd(), "%(projectName)s.xml" % self.Controler.GetProjectProperties()
        dialog = wx.FileDialog(self, _("Choose a file"), directory, filename,  _("PLCOpen files (*.xml)|*.xml|All files|*.*"), wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            if os.path.isdir(os.path.dirname(filepath)):
                result = self.Controler.SaveXMLFile(filepath)
                if not result:
                    self.ShowErrorMessage(_("Can't save project to file %s!") % filepath)
            else:
                self.ShowErrorMessage(_("\"%s\" is not a valid folder!") % os.path.dirname(filepath))
            self._Refresh(TITLE, FILEMENU, PAGETITLES)
        dialog.Destroy()


class PLCOpenEditorApp(wx.App):
    # def SetOpenFile(

    def PrintUsage(self):
        print("\nUsage of PLCOpenEditor.py :")
        print("\n   %s [Filepath]\n" % sys.argv[0])

    def ParseCommandLine(self):
        # Parse options given to PLCOpenEditor in command line
        try:
            opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        except getopt.GetoptError:
            # print help information and exit:
            self.PrintUsage()
            sys.exit(2)

        # Extract if help has been requested
        for o, _a in opts:
            if o in ("-h", "--help"):
                self.PrintUsage()
                sys.exit()

        # Extract the optional filename to open
        self.fileOpen = None
        if len(args) > 1:
            self.PrintUsage()
            sys.exit()
        elif len(args) == 1:
            self.fileOpen = args[0]

    def OnInit(self):
        self.SetAppName('plcopeneditor')
        self.ParseCommandLine()
        InstallLocalRessources(beremiz_dir)
        if wx.VERSION < (3, 0, 0):
            wx.InitAllImageHandlers()
        util.ExceptionHandler.AddExceptHook(version.app_version)
        self.frame = PLCOpenEditor(None, fileOpen=self.fileOpen)
        return True

    def Show(self):
        self.frame.Show()


if __name__ == '__main__':
    app = PLCOpenEditorApp()
    app.Show()
    app.MainLoop()
