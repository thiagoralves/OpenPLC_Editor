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
from builtins import str as text

from nevow import tags, loaders
import simplejson as json  # pylint: disable=import-error
import runtime.NevowServer as NS

svgfile = '%(svgfile)s'

svguiWidgets = {}

currentId = 0


def getNewId():
    global currentId
    currentId += 1
    return currentId


class SvguiWidget(object):

    def __init__(self, classname, id, **kwargs):
        self.classname = classname
        self.id = id
        self.attrs = kwargs.copy()
        self.inputs = {}
        self.outputs = {}
        self.inhibit = False
        self.changed = False

    def setinput(self, attrname, value):
        self.inputs[attrname] = value

    def getinput(self, attrname, default=None):
        if attrname not in self.inputs:
            self.inputs[attrname] = default
        return self.inputs[attrname]

    def setoutput(self, attrname, value):
        if self.outputs.get(attrname) != value:
            self.outputs[attrname] = value
            self.changed = True
            self.RefreshInterface()

    def updateoutputs(self, **kwargs):
        for attrname, value in kwargs.iteritems():
            if self.outputs.get(attrname) != value:
                self.outputs[attrname] = value
                self.changed = True
        self.RefreshInterface()

    def RefreshInterface(self):
        interface = website.getHMI()
        if isinstance(interface, SVGUI_HMI) and self.changed and not self.inhibit:
            self.changed = False
            d = interface.sendData(self)
            if d is not None:
                self.inhibit = True
                d.addCallback(self.InterfaceRefreshed)

    def InterfaceRefreshed(self, result):
        self.inhibit = False
        if self.changed:
            self.RefreshInterface()


def get_object_init_state(obj):
    # Convert objects to a dictionary of their representation
    attrs = obj.attrs.copy()
    attrs.update(obj.inputs)
    d = {
        '__class__': obj.classname,
        'id': obj.id,
        'kwargs': json.dumps(attrs),
    }
    return d


def get_object_current_state(obj):
    # Convert objects to a dictionary of their representation
    d = {
        '__class__': obj.classname,
        'id': obj.id,
        'kwargs': json.dumps(obj.outputs),
    }
    return d


class SVGUI_HMI(website.PLCHMI):
    jsClass = u"LiveSVGPage.LiveSVGWidget"

    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
        tags.xml(loaders.xmlfile(os.path.join(NS.WorkingDir, svgfile))),
    ])

    def HMIinitialisation(self):
        gadgets = []
        for gadget in svguiWidgets.values():
            gadgets.append(text(json.dumps(gadget, default=get_object_init_state, indent=2), 'ascii'))
        d = self.callRemote('init', gadgets)
        d.addCallback(self.HMIinitialised)

    def sendData(self, data):
        if self.initialised:
            return self.callRemote('receiveData', text(json.dumps(data, default=get_object_current_state, indent=2), 'ascii'))
        return None

    def setattr(self, id, attrname, value):
        svguiWidgets[id].setinput(attrname, value)


def createSVGUIControl(*args, **kwargs):
    id = getNewId()
    gad = SvguiWidget(args[0], id, **kwargs)
    svguiWidgets[id] = gad
    gadget = [text(json.dumps(gad, default=get_object_init_state, indent=2), 'ascii')]
    interface = website.getHMI()
    if isinstance(interface, SVGUI_HMI) and interface.initialised:
        interface.callRemote('init', gadget)
    return id


def setAttr(id, attrname, value):
    gad = svguiWidgets.get(id, None)
    if gad is not None:
        gad.setoutput(attrname, value)


def updateAttr(id, **kwargs):
    gad = svguiWidgets.get(id, None)
    if gad is not None:
        gad.updateoutput(**kwargs)


def getAttr(id, attrname, default=None):
    gad = svguiWidgets.get(id, None)
    if gad is not None:
        return gad.getinput(attrname, default)
    return default
