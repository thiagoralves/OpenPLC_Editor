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
from builtins import str as text

import wx
import wx.grid
import wx.stc as stc
import wx.lib.buttons
from six.moves import xrange


from plcopen.plcopen import TestTextElement
from plcopen.structures import TestIdentifier, IEC_KEYWORDS, DefaultType
from controls import CustomGrid, CustomTable
from controls.CustomStyledTextCtrl import CustomStyledTextCtrl, faces, GetCursorPos, NAVIGATION_KEYS
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor
from util.BitmapLibrary import GetBitmap
from util.TranslationCatalogs import NoTranslate
from graphics.GraphicCommons import ERROR_HIGHLIGHT, SEARCH_RESULT_HIGHLIGHT, REFRESH_HIGHLIGHT_PERIOD


[STC_CODE_ERROR, STC_CODE_SEARCH_RESULT,
 STC_CODE_SECTION] = range(15, 18)

HIGHLIGHT_TYPES = {
    ERROR_HIGHLIGHT: STC_CODE_ERROR,
    SEARCH_RESULT_HIGHLIGHT: STC_CODE_SEARCH_RESULT,
}

EDGE_COLUMN = 80


def GetSectionsText(controler, sections_headers):
    parts = controler.GetTextParts()
    text = ""
    for section in controler.SECTIONS_NAMES:
        text += sections_headers(section)
        if parts[section] == "":
            text += "\n"
        else:
            if not parts[section].startswith("\n"):
                text += "\n"
            text += parts[section]
            if not parts[section].endswith("\n"):
                text += "\n"
    return text


class CodeEditor(CustomStyledTextCtrl):

    KEYWORDS = []
    COMMENT_HEADER = ""

    def __init__(self, parent, window, controler):
        CustomStyledTextCtrl.__init__(self, parent, -1, wx.DefaultPosition,
                                      wx.Size(-1, 300), 0)

        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 25)

        self.SetProperty("fold", "1")
        self.SetProperty("tab.timmy.whinge.level", "1")
        self.SetMargins(0, 0)

        self.SetViewWhiteSpace(False)

        self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        self.SetEdgeColumn(EDGE_COLUMN)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # Like a flattened tree control using square headers
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,             "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,           "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,           "white", "#808080")

        self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        # Make some styles,  The lexer defines what each style is used for, we
        # just have to define what each style looks like.  This set is adapted from
        # Scintilla sample property files.

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(mono)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")

        # Highlighting styles
        self.StyleSetSpec(STC_CODE_ERROR, 'fore:#FF0000,back:#FFFF00,size:%(size)d' % faces)
        self.StyleSetSpec(STC_CODE_SEARCH_RESULT, 'fore:#FFFFFF,back:#FFA500,size:%(size)d' % faces)

        # Section style
        self.StyleSetSpec(STC_CODE_SECTION, 'fore:#808080,size:%(size)d')
        self.StyleSetChangeable(STC_CODE_SECTION, False)

        # Indentation size
        self.SetTabWidth(4)
        self.SetUseTabs(0)

        self.SetCodeLexer()
        self.SetKeyWords(0, " ".join(self.KEYWORDS))

        self.Controler = controler
        self.ParentWindow = window

        self.DisableEvents = True
        self.CurrentAction = None

        self.ResetSearchResults()

        self.RefreshHighlightsTimer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnRefreshHighlightsTimer, self.RefreshHighlightsTimer)

        self.SectionsComments = {}
        for section in self.Controler.SECTIONS_NAMES:
            section_comment = " %s section " % (section)
            len_headers = EDGE_COLUMN - len(section_comment)
            section_comment = \
                self.COMMENT_HEADER * (len_headers // 2) + \
                section_comment + \
                self.COMMENT_HEADER * (len_headers - len_headers // 2)

            self.SectionsComments[section] = {
                "comment": section_comment,
            }

        for i, section in enumerate(self.Controler.SECTIONS_NAMES):
            section_infos = self.SectionsComments[section]
            if i + 1 < len(self.Controler.SECTIONS_NAMES):
                section_end = self.SectionsComments[
                    self.Controler.SECTIONS_NAMES[i + 1]]["comment"]
            else:
                section_end = "$"
            section_infos["pattern"] = re.compile(
                section_infos["comment"] + "(.*)" +
                section_end, re.DOTALL)

        self.SetModEventMask(wx.stc.STC_MOD_BEFOREINSERT | wx.stc.STC_MOD_BEFOREDELETE)

        self.Bind(wx.stc.EVT_STC_DO_DROP, self.OnDoDrop)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModification)

    def SetCodeLexer(self):
        pass

    def ResetSearchResults(self):
        self.Highlights = []
        self.SearchParams = None
        self.SearchResults = None
        self.CurrentFindHighlight = None

    def OnModification(self, event):
        if not self.DisableEvents:
            mod_type = event.GetModificationType()
            if not (mod_type & wx.stc.STC_PERFORMED_UNDO or mod_type & wx.stc.STC_PERFORMED_REDO):
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
        wx.CallAfter(self.RefreshSectionStyling)
        event.Skip()

    def OnDoDrop(self, event):
        try:
            values = eval(event.GetDragText())
        except Exception:
            values = event.GetDragText()
        if isinstance(values, tuple):
            if values[3] == self.Controler.GetCurrentLocation():
                self.ResetBuffer()
                event.SetDragText(values[0])
                wx.CallAfter(self.RefreshModel)
            else:
                event.SetDragText("")
        else:
            self.ResetBuffer()
            wx.CallAfter(self.RefreshModel)
        event.Skip()

    # Buffer the last model state
    def RefreshBuffer(self):
        self.Controler.BufferCodeFile()
        if self.ParentWindow is not None:
            self.ParentWindow.RefreshTitle()
            self.ParentWindow.RefreshFileMenu()
            self.ParentWindow.RefreshEditMenu()
            self.ParentWindow.RefreshPageTitles()

    def StartBuffering(self):
        self.Controler.StartBuffering()
        if self.ParentWindow is not None:
            self.ParentWindow.RefreshTitle()
            self.ParentWindow.RefreshFileMenu()
            self.ParentWindow.RefreshEditMenu()
            self.ParentWindow.RefreshPageTitles()

    def ResetBuffer(self):
        if self.CurrentAction is not None:
            self.Controler.EndBuffering()
            self.CurrentAction = None

    def GetCodeText(self):
        return GetSectionsText(
            self.Controler,
            lambda section: self.SectionsComments[section]["comment"])

    def RefreshView(self, scroll_to_highlight=False):
        self.ResetBuffer()
        self.DisableEvents = True
        old_cursor_pos = self.GetCurrentPos()
        line = self.GetFirstVisibleLine()
        column = self.GetXOffset()
        old_text = self.GetText()
        new_text = self.GetCodeText()
        if old_text != new_text:
            self.SetText(new_text)
            new_cursor_pos = GetCursorPos(old_text, new_text)
            self.LineScroll(column, line)
            if new_cursor_pos is not None:
                self.GotoPos(new_cursor_pos)
            else:
                self.GotoPos(old_cursor_pos)
            self.EmptyUndoBuffer()
        self.DisableEvents = False

        self.RefreshSectionStyling()

        self.ShowHighlights()

    def RefreshSectionStyling(self):
        self.Colourise(0, -1)

        for line in xrange(self.GetLineCount()):
            self.SetLineState(line, 0)

        doc_end_pos = self.GetLength()
        for section in self.Controler.SECTIONS_NAMES:
            section_comments = self.SectionsComments[section]
            start_pos = self.FindText(0, doc_end_pos, section_comments["comment"])
            end_pos = start_pos + len(section_comments["comment"])
            self.StartStyling(start_pos, 0xff)
            self.SetStyling(end_pos - start_pos, STC_CODE_SECTION)
            self.SetLineState(self.LineFromPosition(start_pos), 1)

        self.StartStyling(end_pos, 0x00)
        self.SetStyling(doc_end_pos - end_pos, stc.STC_STYLE_DEFAULT)

    def DoGetBestSize(self):
        return self.ParentWindow.GetPanelBestSize()

    def RefreshModel(self):
        text = self.GetText()
        parts = {}
        for section in self.Controler.SECTIONS_NAMES:
            section_comments = self.SectionsComments[section]
            result = section_comments["pattern"].search(text)
            if result is not None:
                parts[section] = result.group(1)
            else:
                parts[section] = ""
        self.Controler.SetTextParts(parts)
        self.ResetSearchResults()

    def OnKeyPressed(self, event):
        if self.CallTipActive():
            self.CallTipCancel()
        key = event.GetKeyCode()
        current_pos = self.GetCurrentPos()
        selected = self.GetSelection()
        text_selected = selected[0] != selected[1]

        # Test if caret is before Windows like new line
        text = self.GetText()
        if current_pos < len(text) and ord(text[current_pos]) == 13:
            newline_size = 2
        else:
            newline_size = 1

        # Disable to type any character in section header lines
        if self.GetLineState(self.LineFromPosition(current_pos)) and \
           not text_selected and \
           key not in NAVIGATION_KEYS + [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            return

        # Disable to delete line between code and header lines
        elif (self.GetCurLine()[0].strip() != "" and not text_selected and
              (key == wx.WXK_BACK and
               self.GetLineState(self.LineFromPosition(max(0, current_pos - 1))) or
               key in [wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE] and
               self.GetLineState(self.LineFromPosition(min(len(text), current_pos + newline_size))))):
            return

        elif key == 32 and event.ControlDown():
            # Tips
            if event.ShiftDown():
                pass
            # Code completion
            else:
                self.AutoCompSetIgnoreCase(False)  # so this needs to match

                keywords = self.KEYWORDS + [var["Name"]
                                            for var in self.Controler.GetVariables()]
                keywords.sort()
                self.AutoCompShow(0, " ".join(keywords))
        else:
            event.Skip()

    def OnKillFocus(self, event):
        self.AutoCompCancel()
        event.Skip()

    def OnUpdateUI(self, event):
        # check for matching braces
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()

        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # check before
        if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # check after
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)

            if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1 and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

        selected_text = self.GetSelectedText()
        if selected_text:
            self.ParentWindow.SetCopyBuffer(selected_text, True)

    def OnMarginClick(self, event):
        # fold and unfold as needed
        if event.GetMargin() == 2:
            if event.GetShift() and event.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.LineFromPosition(event.GetPosition())

                if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if event.GetShift():
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif event.GetControl():
                        if self.GetFoldExpanded(lineClicked):
                            self.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.ToggleFold(lineClicked)
        event.Skip()

    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)

            if level == -1:
                level = self.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line

    def Cut(self):
        self.ResetBuffer()
        self.DisableEvents = True
        self.CmdKeyExecute(wx.stc.STC_CMD_CUT)
        self.DisableEvents = False
        self.RefreshModel()
        self.RefreshBuffer()

    def Copy(self):
        self.CmdKeyExecute(wx.stc.STC_CMD_COPY)
        self.ParentWindow.RefreshEditMenu()

    def Paste(self):
        self.ResetBuffer()
        self.DisableEvents = True
        self.CmdKeyExecute(wx.stc.STC_CMD_PASTE)
        self.DisableEvents = False
        self.RefreshModel()
        self.RefreshBuffer()

    def Find(self, direction, search_params):
        if self.SearchParams != search_params:
            self.ClearHighlights(SEARCH_RESULT_HIGHLIGHT)

            self.SearchParams = search_params

            self.SearchResults = [
                (start, end, SEARCH_RESULT_HIGHLIGHT)
                for start, end, _text in
                TestTextElement(self.GetText(), search_params)]
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
                caret_pos = self.GetCurrentPos()
                if self.SearchParams["wrap"]:
                    self.CurrentFindHighlight = self.SearchResults[0]
                else:
                    self.CurrentFindHighlight = None
                for start, end, highlight_type in self.SearchResults:
                    if start[0] == 0:
                        highlight_start_pos = start[1]
                    else:
                        highlight_start_pos = self.GetLineEndPosition(start[0] - 1) + start[1] + 1
                    if highlight_start_pos >= caret_pos:
                        self.CurrentFindHighlight = (start, end, highlight_type)
                        break
                if self.CurrentFindHighlight is not None:
                    self.AddHighlight(*self.CurrentFindHighlight)

            self.ScrollToLine(self.CurrentFindHighlight[0][0])

        else:
            if self.CurrentFindHighlight is not None:
                self.RemoveHighlight(*self.CurrentFindHighlight)
            self.CurrentFindHighlight = None

    # -------------------------------------------------------------------------------
    #                        Highlights showing functions
    # -------------------------------------------------------------------------------

    def OnRefreshHighlightsTimer(self, event):
        self.RefreshView(True)
        event.Skip()

    def ClearHighlights(self, highlight_type=None):
        if highlight_type is None:
            self.Highlights = []
        else:
            highlight_type = HIGHLIGHT_TYPES.get(highlight_type, None)
            if highlight_type is not None:
                self.Highlights = [(start, end, highlight) for (start, end, highlight) in self.Highlights if highlight != highlight_type]
        self.RefreshView()

    def AddHighlight(self, start, end, highlight_type):
        highlight_type = HIGHLIGHT_TYPES.get(highlight_type, None)
        if highlight_type is not None:
            self.Highlights.append((start, end, highlight_type))
            self.GotoPos(self.PositionFromLine(start[0]) + start[1])
            self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)
            self.RefreshView()

    def RemoveHighlight(self, start, end, highlight_type):
        highlight_type = HIGHLIGHT_TYPES.get(highlight_type, None)
        if highlight_type is not None and \
           (start, end, highlight_type) in self.Highlights:
            self.Highlights.remove((start, end, highlight_type))
            self.RefreshHighlightsTimer.Start(int(REFRESH_HIGHLIGHT_PERIOD * 1000), oneShot=True)

    def ShowHighlights(self):
        for start, end, highlight_type in self.Highlights:
            if start[0] == 0:
                highlight_start_pos = start[1]
            else:
                highlight_start_pos = self.GetLineEndPosition(start[0] - 1) + start[1] + 1
            if end[0] == 0:
                highlight_end_pos = end[1] + 1
            else:
                highlight_end_pos = self.GetLineEndPosition(end[0] - 1) + end[1] + 2
            self.StartStyling(highlight_start_pos, 0xff)
            self.SetStyling(highlight_end_pos - highlight_start_pos, highlight_type)
            self.StartStyling(highlight_end_pos, 0x00)
            self.SetStyling(len(self.GetText()) - highlight_end_pos, stc.STC_STYLE_DEFAULT)


# -------------------------------------------------------------------------------
#                         Helper for VariablesGrid values
# -------------------------------------------------------------------------------

class AllGridCellEditor(wx.grid.GridCellTextEditor):
    def __init__(self, table, row, col):
        wx.grid.GridCellTextEditor.__init__(self)


class ClassGridCellEditor(wx.grid.GridCellChoiceEditor):
    def __init__(self, table, row, col):
        wx.grid.GridCellChoiceEditor.__init__(self)
        self.SetParameters("input,memory,output")


class VariablesTable(CustomTable):
    __defaultColumnType = dict(
        [(name, AllGridCellEditor) for name in
         ["Name", "Initial", "Description", "OnChange", "Options"]] +
        [('Class', ClassGridCellEditor), ('Type', None)])

    def __init__(self, *args, **kwargs):
        my_columns = kwargs.pop("additional_columns")
        super(VariablesTable, self).__init__(*args, **kwargs)
        self.columnTypes = dict(self.__defaultColumnType)
        if my_columns is not None:
            for key in my_columns.keys():
                if key in self.columnTypes.keys():
                    self.columnTypes[key] = my_columns[key]

    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            if col == 0:
                return row + 1
            else:
                return text(self.data[row].get(self.GetColLabelValue(col, False), ""))

    def _updateColAttrs(self, grid):
        """
        wxGrid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """

        for row in range(self.GetNumberRows()):
            row_highlights = self.Highlights.get(row, {})
            for col in range(self.GetNumberCols()):
                editor = None
                renderer = None
                colname = self.GetColLabelValue(col, False)

                editortype = self.columnTypes.get(colname, None)
                if editortype is not None:
                    editor = editortype(self, row, col)

                grid.SetCellEditor(row, col, editor)
                grid.SetCellRenderer(row, col, renderer)

                highlight_colours = row_highlights.get(colname.lower(), [(wx.WHITE, wx.BLACK)])[-1]
                grid.SetCellBackgroundColour(row, col, highlight_colours[0])
                grid.SetCellTextColour(row, col, highlight_colours[1])
            self.ResizeRow(grid, row)


class VariablesEditor(wx.Panel):

    def __init__(self, parent, window, controler, additional_columns=None):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)

        main_sizer = wx.FlexGridSizer(cols=2, hgap=0, rows=1, vgap=4)
        main_sizer.AddGrowableCol(1)
        main_sizer.AddGrowableRow(0)

        controls_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSizer(controls_sizer, border=5, flag=wx.ALL)

        for name, bitmap, help in [
                ("AddVariableButton", "add_element", _("Add variable")),
                ("DeleteVariableButton", "remove_element", _("Remove variable")),
                ("UpVariableButton", "up", _("Move variable up")),
                ("DownVariableButton", "down", _("Move variable down"))]:
            button = wx.lib.buttons.GenBitmapButton(self, bitmap=GetBitmap(bitmap),
                                                    size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            controls_sizer.AddWindow(button, border=5, flag=wx.BOTTOM)

        self.VariablesGrid = CustomGrid(self, style=wx.VSCROLL)
        self.VariablesGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnVariablesGridCellChange)
        self.VariablesGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnVariablesGridCellLeftClick)
        self.VariablesGrid.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.OnVariablesGridEditorShown)
        main_sizer.AddWindow(self.VariablesGrid, flag=wx.GROW)

        self.SetSizer(main_sizer)

        self.ParentWindow = window
        self.Controler = controler

        self.VariablesDefaultValue = {
            "Name":        "LocalVar0",
            "Type":        DefaultType,
            "Initial":     "",
            "Description": "",
            "OnChange":    "",
            "Options":     ""
        }

        self.Table = VariablesTable(self, [], self.GetVariableTableColnames(), additional_columns=additional_columns)
        self.ColAlignements = [wx.ALIGN_RIGHT] +  \
                              [wx.ALIGN_LEFT]*(len(self.VariablesDefaultValue))
        self.ColSizes = [20, 150] + [130]*(len(self.VariablesDefaultValue)-1)
        self.VariablesGrid.SetTable(self.Table)
        self.VariablesGrid.SetButtons({"Add": self.AddVariableButton,
                                       "Delete": self.DeleteVariableButton,
                                       "Up": self.UpVariableButton,
                                       "Down": self.DownVariableButton})

        def _AddVariable(new_row):
            if new_row > 0:
                row_content = self.Table.data[new_row - 1].copy()
                old_name = row_content['Name']
                row_content['Name'] =\
                    self.Controler.GenerateNewName(old_name, old_name+'%d')
            else:
                row_content = self.VariablesDefaultValue.copy()
            self.Table.InsertRow(new_row, row_content)
            self.RefreshModel()
            self.RefreshView()
            return new_row
        setattr(self.VariablesGrid, "_AddRow", _AddVariable)

        def _DeleteVariable(row):
            self.Table.RemoveRow(row)
            self.RefreshModel()
            self.RefreshView()
        setattr(self.VariablesGrid, "_DeleteRow", _DeleteVariable)

        def _MoveVariable(row, move):
            new_row = self.Table.MoveRow(row, move)
            if new_row != row:
                self.RefreshModel()
                self.RefreshView()
            return new_row
        setattr(self.VariablesGrid, "_MoveRow", _MoveVariable)

        self.VariablesGrid.SetRowLabelSize(0)
        for col in range(self.Table.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.ColAlignements[col], wx.ALIGN_CENTRE)
            self.VariablesGrid.SetColAttr(col, attr)
            self.VariablesGrid.SetColSize(col, self.ColSizes[col])
        self.Table.ResetView(self.VariablesGrid)

    def GetVariableTableColnames(self):
        _ = NoTranslate
        return ["#",
                _("Name"),
                _("Type"),
                _("Initial"),
                _("Description"),
                _("OnChange"),
                _("Options")]

    def RefreshModel(self):
        self.Controler.SetVariables(self.Table.GetData())
        self.RefreshBuffer()

    # Buffer the last model state
    def RefreshBuffer(self):
        self.Controler.BufferCodeFile()
        self.ParentWindow.RefreshTitle()
        self.ParentWindow.RefreshFileMenu()
        self.ParentWindow.RefreshEditMenu()
        self.ParentWindow.RefreshPageTitles()

    def RefreshView(self):
        self.Table.SetData(self.Controler.GetVariables())
        self.Table.ResetView(self.VariablesGrid)
        self.VariablesGrid.RefreshButtons()

    def DoGetBestSize(self):
        return self.ParentWindow.GetPanelBestSize()

    def ShowErrorMessage(self, message):
        dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()

    def OnVariablesGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        colname = self.Table.GetColLabelValue(col, False)
        value = self.Table.GetValue(row, col)
        message = None

        if colname == "Name" and value != "":
            if not TestIdentifier(value):
                message = _("\"%s\" is not a valid identifier!") % value
            elif value.upper() in IEC_KEYWORDS:
                message = _("\"%s\" is a keyword. It can't be used!") % value
            elif value.upper() in [var["Name"].upper()
                                   for var_row, var in enumerate(self.Table.data)
                                   if var_row != row]:
                message = _("A variable with \"%s\" as name already exists!") % value
            else:
                self.RefreshModel()
                wx.CallAfter(self.RefreshView)
        else:
            self.RefreshModel()
            wx.CallAfter(self.RefreshView)

        if message is not None:
            event.Veto()
            wx.CallAfter(self.ShowErrorMessage, message)
        else:
            event.Skip()

    def OnVariablesGridEditorShown(self, event):
        row, col = event.GetRow(), event.GetCol()
        if self.Table.GetColLabelValue(col, False) == "Type":
            type_menu = wx.Menu(title='')
            base_menu = wx.Menu(title='')
            for base_type in self.Controler.GetBaseTypes():
                new_id = wx.NewId()
                base_menu.Append(help='', id=new_id, kind=wx.ITEM_NORMAL, text=base_type)
                self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(base_type), id=new_id)
            type_menu.AppendMenu(wx.NewId(), "Base Types", base_menu)
            datatype_menu = wx.Menu(title='')
            for datatype in self.Controler.GetDataTypes():
                new_id = wx.NewId()
                datatype_menu.Append(help='', id=new_id, kind=wx.ITEM_NORMAL, text=datatype)
                self.Bind(wx.EVT_MENU, self.GetVariableTypeFunction(datatype), id=new_id)
            type_menu.AppendMenu(wx.NewId(), "User Data Types", datatype_menu)
            rect = self.VariablesGrid.BlockToDeviceRect((row, col), (row, col))

            self.VariablesGrid.PopupMenuXY(type_menu, rect.x + rect.width, rect.y + self.VariablesGrid.GetColLabelSize())
            type_menu.Destroy()
            event.Veto()
        else:
            event.Skip()

    def GetVariableTypeFunction(self, base_type):
        def VariableTypeFunction(event):
            row = self.VariablesGrid.GetGridCursorRow()
            self.Table.SetValueByName(row, "Type", base_type)
            self.Table.ResetView(self.VariablesGrid)
            self.RefreshModel()
            self.RefreshView()
            event.Skip()
        return VariableTypeFunction

    def OnVariablesGridCellLeftClick(self, event):
        if event.GetCol() == 0:
            row = event.GetRow()
            data_type = self.Table.GetValueByName(row, "Type")
            var_name = self.Table.GetValueByName(row, "Name")
            data = wx.TextDataObject(str((var_name, "Global", data_type,
                                          self.Controler.GetCurrentLocation())))
            dragSource = wx.DropSource(self.VariablesGrid)
            dragSource.SetData(data)
            dragSource.DoDragDrop()
            return
        event.Skip()

    def AddVariableHighlight(self, infos, highlight_type):
        self.Table.AddHighlight(infos, highlight_type)
        cell_visible = infos[0]
        colnames = [colname.lower() for colname in self.Table.colnames]
        self.VariablesGrid.MakeCellVisible(cell_visible, colnames.index(infos[1]))
        self.Table.ResetView(self.VariablesGrid)

    def RemoveVariableHighlight(self, infos, highlight_type):
        self.Table.RemoveHighlight(infos, highlight_type)
        self.Table.ResetView(self.VariablesGrid)

    def ClearHighlights(self, highlight_type=None):
        self.Table.ClearHighlights(highlight_type)
        self.Table.ResetView(self.VariablesGrid)

# -------------------------------------------------------------------------------
#                          CodeFileEditor Main Frame Class
# -------------------------------------------------------------------------------


class CodeFileEditor(ConfTreeNodeEditor):

    CONFNODEEDITOR_TABS = []
    CODE_EDITOR = None
    COLUMNS_TYPE = None

    def _create_CodePanel(self, prnt):
        self.CodeEditorPanel = wx.SplitterWindow(prnt)
        self.CodeEditorPanel.SetMinimumPaneSize(1)

        self.VariablesPanel = VariablesEditor(self.CodeEditorPanel,
                                              self.ParentWindow,
                                              self.Controler,
                                              self.COLUMNS_TYPE)

        if self.CODE_EDITOR is not None:
            self.CodeEditor = self.CODE_EDITOR(self.CodeEditorPanel,
                                               self.ParentWindow, self.Controler)

            self.CodeEditorPanel.SplitHorizontally(self.VariablesPanel,
                                                   self.CodeEditor, 150)
        else:
            self.CodeEditorPanel.Initialize(self.VariablesPanel)

        return self.CodeEditorPanel

    def __init__(self, parent, controler, window):
        ConfTreeNodeEditor.__init__(self, parent, controler, window)

        wx.CallAfter(self.CodeEditorPanel.SetSashPosition, 150)

    def GetBufferState(self):
        return self.Controler.GetBufferState()

    def Undo(self):
        self.Controler.LoadPrevious()
        self.RefreshView()

    def Redo(self):
        self.Controler.LoadNext()
        self.RefreshView()

    def RefreshView(self):
        ConfTreeNodeEditor.RefreshView(self)

        self.VariablesPanel.RefreshView()
        self.CodeEditor.RefreshView()

    def Find(self, direction, search_params):
        self.CodeEditor.Find(direction, search_params)

    def AddHighlight(self, infos, start, end, highlight_type):
        if self.VariablesPanel is not None and infos[0] == "var_inout":
            self.VariablesPanel.AddVariableHighlight(infos[1:], highlight_type)
        else:
            self.CodeEditor.AddHighlight(start, end, highlight_type)

    def RemoveHighlight(self, infos, start, end, highlight_type):
        if self.VariablesPanel is not None and infos[0] == "var_inout":
            self.VariablesPanel.RemoveVariableHighlight(infos[1:], highlight_type)
        else:
            self.CodeEditor.RemoveHighlight(start, end, highlight_type)

    def ClearHighlights(self, highlight_type=None):
        if self.VariablesPanel is not None:
            self.VariablesPanel.ClearHighlights(highlight_type)
        else:
            self.CodeEditor.ClearHighlights(highlight_type)
