#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2012: Edouard TISSERANT and Laurent BESSARD
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
from datetime import timedelta
import binascii
import numpy
from graphics.DebugDataConsumer import DebugDataConsumer, TYPE_TRANSLATOR

# -------------------------------------------------------------------------------
#                 Constant for calculate CRC for string variables
# -------------------------------------------------------------------------------

STRING_CRC_SIZE = 8
STRING_CRC_MASK = 2 ** STRING_CRC_SIZE - 1

# -------------------------------------------------------------------------------
#                          Debug Variable Item Class
# -------------------------------------------------------------------------------


class DebugVariableItem(DebugDataConsumer):
    """
    Class that implements an element that consumes debug values for PLC variable and
    stores received values for displaying them in graphic panel or table
    """

    def __init__(self, parent, variable, store_data=False):
        """
        Constructor
        @param parent: Reference to debug variable panel
        @param variable: Path of variable to debug
        """
        DebugDataConsumer.__init__(self)

        self.Parent = parent
        self.Variable = variable
        self.StoreData = store_data

        # Get Variable data type
        self.RefreshVariableType()

    def __del__(self):
        """
        Destructor
        """
        # Reset reference to debug variable panel
        self.Parent = None

    def SetVariable(self, variable):
        """
        Set path of variable
        @param variable: Path of variable to debug
        """
        if self.Parent is not None and self.Variable != variable:
            # Store variable path
            self.Variable = variable
            # Get Variable data type
            self.RefreshVariableType()

            # Refresh debug variable panel
            self.Parent.RefreshView()

    def GetVariable(self, mask=None):
        """
        Return path of variable
        @param mask: Mask to apply to variable path [var_name, '*',...]
        @return: String containing masked variable path
        """
        # Apply mask to variable name
        if mask is not None:
            # '#' correspond to parts that are different between all items

            # Extract variable path parts
            parts = self.Variable.split('.')
            # Adjust mask size to size of variable path
            mask = mask + ['*'] * max(0, len(parts) - len(mask))

            # Store previous mask
            last = None
            # Init masked variable path
            variable = ""

            for m, p in zip(mask, parts):
                # Part is not masked, add part prefixed with '.' is previous
                # wasn't masked
                if m == '*':
                    variable += ('.' if last == '*' else '') + p

                # Part is mask, add '..' if first or previous wasn't masked
                elif last is None or last == '*':
                    variable += '..'

                last = m

            return variable

        return self.Variable

    def RefreshVariableType(self):
        """
        Get and store variable data type
        """
        self.VariableType = self.Parent.GetDataType(self.Variable)
        # Reset data stored
        self.ResetData()

    def GetVariableType(self):
        """
        Return variable data type
        @return: Variable data type
        """
        return self.VariableType

    def GetData(self, start_tick=None, end_tick=None):
        """
        Return data stored contained in given range
        @param start_tick: Start tick of given range (default None, first data)
        @param end_tick: end tick of given range (default None, last data)
        @return: Data as numpy.array([(tick, value, forced),...])
        """
        # Return immediately if data empty or none
        if self.Data is None or len(self.Data) == 0:
            return self.Data

        # Find nearest data outside given range indexes
        start_idx = (self.GetNearestData(start_tick, -1)
                     if start_tick is not None
                     else 0)
        end_idx = (self.GetNearestData(end_tick, 1)
                   if end_tick is not None
                   else len(self.Data))

        # Return data between indexes
        return self.Data[start_idx:end_idx]

    def GetRawValue(self, index):
        """
        Return raw value at given index for string variables
        @param index: Variable value index
        @return: Variable data type
        """
        if self.VariableType in ["STRING", "WSTRING"] and index < len(self.RawData):
            return self.RawData[index][0]
        return ""

    def GetValueRange(self):
        """
        Return variable value range
        @return: (minimum_value, maximum_value)
        """
        return self.MinValue, self.MaxValue

    def GetDataAndValueRange(self, start_tick, end_tick, full_range=True):
        """
        Return variable data and value range for a given tick range
        @param start_tick: Start tick of given range (default None, first data)
        @param end_tick: end tick of given range (default None, last data)
        @param full_range: Value range is calculated on whole data (False: only
        calculated on data in given range)
        @return: (numpy.array([(tick, value, forced),...]),
                  min_value, max_value)
        """
        # Get data in given tick range
        data = self.GetData(start_tick, end_tick)

        # Value range is calculated on whole data
        if full_range:
            return data, self.MinValue, self.MaxValue

        # Check that data in given range is not empty
        values = data[:, 1]
        if len(values) > 0:
            # Return value range for data in given tick range
            return (data,
                    data[numpy.argmin(values), 1],
                    data[numpy.argmax(values), 1])

        # Return default values
        return data, None, None

    def ResetData(self):
        """
        Reset data stored when store data option enabled
        """
        if self.StoreData and self.IsNumVariable():
            # Init table storing data
            self.Data = numpy.array([]).reshape(0, 3)

            # Init table storing raw data if variable is strin
            self.RawData = ([]
                            if self.VariableType in ["STRING", "WSTRING"]
                            else None)

            # Init Value range variables
            self.MinValue = None
            self.MaxValue = None

        else:
            self.Data = None
            self.MinValue = None
            self.MaxValue = None
        # Init variable value
        self.Value = ""

    def IsNumVariable(self):
        """
        Return if variable data type is numeric. String variables are
        considered as numeric (string CRC). Time variables are considered
        as number of seconds
        @return: True if data type is numeric
        """
        return (self.Parent.IsNumType(self.VariableType) or
                self.VariableType in ["STRING", "WSTRING", "TIME", "TOD", "DT", "DATE"])

    def NewValues(self, ticks, values):
        """
        Function called by debug thread when a new debug value is available
        @param tick: PLC tick when value was captured
        @param value: Value captured
        @param forced: Forced flag, True if value is forced (default: False)
        """
        DebugDataConsumer.NewValues(self, ticks[-1], values[-1], raw=None)

        if self.Data is not None:

            if self.VariableType in ["STRING", "WSTRING"]:
                last_raw_data = (self.RawData[-1]
                                 if len(self.RawData) > 0 else None)
                last_raw_data_idx = len(self.RawData) - 1

            data_values = []
            for tick, (value, forced) in zip(ticks, values):
                # Translate forced flag to float for storing in Data table
                forced_value = float(forced)

                if self.VariableType in ["STRING", "WSTRING"]:
                    # String data value is CRC
                    num_value = (binascii.crc32(value) & STRING_CRC_MASK)
                elif self.VariableType in ["TIME", "TOD", "DT", "DATE"]:
                    # Numeric value of time type variables
                    # is represented in seconds
                    num_value = float(value.total_seconds())
                else:
                    num_value = float(value)

                # Update variable range values
                self.MinValue = (min(self.MinValue, num_value)
                                 if self.MinValue is not None
                                 else num_value)
                self.MaxValue = (max(self.MaxValue, num_value)
                                 if self.MaxValue is not None
                                 else num_value)

                # In the case of string variables, we store raw string value and
                # forced flag in raw data table. Only changes in this two values
                # are stored. Index to the corresponding raw value is stored in
                # data third column
                if self.VariableType in ["STRING", "WSTRING"]:
                    raw_data = (value, forced_value)
                    if len(self.RawData) == 0 or last_raw_data != raw_data:
                        last_raw_data_idx += 1
                        last_raw_data = raw_data
                        self.RawData.append(raw_data)
                    extra_value = last_raw_data_idx

                # In other case, data third column is forced flag
                else:
                    extra_value = forced_value

                data_values.append(
                    [float(tick), num_value, extra_value])

            # Add New data to stored data table
            self.Data = numpy.append(self.Data, data_values, axis=0)

            # Signal to debug variable panel to refresh
            self.Parent.HasNewData = True

    def SetForced(self, forced):
        """
        Update Forced flag
        @param forced: New forced flag
        """
        # Store forced flag
        if self.Forced != forced:
            self.Forced = forced

            # Signal to debug variable panel to refresh
            self.Parent.HasNewData = True

    def SetValue(self, value):
        """
        Update value.
        @param value: New value
        """
        # Remove quote and double quote surrounding string value to get raw value
        if self.VariableType == "STRING" and value.startswith("'") and value.endswith("'") or \
           self.VariableType == "WSTRING" and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        # Store variable value
        if self.Value != value:
            self.Value = value

            # Signal to debug variable panel to refresh
            self.Parent.HasNewData = True

    def GetValue(self, tick=None, raw=False):
        """
        Return current value or value and forced flag for tick given
        @return: Current value or value and forced flag
        """
        # If tick given and stored data option enabled
        if tick is not None and self.Data is not None:

            # Return current value and forced flag if data empty
            if len(self.Data) == 0:
                return self.Value, self.IsForced()

            # Get index of nearest data from tick given
            idx = self.GetNearestData(tick, 0)

            # Get value and forced flag at given index
            value, forced = \
                self.RawData[int(self.Data[idx, 2])] \
                if self.VariableType in ["STRING", "WSTRING"] \
                else self.Data[idx, 1:3]

            if self.VariableType in ["TIME", "TOD", "DT", "DATE"]:
                value = timedelta(seconds=value)

            # Get raw value if asked
            if not raw:
                value = TYPE_TRANSLATOR.get(
                    self.VariableType, str)(value)

            return value, forced

        # Return raw value if asked
        if not raw and self.VariableType in ["STRING", "WSTRING"]:
            return TYPE_TRANSLATOR.get(
                self.VariableType, str)(self.Value)
        return self.Value

    def GetNearestData(self, tick, adjust):
        """
        Return index of nearest data from tick given
        @param tick: Tick where find nearest data
        @param adjust: Constraint for data position from tick
                       -1: older than tick
                       1:  newer than tick
                       0:  doesn't matter
        @return: Index of nearest data
        """
        # Return immediately if data is empty
        if self.Data is None:
            return None

        # Extract data ticks
        ticks = self.Data[:, 0]

        # Get nearest data from tick
        idx = numpy.argmin(abs(ticks - tick))

        # Adjust data index according to constraint
        if adjust < 0 and ticks[idx] > tick and idx > 0 or \
           adjust > 0 and ticks[idx] < tick and idx < len(ticks):
            idx += adjust

        return idx
