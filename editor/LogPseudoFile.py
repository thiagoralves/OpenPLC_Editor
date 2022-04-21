import time
from threading import Lock, Timer, currentThread
from time import time as gettime

import wx

MainThread = currentThread().ident
REFRESH_PERIOD = 0.1


class LogPseudoFile(object):
    """ Base class for file like objects to facilitate StdOut for the Shell."""

    def __init__(self, output, risecall):
        self.red_white = 1
        self.red_yellow = 2
        self.black_white = wx.stc.STC_STYLE_DEFAULT
        self.output = output
        self.risecall = risecall
        # to prevent rapid fire on rising log panel
        self.rising_timer = 0
        self.lock = Lock()
        self.YieldLock = Lock()
        self.RefreshLock = Lock()
        self.TimerAccessLock = Lock()
        self.stack = []
        self.LastRefreshTime = gettime()
        self.LastRefreshTimer = None

    def write(self, s, style=None):
        if self.lock.acquire():
            self.stack.append((s, style))
            self.lock.release()
            current_time = gettime()
            self.TimerAccessLock.acquire()
            if self.LastRefreshTimer:
                self.LastRefreshTimer.cancel()
                self.LastRefreshTimer = None
            self.TimerAccessLock.release()
            if current_time - self.LastRefreshTime > REFRESH_PERIOD and self.RefreshLock.acquire(False):
                self._should_write()
            else:
                self.TimerAccessLock.acquire()
                self.LastRefreshTimer = Timer(REFRESH_PERIOD, self._timer_expired)
                self.LastRefreshTimer.start()
                self.TimerAccessLock.release()

    def _timer_expired(self):
        if self.RefreshLock.acquire(False):
            self._should_write()
        else:
            self.TimerAccessLock.acquire()
            self.LastRefreshTimer = Timer(REFRESH_PERIOD, self._timer_expired)
            self.LastRefreshTimer.start()
            self.TimerAccessLock.release()

    def _should_write(self):
        app = wx.GetApp()
        if app is not None:
            wx.CallAfter(self._write)

        if MainThread == currentThread().ident:
            if app is not None:
                if self.YieldLock.acquire(0):
                    app.Yield()
                    self.YieldLock.release()

    def _write(self):
        if self.output:
            self.output.Freeze()
            self.lock.acquire()
            for s, style in self.stack:
                if style is None:
                    style = self.black_white
                if style != self.black_white:
                    self.output.StartStyling(self.output.GetLength(), 0xff)

                # Temporary deactivate read only mode on StyledTextCtrl for
                # adding text. It seems that text modifications, even
                # programmatically, are disabled in StyledTextCtrl when read
                # only is active
                start_pos = self.output.GetLength()
                self.output.SetReadOnly(False)
                self.output.AppendText(s)
                self.output.SetReadOnly(True)
                text_len = self.output.GetLength() - start_pos

                if style != self.black_white:
                    self.output.SetStyling(text_len, style)
            self.stack = []
            self.lock.release()
            self.output.Thaw()
            self.LastRefreshTime = gettime()
            try:
                self.RefreshLock.release()
            except Exception:
                pass
            newtime = time.time()
            if newtime - self.rising_timer > 1:
                self.risecall(self.output)
            self.rising_timer = newtime

    def write_warning(self, s):
        self.write(s, self.red_white)

    def write_error(self, s):
        self.write(s, self.red_yellow)

    def flush(self):
        # Temporary deactivate read only mode on StyledTextCtrl for clearing
        # text. It seems that text modifications, even programmatically, are
        # disabled in StyledTextCtrl when read only is active
        self.output.SetReadOnly(False)
        self.output.SetText("")
        self.output.SetReadOnly(True)

    def isatty(self):
        return False
