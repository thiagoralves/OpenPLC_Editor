#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
# Copyright (C) 2021: Edouard TISSERANT
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
import os
import shutil
import hashlib
import shlex
import time

import wx

from lxml import etree
from lxml.etree import XSLTApplyError

import util.paths as paths
from POULibrary import POULibrary
from docutil import open_svg, get_inkscape_path

from util.ProcessLogger import ProcessLogger
from runtime.typemapping import DebugTypesSize
import targets
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor
from XSLTransform import XSLTransform
from svghmi.i18n import EtreeToMessages, SaveCatalog, ReadTranslations,\
                        MatchTranslations, TranslationToEtree, open_pofile,\
                        GetPoFiles
from svghmi.hmi_tree import HMI_TYPES, HMITreeNode, SPECIAL_NODES 
from svghmi.ui import SVGHMI_UI
from svghmi.fonts import GetFontTypeAndFamilyName, GetCSSFontFaceFromFontFile


ScriptDirectory = paths.AbsDir(__file__)


# module scope for HMITree root
# so that CTN can use HMITree deduced in Library
# note: this only works because library's Generate_C is
#       systematicaly invoked before CTN's CTNGenerate_C

hmi_tree_root = None

on_hmitree_update = None

maxConnectionsTotal = 0

class SVGHMILibrary(POULibrary):
    def GetLibraryPath(self):
         return paths.AbsNeighbourFile(__file__, "pous.xml")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):
        global hmi_tree_root, on_hmitree_update, maxConnectionsTotal

        maxConnectionsTotal = 0

        already_found_watchdog = False
        found_SVGHMI_instance = False
        for CTNChild in self.GetCTR().IterChildren():
            if isinstance(CTNChild, SVGHMI):
                found_SVGHMI_instance = True
                # collect maximum connection total for all svghmi nodes
                maxConnectionsTotal += CTNChild.GetParamsAttributes("SVGHMI.MaxConnections")["value"]

                # spot watchdog abuse
                if CTNChild.GetParamsAttributes("SVGHMI.EnableWatchdog")["value"]:
                    if already_found_watchdog:
                        self.FatalError("SVGHMI: Only one watchdog enabled HMI allowed")
                    already_found_watchdog = True

        if not found_SVGHMI_instance:
            self.FatalError("SVGHMI : Library is selected but not used. Please either deselect it in project config or add a SVGHMI node to project.")


        """
        PLC Instance Tree:
          prog0
           +->v1 HMI_INT
           +->v2 HMI_INT
           +->fb0 (type mhoo)
           |   +->va HMI_NODE
           |   +->v3 HMI_INT
           |   +->v4 HMI_INT
           |
           +->fb1 (type mhoo)
           |   +->va HMI_NODE
           |   +->v3 HMI_INT
           |   +->v4 HMI_INT
           |
           +->fb2
               +->v5 HMI_IN

        HMI tree:
          hmi0
           +->v1
           +->v2
           +->fb0 class:va
           |   +-> v3
           |   +-> v4
           |
           +->fb1 class:va
           |   +-> v3
           |   +-> v4
           |
           +->v5

        """

        # Filter known HMI types
        hmi_types_instances = [v for v in varlist if v["derived"] in HMI_TYPES]

        hmi_tree_root = None

        # take first HMI_NODE (placed as special node), make it root
        for i,v in enumerate(hmi_types_instances):
            path = v["IEC_path"].split(".")
            derived = v["derived"]
            if derived == "HMI_NODE":
                hmi_tree_root = HMITreeNode(path, "", derived, v["type"], v["vartype"], v["C_path"])
                hmi_types_instances.pop(i)
                break

        # deduce HMI tree from PLC HMI_* instances
        for v in hmi_types_instances:
            path = v["IEC_path"].split(".")
            # ignores variables starting with _TMP_
            if path[-1].startswith("_TMP_"):
                continue
            vartype = v["vartype"]
            # ignores external variables
            if vartype == "EXT":
                continue
            derived = v["derived"]
            kwargs={}
            if derived == "HMI_NODE":
                # TODO : make problem if HMI_NODE used in CONFIG or RESOURCE
                name = path[-2]
                kwargs['hmiclass'] = path[-1]
            else:
                name = path[-1]
            new_node = HMITreeNode(path, name, derived, v["type"], vartype, v["C_path"], **kwargs)
            placement_result = hmi_tree_root.place_node(new_node)
            if placement_result is not None:
                cause, problematic_node = placement_result
                if cause == "Non_Unique":
                    message = _("HMI tree nodes paths are not unique.\nConflicting variable: {} {}").format(
                        ".".join(problematic_node.path),
                        ".".join(new_node.path))

                    last_FB = None 
                    for _v in varlist:
                        if _v["vartype"] == "FB":
                            last_FB = _v 
                        if _v["C_path"] == problematic_node:
                            break
                    if last_FB is not None:
                        failing_parent = last_FB["type"]
                        message += "\n"
                        message += _("Solution: Add HMI_NODE at beginning of {}").format(failing_parent)

                elif cause in ["Late_HMI_NODE", "Duplicate_HMI_NODE"]:
                    cause, problematic_node = placement_result
                    message = _("There must be only one occurrence of HMI_NODE before any HMI_* variable in POU.\nConflicting variable: {} {}").format(
                        ".".join(problematic_node.path),
                        ".".join(new_node.path))

                self.FatalError("SVGHMI : " + message)

        if on_hmitree_update is not None:
            on_hmitree_update(hmi_tree_root)

        variable_decl_array = []
        extern_variables_declarations = []
        buf_index = 0
        item_count = 0
        found_heartbeat = False

        hearbeat_IEC_path = ['CONFIG', 'HEARTBEAT']

        for node in hmi_tree_root.traverse():
            if not found_heartbeat and node.path == hearbeat_IEC_path:
                hmi_tree_hearbeat_index = item_count
                found_heartbeat = True
                extern_variables_declarations += [
                    "#define heartbeat_index "+str(hmi_tree_hearbeat_index)
                ]
            if hasattr(node, "iectype"):
                sz = DebugTypesSize.get(node.iectype, 0)
                variable_decl_array += [
                    "HMITREE_ITEM_INITIALIZER(" + node.cpath + ", " + node.iectype + {
                        "EXT": "_P_ENUM",
                        "IN":  "_P_ENUM",
                        "MEM": "_O_ENUM",
                        "OUT": "_O_ENUM",
                        "VAR": "_ENUM"
                    }[node.vartype] + ", " +
                    str(buf_index) + ")"]
                buf_index += sz
                item_count += 1
                if len(node.path) == 1:
                    extern_variables_declarations += [
                        "extern __IEC_" + node.iectype + "_" +
                        "t" if node.vartype is "VAR" else "p"
                        + node.cpath + ";"]

        assert(found_heartbeat)

        # TODO : filter only requiered external declarations
        for v in varlist:
            if v["C_path"].find('.') < 0:
                extern_variables_declarations += [
                    "extern %(type)s %(C_path)s;" % v]

        # TODO check if programs need to be declared separately
        # "programs_declarations": "\n".join(["extern %(type)s %(C_path)s;" %
        #                                     p for p in self._ProgramList]),

        # C code to observe/access HMI tree variables
        svghmi_c_filepath = paths.AbsNeighbourFile(__file__, "svghmi.c")
        svghmi_c_file = open(svghmi_c_filepath, 'r')
        svghmi_c_code = svghmi_c_file.read()
        svghmi_c_file.close()
        svghmi_c_code = svghmi_c_code % {
            "variable_decl_array": ",\n".join(variable_decl_array),
            "extern_variables_declarations": "\n".join(extern_variables_declarations),
            "buffer_size": buf_index,
            "item_count": item_count,
            "var_access_code": targets.GetCode("var_access.c"),
            "PLC_ticktime": self.GetCTR().GetTicktime(),
            "hmi_hash_ints": ",".join(map(str,hmi_tree_root.hash())),
            "max_connections": maxConnectionsTotal
            }

        gen_svghmi_c_path = os.path.join(buildpath, "svghmi.c")
        gen_svghmi_c = open(gen_svghmi_c_path, 'w')
        gen_svghmi_c.write(svghmi_c_code)
        gen_svghmi_c.close()

        # Python based WebSocket HMITree Server
        svghmiserverfile = open(paths.AbsNeighbourFile(__file__, "svghmi_server.py"), 'r')
        svghmiservercode = svghmiserverfile.read()
        svghmiserverfile.close()

        runtimefile_path = os.path.join(buildpath, "runtime_00_svghmi.py")
        runtimefile = open(runtimefile_path, 'w')
        runtimefile.write(svghmiservercode)
        runtimefile.close()

        # Backup HMI Tree in XML form so that it can be loaded without building
        hmitree_backup_path = os.path.join(buildpath, "hmitree.xml")
        hmitree_backup_file = open(hmitree_backup_path, 'wb')
        hmitree_backup_file.write(etree.tostring(hmi_tree_root.etree()))
        hmitree_backup_file.close()

        return ((["svghmi"], [(gen_svghmi_c_path, IECCFLAGS)], True), "",
                ("runtime_00_svghmi.py", open(runtimefile_path, "rb")))
                #         ^
                # note the double zero after "runtime_", 
                # to ensure placement before other CTN generated code in execution order

    def GlobalInstances(self):
        """ Adds HMI tree root and hearbeat to PLC Configuration's globals """
        return [(name, iec_type, "") for name, iec_type in SPECIAL_NODES]



def Register_SVGHMI_UI_for_HMI_tree_updates(ref):
    global on_hmitree_update
    def HMITreeUpdate(_hmi_tree_root):
        obj = ref()
        if obj is not None:
            obj.HMITreeUpdate(_hmi_tree_root)

    on_hmitree_update = HMITreeUpdate


class SVGHMIEditor(ConfTreeNodeEditor):
    CONFNODEEDITOR_TABS = [
        (_("HMI Tree"), "CreateSVGHMI_UI")]

    def __init__(self, parent, controler, window):
        ConfTreeNodeEditor.__init__(self, parent, controler, window)
        self.Controler = controler

    def CreateSVGHMI_UI(self, parent):
        global hmi_tree_root

        if hmi_tree_root is None:
            buildpath = self.Controler.GetCTRoot()._getBuildPath()
            hmitree_backup_path = os.path.join(buildpath, "hmitree.xml")
            if os.path.exists(hmitree_backup_path):
                hmitree_backup_file = open(hmitree_backup_path, 'rb')
                hmi_tree_root = HMITreeNode.from_etree(etree.parse(hmitree_backup_file).getroot())

        ret = SVGHMI_UI(parent, self.Controler, Register_SVGHMI_UI_for_HMI_tree_updates)

        on_hmitree_update(hmi_tree_root)

        return ret

if wx.Platform == '__WXMSW__':
    default_cmds={
        "launch":"cmd.exe /c 'start msedge {url}'",
        "watchdog":"cmd.exe /k 'echo watchdog for {url} !'"}
else:
    default_cmds={
        "launch":"chromium {url}",
        "watchdog":"echo Watchdog for {name} !"}

class SVGHMI(object):
    XSD = """<?xml version="1.0" encoding="utf-8" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="SVGHMI">
        <xsd:complexType>
          <xsd:attribute name="OnStart" type="xsd:string" use="optional" default="%(launch)s"/>
          <xsd:attribute name="OnStop" type="xsd:string" use="optional" default=""/>
          <xsd:attribute name="OnWatchdog" type="xsd:string" use="optional" default="%(watchdog)s"/>
          <xsd:attribute name="EnableWatchdog" type="xsd:boolean" use="optional" default="false"/>
          <xsd:attribute name="WatchdogInitial" use="optional" default="30">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="2"/>
                    <xsd:maxInclusive value="600"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="WatchdogInterval" use="optional" default="5">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="2"/>
                    <xsd:maxInclusive value="60"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
          <xsd:attribute name="Port" type="xsd:integer" use="optional" default="8008"/>
          <xsd:attribute name="Interface" type="xsd:string" use="optional" default="localhost"/>
          <xsd:attribute name="Path" type="xsd:string" use="optional" default="{name}"/>
          <xsd:attribute name="MaxConnections" use="optional" default="16">
            <xsd:simpleType>
                <xsd:restriction base="xsd:integer">
                    <xsd:minInclusive value="1"/>
                    <xsd:maxInclusive value="1024"/>
                </xsd:restriction>
            </xsd:simpleType>
          </xsd:attribute>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """%default_cmds

    EditorType = SVGHMIEditor

    ConfNodeMethods = [
        {
            "bitmap":    "ImportSVG",
            "name":    _("Import SVG"),
            "tooltip": _("Import SVG"),
            "method":   "_ImportSVG"
        },
        {
            "bitmap":    "EditSVG",
            "name":    _("Inkscape"),
            "tooltip": _("Edit HMI"),
            "method":   "_StartInkscape"
        },
        {
            "bitmap":    "OpenPOT",
            "name":    _("New lang"),
            "tooltip": _("Open non translated message catalog (POT) to start new language"),
            "method":   "_OpenPOT"
        },
        {
            "bitmap":    "EditPO",
            "name":    _("Edit lang"),
            "tooltip": _("Edit existing message catalog (PO) for specific language"),
            "method":   "_EditPO"
        },
        {
            "bitmap":    "AddFont",
            "name":    _("Add Font"),
            "tooltip": _("Add TTF, OTF or WOFF font to be embedded in HMI"),
            "method":   "_AddFont"
        },
        {
            "bitmap":    "DelFont",
            "name":    _("Delete Font"),
            "tooltip": _("Remove font previously added to HMI"),
            "method":   "_DelFont"
        },
    ]

    def _getSVGpath(self, project_path=None):
        if project_path is None:
            project_path = self.CTNPath()
        return os.path.join(project_path, "svghmi.svg")

    def _getPOTpath(self, project_path=None):
        if project_path is None:
            project_path = self.CTNPath()
        return os.path.join(project_path, "messages.pot")

    def OnCTNSave(self, from_project_path=None):
        if from_project_path is not None:
            shutil.copyfile(self._getSVGpath(from_project_path),
                            self._getSVGpath())

            potpath = self._getPOTpath(from_project_path)
            if os.path.isfile(potpath):
                shutil.copyfile(potpath, self._getPOTpath())
                # copy .PO files
                for _name, pofile in GetPoFiles(from_project_path):
                    shutil.copy(pofile, self.CTNPath())
        return True

    def GetSVGGeometry(self):
        self.ProgressStart("inkscape", "collecting SVG geometry (Inkscape)")
        # invoke inskscape -S, csv-parse output, produce elements
        InkscapeGeomColumns = ["Id", "x", "y", "w", "h"]

        inkpath = get_inkscape_path()

        if inkpath is None:
            self.FatalError("SVGHMI: inkscape is not installed.")

        svgpath = self._getSVGpath()
        status, result, _err_result = ProcessLogger(self.GetCTRoot().logger,
                                                     '"' + inkpath + '" -S "' + svgpath + '"',
                                                     no_stdout=True,
                                                     no_stderr=True).spin()
        if status != 0:
            self.FatalError("SVGHMI: inkscape couldn't extract geometry from given SVG.")

        res = []
        for line in result.split():
            strippedline = line.strip()
            attrs = dict(
                zip(InkscapeGeomColumns, line.strip().split(',')))

            res.append(etree.Element("bbox", **attrs))

        self.ProgressEnd("inkscape")
        return res

    def GetHMITree(self):
        global hmi_tree_root
        self.ProgressStart("hmitree", "getting HMI tree")
        res = [hmi_tree_root.etree(add_hash=True)]
        self.ProgressEnd("hmitree")
        return res

    def GetTranslations(self, _context, msgs):
        self.ProgressStart("i18n", "getting Translations")
        messages = EtreeToMessages(msgs)

        if len(messages) == 0:
            self.ProgressEnd("i18n")
            return

        SaveCatalog(self._getPOTpath(), messages)

        translations = ReadTranslations(self.CTNPath())
            
        langs,translated_messages = MatchTranslations(translations, messages, 
            errcallback=self.GetCTRoot().logger.write_warning)

        ret = TranslationToEtree(langs,translated_messages)

        self.ProgressEnd("i18n")

        return ret

    def GetFontsFiles(self):
        project_path = self.CTNPath()
        fontdir = os.path.join(project_path, "fonts") 
        if os.path.isdir(fontdir):
            return [os.path.join(fontdir,f) for f in sorted(os.listdir(fontdir))]
        return []

    def GetFonts(self, _context):
        css_parts = []

        for fontfile in self.GetFontsFiles():
            if os.path.isfile(fontfile):
                css_parts.append(GetCSSFontFaceFromFontFile(fontfile))

        return "".join(css_parts)

    times_msgs = {}
    indent = 1
    def ProgressStart(self, k, m):
        self.times_msgs[k] = (time.time(), m)
        self.GetCTRoot().logger.write("    "*self.indent + "Start %s...\n"%m)
        self.indent = self.indent + 1

    def ProgressEnd(self, k):
        t = time.time()
        oldt, m = self.times_msgs[k]
        self.indent = self.indent - 1
        self.GetCTRoot().logger.write("    "*self.indent + "... finished in %.3fs\n"%(t - oldt))

    def get_SVGHMI_options(self):
        name = self.BaseParams.getName()
        port = self.GetParamsAttributes("SVGHMI.Port")["value"]
        interface = self.GetParamsAttributes("SVGHMI.Interface")["value"]
        path = self.GetParamsAttributes("SVGHMI.Path")["value"].format(name=name)
        if path and path[0]=='/':
            path = path[1:]
        enable_watchdog = self.GetParamsAttributes("SVGHMI.EnableWatchdog")["value"]
        url="http://"+interface+("" if port==80 else (":"+str(port))
            ) + (("/"+path) if path else ""
            ) + ("#watchdog" if enable_watchdog else "")

        return dict(
            name=name,
            port=port,
            interface=interface,
            path=path,
            enable_watchdog=enable_watchdog,
            url=url)

    def CTNGenerate_C(self, buildpath, locations):
        global hmi_tree_root

        if hmi_tree_root is None:
            self.FatalError("SVGHMI : Library is not selected. Please select it in project config.")

        location_str = "_".join(map(str, self.GetCurrentLocation()))
        svghmi_options = self.get_SVGHMI_options()

        svgfile = self._getSVGpath()

        res = ([], "", False)

        target_fname = "svghmi_"+location_str+".xhtml"

        build_path = self._getBuildPath()
        target_path = os.path.join(build_path, target_fname)
        hash_path = os.path.join(build_path, "svghmi_"+location_str+".md5")

        self.GetCTRoot().logger.write("SVGHMI:\n")

        if os.path.exists(svgfile):

            hasher = hashlib.md5()
            hmi_tree_root._hash(hasher)
            pofiles = GetPoFiles(self.CTNPath())
            filestocheck = [svgfile] + \
                           (list(zip(*pofiles)[1]) if pofiles else []) + \
                           self.GetFontsFiles()

            for filetocheck in filestocheck:
                with open(filetocheck, 'rb') as afile:
                    while True:
                        buf = afile.read(65536)
                        if len(buf) > 0:
                            hasher.update(buf)
                        else:
                            break
            digest = hasher.hexdigest()

            if os.path.exists(hash_path):
                with open(hash_path, 'rb') as digest_file:
                    last_digest = digest_file.read()
            else:
                last_digest = None
            
            if digest != last_digest:

                transform = XSLTransform(os.path.join(ScriptDirectory, "gen_index_xhtml.xslt"),
                              [("GetSVGGeometry", lambda *_ignored:self.GetSVGGeometry()),
                               ("GetHMITree", lambda *_ignored:self.GetHMITree()),
                               ("GetTranslations", self.GetTranslations),
                               ("GetFonts", self.GetFonts),
                               ("ProgressStart", lambda _ign,k,m:self.ProgressStart(str(k),str(m))),
                               ("ProgressEnd", lambda _ign,k:self.ProgressEnd(str(k)))])

                self.ProgressStart("svg", "source SVG parsing")

                # load svg as a DOM with Etree
                svgdom = etree.parse(svgfile)

                self.ProgressEnd("svg")

                # call xslt transform on Inkscape's SVG to generate XHTML
                try: 
                    self.ProgressStart("xslt", "XSLT transform")
                    result = transform.transform(
                        svgdom, instance_name=location_str)  # , profile_run=True)
                    self.ProgressEnd("xslt")
                except XSLTApplyError as e:
                    self.FatalError("SVGHMI " + svghmi_options["name"] + ": " + e.message)
                finally:
                    for entry in transform.get_error_log():
                        message = "SVGHMI: "+ entry.message + "\n" 
                        self.GetCTRoot().logger.write_warning(message)

                target_file = open(target_path, 'wb')
                result.write(target_file, encoding="utf-8")
                target_file.close()

                # print(str(result))
                # print(transform.xslt.error_log)
                # print(etree.tostring(result.xslt_profile,pretty_print=True))

                with open(hash_path, 'wb') as digest_file:
                    digest_file.write(digest)
            else:
                self.GetCTRoot().logger.write("    No changes - XSLT transformation skipped\n")

        else:
            target_file = open(target_path, 'wb')
            target_file.write("""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>SVGHMI</title>
</head>
<body>
<h1> No SVG file provided </h1>
</body>
</html>
""")
            target_file.close()

            # In case no SVG is given, watchdog is useless
            svghmi_options["enable_watchdog"] = False

        res += ((target_fname, open(target_path, "rb")),)

        svghmi_cmds = {}
        for thing in ["Start", "Stop", "Watchdog"]:
             given_command = self.GetParamsAttributes("SVGHMI.On"+thing)["value"]
             svghmi_cmds[thing] = (
                "Popen(" +
                repr(shlex.split(given_command.format(**svghmi_options))) +
                ")") if given_command else "pass # no command given"

        runtimefile_path = os.path.join(buildpath, "runtime_%s_svghmi_.py" % location_str)
        runtimefile = open(runtimefile_path, 'w')
        runtimefile.write("""
# TODO : multiple watchdog (one for each svghmi instance)
def svghmi_{location}_watchdog_trigger():
    {svghmi_cmds[Watchdog]}

max_svghmi_sessions = {maxConnections_total}

def _runtime_{location}_svghmi_start():
    global svghmi_watchdog, svghmi_servers

    srv = svghmi_servers.get("{interface}:{port}", None)
    if srv is not None:
        svghmi_root, svghmi_listener, path_list = srv
        if '{path}' in path_list:
            raise Exception("SVGHMI {name}: path {path} already used on {interface}:{port}")
    else:
        svghmi_root = Resource()
        factory = HMIWebSocketServerFactory()
        factory.setProtocolOptions(maxConnections={maxConnections})

        svghmi_root.putChild("ws", WebSocketResource(factory))

        svghmi_listener = reactor.listenTCP({port}, Site(svghmi_root), interface='{interface}')
        path_list = []
        svghmi_servers["{interface}:{port}"] = (svghmi_root, svghmi_listener, path_list)

    svghmi_root.putChild(
        '{path}',
        NoCacheFile('{xhtml}',
            defaultType='application/xhtml+xml'))

    path_list.append("{path}")

    {svghmi_cmds[Start]}

    if {enable_watchdog}:
        if svghmi_watchdog is None:
            svghmi_watchdog = Watchdog(
                {watchdog_initial},
                {watchdog_interval},
                svghmi_{location}_watchdog_trigger)
        else:
            raise Exception("SVGHMI {name}: only one watchdog allowed")


def _runtime_{location}_svghmi_stop():
    global svghmi_watchdog, svghmi_servers

    if svghmi_watchdog is not None:
        svghmi_watchdog.cancel()
        svghmi_watchdog = None

    svghmi_root, svghmi_listener, path_list = svghmi_servers["{interface}:{port}"]
    svghmi_root.delEntity('{path}')

    path_list.remove('{path}')

    if len(path_list)==0:
        svghmi_root.delEntity("ws")
        svghmi_listener.stopListening()
        svghmi_servers.pop("{interface}:{port}")

    {svghmi_cmds[Stop]}

        """.format(location=location_str,
                   xhtml=target_fname,
                   svghmi_cmds=svghmi_cmds,
                   watchdog_initial = self.GetParamsAttributes("SVGHMI.WatchdogInitial")["value"],
                   watchdog_interval = self.GetParamsAttributes("SVGHMI.WatchdogInterval")["value"],
                   maxConnections = self.GetParamsAttributes("SVGHMI.MaxConnections")["value"],
                   maxConnections_total = maxConnectionsTotal,
                   **svghmi_options
        ))

        runtimefile.close()

        res += (("runtime_%s_svghmi.py" % location_str, open(runtimefile_path, "rb")),)

        return res

    def _ImportSVG(self):
        dialog = wx.FileDialog(self.GetCTRoot().AppFrame, _("Choose a SVG file"), os.getcwd(), "",  _("SVG files (*.svg)|*.svg|All files|*.*"), wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            svgpath = dialog.GetPath()
            if os.path.isfile(svgpath):
                shutil.copy(svgpath, self._getSVGpath())
            else:
                self.GetCTRoot().logger.write_error(_("No such SVG file: %s\n") % svgpath)
        dialog.Destroy()

    def getDefaultSVG(self):
        return os.path.join(ScriptDirectory, "default.svg")

    def _StartInkscape(self):
        svgfile = self._getSVGpath()
        open_inkscape = True
        if not self.GetCTRoot().CheckProjectPathPerm():
            dialog = wx.MessageDialog(self.GetCTRoot().AppFrame,
                                      _("You don't have write permissions.\nOpen Inkscape anyway ?"),
                                      _("Open Inkscape"),
                                      wx.YES_NO | wx.ICON_QUESTION)
            open_inkscape = dialog.ShowModal() == wx.ID_YES
            dialog.Destroy()
        if open_inkscape:
            if not os.path.isfile(svgfile):
                # make a copy of default svg from source
                default = self.getDefaultSVG()
                shutil.copyfile(default, svgfile)
            open_svg(svgfile)

    def _StartPOEdit(self, POFile):
        open_poedit = True
        if not self.GetCTRoot().CheckProjectPathPerm():
            dialog = wx.MessageDialog(self.GetCTRoot().AppFrame,
                                      _("You don't have write permissions.\nOpen POEdit anyway ?"),
                                      _("Open POEdit"),
                                      wx.YES_NO | wx.ICON_QUESTION)
            open_poedit = dialog.ShowModal() == wx.ID_YES
            dialog.Destroy()
        if open_poedit:
            open_pofile(POFile)

    def _EditPO(self):
        """ Select a specific translation and edit it with POEdit """
        project_path = self.CTNPath()
        dialog = wx.FileDialog(self.GetCTRoot().AppFrame, _("Choose a PO file"), project_path, "",  _("PO files (*.po)|*.po"), wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            POFile = dialog.GetPath()
            if os.path.isfile(POFile):
                if os.path.relpath(POFile, project_path) == os.path.basename(POFile):
                    self._StartPOEdit(POFile)
                else:
                    self.GetCTRoot().logger.write_error(_("PO file misplaced: %s is not in %s\n") % (POFile,project_path))
            else:
                self.GetCTRoot().logger.write_error(_("PO file does not exist: %s\n") % POFile)
        dialog.Destroy()

    def _OpenPOT(self):
        """ Start POEdit with untouched empty catalog """
        POFile = self._getPOTpath()
        if os.path.isfile(POFile):
            self._StartPOEdit(POFile)
        else:
            self.GetCTRoot().logger.write_error(_("POT file does not exist, add translatable text (label starting with '_') in Inkscape first\n"))

    def _AddFont(self):
        dialog = wx.FileDialog(
            self.GetCTRoot().AppFrame,
            _("Choose a font"),
            os.path.expanduser("~"),
            "",
            _("Font files (*.ttf;*.otf;*.woff;*.woff2)|*.ttf;*.otf;*.woff;*.woff2"), wx.OPEN)

        if dialog.ShowModal() == wx.ID_OK:
            fontfile = dialog.GetPath()
            if os.path.isfile(fontfile):
                familyname, uniquename, formatname, mimetype = GetFontTypeAndFamilyName(fontfile)
            else:
                self.GetCTRoot().logger.write_error(
                    _('Selected font %s is not a readable file\n')%fontfile)
                return
            if familyname is None or uniquename is None or formatname is None or mimetype is None:
                self.GetCTRoot().logger.write_error(
                    _('Selected font file %s is invalid or incompatible\n')%fontfile)
                return

            project_path = self.CTNPath()

            fontfname = uniquename + "." + mimetype.split('/')[1]
            fontdir = os.path.join(project_path, "fonts") 
            newfontfile = os.path.join(fontdir, fontfname) 

            if not os.path.exists(fontdir):
                os.mkdir(fontdir)

            shutil.copyfile(fontfile, newfontfile)

            self.GetCTRoot().logger.write(
                _('Added font %s as %s\n')%(fontfile,newfontfile))

    def _DelFont(self):
        project_path = self.CTNPath()
        fontdir = os.path.join(project_path, "fonts") 
        dialog = wx.FileDialog(
            self.GetCTRoot().AppFrame,
            _("Choose a font to remove"),
            fontdir,
            "",
            _("Font files (*.ttf;*.otf;*.woff;*.woff2)|*.ttf;*.otf;*.woff;*.woff2"), wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            fontfile = dialog.GetPath()
            if os.path.isfile(fontfile):
                if os.path.relpath(fontfile, fontdir) == os.path.basename(fontfile):
                    os.remove(fontfile) 
                    self.GetCTRoot().logger.write(
                        _('Removed font %s\n')%fontfile)
                else:
                    self.GetCTRoot().logger.write_error(
                        _("Font to remove %s is not in %s\n") % (fontfile,fontdir))
            else:
                self.GetCTRoot().logger.write_error(
                    _("Font file does not exist: %s\n") % fontfile)
        
    def CTNGlobalInstances(self):
        location_str = "_".join(map(str, self.GetCurrentLocation()))
        return [("CURRENT_PAGE_"+location_str, "HMI_STRING", "")]

    ## In case one day we support more than one heartbeat
    #     view_name = self.BaseParams.getName()
    #     return [(view_name + "_HEARTBEAT", "HMI_INT", "")]

    def GetIconName(self):
        return "SVGHMI"
