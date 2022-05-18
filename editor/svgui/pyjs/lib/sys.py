# the platform name (PyV8, smjs, Mozilla, IE6, Opera, Safari etc.)
platform = ''  # to be updated by app, on compile

# a dictionary of module override names (platform-specific)
overrides = {}  # to be updated by app, on compile

# the remote path for loading modules
loadpath = None

stacktrace = None

appname = None


def setloadpath(lp):
    global loadpath
    loadpath = lp


def setappname(an):
    global appname
    appname = an


def getloadpath():
    return loadpath


def addoverride(module_name, path):
    overrides[module_name] = path


def addstack(linedebug):
    JS("""
        if (pyjslib.bool((sys.stacktrace === null))) {
            sys.stacktrace = new pyjslib.List([]);
        }
        sys.stacktrace.append(linedebug);
    """)


def popstack():
    JS("""
        sys.stacktrace.pop()
    """)


def printstack():
    JS("""
        var res = '';

        var __l = sys.stacktrace.__iter__();
        try {
            while (true) {
                var l = __l.next();
                res +=  ( l + '\\n' ) ;
            }
        } catch (e) {
            if (e != pyjslib.StopIteration) {
                throw e;
            }
        }

        return res;
    """)
