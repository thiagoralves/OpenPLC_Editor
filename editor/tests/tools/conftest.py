#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2017: Andrey Skvortsov
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

# import pytest
# import xvfbwrapper


def init_environment():
    """Append module root directory to sys.path"""
    try:
        import Beremiz as _Beremiz
    except ImportError:
        sys.path.append(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), '..', '..')
            )
        )


init_environment()

#
# Something seems to be broken in Beremiz application,
# because after tests in test_application.py during Xvfb shutdown
# pytest returns error message:
# pytest: Fatal IO error 11 (Die Ressource ist zur Zeit nicht verfügbar) on X server :2821.
#
# As a result of that pytest returns code 1 as some tests were failed,
# but they aren't.
#
# To avoid this Xvfb is launched and killed not by pytest.
# $ Xvfb :42 -screen 0 1280x1024x24 &
# $ export DISPLAY=:42
# $ pytest --timeout=10 ./tests/tools
# $ pkill -9 Xvfb
#
# TODO: find root of this problem.


# vdisplay = None
#
# @pytest.fixture(scope="session", autouse=True)
# def start_xvfb_server(request):
#     global vdisplay
#     vdisplay = xvfbwrapper.Xvfb(width=1280, height=720)
#     vdisplay.start()
#     request.addfinalizer(stop_xvfb_server)
#
# def stop_xvfb_server():
#     if vdisplay is not None:
#         vdisplay.stop()
