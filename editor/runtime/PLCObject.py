#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz runtime.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
#
# See COPYING.Runtime file for copyrights details.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA


from __future__ import absolute_import
from threading import Thread, Lock, Semaphore, Event
import ctypes
import os
import sys
import traceback
import shutil
from time import time
import hashlib
from tempfile import mkstemp
from functools import wraps, partial
from six.moves import xrange
from past.builtins import execfile
import _ctypes

from runtime.typemapping import TypeTranslator
from runtime.loglevels import LogLevelsDefault, LogLevelsCount
from runtime.Stunnel import getPSKID
from runtime import PlcStatus
from runtime import MainWorker

if os.name in ("nt", "ce"):
    dlopen = _ctypes.LoadLibrary
    dlclose = _ctypes.FreeLibrary
elif os.name == "posix":
    dlopen = _ctypes.dlopen
    dlclose = _ctypes.dlclose


def get_last_traceback(tb):
    while tb.tb_next:
        tb = tb.tb_next
    return tb


lib_ext = {
    "linux2": ".so",
    "win32":  ".dll",
}.get(sys.platform, "")


def PLCprint(message):
    sys.stdout.write("PLCobject : "+message+"\n")
    sys.stdout.flush()


def RunInMain(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        return MainWorker.call(func, *args, **kwargs)
    return func_wrapper


class PLCObject(object):
    def __init__(self, WorkingDir, argv, statuschange, evaluator, pyruntimevars):
        self.workingdir = WorkingDir  # must exits already
        self.tmpdir = os.path.join(WorkingDir, 'tmp')
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)
        os.mkdir(self.tmpdir)
        # FIXME : is argv of any use nowadays ?
        self.argv = [WorkingDir] + argv  # force argv[0] to be "path" to exec...
        self.statuschange = statuschange
        self.evaluator = evaluator
        self.pyruntimevars = pyruntimevars
        self.PLCStatus = PlcStatus.Empty
        self.PLClibraryHandle = None
        self.PLClibraryLock = Lock()
        # Creates fake C funcs proxies
        self._InitPLCStubCalls()
        self._loading_error = None
        self.python_runtime_vars = None
        self.TraceThread = None
        self.TraceLock = Lock()
        self.Traces = []
        self.DebugToken = 0

        self._init_blobs()

    # First task of worker -> no @RunInMain
    def AutoLoad(self, autostart):
        # Get the last transfered PLC
        try:
            self.CurrentPLCFilename = open(
                self._GetMD5FileName(),
                "r").read().strip() + lib_ext
            if self.LoadPLC():
                self.PLCStatus = PlcStatus.Stopped
                if autostart:
                    self.StartPLC()
                    return
        except Exception:
            self.PLCStatus = PlcStatus.Empty
            self.CurrentPLCFilename = None

        self.StatusChange()

    def StatusChange(self):
        if self.statuschange is not None:
            for callee in self.statuschange:
                callee(self.PLCStatus)

    @RunInMain
    def LogMessage(self, *args):
        if len(args) == 2:
            level, msg = args
        else:
            level = LogLevelsDefault
            msg, = args
        PLCprint(msg)
        if self._LogMessage is not None:
            return self._LogMessage(level, msg, len(msg))
        return None

    @RunInMain
    def ResetLogCount(self):
        if self._ResetLogCount is not None:
            self._ResetLogCount()

    # used internaly
    def GetLogCount(self, level):
        if self._GetLogCount is not None:
            return int(self._GetLogCount(level))
        elif self._loading_error is not None and level == 0:
            return 1

    @RunInMain
    def GetLogMessage(self, level, msgid):
        tick = ctypes.c_uint32()
        tv_sec = ctypes.c_uint32()
        tv_nsec = ctypes.c_uint32()
        if self._GetLogMessage is not None:
            maxsz = len(self._log_read_buffer)-1
            sz = self._GetLogMessage(level, msgid,
                                     self._log_read_buffer, maxsz,
                                     ctypes.byref(tick),
                                     ctypes.byref(tv_sec),
                                     ctypes.byref(tv_nsec))
            if sz and sz <= maxsz:
                self._log_read_buffer[sz] = '\x00'
                return self._log_read_buffer.value, tick.value, tv_sec.value, tv_nsec.value
        elif self._loading_error is not None and level == 0:
            return self._loading_error, 0, 0, 0
        return None

    def _GetMD5FileName(self):
        return os.path.join(self.workingdir, "lasttransferedPLC.md5")

    def _GetLibFileName(self):
        return os.path.join(self.workingdir, self.CurrentPLCFilename)

    def _LoadPLC(self):
        """
        Load PLC library
        Declare all functions, arguments and return values
        """
        md5 = open(self._GetMD5FileName(), "r").read()
        self.PLClibraryLock.acquire()
        try:
            self._PLClibraryHandle = dlopen(self._GetLibFileName())
            self.PLClibraryHandle = ctypes.CDLL(self.CurrentPLCFilename, handle=self._PLClibraryHandle)

            self.PLC_ID = ctypes.c_char_p.in_dll(self.PLClibraryHandle, "PLC_ID")
            if len(md5) == 32:
                self.PLC_ID.value = md5

            self._startPLC = self.PLClibraryHandle.startPLC
            self._startPLC.restype = ctypes.c_int
            self._startPLC.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]

            self._stopPLC_real = self.PLClibraryHandle.stopPLC
            self._stopPLC_real.restype = None

            self._PythonIterator = getattr(self.PLClibraryHandle, "PythonIterator", None)
            if self._PythonIterator is not None:
                self._PythonIterator.restype = ctypes.c_char_p
                self._PythonIterator.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]

                self._stopPLC = self._stopPLC_real
            else:
                # If python confnode is not enabled, we reuse _PythonIterator
                # as a call that block pythonthread until StopPLC
                self.PlcStopping = Event()

                def PythonIterator(res, blkid):
                    self.PlcStopping.clear()
                    self.PlcStopping.wait()
                    return None
                self._PythonIterator = PythonIterator

                def __StopPLC():
                    self._stopPLC_real()
                    self.PlcStopping.set()
                self._stopPLC = __StopPLC

            self._ResetDebugVariables = self.PLClibraryHandle.ResetDebugVariables
            self._ResetDebugVariables.restype = None

            self._RegisterDebugVariable = self.PLClibraryHandle.RegisterDebugVariable
            self._RegisterDebugVariable.restype = None
            self._RegisterDebugVariable.argtypes = [ctypes.c_int, ctypes.c_void_p]

            self._FreeDebugData = self.PLClibraryHandle.FreeDebugData
            self._FreeDebugData.restype = None

            self._GetDebugData = self.PLClibraryHandle.GetDebugData
            self._GetDebugData.restype = ctypes.c_int
            self._GetDebugData.argtypes = [ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_void_p)]

            self._suspendDebug = self.PLClibraryHandle.suspendDebug
            self._suspendDebug.restype = ctypes.c_int
            self._suspendDebug.argtypes = [ctypes.c_int]

            self._resumeDebug = self.PLClibraryHandle.resumeDebug
            self._resumeDebug.restype = None

            self._ResetLogCount = self.PLClibraryHandle.ResetLogCount
            self._ResetLogCount.restype = None

            self._GetLogCount = self.PLClibraryHandle.GetLogCount
            self._GetLogCount.restype = ctypes.c_uint32
            self._GetLogCount.argtypes = [ctypes.c_uint8]

            self._LogMessage = self.PLClibraryHandle.LogMessage
            self._LogMessage.restype = ctypes.c_int
            self._LogMessage.argtypes = [ctypes.c_uint8, ctypes.c_char_p, ctypes.c_uint32]

            self._log_read_buffer = ctypes.create_string_buffer(1 << 14)  # 16K
            self._GetLogMessage = self.PLClibraryHandle.GetLogMessage
            self._GetLogMessage.restype = ctypes.c_uint32
            self._GetLogMessage.argtypes = [ctypes.c_uint8, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]

            self._loading_error = None

        except Exception:
            self._loading_error = traceback.format_exc()
            PLCprint(self._loading_error)
            return False
        finally:
            self.PLClibraryLock.release()

        return True

    @RunInMain
    def LoadPLC(self):
        res = self._LoadPLC()
        if res:
            self.PythonRuntimeInit()
        else:
            self._FreePLC()

        return res

    @RunInMain
    def UnLoadPLC(self):
        self.PythonRuntimeCleanup()
        self._FreePLC()

    def _InitPLCStubCalls(self):
        """
        create dummy C func proxies
        """
        self._startPLC = lambda x, y: None
        self._stopPLC = lambda: None
        self._ResetDebugVariables = lambda: None
        self._RegisterDebugVariable = lambda x, y: None
        self._IterDebugData = lambda x, y: None
        self._FreeDebugData = lambda: None
        self._GetDebugData = lambda: -1
        self._suspendDebug = lambda x: -1
        self._resumeDebug = lambda: None
        self._PythonIterator = lambda: ""
        self._GetLogCount = None
        self._LogMessage = None
        self._GetLogMessage = None
        self._PLClibraryHandle = None
        self.PLClibraryHandle = None

    def _FreePLC(self):
        """
        Unload PLC library.
        This is also called by __init__ to create dummy C func proxies
        """
        self.PLClibraryLock.acquire()
        try:
            # Unload library explicitely
            if getattr(self, "_PLClibraryHandle", None) is not None:
                dlclose(self._PLClibraryHandle)

            # Forget all refs to library
            self._InitPLCStubCalls()

        finally:
            self.PLClibraryLock.release()

        return False

    def PythonRuntimeCall(self, methodname):
        """
        Calls init, start, stop or cleanup method provided by
        runtime python files, loaded when new PLC uploaded
        """
        for method in self.python_runtime_vars.get("_runtime_%s" % methodname, []):
            _res, exp = self.evaluator(method)
            if exp is not None:
                self.LogMessage(0, '\n'.join(traceback.format_exception(*exp)))

    # used internaly
    def PythonRuntimeInit(self):
        MethodNames = ["init", "start", "stop", "cleanup"]
        self.python_runtime_vars = globals().copy()
        self.python_runtime_vars.update(self.pyruntimevars)
        parent = self

        class PLCSafeGlobals(object):
            def __getattr__(self, name):
                try:
                    t = parent.python_runtime_vars["_"+name+"_ctype"]
                except KeyError:
                    raise KeyError("Try to get unknown shared global variable : %s" % name)
                v = t()
                parent.python_runtime_vars["_PySafeGetPLCGlob_"+name](ctypes.byref(v))
                return parent.python_runtime_vars["_"+name+"_unpack"](v)

            def __setattr__(self, name, value):
                try:
                    t = parent.python_runtime_vars["_"+name+"_ctype"]
                except KeyError:
                    raise KeyError("Try to set unknown shared global variable : %s" % name)
                v = parent.python_runtime_vars["_"+name+"_pack"](t, value)
                parent.python_runtime_vars["_PySafeSetPLCGlob_"+name](ctypes.byref(v))

        self.python_runtime_vars.update({
            "PLCGlobals":     PLCSafeGlobals(),
            "WorkingDir":     self.workingdir,
            "PLCObject":      self,
            "PLCBinary":      self.PLClibraryHandle,
            "PLCGlobalsDesc": []})

        for methodname in MethodNames:
            self.python_runtime_vars["_runtime_%s" % methodname] = []

        try:
            filenames = os.listdir(self.workingdir)
            filenames.sort()
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if name.upper().startswith("RUNTIME") and ext.upper() == ".PY":
                    execfile(os.path.join(self.workingdir, filename), self.python_runtime_vars)
                    for methodname in MethodNames:
                        method = self.python_runtime_vars.get("_%s_%s" % (name, methodname), None)
                        if method is not None:
                            self.python_runtime_vars["_runtime_%s" % methodname].append(method)
        except Exception:
            self.LogMessage(0, traceback.format_exc())
            raise

        self.PythonRuntimeCall("init")

    # used internaly
    def PythonRuntimeCleanup(self):
        if self.python_runtime_vars is not None:
            self.PythonRuntimeCall("cleanup")

        self.python_runtime_vars = None

    def PythonThreadProc(self):
        self.StartSem.release()
        res, cmd, blkid = "None", "None", ctypes.c_void_p()
        compile_cache = {}
        while True:
            cmd = self._PythonIterator(res, blkid)
            FBID = blkid.value
            if cmd is None:
                break
            try:
                self.python_runtime_vars["FBID"] = FBID
                ccmd, AST = compile_cache.get(FBID, (None, None))
                if ccmd is None or ccmd != cmd:
                    AST = compile(cmd, '<plc>', 'eval')
                    compile_cache[FBID] = (cmd, AST)
                result, exp = self.evaluator(eval, AST, self.python_runtime_vars)
                if exp is not None:
                    res = "#EXCEPTION : "+str(exp[1])
                    self.LogMessage(1, ('PyEval@0x%x(Code="%s") Exception "%s"') % (
                        FBID, cmd, '\n'.join(traceback.format_exception(*exp))))
                else:
                    res = str(result)
                self.python_runtime_vars["FBID"] = None
            except Exception as e:
                res = "#EXCEPTION : "+str(e)
                self.LogMessage(1, ('PyEval@0x%x(Code="%s") Exception "%s"') % (FBID, cmd, str(e)))

    @RunInMain
    def StartPLC(self):
        if self.CurrentPLCFilename is not None and self.PLCStatus == PlcStatus.Stopped:
            c_argv = ctypes.c_char_p * len(self.argv)
            res = self._startPLC(len(self.argv), c_argv(*self.argv))
            if res == 0:
                self.PLCStatus = PlcStatus.Started
                self.StatusChange()
                self.PythonRuntimeCall("start")
                self.StartSem = Semaphore(0)
                self.PythonThread = Thread(target=self.PythonThreadProc)
                self.PythonThread.start()
                self.StartSem.acquire()
                self.LogMessage("PLC started")
            else:
                self.LogMessage(0, _("Problem starting PLC : error %d" % res))
                self.PLCStatus = PlcStatus.Broken
                self.StatusChange()

    @RunInMain
    def StopPLC(self):
        if self.PLCStatus == PlcStatus.Started:
            self.LogMessage("PLC stopped")
            self._stopPLC()
            self.PythonThread.join()
            self.PLCStatus = PlcStatus.Stopped
            self.StatusChange()
            self.PythonRuntimeCall("stop")
            if self.TraceThread is not None:
                self.TraceThread.join()
                self.TraceThread = None
            return True
        return False

    @RunInMain
    def GetPLCstatus(self):
        return self.PLCStatus, map(self.GetLogCount, xrange(LogLevelsCount))

    @RunInMain
    def GetPLCID(self):
        return getPSKID(partial(self.LogMessage, 0))

    def _init_blobs(self):
        self.blobs = {}
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)
        os.mkdir(self.tmpdir)

    @RunInMain
    def SeedBlob(self, seed):
        blob = (mkstemp(dir=self.tmpdir) + (hashlib.new('md5'),))
        _fobj, _path, md5sum = blob
        md5sum.update(seed)
        newBlobID = md5sum.digest()
        self.blobs[newBlobID] = blob
        return newBlobID

    @RunInMain
    def AppendChunkToBlob(self, data, blobID):
        blob = self.blobs.pop(blobID, None)

        if blob is None:
            return None

        fobj, _path, md5sum = blob
        md5sum.update(data)
        newBlobID = md5sum.digest()
        os.write(fobj, data)
        self.blobs[newBlobID] = blob
        return newBlobID

    @RunInMain
    def PurgeBlobs(self):
        for fobj, _path, _md5sum in self.blobs:
            os.close(fobj)
        self._init_blobs()

    def _BlobAsFile(self, blobID, newpath):
        blob = self.blobs.pop(blobID, None)

        if blob is None:
            raise Exception(_("Missing data to create file: {}").format(newpath))

        fobj, path, _md5sum = blob
        os.close(fobj)
        shutil.move(path, newpath)

    @RunInMain
    def NewPLC(self, md5sum, plc_object, extrafiles):
        if self.PLCStatus in [PlcStatus.Stopped, PlcStatus.Empty, PlcStatus.Broken]:
            NewFileName = md5sum + lib_ext
            extra_files_log = os.path.join(self.workingdir, "extra_files.txt")

            old_PLC_filename = os.path.join(self.workingdir, self.CurrentPLCFilename) \
                if self.CurrentPLCFilename is not None \
                else None
            new_PLC_filename = os.path.join(self.workingdir, NewFileName)

            self.UnLoadPLC()

            self.LogMessage("NewPLC (%s)" % md5sum)
            self.PLCStatus = PlcStatus.Empty

            try:
                os.remove(old_PLC_filename)
                for filename in open(extra_files_log, "rt").readlines() + [extra_files_log]:
                    try:
                        os.remove(os.path.join(self.workingdir, filename.strip()))
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                # Create new PLC file
                self._BlobAsFile(plc_object, new_PLC_filename)

                # Store new PLC filename based on md5 key
                open(self._GetMD5FileName(), "w").write(md5sum)

                # Then write the files
                log = open(extra_files_log, "w")
                for fname, blobID in extrafiles:
                    fpath = os.path.join(self.workingdir, fname)
                    self._BlobAsFile(blobID, fpath)
                    log.write(fname+'\n')

                # Store new PLC filename
                self.CurrentPLCFilename = NewFileName
            except Exception:
                self.PLCStatus = PlcStatus.Broken
                self.StatusChange()
                PLCprint(traceback.format_exc())
                return False

            if self.LoadPLC():
                self.PLCStatus = PlcStatus.Stopped
            else:
                self.PLCStatus = PlcStatus.Broken
            self.StatusChange()

            return self.PLCStatus == PlcStatus.Stopped
        return False

    def MatchMD5(self, MD5):
        try:
            last_md5 = open(self._GetMD5FileName(), "r").read()
            return last_md5 == MD5
        except Exception:
            pass
        return False

    @RunInMain
    def SetTraceVariablesList(self, idxs):
        """
        Call ctype imported function to append
        these indexes to registred variables in PLC debugger
        """
        self.DebugToken += 1
        if idxs:
            # suspend but dont disable
            if self._suspendDebug(False) == 0:
                # keep a copy of requested idx
                self._ResetDebugVariables()
                for idx, iectype, force in idxs:
                    if force is not None:
                        c_type, _unpack_func, pack_func = \
                            TypeTranslator.get(iectype,
                                               (None, None, None))
                        force = ctypes.byref(pack_func(c_type, force))
                    self._RegisterDebugVariable(idx, force)
                self._TracesSwap()
                self._resumeDebug()
                return self.DebugToken
        else:
            self._suspendDebug(True)
        return None

    def _TracesSwap(self):
        self.LastSwapTrace = time()
        if self.TraceThread is None and self.PLCStatus == PlcStatus.Started:
            self.TraceThread = Thread(target=self.TraceThreadProc)
            self.TraceThread.start()
        self.TraceLock.acquire()
        Traces = self.Traces
        self.Traces = []
        self.TraceLock.release()
        return Traces

    @RunInMain
    def GetTraceVariables(self, DebugToken):
        if DebugToken is not None and DebugToken == self.DebugToken:
            return self.PLCStatus, self._TracesSwap()
        return PlcStatus.Broken, []

    def TraceThreadProc(self):
        """
        Return a list of traces, corresponding to the list of required idx
        """
        self._resumeDebug()  # Re-enable debugger
        while self.PLCStatus == PlcStatus.Started:
            tick = ctypes.c_uint32()
            size = ctypes.c_uint32()
            buff = ctypes.c_void_p()
            TraceBuffer = None

            self.PLClibraryLock.acquire()

            res = self._GetDebugData(ctypes.byref(tick),
                                     ctypes.byref(size),
                                     ctypes.byref(buff))
            if res == 0:
                if size.value:
                    TraceBuffer = ctypes.string_at(buff.value, size.value)
                self._FreeDebugData()

            self.PLClibraryLock.release()

            # leave thread if GetDebugData isn't happy.
            if res != 0:
                break

            if TraceBuffer is not None:
                self.TraceLock.acquire()
                lT = len(self.Traces)
                if lT != 0 and lT * len(self.Traces[0]) > 1024 * 1024:
                    self.Traces.pop(0)
                self.Traces.append((tick.value, TraceBuffer))
                self.TraceLock.release()

            # TraceProc stops here if Traces not polled for 3 seconds
            traces_age = time() - self.LastSwapTrace
            if traces_age > 3:
                self.TraceLock.acquire()
                self.Traces = []
                self.TraceLock.release()
                self._suspendDebug(True)  # Disable debugger
                break

        self.TraceThread = None

    def RemoteExec(self, script, *kwargs):
        try:
            exec(script, kwargs)
        except Exception:
            _e_type, e_value, e_traceback = sys.exc_info()
            line_no = traceback.tb_lineno(get_last_traceback(e_traceback))
            return (-1, "RemoteExec script failed!\n\nLine %d: %s\n\t%s" %
                    (line_no, e_value, script.splitlines()[line_no - 1]))
        return (0, kwargs.get("returnVal", None))
