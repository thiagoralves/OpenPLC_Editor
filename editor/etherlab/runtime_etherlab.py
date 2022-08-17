#!/usr/bin/env python
# -*- coding: utf-8 -*-

# this file is part of beremiz
#
# copyright (c) 2011-2014: laurent bessard, edouard tisserant
#                          rtes lab : crkim, jblee, youcu
#                          higen motor : donggu kang
#
# see copying file for copyrights details.

from __future__ import absolute_import
import os
import signal
import subprocess
import ctypes
from threading import Thread
import time
import re

import runtime.PLCObject as PLCObject
from runtime.loglevels import LogLevelsDict

SDOAnswered = PLCBinary.SDOAnswered
SDOAnswered.restype = None
SDOAnswered.argtypes = []

SDOThread = None
SDOProc = None
Result = None


def SDOThreadProc(*params):
    global Result, SDOProc
    if params[0] == "upload":
        cmdfmt = "ethercat upload -p %d -t %s 0x%.4x 0x%.2x"
    else:
        cmdfmt = "ethercat download -p %d -t %s 0x%.4x 0x%.2x %s"

    command = cmdfmt % params[1:]
    SDOProc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    res = SDOProc.wait()
    output = SDOProc.communicate()[0]

    if params[0] == "upload":
        Result = None
        if res == 0:
            if params[2] in ["float", "double"]:
                Result = float(output)
            elif params[2] in ["string", "octet_string", "unicode_string"]:
                Result = output
            else:
                hex_value, dec_value = output.split()
                if int(hex_value, 16) == int(dec_value):
                    Result = int(dec_value)
    else:
        Result = res == 0

    SDOAnswered()
    if res != 0:
        PLCObject.LogMessage(
            LogLevelsDict["WARNING"],
            "%s : %s" % (command, output))


def EthercatSDOUpload(pos, index, subindex, var_type):
    global SDOThread
    SDOThread = Thread(target=SDOThreadProc, args=["upload", pos, var_type, index, subindex])
    SDOThread.start()


def EthercatSDODownload(pos, index, subindex, var_type, value):
    global SDOThread
    SDOThread = Thread(target=SDOThreadProc, args=["download", pos, var_type, index, subindex, value])
    SDOThread.start()


def GetResult():
    return Result


KMSGPollThread = None
StopKMSGThread = False


def KMSGPollThreadProc():
    """
    Logs Kernel messages starting with EtherCAT
    Uses GLibc wrapper to Linux syscall "klogctl"
    Last 4 KB are polled, and lines compared to last
    captured line to detect new lines
    """
    libc = ctypes.CDLL("libc.so.6")
    klog = libc.klogctl
    klog.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    klog.restype = ctypes.c_int
    s = ctypes.create_string_buffer(4*1024)
    last = None
    while not StopKMSGThread:
        bytes_to_read = klog(3, s, len(s)-1)
        log = s.value[:bytes_to_read-1]
        if last:
            log = log.rpartition(last)[2]
        if log:
            last = log.rpartition('\n')[2]
            for lvl, msg in re.findall(
                    r'<(\d)>\[\s*\d*\.\d*\]\s*(EtherCAT\s*.*)$',
                    log, re.MULTILINE):
                PLCObject.LogMessage(
                    LogLevelsDict[{
                        "4": "WARNING",
                        "3": "CRITICAL"}.get(lvl, "DEBUG")],
                    msg)
        time.sleep(0.5)


# TODO : rename to match _runtime_{location}_extname_init() format
def _runtime_etherlab_init():
    global KMSGPollThread, StopKMSGThread
    StopKMSGThread = False
    KMSGPollThread = Thread(target=KMSGPollThreadProc)
    KMSGPollThread.start()


# TODO : rename to match _runtime_{location}_extname_cleanup() format
def _runtime_etherlab_cleanup():
    global KMSGPollThread, StopKMSGThread, SDOThread
    try:
        os.kill(SDOProc.pid, signal.SIGTERM)
    except Exception:
        pass
    SDOThread = None
    StopKMSGThread = True
    KMSGPollThread = None
