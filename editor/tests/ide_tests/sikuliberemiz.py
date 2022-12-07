"Commons definitions for sikuli based beremiz IDE GUI tests"

import os
import sys
import subprocess
import traceback
from threading import Thread, Event, Lock
from time import time as timesec

import sikuli

beremiz_path = os.environ["BEREMIZPATH"]
python_bin = os.environ.get("BEREMIZPYTHONPATH", "/usr/bin/python")

opj = os.path.join


class KBDShortcut:
    """Send shortut to app by calling corresponding methods.

    example:
        k = KBDShortcut()
        k.Clean()
    """

    fkeys = {"Stop":     sikuli.Key.F4,
             "Run":      sikuli.Key.F5,
             "Transfer": sikuli.Key.F6,
             "Connect":  sikuli.Key.F7,
             "Clean":    sikuli.Key.F9,
             "Build":    sikuli.Key.F11,
             "Save":     ("s",sikuli.Key.CTRL),
             "New":      ("n",sikuli.Key.CTRL),
             "Address":  ("l",sikuli.Key.CTRL)}  # to reach address bar in GTK's file selector

    def __init__(self, app):
        self.app = app
    
    def __getattr__(self, name):
        fkey = self.fkeys[name]
        if type(fkey) != tuple:
            fkey = (fkey,)

        def PressShortCut():
            self.app.sikuliapp.focus()
            sikuli.type(*fkey)
            self.app.ReportText("Sending " + name + " shortcut")

        return PressShortCut


class IDEIdleObserver:
    "Detects when IDE is idle. This is particularly handy when staring an operation and witing for the en of it."

    def __init__(self):
        """
        Parameters: 
            app (class BeremizApp)
        """
        self.r = sikuli.Region(self.sikuliapp.window())

        self.idechanged = False
        
        # 200 was selected because default 50 was still catching cursor blinking in console
        # FIXME : remove blinking cursor in console
        self.r.onChange(200,self._OnIDEWindowChange)
        self.r.observeInBackground()

    def __del__(self):
        self.r.stopObserver()

    def _OnIDEWindowChange(self, event):
        self.idechanged = True

    def WaitIdleUI(self, period=1, timeout=15):
        """
        Wait for IDE to stop changing
        Parameters: 
            period (int): how many seconds with no change to consider idle
            timeout (int): how long to wait for idle, in seconds
        """
        c = max(timeout/period,1)
        while c > 0:
            self.idechanged = False
            sikuli.wait(period)
            if not self.idechanged:
                break
            c = c - 1

        self.ReportScreenShot("UI is idle" if c != 0 else "UI is not idle")

        if c == 0:
            raise Exception("Window did not idle before timeout")

 
class stdoutIdleObserver:
    "Detects when IDE's stdout is idle. Can be more reliable than pixel based version (false changes ?)"

    def __init__(self):
        """
        Parameters: 
            app (class BeremizApp)
        """
        self.stdoutchanged = False

        self.event = Event()

        self.pattern = None
        self.success_event = Event()

        self.thread = Thread(target = self._waitStdoutProc).start()

    def __del__(self):
        pass  # self.thread.join() ?

    def _waitStdoutProc(self):
        while True:
            a = self.proc.stdout.readline()
            if len(a) == 0 or a is None: 
                break
            sys.stdout.write(a)
            self.ReportOutput(a)
            self.event.set()
            if self.pattern is not None and a.find(self.pattern) >= 0:
                sys.stdout.write("found pattern in '" + a +"'")
                self.success_event.set()

    def waitForChangeAndIdleStdout(self, period=2, timeout=15):
        """
        Wait for IDE'stdout to start changing
        Parameters: 
            timeout (int): how long to wait for change, in seconds
        """
        start_time = timesec()

        wait_result = self.event.wait(timeout)

        self.ReportScreenShot("stdout changed" if wait_result else "stdout didn't change")

        if wait_result:
            self.event.clear()
        else:
            raise Exception("Stdout didn't become active before timeout")

        self.waitIdleStdout(period, timeout - (timesec() - start_time))

    def waitIdleStdout(self, period=2, timeout=15):
        """
        Wait for IDE'stdout to stop changing
        Parameters: 
            period (int): how many seconds with no change to consider idle
            timeout (int): how long to wait for idle, in seconds
        """
        end_time = timesec() + timeout
        self.event.clear()
        while timesec() < end_time:
            if self.event.wait(period):
                # no timeout -> got event -> not idle -> loop again
                self.event.clear()
            else:
                # timeout -> no event -> idle -> exit
                self.ReportScreenShot("stdout is idle")
                return True

        self.ReportScreenShot("stdout did not idle")

        raise Exception("Stdout did not idle before timeout")

    def waitPatternInStdout(self, pattern, timeout, count=1):
        found = 0
        self.pattern = pattern
        end_time = timesec() + timeout
        self.event.clear()
        while True:
            remain = end_time - timesec()
            if remain <= 0 :
                res = False
                break

            res = self.success_event.wait(remain)
            if res:
                self.success_event.clear()
                found = found + 1
                if found >= count:
                    break
        self.pattern = None
        self.ReportScreenShot("found pattern" if res else "pattern not found")
        return res

class BeremizApp(IDEIdleObserver, stdoutIdleObserver):
    def __init__(self, projectpath=None, exemple=None):
        """
        Starts Beremiz IDE, waits for main window to appear, maximize it.

            Parameters: 
                projectpath (str): path to project to open
                exemple (str): path relative to exemples directory

            Returns:
                Sikuli App class instance
        """

        sikuli.OCR.Options().smallFont()

        self.screenshotnum = 0
        self.starttime = timesec()
        self.screen = sikuli.Screen()

        self.report = open("report.html", "w")
        self.report.write("""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="color-scheme" content="light dark">
    <title>Test report</title>
  </head>
  <body>
""")

        command = [python_bin, opj(beremiz_path,"Beremiz.py"), "--log=/dev/stdout"]

        if exemple is not None:
            command.append(opj(beremiz_path,"exemples",exemple))
        elif projectpath is not None:
            command.append(projectpath)

        # App class is broken in Sikuli 2.0.5: can't start process with arguments.
        # 
        # Workaround : - use subprocess module to spawn IDE process,
        #              - use wmctrl to find IDE window details and maximize it
        #              - pass exact window title to App class constructor

        self.ReportText("Launching " + repr(command))

        self.proc = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)

        # Window are macthed against process' PID
        ppid = self.proc.pid

        # Timeout 5s
        c = 50
        while c > 0:
            # equiv to "wmctrl -l -p | grep $pid"
            try:
                wlist = filter(lambda l:(len(l)>2 and l[2]==str(ppid)), map(lambda s:s.split(None,4), subprocess.check_output(["wmctrl", "-l", "-p"]).splitlines()))
            except subprocess.CalledProcessError:
                wlist = []

            # window with no title only has 4 fields do describe it
            # beremiz splashcreen has no title
            # wait until main window is visible
            if len(wlist) == 1 and len(wlist[0]) == 5:
                windowID,_zero,wpid,_XID,wtitle = wlist[0] 
                break

            sikuli.wait(0.1)
            c = c - 1

        if c == 0:
            raise Exception("Couldn't find Beremiz window")

        # Maximize window x and y
        subprocess.check_call(["wmctrl", "-i", "-r", windowID, "-b", "add,maximized_vert,maximized_horz"])

        # switchApp creates an App object by finding window by title, is not supposed to spawn a process
        self.sikuliapp = sikuli.switchApp(wtitle)
        self.k = KBDShortcut(self)

        IDEIdleObserver.__init__(self)
        stdoutIdleObserver.__init__(self)

        # stubs for common sikuli calls to allow adding hooks later
        for name in ["click","doubleClick","type","rightClick","wait"]:
            def makeMyMeth(n):
                def myMeth(*args, **kwargs):
                    self.ReportScreenShot("Begin: " + n + "(" + repr(args) + "," + repr(kwargs) + ")")
                    try:
                        getattr(sikuli, n)(*args, **kwargs)
                    finally:
                        self.ReportScreenShot("end: " + n + "(" + repr(args) + "," + repr(kwargs) + ")")
                return myMeth
            setattr(self, name, makeMyMeth(name))

    def close(self):
        self.sikuliapp.close()
        self.sikuliapp = None
        self.report.write("""
  </body>
</html>""")
        self.report.close()

    def __del__(self):
        if self.sikuliapp is not None:
            self.sikuliapp.close()
        IDEIdleObserver.__del__(self)
        stdoutIdleObserver.__del__(self)

    def ReportScreenShot(self, msg):
        elapsed = "%.3fs: "%(timesec() - self.starttime)
        fname = "capture"+str(self.screenshotnum)+".png"
        cap = self.screen.capture(self.r)
        cap.save(".", fname)
        self.screenshotnum = self.screenshotnum + 1
        self.report.write( "<p>" + elapsed + msg + "<br/><img src=\""+ fname + "\">" + "</p>")

    def ReportText(self, text):
        elapsed = "%.3fs: "%(timesec() - self.starttime)
        self.report.write("<p>" + elapsed + text + "</p>")

    def ReportOutput(self, text):
        elapsed = "%.3fs: "%(timesec() - self.starttime)
        self.report.write("<pre>" + elapsed + text + "</pre>")


def run_test(func, *args, **kwargs):
    app = BeremizApp(*args, **kwargs)
    try:
        success = func(app)
    except:
        # sadly, sys.excepthook is broken in sikuli/jython 
        # purpose of this run_test function is to work around it.
        # and catch exception cleanly anyhow
        e_type, e_value, e_traceback = sys.exc_info()
        err_msg = "\n".join(traceback.format_exception(e_type, e_value, e_traceback))
        sys.stdout.write(err_msg)
        app.ReportOutput(err_msg)
        success = False

    app.close()

    if success:
        sikuli.exit(0)
    else:
        sikuli.exit(1)



