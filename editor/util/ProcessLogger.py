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
import os
import sys
import subprocess
import ctypes
from threading import Timer, Lock, Thread, Semaphore
import signal


class outputThread(Thread):
    """
    Thread is used to print the output of a command to the stdout
    """
    def __init__(self, Proc, fd, callback=None, endcallback=None):
        Thread.__init__(self)
        self.killed = False
        self.finished = False
        self.retval = None
        self.Proc = Proc
        self.callback = callback
        self.endcallback = endcallback
        self.fd = fd

    def run(self):
        outchunk = None
        self.retval = None
        while self.retval is None and not self.killed:
            if self.endcallback:
                self.retval = self.Proc.poll()
            else:
                self.retval = self.Proc.returncode

            outchunk = self.fd.readline()
            if self.callback:
                self.callback(outchunk)
        while outchunk != '' and not self.killed:
            outchunk = self.fd.readline()
            if self.callback:
                self.callback(outchunk)
        if self.endcallback:
            try:
                err = self.Proc.wait()
            except Exception:
                err = self.retval
            self.finished = True
            self.endcallback(self.Proc.pid, err)


class ProcessLogger(object):
    def __init__(self, logger, Command, finish_callback=None,
                 no_stdout=False, no_stderr=False, no_gui=True,
                 timeout=None, outlimit=None, errlimit=None,
                 endlog=None, keyword=None, kill_it=False, cwd=None,
                 encoding=None, output_encoding=None):
        self.logger = logger
        if not isinstance(Command, list):
            self.Command_str = Command
            self.Command = []
            for i, word in enumerate(Command.replace("'", '"').split('"')):
                if i % 2 == 0:
                    word = word.strip()
                    if len(word) > 0:
                        self.Command.extend(word.split())
                else:
                    self.Command.append(word)
        else:
            self.Command = Command
            self.Command_str = subprocess.list2cmdline(self.Command)

        fsencoding = sys.getfilesystemencoding()
        self.output_encoding = output_encoding

        if encoding is None:
            encoding = fsencoding
        self.Command = [self.Command[0].encode(fsencoding)]+map(
            lambda x: x.encode(encoding), self.Command[1:])

        self.finish_callback = finish_callback
        self.no_stdout = no_stdout
        self.no_stderr = no_stderr
        self.startupinfo = None
        self.errlen = 0
        self.outlen = 0
        self.errlimit = errlimit
        self.outlimit = outlimit
        self.exitcode = None
        self.outdata = []
        self.errdata = []
        self.keyword = keyword
        self.kill_it = kill_it
        self.startsem = Semaphore(0)
        self.finishsem = Semaphore(0)
        self.endlock = Lock()

        popenargs = {
            "cwd":    os.getcwd() if cwd is None else cwd,
            "stdin":  subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }

        if no_gui and os.name in ("nt", "ce"):
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            popenargs["startupinfo"] = self.startupinfo
        elif os.name == 'posix':
            popenargs["shell"] = False

        if timeout:
            self.timeout = Timer(timeout, self.endlog)
            self.timeout.start()
        else:
            self.timeout = None

        self.Proc = subprocess.Popen(self.Command, **popenargs)

        self.outt = outputThread(
            self.Proc,
            self.Proc.stdout,
            self.output,
            self.finish)
        self.outt.start()

        self.errt = outputThread(
            self.Proc,
            self.Proc.stderr,
            self.errors)
        self.errt.start()
        self.startsem.release()

    def output(self, v):
        if v and self.output_encoding:
            v = v.decode(self.output_encoding)
        self.outdata.append(v)
        self.outlen += 1
        if not self.no_stdout:
            self.logger.write(v)
        if (self.keyword and v.find(self.keyword) != -1) or (self.outlimit and self.outlen > self.outlimit):
            self.endlog()

    def errors(self, v):
        if v and self.output_encoding:
            v = v.decode(self.output_encoding)
        self.errdata.append(v)
        self.errlen += 1
        if not self.no_stderr:
            self.logger.write_warning(v)
        if self.errlimit and self.errlen > self.errlimit:
            self.endlog()

    def log_the_end(self, ecode, pid):
        self.logger.write(self.Command_str + "\n")
        self.logger.write_warning(_("exited with status {a1} (pid {a2})\n").format(a1=str(ecode), a2=str(pid)))

    def finish(self, pid, ecode):
        # avoid running function before start is finished
        self.startsem.acquire()
        self.startsem.release()
        if self.timeout:
            self.timeout.cancel()
        self.exitcode = ecode
        if self.exitcode != 0:
            self.log_the_end(ecode, pid)
        if self.finish_callback is not None:
            self.finish_callback(self, ecode, pid)
        self.errt.join()
        self.finishsem.release()

    def kill(self, gently=True):
        # avoid running kill before start is finished
        self.startsem.acquire()
        self.startsem.release()

        self.outt.killed = True
        self.errt.killed = True
        if os.name in ("nt", "ce"):
            PROCESS_TERMINATE = 1
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, self.Proc.pid)
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
        else:
            if gently:
                sig = signal.SIGTERM
            else:
                sig = signal.SIGKILL
            try:
                os.kill(self.Proc.pid, sig)
            except Exception:
                pass
        self.outt.join()
        self.errt.join()

    def endlog(self):
        if self.endlock.acquire(False):
            if not self.outt.finished and self.kill_it:
                self.kill()
            self.finishsem.release()

    def spin(self):
        self.finishsem.acquire()
        return [self.exitcode, "".join(self.outdata), "".join(self.errdata)]
