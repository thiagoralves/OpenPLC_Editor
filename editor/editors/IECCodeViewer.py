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
from editors.TextViewer import TextViewer
from plcopen.plcopen import TestTextElement


class IECCodeViewer(TextViewer):

    def __del__(self):
        TextViewer.__del__(self)
        if getattr(self, "_OnClose"):
            self._OnClose(self)

    def Paste(self):
        if self.Controler is not None:
            TextViewer.Paste(self)

    def Search(self, criteria):
        return [((self.TagName, "body", 0),) + result for result in TestTextElement(self.Editor.GetText(), criteria)]
