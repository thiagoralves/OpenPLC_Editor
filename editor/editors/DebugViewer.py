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
from threading import Lock, Timer
from time import time as gettime

import wx

REFRESH_PERIOD = 0.1         # Minimum time between 2 refresh
DEBUG_REFRESH_LOCK = Lock()  # Common refresh lock for all debug viewers

# -------------------------------------------------------------------------------
#                               Debug Viewer Class
# -------------------------------------------------------------------------------


class DebugViewer(object):
    """
    Class that implements common behavior of every viewers able to display debug
    values
    """

    def __init__(self, producer, debug, subscribe_tick=True):
        """
        Constructor
        @param producer: Object receiving debug value and dispatching them to
        consumers
        @param debug: Flag indicating that Viewer is debugging
        @param subscribe_tick: Flag indicating that viewer need tick value to
        synchronize
        """
        self.Debug = debug
        self.SubscribeTick = subscribe_tick

        # Flag indicating that consumer value update inhibited
        # (DebugViewer is refreshing)
        self.Inhibited = False

        # List of data consumers subscribed to DataProducer
        self.DataConsumers = {}

        # Time stamp indicating when last refresh have been initiated
        self.LastRefreshTime = gettime()
        # Flag indicating that DebugViewer has acquire common debug lock
        self.HasAcquiredLock = False
        # Lock for access to the two preceding variable
        self.AccessLock = Lock()

        # Timer to refresh Debug Viewer one last time in the case that a new
        # value have been received during refresh was inhibited and no one
        # after refresh was activated
        self.LastRefreshTimer = None
        # Lock for access to the timer
        self.TimerAccessLock = Lock()

        # Set DataProducer and subscribe tick if needed
        self.SetDataProducer(producer)

    def __del__(self):
        """
        Destructor
        """
        # Unsubscribe all data consumers
        self.UnsubscribeAllDataConsumers()

        # Delete reference to DataProducer
        self.DataProducer = None

        # Stop last refresh timer
        if self.LastRefreshTimer is not None:
            self.LastRefreshTimer.cancel()

        # Release Common debug lock if DebugViewer has acquired it
        if self.HasAcquiredLock:
            DEBUG_REFRESH_LOCK.release()

    def SetDataProducer(self, producer):
        """
        Set Data Producer
        @param producer: Data Producer
        """
        # In the case that tick need to be subscribed and DebugViewer is
        # debugging
        if self.SubscribeTick and self.Debug:

            # Subscribe tick to new data producer
            if producer is not None:
                producer.SubscribeDebugIECVariable("__tick__", self, True)

            # Unsubscribe tick from old data producer
            if getattr(self, "DataProducer", None) is not None:
                self.DataProducer.UnsubscribeDebugIECVariable("__tick__", self)

        # Save new data producer
        self.DataProducer = producer

    def IsDebugging(self):
        """
        Get flag indicating if Debug Viewer is debugging
        @return: Debugging flag
        """
        return self.Debug

    def Inhibit(self, inhibit):
        """
        Set consumer value update inhibit flag
        @param inhibit: Inhibit flag
        """
        # Inhibit every data consumers in list
        for consumer, _iec_path in self.DataConsumers.iteritems():
            consumer.Inhibit(inhibit)

        # Save inhibit flag
        self.Inhibited = inhibit

    def AddDataConsumer(self, iec_path, consumer, buffer_list=False):
        """
        Subscribe data consumer to DataProducer
        @param iec_path: Path in PLC of variable needed by data consumer
        @param consumer: Data consumer to subscribe
        @return: List of value already received [(tick, data),...] (None if
        subscription failed)
        """
        # Return immediately if no DataProducer defined
        if self.DataProducer is None:
            return None

        # Subscribe data consumer to DataProducer
        result = self.DataProducer.SubscribeDebugIECVariable(
            iec_path, consumer, buffer_list)
        if result is not None and consumer != self:

            # Store data consumer if successfully subscribed and inform
            # consumer of variable data type
            self.DataConsumers[consumer] = iec_path
            consumer.SetDataType(self.GetDataType(iec_path))

        return result

    def RemoveDataConsumer(self, consumer):
        """
        Unsubscribe data consumer from DataProducer
        @param consumer: Data consumer to unsubscribe
        """
        # Remove consumer from data consumer list
        iec_path = self.DataConsumers.pop(consumer, None)

        # Unsubscribe consumer from DataProducer
        if iec_path is not None:
            self.DataProducer.UnsubscribeDebugIECVariable(iec_path, consumer)

    def SubscribeAllDataConsumers(self):
        """
        Called to Subscribe all data consumers contained in DebugViewer.
        May be overridden by inherited classes.
        """
        # Subscribe tick if needed
        if self.SubscribeTick and self.Debug and self.DataProducer is not None:
            self.DataProducer.SubscribeDebugIECVariable("__tick__", self, True)

    def UnsubscribeAllDataConsumers(self, tick=True):
        """
        Called to Unsubscribe all data consumers.
        """
        if self.DataProducer is not None:

            # Unscribe tick if needed
            if self.SubscribeTick and tick and self.Debug:
                self.DataProducer.UnsubscribeDebugIECVariable("__tick__", self)

            # Unsubscribe all data consumers in list
            for consumer, iec_path in self.DataConsumers.iteritems():
                self.DataProducer.UnsubscribeDebugIECVariable(iec_path, consumer)

        self.DataConsumers = {}

    def GetDataType(self, iec_path):
        """
        Return variable data type.
        @param iec_path: Path in PLC of variable
        @return: variable data type (None if not found)
        """
        if self.DataProducer is not None:

            # Search for variable informations in project compilation files
            data_type = self.DataProducer.GetDebugIECVariableType(
                iec_path.upper())
            if data_type is not None:
                return data_type

            # Search for variable informations in project data
            infos = self.DataProducer.GetInstanceInfos(iec_path)
            if infos is not None:
                return infos.type

        return None

    def IsNumType(self, data_type):
        """
        Indicate if data type given is a numeric data type
        @param data_type: Data type to test
        @return: True if data type given is numeric
        """
        if self.DataProducer is not None:
            return self.DataProducer.IsNumType(data_type)

        return False

    def ForceDataValue(self, iec_path, value):
        """
        Force PLC variable value
        @param iec_path: Path in PLC of variable to force
        @param value: Value forced
        """
        if self.DataProducer is not None:
            self.DataProducer.ForceDebugIECVariable(iec_path, value)

    def ReleaseDataValue(self, iec_path):
        """
        Release PLC variable value
        @param iec_path: Path in PLC of variable to release
        """
        if self.DataProducer is not None:
            self.DataProducer.ReleaseDebugIECVariable(iec_path)

    def NewDataAvailable(self, ticks):
        """
        Called by DataProducer for each tick captured
        @param tick: PLC tick captured
        All other parameters are passed to refresh function
        """
        # Stop last refresh timer
        self.TimerAccessLock.acquire()
        if self.LastRefreshTimer is not None:
            self.LastRefreshTimer.cancel()
            self.LastRefreshTimer = None
        self.TimerAccessLock.release()

        # Only try to refresh DebugViewer if it is visible on screen and not
        # already refreshing
        if self.IsShown() and not self.Inhibited:

            # Try to get acquire common refresh lock if minimum period between
            # two refresh has expired
            if gettime() - self.LastRefreshTime > REFRESH_PERIOD and \
               DEBUG_REFRESH_LOCK.acquire(False):
                self.StartRefreshing()

            # If common lock wasn't acquired for any reason, restart last
            # refresh timer
            else:
                self.StartLastRefreshTimer()

        # In the case that DebugViewer isn't visible on screen and has already
        # acquired common refresh lock, reset DebugViewer
        elif not self.IsShown() and self.HasAcquiredLock:
            DebugViewer.RefreshNewData(self)

    def ShouldRefresh(self):
        """
        Callback function called when last refresh timer expired
        All parameters are passed to refresh function
        """
        # Cancel if DebugViewer is not visible on screen
        if self and self.IsShown():

            # Try to acquire common refresh lock
            if DEBUG_REFRESH_LOCK.acquire(False):
                self.StartRefreshing()

            # Restart last refresh timer if common refresh lock acquired failed
            else:
                self.StartLastRefreshTimer()

    def StartRefreshing(self):
        """
        Called to initiate a refresh of DebugViewer
        All parameters are passed to refresh function
        """
        # Update last refresh time stamp and flag for common refresh
        # lock acquired
        self.AccessLock.acquire()
        self.HasAcquiredLock = True
        self.LastRefreshTime = gettime()
        self.AccessLock.release()

        # Inhibit data consumer value update
        self.Inhibit(True)

        # Initiate DebugViewer refresh
        wx.CallAfter(self.RefreshNewData)

    def StartLastRefreshTimer(self):
        """
        Called to start last refresh timer for the minimum time between 2
        refresh
        All parameters are passed to refresh function
        """
        self.TimerAccessLock.acquire()
        self.LastRefreshTimer = Timer(
            REFRESH_PERIOD, self.ShouldRefresh)
        self.LastRefreshTimer.start()
        self.TimerAccessLock.release()

    def RefreshNewData(self):
        """
        Called to refresh DebugViewer according to values received by data
        consumers
        May be overridden by inherited classes
        Can receive any parameters depending on what is needed by inherited
        class
        """
        if self:
            # Activate data consumer value update
            self.Inhibit(False)

            # Release common refresh lock if acquired and update
            # last refresh time
            self.AccessLock.acquire()
            if self.HasAcquiredLock:
                DEBUG_REFRESH_LOCK.release()
                self.HasAcquiredLock = False
            if gettime() - self.LastRefreshTime > REFRESH_PERIOD:
                self.LastRefreshTime = gettime()
            self.AccessLock.release()
