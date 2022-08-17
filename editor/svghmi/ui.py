#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
# Copyright (C) 2021: Edouard TISSERANT
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
import os
import hashlib
import weakref
import re
import tempfile
from threading import Thread, Lock
from functools import reduce
from itertools import izip
from operator import or_
from tempfile import NamedTemporaryFile

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from lxml import etree
from lxml.etree import XSLTApplyError
from XSLTransform import XSLTransform

import util.paths as paths
from IDEFrame import EncodeFileSystemPath, DecodeFileSystemPath
from docutil import get_inkscape_path, get_inkscape_version

from util.ProcessLogger import ProcessLogger

ScriptDirectory = paths.AbsDir(__file__)

HMITreeDndMagicWord = "text/beremiz-hmitree"

class HMITreeSelector(wx.TreeCtrl):
    def __init__(self, parent):

        wx.TreeCtrl.__init__(self, parent, style=(
            wx.TR_MULTIPLE |
            wx.TR_HAS_BUTTONS |
            wx.SUNKEN_BORDER |
            wx.TR_LINES_AT_ROOT))

        self.ordered_items = []
        self.parent = parent

        self.MakeTree()

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeNodeSelection)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnTreeBeginDrag)

    def _recurseTree(self, current_hmitree_root, current_tc_root):
        for c in current_hmitree_root.children:
            if hasattr(c, "children"):
                display_name = ('{} (class={})'.format(c.name, c.hmiclass)) \
                               if c.hmiclass is not None else c.name
                tc_child = self.AppendItem(current_tc_root, display_name)
                self.SetPyData(tc_child, c)

                self._recurseTree(c,tc_child)
            else:
                display_name = '{} {}'.format(c.nodetype[4:], c.name)
                tc_child = self.AppendItem(current_tc_root, display_name)
                self.SetPyData(tc_child, c)

    def OnTreeNodeSelection(self, event):
        items = self.GetSelections()
        items_pydata = [self.GetPyData(item) for item in items]

        # append new items to ordered item list
        for item_pydata in items_pydata:
            if item_pydata not in self.ordered_items:
                self.ordered_items.append(item_pydata)

        # filter out vanished items
        self.ordered_items = [
            item_pydata 
            for item_pydata in self.ordered_items 
            if item_pydata in items_pydata]

        self.parent.OnHMITreeNodeSelection(self.ordered_items)

    def OnTreeBeginDrag(self, event):
        """
        Called when a drag is started in tree
        @param event: wx.TreeEvent
        """
        if self.ordered_items:
            # Just send a recognizable mime-type, drop destination
            # will get python data from parent
            data = wx.CustomDataObject(HMITreeDndMagicWord)
            dragSource = wx.DropSource(self)
            dragSource.SetData(data)
            dragSource.DoDragDrop()

    def MakeTree(self, hmi_tree_root=None):

        self.Freeze()

        self.root = None
        self.DeleteAllItems()

        root_display_name = _("Please build to see HMI Tree") \
            if hmi_tree_root is None else "HMI"
        self.root = self.AddRoot(root_display_name)
        self.SetPyData(self.root, hmi_tree_root)

        if hmi_tree_root is not None:
            self._recurseTree(hmi_tree_root, self.root)
            self.Expand(self.root)

        self.Thaw()

class WidgetPicker(wx.TreeCtrl):
    def __init__(self, parent, initialdir=None):
        wx.TreeCtrl.__init__(self, parent, style=(
            wx.TR_MULTIPLE |
            wx.TR_HAS_BUTTONS |
            wx.SUNKEN_BORDER |
            wx.TR_LINES_AT_ROOT))

        self.MakeTree(initialdir)

    def _recurseTree(self, current_dir, current_tc_root, dirlist):
        """
        recurse through subdirectories, but creates tree nodes 
        only when (sub)directory conbtains .svg file
        """
        res = []
        for f in sorted(os.listdir(current_dir)):
            p = os.path.join(current_dir,f)
            if os.path.isdir(p):

                r = self._recurseTree(p, current_tc_root, dirlist + [f])
                if len(r) > 0 :
                    res = r
                    dirlist = []
                    current_tc_root = res.pop()

            elif os.path.splitext(f)[1].upper() == ".SVG":
                if len(dirlist) > 0 :
                    res = []
                    for d in dirlist:
                        current_tc_root = self.AppendItem(current_tc_root, d)
                        res.append(current_tc_root)
                        self.SetPyData(current_tc_root, None)
                    dirlist = []
                    res.pop()
                tc_child = self.AppendItem(current_tc_root, f)
                self.SetPyData(tc_child, p)
        return res

    def MakeTree(self, lib_dir = None):

        self.Freeze()

        self.root = None
        self.DeleteAllItems()

        root_display_name = _("Please select widget library directory") \
            if lib_dir is None else os.path.basename(lib_dir)
        self.root = self.AddRoot(root_display_name)
        self.SetPyData(self.root, None)

        if lib_dir is not None and os.path.exists(lib_dir):
            self._recurseTree(lib_dir, self.root, [])
            self.Expand(self.root)

        self.Thaw()

class PathDropTarget(wx.DropTarget):

    def __init__(self, parent):
        data = wx.CustomDataObject(HMITreeDndMagicWord)
        wx.DropTarget.__init__(self, data)
        self.ParentWindow = parent

    def OnDrop(self, x, y):
        self.ParentWindow.OnHMITreeDnD()
        return True

class ParamEditor(wx.Panel):
    def __init__(self, parent, paramdesc):
        wx.Panel.__init__(self, parent.main_panel)
        label = paramdesc.get("name")+ ": " + paramdesc.get("accepts") 
        if paramdesc.text:
            label += "\n\"" + paramdesc.text + "\""
        self.desc = wx.StaticText(self, label=label)
        self.valid_bmp = wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR, (16,16))
        self.invalid_bmp = wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR, (16,16))
        self.validity_sbmp = wx.StaticBitmap(self, -1, self.invalid_bmp)
        self.edit = wx.TextCtrl(self)
        self.edit_sizer = wx.FlexGridSizer(cols=2, hgap=0, rows=1, vgap=0)
        self.edit_sizer.AddGrowableCol(0)
        self.edit_sizer.AddGrowableRow(0)
        self.edit_sizer.Add(self.edit, flag=wx.GROW)
        self.edit_sizer.Add(self.validity_sbmp, flag=wx.GROW)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.desc, flag=wx.GROW)
        self.main_sizer.Add(self.edit_sizer, flag=wx.GROW)
        self.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)

    def GetValue(self):
        return self.edit.GetValue()

    def setValidity(self, validity):
        if validity is not None:
            bmp = self.valid_bmp if validity else self.invalid_bmp
            self.validity_sbmp.SetBitmap(bmp)
            self.validity_sbmp.Show(True)
        else :
            self.validity_sbmp.Show(False)

models = { typename: re.compile(regex) for typename, regex in [
    ("string", r".*"),
    ("int", r"^-?([1-9][0-9]*|0)$"),
    ("real", r"^-?([1-9][0-9]*|0)(\.[0-9]+)?$")]}

class ArgEditor(ParamEditor):
    def __init__(self, parent, argdesc, prefillargdesc):
        ParamEditor.__init__(self, parent, argdesc)
        self.ParentObj = parent
        self.argdesc = argdesc
        self.Bind(wx.EVT_TEXT, self.OnArgChanged, self.edit)
        prefill = "" if prefillargdesc is None else prefillargdesc.get("value")
        self.edit.SetValue(prefill)
        # TODO add a button to add more ArgEditror instance 
        #      when ordinality is multiple

    def OnArgChanged(self, event):
        txt = self.edit.GetValue()
        accepts = self.argdesc.get("accepts").split(',')
        self.setValidity(
            reduce(or_,
                   map(lambda typename: 
                           models[typename].match(txt) is not None,
                       accepts), 
                   False)
            if accepts and txt else None)
        self.ParentObj.RegenSVGLater()
        event.Skip()

class PathEditor(ParamEditor):
    def __init__(self, parent, pathdesc):
        ParamEditor.__init__(self, parent, pathdesc)
        self.ParentObj = parent
        self.pathdesc = pathdesc
        DropTarget = PathDropTarget(self)
        self.edit.SetDropTarget(DropTarget)
        self.edit.SetHint(_("Drag'n'drop HMI variable here"))
        self.Bind(wx.EVT_TEXT, self.OnPathChanged, self.edit)

    def OnHMITreeDnD(self):
        self.ParentObj.GotPathDnDOn(self)

    def SetPath(self, hmitree_node):
        self.edit.ChangeValue(hmitree_node.hmi_path())
        self.setValidity(
            hmitree_node.nodetype in self.pathdesc.get("accepts").split(","))

    def OnPathChanged(self, event):
        # TODO : find corresponding hmitre node and type to update validity
        # Lazy way : hide validity
        self.setValidity(None)
        self.ParentObj.RegenSVGLater()
        event.Skip()
    
def KeepDoubleNewLines(txt):
    return "\n\n".join(map(
        lambda s:re.sub(r'\s+',' ',s),
        txt.split("\n\n")))

_conf_key = "SVGHMIWidgetLib"
_preview_height = 200
_preview_margin = 5
thumbnail_temp_path = None

class WidgetLibBrowser(wx.SplitterWindow):
    def __init__(self, parent, controler, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):

        wx.SplitterWindow.__init__(self, parent,
                                   style=wx.SUNKEN_BORDER | wx.SP_3D)

        self.bmp = None
        self.msg = None
        self.hmitree_nodes = []
        self.selected_SVG = None
        self.Controler = controler

        self.Config = wx.ConfigBase.Get()
        self.libdir = self.RecallLibDir()
        if self.libdir is None:
            self.libdir = os.path.join(ScriptDirectory, "widgetlib") 

        self.picker_desc_splitter = wx.SplitterWindow(self, style=wx.SUNKEN_BORDER | wx.SP_3D)

        self.picker_panel = wx.Panel(self.picker_desc_splitter)
        self.picker_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=0)
        self.picker_sizer.AddGrowableCol(0)
        self.picker_sizer.AddGrowableRow(1)

        self.widgetpicker = WidgetPicker(self.picker_panel, self.libdir)
        self.libbutton = wx.Button(self.picker_panel, -1, _("Select SVG widget library"))

        self.picker_sizer.Add(self.libbutton, flag=wx.GROW)
        self.picker_sizer.Add(self.widgetpicker, flag=wx.GROW)
        self.picker_sizer.Layout()
        self.picker_panel.SetAutoLayout(True)
        self.picker_panel.SetSizer(self.picker_sizer)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnWidgetSelection, self.widgetpicker)
        self.Bind(wx.EVT_BUTTON, self.OnSelectLibDir, self.libbutton)



        self.main_panel = ScrolledPanel(parent=self,
                                                name='MiscellaneousPanel',
                                                style=wx.TAB_TRAVERSAL)

        self.main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=3, vgap=0)
        self.main_sizer.AddGrowableCol(0)
        self.main_sizer.AddGrowableRow(2)

        self.staticmsg = wx.StaticText(self, label = _("Drag selected Widget from here to Inkscape"))
        self.preview = wx.Panel(self.main_panel, size=(-1, _preview_height + _preview_margin*2))
        self.signature_sizer = wx.BoxSizer(wx.VERTICAL)
        self.args_box = wx.StaticBox(self.main_panel, -1,
                                     _("Widget's arguments"),
                                     style = wx.ALIGN_CENTRE_HORIZONTAL)
        self.args_sizer = wx.StaticBoxSizer(self.args_box, wx.VERTICAL)
        self.paths_box = wx.StaticBox(self.main_panel, -1,
                                      _("Widget's variables"),
                                      style = wx.ALIGN_CENTRE_HORIZONTAL)
        self.paths_sizer = wx.StaticBoxSizer(self.paths_box, wx.VERTICAL)
        self.signature_sizer.Add(self.args_sizer, flag=wx.GROW)
        self.signature_sizer.AddSpacer(5)
        self.signature_sizer.Add(self.paths_sizer, flag=wx.GROW)
        self.main_sizer.Add(self.staticmsg, flag=wx.GROW)
        self.main_sizer.Add(self.preview, flag=wx.GROW)
        self.main_sizer.Add(self.signature_sizer, flag=wx.GROW)
        self.main_sizer.Layout()
        self.main_panel.SetAutoLayout(True)
        self.main_panel.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self.main_panel)
        self.preview.Bind(wx.EVT_PAINT, self.OnPaint)
        self.preview.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

        self.desc = wx.TextCtrl(self.picker_desc_splitter, size=wx.Size(-1, 160),
                                   style=wx.TE_READONLY | wx.TE_MULTILINE)

        self.picker_desc_splitter.SplitHorizontally(self.picker_panel, self.desc, 400)
        self.SplitVertically(self.main_panel, self.picker_desc_splitter, 300)

        self.tempf = None 

        self.RegenSVGThread = None
        self.RegenSVGLock = Lock()
        self.RegenSVGTimer = wx.Timer(self, -1)
        self.RegenSVGParams = None
        self.Bind(wx.EVT_TIMER,
                  self.RegenSVG,
                  self.RegenSVGTimer)

        self.args_editors = []
        self.paths_editors = []

    def SetMessage(self, msg):
        self.staticmsg.SetLabel(msg)
        self.main_sizer.Layout()

    def ResetSignature(self):
        self.args_sizer.Clear()
        for editor in self.args_editors:
            editor.Destroy()
        self.args_editors = []

        self.paths_sizer.Clear()
        for editor in self.paths_editors:
            editor.Destroy()
        self.paths_editors = []

    def AddArgToSignature(self, arg, prefillarg):
        new_editor = ArgEditor(self, arg, prefillarg)
        self.args_editors.append(new_editor)
        self.args_sizer.Add(new_editor, flag=wx.GROW)

    def AddPathToSignature(self, path):
        new_editor = PathEditor(self, path)
        self.paths_editors.append(new_editor)
        self.paths_sizer.Add(new_editor, flag=wx.GROW)

    def GotPathDnDOn(self, target_editor):
        dndindex = self.paths_editors.index(target_editor)

        for hmitree_node,editor in zip(self.hmitree_nodes,
                                   self.paths_editors[dndindex:]):
            editor.SetPath(hmitree_node)

        self.RegenSVGNow()

    def RecallLibDir(self):
        conf = self.Config.Read(_conf_key)
        if len(conf) == 0:
            return None
        else:
            return DecodeFileSystemPath(conf)

    def RememberLibDir(self, path):
        self.Config.Write(_conf_key,
                          EncodeFileSystemPath(path))
        self.Config.Flush()

    def DrawPreview(self):
        """
        Refresh preview panel 
        """
        # Init preview panel paint device context
        dc = wx.PaintDC(self.preview)
        dc.Clear()

        if self.bmp:
            # Get Preview panel size
            sz = self.preview.GetClientSize()
            w = self.bmp.GetWidth()
            dc.DrawBitmap(self.bmp, (sz.width - w)/2, _preview_margin)



    def OnSelectLibDir(self, event):
        defaultpath = self.RecallLibDir()
        if defaultpath == None:
            defaultpath = os.path.expanduser("~")

        dialog = wx.DirDialog(self, _("Choose a widget library"), defaultpath,
                              style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        if dialog.ShowModal() == wx.ID_OK:
            self.libdir = dialog.GetPath()
            self.RememberLibDir(self.libdir)
            self.widgetpicker.MakeTree(self.libdir)

        dialog.Destroy()

    def OnPaint(self, event):
        """
        Called when Preview panel needs to be redrawn
        @param event: wx.PaintEvent
        """
        self.DrawPreview()
        event.Skip()

    def GenThumbnail(self, svgpath, thumbpath):
        inkpath = get_inkscape_path()
        if inkpath is None:
            self.msg = _("Inkscape is not installed.")
            return False

        export_opt = "-o" if get_inkscape_version()[0] > 0 else "-e"

        # TODO: spawn a thread, to decouple thumbnail gen
        status, result, _err_result = ProcessLogger(
            self.Controler.GetCTRoot().logger,
            '"' + inkpath + '" "' + svgpath + '" ' +
            export_opt + ' "' + thumbpath +
            '" -D -h ' + str(_preview_height)).spin()
        if status != 0:
            self.msg = _("Inkscape couldn't generate thumbnail.")
            return False
        return True

    def OnWidgetSelection(self, event):
        """
        Called when tree item is selected
        @param event: wx.TreeEvent
        """
        global thumbnail_temp_path
        event.Skip()
        item_pydata = self.widgetpicker.GetPyData(event.GetItem())
        if item_pydata is not None:
            svgpath = item_pydata

            if thumbnail_temp_path is None:
                try:
                    dname = os.path.dirname(svgpath)
                    thumbdir = os.path.join(dname, ".svghmithumbs") 
                    if not os.path.exists(thumbdir):
                        os.mkdir(thumbdir)
                except Exception :
                    # library not writable : use temp dir
                    thumbnail_temp_path = os.path.join(
                        tempfile.gettempdir(), "svghmithumbs")
                    thumbdir = thumbnail_temp_path
                    if not os.path.exists(thumbdir):
                        os.mkdir(thumbdir)
            else:
                thumbdir = thumbnail_temp_path

            fname = os.path.basename(svgpath)
            hasher = hashlib.new('md5')
            with open(svgpath, 'rb') as afile:
                while True:
                    buf = afile.read(65536)
                    if len(buf) > 0:
                        hasher.update(buf)
                    else:
                        break
            digest = hasher.hexdigest()
            thumbfname = os.path.splitext(fname)[0]+"_"+digest+".png"
            thumbpath = os.path.join(thumbdir, thumbfname) 

            have_thumb = os.path.exists(thumbpath)

            if not have_thumb:
                self.Controler.GetCTRoot().logger.write(
                    "Rendering preview of " + fname + " widget.\n")
                have_thumb = self.GenThumbnail(svgpath, thumbpath)

            self.bmp = wx.Bitmap(thumbpath) if have_thumb else None

            self.selected_SVG = svgpath if have_thumb else None

            self.AnalyseWidgetAndUpdateUI(fname)

            self.SetMessage(self.msg)

            self.Refresh()

    def OnHMITreeNodeSelection(self, hmitree_nodes):
        self.hmitree_nodes = hmitree_nodes

    def OnLeftDown(self, evt):
        if self.tempf is not None:
            filename = self.tempf.name
            data = wx.FileDataObject()
            data.AddFile(filename)
            dropSource = wx.DropSource(self)
            dropSource.SetData(data)
            dropSource.DoDragDrop(wx.Drag_AllowMove)

    def RegenSVGLater(self, when=1):
        self.SetMessage(_("SVG generation pending"))
        self.RegenSVGTimer.Start(milliseconds=when*1000, oneShot=True)

    def RegenSVGNow(self):
        self.RegenSVGLater(when=0)

    def RegenSVG(self, event):
        self.SetMessage(_("Generating SVG..."))
        args = [arged.GetValue() for arged in self.args_editors]
        while args and not args[-1]: args.pop(-1)
        paths = [pathed.GetValue() for pathed in self.paths_editors]
        while paths and not paths[-1]: paths.pop(-1)
        if self.RegenSVGLock.acquire(True):
            self.RegenSVGParams = (args, paths)
            if self.RegenSVGThread is None:
                self.RegenSVGThread = \
                    Thread(target=self.RegenSVGProc,
                           name="RegenSVGThread").start()
            self.RegenSVGLock.release()
        event.Skip()

    def RegenSVGProc(self):
        self.RegenSVGLock.acquire(True)

        newparams = self.RegenSVGParams
        self.RegenSVGParams = None

        while newparams is not None:
            self.RegenSVGLock.release()

            res = self.GenDnDSVG(newparams)

            self.RegenSVGLock.acquire(True)

            newparams = self.RegenSVGParams
            self.RegenSVGParams = None

        self.RegenSVGThread = None

        self.RegenSVGLock.release()

        wx.CallAfter(self.DoneRegenSVG)
        
    def DoneRegenSVG(self):
        self.SetMessage(self.msg if self.msg else _("SVG ready for drag'n'drop"))
        
    def AnalyseWidgetAndUpdateUI(self, fname):
        self.msg = ""
        self.ResetSignature()

        try:
            if self.selected_SVG is None:
                raise Exception(_("No widget selected"))

            transform = XSLTransform(
                os.path.join(ScriptDirectory, "analyse_widget.xslt"),[])

            svgdom = etree.parse(self.selected_SVG)

            signature = transform.transform(svgdom)

            for entry in transform.get_error_log():
                self.msg += "XSLT: " + entry.message + "\n" 

        except Exception as e:
            self.msg += str(e)
            return
        except XSLTApplyError as e:
            self.msg += "Widget " + fname + " analysis error: " + e.message
            return
            
        self.msg += "Widget " + fname + ": OK"

        widgets = signature.getroot()
        widget = widgets.find("widget")
        defs = widget.find("defs")
        # Keep double newlines (to mark paragraphs)
        widget_desc = widget.find("desc")
        self.desc.SetValue(
            fname + ":\n\n" + (
                _("No description given") if widget_desc is None else 
                KeepDoubleNewLines(widget_desc.text)
            ) + "\n\n" +
            defs.find("type").text + " Widget: "+defs.find("shortdesc").text+"\n\n" +
            KeepDoubleNewLines(defs.find("longdesc").text))
        prefillargs = widget.findall("arg")
        args = defs.findall("arg")
        # extend args description in prefilled args in longer 
        # (case of variable list of args)
        if len(prefillargs) < len(args):
            prefillargs += [None]*(len(args)-len(prefillargs))
        if args and len(prefillargs) > len(args):
            # TODO: check ordinality of last arg
            # TODO: check that only last arg has multiple ordinality
            args += [args[-1]]*(len(prefillargs)-len(args))
        self.args_box.Show(len(args)!=0)
        for arg, prefillarg in izip(args,prefillargs):
            self.AddArgToSignature(arg, prefillarg)

        # TODO support predefined path count (as for XYGraph)
        paths = defs.findall("path")
        self.paths_box.Show(len(paths)!=0)
        for path in paths:
            self.AddPathToSignature(path)

        # # TODO DEAD CODE ?
        # for widget in widgets:
        #     widget_type = widget.get("type")
        #     for path in widget.iterchildren("path"):
        #         path_value = path.get("value")
        #         path_accepts = map(
        #             str.strip, path.get("accepts", '')[1:-1].split(','))

        self.main_panel.SetupScrolling(scroll_x=False)

    def GetWidgetParams(self, _context):
        args,paths = self.GenDnDSVGParams
        root = etree.Element("params")
        for arg in args:
            etree.SubElement(root, "arg", value=arg)
        for path in paths:
            etree.SubElement(root, "path", value=path)
        return root


    def GenDnDSVG(self, newparams):
        self.msg = ""

        self.GenDnDSVGParams = newparams

        if self.tempf is not None:
            os.unlink(self.tempf.name)
            self.tempf = None

        try:
            if self.selected_SVG is None:
                raise Exception(_("No widget selected"))

            transform = XSLTransform(
                os.path.join(ScriptDirectory, "gen_dnd_widget_svg.xslt"),
                [("GetWidgetParams", self.GetWidgetParams)])

            svgdom = etree.parse(self.selected_SVG)

            result = transform.transform(svgdom)

            for entry in transform.get_error_log():
                self.msg += "XSLT: " + entry.message + "\n" 

            self.tempf = NamedTemporaryFile(suffix='.svg', delete=False)
            result.write(self.tempf, encoding="utf-8")
            self.tempf.close()

        except Exception as e:
            self.msg += str(e)
        except XSLTApplyError as e:
            self.msg += "Widget transform error: " + e.message
                
    def __del__(self):
        if self.tempf is not None:
            os.unlink(self.tempf.name)

class SVGHMI_UI(wx.SplitterWindow):

    def __init__(self, parent, controler, register_for_HMI_tree_updates):
        wx.SplitterWindow.__init__(self, parent,
                                   style=wx.SUNKEN_BORDER | wx.SP_3D)

        self.SelectionTree = HMITreeSelector(self)
        self.Staging = WidgetLibBrowser(self, controler)
        self.SplitVertically(self.SelectionTree, self.Staging, 300)
        register_for_HMI_tree_updates(weakref.ref(self))

    def HMITreeUpdate(self, hmi_tree_root):
        self.SelectionTree.MakeTree(hmi_tree_root)

    def OnHMITreeNodeSelection(self, hmitree_nodes):
        self.Staging.OnHMITreeNodeSelection(hmitree_nodes)
