#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz runtime.
#
# Copyright (C) 2018: Edouard TISSERANT
#
# See COPYING.Runtime file for copyrights details.

from __future__ import absolute_import
import sys
from threading import Lock, Condition
import six
from six.moves import _thread


class job(object):
    """
    job to be executed by a worker
    """
    def __init__(self, call, *args, **kwargs):
        self.job = (call, args, kwargs)
        self.result = None
        self.success = False
        self.exc_info = None

    def do(self):
        """
        do the job by executing the call, and deal with exceptions
        """
        try:
            call, args, kwargs = self.job
            self.result = call(*args, **kwargs)
            self.success = True
        except Exception:
            self.success = False
            self.exc_info = sys.exc_info()


class worker(object):
    """
    serialize main thread load/unload of PLC shared objects
    """
    def __init__(self):
        # Only one job at a time
        self._finish = False
        self._threadID = None
        self.mutex = Lock()
        self.todo = Condition(self.mutex)
        self.done = Condition(self.mutex)
        self.free = Condition(self.mutex)
        self.job = None

    def reraise(self, job):
        """
        reraise exception happend in a job
        @param job: job where original exception happend
        """
        exc_type = job.exc_info[0]
        exc_value = job.exc_info[1]
        exc_traceback = job.exc_info[2]
        six.reraise(exc_type, exc_value, exc_traceback)

    def runloop(self, *args, **kwargs):
        """
        meant to be called by worker thread (blocking)
        """
        self._threadID = _thread.get_ident()
        self.mutex.acquire()
        if args or kwargs:
            _job = job(*args, **kwargs)
            _job.do()
            if not _job.success:
                self.reraise(_job)

        while not self._finish:
            self.todo.wait()
            if self.job is not None:
                self.job.do()
                self.done.notify()
            else:
                break

        self.mutex.release()

    def call(self, *args, **kwargs):
        """
        creates a job, execute it in worker thread, and deliver result.
        if job execution raise exception, re-raise same exception
        meant to be called by non-worker threads, but this is accepted.
        blocking until job done
        """

        _job = job(*args, **kwargs)

        if self._threadID == _thread.get_ident():
            # if caller is worker thread execute immediately
            _job.do()
        else:
            # otherwise notify and wait for completion
            self.mutex.acquire()

            while self.job is not None:
                self.free.wait()

            self.job = _job
            self.todo.notify()
            self.done.wait()
            self.job = None
            self.free.notify()
            self.mutex.release()

        if _job.success:
            return _job.result
        else:
            self.reraise(_job)

    def quit(self):
        """
        unblocks main thread, and terminate execution of runloop()
        """
        # mark queue
        self._finish = True
        self.mutex.acquire()
        self.job = None
        self.todo.notify()
        self.mutex.release()
