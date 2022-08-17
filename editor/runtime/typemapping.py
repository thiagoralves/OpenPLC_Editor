#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# See COPYING.Runtime file for copyrights details.
#

from __future__ import absolute_import
import ctypes
from ctypes import *
from datetime import timedelta as td

ctypes.pythonapi.PyString_AsString.argtypes = (ctypes.c_void_p,)
ctypes.pythonapi.PyString_AsString.restype = ctypes.POINTER(ctypes.c_char)


class IEC_STRING(Structure):
    """
    Must be changed according to changes in iec_types.h
    """
    _fields_ = [("len", c_uint8),
                ("body", c_char * 126)]


class IEC_TIME(Structure):
    """
    Must be changed according to changes in iec_types.h
    """
    _fields_ = [("s", c_long),   # tv_sec
                ("ns", c_long)]  # tv_nsec


def _t(t, u=lambda x: x.value, p=lambda t, x: t(x)):
    return (t, u, p)


def _ttime():
    return (IEC_TIME,
            lambda x: td(0, x.s, x.ns/1000.0),
            lambda t, x: t(x.days * 24 * 3600 + x.seconds, x.microseconds*1000))


SameEndianessTypeTranslator = {
    "BOOL":       _t(c_uint8, lambda x: x.value != 0),
    "STEP":       _t(c_uint8),
    "TRANSITION": _t(c_uint8),
    "ACTION":     _t(c_uint8),
    "SINT":       _t(c_int8),
    "USINT":      _t(c_uint8),
    "BYTE":       _t(c_uint8),
    "STRING":     (IEC_STRING,
                   lambda x: x.body[:x.len],
                   lambda t, x: t(len(x), x)),
    "INT":        _t(c_int16),
    "UINT":       _t(c_uint16),
    "WORD":       _t(c_uint16),
    "DINT":       _t(c_int32),
    "UDINT":      _t(c_uint32),
    "DWORD":      _t(c_uint32),
    "LINT":       _t(c_int64),
    "ULINT":      _t(c_uint64),
    "LWORD":      _t(c_uint64),
    "REAL":       _t(c_float),
    "LREAL":      _t(c_double),
    "TIME":       _ttime(),
    "TOD":        _ttime(),
    "DATE":       _ttime(),
    "DT":         _ttime(),
    }

SwapedEndianessTypeTranslator = {
    # TODO
    }

TypeTranslator = SameEndianessTypeTranslator

# Construct debugger natively supported types
DebugTypesSize = dict([(key, sizeof(t)) for key, (t, p, u) in SameEndianessTypeTranslator.iteritems() if t is not None])


def UnpackDebugBuffer(buff, indexes):
    res = []
    buffoffset = 0
    buffsize = len(buff)
    buffptr = cast(ctypes.pythonapi.PyString_AsString(id(buff)), c_void_p).value
    for iectype in indexes:
        c_type, unpack_func, _pack_func = \
            TypeTranslator.get(iectype, (None, None, None))

        cursor = c_void_p(buffptr + buffoffset)
        if iectype == "STRING":
            # strlen is stored in c_uint8 and sizeof(c_uint8) is 1
            # first check we can read size
            if (buffoffset + 1) <= buffsize:
                size = 1 + cast(cursor,POINTER(c_type)).contents.len
            else:
                return None
        else:
            size = sizeof(c_type)

        if c_type is not None and (buffoffset + size) <= buffsize:
            value = unpack_func(cast(cursor,
                                     POINTER(c_type)).contents)
            buffoffset += size
            res.append(value)
        else:
            return None
    if buffoffset and buffoffset == buffsize:
        return res
    return None
