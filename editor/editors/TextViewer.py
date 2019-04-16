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
import re
from functools import reduce

import wx
import wx.stc
from six.moves import xrange

from graphics.GraphicCommons import ERROR_HIGHLIGHT, SEARCH_RESULT_HIGHLIGHT, REFRESH_HIGHLIGHT_PERIOD
from plcopen.structures import ST_BLOCK_START_KEYWORDS, IEC_BLOCK_START_KEYWORDS, LOCATIONDATATYPES
from editors.EditorPanel import EditorPanel
from controls.CustomStyledTextCtrl import CustomStyledTextCtrl, faces, GetCursorPos

# -------------------------------------------------------------------------------
#                         Textual programs Viewer class
# -------------------------------------------------------------------------------


NEWLINE = "\n"
NUMBERS = [str(i) for i in xrange(10)]
LETTERS = ['_']
for i in xrange(26):
    LETTERS.append(chr(ord('a') + i))
    LETTERS.append(chr(ord('A') + i))

[STC_PLC_WORD, STC_PLC_COMMENT, STC_PLC_NUMBER, STC_PLC_STRING,
 STC_PLC_VARIABLE, STC_PLC_PARAMETER, STC_PLC_FUNCTION, STC_PLC_JUMP,
 STC_PLC_ERROR, STC_PLC_SEARCH_RESULT,
 STC_PLC_EMPTY] = range(11)
[SPACE, WORD, NUMBER, STRING, WSTRING, COMMENT, PRAGMA, DPRAGMA] = range(8)

[
    ID_TEXTVIEWER, ID_TEXTVIEWERTEXTCTRL,
] = [wx.NewId() for _init_ctrls in range(2)]

re_texts = {}
re_texts["letter"] = "[A-Za-z]"
re_texts["digit"] = "[0-9]"
re_texts["identifier"] = "((?:%(letter)s|(?:_(?:%(letter)s|%(digit)s)))(?:_?(?:%(letter)s|%(digit)s))*)" % re_texts
IDENTIFIER_MODEL = re.compile(re_texts["identifier"])
LABEL_MODEL = re.compile("[ \t\n]%(identifier)s:[ \t\n]" % re_texts)
EXTENSIBLE_PARAMETER = re.compile("IN[1-9][0-9]*$")

HIGHLIGHT_TYPES = {
    ERROR_HIGHLIGHT: STC_PLC_ERROR,
    SEARCH_RESULT_HIGHLIGHT: STC_PLC_SEARCH_RESULT,
}


def LineStartswith(line, symbols):
    return reduce(lambda x, y: x or y, map(line.startswith, symbols), False)


class TextViewer(EditorPanel):

    ID = ID_TEXTVIEWER

    def _init_Editor(self, prnt):
        self.Editor = CustomStyledTextCtrl(id=ID_TEXTVIEWERTEXTCTRL,
                                           parent=prnt, name="TextViewer", size=wx.Size(0, 0), style=0)
        self.Editor.ParentWindow = self

        self.Editor.CmdKeyAssign(ord('+'), wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMIN)
        self.Editor.CmdKeyAssign(ord('-'), wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_ZOOMOUT)

        self.Editor.SetViewWhiteSpace(False)

        self.Editor.SetLexer(wx.stc.STC_LEX_CONTAINER)

        # Global default styles for all languages
        self.Editor.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "face:%(mono)s,size:%(size)d" % faces)
        self.Editor.StyleClearAll()  # Reset all to be like the default

        self.Editor.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,size:%(size)d" % faces)
        self.Editor.SetSelBackground(1, "#E0E0E0")

        # Highlighting styles
        self.Editor.StyleSetSpec(STC_PLC_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_VARIABLE, "fore:#7F0000,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_PARAMETER, "fore:#7F007F,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_FUNCTION, "fore:#7F7F00,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_COMMENT, "fore:#7F7F7F,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_NUMBER, "fore:#007F7F,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_STRING, "fore:#007F00,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_JUMP, "fore:#FF7FFF,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_ERROR, "fore:#FF0000,back:#FFFF00,size:%(size)d" % faces)
        self.Editor.StyleSetSpec(STC_PLC_SEARCH_RESULT, "fore:#FFFFFF,back:#FFA500,size:%(size)d" % faces)

        # Indicators styles
        self.Editor.IndicatorSetStyle(0, wx.stc.STC_INDIC_SQUIGGLE)
        if self.ParentWindow is not None and self.Controler is not None:
            self.Editor.IndicatorSetForeground(0, wx.RED)
        else:
            self.Editor.IndicatorSetForeground(0, wx.WHITE)

        # Line numbers in the margin
        self.Editor.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.Editor.SetMarginWidth(1, 50)

        # Folding
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,    wx.stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,        wx.stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,     wx.stc.STC_MARK_VLINE,             "white", "#808080")
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,    wx.stc.STC_MARK_LCORNER,           "white", "#808080")
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,     wx.stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.Editor.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_TCORNER,           "white", "#808080")

        # Indentation size
        self.Editor.SetTabWidth(2)
        self.Editor.SetUseTabs(0)

        self.Editor.SetModEventMask(wx.stc.STC_MOD_BEFOREINSERT |
                                    wx.stc.STC_MOD_BEFOREDELETE |
                                    wx.stc.STC_PERFORMED_USER)

        self.Bind(wx.stc.EVT_STC_STYLENEEDED, self.OnStyleNeeded, id=ID_TEXTVIEWERTEXTCTRL)
        self.Editor.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Editor.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        if self.Controler is not None:
            self.Editor.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
            self.Bind(wx.stc.EVT_STC_DO_DROP, self.OnDoDrop, id=ID_TEXTVIEWERTEXTCTRL)
            self.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModification, id=ID_TEXTVIEWERTEXTCTRL)

    def __init__(self, parent, tagname, window, controler, debug=False, instancepath=""):
        if tagname != "" and controler is not None:
            self.VARIABLE_PANEL_TYPE = controler.GetPouType(tagname.split("::")[1])

        EditorPanel.__init__(self, parent, tagname, window, controler, debug)

        self.Keywords = []
        self.Variables = {}
        self.Functions = {}
        self.TypeNames = []
        self.Jumps = []
        self.EnumeratedValues = []
        self.DisableEvents = True
        self.TextSyntax = None
        self.CurrentAction = None

        self.InstancePath = instancepath
        self.ContextStack = []
        self.CallStack = []

        self.ResetSearchResults()

        self.RefreshHighlightsTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnRefreshHighlightsTimer, self.RefreshHighlightsTimer)

    def __del__(self):
        self.RefreshHighlightsTimer.Stop()

    def GetTitle(self):
        if self.Debug or self.TagName == "":
            if len(self.InstancePath) > 15:
                return "..." + self.InstancePath[-12:]
            return self.InstancePath
        return EditorPanel.GetTitle(self)

    def GetInstancePath(self):
        return self.InstancePath

    def IsViewing(self, tagname):
        if self.Debug or self.TagName == "":
            return self.InstancePath == tagname
        else:
            return self.TagName == tagname

    def GetText(self):
        return self.Editor.GetText()

    def SetText(self, text):
        self.Editor.SetText(text)

    def SelectAll(self):
        self.Editor.SelectAll()

    def Colourise(self, start, end):
        self.Editor.Colourise(start, end)

    def StartStyling(self, pos, mask):
        self.Editor.StartStyling(pos, mask)

    def SetStyling(self, length, style):
        self.Editor.SetStyling(length, style)

    def GetCurrentPos(self):
        return self.Editor.GetCurrentPos()

    def ResetSearchResults(self):
        self.Highlights = []
        self.SearchParams = None
        self.SearchResults = None
        self.CurrentFindHighlight = None

    def OnModification(self, event):
        if not self.DisableEvents:
            mod_type = event.GetModificationType()
            if mod_type & wx.stc.STC_MOD_BEFOREINSERT:
                if self.CurrentAction is None:
                    self.StartBuffering()
                elif self.CurrentAction[0] != "Add" or self.CurrentAction[1] != event.GetPosition() - 1:
                    self.Controler.EndBuffering()
                    self.StartBuffering()
                self.CurrentAction = ("Add", event.GetPosition())
                wx.CallAfter(self.RefreshModel)
            elif mod_type & wx.stc.STC_MOD_BEFOREDELETE:
                if self.CurrentAction is None:
                    self.StartBuffering()
                elif self.CurrentAction[0] != "Delete" or self.CurrentAction[1] != event.GetPosition() + 1:
                    self.Controler.EndBuffering()
                    self.StartBuffering()
                self.CurrentAction = ("Delete", event.GetPosition())
                wx.CallAfter(self.RefreshModel)
        event.Skip()

    def OnDoDrop(self, event):
        try:
            values = eval(event.GetDragText())
        except Exception:
            values = event.GetDragText()
        if isinstance(values, tuple):
            message = None
            if values[1] in ["program", "debug"]:
                event.SetDragText("")
            elif values[1] in ["functionBlock", "function"]:
                blocktype = values[0]
                blockname = values[2]
                if len(values) > 3:
                    blockinputs = values[3]
                else:
                    blockinputs = None
                if values[1] != "function":
                    if blockname == "":
                        dialog = wx.TextEntryDialog(self.ParentWindow, _("Block name"), _("Please enter a block name"), "", wx.OK | wx.CANCEL | wx.CENTRE)
                        if dialog.ShowModal() == wx.ID_OK:
                            blockname = dialog.GetValue()
                        else:
                            event.SetDragText("")
                            return
                        dialog.Destroy()
                    if blockname.upper() in [name.upper() for name in self.Controler.GetProjectPouNames(self.Debug)]:
                        message = _("\"%s\" pou already exists!") % blockname
                    elif blockname.upper() in [name.upper() for name in self.Controler.GetEditedElementVariables(self.TagName, self.Debug)]:
                        message = _("\"%s\" element for this pou already exists!") % blockname
                    else:
                        self.Controler.AddEditedElementPouVar(self.TagName, values[0], blockname)
                        self.RefreshVariablePanel()
                        self.RefreshVariableTree()
                blockinfo = self.Controler.GetBlockType(blocktype, blockinputs, self.Debug)
                hint = ',\n    '.join(
                    [" " + fctdecl[0]+" := (*"+fctdecl[1]+"*)" for fctdecl in blockinfo["inputs"]] +
                    [" " + fctdecl[0]+" => (*"+fctdecl[1]+"*)" for fctdecl in blockinfo["outputs"]])
                if values[1] == "function":
                    event.SetDragText(blocktype+"(\n    "+hint+")")
                else:
                    event.SetDragText(blockname+"(\n    "+hint+")")
            elif values[1] == "location":
                _pou_name, pou_type = self.Controler.GetEditedElementType(self.TagName, self.Debug)
                if len(values) > 2 and pou_type == "program":
                    var_name = values[3]
                    dlg = wx.TextEntryDialog(
                        self.ParentWindow,
                        _("Confirm or change variable name"),
                        _('Variable Drop'), var_name)
                    dlg.SetValue(var_name)
                    var_name = dlg.GetValue() if dlg.ShowModal() == wx.ID_OK else None
                    dlg.Destroy()
                    if var_name is None:
                        return
                    elif var_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames(self.Debug)]:
                        message = _("\"%s\" pou already exists!") % var_name
                    elif var_name.upper() in [name.upper() for name in self.Controler.GetEditedElementVariables(self.TagName, self.Debug)]:
                        message = _("\"%s\" element for this pou already exists!") % var_name
                    else:
                        location = values[0]
                        if not location.startswith("%"):
                            dialog = wx.SingleChoiceDialog(
                                self.ParentWindow,
                                _("Select a variable class:"),
                                _("Variable class"),
                                [_("Input"), _("Output"), _("Memory")],
                                wx.DEFAULT_DIALOG_STYLE | wx.OK | wx.CANCEL)
                            if dialog.ShowModal() == wx.ID_OK:
                                selected = dialog.GetSelection()
                            else:
                                selected = None
                            dialog.Destroy()
                            if selected is None:
                                event.SetDragText("")
                                return
                            if selected == 0:
                                location = "%I" + location
                            elif selected == 1:
                                location = "%Q" + location
                            else:
                                location = "%M" + location
                        if values[2] is not None:
                            var_type = values[2]
                        else:
                            var_type = LOCATIONDATATYPES.get(location[2], ["BOOL"])[0]
                        self.Controler.AddEditedElementPouVar(
                            self.TagName,
                            var_type, var_name,
                            location=location, description=values[4])
                        self.RefreshVariablePanel()
                        self.RefreshVariableTree()
                        event.SetDragText(var_name)
                else:
                    event.SetDragText("")
            elif values[1] == "NamedConstant":
                _pou_name, pou_type = self.Controler.GetEditedElementType(self.TagName, self.Debug)
                if pou_type == "program":
                    initval = values[0]
                    var_name = values[3]
                    dlg = wx.TextEntryDialog(
                        self.ParentWindow,
                        _("Confirm or change variable name"),
                        _('Variable Drop'), var_name)
                    dlg.SetValue(var_name)
                    var_name = dlg.GetValue() if dlg.ShowModal() == wx.ID_OK else None
                    dlg.Destroy()
                    if var_name is None:
                        return
                    elif var_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames(self.Debug)]:
                        message = _("\"%s\" pou already exists!") % var_name
                    else:
                        var_type = values[2]
                        if not var_name.upper() in [name.upper() for name in self.Controler.GetEditedElementVariables(self.TagName, self.Debug)]:
                            self.Controler.AddEditedElementPouVar(self.TagName,
                                                                  var_type,
                                                                  var_name,
                                                                  description=values[4], initval=initval)
                            self.RefreshVariablePanel()
                            self.RefreshVariableTree()
                        event.SetDragText(var_name)
            elif values[1] == "Global":
                var_name = values[0]
                dlg = wx.TextEntryDialog(
                    self.ParentWindow,
                    _("Confirm or change variable name"),
                    _('Variable Drop'), var_name)
                dlg.SetValue(var_name)
                var_name = dlg.GetValue() if dlg.ShowModal() == wx.ID_OK else None
                dlg.Destroy()
                if var_name is None:
                    return
                elif var_name.upper() in [name.upper() for name in self.Controler.GetProjectPouNames(self.Debug)]:
                    message = _("\"%s\" pou already exists!") % var_name
                else:
                    if not var_name.upper() in [name.upper() for name in self.Controler.GetEditedElementVariables(self.TagName, self.Debug)]:
                        self.Controler.AddEditedElementPouExternalVar(self.TagName, values[2], var_name)
                        self.RefreshVariablePanel()
                        self.RefreshVariableTree()
                    event.SetDragText(var_name)
            elif values[1] == "Constant":
                event.SetDragText(values[0])
            elif values[3] == self.TagName:
                self.ResetBuffer()
                event.SetDragText(values[0])
                wx.CallAfter(self.RefreshModel)
            else:
                message = _("Variable don't belong to this POU!")
            if message is not None:
                dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
                dialog.ShowModal()
                dialog.Destroy()
                event.SetDragText("")
        event.Skip()

    def SetTextSyntax(self, syntax):
        self.TextSyntax = syntax
        if syntax in ["ST", "ALL"]:
            self.Editor.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
            self.Editor.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
            self.Editor.SetMarginSensitive(2, 1)
            self.Editor.SetMarginWidth(2, 12)
            if syntax == "ST":
                self.BlockStartKeywords = ST_BLOCK_START_KEYWORDS
                self.BlockEndKeywords = ST_BLOCK_START_KEYWORDS
            else:
                self.BlockStartKeywords = IEC_BLOCK_START_KEYWORDS
                self.BlockEndKeywords = IEC_BLOCK_START_KEYWORDS
        else:
            self.BlockStartKeywords = []
            self.BlockEndKeywords = []

    def SetKeywords(self, keywords):
        self.Keywords = [keyword.upper() for keyword in keywords]
        self.Colourise(0, -1)

    def RefreshJumpList(self):
        if self.TextSyntax == "IL":
            self.Jumps = [jump.upper() for jump in LABEL_MODEL.findall(self.GetText())]

    # Buffer the last model state
    def RefreshBuffer(self):
        self.Controler.BufferProject()
        if self.ParentWindow:
            self.ParentWindow.RefreshTitle()
            self.ParentWindow.RefreshFileMenu()
            self.ParentWindow.RefreshEditMenu()

    def StartBuffering(self):
        self.Controler.StartBuffering()
        if self.ParentWindow:
            self.ParentWindow.RefreshTitle()
            self.ParentWindow.RefreshFileMenu()
            self.ParentWindow.RefreshEditMenu()

    def ResetBuffer(self):
        if self.CurrentAction is not None:
            self.Controler.EndBuffering()
            self.CurrentAction = None

    def GetBufferState(self):
        if not self.Debug and self.TextSyntax != "ALL":
            return self.Controler.GetBufferState()
        return False, False

    def Undo(self):
        if not self.Debug and self.TextSyntax != "ALL":
            self.Controler.LoadPrevious()
            self.ParentWindow.CloseTabsWithoutModel()

    def Redo(self):
        if not self.Debug and self.TextSyntax != "ALL":
            self.Controler.LoadNext()
            self.ParentWindow.CloseTabsWithoutModel()

    def HasNoModel(self):
        if not self.Debug and self.TextSyntax != "ALL":
            return self.Controler.GetEditedElement(self.TagName) is None
        return False

    def RefreshView(self, variablepanel=True):
        EditorPanel.RefreshView(self, variablepanel)

        if self.Controler is not None:
            self.ResetBuffer()
            self.DisableEvents = True
            old_cursor_pos = self.GetCurrentPos()
            line = self.Editor.GetFirstVisibleLine()
            column = self.Editor.GetXOffset()
            old_text = self.GetText()
            new_text = self.Controler.GetEditedElementText(self.TagName, self.Debug)
            if old_text != new_text:
                self.SetText(new_text)
                new_cursor_pos = GetCursorPos(old_text, new_text)
                self.Editor.LineScroll(column, line)
                if new_cursor_pos is not None:
                    self.Editor.GotoPos(new_cursor_pos)
                else:
                    self.Editor.GotoPos(old_cursor_pos)
                self.RefreshJumpList()
                self.Editor.EmptyUndoBuffer()
            self.DisableEvents = False

            self.RefreshVariableTree()

            self.TypeNames = [typename.upper() for typename in self.Controler.GetDataTypes(self.TagName, True, self.Debug)]
            self.EnumeratedValues = [value.upper() for value in self.Controler.GetEnumeratedDataValues()]

            self.Functions = {}
            for category in self.Controler.GetBlockTypes(self.TagName, self.Debug):
                for blocktype in category["list"]:
                    blockname = blocktype["name"].upper()
                    if blocktype["type"] == "function" and blockname not in self.Keywords and blockname not in self.Variables.keys():
                        interface = dict([(name, {}) for name, _type, _modifier in blocktype["inputs"] + blocktype["outputs"] if name != ''])
                        for param in ["EN", "ENO"]:
                            if param not in interface:
                                interface[param] = {}
                        if blockname in self.Functions:
                            self.Functions[blockname]["interface"].update(interface)
                            self.Functions[blockname]["extensible"] |= blocktype["extensible"]
                        else:
                            self.Functions[blockname] = {"interface": interface,
                                                         "extensible": blocktype["extensible"]}

        self.Colourise(0, -1)

    def RefreshVariableTree(self):
        words = self.TagName.split("::")
        self.Variables = self.GenerateVariableTree([
            (variable.Name, variable.Type, variable.Tree)
            for variable in
            self.Controler.GetEditedElementInterfaceVars(
                self.TagName, True, self.Debug)
        ])
        if self.Controler.GetEditedElementType(self.TagName, self.Debug)[1] == "function" or words[0] == "T" and self.TextSyntax == "IL":
            return_type, (var_tree, _var_dimension) = self.Controler.GetEditedElementInterfaceReturnType(self.TagName, True, self.Debug)
            if return_type is not None:
                self.Variables[words[-1].upper()] = self.GenerateVariableTree(var_tree)
            else:
                self.Variables[words[-1].upper()] = {}

    def GenerateVariableTree(self, list):
        tree = {}
        for var_name, _var_type, (var_tree, _var_dimension) in list:
            tree[var_name.upper()] = self.GenerateVariableTree(var_tree)
        return tree

    def IsValidVariable(self, name, context):
        return context is not None and context.get(name, None) is not None

    def IsCallParameter(self, name, call):
        if call is not None:
            return (call["interface"].get(name.upper(), None) is not None or
                    call["extensible"] and EXTENSIBLE_PARAMETER.match(name.upper()) is not None)
        return False

    def RefreshLineFolding(self, line_number):
        if self.TextSyntax in ["ST", "ALL"]:
            level = wx.stc.STC_FOLDLEVELBASE + self.Editor.GetLineIndentation(line_number)
            line = self.Editor.GetLine(line_number).strip()
            if line == "":
                if line_number > 0:
                    if LineStartswith(self.Editor.GetLine(line_number - 1).strip(), self.BlockEndKeywords):
                        level = self.Editor.GetFoldLevel(self.Editor.GetFoldParent(line_number - 1)) & wx.stc.STC_FOLDLEVELNUMBERMASK
                    else:
                        level = self.Editor.GetFoldLevel(line_number - 1) & wx.stc.STC_FOLDLEVELNUMBERMASK
                if level != wx.stc.STC_FOLDLEVELBASE:
                    level |= wx.stc.STC_FOLDLEVELWHITEFLAG
            elif LineStartswith(line, self.BlockStartKeywords):
                level |= wx.stc.STC_FOLDLEVELHEADERFLAG
            elif LineStartswith(line, self.BlockEndKeywords):
                if LineStartswith(self.Editor.GetLine(line_number - 1).strip(), self.BlockEndKeywords):
                    level = self.Editor.GetFoldLevel(self.Editor.GetFoldParent(line_number - 1)) & wx.stc.STC_FOLDLEVELNUMBERMASK
                else:
                    level = self.Editor.GetFoldLevel(line_number - 1) & wx.stc.STC_FOLDLEVELNUMBERMASK
            self.Editor.SetFoldLevel(line_number, level)

    def OnStyleNeeded(self, event):
        self.TextChanged = True
        line_number = self.Editor.LineFromPosition(self.Editor.GetEndStyled())
        if line_number == 0:
            start_pos = last_styled_pos = 0
        else:
            start_pos = last_styled_pos = self.Editor.GetLineEndPosition(line_number - 1) + 1
        self.RefreshLineFolding(line_number)
        end_pos = event.GetPosition()
        self.StartStyling(start_pos, 0xff)

        current_context = self.Variables
        current_call = None

        current_pos = last_styled_pos
        state = SPACE
        line = ""
        word = ""
        while current_pos < end_pos:
            char = chr(self.Editor.GetCharAt(current_pos)).upper()
            line += char
            if char == NEWLINE:
                self.ContextStack = []
                current_context = self.Variables
                if state == COMMENT:
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_COMMENT)
                elif state == NUMBER:
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_NUMBER)
                elif state == WORD:
                    if word in self.Keywords or word in self.TypeNames:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_WORD)
                    elif self.IsValidVariable(word, current_context):
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_VARIABLE)
                    elif self.IsCallParameter(word, current_call):
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_PARAMETER)
                    elif word in self.Functions:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_FUNCTION)
                    elif self.TextSyntax == "IL" and word in self.Jumps:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_JUMP)
                    elif word in self.EnumeratedValues:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_NUMBER)
                    else:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                        if word not in ["]", ")"] and (self.GetCurrentPos() < last_styled_pos or self.GetCurrentPos() > current_pos):
                            self.StartStyling(last_styled_pos, wx.stc.STC_INDICS_MASK)
                            self.SetStyling(current_pos - last_styled_pos, wx.stc.STC_INDIC0_MASK)
                            self.StartStyling(current_pos, 0xff)
                else:
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                last_styled_pos = current_pos
                if (state != DPRAGMA) and (state != COMMENT):
                    state = SPACE
                line = ""
                line_number += 1
                self.RefreshLineFolding(line_number)
            elif line.endswith("(*") and state != COMMENT:
                self.SetStyling(current_pos - last_styled_pos - 1, STC_PLC_EMPTY)
                last_styled_pos = current_pos
                if state == WORD:
                    current_context = self.Variables
                state = COMMENT
            elif line.endswith("{") and state not in [PRAGMA, DPRAGMA]:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                last_styled_pos = current_pos
                if state == WORD:
                    current_context = self.Variables
                state = PRAGMA
            elif line.endswith("{{") and state == PRAGMA:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                last_styled_pos = current_pos
                state = DPRAGMA
            elif state == COMMENT:
                if line.endswith("*)"):
                    self.SetStyling(current_pos - last_styled_pos + 2, STC_PLC_COMMENT)
                    last_styled_pos = current_pos + 1
                    state = SPACE
                    if len(self.CallStack) > 0:
                        current_call = self.CallStack.pop()
                    else:
                        current_call = None
            elif state == PRAGMA:
                if line.endswith("}"):
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                    last_styled_pos = current_pos
                    state = SPACE
            elif state == DPRAGMA:
                if line.endswith("}}"):
                    self.SetStyling(current_pos - last_styled_pos + 1, STC_PLC_EMPTY)
                    last_styled_pos = current_pos + 1
                    state = SPACE
            elif (line.endswith("'") or line.endswith('"')) and state not in [STRING, WSTRING]:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                last_styled_pos = current_pos
                if state == WORD:
                    current_context = self.Variables
                if line.endswith("'"):
                    state = STRING
                else:
                    state = WSTRING
            elif state == STRING:
                if line.endswith("'") and not line.endswith("$'"):
                    self.SetStyling(current_pos - last_styled_pos + 1, STC_PLC_STRING)
                    last_styled_pos = current_pos + 1
                    state = SPACE
            elif state == WSTRING:
                if line.endswith('"') and not line.endswith('$"'):
                    self.SetStyling(current_pos - last_styled_pos + 1, STC_PLC_STRING)
                    last_styled_pos = current_pos + 1
                    state = SPACE
            elif char in LETTERS:
                if state == NUMBER:
                    word = "#"
                    state = WORD
                elif state == SPACE:
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                    word = char
                    last_styled_pos = current_pos
                    state = WORD
                else:
                    word += char
            elif char in NUMBERS or char == '.' and state != WORD:
                if state == SPACE:
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                    last_styled_pos = current_pos
                    state = NUMBER
                elif state == WORD and char != '.':
                    word += char
            elif char == '(' and state == SPACE:
                self.CallStack.append(current_call)
                current_call = None
            else:
                if state == WORD:
                    if word in self.Keywords or word in self.TypeNames:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_WORD)
                    elif self.IsValidVariable(word, current_context):
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_VARIABLE)
                    elif self.IsCallParameter(word, current_call):
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_PARAMETER)
                    elif word in self.Functions:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_FUNCTION)
                    elif self.TextSyntax == "IL" and word in self.Jumps:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_JUMP)
                    elif word in self.EnumeratedValues:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_NUMBER)
                    else:
                        self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
                        if word not in ["]", ")"] and (self.GetCurrentPos() < last_styled_pos or self.GetCurrentPos() > current_pos):
                            self.StartStyling(last_styled_pos, wx.stc.STC_INDICS_MASK)
                            self.SetStyling(current_pos - last_styled_pos, wx.stc.STC_INDIC0_MASK)
                            self.StartStyling(current_pos, 0xff)
                    if char == '.':
                        if word != "]":
                            if current_context is not None:
                                current_context = current_context.get(word, None)
                            else:
                                current_context = None
                    elif char == '(':
                        self.CallStack.append(current_call)
                        current_call = self.Functions.get(word, None)
                        if current_call is None and self.IsValidVariable(word, current_context):
                            current_call = {"interface": current_context.get(word, {}),
                                            "extensible": False}
                        current_context = self.Variables
                    else:
                        if char == '[' and current_context is not None:
                            self.ContextStack.append(current_context.get(word, None))
                        current_context = self.Variables

                    word = ""
                    last_styled_pos = current_pos
                    state = SPACE
                elif state == NUMBER:
                    self.SetStyling(current_pos - last_styled_pos, STC_PLC_NUMBER)
                    last_styled_pos = current_pos
                    state = SPACE
                if char == ']':
                    if len(self.ContextStack) > 0:
                        current_context = self.ContextStack.pop()
                    else:
                        current_context = self.Variables
                    word = char
                    state = WORD
                elif char == ')':
                    current_context = self.Variables
                    if len(self.CallStack) > 0:
                        current_call = self.CallStack.pop()
                    else:
                        current_call = None
                    word = char
                    state = WORD
            current_pos += 1
        if state == COMMENT:
            self.SetStyling(current_pos - last_styled_pos + 2, STC_PLC_COMMENT)
        elif state == NUMBER:
            self.SetStyling(current_pos - last_styled_pos, STC_PLC_NUMBER)
        elif state == WORD:
            if word in self.Keywords or word in self.TypeNames:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_WORD)
            elif self.IsValidVariable(word, current_context):
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_VARIABLE)
            elif self.IsCallParameter(word, current_call):
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_PARAMETER)
            elif self.TextSyntax == "IL" and word in self.Functions:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_FUNCTION)
            elif word in self.Jumps:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_JUMP)
            elif word in self.EnumeratedValues:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_NUMBER)
            else:
                self.SetStyling(current_pos - last_styled_pos, STC_PLC_EMPTY)
        else:
            self.SetStyling(current_pos - start_pos, STC_PLC_EMPTY)
        self.ShowHighlights(start_pos, end_pos)
        event.Skip()

    def OnMarginClick(self, event):
        if event.GetMargin() == 2:
            line = self.Editor.LineFromPosition(event.GetPosition())
            if self.Editor.GetFoldLevel(line) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                self.Editor.ToggleFold(line)
        event.Skip()

    def OnUpdateUI(self, event):
        selected = self.Editor.GetSelectedText()
        if self.ParentWindow and selected != "":
            self.ParentWindow.SetCopyBuffer(selected, True)
        event.Skip()

    def Cut(self):
        self.ResetBuffer()
        self.DisableEvents = True
        self.Editor.CmdKeyExecute(wx.stc.STC_CMD_CUT)
        self.DisableEvents = False
        self.RefreshModel()
        self.RefreshBuffer()

    def Copy(self):
        self.Editor.CmdKeyExecute(wx.stc.STC_CMD_COPY)
        if self.ParentWindow:
            self.ParentWindow.RefreshEditMenu()

    def Paste(self):
        self.ResetBuffer()
        self.DisableEvents = True
        self.Editor.CmdKeyExecute(wx.stc.STC_CMD_PASTE)
        self.DisableEvents = False
        self.RefreshModel()
        self.RefreshBuffer()

    def Search(self, criteria):
        return self.Controler.SearchInPou(self.TagName, criteria, self.Debug)

    def Find(self, direction, search_params):
        if self.SearchParams != search_params:
            self.ClearHighlights(SEARCH_RESULT_HIGHLIGHT)

            self.SearchParams = search_params
            self.SearchResults = [
                (infos[1:], start, end, SEARCH_RESULT_HIGHLIGHT)
                for infos, start, end, _text in
                self.Search(search_params)]
            self.CurrentFindHighlight = None

        if len(self.SearchResults) > 0:
            if self.CurrentFindHighlight is not None:
                old_idx = self.SearchResults.index(self.CurrentFindHighlight)
                if self.SearchParams["wrap"]:
                    idx = (old_idx + direction) % len(self.SearchResults)
                else:
                    idx = max(0, min(old_idx + direction, len(self.SearchResults) - 1))
                if idx != old_idx:
                    self.RemoveHighlight(*self.CurrentFindHighlight)
                    self.CurrentFindHighlight = self.SearchResults[idx]
                    self.AddHighlight(*self.CurrentFindHighlight)
            else:
                self.CurrentFindHighlight = self.SearchResults[0]
                self.AddHighlight(*self.CurrentFindHighlight)

        else:
            if self.CurrentFindHighlight is not None:
                self.RemoveHighlight(*self.CurrentFindHighlight)
            self.CurrentFindHighlight = None

    def RefreshModel(self):
        self.RefreshJumpList()
        self.Colourise(0, -1)
        self.Controler.SetEditedElementText(self.TagName, self.GetText())
        self.ResetSearchResults()

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        if self.Controler is not None:

            if self.Editor.CallTipActive():
                self.Editor.CallTipCancel()

            key_handled = False

            line = self.Editor.GetCurrentLine()
            if line == 0:
                start_pos = 0
            else:
                start_pos = self.Editor.GetLineEndPosition(line - 1) + 1
            end_pos = self.GetCurrentPos()
            lineText = self.Editor.GetTextRange(start_pos, end_pos).replace("\t", " ")

            # Code completion
            if key == wx.WXK_SPACE and event.ControlDown():

                words = lineText.split(" ")
                words = [word for i, word in enumerate(words) if word != '' or i == len(words) - 1]

                kw = []

                if self.TextSyntax == "IL":
                    if len(words) == 1:
                        kw = self.Keywords
                    elif len(words) == 2:
                        if words[0].upper() in ["CAL", "CALC", "CALNC"]:
                            kw = self.Functions
                        elif words[0].upper() in ["JMP", "JMPC", "JMPNC"]:
                            kw = self.Jumps
                        else:
                            kw = self.Variables.keys()
                else:
                    kw = self.Keywords + self.Variables.keys() + self.Functions.keys()
                if len(kw) > 0:
                    if len(words[-1]) > 0:
                        kw = [keyword for keyword in kw if keyword.startswith(words[-1])]
                    kw.sort()
                    self.Editor.AutoCompSetIgnoreCase(True)
                    self.Editor.AutoCompShow(len(words[-1]), " ".join(kw))
                key_handled = True
            elif key == wx.WXK_RETURN or key == wx.WXK_NUMPAD_ENTER:
                if self.TextSyntax in ["ST", "ALL"]:
                    indent = self.Editor.GetLineIndentation(line)
                    if LineStartswith(lineText.strip(), self.BlockStartKeywords):
                        indent = (indent // 2 + 1) * 2
                    self.Editor.AddText("\n" + " " * indent)
                    key_handled = True
            elif key == wx.WXK_BACK:
                if self.TextSyntax in ["ST", "ALL"]:
                    if not self.Editor.GetSelectedText():
                        indent = self.Editor.GetColumn(self.Editor.GetCurrentPos())
                        if lineText.strip() == "" and len(lineText) > 0 and indent > 0:
                            self.Editor.DelLineLeft()
                            self.Editor.AddText(" " * ((max(0, indent - 1) // 2) * 2))
                            key_handled = True
            if not key_handled:
                event.Skip()
        else:
            event.Skip()

    def OnKillFocus(self, event):
        self.Editor.AutoCompCancel()
        event.Skip()

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def OnRefreshHighlightsTimer(self, event):
        self.RefreshView()
        event.Skip()

    def ClearHighlights(self, highlight_type=None):
        EditorPanel.ClearHighlights(self, highlight_type)

        if highlight_type is None:
            self.Highlights = []
        else:
            highlight_type = HIGHLIGHT_TYPES.get(highlight_type, None)
            if highlight_type is not None:
                self.Highlights = [(infos, start, end, highlight) for (infos, start, end, highlight) in self.Highlights if highlight != highlight_type]
        self.RefreshView()

    def AddHighlight(self, infos, start, end, highlight_type):
        EditorPanel.AddHighlight(self, infos, start, end, highlight_type)

        highlight_type = HIGHLIGHT_TYPES.get(highlight_type, None)
        if infos[0] == "body" and highlight_type is not None:
            self.Highlights.append((infos[1], start, end, highlight_type))
            self.Editor.GotoPos(self.Editor.PositionFromLine(start[0]) + start[1])
            self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def RemoveHighlight(self, infos, start, end, highlight_type):
        EditorPanel.RemoveHighlight(self, infos, start, end, highlight_type)

        highlight_type = HIGHLIGHT_TYPES.get(highlight_type, None)
        if infos[0] == "body" and highlight_type is not None and \
           (infos[1], start, end, highlight_type) in self.Highlights:
            self.Highlights.remove((infos[1], start, end, highlight_type))
            self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def ShowHighlights(self, start_pos, end_pos):
        for indent, start, end, highlight_type in self.Highlights:
            if start[0] == 0:
                highlight_start_pos = start[1] - indent
            else:
                highlight_start_pos = self.Editor.GetLineEndPosition(start[0] - 1) + start[1] - indent + 1
            if end[0] == 0:
                highlight_end_pos = end[1] - indent + 1
            else:
                highlight_end_pos = self.Editor.GetLineEndPosition(end[0] - 1) + end[1] - indent + 2
            if highlight_start_pos < end_pos and highlight_end_pos > start_pos:
                self.StartStyling(highlight_start_pos, 0xff)
                self.SetStyling(highlight_end_pos - highlight_start_pos, highlight_type)
                self.StartStyling(highlight_start_pos, 0x00)
                until_end = max(0, len(self.Editor.GetText()) - highlight_end_pos)
                self.SetStyling(until_end, wx.stc.STC_STYLE_DEFAULT)
