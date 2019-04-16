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
import datetime


# -------------------------------------------------------------------------------
#                        Date and Time conversion function
# -------------------------------------------------------------------------------

SECOND = 1000000      # Number of microseconds in one second
MINUTE = 60 * SECOND  # Number of microseconds in one minute
HOUR = 60 * MINUTE    # Number of microseconds in one hour
DAY = 24 * HOUR       # Number of microseconds in one day

# Date corresponding to Epoch (1970 January the first)
DATE_ORIGIN = datetime.datetime(1970, 1, 1)


def get_microseconds(value):
    """
    Function converting time duration expressed in day, second and microseconds
    into one expressed in microseconds
    @param value: Time duration to convert
    @return: Time duration expressed in microsecond
    """
    return float(value.days * DAY +
                 value.seconds * SECOND +
                 value.microseconds)


def generate_time(value):
    """
    Function converting time duration expressed in day, second and microseconds
    into a IEC 61131 TIME literal
    @param value: Time duration to convert
    @return: IEC 61131 TIME literal
    """
    microseconds = get_microseconds(value)

    # Get absolute microseconds value and save if it was negative
    negative = microseconds < 0
    microseconds = abs(microseconds)

    # TIME literal prefix
    data = "T#"
    if negative:
        data += "-"

    # In TIME literal format, it isn't mandatory to indicate null values
    # if no greater non-null values are available. This variable is used to
    # inhibit formatting until a non-null value is found
    not_null = False

    for val, format in [
            (int(microseconds) // DAY, "%dd"),                 # Days
            ((int(microseconds) % DAY) // HOUR, "%dh"),        # Hours
            ((int(microseconds) % HOUR) // MINUTE, "%dm"),     # Minutes
            ((int(microseconds) % MINUTE) // SECOND, "%ds")]:  # Seconds

        # Add value to TIME literal if value is non-null or another non-null
        # value have already be found
        if val > 0 or not_null:
            data += format % val

            # Update non-null variable
            not_null = True

    # In any case microseconds have to be added to TIME literal
    data += "%gms" % (microseconds % SECOND / 1000.)

    return data


def generate_date(value):
    """
    Function converting time duration expressed in day, second and microseconds
    into a IEC 61131 DATE literal
    @param value: Time duration to convert
    @return: IEC 61131 DATE literal
    """
    return (DATE_ORIGIN + value).strftime("DATE#%Y-%m-%d")


def generate_datetime(value):
    """
    Function converting time duration expressed in day, second and microseconds
    into a IEC 61131 DATE_AND_TIME literal
    @param value: Time duration to convert
    @return: IEC 61131 DATE_AND_TIME literal
    """
    return (DATE_ORIGIN + value).strftime("DT#%Y-%m-%d-%H:%M:%S.%f")


def generate_timeofday(value):
    """
    Function converting time duration expressed in day, second and microseconds
    into a IEC 61131 TIME_OF_DAY literal
    @param value: Time duration to convert
    @return: IEC 61131 TIME_OF_DAY literal
    """
    microseconds = get_microseconds(value)

    # TIME_OF_DAY literal prefix
    data = "TOD#"

    for val, format in [
            (int(microseconds) // HOUR, "%2.2d:"),               # Hours
            ((int(microseconds) % HOUR) // MINUTE, "%2.2d:"),    # Minutes
            ((int(microseconds) % MINUTE) // SECOND, "%2.2d."),  # Seconds
            (microseconds % SECOND, "%6.6d")]:                  # Microseconds

        # Add value to TIME_OF_DAY literal
        data += format % val

    return data


# Dictionary of translation functions from value send by debugger to IEC
# literal stored by type
TYPE_TRANSLATOR = {
    "TIME": generate_time,
    "DATE": generate_date,
    "DT": generate_datetime,
    "TOD": generate_timeofday,
    "STRING": lambda v: "'%s'" % v,
    "WSTRING": lambda v: '"%s"' % v,
    "REAL": lambda v: "%.6g" % v,
    "LREAL": lambda v: "%.6g" % v}


# -------------------------------------------------------------------------------
#                            Debug Data Consumer Class
# -------------------------------------------------------------------------------


class DebugDataConsumer(object):
    """
    Class that implements an element that consumes debug values
    Value update can be inhibited during the time the associated Debug Viewer is
    refreshing
    """

    def __init__(self):
        """
        Constructor
        """
        # Debug value and forced flag
        self.Value = None
        self.Forced = False

        # Store debug value and forced flag when value update is inhibited
        self.LastValue = None
        self.LastForced = False

        # Value IEC data type
        self.DataType = None

        # Flag that value update is inhibited
        self.Inhibited = False

    def Inhibit(self, inhibit):
        """
        Set flag to inhibit or activate value update
        @param inhibit: Inhibit flag
        """
        # Save inhibit flag
        self.Inhibited = inhibit

        # When reactivated update value and forced flag with stored values
        if not inhibit and self.LastValue is not None:
            self.SetForced(self.LastForced)
            self.SetValue(self.LastValue)

            # Reset stored values
            self.LastValue = None
            self.LastForced = False

    def SetDataType(self, data_type):
        """
        Set value IEC data type
        @param data_type: Value IEC data type
        """
        self.DataType = data_type

    def NewValues(self, tick, values, raw="BOOL"):
        """
        Function called by debug thread when a new debug value is available
        @param tick: PLC tick when value was captured
        @param value: Value captured
        @param forced: Forced flag, True if value is forced (default: False)
        @param raw: Data type of values not translated (default: 'BOOL')
        """
        value, forced = values

        # Translate value to IEC literal
        if self.DataType != raw:
            value = TYPE_TRANSLATOR.get(self.DataType, str)(value)

        # Store value and forced flag when value update is inhibited
        if self.Inhibited:
            self.LastValue = value
            self.LastForced = forced

        # Update value and forced flag in any other case
        else:
            self.SetForced(forced)
            self.SetValue(value)

    def SetValue(self, value):
        """
        Update value.
        May be overridden by inherited classes
        @param value: New value
        """
        self.Value = value

    def GetValue(self):
        """
        Return current value
        @return: Current value
        """
        return self.Value

    def SetForced(self, forced):
        """
        Update Forced flag.
        May be overridden by inherited classes
        @param forced: New forced flag
        """
        self.Forced = forced

    def IsForced(self):
        """
        Indicate if current value is forced
        @return: Current forced flag
        """
        return self.Forced
