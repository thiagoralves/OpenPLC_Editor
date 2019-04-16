# Copyright 2006 James Tauber and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-function-args,undefined-variable,no-absolute-import,assign-to-new-keyword,nonzero-method,next-method-called,next-method-defined

# iteration from Bob Ippolito's Iteration in JavaScript

from __pyjamas__ import JS

# must declare import _before_ importing sys


def import_module(path, parent_module, module_name, dynamic=1, async=False):

    JS("""
        var cache_file;

        if (module_name == "sys" || module_name == 'pyjslib')
        {
            /*module_load_request[module_name] = 1;*/
            return;
        }

        if (path == null)
        {
            path = './';
        }

        var override_name = sys.platform + "." + module_name;
        if (((sys.overrides != null) &&
             (sys.overrides.has_key(override_name))))
        {
            cache_file =  sys.overrides.__getitem__(override_name) ;
        }
        else
        {
            cache_file =  module_name ;
        }

        cache_file = (path + cache_file + '.cache.js' ) ;

        //alert("cache " + cache_file + " " + module_name + " " + parent_module);

        /* already loaded? */
        if (module_load_request[module_name])
        {
            if (module_load_request[module_name] >= 3 && parent_module != null)
            {
                //onload_fn = parent_module + '.' + module_name + ' = ' + module_name + ';';
                //pyjs_eval(onload_fn); /* set up the parent-module namespace */
            }
            return;
        }
        if (typeof (module_load_request[module_name]) == 'undefined')
        {
            module_load_request[module_name] = 1;
        }

        /* following a load, this first executes the script
         * "preparation" function MODULENAME_loaded_fn()
         * and then sets up the loaded module in the namespace
         * of the parent.
         */

        onload_fn = ''; // module_name + "_loaded_fn();"

        if (parent_module != null)
        {
            //onload_fn += parent_module + '.' + module_name + ' = ' + module_name + ';';
            /*pmod = parent_module + '.' + module_name;
            onload_fn += 'alert("' + pmod + '"+' + pmod+');';*/
        }


        if (dynamic)
        {
            /* this one tacks the script onto the end of the DOM
             */

            pyjs_load_script(cache_file, onload_fn, async);

            /* this one actually RUNS the script (eval) into the page.
               my feeling is that this would be better for non-async
               but i can't get it to work entirely yet.
             */
            /*pyjs_ajax_eval(cache_file, onload_fn, async);*/
        }
        else
        {
            if (module_name != "pyjslib" &&
                module_name != "sys")
                pyjs_eval(onload_fn);
        }

    """)


JS("""
function import_wait(proceed_fn, parent_mod, dynamic) {

    var data = '';
    var element = $doc.createElement("div");
    $doc.body.appendChild(element);
    function write_dom(txt) {
        element.innerHTML = txt + '<br />';
    }

    var timeoutperiod = 1;
    if (dynamic)
        var timeoutperiod = 1;

    var wait = function() {

        var status = '';
        for (l in module_load_request)
        {
            var m = module_load_request[l];
            if (l == "sys" || l == 'pyjslib')
                continue;
            status += l + m + " ";
        }

        //write_dom( " import wait " + wait_count + " " + status + " parent_mod " + parent_mod);
        wait_count += 1;

        if (status == '')
        {
            setTimeout(wait, timeoutperiod);
            return;
        }

        for (l in module_load_request)
        {
            var m = module_load_request[l];
            if (l == "sys" || l == 'pyjslib')
            {
                module_load_request[l] = 4;
                continue;
            }
            if ((parent_mod != null) && (l == parent_mod))
            {
                if (m == 1)
                {
                    setTimeout(wait, timeoutperiod);
                    return;
                }
                if (m == 2)
                {
                    /* cheat and move app on to next stage */
                    module_load_request[l] = 3;
                }
            }
            if (m == 1 || m == 2)
            {
                setTimeout(wait, timeoutperiod);
                return;
            }
            if (m == 3)
            {
                //alert("waited for module " + l + ": loaded");
                module_load_request[l] = 4;
                mod_fn = modules[l];
            }
        }
        //alert("module wait done");

        if (proceed_fn.importDone)
            proceed_fn.importDone(proceed_fn);
        else
            proceed_fn();
    }

    wait();
}
""")


# pylint: disable=old-style-class
class Object:
    def __init__(self):
        pass


object = Object


class Modload:

    def __init__(self, path, app_modlist, app_imported_fn, dynamic,
                 parent_mod):
        self.app_modlist = app_modlist
        self.app_imported_fn = app_imported_fn
        self.path = path
        self.idx = 0
        self.dynamic = dynamic
        self.parent_mod = parent_mod

    def next(self):

        for i in range(len(self.app_modlist[self.idx])):
            app = self.app_modlist[self.idx][i]
            import_module(self.path, self.parent_mod, app, self.dynamic, True)
        self.idx += 1

        if self.idx >= len(self.app_modlist):
            import_wait(self.app_imported_fn, self.parent_mod, self.dynamic)
        else:
            import_wait(getattr(self, "next"), self.parent_mod, self.dynamic)


def get_module(module_name):
    _ev = "__mod = %s;" % module_name
    JS("pyjs_eval(_ev);")
    return __mod


def preload_app_modules(path, app_modnames, app_imported_fn, dynamic,
                        parent_mod=None):

    loader = Modload(path, app_modnames, app_imported_fn, dynamic, parent_mod)
    loader.next()


# as comment on line 20 says
# import sys should be below
import sys  # noqa # pylint: disable=wrong-import-order,unused-import,wrong-import-position


class BaseException:

    name = "BaseException"

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        if len(self.args) is 0:
            return ''
        elif len(self.args) is 1:
            return repr(self.args[0])
        return repr(self.args)

    def toString(self):
        return str(self)


class Exception(BaseException):
    name = "Exception"


class TypeError(BaseException):
    name = "TypeError"


class StandardError(Exception):
    name = "StandardError"


class LookupError(StandardError):
    name = "LookupError"

    def toString(self):
        return self.name + ": " + self.args[0]


class KeyError(LookupError):
    name = "KeyError"


class AttributeError(StandardError):
    name = "AttributeError"

    def toString(self):
        return "AttributeError: %s of %s" % (self.args[1], self.args[0])


JS(r"""
pyjslib.StopIteration = function () { };
pyjslib.StopIteration.prototype = new Error();
pyjslib.StopIteration.name = 'StopIteration';
pyjslib.StopIteration.message = 'StopIteration';

pyjslib.String_find = function(sub, start, end) {
    var pos=this.indexOf(sub, start);
    if (pyjslib.isUndefined(end)) return pos;

    if (pos + sub.length>end) return -1;
    return pos;
}

pyjslib.String_join = function(data) {
    var text="";

    if (pyjslib.isArray(data)) {
        return data.join(this);
    }
    else if (pyjslib.isIteratable(data)) {
        var iter=data.__iter__();
        try {
            text+=iter.next();
            while (true) {
                var item=iter.next();
                text+=this + item;
            }
        }
        catch (e) {
            if (e != pyjslib.StopIteration) throw e;
        }
    }

    return text;
}

pyjslib.String_isdigit = function() {
    return (this.match(/^\d+$/g) != null);
}

pyjslib.String_replace = function(old, replace, count) {
    var do_max=false;
    var start=0;
    var new_str="";
    var pos=0;

    if (!pyjslib.isString(old)) return this.__replace(old, replace);
    if (!pyjslib.isUndefined(count)) do_max=true;

    while (start<this.length) {
        if (do_max && !count--) break;

        pos=this.indexOf(old, start);
        if (pos<0) break;

        new_str+=this.substring(start, pos) + replace;
        start=pos+old.length;
    }
    if (start<this.length) new_str+=this.substring(start);

    return new_str;
}

pyjslib.String_split = function(sep, maxsplit) {
    var items=new pyjslib.List();
    var do_max=false;
    var subject=this;
    var start=0;
    var pos=0;

    if (pyjslib.isUndefined(sep) || pyjslib.isNull(sep)) {
        sep=" ";
        subject=subject.strip();
        subject=subject.replace(/\s+/g, sep);
    }
    else if (!pyjslib.isUndefined(maxsplit)) do_max=true;

    if (subject.length == 0) {
        return items;
    }

    while (start<subject.length) {
        if (do_max && !maxsplit--) break;

        pos=subject.indexOf(sep, start);
        if (pos<0) break;

        items.append(subject.substring(start, pos));
        start=pos+sep.length;
    }
    if (start<=subject.length) items.append(subject.substring(start));

    return items;
}

pyjslib.String___iter__ = function() {
    var i = 0;
    var s = this;
    return {
        'next': function() {
            if (i >= s.length) {
                throw pyjslib.StopIteration;
            }
            return s.substring(i++, i, 1);
        },
        '__iter__': function() {
            return this;
        }
    };
}

pyjslib.String_strip = function(chars) {
    return this.lstrip(chars).rstrip(chars);
}

pyjslib.String_lstrip = function(chars) {
    if (pyjslib.isUndefined(chars)) return this.replace(/^\s+/, "");

    return this.replace(new RegExp("^[" + chars + "]+"), "");
}

pyjslib.String_rstrip = function(chars) {
    if (pyjslib.isUndefined(chars)) return this.replace(/\s+$/, "");

    return this.replace(new RegExp("[" + chars + "]+$"), "");
}

pyjslib.String_startswith = function(prefix, start) {
    if (pyjslib.isUndefined(start)) start = 0;

    if (this.substring(start, prefix.length) == prefix) return true;
    return false;
}

pyjslib.abs = Math.abs;

""")


class Class:
    def __init__(self, name):
        self.name = name

    def __str___(self):
        return self.name


def eq(a, b):
    JS("""
    if (pyjslib.hasattr(a, "__cmp__")) {
        return a.__cmp__(b) == 0;
    } else if (pyjslib.hasattr(b, "__cmp__")) {
        return b.__cmp__(a) == 0;
    }
    return a == b;
    """)


def cmp(a, b):
    if hasattr(a, "__cmp__"):
        return a.__cmp__(b)
    elif hasattr(b, "__cmp__"):
        return -b.__cmp__(a)
    if a > b:
        return 1
    elif b > a:
        return -1
    else:
        return 0


def bool(v):
    # this needs to stay in native code without any dependencies here,
    # because this is used by if and while, we need to prevent
    # recursion
    JS("""
    if (!v) return false;
    switch(typeof v){
    case 'boolean':
        return v;
    case 'object':
        if (v.__nonzero__){
            return v.__nonzero__();
        }else if (v.__len__){
            return v.__len__()>0;
        }
        return true;
    }
    return Boolean(v);
    """)


class List:
    def __init__(self, data=None):
        JS("""
        this.l = [];
        this.extend(data);
        """)

    def append(self, item):
        JS("""    this.l[this.l.length] = item;""")

    def extend(self, data):
        JS("""
        if (pyjslib.isArray(data)) {
            n = this.l.length;
            for (var i=0; i < data.length; i++) {
                this.l[n+i]=data[i];
                }
            }
        else if (pyjslib.isIteratable(data)) {
            var iter=data.__iter__();
            var i=this.l.length;
            try {
                while (true) {
                    var item=iter.next();
                    this.l[i++]=item;
                    }
                }
            catch (e) {
                if (e != pyjslib.StopIteration) throw e;
                }
            }
        """)

    def remove(self, value):
        JS("""
        var index=this.index(value);
        if (index<0) return false;
        this.l.splice(index, 1);
        return true;
        """)

    def index(self, value, start=0):
        JS("""
        var length=this.l.length;
        for (var i=start; i<length; i++) {
            if (this.l[i]==value) {
                return i;
                }
            }
        return -1;
        """)

    def insert(self, index, value):
        JS("""    var a = this.l; this.l=a.slice(0, index).concat(value, a.slice(index));""")

    def pop(self, index=-1):
        JS("""
        if (index<0) index = this.l.length + index;
        var a = this.l[index];
        this.l.splice(index, 1);
        return a;
        """)

    def __cmp__(self, l):
        if not isinstance(l, List):
            return -1
        ll = len(self) - len(l)
        if ll != 0:
            return ll
        for x in range(len(l)):
            ll = cmp(self.__getitem__(x), l[x])
            if ll != 0:
                return ll
        return 0

    def slice(self, lower, upper):
        JS("""
        if (upper==null) return pyjslib.List(this.l.slice(lower));
        return pyjslib.List(this.l.slice(lower, upper));
        """)

    def __getitem__(self, index):
        JS("""
        if (index<0) index = this.l.length + index;
        return this.l[index];
        """)

    def __setitem__(self, index, value):
        JS("""    this.l[index]=value;""")

    def __delitem__(self, index):
        JS("""    this.l.splice(index, 1);""")

    def __len__(self):
        JS("""    return this.l.length;""")

    def __contains__(self, value):
        return self.index(value) >= 0

    def __iter__(self):
        JS("""
        var i = 0;
        var l = this.l;
        return {
            'next': function() {
                if (i >= l.length) {
                    throw pyjslib.StopIteration;
                }
                return l[i++];
            },
            '__iter__': function() {
                return this;
            }
        };
        """)

    def reverse(self):
        JS("""    this.l.reverse();""")

    def sort(self, compareFunc=None, keyFunc=None, reverse=False):
        if not compareFunc:
            compareFunc = cmp
        if keyFunc and reverse:
            def thisSort1(a, b):
                return -compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort1)
        elif keyFunc:
            def thisSort2(a, b):
                return compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort2)
        elif reverse:
            def thisSort3(a, b):
                return -compareFunc(a, b)
            self.l.sort(thisSort3)
        else:
            self.l.sort(compareFunc)

    def getArray(self):
        """
        Access the javascript Array that is used internally by this list
        """
        return self.l

    def __str__(self):
        return repr(self)


list = List


class Tuple:
    def __init__(self, data=None):
        JS("""
        this.l = [];
        this.extend(data);
        """)

    def append(self, item):
        JS("""    this.l[this.l.length] = item;""")

    def extend(self, data):
        JS("""
        if (pyjslib.isArray(data)) {
            n = this.l.length;
            for (var i=0; i < data.length; i++) {
                this.l[n+i]=data[i];
                }
            }
        else if (pyjslib.isIteratable(data)) {
            var iter=data.__iter__();
            var i=this.l.length;
            try {
                while (true) {
                    var item=iter.next();
                    this.l[i++]=item;
                    }
                }
            catch (e) {
                if (e != pyjslib.StopIteration) throw e;
                }
            }
        """)

    def remove(self, value):
        JS("""
        var index=this.index(value);
        if (index<0) return false;
        this.l.splice(index, 1);
        return true;
        """)

    def index(self, value, start=0):
        JS("""
        var length=this.l.length;
        for (var i=start; i<length; i++) {
            if (this.l[i]==value) {
                return i;
                }
            }
        return -1;
        """)

    def insert(self, index, value):
        JS("""    var a = this.l; this.l=a.slice(0, index).concat(value, a.slice(index));""")

    def pop(self, index=-1):
        JS("""
        if (index<0) index = this.l.length + index;
        var a = this.l[index];
        this.l.splice(index, 1);
        return a;
        """)

    def __cmp__(self, l):
        if not isinstance(l, Tuple):
            return -1
        ll = len(self) - len(l)
        if ll != 0:
            return ll
        for x in range(len(l)):
            ll = cmp(self.__getitem__(x), l[x])
            if ll != 0:
                return ll
        return 0

    def slice(self, lower, upper):
        JS("""
        if (upper==null) return pyjslib.Tuple(this.l.slice(lower));
        return pyjslib.Tuple(this.l.slice(lower, upper));
        """)

    def __getitem__(self, index):
        JS("""
        if (index<0) index = this.l.length + index;
        return this.l[index];
        """)

    def __setitem__(self, index, value):
        JS("""    this.l[index]=value;""")

    def __delitem__(self, index):
        JS("""    this.l.splice(index, 1);""")

    def __len__(self):
        JS("""    return this.l.length;""")

    def __contains__(self, value):
        return self.index(value) >= 0

    def __iter__(self):
        JS("""
        var i = 0;
        var l = this.l;
        return {
            'next': function() {
                if (i >= l.length) {
                    throw pyjslib.StopIteration;
                }
                return l[i++];
            },
            '__iter__': function() {
                return this;
            }
        };
        """)

    def reverse(self):
        JS("""    this.l.reverse();""")

    def sort(self, compareFunc=None, keyFunc=None, reverse=False):
        if not compareFunc:
            compareFunc = cmp
        if keyFunc and reverse:
            def thisSort1(a, b):
                return -compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort1)
        elif keyFunc:
            def thisSort2(a, b):
                return compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort2)
        elif reverse:
            def thisSort3(a, b):
                return -compareFunc(a, b)
            self.l.sort(thisSort3)
        else:
            self.l.sort(compareFunc)

    def getArray(self):
        """
        Access the javascript Array that is used internally by this list
        """
        return self.l

    def __str__(self):
        return repr(self)


tuple = Tuple


class Dict:
    def __init__(self, data=None):
        JS("""
        this.d = {};

        if (pyjslib.isArray(data)) {
            for (var i in data) {
                var item=data[i];
                this.__setitem__(item[0], item[1]);
                //var sKey=pyjslib.hash(item[0]);
                //this.d[sKey]=item[1];
                }
            }
        else if (pyjslib.isIteratable(data)) {
            var iter=data.__iter__();
            try {
                while (true) {
                    var item=iter.next();
                    this.__setitem__(item.__getitem__(0), item.__getitem__(1));
                    }
                }
            catch (e) {
                if (e != pyjslib.StopIteration) throw e;
                }
            }
        else if (pyjslib.isObject(data)) {
            for (var key in data) {
                this.__setitem__(key, data[key]);
                }
            }
        """)

    def __setitem__(self, key, value):
        JS("""
        var sKey = pyjslib.hash(key);
        this.d[sKey]=[key, value];
        """)

    def __getitem__(self, key):
        JS("""
        var sKey = pyjslib.hash(key);
        var value=this.d[sKey];
        if (pyjslib.isUndefined(value)){
            throw pyjslib.KeyError(key);
        }
        return value[1];
        """)

    def __nonzero__(self):
        JS("""
        for (var i in this.d){
            return true;
        }
        return false;
        """)

    def __len__(self):
        JS("""
        var size=0;
        for (var i in this.d) size++;
        return size;
        """)

    def has_key(self, key):
        return self.__contains__(key)

    def __delitem__(self, key):
        JS("""
        var sKey = pyjslib.hash(key);
        delete this.d[sKey];
        """)

    def __contains__(self, key):
        JS("""
        var sKey = pyjslib.hash(key);
        return (pyjslib.isUndefined(this.d[sKey])) ? false : true;
        """)

    def keys(self):
        JS("""
        var keys=new pyjslib.List();
        for (var key in this.d) {
            keys.append(this.d[key][0]);
        }
        return keys;
        """)

    def values(self):
        JS("""
        var values=new pyjslib.List();
        for (var key in this.d) values.append(this.d[key][1]);
        return values;
        """)

    def items(self):
        JS("""
        var items = new pyjslib.List();
        for (var key in this.d) {
          var kv = this.d[key];
          items.append(new pyjslib.List(kv))
          }
          return items;
        """)

    def __iter__(self):
        return self.keys().__iter__()

    def iterkeys(self):
        return self.__iter__()

    def itervalues(self):
        return self.values().__iter__()

    def iteritems(self):
        return self.items().__iter__()

    def setdefault(self, key, default_value):
        if key not in self:
            self[key] = default_value

    def get(self, key, default_=None):
        if key not in self:
            return default_
        return self[key]

    def update(self, d):
        for k, v in d.iteritems():
            self[k] = v

    def getObject(self):
        """
        Return the javascript Object which this class uses to store
        dictionary keys and values
        """
        return self.d

    def copy(self):
        return Dict(self.items())

    def __str__(self):
        return repr(self)


dict = Dict

# taken from mochikit: range( [start,] stop[, step] )


def range():
    JS("""
    var start = 0;
    var stop = 0;
    var step = 1;

    if (arguments.length == 2) {
        start = arguments[0];
        stop = arguments[1];
        }
    else if (arguments.length == 3) {
        start = arguments[0];
        stop = arguments[1];
        step = arguments[2];
        }
    else if (arguments.length>0) stop = arguments[0];

    return {
        'next': function() {
            if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) throw pyjslib.StopIteration;
            var rval = start;
            start += step;
            return rval;
            },
        '__iter__': function() {
            return this;
            }
        }
    """)


def slice(object, lower, upper):
    JS("""
    if (pyjslib.isString(object)) {
        if (lower < 0) {
           lower = object.length + lower;
        }
        if (upper < 0) {
           upper = object.length + upper;
        }
        if (pyjslib.isNull(upper)) upper=object.length;
        return object.substring(lower, upper);
    }
    if (pyjslib.isObject(object) && object.slice)
        return object.slice(lower, upper);

    return null;
    """)


def str(text):
    JS("""
    if (pyjslib.hasattr(text,"__str__")) {
        return text.__str__();
    }
    return String(text);
    """)


def ord(x):
    if isString(x) and len(x) is 1:
        JS("""
            return x.charCodeAt(0);
        """)
    else:
        JS("""
            throw pyjslib.TypeError();
        """)
    return None


def chr(x):
    JS("""
        return String.fromCharCode(x)
    """)


def is_basetype(x):
    JS("""
       var t = typeof(x);
       return t == 'boolean' ||
       t == 'function' ||
       t == 'number' ||
       t == 'string' ||
       t == 'undefined'
       ;
    """)


def get_pyjs_classtype(x):
    JS("""
       if (pyjslib.hasattr(x, "__class__"))
           if (pyjslib.hasattr(x.__class__, "__new__"))
               var src = x.__class__.__name__;
               return src;
       return null;
    """)


def repr(x):
    """ Return the string representation of 'x'.
    """
    JS("""
       if (x === null)
           return "null";

       if (x === undefined)
           return "undefined";

       var t = typeof(x);

        //alert("repr typeof " + t + " : " + x);

       if (t == "boolean")
           return x.toString();

       if (t == "function")
           return "<function " + x.toString() + ">";

       if (t == "number")
           return x.toString();

       if (t == "string") {
           if (x.indexOf("'") == -1)
               return "'" + x + "'";
           if (x.indexOf('"') == -1)
               return '"' + x + '"';
           var s = x.replace(new RegExp('"', "g"), '\\\\"');
           return '"' + s + '"';
       };

       if (t == "undefined")
           return "undefined";

       // If we get here, x is an object.  See if it's a Pyjamas class.

       if (!pyjslib.hasattr(x, "__init__"))
           return "<" + x.toString() + ">";

       // Handle the common Pyjamas data types.

       var constructor = "UNKNOWN";

       constructor = pyjslib.get_pyjs_classtype(x);

        //alert("repr constructor: " + constructor);

       if (constructor == "Tuple") {
           var contents = x.getArray();
           var s = "(";
           for (var i=0; i < contents.length; i++) {
               s += pyjslib.repr(contents[i]);
               if (i < contents.length - 1)
                   s += ", ";
           };
           s += ")"
           return s;
       };

       if (constructor == "List") {
           var contents = x.getArray();
           var s = "[";
           for (var i=0; i < contents.length; i++) {
               s += pyjslib.repr(contents[i]);
               if (i < contents.length - 1)
                   s += ", ";
           };
           s += "]"
           return s;
       };

       if (constructor == "Dict") {
           var keys = new Array();
           for (var key in x.d)
               keys.push(key);

           var s = "{";
           for (var i=0; i<keys.length; i++) {
               var key = keys[i]
               s += pyjslib.repr(key) + ": " + pyjslib.repr(x.d[key]);
               if (i < keys.length-1)
                   s += ", "
           };
           s += "}";
           return s;
       };

       // If we get here, the class isn't one we know -> return the class name.
       // Note that we replace underscores with dots so that the name will
       // (hopefully!) look like the original Python name.

       //var s = constructor.replace(new RegExp('_', "g"), '.');
       return "<" + constructor + " object>";
    """)


def float(text):
    JS("""
    return parseFloat(text);
    """)


def int(text, radix=0):
    JS("""
    return parseInt(text, radix);
    """)


def len(object):
    JS("""
    if (object==null) return 0;
    if (pyjslib.isObject(object) && object.__len__) return object.__len__();
    return object.length;
    """)


def isinstance(object_, classinfo):
    if pyjslib.isUndefined(object_):
        return False
    if not pyjslib.isObject(object_):

        return False
    if _isinstance(classinfo, Tuple):
        for ci in classinfo:
            if isinstance(object_, ci):
                return True
        return False
    else:
        return _isinstance(object_, classinfo)


def _isinstance(object_, classinfo):
    if not pyjslib.isObject(object_):
        return False
    JS("""
    if (object_.__class__){
        var res =  object_ instanceof classinfo.constructor;
        return res;
    }
    return false;
    """)


def getattr(obj, name, default_=None):
    JS("""
    if ((!pyjslib.isObject(obj))||(pyjslib.isUndefined(obj[name]))){
        if (pyjslib.isUndefined(default_)){
            throw pyjslib.AttributeError(obj, name);
        }else{
        return default_;
        }
    }
    if (!pyjslib.isFunction(obj[name])) return obj[name];
    var fnwrap = function() {
        var args = [];
        for (var i = 0; i < arguments.length; i++) {
          args.push(arguments[i]);
        }
        return obj[name].apply(obj,args);
        }
    fnwrap.__name__ = name;
    return fnwrap;
    """)


def setattr(obj, name, value):
    JS("""
    if (!pyjslib.isObject(obj)) return null;

    obj[name] = value;

    """)


def hasattr(obj, name):
    JS("""
    if (!pyjslib.isObject(obj)) return false;
    if (pyjslib.isUndefined(obj[name])) return false;

    return true;
    """)


def dir(obj):
    JS("""
    var properties=new pyjslib.List();
    for (property in obj) properties.append(property);
    return properties;
    """)


def filter(obj, method, sequence=None):
    # object context is LOST when a method is passed, hence object must be passed separately
    # to emulate python behaviour, should generate this code inline rather than as a function call
    items = []
    if sequence is None:
        sequence = method
        method = obj

        for item in sequence:
            if method(item):
                items.append(item)
    else:
        for item in sequence:
            if method.call(obj, item):
                items.append(item)

    return items


def map(obj, method, sequence=None):
    items = []

    if sequence is None:
        sequence = method
        method = obj

        for item in sequence:
            items.append(method(item))
    else:
        for item in sequence:
            items.append(method.call(obj, item))

    return items


def enumerate(sequence):
    enumeration = []
    nextIndex = 0
    for item in sequence:
        enumeration.append([nextIndex, item])
        nextIndex = nextIndex + 1
    return enumeration


def min(*sequence):
    minValue = None
    for item in sequence:
        if minValue is None:
            minValue = item
        elif item < minValue:
            minValue = item
    return minValue


def max(*sequence):
    maxValue = None
    for item in sequence:
        if maxValue is None:
            maxValue = item
        elif item > maxValue:
            maxValue = item
    return maxValue


next_hash_id = 0


def hash(obj):
    JS("""
    if (obj == null) return null;

    if (obj.$H) return obj.$H;
    if (obj.__hash__) return obj.__hash__();
    if (obj.constructor == String || obj.constructor == Number || obj.constructor == Date) return obj;

    obj.$H = ++pyjslib.next_hash_id;
    return obj.$H;
    """)


# type functions from Douglas Crockford's Remedial Javascript: http://www.crockford.com/javascript/remedial.html
def isObject(a):
    JS("""
    return (a != null && (typeof a == 'object')) || pyjslib.isFunction(a);
    """)


def isFunction(a):
    JS("""
    return typeof a == 'function';
    """)


def isString(a):
    JS("""
    return typeof a == 'string';
    """)


def isNull(a):
    JS("""
    return typeof a == 'object' && !a;
    """)


def isArray(a):
    JS("""
    return pyjslib.isObject(a) && a.constructor == Array;
    """)


def isUndefined(a):
    JS("""
    return typeof a == 'undefined';
    """)


def isIteratable(a):
    JS("""
    return pyjslib.isString(a) || (pyjslib.isObject(a) && a.__iter__);
    """)


def isNumber(a):
    JS("""
    return typeof a == 'number' && isFinite(a);
    """)


def toJSObjects(x):
    """
       Convert the pyjs pythonic List and Dict objects into javascript Object and Array
       objects, recursively.
    """
    if isArray(x):
        JS("""
        var result = [];
        for(var k=0; k < x.length; k++) {
           var v = x[k];
           var tv = pyjslib.toJSObjects(v);
           result.push(tv);
        }
        return result;
        """)
    if isObject(x):
        if isinstance(x, Dict):
            JS("""
            var o = x.getObject();
            var result = {};
            for (var i in o) {
               result[o[i][0].toString()] = o[i][1];
            }
            return pyjslib.toJSObjects(result)
            """)
        elif isinstance(x, List):
            return toJSObjects(x.l)
        elif hasattr(x, '__class__'):
            # we do not have a special implementation for custom
            # classes, just pass it on
            return x
    if isObject(x):
        JS("""
        var result = {};
        for(var k in x) {
            var v = x[k];
            var tv = pyjslib.toJSObjects(v)
            result[k] = tv;
            }
            return result;
         """)
    return x


def printFunc(objs):
    JS("""
    if ($wnd.console==undefined)  return;
    var s = "";
    for(var i=0; i < objs.length; i++) {
        if(s != "") s += " ";
        s += objs[i];
    }
    console.debug(s)
    """)


def type(clsname, bases=None, methods=None):
    """ creates a class, derived from bases, with methods and variables
    """

    JS(" var mths = {}; ")
    if methods:
        for k in methods.keys():
            _mth = methods[k]
            JS(" mths[k] = _mth; ")

    JS(" var bss = null; ")
    if bases:
        JS("bss = bases.l;")
    JS(" return pyjs_type(clsname, bss, mths); ")
