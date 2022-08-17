# vi: set ft=python sw=4 ts=4 et:

'''monotonic time for Python 2 and 3, on Linux, FreeBSD, Mac OS X, and Windows.

Copyright 2010, 2011, 2017 Gavin Beatty <gavinbeatty@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from __future__ import print_function
from __future__ import unicode_literals

__author__ = 'Gavin Beatty <gavinbeatty@gmail.com>'
__version__ = '2.1.0.dev0'
__date__ = '2017-05-28'
__all__ = ['monotonic']

import contextlib
import ctypes
import errno
import os
import platform
import sys
import time

_machine64 = (platform.machine(), sys.maxsize > 2**32)


class _NS():
    pass


class _mach_timespec(ctypes.Structure):
    _fields_ = [('tv_sec', ctypes.c_uint), ('tv_nsec', ctypes.c_int)]


class _posix_timespec(ctypes.Structure):
    _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]


def _timespec_to_seconds(ts):
    return float(ts.tv_sec) + float(ts.tv_nsec) * 1e-9


def _get_ctypes_libmacho_macho_functions():
    libmacho = ctypes.CDLL('/usr/lib/system/libmacho.dylib', use_errno=True)
    macho = _NS()
    macho.get_host = libmacho.mach_host_self
    macho.get_host.argtypes = []
    macho.get_host.restype = ctypes.c_uint
    macho.get_clock = libmacho.host_get_clock_service
    macho.get_clock.argtypes = [ctypes.c_uint,
                                ctypes.c_int,
                                ctypes.POINTER(ctypes.c_uint)
                                ]
    macho.get_time = libmacho.clock_get_time
    macho.get_time.argtypes = [ctypes.c_uint, ctypes.POINTER(_mach_timespec)]
    macho.deallocate = libmacho.mach_port_deallocate
    macho.deallocate.argtypes = [ctypes.c_uint, ctypes.c_uint]
    return libmacho, macho


def _get_ctypes_clock_gettime(library):
    clock_gettime = ctypes.CDLL(library, use_errno=True).clock_gettime
    clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(_posix_timespec)]
    return clock_gettime


def _call_ctypes_clock_gettime(clock_gettime, clockid):
    timespec = _posix_timespec()
    ret = clock_gettime(clockid, ctypes.pointer(timespec))
    if int(ret) != 0:
        errno_ = ctypes.get_errno()
        raise OSError(errno_, os.strerror(errno_))
    return timespec


_py_monotonic = getattr(time, 'monotonic', None)
if _py_monotonic is not None:
    monotonic = _py_monotonic
elif sys.platform.startswith('linux'):
    _clock_gettime = _get_ctypes_clock_gettime('librt.so.1')

    def monotonic():
        clockid = ctypes.c_int(1)
        timespec = _call_ctypes_clock_gettime(_clock_gettime, clockid)
        return _timespec_to_seconds(timespec)
elif sys.platform.startswith('freebsd'):
    _clock_gettime = _get_ctypes_clock_gettime('libc.so')

    def monotonic():
        clockid = ctypes.c_int(4)
        timespec = _call_ctypes_clock_gettime(_clock_gettime, clockid)
        return _timespec_to_seconds(timespec)
elif sys.platform.startswith('darwin') and _machine64 == ('x86_64', True):
    _libmacho, _macho = _get_ctypes_libmacho_macho_functions()

    @contextlib.contextmanager
    def _deallocate(task, port):
        try:
            yield
        finally:
            if int(_macho.deallocate(task, port)) == 0:
                return
            errno_ = ctypes.get_errno()
            raise OSError(errno_, os.strerror(errno_))

    def monotonic():
        task = ctypes.c_uint.in_dll(_libmacho, 'mach_task_self_')
        host = _macho.get_host()
        with _deallocate(task, host):
            clock = ctypes.c_uint(0)
            clockid = ctypes.c_int(0)
            ret = _macho.get_clock(host, clockid, ctypes.pointer(clock))
            if int(ret) != 0:
                errno_ = ctypes.get_errno()
                raise OSError(errno_, os.strerror(errno_))
            with _deallocate(task, clock):
                timespec = _mach_timespec()
                ret = _macho.get_time(clock, ctypes.pointer(timespec))
                if int(ret) != 0:
                    errno_ = ctypes.get_errno()
                    raise OSError(errno_, os.strerror(errno_))
                return _timespec_to_seconds(timespec)
elif sys.platform.startswith('win32'):
    _GetTickCount = getattr(ctypes.windll.kernel32, 'GetTickCount64', None)

    if _GetTickCount is not None:
        _GetTickCount.restype = ctypes.c_uint64
    else:
        _GetTickCount = ctypes.windll.kernel32.GetTickCount
        _GetTickCount.restype = ctypes.c_uint32

    def monotonic():
        return float(_GetTickCount()) * 1e-3
else:
    def monotonic():
        msg = 'monotonic not supported on your platform'
        raise OSError(errno.ENOSYS, msg)


if __name__ == '__main__':
    print(monotonic())
