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
from __future__ import print_function
import time
import json
import os
import re
from builtins import str as text
from autobahn.twisted import wamp
from autobahn.twisted.websocket import WampWebSocketClientFactory, connectWS
from autobahn.wamp import types, auth
from autobahn.wamp.serializer import MsgPackSerializer
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.python.components import registerAdapter

from formless import annotate, webform
import formless
from nevow import tags, url, static
from runtime import GetPLCObjectSingleton

mandatoryConfigItems = ["ID", "active", "realm", "url"]

_transportFactory = None
_WampSession = None
_PySrv = None
WorkingDir = None

# Find pre-existing project WAMP config file
_WampConf = None
_WampSecret = None

ExposedCalls = [
    ("StartPLC", {}),
    ("StopPLC", {}),
    ("GetPLCstatus", {}),
    ("GetPLCID", {}),
    ("SeedBlob", {}),
    ("AppendChunkToBlob", {}),
    ("PurgeBlobs", {}),
    ("NewPLC", {}),
    ("MatchMD5", {}),
    ("SetTraceVariablesList", {}),
    ("GetTraceVariables", {}),
    ("RemoteExec", {}),
    ("GetLogMessage", {}),
    ("ResetLogCount", {})
]

# de-activated dumb wamp config
defaultWampConfig = {
    "ID": "wamptest",
    "active": False,
    "realm": "Automation",
    "url": "ws://127.0.0.1:8888"
}

# Those two lists are meant to be filled by customized runtime
# or User python code.

""" crossbar Events to register to """
SubscribedEvents = []

""" things to do on join (callables) """
DoOnJoin = []

lastKnownConfig = None


def GetCallee(name):
    """ Get Callee or Subscriber corresponding to '.' spearated object path """
    names = name.split('.')
    obj = GetPLCObjectSingleton()
    while names:
        obj = getattr(obj, names.pop(0))
    return obj


class WampSession(wamp.ApplicationSession):

    def onConnect(self):
        if "secret" in self.config.extra:
            user = self.config.extra["ID"]
            self.join(u"Automation", [u"wampcra"], user)
        else:
            self.join(u"Automation")

    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            if "secret" in self.config.extra:
                secret = self.config.extra["secret"].encode('utf8')
                signature = auth.compute_wcs(
                    secret, challenge.extra['challenge'].encode('utf8'))
                return signature.decode("ascii")
            else:
                raise Exception("no secret given for authentication")
        else:
            raise Exception(
                "don't know how to handle authmethod {}".format(challenge.method))

    def onJoin(self, details):
        global _WampSession
        _WampSession = self
        ID = self.config.extra["ID"]

        for name, kwargs in ExposedCalls:
            try:
                registerOptions = types.RegisterOptions(**kwargs)
            except TypeError as e:
                registerOptions = None
                print(_("TypeError register option: {}".format(e)))

            self.register(GetCallee(name), u'.'.join((ID, name)), registerOptions)

        for name in SubscribedEvents:
            self.subscribe(GetCallee(name), text(name))

        for func in DoOnJoin:
            func(self)

        print(_('WAMP session joined (%s) by:' % time.ctime()), ID)

    def onLeave(self, details):
        global _WampSession, _transportFactory
        super(WampSession, self).onLeave(details)
        _WampSession = None
        _transportFactory = None
        print(_('WAMP session left'))

    def publishWithOwnID(self, eventID, value):
        ID = self.config.extra["ID"]
        self.publish(text(ID+'.'+eventID), value)


class ReconnectingWampWebSocketClientFactory(WampWebSocketClientFactory, ReconnectingClientFactory):

    def __init__(self, config, *args, **kwargs):
        global _transportFactory
        WampWebSocketClientFactory.__init__(self, *args, **kwargs)

        try:
            protocolOptions = config.extra.get('protocolOptions', None)
            if protocolOptions:
                self.setProtocolOptions(**protocolOptions)
            _transportFactory = self
        except Exception as e:
            print(_("Custom protocol options failed :"), e)
            _transportFactory = None

    def buildProtocol(self, addr):
        self.resetDelay()
        return ReconnectingClientFactory.buildProtocol(self, addr)

    def clientConnectionFailed(self, connector, reason):
        print(_("WAMP Client connection failed (%s) .. retrying ..") %
              time.ctime())
        super(ReconnectingWampWebSocketClientFactory,
              self).clientConnectionFailed(connector, reason)

    def clientConnectionLost(self, connector, reason):
        print(_("WAMP Client connection lost (%s) .. retrying ..") %
              time.ctime())
        super(ReconnectingWampWebSocketClientFactory,
              self).clientConnectionFailed(connector, reason)


def CheckConfiguration(WampClientConf):
    url = WampClientConf["url"]
    if not IsCorrectUri(url):
        raise annotate.ValidateError(
            {"url": "Invalid URL: {}".format(url)},
            _("WAMP configuration error:"))


def GetConfiguration():
    global lastKnownConfig

    if os.path.exists(_WampConf):
        WampClientConf = json.load(open(_WampConf))
    else:
        WampClientConf = defaultWampConfig.copy()

    for itemName in mandatoryConfigItems:
        if WampClientConf.get(itemName, None) is None:
            raise Exception(
                _("WAMP configuration error : missing '{}' parameter.").format(itemName))

    CheckConfiguration(WampClientConf)

    lastKnownConfig = WampClientConf.copy()
    return WampClientConf


def SetWampSecret(wampSecret):
    with open(os.path.realpath(_WampSecret), 'w') as f:
        f.write(wampSecret)


def SetConfiguration(WampClientConf):
    global lastKnownConfig

    CheckConfiguration(WampClientConf)

    lastKnownConfig = WampClientConf.copy()

    with open(os.path.realpath(_WampConf), 'w') as f:
        json.dump(WampClientConf, f, sort_keys=True, indent=4)
    StopReconnectWampClient()
    if 'active' in WampClientConf and WampClientConf['active']:
        StartReconnectWampClient()

    return WampClientConf


def LoadWampSecret(secretfname):
    WSClientWampSecret = open(secretfname, 'rb').read()
    if len(WSClientWampSecret) == 0:
        raise Exception(_("WAMP secret empty"))
    return WSClientWampSecret


def IsCorrectUri(uri):
    return re.match(r'wss?://[^\s?:#-]+(:[0-9]+)?(/[^\s]*)?$', uri) is not None


def RegisterWampClient(wampconf=None, wampsecret=None):
    global _WampConf, _WampSecret
    _WampConfDefault = os.path.join(WorkingDir, "wampconf.json")
    _WampSecretDefault = os.path.join(WorkingDir, "wamp.secret")

    # set config file path only if not already set
    if _WampConf is None:
        # default project's wampconf has precedance over commandline given
        if os.path.exists(_WampConfDefault) or wampconf is None:
            _WampConf = _WampConfDefault
        else:
            _WampConf = wampconf

    WampClientConf = GetConfiguration()

    # set secret file path only if not already set
    if _WampSecret is None:
        # default project's wamp secret also
        # has precedance over commandline given
        if os.path.exists(_WampSecretDefault):
            _WampSecret = _WampSecretDefault
        else:
            _WampSecret = wampsecret

    if _WampSecret is not None:
        WampClientConf["secret"] = LoadWampSecret(_WampSecret)
    else:
        print(_("WAMP authentication has no secret configured"))
        _WampSecret = _WampSecretDefault

    if not WampClientConf["active"]:
        print(_("WAMP deactivated in configuration"))
        return

    # create a WAMP application session factory
    component_config = types.ComponentConfig(
        realm=WampClientConf["realm"],
        extra=WampClientConf)
    session_factory = wamp.ApplicationSessionFactory(
        config=component_config)
    session_factory.session = WampSession

    # create a WAMP-over-WebSocket transport client factory
    ReconnectingWampWebSocketClientFactory(
        component_config,
        session_factory,
        url=WampClientConf["url"],
        serializers=[MsgPackSerializer()])

    # start the client from a Twisted endpoint
    if _transportFactory:
        connectWS(_transportFactory)
        print(_("WAMP client connecting to :"), WampClientConf["url"])
        return True
    else:
        print(_("WAMP client can not connect to :"), WampClientConf["url"])
        return False


def StopReconnectWampClient():
    if _transportFactory is not None:
        _transportFactory.stopTrying()
    if _WampSession is not None:
        _WampSession.leave()


def StartReconnectWampClient():
    if _WampSession:
        # do reconnect
        _WampSession.disconnect()
        return True
    else:
        # do connect
        RegisterWampClient()
        return True


def GetSession():
    return _WampSession


def getWampStatus():
    if _transportFactory is not None:
        if _WampSession is not None:
            if _WampSession.is_attached():
                return "Attached"
            return "Established"
        return "Connecting"
    return "Disconnected"


def SetServer(pysrv):
    global _PySrv
    _PySrv = pysrv


def PublishEvent(eventID, value):
    if getWampStatus() == "Attached":
        _WampSession.publish(text(eventID), value)


def PublishEventWithOwnID(eventID, value):
    if getWampStatus() == "Attached":
        _WampSession.publishWithOwnID(text(eventID), value)


# WEB CONFIGURATION INTERFACE
WAMP_SECRET_URL = "secret"
webExposedConfigItems = ['active', 'url', 'ID']


def wampConfigDefault(ctx, argument):
    if lastKnownConfig is not None:
        return lastKnownConfig.get(argument.name, None)


def wampConfig(**kwargs):
    secretfile_field = kwargs["secretfile"]
    if secretfile_field is not None:
        secretfile = getattr(secretfile_field, "file", None)
        if secretfile is not None:
            secret = secretfile_field.file.read()
            SetWampSecret(secret)

    newConfig = lastKnownConfig.copy()
    for argname in webExposedConfigItems:
        arg = kwargs.get(argname, None)
        if arg is not None:
            newConfig[argname] = arg

    SetConfiguration(newConfig)


class FileUploadDownload(annotate.FileUpload):
    pass


class FileUploadDownloadRenderer(webform.FileUploadRenderer):

    def input(self, context, slot, data, name, value):
        # pylint: disable=expression-not-assigned
        slot[_("Upload:")]
        slot = webform.FileUploadRenderer.input(
            self, context, slot, data, name, value)
        download_url = data.typedValue.getAttribute('download_url')
        return slot[tags.a(href=download_url)[_("Download")]]


registerAdapter(FileUploadDownloadRenderer, FileUploadDownload,
                formless.iformless.ITypedRenderer)


def getDownloadUrl(ctx, argument):
    if lastKnownConfig is not None:
        return url.URL.fromContext(ctx).\
            child(WAMP_SECRET_URL).\
            child(lastKnownConfig["ID"] + ".secret")


webFormInterface = [
    ("status",
     annotate.String(label=_("Current status"),
                     immutable=True,
                     default=lambda *k:getWampStatus())),
    ("ID",
     annotate.String(label=_("ID"),
                     default=wampConfigDefault)),
    ("secretfile",
     FileUploadDownload(label=_("File containing secret for that ID"),
                        download_url=getDownloadUrl)),
    ("active",
     annotate.Boolean(label=_("Enable WAMP connection"),
                      default=wampConfigDefault)),
    ("url",
     annotate.String(label=_("WAMP Server URL"),
                     default=wampConfigDefault))]


def deliverWampSecret(ctx, segments):
    # filename = segments[1].decode('utf-8')

    # FIXME: compare filename to ID+".secret"
    # for now all url under /secret returns the secret

    # TODO: make beautifull message in case of exception
    # while loading secret (if empty or dont exist)
    secret = LoadWampSecret(_WampSecret)
    return static.Data(secret, 'application/octet-stream'), ()


def RegisterWebSettings(NS):

    NS.ConfigurableSettings.addSettings(
        "wamp",
        _("Wamp Settings"),
        webFormInterface,
        _("Set"),
        wampConfig)

    NS.customSettingsURLs[WAMP_SECRET_URL] = deliverWampSecret
