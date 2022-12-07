#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from types import ModuleType

# TODO use gettext instead
def get_translation(txt):
    return txt


class FakeObject:
    def __init__(self, *args, **kwargs):
        self.__classname__ = kwargs["__classname__"]

    def __getattr__(self,name):
        if name.startswith('__'):
            raise AttributeError(name)
        return FakeObject(__classname__=self.__classname__+"."+name)

    def __call__(self, *args, **kwargs):
        return FakeObject(__classname__=self.__classname__+"()")

    def __getitem__(self, key):
        raise IndexError(key)

    def __str__(self):
        return self.__classname__

    def __or__(self, other):
        return FakeObject(__classname__=self.__classname__+"|"+other.__classname__)


class FakeClass:
    def __init__(self, *args, **kwargs):
        print(("DUMMY Class __init__ !",self.__name__,args,kwargs))


class FakeModule(ModuleType):
    def __init__(self, name, classes):
        self.__modname__ = name
        self.__objects__ = dict([(desc, type(desc, (FakeClass,), {}))
            if type(desc)==str else desc for desc in classes])
        ModuleType(name)

    def __getattr__(self,name):
        if name.startswith('__'):
            raise AttributeError(name)
  
        if name in self.__objects__:
            return self.__objects__[name]
  
        obj = FakeObject(__classname__=self.__modname__+"."+name)
        self.__objects__[name] = obj
        return obj


# Keep track of already faked modules to catch those
# that are already present in sys.modules from start
# (i.e. mpl_toolkits for exemple)
already_patched = {}

for name, classes in [
    # list given for each module name contains name string for a FakeClass,
    # otherwise a tuple (name, object) for arbitrary object/function/class
    ('wx',[
        'Panel', 'PyCommandEvent', 'Dialog', 'PopupWindow', 'TextEntryDialog',
        'Notebook', 'ListCtrl', 'TextDropTarget', 'PyControl', 'TextCtrl', 
        'SplitterWindow', 'Frame', 'Printout', 'StaticBitmap', 'DropTarget',
        ('GetTranslation', get_translation)]),
    ('wx.lib.agw.advancedsplash',[]),
    ('wx.dataview',['DataViewIndexListModel', 'PyDataViewIndexListModel']),
    ('wx.lib.buttons',['GenBitmapTextButton']),
    ('wx.adv',['EditableListBox']),
    ('wx.grid',[
        'Grid', 'PyGridTableBase', 'GridCellEditor', 'GridCellTextEditor',
        'GridCellChoiceEditor']),
    ('wx.lib.agw.customtreectrl',['CustomTreeCtrl']),
    ('wx.lib.gizmos',[]),
    ('wx.lib.intctrl',['IntCtrl']),
    ('matplotlib.pyplot',[]),
    ('matplotlib.backends.backend_wxagg',['FigureCanvasWxAgg']),
    ('wx.stc',['StyledTextCtrl']),
    ('wx.lib.scrolledpanel',[]),
    ('wx.lib.mixins.listctrl',['ColumnSorterMixin', 'ListCtrlAutoWidthMixin']),
    ('wx.dataview',['PyDataViewIndexListModel']),
    ('matplotlib.backends.backend_agg',[]),
    ('wx.aui',[]),
    ('mpl_toolkits.mplot3d',[])]:
    modpath = None
    parentmod = None
    for identifier in name.split("."):
        modpath = (modpath + "." + identifier) if modpath else identifier
        mod = sys.modules.get(modpath, None)

        if mod is None or modpath not in already_patched:
            mod = FakeModule(modpath, classes)
            sys.modules[modpath] = mod
            already_patched[modpath] = True

        if parentmod is not None:
            parentmod.__objects__[identifier] = mod

        parentmod = mod

import builtins

builtins.__dict__['_'] = get_translation

