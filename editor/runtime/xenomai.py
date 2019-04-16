#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# See COPYING.Runtime file for copyrights details.
#

from __future__ import absolute_import
from ctypes import CDLL, RTLD_GLOBAL, pointer, c_int, POINTER, c_char, create_string_buffer


def TryPreloadXenomai():
    """
    Xenomai 3 (at least for version <= 3.0.6) do not handle properly dlclose
    of shared objects whose dlopen did trigger xenomai_init.
    As a workaround, this pre-loads xenomai libraries that need to be
    initialized and call xenomai_init once for all.

    Xenomai auto init of libs MUST be disabled (see --auto-init-solib in xeno-config)
    """
    try:
        for name in ["cobalt", "modechk", "copperplate", "alchemy"]:
            globals()[name] = CDLL("lib"+name+".so", mode=RTLD_GLOBAL)
        cobalt.xenomai_init(pointer(c_int(0)), pointer((POINTER(c_char)*2)(create_string_buffer("prog_name"), None)))
    except Exception:
        pass
