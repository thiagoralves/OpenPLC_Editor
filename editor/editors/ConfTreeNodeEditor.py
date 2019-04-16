#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov <andrej.skvortzov@gmail.com>
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

from editors.EditorPanel import EditorPanel

from IDEFrame import TITLE, FILEMENU, PROJECTTREE, PAGETITLES

from controls import TextCtrlAutoComplete
from dialogs import BrowseValuesLibraryDialog, UriEditor
from util.BitmapLibrary import GetBitmap

if wx.Platform == '__WXMSW__':
    faces = {
        'times': 'Times New Roman',
        'mono':  'Courier New',
        'helv':  'Arial',
        'other': 'Comic Sans MS',
        'size':  16,
    }
else:
    faces = {
        'times': 'Times',
        'mono':  'Courier',
        'helv':  'Helvetica',
        'other': 'new century schoolbook',
        'size':  18,
    }

SCROLLBAR_UNIT = 10


class GenBitmapTextButton(wx.lib.buttons.GenBitmapTextButton):
    def _GetLabelSize(self):
        """ used internally """
        w, h = self.GetTextExtent(self.GetLabel())
        if not self.bmpLabel:
            return w, h, False       # if there isn't a bitmap use the size of the text

        w_bmp = self.bmpLabel.GetWidth()+2
        h_bmp = self.bmpLabel.GetHeight()+2
        height = h + h_bmp
        if w_bmp > w:
            width = w_bmp
        else:
            width = w
        return width, height, False

    def DrawLabel(self, dc, width, height, dw=0, dy=0):
        bmp = self.bmpLabel
        if bmp is not None:     # if the bitmap is used
            if self.bmpDisabled and not self.IsEnabled():
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw, bh = bmp.GetWidth(), bmp.GetHeight()
            if not self.up:
                dw = dy = self.labelDelta
            hasMask = bmp.GetMask() is not None
        else:
            bw = bh = 0     # no bitmap -> size is zero

        dc.SetFont(self.GetFont())
        if self.IsEnabled():
            dc.SetTextForeground(self.GetForegroundColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        label = self.GetLabel()
        tw, th = dc.GetTextExtent(label)        # size of text
        if not self.up:
            dw = dy = self.labelDelta

        pos_x = (width - bw) // 2 + dw      # adjust for bitmap and text to centre
        pos_y = (height - bh - th) // 2 + dy
        if bmp is not None:
            dc.DrawBitmap(bmp, pos_x, pos_y, hasMask)  # draw bitmap if available
            pos_x = (width-tw)//2+dw      # adjust for bitmap and text to centre
            pos_y += bh + 2

        dc.DrawText(label, pos_x, pos_y)      # draw the text


class GenStaticBitmap(wx.StaticBitmap):
    """ Customized GenStaticBitmap, fix transparency redraw bug on wx2.8/win32,
    and accept image name as __init__ parameter, fail silently if file do not exist"""
    def __init__(self, parent, ID, bitmapname,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0,
                 name="genstatbmp"):

        bitmap = GetBitmap(bitmapname)
        if bitmap is None:
            bitmap = wx.EmptyBitmap(0, 0)

        wx.StaticBitmap.__init__(self, parent, ID,
                                 bitmap,
                                 pos, size,
                                 style,
                                 name)


class ConfTreeNodeEditor(EditorPanel):

    SHOW_BASE_PARAMS = True
    SHOW_PARAMS = True
    CONFNODEEDITOR_TABS = []

    def _init_Editor(self, parent):
        tabs_num = len(self.CONFNODEEDITOR_TABS)
        if self.SHOW_PARAMS and len(self.Controler.GetParamsAttributes()) > 0:
            tabs_num += 1

        if tabs_num > 1 or self.SHOW_BASE_PARAMS:
            self.Editor = wx.Panel(parent,
                                   style=wx.SUNKEN_BORDER | wx.SP_3D)

            self.MainSizer = wx.BoxSizer(wx.VERTICAL)

            if self.SHOW_BASE_PARAMS:
                baseparamseditor_sizer = wx.BoxSizer(wx.HORIZONTAL)
                self.MainSizer.AddSizer(baseparamseditor_sizer, border=5,
                                        flag=wx.GROW | wx.ALL)

                self.FullIECChannel = wx.StaticText(self.Editor, -1)
                self.FullIECChannel.SetFont(
                    wx.Font(faces["size"], wx.DEFAULT, wx.NORMAL,
                            wx.BOLD, faceName=faces["helv"]))
                baseparamseditor_sizer.AddWindow(self.FullIECChannel,
                                                 flag=wx.ALIGN_CENTER_VERTICAL)

                updownsizer = wx.BoxSizer(wx.VERTICAL)
                baseparamseditor_sizer.AddSizer(updownsizer, border=5,
                                                flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)

                self.IECCUpButton = wx.lib.buttons.GenBitmapTextButton(
                    self.Editor,
                    bitmap=GetBitmap('IECCDown'),
                    size=wx.Size(16, 16),
                    style=wx.NO_BORDER)
                self.IECCUpButton.Bind(wx.EVT_BUTTON, self.GetItemChannelChangedFunction(1),
                                       self.IECCUpButton)
                updownsizer.AddWindow(self.IECCUpButton, flag=wx.ALIGN_LEFT)

                self.IECCDownButton = wx.lib.buttons.GenBitmapButton(
                    self.Editor, bitmap=GetBitmap('IECCUp'),
                    size=wx.Size(16, 16), style=wx.NO_BORDER)
                self.IECCDownButton.Bind(wx.EVT_BUTTON, self.GetItemChannelChangedFunction(-1),
                                         self.IECCDownButton)
                updownsizer.AddWindow(self.IECCDownButton, flag=wx.ALIGN_LEFT)

                self.ConfNodeName = wx.TextCtrl(self.Editor,
                                                size=wx.Size(150, 25))
                self.ConfNodeName.SetFont(
                    wx.Font(faces["size"] * 0.75, wx.DEFAULT, wx.NORMAL,
                            wx.BOLD, faceName=faces["helv"]))
                self.ConfNodeName.Bind(
                    wx.EVT_TEXT,
                    self.GetTextCtrlCallBackFunction(self.ConfNodeName, "BaseParams.Name", True),
                    self.ConfNodeName)
                baseparamseditor_sizer.AddWindow(
                    self.ConfNodeName, border=5,
                    flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)

                buttons_sizer = self.GenerateMethodButtonSizer()
                baseparamseditor_sizer.AddSizer(buttons_sizer, flag=wx.ALIGN_CENTER)

            if tabs_num > 1:
                self.ConfNodeNoteBook = wx.Notebook(self.Editor)
                parent = self.ConfNodeNoteBook
                self.MainSizer.AddWindow(self.ConfNodeNoteBook, 1, flag=wx.GROW)
            else:
                parent = self.Editor
                self.ConfNodeNoteBook = None

            self.Editor.SetSizer(self.MainSizer)
        else:
            self.ConfNodeNoteBook = None
            self.Editor = None

        for title, create_func_name in self.CONFNODEEDITOR_TABS:
            editor = getattr(self, create_func_name)(parent)
            if self.ConfNodeNoteBook is not None:
                self.ConfNodeNoteBook.AddPage(editor, title)
            elif self.SHOW_BASE_PARAMS:
                self.MainSizer.AddWindow(editor, 1, flag=wx.GROW)
            else:
                self.Editor = editor

        if self.SHOW_PARAMS and len(self.Controler.GetParamsAttributes()) > 0:

            panel_style = wx.TAB_TRAVERSAL | wx.HSCROLL | wx.VSCROLL
            if self.ConfNodeNoteBook is None and parent != self.Editor:
                panel_style |= wx.SUNKEN_BORDER
            self.ParamsEditor = wx.ScrolledWindow(parent,
                                                  style=panel_style)
            self.ParamsEditor.Bind(wx.EVT_SIZE, self.OnParamsEditorResize)
            self.ParamsEditor.Bind(wx.EVT_SCROLLWIN, self.OnParamsEditorScroll)

            self.ParamsEditorSizer = wx.FlexGridSizer(cols=1, hgap=0, rows=1, vgap=5)
            self.ParamsEditorSizer.AddGrowableCol(0)
            self.ParamsEditorSizer.AddGrowableRow(0)
            self.ParamsEditor.SetSizer(self.ParamsEditorSizer)

            self.ConfNodeParamsSizer = wx.BoxSizer(wx.VERTICAL)
            self.ParamsEditorSizer.AddSizer(self.ConfNodeParamsSizer, border=5,
                                            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM)

            self.RefreshConfNodeParamsSizer()

            if self.ConfNodeNoteBook is not None:
                self.ConfNodeNoteBook.AddPage(self.ParamsEditor, _("Config"))
            elif self.SHOW_BASE_PARAMS:
                self.MainSizer.AddWindow(self.ParamsEditor, 1, flag=wx.GROW)
            else:
                self.Editor = self.ParamsEditor
        else:
            self.ParamsEditor = None

    def __init__(self, parent, controler, window, tagname=""):
        EditorPanel.__init__(self, parent, tagname, window, controler)

        icon_name = self.Controler.GetIconName()
        if icon_name is not None:
            self.SetIcon(GetBitmap(icon_name))
        else:
            self.SetIcon(GetBitmap("Extension"))

    def __del__(self):
        self.Controler.OnCloseEditor(self)

    def GetTagName(self):
        return self.Controler.CTNFullName()

    def GetTitle(self):
        fullname = self.Controler.CTNFullName()
        if self.Controler.CTNTestModified():
            return "~%s~" % fullname
        return fullname

    def HasNoModel(self):
        return False

    def GetBufferState(self):
        return False, False

    def Undo(self):
        pass

    def Redo(self):
        pass

    def RefreshView(self):
        EditorPanel.RefreshView(self)
        if self.SHOW_BASE_PARAMS:
            self.ConfNodeName.ChangeValue(self.Controler.MandatoryParams[1].getName())
            self.RefreshIECChannelControlsState()
        if self.ParamsEditor is not None:
            self.RefreshConfNodeParamsSizer()
            self.RefreshScrollbars()

    def RefreshIECChannelControlsState(self):
        self.FullIECChannel.SetLabel(self.Controler.GetFullIEC_Channel())
        self.IECCDownButton.Enable(self.Controler.BaseParams.getIEC_Channel() > 0)
        self.MainSizer.Layout()

    def RefreshConfNodeParamsSizer(self):
        self.Freeze()
        self.ConfNodeParamsSizer.Clear(True)

        confnode_infos = self.Controler.GetParamsAttributes()
        if len(confnode_infos) > 0:
            self.GenerateSizerElements(self.ConfNodeParamsSizer, confnode_infos, None, False)

        self.ParamsEditorSizer.Layout()
        self.Thaw()

    def GenerateMethodButtonSizer(self):
        normal_bt_font = wx.Font(faces["size"] // 3,    wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName=faces["helv"])
        mouseover_bt_font = wx.Font(faces["size"] // 3, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName=faces["helv"], underline=True)

        msizer = wx.BoxSizer(wx.HORIZONTAL)

        for confnode_method in self.Controler.ConfNodeMethods:
            if "method" in confnode_method and confnode_method.get("shown", True):
                button = GenBitmapTextButton(self.Editor,
                                             bitmap=GetBitmap(confnode_method.get("bitmap", "Unknown")),
                                             label=confnode_method["name"],
                                             style=wx.NO_BORDER)
                button.SetFont(normal_bt_font)
                button.SetToolTipString(confnode_method["tooltip"])
                if confnode_method.get("push", False):
                    button.Bind(wx.EVT_LEFT_DOWN, self.GetButtonCallBackFunction(confnode_method["method"], True))
                else:
                    button.Bind(wx.EVT_BUTTON, self.GetButtonCallBackFunction(confnode_method["method"]), button)
                # a fancy underline on mouseover

                def setFontStyle(b, s):
                    def fn(event):
                        b.SetFont(s)
                        b.Refresh()
                        event.Skip()
                    return fn
                button.Bind(wx.EVT_ENTER_WINDOW, setFontStyle(button, mouseover_bt_font))
                button.Bind(wx.EVT_LEAVE_WINDOW, setFontStyle(button, normal_bt_font))
                # hack to force size to mini
                if not confnode_method.get("enabled", True):
                    button.Disable()
                msizer.AddWindow(button, flag=wx.ALIGN_CENTER)
        return msizer

    def UriOptions(self, event):
        CTR = self.ParentWindow.CTR
        CTR_BeremizRoot = CTR.BeremizRoot
        CTR_AppFrame = CTR.AppFrame

        # Get connector uri
        uri = CTR_BeremizRoot.getURI_location().strip()
        dialog = UriEditor(CTR_AppFrame, CTR, uri)

        if dialog.ShowModal() == wx.ID_OK:
            CTR_BeremizRoot.setURI_location(dialog.GetURI())
            if CTR._View is not None:
                CTR._View.RefreshView()
            if CTR_AppFrame is not None:
                CTR_AppFrame.RefreshTitle()
                CTR_AppFrame.RefreshFileMenu()
                CTR_AppFrame.RefreshEditMenu()
                CTR_AppFrame.RefreshPageTitles()

        dialog.Destroy()

    def GenerateSizerElements(self, sizer, elements, path, clean=True):
        if clean:
            sizer.Clear(True)
        first = True
        for element_infos in elements:
            if path:
                element_path = "%s.%s" % (path, element_infos["name"])
            else:
                element_path = element_infos["name"]
            if element_infos["type"] == "element":
                name = element_infos["name"]
                value = element_infos["value"]
                label = _(name)
                if value is not None:
                    label += " - %s" % _(value)
                staticbox = wx.StaticBox(self.ParamsEditor,
                                         label=_(label), size=wx.Size(10, 0))
                staticboxsizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
                flags = (wx.GROW | wx.BOTTOM | wx.LEFT | wx.RIGHT)
                if first:
                    flags |= wx.TOP
                sizer.AddSizer(staticboxsizer, border=5, flag=flags)
                self.GenerateSizerElements(staticboxsizer,
                                           element_infos["children"],
                                           element_path)
            else:
                boxsizer = wx.FlexGridSizer(cols=3, rows=1)
                boxsizer.AddGrowableCol(1)
                flags = (wx.GROW | wx.BOTTOM | wx.LEFT | wx.RIGHT)
                if first:
                    flags |= wx.TOP
                sizer.AddSizer(boxsizer, border=5, flag=flags)
                staticbitmap = GenStaticBitmap(
                    ID=-1, bitmapname=element_infos["name"],
                    name="%s_bitmap" % element_infos["name"], parent=self.ParamsEditor,
                    pos=wx.Point(0, 0), size=wx.Size(24, 24), style=0)
                boxsizer.AddWindow(staticbitmap, border=5, flag=wx.RIGHT)

                statictext = wx.StaticText(self.ParamsEditor,
                                           label="%s:" % _(element_infos["name"]))
                boxsizer.AddWindow(statictext, border=5,
                                   flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)

                if isinstance(element_infos["type"], list):
                    if isinstance(element_infos["value"], tuple):
                        browse_boxsizer = wx.BoxSizer(wx.HORIZONTAL)
                        boxsizer.AddSizer(browse_boxsizer)

                        textctrl = wx.TextCtrl(self.ParamsEditor,
                                               size=wx.Size(275, -1), style=wx.TE_READONLY)
                        if element_infos["value"] is not None:
                            textctrl.SetValue(element_infos["value"][0])
                            value_infos = element_infos["value"][1]
                        else:
                            value_infos = None
                        browse_boxsizer.AddWindow(textctrl)

                        button = wx.Button(self.ParamsEditor, label="...")
                        browse_boxsizer.AddWindow(button)
                        button.Bind(wx.EVT_BUTTON,
                                    self.GetBrowseCallBackFunction(element_infos["name"], textctrl, element_infos["type"],
                                                                   value_infos, element_path),
                                    button)
                    else:
                        combobox = wx.ComboBox(self.ParamsEditor,
                                               size=wx.Size(300, -1), style=wx.CB_READONLY)
                        boxsizer.AddWindow(combobox)

                        if element_infos["use"] == "optional":
                            combobox.Append("")
                        if len(element_infos["type"]) > 0 and isinstance(element_infos["type"][0], tuple):
                            for choice, _xsdclass in element_infos["type"]:
                                combobox.Append(choice)
                            name = element_infos["name"]
                            value = element_infos["value"]

                            staticbox = wx.StaticBox(self.ParamsEditor,
                                                     label="%s - %s" % (_(name), _(value)),
                                                     size=wx.Size(10, 0))
                            staticboxsizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
                            sizer.AddSizer(staticboxsizer, border=5, flag=wx.GROW | wx.BOTTOM | wx.LEFT | wx.RIGHT)
                            self.GenerateSizerElements(staticboxsizer, element_infos["children"], element_path)
                            callback = self.GetChoiceContentCallBackFunction(combobox, staticboxsizer, element_path)
                        else:
                            for choice in element_infos["type"]:
                                combobox.Append(choice)
                            callback = self.GetChoiceCallBackFunction(combobox, element_path)
                        if element_infos["value"] is None:
                            combobox.SetStringSelection("")
                        else:
                            combobox.SetStringSelection(element_infos["value"])
                        combobox.Bind(wx.EVT_COMBOBOX, callback, combobox)

                elif isinstance(element_infos["type"], dict):
                    scmin = -(2**31)
                    scmax = 2**31-1
                    if "min" in element_infos["type"]:
                        scmin = element_infos["type"]["min"]
                    if "max" in element_infos["type"]:
                        scmax = element_infos["type"]["max"]
                    spinctrl = wx.SpinCtrl(self.ParamsEditor,
                                           size=wx.Size(300, -1),
                                           style=wx.SP_ARROW_KEYS | wx.ALIGN_RIGHT)
                    spinctrl.SetRange(scmin, scmax)
                    boxsizer.AddWindow(spinctrl)
                    if element_infos["value"] is not None:
                        spinctrl.SetValue(element_infos["value"])
                    spinctrl.Bind(wx.EVT_SPINCTRL,
                                  self.GetTextCtrlCallBackFunction(spinctrl, element_path),
                                  spinctrl)

                else:
                    if element_infos["type"] == "boolean":
                        checkbox = wx.CheckBox(self.ParamsEditor, size=wx.Size(17, 25))
                        boxsizer.AddWindow(checkbox)
                        if element_infos["value"] is not None:
                            checkbox.SetValue(element_infos["value"])
                        checkbox.Bind(wx.EVT_CHECKBOX,
                                      self.GetCheckBoxCallBackFunction(checkbox, element_path),
                                      checkbox)

                    elif element_infos["type"] in ["unsignedLong", "long", "integer"]:
                        if element_infos["type"].startswith("unsigned"):
                            scmin = 0
                        else:
                            scmin = -(2**31)
                        scmax = 2**31-1
                        spinctrl = wx.SpinCtrl(self.ParamsEditor,
                                               size=wx.Size(300, -1),
                                               style=wx.SP_ARROW_KEYS | wx.ALIGN_RIGHT)
                        spinctrl.SetRange(scmin, scmax)
                        boxsizer.AddWindow(spinctrl)
                        if element_infos["value"] is not None:
                            spinctrl.SetValue(element_infos["value"])
                        spinctrl.Bind(wx.EVT_SPINCTRL,
                                      self.GetTextCtrlCallBackFunction(spinctrl, element_path),
                                      spinctrl)

                    else:
                        choices = self.ParentWindow.GetConfigEntry(element_path, [""])
                        textctrl = TextCtrlAutoComplete(name=element_infos["name"],
                                                        parent=self.ParamsEditor,
                                                        choices=choices,
                                                        element_path=element_path,
                                                        size=wx.Size(300, -1))

                        if element_infos["name"] == "URI_location":
                            uriSizer = wx.FlexGridSizer(cols=2, hgap=0, rows=1, vgap=0)
                            uriSizer.AddGrowableCol(0)
                            uriSizer.AddGrowableRow(0)

                            self.EditButton = wx.Button(self.ParamsEditor, label='...', size=wx.Size(30, -1))
                            self.Bind(wx.EVT_BUTTON, self.UriOptions, self.EditButton)

                            uriSizer.AddWindow(textctrl, flag=wx.GROW)
                            uriSizer.AddWindow(self.EditButton, flag=wx.GROW)

                            boxsizer.AddWindow(uriSizer)
                        else:
                            boxsizer.AddWindow(textctrl)

                        if element_infos["value"] is not None:
                            textctrl.ChangeValue(str(element_infos["value"]))
                        callback = self.GetTextCtrlCallBackFunction(textctrl, element_path)
                        textctrl.Bind(wx.EVT_TEXT_ENTER, callback)
                        textctrl.Bind(wx.EVT_TEXT, callback)
                        textctrl.Bind(wx.EVT_KILL_FOCUS, callback)
            first = False
        sizer.Layout()
        self.RefreshScrollbars()

    def GetItemChannelChangedFunction(self, dir):
        def OnConfNodeTreeItemChannelChanged(event):
            confnode_IECChannel = self.Controler.BaseParams.getIEC_Channel()
            self.SetConfNodeParamsAttribute("BaseParams.IEC_Channel", confnode_IECChannel + dir)
            wx.CallAfter(self.RefreshIECChannelControlsState)
            wx.CallAfter(self.ParentWindow._Refresh, TITLE, FILEMENU, PROJECTTREE)
            event.Skip()
        return OnConfNodeTreeItemChannelChanged

    def SetConfNodeParamsAttribute(self, *args, **kwargs):
        res, StructChanged = self.Controler.SetParamsAttribute(*args, **kwargs)
        if StructChanged and self.ParamsEditor is not None:
            wx.CallAfter(self.RefreshConfNodeParamsSizer)
        wx.CallAfter(self.ParentWindow._Refresh, TITLE, FILEMENU)
        return res

    def GetButtonCallBackFunction(self, method, push=False):
        """ Generate the callbackfunc for a given confnode method"""
        def OnButtonClick(event):
            # Disable button to prevent re-entrant call
            event.GetEventObject().Disable()
            # Call
            getattr(self.Controler, method)()
            # Re-enable button
            event.GetEventObject().Enable()

            if not push:
                event.Skip()
        return OnButtonClick

    def GetChoiceCallBackFunction(self, choicectrl, path):
        def OnChoiceChanged(event):
            res = self.SetConfNodeParamsAttribute(path, choicectrl.GetStringSelection())
            if res is None:
                res = ""
            choicectrl.SetStringSelection(res)
            event.Skip()
        return OnChoiceChanged

    def GetChoiceContentCallBackFunction(self, choicectrl, staticboxsizer, path):
        def OnChoiceContentChanged(event):
            self.SetConfNodeParamsAttribute(path, choicectrl.GetStringSelection())
            wx.CallAfter(self.RefreshConfNodeParamsSizer)
            event.Skip()
        return OnChoiceContentChanged

    def GetTextCtrlCallBackFunction(self, textctrl, path, refresh=False):
        def OnTextCtrlChanged(event):
            res = self.SetConfNodeParamsAttribute(path, textctrl.GetValue())
            if res != textctrl.GetValue():
                if isinstance(textctrl, wx.SpinCtrl):
                    textctrl.SetValue(res)
                elif res is not None:
                    textctrl.ChangeValue(str(res))
            if refresh:
                wx.CallAfter(self.ParentWindow._Refresh, TITLE, FILEMENU, PROJECTTREE, PAGETITLES)
                wx.CallAfter(self.ParentWindow.SelectProjectTreeItem, self.GetTagName())
            event.Skip()
        return OnTextCtrlChanged

    def GetCheckBoxCallBackFunction(self, chkbx, path):
        def OnCheckBoxChanged(event):
            res = self.SetConfNodeParamsAttribute(path, chkbx.IsChecked())
            chkbx.SetValue(res)
            event.Skip()
        return OnCheckBoxChanged

    def GetBrowseCallBackFunction(self, name, textctrl, library, value_infos, path):
        infos = [value_infos]

        def OnBrowseButton(event):
            dialog = BrowseValuesLibraryDialog(self, name, library, infos[0])
            if dialog.ShowModal() == wx.ID_OK:
                value, value_infos = self.SetConfNodeParamsAttribute(path, dialog.GetValueInfos())
                textctrl.ChangeValue(value)
                infos[0] = value_infos
            dialog.Destroy()
            event.Skip()
        return OnBrowseButton

    def RefreshScrollbars(self):
        self.ParamsEditor.GetBestSize()
        xstart, ystart = self.ParamsEditor.GetViewStart()
        window_size = self.ParamsEditor.GetClientSize()
        maxx, maxy = self.ParamsEditorSizer.GetMinSize()
        posx = max(0, min(xstart, (maxx - window_size[0]) // SCROLLBAR_UNIT))
        posy = max(0, min(ystart, (maxy - window_size[1]) // SCROLLBAR_UNIT))
        self.ParamsEditor.Scroll(posx, posy)
        self.ParamsEditor.SetScrollbars(SCROLLBAR_UNIT, SCROLLBAR_UNIT,
                                        maxx // SCROLLBAR_UNIT,
                                        maxy // SCROLLBAR_UNIT,
                                        posx, posy)

    def OnParamsEditorResize(self, event):
        self.RefreshScrollbars()
        event.Skip()

    def OnParamsEditorScroll(self, event):
        control = self.ParamsEditor.FindFocus()
        if isinstance(control, TextCtrlAutoComplete):
            control.DismissListBox()
            self.Refresh()
        event.Skip()
