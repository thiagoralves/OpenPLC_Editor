#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz runtime.

# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov
# Copyright (C) 2018: Edouard TISSERANT

# See COPYING file for copyrights details.

from __future__ import absolute_import
from __future__ import print_function
import sys
import os

import Pyro
import Pyro.core as pyro
import runtime
from runtime.ServicePublisher import ServicePublisher


class PyroServer(object):
    def __init__(self, servicename, ip_addr, port):
        self.continueloop = True
        self.daemon = None
        self.servicename = servicename
        self.ip_addr = ip_addr
        self.port = port
        self.servicepublisher = None
        self.piper, self.pipew = None, None

    def _to_be_published(self):
        return self.servicename is not None and \
               self.ip_addr not in ["", "localhost", "127.0.0.1"]

    def PrintServerInfo(self):
        print(_("Pyro port :"), self.port)

        if self._to_be_published():
            print(_("Publishing service on local network"))

        sys.stdout.flush()

    def PyroLoop(self, when_ready):
        if self._to_be_published():
            self.Publish()

        while self.continueloop:
            Pyro.config.PYRO_MULTITHREADED = 0
            pyro.initServer()
            self.daemon = pyro.Daemon(host=self.ip_addr, port=self.port)

            # pyro never frees memory after connection close if no timeout set
            # taking too small timeout value may cause
            # unwanted diconnection when IDE is kept busy for long periods
            self.daemon.setTimeout(60)

            pyro_obj = Pyro.core.ObjBase()
            pyro_obj.delegateTo(runtime.GetPLCObjectSingleton())

            self.daemon.connect(pyro_obj, "PLCObject")

            when_ready()

            # "pipe to self" trick to to accelerate runtime shutdown 
            # instead of waiting for arbitrary pyro timeout.
            others = []
            if not sys.platform.startswith('win'):
                self.piper, self.pipew = os.pipe()
                others.append(self.piper)

            self.daemon.requestLoop(others=others, callback=lambda x: None)
            self.piper, self.pipew = None, None
            if hasattr(self, 'sock'):
                self.daemon.sock.close()
        self.Unpublish()

    def Restart(self):
        self.daemon.shutdown(True)

    def Quit(self):
        self.continueloop = False
        self.daemon.shutdown(True)
        self.daemon.closedown()
        if not sys.platform.startswith('win'):
            if self.pipew is not None:
                os.write(self.pipew, "goodbye")

    def Publish(self):
        self.servicepublisher = ServicePublisher("PYRO")
        self.servicepublisher.RegisterService(self.servicename,
                                              self.ip_addr, self.port)

    def Unpublish(self):
        if self.servicepublisher is not None:
            self.servicepublisher.UnRegisterService()
            self.servicepublisher = None
