#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007:      Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2016-2017: Andrey Skvortsov <andrej.skvortzov@gmail.com>
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
import os
import sys
import time
import tempfile
import platform
import traceback
import threading
import wx

Max_Traceback_List_Size = 20


def Display_Exception_Dialog(e_type, e_value, e_tb, bug_report_path, exit):
    trcbck_lst = []
    for i, line in enumerate(traceback.extract_tb(e_tb)):
        trcbck = " " + str(i+1) + ". "
        if line[0].find(os.getcwd()) == -1:
            trcbck += "file : " + str(line[0]) + ",   "
        else:
            trcbck += "file : " + str(line[0][len(os.getcwd()):]) + ",   "
        trcbck += "line : " + str(line[1]) + ",   " + "function : " + str(line[2])
        trcbck_lst.append(trcbck)

    # Allow clicking....
    cap = wx.Window_GetCapture()
    if cap:
        cap.ReleaseMouse()

    dlg = wx.SingleChoiceDialog(
        None,
        _("""
An unhandled exception (bug) occured. Bug report saved at :
(%s)

Please be kind enough to send this file to:
beremiz-devel@lists.sourceforge.net

You should now restart program.

Traceback:
""") % bug_report_path +
        repr(e_type) + " : " + repr(e_value),
        _("Error"),
        trcbck_lst)
    try:
        res = (dlg.ShowModal() == wx.ID_OK)
    finally:
        dlg.Destroy()

    if exit:
        sys.exit()  # wx.Exit()

    return res


def get_last_traceback(tb):
    while tb.tb_next:
        tb = tb.tb_next
    return tb


def format_namespace(d, indent='    '):
    return '\n'.join(['%s%s: %s' % (indent, k, repr(v)[:10000]) for k, v in d.iteritems()])


ignored_exceptions = []  # a problem with a line in a module is only reported once per session


def AddExceptHook(app_version='[No version]'):

    def save_bug_report(e_type, e_value, e_traceback, bug_report_path, date):
        info = {
            'app-title': wx.GetApp().GetAppName(),
            'app-version': app_version,
            'wx-version': wx.VERSION_STRING,
            'wx-platform': wx.Platform,
            'python-version': platform.python_version(),
            'platform': platform.platform(),
            'e-type': e_type,
            'e-value': e_value,
            'date': date,
            'cwd': os.getcwd(),
        }
        if e_traceback:
            info['traceback'] = ''.join(traceback.format_tb(e_traceback)) + '%s: %s' % (e_type, e_value)
            last_tb = get_last_traceback(e_traceback)
            exception_locals = last_tb.tb_frame.f_locals  # the locals at the level of the stack trace where the exception actually occurred
            info['locals'] = format_namespace(exception_locals)
            if 'self' in exception_locals:
                try:
                    info['self'] = format_namespace(exception_locals['self'].__dict__)
                except Exception:
                    pass
        path = os.path.dirname(bug_report_path)
        if not os.path.exists(path):
            os.mkdir(path)
        output = open(bug_report_path, 'w')
        lst = info.keys()
        lst.sort()
        for a in lst:
            output.write(a + ":\n" + str(info[a]) + "\n\n")
        output.close()

    def handle_exception(e_type, e_value, e_traceback, exit=False):
        traceback.print_exception(e_type, e_value, e_traceback)  # this is very helpful when there's an exception in the rest of this func
        last_tb = get_last_traceback(e_traceback)
        ex = (last_tb.tb_frame.f_code.co_filename, last_tb.tb_frame.f_lineno)
        if ex not in ignored_exceptions:
            ignored_exceptions.append(ex)
            date = time.ctime()
            path = tempfile.gettempdir()+os.sep+wx.GetApp().GetAppName()
            bug_report_path = path + os.sep + "bug_report_" + time.strftime("%Y_%m_%d__%H-%M-%S") + ".txt"
            save_bug_report(e_type, e_value, e_traceback, bug_report_path, date)
            wx.CallAfter(Display_Exception_Dialog, e_type, e_value, e_traceback, bug_report_path, exit)
    # sys.excepthook = lambda *args: wx.CallAfter(handle_exception, *args)
    sys.excepthook = handle_exception

    init_old = threading.Thread.__init__

    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run

        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init

    return handle_exception
