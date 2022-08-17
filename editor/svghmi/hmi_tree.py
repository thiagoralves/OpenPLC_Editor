#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
# Copyright (C) 2021: Edouard TISSERANT
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
from itertools import izip, imap
from pprint import pformat
import weakref
import hashlib

from lxml import etree

HMI_TYPES_DESC = {
    "HMI_NODE":{},
    "HMI_STRING":{},
    "HMI_INT":{},
    "HMI_BOOL":{},
    "HMI_REAL":{}
}

HMI_TYPES = HMI_TYPES_DESC.keys()

class HMITreeNode(object):
    def __init__(self, path, name, nodetype, iectype = None, vartype = None, cpath = None, hmiclass = None):
        self.path = path
        self.name = name
        self.nodetype = nodetype
        self.hmiclass = hmiclass
        self.parent = None

        if iectype is not None:
            self.iectype = iectype
            self.vartype = vartype
            self.cpath = cpath

        if nodetype in ["HMI_NODE"]:
            self.children = []

    def pprint(self, indent = 0):
        res = ">"*indent + pformat(self.__dict__, indent = indent, depth = 1) + "\n"
        if hasattr(self, "children"):
            res += "\n".join([child.pprint(indent = indent + 1)
                              for child in self.children])
            res += "\n"

        return res

    def place_node(self, node):
        best_child = None
        known_best_match = 0
        potential_siblings = {}
        for child in self.children:
            if child.path is not None:
                in_common = 0
                for child_path_item, node_path_item in izip(child.path, node.path):
                    if child_path_item == node_path_item:
                        in_common +=1
                    else:
                        break
                # Match can only be HMI_NODE, and the whole path of node
                # must match candidate node (except for name part)
                # since candidate would become child of that node
                if in_common > known_best_match and \
                   child.nodetype == "HMI_NODE" and \
                   in_common == len(child.path) - 1:
                    known_best_match = in_common
                    best_child = child
                else:
                    potential_siblings[child.path[
                        -2 if child.nodetype == "HMI_NODE" else -1]] = child
        if best_child is not None:
            if node.nodetype == "HMI_NODE" and best_child.path[:-1] == node.path[:-1]:
                return "Duplicate_HMI_NODE", best_child
            return best_child.place_node(node)
        else:
            candidate_name = node.path[-2 if node.nodetype == "HMI_NODE" else -1]
            if candidate_name in potential_siblings:
                return "Non_Unique", potential_siblings[candidate_name]

            if node.nodetype == "HMI_NODE" and len(self.children) > 0:
                prev = self.children[-1]
                if prev.path[:-1] == node.path[:-1]:
                    return "Late_HMI_NODE",prev

            node.parent = weakref.ref(self)
            self.children.append(node)
            return None

    def etree(self, add_hash=False):

        attribs = dict(name=self.name)
        if self.path is not None:
            attribs["path"] = ".".join(self.path)

        if self.hmiclass is not None:
            attribs["class"] = self.hmiclass

        if add_hash:
            attribs["hash"] = ",".join(map(str,self.hash()))

        res = etree.Element(self.nodetype, **attribs)

        if hasattr(self, "children"):
            for child_etree in imap(lambda c:c.etree(), self.children):
                res.append(child_etree)

        return res

    @classmethod
    def from_etree(cls, enode):
        """
        alternative constructor, restoring HMI Tree from XML backup
        note: all C-related information is gone, 
              this restore is only for tree display and widget picking
        """
        nodetype = enode.tag
        attributes = enode.attrib
        name = attributes["name"]
        path = attributes["path"].split('.') if "path" in attributes else None 
        hmiclass = attributes.get("class", None)
        # hash is computed on demand
        node = cls(path, name, nodetype, hmiclass=hmiclass)
        for child in enode.iterchildren():
            newnode = cls.from_etree(child)
            newnode.parent = weakref.ref(node)
            node.children.append(newnode)
        return node

    def traverse(self):
        yield self
        if hasattr(self, "children"):
            for c in self.children:
                for yoodl in c.traverse():
                    yield yoodl

    def hmi_path(self):
        if self.parent is None:
            return "/"
        p = self.parent()
        if p.parent is None:
            return "/" + self.name
        return p.hmi_path() + "/" + self.name

    def hash(self):
        """ Produce a hash, any change in HMI tree structure change that hash """
        s = hashlib.new('md5')
        self._hash(s)
        # limit size to HMI_HASH_SIZE as in svghmi.c
        return map(ord,s.digest())[:8]

    def _hash(self, s):
        s.update(str((self.name,self.nodetype)))
        if hasattr(self, "children"):
            for c in self.children:
                c._hash(s)

SPECIAL_NODES = [("HMI_ROOT", "HMI_NODE"),
                 ("heartbeat", "HMI_INT")]

