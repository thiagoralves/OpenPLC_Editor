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
import keyword
import wx.stc as stc

from controls.CustomStyledTextCtrl import faces
from editors.CodeFileEditor import CodeFileEditor, CodeEditor


class PythonCodeEditor(CodeEditor):

    KEYWORDS = keyword.kwlist
    COMMENT_HEADER = "#"

    def SetCodeLexer(self):
        self.SetLexer(stc.STC_LEX_PYTHON)

        # Line numbers in margin
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, 'fore:#000000,back:#99A9C2,size:%(size)d' % faces)
        # Highlighted brace
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, 'fore:#00009D,back:#FFFF00,size:%(size)d' % faces)
        # Unmatched brace
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD, 'fore:#00009D,back:#FF0000,size:%(size)d' % faces)
        # Indentation guide
        self.StyleSetSpec(stc.STC_STYLE_INDENTGUIDE, 'fore:#CDCDCD,size:%(size)d' % faces)

        # Python styles
        self.StyleSetSpec(stc.STC_P_DEFAULT, 'fore:#000000,size:%(size)d' % faces)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE,  'fore:#008000,back:#F0FFF0,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, 'fore:#008000,back:#F0FFF0,size:%(size)d' % faces)
        # Numbers
        self.StyleSetSpec(stc.STC_P_NUMBER, 'fore:#008080,size:%(size)d' % faces)
        # Strings and characters
        self.StyleSetSpec(stc.STC_P_STRING, 'fore:#800080,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_P_CHARACTER, 'fore:#800080,size:%(size)d' % faces)
        # Keywords
        self.StyleSetSpec(stc.STC_P_WORD, 'fore:#000080,bold,size:%(size)d' % faces)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, 'fore:#800080,back:#FFFFEA,size:%(size)d' % faces)
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, 'fore:#800080,back:#FFFFEA,size:%(size)d' % faces)
        # Class names
        self.StyleSetSpec(stc.STC_P_CLASSNAME, 'fore:#0000FF,bold,size:%(size)d' % faces)
        # Function names
        self.StyleSetSpec(stc.STC_P_DEFNAME, 'fore:#008080,bold,size:%(size)d' % faces)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, 'fore:#800000,bold,size:%(size)d' % faces)
        # Identifiers. I leave this as not bold because everything seems
        # to be an identifier if it doesn't match the above criterae
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, 'fore:#000000,size:%(size)d' % faces)


# -------------------------------------------------------------------------------
#                          CFileEditor Main Frame Class
# -------------------------------------------------------------------------------

class PythonEditor(CodeFileEditor):

    CONFNODEEDITOR_TABS = [
        (_("Python code"), "_create_CodePanel")]
    CODE_EDITOR = PythonCodeEditor
