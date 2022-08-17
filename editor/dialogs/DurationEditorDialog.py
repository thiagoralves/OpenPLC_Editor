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
import re

import wx

# -------------------------------------------------------------------------------
#                                  Helpers
# -------------------------------------------------------------------------------

MICROSECONDS = 0.001
MILLISECONDS = 1
SECOND = 1000
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR

IEC_TIME_MODEL = re.compile(r"(?:T|TIME)#(-)?(?:(%(float)s)D_?)?(?:(%(float)s)H_?)?(?:(%(float)s)M(?!S)_?)?(?:(%(float)s)S_?)?(?:(%(float)s)MS)?$" % {"float": r"[0-9]+(?:\.[0-9]+)?"})


# -------------------------------------------------------------------------------
#                         Edit Duration Value Dialog
# -------------------------------------------------------------------------------


class DurationEditorDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title=_('Edit Duration'))

        CONTROLS = [
            ("Days", _('Days:')),
            ("Hours", _('Hours:')),
            ("Minutes", _('Minutes:')),
            ("Seconds", _('Seconds:')),
            ("Milliseconds", _('Milliseconds:')),
            ("Microseconds", _('Microseconds:')),
        ]

        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)

        controls_sizer = wx.FlexGridSizer(cols=len(CONTROLS), hgap=10, rows=2, vgap=10)
        main_sizer.AddSizer(controls_sizer, border=20,
                            flag=wx.TOP | wx.LEFT | wx.RIGHT | wx.GROW)

        controls = []
        for i, (name, label) in enumerate(CONTROLS):
            controls_sizer.AddGrowableCol(i)

            st = wx.StaticText(self, label=label)
            txtctrl = wx.TextCtrl(self, value='0', style=wx.TE_PROCESS_ENTER)
            self.Bind(wx.EVT_TEXT_ENTER,
                      self.GetControlValueTestFunction(txtctrl),
                      txtctrl)
            setattr(self, name, txtctrl)

            controls.append((st, txtctrl))

        for st, txtctrl in controls:
            controls_sizer.AddWindow(st, flag=wx.GROW)

        for st, txtctrl in controls:
            controls_sizer.AddWindow(txtctrl, flag=wx.GROW)

        button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL | wx.CENTRE)
        self.Bind(wx.EVT_BUTTON, self.OnOK, button_sizer.GetAffirmativeButton())
        main_sizer.AddSizer(button_sizer, border=20,
                            flag=wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT)

        self.SetSizer(main_sizer)
        self.Fit()
        self.Days.SetFocus()

    def SetDuration(self, value):
        result = IEC_TIME_MODEL.match(value.upper())
        if result is not None:
            values = result.groups()
            for control, index in [(self.Days, 1), (self.Hours, 2),
                                   (self.Minutes, 3), (self.Seconds, 4)]:
                value = values[index]
                if value is not None:
                    control.SetValue(value)
                else:
                    control.SetValue("0")
            milliseconds = values[5]
            if milliseconds is not None:
                self.Milliseconds.SetValue("%d" % int(float(milliseconds)))
                self.Microseconds.SetValue("%.3f" % ((float(milliseconds) % MILLISECONDS) / MICROSECONDS))
            else:
                self.Milliseconds.SetValue("0")
                self.Microseconds.SetValue("0")

    def GetControlValueTestFunction(self, control):
        def OnValueChanged(event):
            try:
                float(control.GetValue())
            except ValueError:
                message = wx.MessageDialog(self, _("Invalid value!\nYou must fill a numeric value."), _("Error"), wx.OK | wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
            event.Skip()
            self.OnCloseDialog()
        return OnValueChanged

    def GetDuration(self):
        milliseconds = 0
        for control, factor in [(self.Days, DAY), (self.Hours, HOUR),
                                (self.Minutes, MINUTE), (self.Seconds, SECOND),
                                (self.Milliseconds, MILLISECONDS), (self.Microseconds, MICROSECONDS)]:

            milliseconds += float(control.GetValue()) * factor

        not_null = False
        duration = "T#"
        for value, format in [((int(milliseconds) // DAY),             "%dd"),
                              ((int(milliseconds) % DAY) // HOUR,      "%dh"),
                              ((int(milliseconds) % HOUR) // MINUTE,   "%dm"),
                              ((int(milliseconds) % MINUTE) // SECOND, "%ds")]:

            if value > 0 or not_null:
                duration += format % value
                not_null = True

        duration += ("%f" % (milliseconds % SECOND)).rstrip("0").rstrip(".") + "ms"
        return duration

    def OnOK(self, event):
        self.OnCloseDialog()

    def OnCloseDialog(self):
        errors = []
        for control, name in [(self.Days, _("days")), (self.Hours, _("hours")),
                              (self.Minutes, _("minutes")), (self.Seconds, _("seconds")),
                              (self.Milliseconds, _("milliseconds")),
                              (self.Microseconds, _("microseconds"))]:
            try:
                float(control.GetValue())
            except ValueError:
                errors.append(name)
        if len(errors) > 0:
            if len(errors) == 1:
                message = _("Field %s hasn't a valid value!") % errors[0]
            else:
                message = _("Fields %s haven't a valid value!") % ",".join(errors)
            dialog = wx.MessageDialog(self, message, _("Error"), wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
        else:
            self.EndModal(wx.ID_OK)
