#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
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
from __future__ import division
import unittest
import time

import wx
import conftest
import controls.CustomIntCtrl


class TestCustomIntCtrl(unittest.TestCase):
    def setUp(self):
        self.app = wx.App()
        self.frame = wx.Frame(None)

    def tearDown(self):
        self.frame.Destroy()
        wx.CallAfter(self.app.Exit)
        self.app.MainLoop()

    def testMaxLimit(self):
        """Test working upper bound"""
        self.AddControls()
        self.int_ctrl.SetValue(self.max_val + 100)
        self.ProcessEvents()

        self.txt_ctrl.SetFocus()
        self.ProcessEvents()
        self.assertEqual(self.int_ctrl.GetValue(), self.max_val)

    def testMinLimit(self):
        """Test working lower bound"""
        self.AddControls()
        self.int_ctrl.SetValue(self.min_val - 100)
        self.ProcessEvents()

        self.txt_ctrl.SetFocus()
        self.ProcessEvents()

        self.assertEqual(self.int_ctrl.GetValue(), self.min_val)

    def testCorrectValue(self):
        """Test case if no limiting is necessary"""
        self.AddControls()
        val = (self.max_val + self.min_val) // 2
        self.int_ctrl.SetValue(val)
        self.ProcessEvents()

        self.txt_ctrl.SetFocus()
        self.ProcessEvents()

        self.assertEqual(self.int_ctrl.GetValue(), val)

    def testEventBinding(self):
        """Test event sending after edit and bound checks are done"""
        self.AddControls()
        self.event_happend = False

        def EventHandler(event):
            self.event_happend = True
            event.Skip()

        self.int_ctrl.Bind(controls.CustomIntCtrl.EVT_CUSTOM_INT, EventHandler)

        val = (self.max_val + self.min_val) // 2

        self.int_ctrl.SetValue(val)
        self.ProcessEvents()
        self.txt_ctrl.SetFocus()

        self.ProcessEvents()
        self.txt_ctrl.SetFocus()
        self.ProcessEvents()

        self.assertEqual(self.int_ctrl.GetValue(), val)
        self.assertTrue(self.event_happend)

    def testLongNumbers(self):
        """Test support of long integer"""
        self.AddControls()
        val = 40000000000
        self.int_ctrl.SetMax(val)
        self.int_ctrl.SetValue(val)
        self.ProcessEvents()

        self.txt_ctrl.SetFocus()
        self.ProcessEvents()

        self.assertEqual(val, val)

    def ProcessEvents(self):
        for dummy in range(0, 10):
            wx.Yield()
            time.sleep(0.01)

    def AddControls(self):
        vs = wx.BoxSizer(wx.VERTICAL)
        self.int_ctrl = controls.CustomIntCtrl(self.frame)
        self.txt_ctrl = wx.TextCtrl(self.frame)
        vs.Add(self.int_ctrl, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        vs.Add(self.txt_ctrl, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.frame.SetSizer(vs)
        vs.Fit(self.frame)
        self.frame.Show()
        self.frame.Raise()

        self.min_val = 50
        self.max_val = 100
        self.int_ctrl.SetBounds(self.min_val, self.max_val)
        self.ProcessEvents()


if __name__ == '__main__':
    conftest.init_environment()
    unittest.main()
