#!/usr/bin/env python
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
#
# pylint: disable=no-absolute-import,bad-python3-import

from __future__ import print_function
import sys
import compiler
from compiler import ast
import os
import copy
from builtins import str as text
from past.builtins import basestring
from six.moves import cStringIO

# the standard location for builtins (e.g. pyjslib) can be
# over-ridden by changing this.  it defaults to sys.prefix
# so that on a system-wide install of pyjamas the builtins
# can be found in e.g. {sys.prefix}/share/pyjamas
#
# over-rides can be done by either explicitly modifying
# pyjs.prefix or by setting an environment variable, PYJSPREFIX.

prefix = sys.prefix

if 'PYJSPREFIX' in os.environ:
    prefix = os.environ['PYJSPREFIX']

# pyjs.path is the list of paths, just like sys.path, from which
# library modules will be searched for, for compile purposes.
# obviously we don't want to use sys.path because that would result
# in compiling standard python modules into javascript!

path = [os.path.abspath('')]

if 'PYJSPATH' in os.environ:
    for p in os.environ['PYJSPATH'].split(os.pathsep):
        p = os.path.abspath(p)
        if os.path.isdir(p):
            path.append(p)

# this is the python function used to wrap native javascript
NATIVE_JS_FUNC_NAME = "JS"

UU = ""

PYJSLIB_BUILTIN_FUNCTIONS = ("cmp",
                             "map",
                             "filter",
                             "dir",
                             "getattr",
                             "setattr",
                             "hasattr",
                             "int",
                             "float",
                             "str",
                             "repr",
                             "range",
                             "len",
                             "hash",
                             "abs",
                             "ord",
                             "chr",
                             "enumerate",
                             "min",
                             "max",
                             "bool",
                             "type",
                             "isinstance")

PYJSLIB_BUILTIN_CLASSES = ("BaseException",
                           "Exception",
                           "StandardError",
                           "StopIteration",
                           "AttributeError",
                           "TypeError",
                           "KeyError",
                           "LookupError",
                           "list",
                           "dict",
                           "object",
                           "tuple")


def pyjs_builtin_remap(name):
    # XXX HACK!
    if name == 'list':
        name = 'List'
    if name == 'object':
        name = '__Object'
    if name == 'dict':
        name = 'Dict'
    if name == 'tuple':
        name = 'Tuple'
    return name


# XXX: this is a hack: these should be dealt with another way
# however, console is currently the only global name which is causing
# problems.
PYJS_GLOBAL_VARS = ("console")

# This is taken from the django project.
# Escape every ASCII character with a value less than 32.
JS_ESCAPES = (
    ('\\', r'\x5C'),
    ('\'', r'\x27'),
    ('"', r'\x22'),
    ('>', r'\x3E'),
    ('<', r'\x3C'),
    ('&', r'\x26'),
    (';', r'\x3B')
    ) + tuple([('%c' % z, '\\x%02X' % z) for z in range(32)])


def escapejs(value):
    """Hex encodes characters for use in JavaScript strings."""
    for bad, good in JS_ESCAPES:
        value = value.replace(bad, good)
    return value


def uuprefix(name, leave_alone=0):
    name = name.split(".")
    name = name[:leave_alone] + map(lambda x: "__%s" % x, name[leave_alone:])
    return '.'.join(name)


class Klass(object):

    klasses = {}

    def __init__(self, name, name_):
        self.name = name
        self.name_ = name_
        self.klasses[name] = self
        self.functions = set()

    def set_base(self, base_name):
        self.base = self.klasses.get(base_name)

    def add_function(self, function_name):
        self.functions.add(function_name)


class TranslationError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self)
        self.message = "line %s:\n%s\n%s" % (node.lineno, message, node)

    def __str__(self):
        return self.message


def strip_py(name):
    return name


def mod_var_name_decl(raw_module_name):
    """ function to get the last component of the module e.g.
        pyjamas.ui.DOM into the "namespace".  i.e. doing
        "import pyjamas.ui.DOM" actually ends up with _two_
        variables - one pyjamas.ui.DOM, the other just "DOM".
        but "DOM" is actually local, hence the "var" prefix.

        for PyV8, this might end up causing problems - we'll have
        to see: gen_mod_import and mod_var_name_decl might have
        to end up in a library-specific module, somewhere.
    """
    name = raw_module_name.split(".")
    if len(name) == 1:
        return ''
    child_name = name[-1]
    return "var %s = %s;\n" % (child_name, raw_module_name)


def gen_mod_import(parentName, importName, dynamic=1):
    # pyjs_ajax_eval("%(n)s.cache.js", null, true);
    return """
    pyjslib.import_module(sys.loadpath, '%(p)s', '%(n)s', %(d)d, false);
    """ % ({'p': parentName, 'd': dynamic, 'n': importName}) + \
        mod_var_name_decl(importName)


class Translator(object):

    def __init__(self, mn, module_name, raw_module_name, src, debug, mod, output,
                 dynamic=0, optimize=False,
                 findFile=None):

        if module_name:
            self.module_prefix = module_name + "."
        else:
            self.module_prefix = ""
        self.raw_module_name = raw_module_name
        src = src.replace("\r\n", "\n")
        src = src.replace("\n\r", "\n")
        src = src.replace("\r",   "\n")
        self.src = src.split("\n")
        self.debug = debug
        self.imported_modules = []
        self.imported_modules_as = []
        self.imported_js = set()
        self.top_level_functions = set()
        self.top_level_classes = set()
        self.top_level_vars = set()
        self.local_arg_stack = [[]]
        self.output = output
        self.imported_classes = {}
        self.method_imported_globals = set()
        self.method_self = None
        self.nextTupleAssignID = 1
        self.dynamic = dynamic
        self.optimize = optimize
        self.findFile = findFile

        if module_name.find(".") >= 0:
            vdec = ''
        else:
            vdec = 'var '
        self.printo(UU+"%s%s = function (__mod_name__) {" % (vdec, module_name))

        self.printo("    if("+module_name+".__was_initialized__) return;")
        self.printo("    "+UU+module_name+".__was_initialized__ = true;")
        self.printo(UU+"if (__mod_name__ == null) __mod_name__ = '%s';" % (mn))
        self.printo(UU+"%s.__name__ = __mod_name__;" % (raw_module_name))

        decl = mod_var_name_decl(raw_module_name)
        if decl:
            self.printo(decl)

        if self.debug:
            haltException = self.module_prefix + "HaltException"
            self.printo(haltException + ' = function () {')
            self.printo('  this.message = "Program Halted";')
            self.printo('  this.name = "' + haltException + '";')
            self.printo('}')
            self.printo('')
            self.printo(haltException + ".prototype.__str__ = function()")
            self.printo('{')
            self.printo('return this.message ;')
            self.printo('}')

            self.printo(haltException + ".prototype.toString = function()")
            self.printo('{')
            self.printo('return this.name + ": \\"" + this.message + "\\"";')
            self.printo('}')

            isHaltFunction = self.module_prefix + "IsHaltException"
            self.printo(""")
    %s = function (s) {
      var suffix="HaltException";
      if (s.length < suffix.length) {
        //alert(s + " " + suffix);
        return false;
      } else {
        var ss = s.substring(s.length, (s.length - suffix.length));
        //alert(s + " " + suffix + " " + ss);
        return ss == suffix;
      }
    }
                """ % isHaltFunction)
        for child in mod.node:
            if isinstance(child, ast.Function):
                self.top_level_functions.add(child.name)
            elif isinstance(child, ast.Class):
                self.top_level_classes.add(child.name)

        for child in mod.node:
            if isinstance(child, ast.Function):
                self._function(child, False)
            elif isinstance(child, ast.Class):
                self._class(child)
            elif isinstance(child, ast.Import):
                importName = child.names[0][0]
                if importName == '__pyjamas__':  # special module to help make pyjamas modules loadable in the python interpreter
                    pass
                elif importName.endswith('.js'):
                    self.imported_js.add(importName)
                else:
                    self.add_imported_module(strip_py(importName))
            elif isinstance(child, ast.From):
                if child.modname == '__pyjamas__':  # special module to help make pyjamas modules loadable in the python interpreter
                    pass
                else:
                    self.add_imported_module(child.modname)
                    self._from(child)
            elif isinstance(child, ast.Discard):
                self._discard(child, None)
            elif isinstance(child, ast.Assign):
                self._assign(child, None, True)
            elif isinstance(child, ast.AugAssign):
                self._augassign(child, None)
            elif isinstance(child, ast.If):
                self._if(child, None)
            elif isinstance(child, ast.For):
                self._for(child, None)
            elif isinstance(child, ast.While):
                self._while(child, None)
            elif isinstance(child, ast.Subscript):
                self._subscript_stmt(child, None)
            elif isinstance(child, ast.Global):
                self._global(child, None)
            elif isinstance(child, ast.Printnl):
                self._print(child, None)
            elif isinstance(child, ast.Print):
                self._print(child, None)
            elif isinstance(child, ast.TryExcept):
                self._tryExcept(child, None)
            elif isinstance(child, ast.Raise):
                self._raise(child, None)
            elif isinstance(child, ast.Stmt):
                self._stmt(child, None)
            else:
                raise TranslationError("unsupported type (in __init__)", child)

        # Initialize all classes for this module
        # self.printo("__"+self.modpfx()+\
        #          "classes_initialize = function() {\n")
        # for className in self.top_level_classes:
        #    self.printo("\t"+UU+self.modpfx()+"__"+className+"_initialize();")
        # self.printo("};\n")

        self.printo("return this;\n")
        self.printo("}; /* end %s */ \n" % module_name)

    def printo(self, *args):
        print(*args, file=self.output)

    def module_imports(self):
        return self.imported_modules + self.imported_modules_as

    def add_local_arg(self, varname):
        local_vars = self.local_arg_stack[-1]
        if varname not in local_vars:
            local_vars.append(varname)

    def add_imported_module(self, importName):

        if importName in self.imported_modules:
            return
        self.imported_modules.append(importName)
        name = importName.split(".")
        if len(name) != 1:
            # add the name of the module to the namespace,
            # but don't add the short name to imported_modules
            # because then the short name would be attempted to be
            # added to the dependencies, and it's half way up the
            # module import directory structure!
            child_name = name[-1]
            self.imported_modules_as.append(child_name)
        self.printo(gen_mod_import(self.raw_module_name,
                                   strip_py(importName),
                                   self.dynamic))

    def _default_args_handler(self, node, arg_names, current_klass,
                              output=None):
        if len(node.defaults):
            output = output or self.output
            default_pos = len(arg_names) - len(node.defaults)
            if arg_names and arg_names[0] == self.method_self:
                default_pos -= 1
            for default_node in node.defaults:
                if isinstance(default_node, ast.Const):
                    default_value = self._const(default_node)
                elif isinstance(default_node, ast.Name):
                    default_value = self._name(default_node, current_klass)
                elif isinstance(default_node, ast.UnarySub):
                    default_value = self._unarysub(default_node, current_klass)
                else:
                    raise TranslationError("unsupported type (in _method)", default_node)

                default_name = arg_names[default_pos]
                default_pos += 1
                self.printo("    if (typeof %s == 'undefined') %s=%s;" % (default_name, default_name, default_value))

    def _varargs_handler(self, node, varargname, arg_names, current_klass):
        self.printo("    var", varargname, '= new pyjslib.Tuple();')
        self.printo("    for(var __va_arg="+str(len(arg_names))+"; __va_arg < arguments.length; __va_arg++) {")
        self.printo("        var __arg = arguments[__va_arg];")
        self.printo("        "+varargname+".append(__arg);")
        self.printo("    }")

    def _kwargs_parser(self, node, function_name, arg_names, current_klass):
        if len(node.defaults) or node.kwargs:
            default_pos = len(arg_names) - len(node.defaults)
            if arg_names and arg_names[0] == self.method_self:
                default_pos -= 1
            self.printo(function_name+'.parse_kwargs = function (', ", ".join(["__kwargs"]+arg_names), ") {")
            for _default_node in node.defaults:
                # default_value = self.expr(default_node, current_klass)
                # if isinstance(default_node, ast.Const):
                #     default_value = self._const(default_node)
                # elif isinstance(default_node, ast.Name):
                #     default_value = self._name(default_node)
                # elif isinstance(default_node, ast.UnarySub):
                #     default_value = self._unarysub(default_node, current_klass)
                # else:
                #     raise TranslationError("unsupported type (in _method)", default_node)

                default_name = arg_names[default_pos]
                self.printo("    if (typeof %s == 'undefined')" % (default_name))
                self.printo("        %s=__kwargs.%s;" % (default_name, default_name))
                default_pos += 1

            # self._default_args_handler(node, arg_names, current_klass)
            if node.kwargs:
                arg_names += ["pyjslib.Dict(__kwargs)"]
            self.printo("    var __r = "+"".join(["[", ", ".join(arg_names), "]"])+";")
            if node.varargs:
                self._varargs_handler(node, "__args", arg_names, current_klass)
                self.printo("    __r.push.apply(__r, __args.getArray())")
            self.printo("    return __r;")
            self.printo("};")

    def _function(self, node, local=False):
        if local:
            function_name = node.name
            self.add_local_arg(function_name)
        else:
            function_name = UU + self.modpfx() + node.name

        arg_names = list(node.argnames)
        normal_arg_names = list(arg_names)
        if node.kwargs:
            kwargname = normal_arg_names.pop()
        if node.varargs:
            varargname = normal_arg_names.pop()
        declared_arg_names = list(normal_arg_names)
        if node.kwargs:
            declared_arg_names.append(kwargname)

        function_args = "(" + ", ".join(declared_arg_names) + ")"
        self.printo("%s = function%s {" % (function_name, function_args))
        self._default_args_handler(node, normal_arg_names, None)

        local_arg_names = normal_arg_names + declared_arg_names

        if node.varargs:
            self._varargs_handler(node, varargname, declared_arg_names, None)
            local_arg_names.append(varargname)

        # stack of local variable names for this function call
        self.local_arg_stack.append(local_arg_names)

        for child in node.code:
            self._stmt(child, None)

        # remove the top local arg names
        self.local_arg_stack.pop()

        # we need to return null always, so it is not undefined
        lastStmt = [p for p in node.code][-1]
        if not isinstance(lastStmt, ast.Return):
            if not self._isNativeFunc(lastStmt):
                self.printo("    return null;")

        self.printo("};")
        self.printo("%s.__name__ = '%s';\n" % (function_name, node.name))

        self._kwargs_parser(node, function_name, normal_arg_names, None)

    def _return(self, node, current_klass):
        expr = self.expr(node.value, current_klass)
        # in python a function call always returns None, so we do it
        # here too
        self.printo("    return " + expr + ";")

    def _break(self, node, current_klass):
        self.printo("    break;")

    def _continue(self, node, current_klass):
        self.printo("    continue;")

    def _callfunc(self, v, current_klass):

        if isinstance(v.node, ast.Name):
            if v.node.name in self.top_level_functions:
                call_name = self.modpfx() + v.node.name
            elif v.node.name in self.top_level_classes:
                call_name = self.modpfx() + v.node.name
            elif v.node.name in self.imported_classes:
                call_name = self.imported_classes[v.node.name] + '.' + v.node.name
            elif v.node.name in PYJSLIB_BUILTIN_FUNCTIONS:
                call_name = 'pyjslib.' + v.node.name
            elif v.node.name in PYJSLIB_BUILTIN_CLASSES:
                name = pyjs_builtin_remap(v.node.name)
                call_name = 'pyjslib.' + name
            elif v.node.name == "callable":
                call_name = "pyjslib.isFunction"
            else:
                call_name = v.node.name
            call_args = []
        elif isinstance(v.node, ast.Getattr):
            attr_name = v.node.attrname

            if isinstance(v.node.expr, ast.Name):
                call_name = self._name2(v.node.expr, current_klass, attr_name)
                call_args = []
            elif isinstance(v.node.expr, ast.Getattr):
                call_name = self._getattr2(v.node.expr, current_klass, attr_name)
                call_args = []
            elif isinstance(v.node.expr, ast.CallFunc):
                call_name = self._callfunc(v.node.expr, current_klass) + "." + v.node.attrname
                call_args = []
            elif isinstance(v.node.expr, ast.Subscript):
                call_name = self._subscript(v.node.expr, current_klass) + "." + v.node.attrname
                call_args = []
            elif isinstance(v.node.expr, ast.Const):
                call_name = self.expr(v.node.expr, current_klass) + "." + v.node.attrname
                call_args = []
            else:
                raise TranslationError("unsupported type (in _callfunc)", v.node.expr)
        else:
            raise TranslationError("unsupported type (in _callfunc)", v.node)

        call_name = strip_py(call_name)

        kwargs = []
        star_arg_name = None
        if v.star_args:
            star_arg_name = self.expr(v.star_args, current_klass)

        for ch4 in v.args:
            if isinstance(ch4, ast.Keyword):
                kwarg = ch4.name + ":" + self.expr(ch4.expr, current_klass)
                kwargs.append(kwarg)
            else:
                arg = self.expr(ch4, current_klass)
                call_args.append(arg)

        if kwargs:
            fn_args = ", ".join(['{' + ', '.join(kwargs) + '}']+call_args)
        else:
            fn_args = ", ".join(call_args)

        if kwargs or star_arg_name:
            if not star_arg_name:
                star_arg_name = 'null'
            try:
                call_this, method_name = call_name.rsplit(".", 1)
            except ValueError:
                # Must be a function call ...
                return ("pyjs_kwargs_function_call("+call_name+", " +
                        star_arg_name + ", ["+fn_args+"]" + ")")
            else:
                return ("pyjs_kwargs_method_call("+call_this+", '"+method_name+"', " +
                        star_arg_name + ", ["+fn_args+"]" + ")")
        else:
            return call_name + "(" + ", ".join(call_args) + ")"

    def _print(self, node, current_klass):
        if self.optimize:
            return
        call_args = []
        for ch4 in node.nodes:
            arg = self.expr(ch4, current_klass)
            call_args.append(arg)

        self.printo("pyjslib.printFunc([", ', '.join(call_args), "],", int(isinstance(node, ast.Printnl)), ");")

    def _tryExcept(self, node, current_klass):
        if len(node.handlers) != 1:
            raise TranslationError("except statements in this form are" +
                                   " not supported", node)

        expr = node.handlers[0][0]
        as_ = node.handlers[0][1]
        if as_:
            errName = as_.name
        else:
            errName = 'err'

        # XXX TODO: check that this should instead be added as a _separate_
        # local scope, temporary to the function.  oh dearie me.
        self.add_local_arg(errName)

        self.printo("    try {")
        for stmt in node.body.nodes:
            self._stmt(stmt, current_klass)
        self.printo("    } catch(%s) {" % errName)
        if expr:
            k = []
            if isinstance(expr, ast.Tuple):
                for x in expr.nodes:
                    k.append("(%(err)s.__name__ == %(expr)s.__name__)" % dict(err=errName, expr=self.expr(x, current_klass)))
            else:
                k = [" (%(err)s.__name__ == %(expr)s.__name__) " % dict(err=errName, expr=self.expr(expr, current_klass))]
            self.printo("   if(%s) {" % '||\n\t\t'.join(k))
        for stmt in node.handlers[0][2]:
            self._stmt(stmt, current_klass)
        if expr:
            # self.printo("} else { throw(%s); } " % errName)
            self.printo("}")
        if node.else_ is not None:
            self.printo("    } finally {")
            for stmt in node.else_:
                self._stmt(stmt, current_klass)
        self.printo("    }")

    # XXX: change use_getattr to True to enable "strict" compilation
    # but incurring a 100% performance penalty. oops.
    def _getattr(self, v, current_klass, use_getattr=False):
        attr_name = v.attrname
        if isinstance(v.expr, ast.Name):
            obj = self._name(v.expr, current_klass, return_none_for_module=True)
            if obj is None and v.expr.name in self.module_imports():
                # XXX TODO: distinguish between module import classes
                # and variables.  right now, this is a hack to get
                # the sys module working.
                # if v.expr.name == 'sys':
                return v.expr.name+'.'+attr_name
                # return v.expr.name+'.__'+attr_name+'.prototype.__class__'
            if not use_getattr or attr_name == '__class__' or \
                    attr_name == '__name__':
                return obj + "." + attr_name
            return "pyjslib.getattr(%s, '%s')" % (obj, attr_name)
        elif isinstance(v.expr, ast.Getattr):
            return self._getattr(v.expr, current_klass) + "." + attr_name
        elif isinstance(v.expr, ast.Subscript):
            return self._subscript(v.expr, self.modpfx()) + "." + attr_name
        elif isinstance(v.expr, ast.CallFunc):
            return self._callfunc(v.expr, self.modpfx()) + "." + attr_name
        else:
            raise TranslationError("unsupported type (in _getattr)", v.expr)

    def modpfx(self):
        return strip_py(self.module_prefix)

    def _name(self, v, current_klass, top_level=False,
              return_none_for_module=False):

        if v.name == 'ilikesillynamesfornicedebugcode':
            print(top_level, current_klass, repr(v))
            print(self.top_level_vars)
            print(self.top_level_functions)
            print(self.local_arg_stack)
            print("error...")

        local_var_names = None
        las = len(self.local_arg_stack)
        if las > 0:
            local_var_names = self.local_arg_stack[-1]

        if v.name == "True":
            return "true"
        elif v.name == "False":
            return "false"
        elif v.name == "None":
            return "null"
        elif v.name == '__name__' and current_klass is None:
            return self.modpfx() + v.name
        elif v.name == self.method_self:
            return "this"
        elif v.name in self.top_level_functions:
            return UU+self.modpfx() + v.name
        elif v.name in self.method_imported_globals:
            return UU+self.modpfx() + v.name
        elif not current_klass and las == 1 and v.name in self.top_level_vars:
            return UU+self.modpfx() + v.name
        elif v.name in local_var_names:
            return v.name
        elif v.name in self.imported_classes:
            return UU+self.imported_classes[v.name] + '.__' + v.name + ".prototype.__class__"
        elif v.name in self.top_level_classes:
            return UU+self.modpfx() + "__" + v.name + ".prototype.__class__"
        elif v.name in self.module_imports() and return_none_for_module:
            return None
        elif v.name in PYJSLIB_BUILTIN_CLASSES:
            return "pyjslib." + pyjs_builtin_remap(v.name)
        elif current_klass:
            if v.name not in local_var_names and \
               v.name not in self.top_level_vars and \
               v.name not in PYJS_GLOBAL_VARS and \
               v.name not in self.top_level_functions:

                cls_name = current_klass
                if hasattr(cls_name, "name"):
                    cls_name_ = cls_name.name_
                    cls_name = cls_name.name
                else:
                    cls_name_ = current_klass + "_"  # XXX ???
                name = UU+cls_name_ + ".prototype.__class__." + v.name
                if v.name == 'listener':
                    name = 'listener+' + name
                return name

        return v.name

    def _name2(self, v, current_klass, attr_name):
        obj = v.name

        if obj in self.method_imported_globals:
            call_name = UU+self.modpfx() + obj + "." + attr_name
        elif obj in self.imported_classes:
            # attr_str = ""
            # if attr_name != "__init__":
            attr_str = ".prototype.__class__." + attr_name
            call_name = UU+self.imported_classes[obj] + '.__' + obj + attr_str
        elif obj in self.module_imports():
            call_name = obj + "." + attr_name
        elif obj[0] == obj[0].upper():  # XXX HACK ALERT
            call_name = UU + self.modpfx() + "__" + obj + ".prototype.__class__." + attr_name
        else:
            call_name = UU+self._name(v, current_klass) + "." + attr_name

        return call_name

    def _getattr2(self, v, current_klass, attr_name):
        if isinstance(v.expr, ast.Getattr):
            call_name = self._getattr2(v.expr, current_klass, v.attrname + "." + attr_name)
        elif isinstance(v.expr, ast.Name) and v.expr.name in self.module_imports():
            call_name = UU+v.expr.name + '.__' + v.attrname+".prototype.__class__."+attr_name
        else:
            obj = self.expr(v.expr, current_klass)
            call_name = obj + "." + v.attrname + "." + attr_name

        return call_name

    def _class(self, node):
        """
        Handle a class definition.

        In order to translate python semantics reasonably well, the following
        structure is used:

        A special object is created for the class, which inherits attributes
        from the superclass, or Object if there's no superclass.  This is the
        class object; the object which you refer to when specifying the
        class by name.  Static, class, and unbound methods are copied
        from the superclass object.

        A special constructor function is created with the same name as the
        class, which is used to create instances of that class.

        A javascript class (e.g. a function with a prototype attribute) is
        created which is the javascript class of created instances, and
        which inherits attributes from the class object. Bound methods are
        copied from the superclass into this class rather than inherited,
        because the class object contains unbound, class, and static methods
        that we don't necessarily want to inherit.

        The type of a method can now be determined by inspecting its
        static_method, unbound_method, class_method, or instance_method
        attribute; only one of these should be true.

        Much of this work is done in pyjs_extend, is pyjslib.py
        """
        class_name = self.modpfx() + uuprefix(node.name, 1)
        class_name_ = self.modpfx() + uuprefix(node.name)
        current_klass = Klass(class_name, class_name_)
        init_method = None
        for child in node.code:
            if isinstance(child, ast.Function):
                current_klass.add_function(child.name)
                if child.name == "__init__":
                    init_method = child

        if len(node.bases) == 0:
            base_class = "pyjslib.__Object"
        elif len(node.bases) == 1:
            if isinstance(node.bases[0], ast.Name):
                if node.bases[0].name in self.imported_classes:
                    base_class_ = self.imported_classes[node.bases[0].name] + '.__' + node.bases[0].name
                    base_class = self.imported_classes[node.bases[0].name] + '.' + node.bases[0].name
                else:
                    base_class_ = self.modpfx() + "__" + node.bases[0].name
                    base_class = self.modpfx() + node.bases[0].name
            elif isinstance(node.bases[0], ast.Getattr):
                # the bases are not in scope of the class so do not
                # pass our class to self._name
                base_class_ = self._name(node.bases[0].expr, None) + \
                             ".__" + node.bases[0].attrname
                base_class = \
                    self._name(node.bases[0].expr, None) + \
                    "." + node.bases[0].attrname
            else:
                raise TranslationError("unsupported type (in _class)", node.bases[0])

            current_klass.set_base(base_class)
        else:
            raise TranslationError("more than one base (in _class)", node)

        self.printo(UU+class_name_ + " = function () {")
        # call superconstructor
        # if base_class:
        #    self.printo("    __" + base_class + ".call(this);")
        self.printo("}")

        if not init_method:
            init_method = ast.Function([], "__init__", ["self"], [], 0, None, [])
            # self._method(init_method, current_klass, class_name)

        # Generate a function which constructs the object
        clsfunc = ast.Function(
            [], node.name,
            init_method.argnames[1:],
            init_method.defaults,
            init_method.flags,
            None,
            [ast.Discard(ast.CallFunc(ast.Name("JS"), [ast.Const(
                #            I attempted lazy initialization, but then you can't access static class members
                #            "    if(!__"+base_class+".__was_initialized__)"+
                #            "        __" + class_name + "_initialize();\n" +
                "    var instance = new " + UU + class_name_ + "();\n" +
                "    if(instance.__init__) instance.__init__.apply(instance, arguments);\n" +
                "    return instance;"
            )]))])

        self._function(clsfunc, False)
        self.printo(UU+class_name_ + ".__initialize__ = function () {")
        self.printo("    if("+UU+class_name_+".__was_initialized__) return;")
        self.printo("    "+UU+class_name_+".__was_initialized__ = true;")
        cls_obj = UU+class_name_ + '.prototype.__class__'

        if class_name == "pyjslib.__Object":
            self.printo("    "+cls_obj+" = {};")
        else:
            if base_class and base_class not in ("object", "pyjslib.__Object"):
                self.printo("    if(!"+UU+base_class_+".__was_initialized__)")
                self.printo("        "+UU+base_class_+".__initialize__();")
                self.printo("    pyjs_extend(" + UU+class_name_ + ", "+UU+base_class_+");")
            else:
                self.printo("    pyjs_extend(" + UU+class_name_ + ", "+UU+"pyjslib.__Object);")

        self.printo("    "+cls_obj+".__new__ = "+UU+class_name+";")
        self.printo("    "+cls_obj+".__name__ = '"+UU+node.name+"';")

        for child in node.code:
            if isinstance(child, ast.Pass):
                pass
            elif isinstance(child, ast.Function):
                self._method(child, current_klass, class_name, class_name_)
            elif isinstance(child, ast.Assign):
                self.classattr(child, current_klass)
            elif isinstance(child, ast.Discard) and isinstance(child.expr, ast.Const):
                # Probably a docstring, turf it
                pass
            else:
                raise TranslationError("unsupported type (in _class)", child)
        self.printo("}")

        self.printo(class_name_+".__initialize__();")

    def classattr(self, node, current_klass):
        self._assign(node, current_klass, True)

    def _raise(self, node, current_klass):
        if node.expr2:
            raise TranslationError("More than one expression unsupported",
                                   node)
        self.printo("throw (%s);" % self.expr(
            node.expr1, current_klass))

    def _method(self, node, current_klass, class_name, class_name_):
        # reset global var scope
        self.method_imported_globals = set()

        arg_names = list(node.argnames)

        classmethod = False
        staticmethod = False
        if node.decorators:
            for d in node.decorators:
                if d.name == "classmethod":
                    classmethod = True
                elif d.name == "staticmethod":
                    staticmethod = True

        if staticmethod:
            staticfunc = ast.Function([], class_name_+"."+node.name, node.argnames, node.defaults, node.flags, node.doc, node.code, node.lineno)
            self._function(staticfunc, True)
            self.printo("    " + UU+class_name_ + ".prototype.__class__." + node.name + " = " + class_name_+"."+node.name+";")
            self.printo("    " + UU+class_name_ + ".prototype.__class__." + node.name + ".static_method = true;")
            return
        else:
            if len(arg_names) == 0:
                raise TranslationError("methods must take an argument 'self' (in _method)", node)
            self.method_self = arg_names[0]

            # if not classmethod and arg_names[0] != "self":
            #    raise TranslationError("first arg not 'self' (in _method)", node)

        normal_arg_names = arg_names[1:]
        if node.kwargs:
            kwargname = normal_arg_names.pop()
        if node.varargs:
            varargname = normal_arg_names.pop()
        declared_arg_names = list(normal_arg_names)
        if node.kwargs:
            declared_arg_names.append(kwargname)

        function_args = "(" + ", ".join(declared_arg_names) + ")"

        if classmethod:
            fexpr = UU + class_name_ + ".prototype.__class__." + node.name
        else:
            fexpr = UU + class_name_ + ".prototype." + node.name
        self.printo("    "+fexpr + " = function" + function_args + " {")

        # default arguments
        self._default_args_handler(node, normal_arg_names, current_klass)

        local_arg_names = normal_arg_names + declared_arg_names

        if node.varargs:
            self._varargs_handler(node, varargname, declared_arg_names, current_klass)
            local_arg_names.append(varargname)

        # stack of local variable names for this function call
        self.local_arg_stack.append(local_arg_names)

        for child in node.code:
            self._stmt(child, current_klass)

        # remove the top local arg names
        self.local_arg_stack.pop()

        self.printo("    };")

        self._kwargs_parser(node, fexpr, normal_arg_names, current_klass)

        if classmethod:
            # Have to create a version on the instances which automatically passes the
            # class as "self"
            altexpr = UU + class_name_ + ".prototype." + node.name
            self.printo("    "+altexpr + " = function() {")
            self.printo("        return " + fexpr + ".apply(this.__class__, arguments);")
            self.printo("    };")
            self.printo("    "+fexpr+".class_method = true;")
            self.printo("    "+altexpr+".instance_method = true;")
        else:
            # For instance methods, we need an unbound version in the class object
            altexpr = UU + class_name_ + ".prototype.__class__." + node.name
            self.printo("    "+altexpr + " = function() {")
            self.printo("        return " + fexpr + ".call.apply("+fexpr+", arguments);")
            self.printo("    };")
            self.printo("    "+altexpr+".unbound_method = true;")
            self.printo("    "+fexpr+".instance_method = true;")
            self.printo("    "+altexpr+".__name__ = '%s';" % node.name)

        self.printo(UU + class_name_ + ".prototype.%s.__name__ = '%s';" %
                    (node.name, node.name))

        if node.kwargs or len(node.defaults):
            self.printo("    "+altexpr + ".parse_kwargs = " + fexpr + ".parse_kwargs;")

        self.method_self = None
        self.method_imported_globals = set()

    def _isNativeFunc(self, node):
        if isinstance(node, ast.Discard):
            if isinstance(node.expr, ast.CallFunc):
                if isinstance(node.expr.node, ast.Name) and \
                       node.expr.node.name == NATIVE_JS_FUNC_NAME:
                    return True
        return False

    def _stmt(self, node, current_klass):
        debugStmt = self.debug and not self._isNativeFunc(node)
        if debugStmt:
            self.printo('  try {')

        if isinstance(node, ast.Return):
            self._return(node, current_klass)
        elif isinstance(node, ast.Break):
            self._break(node, current_klass)
        elif isinstance(node, ast.Continue):
            self._continue(node, current_klass)
        elif isinstance(node, ast.Assign):
            self._assign(node, current_klass)
        elif isinstance(node, ast.AugAssign):
            self._augassign(node, current_klass)
        elif isinstance(node, ast.Discard):
            self._discard(node, current_klass)
        elif isinstance(node, ast.If):
            self._if(node, current_klass)
        elif isinstance(node, ast.For):
            self._for(node, current_klass)
        elif isinstance(node, ast.While):
            self._while(node, current_klass)
        elif isinstance(node, ast.Subscript):
            self._subscript_stmt(node, current_klass)
        elif isinstance(node, ast.Global):
            self._global(node, current_klass)
        elif isinstance(node, ast.Pass):
            pass
        elif isinstance(node, ast.Function):
            self._function(node, True)
        elif isinstance(node, ast.Printnl):
            self._print(node, current_klass)
        elif isinstance(node, ast.Print):
            self._print(node, current_klass)
        elif isinstance(node, ast.TryExcept):
            self._tryExcept(node, current_klass)
        elif isinstance(node, ast.Raise):
            self._raise(node, current_klass)
        else:
            raise TranslationError("unsupported type (in _stmt)", node)

        if debugStmt:

            lt = self.get_line_trace(node)
            isHaltFunction = self.module_prefix + "IsHaltException"

            out = (
                '  } catch (__err) {',
                '      if (' + isHaltFunction + '(__err.name)) {',
                '          throw __err;',
                '      } else {',
                '          st = sys.printstack() + ' + '"%s"' % lt + "+ '\\n' ;"
                '          alert("' + 'Error in ' + lt + '"' +
                '+"\\n"+__err.name+": "+__err.message' +
                '+"\\n\\nStack trace:\\n"' + '+st' + ');',
                '          debugger;',
                '          throw new ' + self.module_prefix + 'HaltException();',
                '      }',
                '  }'
            )
            for s in out:
                self.printo(s)

    def get_line_trace(self, node):
        lineNum = "Unknown"
        srcLine = ""
        if hasattr(node, "lineno"):
            if node.lineno is not None:
                lineNum = node.lineno
                srcLine = self.src[min(lineNum, len(self.src))-1]
                srcLine = srcLine.replace('\\', '\\\\')
                srcLine = srcLine.replace('"', '\\"')
                srcLine = srcLine.replace("'", "\\'")

        return self.raw_module_name + ".py, line " \
            + str(lineNum) + ":"\
            + "\\n" \
            + "    " + srcLine

    def _augassign(self, node, current_klass):
        v = node.node
        if isinstance(v, ast.Getattr):
            # XXX HACK!  don't allow += on return result of getattr.
            # TODO: create a temporary variable or something.
            lhs = self._getattr(v, current_klass, False)
        else:
            lhs = self._name(node.node, current_klass)
        op = node.op
        rhs = self.expr(node.expr, current_klass)
        self.printo("    " + lhs + " " + op + " " + rhs + ";")

    def _assign(self, node, current_klass, top_level=False):
        if len(node.nodes) != 1:
            tempvar = '__temp'+str(node.lineno)
            tnode = ast.Assign([ast.AssName(tempvar, "OP_ASSIGN", node.lineno)], node.expr, node.lineno)
            self._assign(tnode, current_klass, top_level)
            for v in node.nodes:
                tnode2 = ast.Assign([v], ast.Name(tempvar, node.lineno), node.lineno)
                self._assign(tnode2, current_klass, top_level)
            return

        local_var_names = None
        if len(self.local_arg_stack) > 0:
            local_var_names = self.local_arg_stack[-1]

        def _lhsFromAttr(v, current_klass):
            attr_name = v.attrname
            if isinstance(v.expr, ast.Name):
                lhs = self._name(v.expr, current_klass) + "." + attr_name
            elif isinstance(v.expr, ast.Getattr):
                lhs = self._getattr(v, current_klass)
            elif isinstance(v.expr, ast.Subscript):
                lhs = self._subscript(v.expr, current_klass) + "." + attr_name
            else:
                raise TranslationError("unsupported type (in _assign)", v.expr)
            return lhs

        def _lhsFromName(v, top_level, current_klass):
            if top_level:
                if current_klass:
                    lhs = UU+current_klass.name_ + ".prototype.__class__." \
                               + v.name
                else:
                    self.top_level_vars.add(v.name)
                    vname = self.modpfx() + v.name
                    if not self.modpfx() and v.name not in\
                       self.method_imported_globals:
                        lhs = "var " + vname
                    else:
                        lhs = UU + vname
                    self.add_local_arg(v.name)
            else:
                if v.name in local_var_names:
                    lhs = v.name
                elif v.name in self.method_imported_globals:
                    lhs = self.modpfx() + v.name
                else:
                    lhs = "var " + v.name
                    self.add_local_arg(v.name)
            return lhs

        dbg = 0
        v = node.nodes[0]
        if isinstance(v, ast.AssAttr):
            lhs = _lhsFromAttr(v, current_klass)
            if v.flags == "OP_ASSIGN":
                op = "="
            else:
                raise TranslationError("unsupported flag (in _assign)", v)

        elif isinstance(v, ast.AssName):
            lhs = _lhsFromName(v, top_level, current_klass)
            if v.flags == "OP_ASSIGN":
                op = "="
            else:
                raise TranslationError("unsupported flag (in _assign)", v)
        elif isinstance(v, ast.Subscript):
            if v.flags == "OP_ASSIGN":
                obj = self.expr(v.expr, current_klass)
                if len(v.subs) != 1:
                    raise TranslationError("must have one sub (in _assign)", v)
                idx = self.expr(v.subs[0], current_klass)
                value = self.expr(node.expr, current_klass)
                self.printo("    " + obj + ".__setitem__(" + idx + ", " + value + ");")
                return
            else:
                raise TranslationError("unsupported flag (in _assign)", v)
        elif isinstance(v, (ast.AssList, ast.AssTuple)):
            uniqueID = self.nextTupleAssignID
            self.nextTupleAssignID += 1
            tempName = "__tupleassign" + str(uniqueID) + "__"
            self.printo("    var " + tempName + " = " + self.expr(node.expr, current_klass) + ";")
            for index, child in enumerate(v.getChildNodes()):
                rhs = tempName + ".__getitem__(" + str(index) + ")"

                if isinstance(child, ast.AssAttr):
                    lhs = _lhsFromAttr(child, current_klass)
                elif isinstance(child, ast.AssName):
                    lhs = _lhsFromName(child, top_level, current_klass)
                elif isinstance(child, ast.Subscript):
                    if child.flags == "OP_ASSIGN":
                        obj = self.expr(child.expr, current_klass)
                        if len(child.subs) != 1:
                            raise TranslationError("must have one sub " +
                                                   "(in _assign)", child)
                        idx = self.expr(child.subs[0], current_klass)
                        value = self.expr(node.expr, current_klass)
                        self.printo("    " + obj + ".__setitem__(" + idx + ", " + rhs + ");")
                        continue
                self.printo("    " + lhs + " = " + rhs + ";")
            return
        else:
            raise TranslationError("unsupported type (in _assign)", v)

        rhs = self.expr(node.expr, current_klass)
        if dbg:
            print("b", repr(node.expr), rhs)
        self.printo("    " + lhs + " " + op + " " + rhs + ";")

    def _discard(self, node, current_klass):

        if isinstance(node.expr, ast.CallFunc):
            debugStmt = self.debug and not self._isNativeFunc(node)
            if debugStmt and isinstance(node.expr.node, ast.Name) and \
               node.expr.node.name == 'import_wait':
                debugStmt = False
            if debugStmt:
                st = self.get_line_trace(node)
                self.printo("sys.addstack('%s');\n" % st)
            if isinstance(node.expr.node, ast.Name) and node.expr.node.name == NATIVE_JS_FUNC_NAME:
                if len(node.expr.args) != 1:
                    raise TranslationError("native javascript function %s must have one arg" % NATIVE_JS_FUNC_NAME, node.expr)
                if not isinstance(node.expr.args[0], ast.Const):
                    raise TranslationError("native javascript function %s must have constant arg" % NATIVE_JS_FUNC_NAME, node.expr)
                raw_js = node.expr.args[0].value
                self.printo(raw_js)
            else:
                expr = self._callfunc(node.expr, current_klass)
                self.printo("    " + expr + ";")

            if debugStmt:
                self.printo("sys.popstack();\n")

        elif isinstance(node.expr, ast.Const):
            if node.expr.value is not None:  # Empty statements generate ignore None
                self.printo(self._const(node.expr))
        else:
            raise TranslationError("unsupported type (in _discard)", node.expr)

    def _if(self, node, current_klass):
        for i in range(len(node.tests)):
            test, consequence = node.tests[i]
            if i == 0:
                keyword = "if"
            else:
                keyword = "else if"

            self._if_test(keyword, test, consequence, current_klass)

        if node.else_:
            keyword = "else"
            test = None
            consequence = node.else_

            self._if_test(keyword, test, consequence, current_klass)

    def _if_test(self, keyword, test, consequence, current_klass):
        if test:
            expr = self.expr(test, current_klass)

            self.printo("    " + keyword + " (pyjslib.bool(" + expr + ")) {")
        else:
            self.printo("    " + keyword + " {")

        if isinstance(consequence, ast.Stmt):
            for child in consequence.nodes:
                self._stmt(child, current_klass)
        else:
            raise TranslationError("unsupported type (in _if_test)", consequence)

        self.printo("    }")

    def _from(self, node):
        for name in node.names:
            # look up "hack" in AppTranslator as to how findFile gets here
            module_name = node.modname + "." + name[0]
            try:
                ff = self.findFile(module_name + ".py")
            except Exception:
                ff = None
            if ff:
                self.add_imported_module(module_name)
            else:
                self.imported_classes[name[0]] = node.modname

    def _compare(self, node, current_klass):
        lhs = self.expr(node.expr, current_klass)

        if len(node.ops) != 1:
            raise TranslationError("only one ops supported (in _compare)", node)

        op = node.ops[0][0]
        rhs_node = node.ops[0][1]
        rhs = self.expr(rhs_node, current_klass)

        if op == "==":
            return "pyjslib.eq(%s, %s)" % (lhs, rhs)
        if op == "in":
            return rhs + ".__contains__(" + lhs + ")"
        elif op == "not in":
            return "!" + rhs + ".__contains__(" + lhs + ")"
        elif op == "is":
            op = "==="
        elif op == "is not":
            op = "!=="

        return "(" + lhs + " " + op + " " + rhs + ")"

    def _not(self, node, current_klass):
        expr = self.expr(node.expr, current_klass)

        return "!(" + expr + ")"

    def _or(self, node, current_klass):
        expr = "("+(") || (".join([self.expr(child, current_klass) for child in node.nodes]))+')'
        return expr

    def _and(self, node, current_klass):
        expr = "("+(") && (".join([self.expr(child, current_klass) for child in node.nodes]))+")"
        return expr

    def _for(self, node, current_klass):
        assign_name = ""
        assign_tuple = ""

        # based on Bob Ippolito's Iteration in Javascript code
        if isinstance(node.assign, ast.AssName):
            assign_name = node.assign.name
            self.add_local_arg(assign_name)
            if node.assign.flags == "OP_ASSIGN":
                op = "="
        elif isinstance(node.assign, ast.AssTuple):
            op = "="
            i = 0
            for child in node.assign:
                child_name = child.name
                if assign_name == "":
                    assign_name = "temp_" + child_name
                self.add_local_arg(child_name)
                assign_tuple += """
                var %(child_name)s %(op)s %(assign_name)s.__getitem__(%(i)i);
                """ % locals()
                i += 1
        else:
            raise TranslationError("unsupported type (in _for)", node.assign)

        if isinstance(node.list, ast.Name):
            list_expr = self._name(node.list, current_klass)
        elif isinstance(node.list, ast.Getattr):
            list_expr = self._getattr(node.list, current_klass)
        elif isinstance(node.list, ast.CallFunc):
            list_expr = self._callfunc(node.list, current_klass)
        else:
            raise TranslationError("unsupported type (in _for)", node.list)

        lhs = "var " + assign_name
        iterator_name = "__" + assign_name

        loc_dict = {
            "iterator_name": iterator_name,
            "list_expr": list_expr,
            "lhs": lhs,
            "op": op,
            "assign_tuple": assign_tuple,
        }

        self.printo("""
        var %(iterator_name)s = %(list_expr)s.__iter__();
        try {
            while (true) {
                %(lhs)s %(op)s %(iterator_name)s.next();
                %(assign_tuple)s
        """ % loc_dict)
        for n in node.body.nodes:
            self._stmt(n, current_klass)
        self.printo("""
            }
        } catch (e) {
            if (e.__name__ != pyjslib.StopIteration.__name__) {
                throw e;
            }
        }
        """)

    def _while(self, node, current_klass):
        test = self.expr(node.test, current_klass)
        self.printo("    while (pyjslib.bool(" + test + ")) {")
        if isinstance(node.body, ast.Stmt):
            for child in node.body.nodes:
                self._stmt(child, current_klass)
        else:
            raise TranslationError("unsupported type (in _while)", node.body)
        self.printo("    }")

    def _const(self, node):
        if isinstance(node.value, int):
            return str(node.value)
        elif isinstance(node.value, float):
            return str(node.value)
        elif isinstance(node.value, basestring):
            v = node.value
            if isinstance(node.value, text):
                v = v.encode('utf-8')
            return "String('%s')" % escapejs(v)
        elif node.value is None:
            return "null"
        else:
            raise TranslationError("unsupported type (in _const)", node)

    def _unaryadd(self, node, current_klass):
        return self.expr(node.expr, current_klass)

    def _unarysub(self, node, current_klass):
        return "-" + self.expr(node.expr, current_klass)

    def _add(self, node, current_klass):
        return self.expr(node.left, current_klass) + " + " + self.expr(node.right, current_klass)

    def _sub(self, node, current_klass):
        return self.expr(node.left, current_klass) + " - " + self.expr(node.right, current_klass)

    def _div(self, node, current_klass):
        return self.expr(node.left, current_klass) + " / " + self.expr(node.right, current_klass)

    def _mul(self, node, current_klass):
        return self.expr(node.left, current_klass) + " * " + self.expr(node.right, current_klass)

    def _mod(self, node, current_klass):
        if isinstance(node.left, ast.Const) and isinstance(node.left.value, str):
            self.imported_js.add("sprintf.js")  # Include the sprintf functionality if it is used
            return "sprintf("+self.expr(node.left, current_klass) + ", " + self.expr(node.right, current_klass)+")"
        return self.expr(node.left, current_klass) + " % " + self.expr(node.right, current_klass)

    def _invert(self, node, current_klass):
        return "~" + self.expr(node.expr, current_klass)

    def _bitand(self, node, current_klass):
        return " & ".join([self.expr(child, current_klass) for child in node.nodes])

    def _bitshiftleft(self, node, current_klass):
        return self.expr(node.left, current_klass) + " << " + self.expr(node.right, current_klass)

    def _bitshiftright(self, node, current_klass):
        return self.expr(node.left, current_klass) + " >>> " + self.expr(node.right, current_klass)

    def _bitxor(self, node, current_klass):
        return " ^ ".join([self.expr(child, current_klass) for child in node.nodes])

    def _bitor(self, node, current_klass):
        return " | ".join([self.expr(child, current_klass) for child in node.nodes])

    def _subscript(self, node, current_klass):
        if node.flags == "OP_APPLY":
            if len(node.subs) == 1:
                return self.expr(node.expr, current_klass) + ".__getitem__(" + self.expr(node.subs[0], current_klass) + ")"
            else:
                raise TranslationError("must have one sub (in _subscript)", node)
        else:
            raise TranslationError("unsupported flag (in _subscript)", node)

    def _subscript_stmt(self, node, current_klass):
        if node.flags == "OP_DELETE":
            self.printo("    " + self.expr(node.expr, current_klass) + ".__delitem__(" + self.expr(node.subs[0], current_klass) + ");")
        else:
            raise TranslationError("unsupported flag (in _subscript)", node)

    def _list(self, node, current_klass):
        return "new pyjslib.List([" + ", ".join([self.expr(x, current_klass) for x in node.nodes]) + "])"

    def _dict(self, node, current_klass):
        items = []
        for x in node.items:
            key = self.expr(x[0], current_klass)
            value = self.expr(x[1], current_klass)
            items.append("[" + key + ", " + value + "]")
        return "new pyjslib.Dict([" + ", ".join(items) + "])"

    def _tuple(self, node, current_klass):
        return "new pyjslib.Tuple([" + ", ".join([self.expr(x, current_klass) for x in node.nodes]) + "])"

    def _lambda(self, node, current_klass):
        if node.varargs:
            raise TranslationError("varargs are not supported in Lambdas", node)
        if node.kwargs:
            raise TranslationError("kwargs are not supported in Lambdas", node)
        res = cStringIO()
        arg_names = list(node.argnames)
        function_args = ", ".join(arg_names)
        for child in node.getChildNodes():
            expr = self.expr(child, None)
        print("function (%s){" % function_args, file=res)
        self._default_args_handler(node, arg_names, None,
                                   output=res)
        print('return %s;}' % expr, file=res)
        return res.getvalue()

    def _slice(self, node, current_klass):
        if node.flags == "OP_APPLY":
            lower = "null"
            upper = "null"
            if node.lower is not None:
                lower = self.expr(node.lower, current_klass)
            if node.upper is not None:
                upper = self.expr(node.upper, current_klass)
            return "pyjslib.slice(" + self.expr(node.expr, current_klass) + ", " + lower + ", " + upper + ")"
        else:
            raise TranslationError("unsupported flag (in _slice)", node)

    def _global(self, node, current_klass):
        for name in node.names:
            self.method_imported_globals.add(name)

    def expr(self, node, current_klass):
        if isinstance(node, ast.Const):
            return self._const(node)
        # @@@ not sure if the parentheses should be here or in individual operator functions - JKT
        elif isinstance(node, ast.Mul):
            return " ( " + self._mul(node, current_klass) + " ) "
        elif isinstance(node, ast.Add):
            return " ( " + self._add(node, current_klass) + " ) "
        elif isinstance(node, ast.Sub):
            return " ( " + self._sub(node, current_klass) + " ) "
        elif isinstance(node, ast.Div):
            return " ( " + self._div(node, current_klass) + " ) "
        elif isinstance(node, ast.Mod):
            return self._mod(node, current_klass)
        elif isinstance(node, ast.UnaryAdd):
            return self._unaryadd(node, current_klass)
        elif isinstance(node, ast.UnarySub):
            return self._unarysub(node, current_klass)
        elif isinstance(node, ast.Not):
            return self._not(node, current_klass)
        elif isinstance(node, ast.Or):
            return self._or(node, current_klass)
        elif isinstance(node, ast.And):
            return self._and(node, current_klass)
        elif isinstance(node, ast.Invert):
            return self._invert(node, current_klass)
        elif isinstance(node, ast.Bitand):
            return "("+self._bitand(node, current_klass)+")"
        elif isinstance(node, ast.LeftShift):
            return self._bitshiftleft(node, current_klass)
        elif isinstance(node, ast.RightShift):
            return self._bitshiftright(node, current_klass)
        elif isinstance(node, ast.Bitxor):
            return "("+self._bitxor(node, current_klass)+")"
        elif isinstance(node, ast.Bitor):
            return "("+self._bitor(node, current_klass)+")"
        elif isinstance(node, ast.Compare):
            return self._compare(node, current_klass)
        elif isinstance(node, ast.CallFunc):
            return self._callfunc(node, current_klass)
        elif isinstance(node, ast.Name):
            return self._name(node, current_klass)
        elif isinstance(node, ast.Subscript):
            return self._subscript(node, current_klass)
        elif isinstance(node, ast.Getattr):
            return self._getattr(node, current_klass)
        elif isinstance(node, ast.List):
            return self._list(node, current_klass)
        elif isinstance(node, ast.Dict):
            return self._dict(node, current_klass)
        elif isinstance(node, ast.Tuple):
            return self._tuple(node, current_klass)
        elif isinstance(node, ast.Slice):
            return self._slice(node, current_klass)
        elif isinstance(node, ast.Lambda):
            return self._lambda(node, current_klass)
        else:
            raise TranslationError("unsupported type (in expr)", node)


def translate(file_name, module_name, debug=False):
    f = open(file_name, "r")
    src = f.read()
    f.close()
    output = cStringIO()
    mod = compiler.parseFile(file_name)
    Translator(module_name, module_name, module_name, src, debug, mod, output)
    return output.getvalue()


class PlatformParser(object):
    def __init__(self, platform_dir="", verbose=True):
        self.platform_dir = platform_dir
        self.parse_cache = {}
        self.platform = ""
        self.verbose = verbose

    def setPlatform(self, platform):
        self.platform = platform

    def parseModule(self, module_name, file_name):

        importing = False
        if file_name not in self.parse_cache:
            importing = True
            mod = compiler.parseFile(file_name)
            self.parse_cache[file_name] = mod
        else:
            mod = self.parse_cache[file_name]

        override = False
        platform_file_name = self.generatePlatformFilename(file_name)
        if self.platform and os.path.isfile(platform_file_name):
            mod = copy.deepcopy(mod)
            mod_override = compiler.parseFile(platform_file_name)
            self.merge(mod, mod_override)
            override = True

        if self.verbose:
            if override:
                print("Importing %s (Platform %s)" % (module_name, self.platform))
            elif importing:
                print("Importing %s" % (module_name))

        return mod, override

    def generatePlatformFilename(self, file_name):
        (module_name, extension) = os.path.splitext(os.path.basename(file_name))
        platform_file_name = module_name + self.platform + extension

        return os.path.join(os.path.dirname(file_name), self.platform_dir, platform_file_name)

    def merge(self, tree1, tree2):
        for child in tree2.node:
            if isinstance(child, ast.Function):
                self.replaceFunction(tree1, child.name, child)
            elif isinstance(child, ast.Class):
                self.replaceClassMethods(tree1, child.name, child)

        return tree1

    def replaceFunction(self, tree, function_name, function_node):
        # find function to replace
        for child in tree.node:
            if isinstance(child, ast.Function) and child.name == function_name:
                self.copyFunction(child, function_node)
                return
        raise TranslationError("function not found: " + function_name, function_node)

    def replaceClassMethods(self, tree, class_name, class_node):
        # find class to replace
        old_class_node = None
        for child in tree.node:
            if isinstance(child, ast.Class) and child.name == class_name:
                old_class_node = child
                break

        if not old_class_node:
            raise TranslationError("class not found: " + class_name, class_node)

        # replace methods
        for function_node in class_node.code:
            if isinstance(function_node, ast.Function):
                found = False
                for child in old_class_node.code:
                    if isinstance(child, ast.Function) and child.name == function_node.name:
                        found = True
                        self.copyFunction(child, function_node)
                        break

                if not found:
                    raise TranslationError("class method not found: " + class_name + "." + function_node.name, function_node)

    def copyFunction(self, target, source):
        target.code = source.code
        target.argnames = source.argnames
        target.defaults = source.defaults
        target.doc = source.doc  # @@@ not sure we need to do this any more


def dotreplace(fname):
    path, ext = os.path.splitext(fname)
    return path.replace(".", "/") + ext


class AppTranslator(object):

    def __init__(self, library_dirs=None, parser=None, dynamic=False,
                 optimize=False, verbose=True):
        self.extension = ".py"
        self.optimize = optimize
        self.library_modules = []
        self.overrides = {}
        library_dirs = [] if library_dirs is None else library_dirs
        self.library_dirs = path + library_dirs
        self.dynamic = dynamic
        self.verbose = verbose

        if not parser:
            self.parser = PlatformParser()
        else:
            self.parser = parser

        self.parser.dynamic = dynamic

    def findFile(self, file_name):
        if os.path.isfile(file_name):
            return file_name

        for library_dir in self.library_dirs:
            file_name = dotreplace(file_name)
            full_file_name = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), library_dir, file_name)
            if os.path.isfile(full_file_name):
                return full_file_name

            fnameinit, _ext = os.path.splitext(file_name)
            fnameinit = fnameinit + "/__init__.py"

            full_file_name = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), library_dir, fnameinit)
            if os.path.isfile(full_file_name):
                return full_file_name

        raise Exception("file not found: " + file_name)

    def _translate(self, module_name, is_app=True, debug=False,
                   imported_js=None):
        if module_name not in self.library_modules:
            self.library_modules.append(module_name)

        file_name = self.findFile(module_name + self.extension)

        output = cStringIO()

        f = open(file_name, "r")
        src = f.read()
        f.close()

        mod, override = self.parser.parseModule(module_name, file_name)
        if override:
            override_name = "%s.%s" % (self.parser.platform.lower(),
                                       module_name)
            self.overrides[override_name] = override_name
        if is_app:
            mn = '__main__'
        else:
            mn = module_name
        t = Translator(mn, module_name, module_name,
                       src, debug, mod, output, self.dynamic, self.optimize,
                       self.findFile)

        module_str = output.getvalue()
        if imported_js is None:
            imported_js = set()
        imported_js.update(set(t.imported_js))
        imported_modules_str = ""
        for module in t.imported_modules:
            if module not in self.library_modules:
                self.library_modules.append(module)
                # imported_js.update(set(t.imported_js))
                # imported_modules_str += self._translate(
                #    module, False, debug=debug, imported_js=imported_js)

        return imported_modules_str + module_str

    def translate(self, module_name, is_app=True, debug=False,
                  library_modules=None):
        app_code = cStringIO()
        lib_code = cStringIO()
        imported_js = set()
        self.library_modules = []
        self.overrides = {}
        if library_modules is not None:
            for library in library_modules:
                if library.endswith(".js"):
                    imported_js.add(library)
                    continue
                self.library_modules.append(library)
                if self.verbose:
                    print('Including LIB', library)
                print('\n//\n// BEGIN LIB '+library+'\n//\n', file=lib_code)
                print(self._translate(library, False, debug=debug, imported_js=imported_js),
                      file=lib_code)

                print("/* initialize static library */", file=lib_code)
                print("%s%s();\n" % (UU, library), file=lib_code)

                print('\n//\n// END LIB '+library+'\n//\n', file=lib_code)
        if module_name:
            print(self._translate(module_name, is_app, debug=debug, imported_js=imported_js),
                  file=app_code)
        for js in imported_js:
            path = self.findFile(js)
            if os.path.isfile(path):
                if self.verbose:
                    print('Including JS', js)
                print('\n//\n// BEGIN JS '+js+'\n//\n', file=lib_code)
                print(open(path).read(), file=lib_code)
                print('\n//\n// END JS '+js+'\n//\n', file=lib_code)
            else:
                print('Warning: Unable to find imported javascript:', js, file=sys.stderr)
        return lib_code.getvalue(), app_code.getvalue()


usage = """
  usage: %s file_name [module_name]
"""


def main():
    if len(sys.argv) < 2:
        print(usage % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    file_name = os.path.abspath(sys.argv[1])
    if not os.path.isfile(file_name):
        print("File not found %s" % file_name, file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) > 2:
        module_name = sys.argv[2]
    else:
        module_name = None
    print(translate(file_name, module_name), end="")


if __name__ == "__main__":
    main()
