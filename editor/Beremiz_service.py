#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
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
from __future__ import print_function
import os
import sys
import getopt
import threading
from threading import Thread, Semaphore, Lock, currentThread
from builtins import str as text
from past.builtins import execfile
from six.moves import builtins

import runtime
from runtime.PyroServer import PyroServer
from runtime.xenomai import TryPreloadXenomai
from runtime import LogMessageAndException
from runtime import PlcStatus
from runtime.Stunnel import ensurePSK
import util.paths as paths


def version():
    from version import app_version
    print("Beremiz_service: ", app_version)


def usage():
    version()
    print("""
Usage of Beremiz PLC execution service :\n
%s {[-n servicename] [-i IP] [-p port] [-x enabletaskbar] [-a autostart]|-h|--help} working_dir
  -n  service name (default:None, zeroconf discovery disabled)
  -i  IP address of interface to bind to (default:localhost)
  -p  port number default:3000
  -h  print this help text and quit
  -a  autostart PLC (0:disable 1:enable) (default:0)
  -x  enable/disable wxTaskbarIcon (0:disable 1:enable) (default:1)
  -t  enable/disable Twisted web interface (0:disable 1:enable) (default:1)
  -w  web server port or "off" to disable web server (default:8009)
  -c  WAMP client config file (can be overriden by wampconf.json in project)
  -s  PSK secret path (default:PSK disabled)
  -e  python extension (absolute path .py)

           working_dir - directory where are stored PLC files
""" % sys.argv[0])


try:
    opts, argv = getopt.getopt(sys.argv[1:], "i:p:n:x:t:a:w:c:e:s:h", ["help", "version"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(str(err))  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

# default values
interface = ''
port = 3000
webport = 8009
PSKpath = None
wampconf = None
servicename = None
autostart = False
enablewx = True
havewx = False
enabletwisted = True
havetwisted = False

extensions = []

for o, a in opts:
    if o == "-h" or o == "--help":
        usage()
        sys.exit()
    if o == "--version":
        version()
        sys.exit()
    elif o == "-i":
        if len(a.split(".")) == 4:
            interface = a
        elif a == "localhost":
            interface = '127.0.0.1'
        else:
            usage()
            sys.exit()
    elif o == "-p":
        # port: port that the service runs on
        port = int(a)
    elif o == "-n":
        servicename = a
    elif o == "-x":
        enablewx = int(a)
    elif o == "-t":
        enabletwisted = int(a)
    elif o == "-a":
        autostart = int(a)
    elif o == "-w":
        webport = None if a == "off" else int(a)
    elif o == "-c":
        wampconf = None if a == "off" else a
    elif o == "-s":
        PSKpath = None if a == "off" else a
    elif o == "-e":
        fnameanddirname = list(os.path.split(os.path.realpath(a)))
        fnameanddirname.reverse()
        extensions.append(fnameanddirname)
    else:
        usage()
        sys.exit()


beremiz_dir = paths.AbsDir(__file__)

if len(argv) > 1:
    usage()
    sys.exit()
elif len(argv) == 1:
    WorkingDir = argv[0]
    os.chdir(WorkingDir)
elif len(argv) == 0:
    WorkingDir = os.getcwd()
    argv = [WorkingDir]

builtins.__dict__['_'] = lambda x: x
# TODO: add a cmdline parameter if Trying Preloading Xenomai makes problem
TryPreloadXenomai()
version()


def Bpath(*args):
    return os.path.join(beremiz_dir, *args)


def SetupI18n():
    # Get folder containing translation files
    localedir = os.path.join(beremiz_dir, "locale")
    # Get the default language
    langid = wx.LANGUAGE_DEFAULT
    # Define translation domain (name of translation files)
    domain = "Beremiz"

    # Define locale for wx
    loc = builtins.__dict__.get('loc', None)
    if loc is None:
        wx.LogGui.EnableLogging(False)
        loc = wx.Locale(langid)
        wx.LogGui.EnableLogging(True)
        builtins.__dict__['loc'] = loc
        # Define location for searching translation files
    loc.AddCatalogLookupPathPrefix(localedir)
    # Define locale domain
    loc.AddCatalog(domain)

    import locale
    global default_locale
    default_locale = locale.getdefaultlocale()[1]

    # sys.stdout.encoding = default_locale
    # if Beremiz_service is started from Beremiz IDE
    # sys.stdout.encoding is None (that means 'ascii' encoding').
    # And unicode string returned by wx.GetTranslation() are
    # automatically converted to 'ascii' string.
    def unicode_translation(message):
        return wx.GetTranslation(message).encode(default_locale)

    builtins.__dict__['_'] = unicode_translation
    # builtins.__dict__['_'] = wx.GetTranslation


# Life is hard... have a candy.
# pylint: disable=wrong-import-position,wrong-import-order
if enablewx:
    try:
        import wx
        havewx = True
    except ImportError:
        print("Wx unavailable !")
        havewx = False

    if havewx:
        import re

        if wx.VERSION >= (3, 0, 0):
            app = wx.App(redirect=False)
        else:
            app = wx.PySimpleApp(redirect=False)
        app.SetTopWindow(wx.Frame(None, -1))

        default_locale = None
        SetupI18n()

        defaulticon = wx.Image(Bpath("images", "brz.png"))
        starticon = wx.Image(Bpath("images", "icoplay24.png"))
        stopicon = wx.Image(Bpath("images", "icostop24.png"))

        class ParamsEntryDialog(wx.TextEntryDialog):

            def __init__(self, parent, message, caption=_("Please enter text"), defaultValue="",
                         style=wx.OK | wx.CANCEL | wx.CENTRE, pos=wx.DefaultPosition):
                wx.TextEntryDialog.__init__(self, parent, message, caption, defaultValue, style, pos)

                self.Tests = []
                self.Bind(wx.EVT_BUTTON, self.OnOK, id=self.GetAffirmativeId())

            def OnOK(self, event):
                value = self.GetValue()
                texts = {"value": value}
                for function, message in self.Tests:
                    if not function(value):
                        message = wx.MessageDialog(self, message % texts, _("Error"), wx.OK | wx.ICON_ERROR)
                        message.ShowModal()
                        message.Destroy()
                        return
                self.EndModal(wx.ID_OK)
                event.Skip()

            def GetValue(self):
                return self.GetSizer().GetItem(1).GetWindow().GetValue()

            def SetTests(self, tests):
                self.Tests = tests

        class BeremizTaskBarIcon(wx.TaskBarIcon):
            TBMENU_START = wx.NewId()
            TBMENU_STOP = wx.NewId()
            TBMENU_CHANGE_NAME = wx.NewId()
            TBMENU_CHANGE_PORT = wx.NewId()
            TBMENU_CHANGE_INTERFACE = wx.NewId()
            TBMENU_LIVE_SHELL = wx.NewId()
            TBMENU_WXINSPECTOR = wx.NewId()
            TBMENU_CHANGE_WD = wx.NewId()
            TBMENU_QUIT = wx.NewId()

            def __init__(self, pyroserver):
                wx.TaskBarIcon.__init__(self)
                self.pyroserver = pyroserver
                # Set the image
                self.UpdateIcon(None)

                # bind some events
                self.Bind(wx.EVT_MENU, self.OnTaskBarStartPLC, id=self.TBMENU_START)
                self.Bind(wx.EVT_MENU, self.OnTaskBarStopPLC, id=self.TBMENU_STOP)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangeName, id=self.TBMENU_CHANGE_NAME)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangeInterface, id=self.TBMENU_CHANGE_INTERFACE)
                self.Bind(wx.EVT_MENU, self.OnTaskBarLiveShell, id=self.TBMENU_LIVE_SHELL)
                self.Bind(wx.EVT_MENU, self.OnTaskBarWXInspector, id=self.TBMENU_WXINSPECTOR)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangePort, id=self.TBMENU_CHANGE_PORT)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangeWorkingDir, id=self.TBMENU_CHANGE_WD)
                self.Bind(wx.EVT_MENU, self.OnTaskBarQuit, id=self.TBMENU_QUIT)

            def CreatePopupMenu(self):
                """
                This method is called by the base class when it needs to popup
                the menu for the default EVT_RIGHT_DOWN event.  Just create
                the menu how you want it and return it from this function,
                the base class takes care of the rest.
                """
                menu = wx.Menu()
                menu.Append(self.TBMENU_START, _("Start PLC"))
                menu.Append(self.TBMENU_STOP, _("Stop PLC"))
                menu.AppendSeparator()
                menu.Append(self.TBMENU_CHANGE_NAME, _("Change Name"))
                menu.Append(self.TBMENU_CHANGE_INTERFACE, _("Change IP of interface to bind"))
                menu.Append(self.TBMENU_CHANGE_PORT, _("Change Port Number"))
                menu.Append(self.TBMENU_CHANGE_WD, _("Change working directory"))
                menu.AppendSeparator()
                menu.Append(self.TBMENU_LIVE_SHELL, _("Launch a live Python shell"))
                menu.Append(self.TBMENU_WXINSPECTOR, _("Launch WX GUI inspector"))
                menu.AppendSeparator()
                menu.Append(self.TBMENU_QUIT, _("Quit"))
                return menu

            def MakeIcon(self, img):
                """
                The various platforms have different requirements for the
                icon size...
                """
                if "wxMSW" in wx.PlatformInfo:
                    img = img.Scale(16, 16)
                elif "wxGTK" in wx.PlatformInfo:
                    img = img.Scale(22, 22)
                # wxMac can be any size upto 128x128, so leave the source img alone....
                icon = wx.IconFromBitmap(img.ConvertToBitmap())
                return icon

            def OnTaskBarStartPLC(self, evt):
                runtime.GetPLCObjectSingleton().StartPLC()

            def OnTaskBarStopPLC(self, evt):
                runtime.GetPLCObjectSingleton().StopPLC()

            def OnTaskBarChangeInterface(self, evt):
                ip_addr = self.pyroserver.ip_addr
                ip_addr = '' if ip_addr is None else ip_addr
                dlg = ParamsEntryDialog(None, _("Enter the IP of the interface to bind"), defaultValue=ip_addr)
                dlg.SetTests([(re.compile(r'\d{1,3}(?:\.\d{1,3}){3}$').match, _("IP is not valid!")),
                              (lambda x:len([x for x in x.split(".") if 0 <= int(x) <= 255]) == 4,
                               _("IP is not valid!"))])
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.ip_addr = dlg.GetValue()
                    self.pyroserver.Restart()

            def OnTaskBarChangePort(self, evt):
                dlg = ParamsEntryDialog(None, _("Enter a port number "), defaultValue=str(self.pyroserver.port))
                dlg.SetTests([(text.isdigit, _("Port number must be an integer!")), (lambda port: 0 <= int(port) <= 65535, _("Port number must be 0 <= port <= 65535!"))])
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.port = int(dlg.GetValue())
                    self.pyroserver.Restart()

            def OnTaskBarChangeWorkingDir(self, evt):
                dlg = wx.DirDialog(None, _("Choose a working directory "), self.pyroserver.workdir, wx.DD_NEW_DIR_BUTTON)
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.workdir = dlg.GetPath()
                    self.pyroserver.Restart()

            def OnTaskBarChangeName(self, evt):
                _servicename = self.pyroserver.servicename
                _servicename = '' if _servicename is None else _servicename
                dlg = ParamsEntryDialog(None, _("Enter a name "), defaultValue=_servicename)
                dlg.SetTests([(lambda name: len(name) is not 0, _("Name must not be null!"))])
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.servicename = dlg.GetValue()
                    self.pyroserver.Restart()

            def _LiveShellLocals(self):
                return {"locals": runtime.GetPLCObjectSingleton().python_runtime_vars}

            def OnTaskBarLiveShell(self, evt):
                from wx import py
                frame = py.crust.CrustFrame(**self._LiveShellLocals())
                frame.Show()

            def OnTaskBarWXInspector(self, evt):
                # Activate the widget inspection tool
                from wx.lib.inspection import InspectionTool
                if not InspectionTool().initialized:
                    InspectionTool().Init(**self._LiveShellLocals())

                wnd = wx.GetApp()
                InspectionTool().Show(wnd, True)

            def OnTaskBarQuit(self, evt):
                if wx.Platform == '__WXMSW__':
                    Thread(target=self.pyroserver.Quit).start()
                self.RemoveIcon()
                wx.CallAfter(wx.GetApp().ExitMainLoop)

            def UpdateIcon(self, plcstatus):
                if plcstatus is PlcStatus.Started:
                    currenticon = self.MakeIcon(starticon)
                elif plcstatus is PlcStatus.Stopped:
                    currenticon = self.MakeIcon(stopicon)
                else:
                    currenticon = self.MakeIcon(defaulticon)
                self.SetIcon(currenticon, "Beremiz Service")


if not os.path.isdir(WorkingDir):
    os.mkdir(WorkingDir)


def default_evaluator(tocall, *args, **kwargs):
    try:
        res = (tocall(*args, **kwargs), None)
    except Exception:
        res = (None, sys.exc_info())
    return res


if enabletwisted:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            if havewx:
                from twisted.internet import wxreactor
                wxreactor.install()
            from twisted.internet import reactor

            havetwisted = True
        except ImportError:
            print(_("Twisted unavailable."))
            havetwisted = False

pyruntimevars = {}
statuschange = []

if havetwisted:
    if havewx:
        reactor.registerWxApp(app)

twisted_reactor_thread_id = None
ui_thread = None

if havewx:
    wx_eval_lock = Semaphore(0)

    def statuschangeTskBar(status):
        wx.CallAfter(taskbar_instance.UpdateIcon, status)

    statuschange.append(statuschangeTskBar)

    def wx_evaluator(obj, *args, **kwargs):
        tocall, args, kwargs = obj.call
        obj.res = default_evaluator(tocall, *args, **kwargs)
        wx_eval_lock.release()

    def evaluator(tocall, *args, **kwargs):
        # To prevent deadlocks, check if current thread is not one of the UI
        # UI threads can be either the one from WX main loop or
        # worker thread from twisted "threadselect" reactor
        current_id = currentThread().ident

        if ui_thread is not None \
            and ui_thread.ident != current_id \
            and (not havetwisted or (
                    twisted_reactor_thread_id is not None
                    and twisted_reactor_thread_id != current_id)):

            o = type('', (object,), dict(call=(tocall, args, kwargs), res=None))
            wx.CallAfter(wx_evaluator, o)
            wx_eval_lock.acquire()
            return o.res
        else:
            # avoid dead lock if called from the wx mainloop
            return default_evaluator(tocall, *args, **kwargs)
else:
    evaluator = default_evaluator

# Exception hooks


def LogException(*exp):
    LogMessageAndException("", exp)


sys.excepthook = LogException


def installThreadExcepthook():
    init_old = threading.Thread.__init__

    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run

        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init


installThreadExcepthook()
havewamp = False

if havetwisted:
    if webport is not None:
        try:
            import runtime.NevowServer as NS  # pylint: disable=ungrouped-imports
        except Exception:
            LogMessageAndException(_("Nevow/Athena import failed :"))
            webport = None
        NS.WorkingDir = WorkingDir

    try:
        import runtime.WampClient as WC  # pylint: disable=ungrouped-imports
        WC.WorkingDir = WorkingDir
        havewamp = True
    except Exception:
        LogMessageAndException(_("WAMP import failed :"))

# Load extensions
for extention_file, extension_folder in extensions:
    sys.path.append(extension_folder)
    execfile(os.path.join(extension_folder, extention_file), locals())

# Service name is used as an ID for stunnel's PSK
# Some extension may set 'servicename' to a computed ID or Serial Number
# instead of using commandline '-n'
if servicename is not None and PSKpath is not None:
    ensurePSK(servicename, PSKpath)

runtime.CreatePLCObjectSingleton(
    WorkingDir, argv, statuschange, evaluator, pyruntimevars)

pyroserver = PyroServer(servicename, interface, port)

if havewx:
    taskbar_instance = BeremizTaskBarIcon(pyroserver)

if havetwisted:
    if webport is not None:
        try:
            website = NS.RegisterWebsite(interface, webport)
            pyruntimevars["website"] = website
            NS.SetServer(pyroserver)
            statuschange.append(NS.website_statuslistener_factory(website))
        except Exception:
            LogMessageAndException(_("Nevow Web service failed. "))

    if havewamp:
        try:
            WC.SetServer(pyroserver)
            WC.RegisterWampClient(wampconf, PSKpath)
            WC.RegisterWebSettings(NS)
        except Exception:
            LogMessageAndException(_("WAMP client startup failed. "))

pyro_thread_started = Lock()
pyro_thread_started.acquire()
pyro_thread = Thread(target=pyroserver.PyroLoop,
                     kwargs=dict(when_ready=pyro_thread_started.release))
pyro_thread.start()

# Wait for pyro thread to be effective
pyro_thread_started.acquire()

pyroserver.PrintServerInfo()

# Beremiz IDE detects LOCAL:// runtime is ready by looking
# for self.workdir in the daemon's stdout.
sys.stdout.write(_("Current working directory :") + WorkingDir + "\n")
sys.stdout.flush()

if havetwisted or havewx:
    ui_thread_started = Lock()
    ui_thread_started.acquire()
    if havetwisted:
        # reactor._installSignalHandlersAgain()
        def ui_thread_target():
            # FIXME: had to disable SignaHandlers install because
            # signal not working in non-main thread
            reactor.run(installSignalHandlers=False)
    else:
        ui_thread_target = app.MainLoop

    ui_thread = Thread(target=ui_thread_target)
    ui_thread.start()

    # This order ui loop to unblock main thread when ready.
    if havetwisted:
        def signal_uithread_started():
            global twisted_reactor_thread_id
            twisted_reactor_thread_id = currentThread().ident
            ui_thread_started.release()
        reactor.callLater(0, signal_uithread_started)
    else:
        wx.CallAfter(ui_thread_started.release)

    # Wait for ui thread to be effective
    ui_thread_started.acquire()
    print("UI thread started successfully.")

try:
    runtime.MainWorker.runloop(
        runtime.GetPLCObjectSingleton().AutoLoad, autostart)
except KeyboardInterrupt:
    pass

pyroserver.Quit()

plcobj = runtime.GetPLCObjectSingleton()
plcobj.StopPLC()
plcobj.UnLoadPLC()

sys.exit(0)
