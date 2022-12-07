#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from functools import wraps
from threading import Timer
from datetime import datetime

import click

import fake_wx

from ProjectController import ProjectController
from LocalRuntimeMixin import LocalRuntimeMixin
from runtime.loglevels import LogLevelsCount, LogLevels


class Log:

    def __init__(self):
        self.crlfpending = False

    def write(self, s):
        if s:
            if self.crlfpending:
                sys.stdout.write("\n")
            sys.stdout.write(s)
            sys.stdout.flush()
            self.crlfpending = 0

    def write_error(self, s):
        if s:
            self.write("Error: "+s)

    def write_warning(self, s):
        if s:
            self.write("Warning: "+s)

    def flush(self):
        sys.stdout.flush()
        
    def isatty(self):
        return False

    def progress(self, s):
        if s:
            sys.stdout.write(s+"\r")
            self.crlfpending = True


def with_project_loaded(func):
    @wraps(func)
    def func_wrapper(self, *args, **kwargs):
        if not self.HasOpenedProject():
            if self.check_and_load_project():
                return 1 
            self.apply_config()
        return func(self, *args, **kwargs)

    return func_wrapper

def connected(func):
    @wraps(func)
    def func_wrapper(self, *args, **kwargs):
        if self._connector is None:
            if self.session.uri:
                self.BeremizRoot.setURI_location(self.session.uri)
            if not self._Connect():
                return 1
        return func(self, *args, **kwargs)

    return func_wrapper

class CLIController(LocalRuntimeMixin, ProjectController):
    def __init__(self, session):
        self.session = session
        log = Log()
        LocalRuntimeMixin.__init__(self, log, use_gui=False)
        ProjectController.__init__(self, None, log)
        self.CLIStatusTimer = None
        self.KillCLIStatusTimer = False


    def StartCLIStatusTimer(self):
        if self.CLIStatusTimer is not None:
            return
        self.CLIStatusTimer = Timer(0.5, self.CLIStatusTimerProc)
        self.KillCLIStatusTimer = False
        self.CLIStatusTimer.start()

    def StopCLIStatusTimer(self):
        if self.CLIStatusTimer is None:
            return
        self.KillCLIStatusTimer = True
        self.CLIStatusTimer.cancel()
        self.CLIStatusTimer = None

    def CLIStatusTimerProc(self):
        self.CLIStatusTimer = None
        if not self.KillCLIStatusTimer:
            self.PullPLCStatusProc(None)
            self.StartCLIStatusTimer()

    def _SetConnector(self, connector, update_status=True):
        self._connector = connector
        self.previous_log_count = [None]*LogLevelsCount
        if connector is not None:
            self.StartCLIStatusTimer()
        else:
            self.StopCLIStatusTimer()
            if update_status:
                self.UpdateMethodsFromPLCStatus()

    def UpdatePLCLog(self, log_count):
        connector = self._connector
        new_messages = []
        if connector:
            for level, count, prev in zip(
                range(LogLevelsCount), log_count, self.previous_log_count):
                if count is not None and prev != count:
                    if prev is None:
                        dump_end = max(-1, count - 10)
                    else:
                        dump_end = prev - 1
                    for msgidx in range(count-1, dump_end, -1):
                        message = connector.GetLogMessage(level, msgidx)
                        if message is not None:
                            msg, _tick, tv_sec, tv_nsec = message
                            date = datetime.utcfromtimestamp(tv_sec + tv_nsec * 1e-9)
                            txt = "%s at %s: %s\n" % (LogLevels[level], date.isoformat(' '), msg)
                            new_messages.append((date,txt))
                        else:
                            break
                self.previous_log_count[level] = count
            new_messages.sort()
            for date, txt in new_messages:
                self.logger.write(txt)

    def check_and_load_project(self):
        if not os.path.isdir(self.session.project_home):
            self.logger.write_error(
                _("\"%s\" is not a valid Beremiz project\n") % self.session.project_home)
            return True

        errmsg, error = self.LoadProject(self.session.project_home, self.session.buildpath)
        if error:
            self.logger.write_error(errmsg)
            return True

    def apply_config(self):
        for k,v in self.session.config:
            self.SetParamsAttribute("BeremizRoot."+k, v)

    @with_project_loaded
    def build_project(self, target):
        if target:
            self.SetParamsAttribute("BeremizRoot.TargetType", target)
        elif sys.platform.startswith('linux'):
            self.SetParamsAttribute("BeremizRoot.TargetType", "Linux")
        elif sys.platform.startswith('darwin'):
            self.SetParamsAttribute("BeremizRoot.TargetType", "OSX")
        elif sys.platform.startswith('win'):
            self.SetParamsAttribute("BeremizRoot.TargetType", "Win32")
            
        return 0 if self._Build() else 1

    @with_project_loaded
    @connected
    def transfer_project(self):

        return 0 if self._Transfer() else 1

    @with_project_loaded
    @connected
    def run_project(self):

        return 0 if self._Run() else 1
        
    @with_project_loaded
    @connected
    def stop_project(self):

        return 0 if self._Stop() else 1
        

    def finish(self):

        self._Disconnect()

        if not self.session.keep:
            self.KillLocalRuntime()


