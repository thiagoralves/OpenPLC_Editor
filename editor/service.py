# Copyright (C) 2022: GP Orcullo
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


import argparse
import threading
import sys
import Pyro5
from Pyro5.server import expose, Daemon
from pubsub import pub
import wx
import wx.adv

from runtime import default_evaluator, MainWorker, PlcStatus
from runtime.PLCObject import PLCObject
import util.paths as paths

ROOT = paths.AbsDir(__file__)
TRAY_TOOLTIP = 'PLCOpen Service'
TRAY_ICON = f'{ROOT}/images/brz.png'
TRAY_START_ICON = f'{ROOT}/images/icoplay24.png'
TRAY_STOP_ICON = f'{ROOT}/images/icostop24.png'


Pyro5.config.SERPENT_BYTES_REPR = True

[ITEM_PLC_START, ITEM_PLC_STOP, ITEM_EXIT] = range(3)

ITEM_PLC_STATE = {
    PlcStatus.Started: ('Stop PLC', ITEM_PLC_START, TRAY_START_ICON),
    PlcStatus.Stopped: ('Start PLC', ITEM_PLC_STOP, TRAY_STOP_ICON),
}


class PLCOpenTaskBar(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.myapp_frame = frame
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, frame.on_left_down)
        self.plcstate = PlcStatus.Empty
        pub.subscribe(self.set_plcstate, 'plc state')

    def _create_menu_item(self, menu, label, id=None):
        item = wx.MenuItem(menu, -1, label)
        menu.Bind(wx.EVT_MENU, lambda e: self.on_menu(e, id), id=item.GetId())
        menu.Append(item)
        return item

    def CreatePopupMenu(self):
        menu = wx.Menu()
        if self.plcstate in (PlcStatus.Started, PlcStatus.Stopped):
            a, b, _ = ITEM_PLC_STATE[self.plcstate]
            self._create_menu_item(menu, a, id=b)
            menu.AppendSeparator()
        self._create_menu_item(menu, 'Exit', id=ITEM_EXIT)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_menu(self, e, i):
        if i in (ITEM_PLC_START, ITEM_PLC_STOP):
            pub.sendMessage('set plc', state=(i == ITEM_PLC_STOP))

        if i == ITEM_EXIT:
            self.myapp_frame.Close()

    def set_plcstate(self, state):
        self.plcstate = state
        if state in (PlcStatus.Started, PlcStatus.Stopped):
            _, _, i = ITEM_PLC_STATE[state]
            self.set_icon(i)
        else:
            self.set_icon(TRAY_ICON)


class PLCOpenService(wx.Frame):
    def __init__(self):
        super().__init__(None, size=(1, 1))
        panel = wx.Panel(self)
        self.tb = PLCOpenTaskBar(self)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def onClose(self, evt):
        self.tb.RemoveIcon()
        self.tb.Destroy()
        wx.CallAfter(self.Destroy)

    def on_left_down(self, evt):
        self.tb.PopupMenu(self.tb.CreatePopupMenu())


class PLCObjectAdapter(PLCObject):
    @expose
    def AppendChunkToBlob(self, *args, **kwargs):
        return super().AppendChunkToBlob(*args, **kwargs)

    @expose
    def GetLogMessage(self, *args, **kwargs):
        return super().GetLogMessage(*args, **kwargs)

    @expose
    def GetPLCID(self, *args, **kwargs):
        return super().GetPLCID(*args, **kwargs)

    @expose
    def GetPLCstatus(self, *args, **kwargs):
        return super().GetPLCstatus(*args, **kwargs)

    @expose
    def GetTraceVariables(self, *args, **kwargs):
        return super().GetTraceVariables(*args, **kwargs)

    @expose
    def MatchMD5(self, *args, **kwargs):
        return super().MatchMD5(*args, **kwargs)

    @expose
    def NewPLC(self, *args, **kwargs):
        return super().NewPLC(*args, **kwargs)

    @expose
    def PurgeBlobs(self, *args, **kwargs):
        return super().PurgeBlobs(*args, **kwargs)

    @expose
    def RemoteExec(self, *args, **kwargs):
        return super().RemoteExec(*args, **kwargs)

    @expose
    def RepairPLC(self, *args, **kwargs):
        return super().RepairPLC(*args, **kwargs)

    @expose
    def ResetLogCount(self, *args, **kwargs):
        return super().ResetLogCount(*args, **kwargs)

    @expose
    def SeedBlob(self, *args, **kwargs):
        return super().SeedBlob(*args, **kwargs)

    @expose
    def SetTraceVariablesList(self, *args, **kwargs):
        return super().SetTraceVariablesList(*args, **kwargs)

    @expose
    def StartPLC(self, *args, **kwargs):
        return super().StartPLC(*args, **kwargs)

    @expose
    def StopPLC(self, *args, **kwargs):
        return super().StopPLC(*args, **kwargs)


def stdout_write(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


class PyroDaemon(threading.Thread):
    def __init__(self, host, port, wdir, evaluator, event):
        super().__init__()
        self.event = event
        self.uri = None
        self.plcobj = None
        self.argv = []
        self.evaluator = evaluator
        self.host = host
        self.port = port
        self.rtvars = {}
        self.wdir = wdir
        self.pyro_daemon = None
        pub.subscribe(self.set_plc, 'set plc')

    def run(self):
        self.pyro_daemon = Daemon(host=self.host, port=self.port)
        self.plcobj = PLCObjectAdapter(self.wdir, self.argv,
                                       [lambda m: pub.sendMessage("plc state",
                                                                  state=m)],
                                       self.evaluator,
                                       self.rtvars)
        self.uri = self.pyro_daemon.register(self.plcobj, 'PLCObject')
        self.event.set()

        stdout_write(f'Pyro port : {str(self.uri).split(":")[-1]}\n'
                     f'Current working directory : {self.wdir}\n')

        self.pyro_daemon.requestLoop()
        stdout_write('Pyro: thread terminated.\n')

    def shutdown(self):
        stdout_write('Pyro: shutting down ...\n')
        self.pyro_daemon.shutdown()

    def set_plc(self, state):
        if state:
            self.plcobj.StartPLC()
        else:
            self.plcobj.StopPLC()


class MainWorkerDaemon(threading.Thread):
    def __init__(self, host, port, wdir, evaluator):
        super().__init__()
        self.event = threading.Event()
        self.pyro_daemon = PyroDaemon(host, port, wdir, evaluator, self.event)
        self.pyro_daemon.daemon = True

    def run(self):
        MainWorker.runloop(self.start_pyro)
        stdout_write('MainWorker: thread terminated.\n')

    def start_pyro(self):
        self.pyro_daemon.start()
        self.event.wait()
        self.pyro_daemon.plcobj.AutoLoad(0)

    def shutdown(self):
        self.pyro_daemon.shutdown()
        self.pyro_daemon.join()
        stdout_write('MainWorker: shutting down ...\n')
        MainWorker.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=0, help='listen on port')
    parser.add_argument('-i', help='listen on address')
    parser.add_argument('-x', type=int, default=1,
                        choices=[0, 1],
                        help='enable GUI (0=disabled)')
    parser.add_argument('tmpdir',
                        help='temporary location for PLC files')
    args = parser.parse_args()

    if args.x:
        app = wx.App()
        PLCOpenService()

    pyro_thread = MainWorkerDaemon(
        args.i, args.p, args.tmpdir, default_evaluator)
    pyro_thread.daemon = True
    pyro_thread.start()
    pyro_thread.event.wait()

    if args.x:
        app.MainLoop()
    else:
        try:
            pyro_thread.join()
        except (KeyboardInterrupt, SystemExit):
            stdout_write('\nExiting...\n')

    pyro_thread.shutdown()
