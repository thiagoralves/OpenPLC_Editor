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
import wx.stc as stc

from controls.CustomStyledTextCtrl import faces
from editors.CodeFileEditor import CodeFileEditor, CodeEditor


class CppEditor(CodeEditor):

    KEYWORDS = ["asm", "auto", "bool", "break", "case", "catch", "char", "class",
                "const", "const_cast", "continue", "default", "delete", "do", "double",
                "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false",
                "float", "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
                "namespace", "new", "operator", "private", "protected", "public", "register",
                "reinterpret_cast", "return", "short", "signed", "sizeof", "static",
                "static_cast", "struct", "switch", "template", "this", "throw", "true", "try",
                "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual",
                "void", "volatile", "wchar_t", "while"]
    COMMENT_HEADER = "/"

    def SetCodeLexer(self):
        self.SetLexer(stc.STC_LEX_CPP)

        self.StyleSetSpec(stc.STC_C_COMMENT, 'fore:#408060,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_COMMENTLINE, 'fore:#408060,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_COMMENTDOC, 'fore:#408060,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_NUMBER, 'fore:#0076AE,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_WORD, 'bold,fore:#800056,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_STRING, 'fore:#2a00ff,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_PREPROCESSOR, 'bold,fore:#800056,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_OPERATOR, 'bold,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_C_STRINGEOL, 'back:#FFD5FF,size:%(size)d' % faces)


class CFileEditor(CodeFileEditor):
    """
    CFileEditor Main Frame Class
    """

    CONFNODEEDITOR_TABS = [
        (_("C code"), "_create_CodePanel")]
    CODE_EDITOR = CppEditor
