#!/usr/bin/env python


from __future__ import absolute_import
from __future__ import print_function
import sys
import shutil
import re
import os
from os.path import join, basename, abspath, split, isfile, isdir
from hashlib import md5
from optparse import OptionParser
from six.moves import cStringIO

from svgui.pyjs import pyjs


usage = """
  usage: %prog [options] <application module name or path>

This is the command line builder for the pyjamas project, which can
be used to build Ajax applications from Python.
For more information, see the website at http://pyjs.org/
"""

# GWT1.2 Impl  | GWT1.2 Output         | Pyjamas 0.2 Platform | Pyjamas 0.2 Output
# -------------+-----------------------+----------------------+----------------------
# IE6          | ie6                   | IE6                  | ie6
# Opera        | opera                 | Opera                | opera
# Safari       | safari                | Safari               | safari
# --           | gecko1_8              | Mozilla              | mozilla
# --           | gecko                 | OldMoz               | oldmoz
# Standard     | all                   | (default code)       | all
# Mozilla      | gecko1_8, gecko       | --                   | --
# Old          | safari, gecko, opera  | --                   | --

version = "%prog pyjamas version 2006-08-19"

# these names in lowercase need match the strings
# returned by "provider$user.agent" in order to be selected corretly
app_platforms = ['IE6', 'Opera', 'OldMoz', 'Safari', 'Mozilla']

# usually defaults to e.g. /usr/share/pyjamas
_data_dir = os.path.join(pyjs.prefix, "share/pyjamas")


# .cache.html files produces look like this
CACHE_HTML_PAT = re.compile(r'^[a-z]*.[0-9a-f]{32}\.cache\.html$')

# ok these are the three "default" library directories, containing
# the builtins (str, List, Dict, ord, round, len, range etc.)
# the main pyjamas libraries (pyjamas.ui, pyjamas.Window etc.)
# and the contributed addons

for p in ["library/builtins",
          "library",
          "addons"]:
    p = os.path.join(_data_dir, p)
    if os.path.isdir(p):
        pyjs.path.append(p)


def read_boilerplate(data_dir, filename):
    return open(join(data_dir, "builder/boilerplate", filename)).read()


def copy_boilerplate(data_dir, filename, output_dir):
    filename = join(data_dir, "builder/boilerplate", filename)
    shutil.copy(filename, output_dir)


# taken and modified from python2.4
def copytree_exists(src, dst, symlinks=False):
    if not os.path.exists(src):
        return

    names = os.listdir(src)
    try:
        os.mkdir(dst)
    except Exception:
        pass

    errors = []
    for name in names:
        if name.startswith('CVS'):
            continue
        if name.startswith('.git'):
            continue
        if name.startswith('.svn'):
            continue

        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif isdir(srcname):
                copytree_exists(srcname, dstname, symlinks)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, why))
    if errors:
        print(errors)


def check_html_file(source_file, dest_path):
    """ Checks if a base HTML-file is available in the PyJamas
        output directory.
        If the HTML-file isn't available, it will be created.

        If a CSS-file with the same name is available
        in the output directory, a reference to this CSS-file
        is included.

        If no CSS-file is found, this function will look for a special
        CSS-file in the output directory, with the name
        "pyjamas_default.css", and if found it will be referenced
        in the generated HTML-file.

        [thank you to stef mientki for contributing this function]
    """

    base_html = """\
<html>
    <!-- auto-generated html - you should consider editing and
         adapting this to suit your requirements
     -->
    <head>
      <meta name="pygwt:module" content="%(modulename)s">
      %(css)s
      <title>%(title)s</title>
    </head>
    <body bgcolor="white">
      <script language="javascript" src="pygwt.js"></script>
    </body>
</html>
"""

    filename = os.path.split(source_file)[1]
    mod_name = os.path.splitext(filename)[0]
    file_name = os.path.join(dest_path, mod_name + '.html')

    # if html file in output directory exists, leave it alone.
    if os.path.exists(file_name):
        return 0

    if os.path.exists(os.path.join(dest_path, mod_name + '.css')):
        css = "<link rel='stylesheet' href='" + mod_name + ".css'>"
    elif os.path.exists(os.path.join(dest_path, 'pyjamas_default.css')):
        css = "<link rel='stylesheet' href='pyjamas_default.css'>"

    else:
        css = ''

    title = 'PyJamas Auto-Generated HTML file ' + mod_name

    base_html = base_html % {'modulename': mod_name, 'title': title, 'css': css}

    fh = open(file_name, 'w')
    fh.write(base_html)
    fh.close()

    return 1


def build(app_name, output, js_includes=(), debug=False, dynamic=0,
          data_dir=None, cache_buster=False, optimize=False):

    # make sure the output directory is always created in the current working
    # directory or at the place given if it is an absolute path.
    output = os.path.abspath(output)
    msg = "Building '%(app_name)s' to output directory '%(output)s'" % locals()
    if debug:
        msg += " with debugging statements"
    print(msg)

    # check the output directory
    if os.path.exists(output) and not os.path.isdir(output):
        print("Output destination %s exists and is not a directory" % output, file=sys.stderr)
        return
    if not os.path.isdir(output):
        try:
            print("Creating output directory")
            os.mkdir(output)
        except OSError as e:
            print("Exception creating output directory %s: %s" % (output, e), file=sys.stderr)

    # public dir
    for p in pyjs.path:
        pub_dir = join(p, 'public')
        if isdir(pub_dir):
            print("Copying: public directory of library %r" % p)
            copytree_exists(pub_dir, output)

    # AppName.html - can be in current or public directory
    html_input_filename = app_name + ".html"
    html_output_filename = join(output, basename(html_input_filename))
    if os.path.isfile(html_input_filename):
        if not os.path.isfile(html_output_filename) or \
               os.path.getmtime(html_input_filename) > \
               os.path.getmtime(html_output_filename):
            try:
                shutil.copy(html_input_filename, html_output_filename)
            except Exception:
                print("Warning: Missing module HTML file %s" % html_input_filename, file=sys.stderr)

            print("Copying: %(html_input_filename)s" % locals())

    if check_html_file(html_input_filename, output):
        print("Warning: Module HTML file %s has been auto-generated" % html_input_filename, file=sys.stderr)

    # pygwt.js

    print("Copying: pygwt.js")

    pygwt_js_template = read_boilerplate(data_dir, "pygwt.js")
    pygwt_js_output = open(join(output, "pygwt.js"), "w")

    print(pygwt_js_template, file=pygwt_js_output)

    pygwt_js_output.close()

    # Images

    print("Copying: Images and History")
    copy_boilerplate(data_dir, "corner_dialog_topleft_black.png", output)
    copy_boilerplate(data_dir, "corner_dialog_topright_black.png", output)
    copy_boilerplate(data_dir, "corner_dialog_bottomright_black.png", output)
    copy_boilerplate(data_dir, "corner_dialog_bottomleft_black.png", output)
    copy_boilerplate(data_dir, "corner_dialog_edge_black.png", output)
    copy_boilerplate(data_dir, "corner_dialog_topleft.png", output)
    copy_boilerplate(data_dir, "corner_dialog_topright.png", output)
    copy_boilerplate(data_dir, "corner_dialog_bottomright.png", output)
    copy_boilerplate(data_dir, "corner_dialog_bottomleft.png", output)
    copy_boilerplate(data_dir, "corner_dialog_edge.png", output)
    copy_boilerplate(data_dir, "tree_closed.gif", output)
    copy_boilerplate(data_dir, "tree_open.gif", output)
    copy_boilerplate(data_dir, "tree_white.gif", output)
    copy_boilerplate(data_dir, "history.html", output)

    # all.cache.html
    app_files = generateAppFiles(data_dir, js_includes, app_name, debug,
                                 output, dynamic, cache_buster, optimize)

    # AppName.nocache.html

    print("Creating: %(app_name)s.nocache.html" % locals())

    home_nocache_html_template = read_boilerplate(data_dir, "home.nocache.html")
    home_nocache_html_output = open(join(output, app_name + ".nocache.html"),
                                    "w")

    # the selector templ is added to the selectScript function
    select_tmpl = """O(["true","%s"],"%s");"""
    script_selectors = cStringIO()

    for platform, file_prefix in app_files:
        print(select_tmpl % (platform, file_prefix), file=script_selectors)

    print(
        home_nocache_html_template % dict(
            app_name=app_name,
            script_selectors=script_selectors.getvalue(),
        ), file=home_nocache_html_output)

    home_nocache_html_output.close()

    print("Done. You can run your app by opening '%(html_output_filename)s' in a browser" % locals())


def generateAppFiles(data_dir, js_includes, app_name, debug, output, dynamic,
                     cache_buster, optimize):

    all_cache_html_template = read_boilerplate(data_dir, "all.cache.html")
    mod_cache_html_template = read_boilerplate(data_dir, "mod.cache.html")

    # clean out the old ones first
    for name in os.listdir(output):
        if CACHE_HTML_PAT.match(name):
            p = join(output, name)
            print("Deleting existing app file %s" % p)
            os.unlink(p)

    app_files = []
    parser = pyjs.PlatformParser("platform")
    app_headers = ''
    scripts = ['<script type="text/javascript" src="%s"></script>' %
               script for script in js_includes]
    app_body = '\n'.join(scripts)

    mod_code = {}
    mod_libs = {}
    modules = {}
    app_libs = {}
    early_app_libs = {}
    app_code = {}
    overrides = {}
    pover = {}
    app_modnames = {}
    mod_levels = {}

    # First, generate all the code.
    # Second, (dynamic only), post-analyse the places where modules
    # haven't changed
    # Third, write everything out.

    for platform in app_platforms:

        mod_code[platform] = {}
        mod_libs[platform] = {}
        modules[platform] = []
        pover[platform] = {}
        app_libs[platform] = ''
        early_app_libs[platform] = ''
        app_code[platform] = {}
        app_modnames[platform] = {}

        # Application.Platform.cache.html

        parser.setPlatform(platform)
        app_translator = pyjs.AppTranslator(
            parser=parser, dynamic=dynamic, optimize=optimize)
        early_app_libs[platform], appcode = \
            app_translator.translate(None, is_app=False,
                                     debug=debug,
                                     library_modules=['dynamicajax.js',
                                                      '_pyjs.js', 'sys',
                                                      'pyjslib'])
        pover[platform].update(app_translator.overrides.items())
        for mname, name in app_translator.overrides.items():
            pd = overrides.setdefault(mname, {})
            pd[platform] = name

        print(appcode)
        # mod_code[platform][app_name] = appcode

        # platform.Module.cache.js

        modules_done = ['pyjslib', 'sys', '_pyjs.js']
        # modules_to_do = [app_name] + app_translator.library_modules
        modules_to_do = [app_name] + app_translator.library_modules

        dependencies = {}

        deps = map(pyjs.strip_py, modules_to_do)
        for d in deps:
            sublist = add_subdeps(dependencies, d)
            modules_to_do += sublist
        deps = uniquify(deps)
        # dependencies[app_name] = deps

        modules[platform] = modules_done + modules_to_do

        while modules_to_do:

            # print "modules to do", modules_to_do

            mn = modules_to_do.pop()
            mod_name = pyjs.strip_py(mn)

            if mod_name in modules_done:
                continue

            modules_done.append(mod_name)

            mod_cache_name = "%s.%s.cache.js" % (platform.lower(), mod_name)

            parser.setPlatform(platform)
            mod_translator = pyjs.AppTranslator(parser=parser, optimize=optimize)
            mod_libs[platform][mod_name], mod_code[platform][mod_name] = \
                mod_translator.translate(mod_name,
                                         is_app=False,
                                         debug=debug)
            pover[platform].update(mod_translator.overrides.items())
            for mname, name in mod_translator.overrides.items():
                pd = overrides.setdefault(mname, {})
                pd[platform] = name

            mods = mod_translator.library_modules
            modules_to_do += mods
            modules[platform] += mods

            deps = map(pyjs.strip_py, mods)
            sd = subdeps(mod_name)
            if len(sd) > 1:
                deps += sd[:-1]
            while mod_name in deps:
                deps.remove(mod_name)

            # print
            # print
            # print "modname preadd:", mod_name, deps
            # print
            # print
            for d in deps:
                sublist = add_subdeps(dependencies, d)
                modules_to_do += sublist
            modules_to_do += add_subdeps(dependencies, mod_name)
            # print "modname:", mod_name, deps
            deps = uniquify(deps)
            # print "modname:", mod_name, deps
            dependencies[mod_name] = deps

        # work out the dependency ordering of the modules

        mod_levels[platform] = make_deps(None, dependencies, modules_done)

    # now write everything out

    for platform in app_platforms:

        early_app_libs_ = early_app_libs[platform]
        app_libs_ = app_libs[platform]
        app_code_ = app_code[platform]
        # modules_ = filter_mods(app_name, modules[platform])
        mods = flattenlist(mod_levels[platform])
        mods.reverse()
        modules_ = filter_mods(None, mods)

        for mod_name in modules_:

            mod_code_ = mod_code[platform][mod_name]

            mod_name = pyjs.strip_py(mod_name)

            override_name = "%s.%s" % (platform.lower(), mod_name)
            if override_name in pover[platform]:
                mod_cache_name = "%s.cache.js" % (override_name)
            else:
                mod_cache_name = "%s.cache.js" % (mod_name)

            print("Creating: " + mod_cache_name)

            modlevels = make_deps(None, dependencies, dependencies[mod_name])

            modnames = []

            for md in modlevels:
                mnames = map(lambda x: "'%s'" % x, md)
                mnames = "new pyjslib.List([\n\t\t\t%s])" % ',\n\t\t\t'.join(mnames)
                modnames.append(mnames)

            modnames.reverse()
            modnames = "new pyjslib.List([\n\t\t%s\n\t])" % ',\n\t\t'.join(modnames)

            # convert the overrides

            overnames = map(lambda x: "'%s': '%s'" % x, pover[platform].items())
            overnames = "new pyjslib.Dict({\n\t\t%s\n\t})" % ',\n\t\t'.join(overnames)

            if dynamic:
                mod_cache_html_output = open(join(output, mod_cache_name), "w")
            else:
                mod_cache_html_output = cStringIO()

            print(mod_cache_html_template % dict(
                mod_name=mod_name,
                app_name=app_name,
                modnames=modnames,
                overrides=overnames,
                mod_libs=mod_libs[platform][mod_name],
                dynamic=dynamic,
                mod_code=mod_code_,
            ), file=mod_cache_html_output)

            if dynamic:
                mod_cache_html_output.close()
            else:
                mod_cache_html_output.seek(0)
                app_libs_ += mod_cache_html_output.read()

        # write out the dependency ordering of the modules

        app_modnames = []

        for md in mod_levels[platform]:
            mnames = map(lambda x: "'%s'" % x, md)
            mnames = "new pyjslib.List([\n\t\t\t%s])" % ',\n\t\t\t'.join(mnames)
            app_modnames.append(mnames)

        app_modnames.reverse()
        app_modnames = "new pyjslib.List([\n\t\t%s\n\t])" % ',\n\t\t'.join(app_modnames)

        # convert the overrides

        overnames = map(lambda x: "'%s': '%s'" % x, pover[platform].items())
        overnames = "new pyjslib.Dict({\n\t\t%s\n\t})" % ',\n\t\t'.join(overnames)

        # print "platform names", platform, overnames
        # print pover

        # now write app.allcache including dependency-ordered list of
        # library modules

        file_contents = all_cache_html_template % dict(
            app_name=app_name,
            early_app_libs=early_app_libs_,
            app_libs=app_libs_,
            app_code=app_code_,
            app_body=app_body,
            overrides=overnames,
            platform=platform.lower(),
            dynamic=dynamic,
            app_modnames=app_modnames,
            app_headers=app_headers
        )
        if cache_buster:
            digest = md5.new(file_contents).hexdigest()
            file_name = "%s.%s.%s" % (platform.lower(), app_name, digest)
        else:
            file_name = "%s.%s" % (platform.lower(), app_name)
        file_name += ".cache.html"
        out_path = join(output, file_name)
        out_file = open(out_path, 'w')
        out_file.write(file_contents)
        out_file.close()
        app_files.append((platform.lower(), file_name))
        print("Created app file %s:%s: %s" % (
            app_name, platform, out_path))

    return app_files


def flattenlist(ll):
    res = []
    for l in ll:
        res += l
    return res


def subdeps(m):
    """
    creates sub-dependencies e.g. pyjamas.ui.Widget
    creates pyjamas.ui.Widget, pyjamas.ui and pyjamas.
    """
    d = []
    m = m.split(".")
    for i in range(0, len(m)):
        d.append('.'.join(m[:i+1]))
    return d


def add_subdeps(deps, mod_name):
    sd = subdeps(mod_name)
    if len(sd) == 1:
        return []
    # print "subdeps", mod_name, sd
    # print "deps", deps
    res = []
    for i in range(0, len(sd)-1):
        parent = sd[i]
        child = sd[i+1]
        k = deps.get(child, [])
        k.append(parent)
        deps[child] = k
        if parent not in res:
            res.append(parent)
    # print deps
    return res


def uniquify(md):
    """
    makes unique and preserves list order
    """
    res = []
    for m in md:
        if m not in res:
            res.append(m)
    return res


def filter_mods(app_name, md):
    while 'sys' in md:
        md.remove('sys')
    while 'pyjslib' in md:
        md.remove('pyjslib')
    while app_name in md:
        md.remove(app_name)
    md = filter(lambda x: not x.endswith('.js'), md)
    md = map(pyjs.strip_py, md)

    return uniquify(md)


def filter_deps(app_name, deps):

    res = {}
    for (k, l) in deps.items():
        mods = filter_mods(k, l)
        while k in mods:
            mods.remove(k)
        res[k] = mods
    return res


def has_nodeps(mod, deps):
    if mod not in deps or not deps[mod]:
        return True
    return False


def nodeps_list(mod_list, deps):
    res = []
    for mod in mod_list:
        if has_nodeps(mod, deps):
            res.append(mod)
    return res

# this function takes a dictionary of dependent modules and
# creates a list of lists.  the first list will be modules
# that have no dependencies; the second list will be those
# modules that have the first list as dependencies; the
# third will be those modules that have the first and second...
# etc.


def make_deps(app_name, deps, mod_list):
    print("Calculating Dependencies ...")
    mod_list = filter_mods(app_name, mod_list)
    deps = filter_deps(app_name, deps)

    if not mod_list:
        return []

    # print mod_list
    # print deps

    ordered_deps = []
    last_len = -1
    while deps:
        l_deps = len(deps)
        # print l_deps
        if l_deps == last_len:
            for m, dl in deps.items():
                for d in dl:
                    if m in deps.get(d, []):
                        raise Exception('Circular Imports found: \n%s %s -> %s %s'
                                        % (m, dl, d, deps[d]))
            # raise Exception('Could not calculate dependencies: \n%s' % deps)
            break
        last_len = l_deps
        # print "modlist", mod_list
        nodeps = nodeps_list(mod_list, deps)
        # print "nodeps", nodeps
        mod_list = filter(lambda x: x not in nodeps, mod_list)
        newdeps = {}
        for k in deps.keys():
            depslist = deps[k]
            depslist = filter(lambda x: x not in nodeps, depslist)
            if depslist:
                newdeps[k] = depslist
        # print "newdeps", newdeps
        deps = newdeps
        ordered_deps.append(nodeps)
        # time.sleep(0)

    if mod_list:
        ordered_deps.append(mod_list)  # last dependencies - usually the app(s)

    ordered_deps.reverse()

    return ordered_deps


def main():
    global app_platforms

    parser = OptionParser(usage=usage, version=version)
    parser.add_option(
        "-o",
        "--output",
        dest="output",
        help="directory to which the webapp should be written"
    )
    parser.add_option(
        "-j",
        "--include-js",
        dest="js_includes",
        action="append",
        help="javascripts to load into the same frame as the rest of the script"
    )
    parser.add_option(
        "-I",
        "--library_dir",
        dest="library_dirs",
        action="append",
        help="additional paths appended to PYJSPATH"
    )
    parser.add_option(
        "-D",
        "--data_dir",
        dest="data_dir",
        help="path for data directory"
    )
    parser.add_option(
        "-m",
        "--dynamic-modules",
        action="store_true",
        dest="dynamic",
        default=False,
        help="Split output into separate dynamically-loaded modules (experimental)"
    )
    parser.add_option(
        "-P",
        "--platforms",
        dest="platforms",
        help="platforms to build for, comma-separated"
    )
    parser.add_option(
        "-d",
        "--debug",
        action="store_true",
        dest="debug"
    )
    parser.add_option(
        "-O",
        "--optimize",
        action="store_true",
        dest="optimize",
        default=False,
        help="Optimize generated code (removes all print statements)",
    )
    parser.add_option(
        "-c",
        "--cache_buster",
        action="store_true",
        dest="cache_buster",
        help="Enable browser cache-busting (MD5 hash added to output filenames)"
    )

    parser.set_defaults(output="output", js_includes=[], library_dirs=[],
                        platforms=(','.join(app_platforms)),
                        data_dir=os.path.join(sys.prefix, "share/pyjamas"),
                        dynamic=False,
                        cache_buster=False,
                        debug=False)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    data_dir = abspath(options.data_dir)

    app_path = args[0]
    if app_path.endswith('.py'):
        app_path = abspath(app_path)
        if not isfile(app_path):
            parser.error("Application file not found %r" % app_path)
        app_path, app_name = split(app_path)
        app_name = app_name[:-3]
        pyjs.path.append(app_path)
    elif os.path.sep in app_path:
        parser.error("Not a valid module declaration %r" % app_path)
    else:
        app_name = app_path

    for d in options.library_dirs:
        pyjs.path.append(abspath(d))

    if options.platforms:
        app_platforms = options.platforms.split(',')

    # this is mostly for getting boilerplate stuff
    data_dir = os.path.abspath(options.data_dir)

    build(app_name, options.output, options.js_includes,
          options.debug, options.dynamic and 1 or 0, data_dir,
          options.cache_buster, options.optimize)


if __name__ == "__main__":
    main()
