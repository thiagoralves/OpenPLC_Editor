from __future__ import absolute_import
from __future__ import print_function
import os
from binascii import b2a_hqx
try:
    from runtime.spawn_subprocess import call
except ImportError:
    from subprocess import call

restart_stunnel_cmdline = ["/etc/init.d/S50stunnel", "restart"]

_PSKpath = None


def restartStunnel():
    """
    Restart stunnel service using SysV init stript
    to apply new generated credentials
    """
    try:
        call(restart_stunnel_cmdline)
    except OSError:
        print(_("Couldn't restart stunnel service"))


def PSKgen(ID, PSKpath):

    # b2a_hqx output len is 4/3 input len
    secret = os.urandom(192)  # int(256/1.3333)
    secretstring = b2a_hqx(secret)

    PSKstring = ID+":"+secretstring
    with open(PSKpath, 'w') as f:
        f.write(PSKstring)
    restartStunnel()


def ensurePSK(ID, PSKpath):
    global _PSKpath
    _PSKpath = PSKpath
    # check if already there
    if not os.path.exists(PSKpath):
        # create if needed
        PSKgen(ID, PSKpath)


def getPSKID(errorlog):
    if _PSKpath is not None:
        if not os.path.exists(_PSKpath):
            errorlog(
                'Error: Pre-Shared-Key Secret in %s is missing!\n' % _PSKpath)
            return None
        ID, _sep, PSK = open(_PSKpath).read().partition(':')
        PSK = PSK.rstrip('\n\r')
        return (ID, PSK)
    return None
