#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
# Copyright (C) 2021: Edouard TISSERANT
#
# See COPYING file for copyrights details.

from __future__ import absolute_import
from lxml import etree
import os
import sys
import subprocess
import time
import ast
import wx
import re

# to have it for python 2, had to install 
# https://pypi.org/project/pycountry/18.12.8/
# python2 -m pip install pycountry==18.12.8 --user
import pycountry

cmd_parser = re.compile(r'(?:"([^"]+)"\s*|([^\s]+)\s*)?')

def open_pofile(pofile):
    """ Opens PO file with POEdit """
    
    if sys.platform.startswith('win'):
        from six.moves import winreg
        poedit_cmd = None
        try:
            poedit_cmd = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE,
                                           'SOFTWARE\\Classes\\poedit\\shell\\open\\command')
            cmd = re.findall(cmd_parser, poedit_cmd)
            dblquote_value,smpl_value = cmd[0]
            poedit_path = dblquote_value+smpl_value
        except OSError:
            poedit_path = None

    else:
        try:
            poedit_path = subprocess.check_output("command -v poedit", shell=True).strip()
        except subprocess.CalledProcessError:
            poedit_path = None

    if poedit_path is None:
        wx.MessageBox("POEdit is not found or installed !")
    else:
        subprocess.Popen([poedit_path,pofile])

def EtreeToMessages(msgs):
    """ Converts XML tree from 'extract_i18n' templates into a list of tuples """
    messages = []

    for msg in msgs:
        messages.append((
            "\n".join([line.text for line in msg]),
            msg.get("label"), msg.get("id")))

    return messages

def SaveCatalog(fname, messages):
    """ Save messages given as list of tupple (msg,label,id) in POT file """
    w = POTWriter()
    w.ImportMessages(messages)

    with open(fname, 'w') as POT_file:
        w.write(POT_file)

def GetPoFiles(dirpath):
    po_files = [fname for fname in os.listdir(dirpath) if fname.endswith(".po")]
    po_files.sort()
    return [(po_fname[:-3],os.path.join(dirpath, po_fname)) for po_fname in po_files]

def ReadTranslations(dirpath):
    """ Read all PO files from a directory and return a list of (langcode, translation_dict) tuples """

    translations = []
    for translation_name, po_path in GetPoFiles(dirpath):
        r = POReader()
        with open(po_path, 'r') as PO_file:
            r.read(PO_file)
            translations.append((translation_name, r.get_messages()))
    return translations

def MatchTranslations(translations, messages, errcallback):
    """
    Matches translations against original message catalog,
    warn about inconsistancies,
    returns list of langs, and a list of (msgid, [translations]) tuples
    """
    translated_messages = []
    broken_lang = set()
    for msgid,label,svgid in messages:
        translated_message = []
        for langcode,translation in translations:
            msg = translation.pop(msgid, None)
            if msg is None:
                broken_lang.add(langcode)
                errcallback(_('{}: Missing translation for "{}" (label:{}, id:{})\n').format(langcode,msgid,label,svgid))
                translated_message.append(msgid)
            else:
                translated_message.append(msg)
        translated_messages.append((msgid,translated_message))
    langs = []
    for langcode,translation in translations:
        try:
            l,c = langcode.split("_")
            language_name = pycountry.languages.get(alpha_2 = l).name
            country_name = pycountry.countries.get(alpha_2 = c).name
            langname = "{} ({})".format(language_name, country_name)
        except:
            try:
                langname = pycountry.languages.get(alpha_2 = langcode).name
            except:
                langname = langcode

        langs.append((langname,langcode))

        broken = False
        for msgid, msg in translation.iteritems():
            broken = True
            errcallback(_('{}: Unused translation "{}":"{}"\n').format(langcode,msgid,msg))
        if broken or langcode in broken_lang:
            errcallback(_('Translation for {} is outdated, please edit {}.po, click "Catalog -> Update from POT File..." and select messages.pot.\n').format(langcode,langcode))


    return langs,translated_messages


def TranslationToEtree(langs,translated_messages):

    result = etree.Element("translations")

    langsroot = etree.SubElement(result, "langs")
    for name, code in langs:
        langel = etree.SubElement(langsroot, "lang", {"code":code})
        langel.text = name

    msgsroot = etree.SubElement(result, "messages")
    for msgid, msgs in translated_messages:
        msgidel = etree.SubElement(msgsroot, "msgid")
        for msg in msgs:
            msgel = etree.SubElement(msgidel, "msg")
            for line in msg.split("\n"):
                lineel = etree.SubElement(msgel, "line")
                lineel.text = escape(line.encode("utf-8")).decode("utf-8")

    return result



locpfx = '#:svghmi.svg:'

pot_header = '''\
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR ORGANIZATION
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"POT-Creation-Date: %(time)s\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: SVGHMI 1.0\\n"

'''
escapes = []

def make_escapes(pass_iso8859):
    global escapes
    escapes = [chr(i) for i in range(256)]
    if pass_iso8859:
        # Allow iso-8859 characters to pass through so that e.g. 'msgid
        # "Höhe"' would result not result in 'msgid "H\366he"'.  Otherwise we
        # escape any character outside the 32..126 range.
        mod = 128
    else:
        mod = 256
    for i in range(mod):
        if not(32 <= i <= 126):
            escapes[i] = "\\%03o" % i
    escapes[ord('\\')] = '\\\\'
    escapes[ord('\t')] = '\\t'
    escapes[ord('\r')] = '\\r'
    escapes[ord('\n')] = '\\n'
    escapes[ord('\"')] = '\\"'

make_escapes(pass_iso8859 = True)

EMPTYSTRING = ''

def escape(s):
    global escapes
    s = list(s)
    for i in range(len(s)):
        s[i] = escapes[ord(s[i])]
    return EMPTYSTRING.join(s)

def normalize(s):
    # This converts the various Python string types into a format that is
    # appropriate for .po files, namely much closer to C style.
    lines = s.split('\n')
    if len(lines) == 1:
        s = '"' + escape(s) + '"'
    else:
        if not lines[-1]:
            del lines[-1]
            lines[-1] = lines[-1] + '\n'
        for i in range(len(lines)):
            lines[i] = escape(lines[i])
        lineterm = '\\n"\n"'
        s = '""\n"' + lineterm.join(lines) + '"'
    return s


class POTWriter:
    def __init__(self):
        self.__messages = {}

    def ImportMessages(self, msgs):
        for  msg, label, svgid in msgs:
            self.addentry(msg.encode("utf-8"), label, svgid)

    def addentry(self, msg, label, svgid):
        entry = (label, svgid)
        self.__messages.setdefault(msg, set()).add(entry)

    def write(self, fp):
        timestamp = time.strftime('%Y-%m-%d %H:%M+%Z')
        print >> fp, pot_header % {'time': timestamp}
        reverse = {}
        for k, v in self.__messages.items():
            keys = list(v)
            keys.sort()
            reverse.setdefault(tuple(keys), []).append((k, v))
        rkeys = reverse.keys()
        rkeys.sort()
        for rkey in rkeys:
            rentries = reverse[rkey]
            rentries.sort()
            for k, v in rentries:
                v = list(v)
                v.sort()
                locline = locpfx
                for label, svgid in v:
                    d = {'label': label, 'svgid': svgid}
                    s = _(' %(label)s:%(svgid)s') % d
                    if len(locline) + len(s) <= 78:
                        locline = locline + s
                    else:
                        print >> fp, locline
                        locline = locpfx + s
                if len(locline) > len(locpfx):
                    print >> fp, locline
                print >> fp, 'msgid', normalize(k)
                print >> fp, 'msgstr ""\n'


class POReader:
    def __init__(self):
        self.__messages = {}

    def get_messages(self):
        return self.__messages

    def add(self, msgid, msgstr, fuzzy):
        "Add a non-fuzzy translation to the dictionary."
        if not fuzzy and msgstr and msgid:
            self.__messages[msgid.decode('utf-8')] = msgstr.decode('utf-8')

    def read(self, fp):
        ID = 1
        STR = 2

        lines = fp.readlines()
        section = None
        fuzzy = 0

        # Parse the catalog
        lno = 0
        for l in lines:
            lno += 1
            # If we get a comment line after a msgstr, this is a new entry
            if l[0] == '#' and section == STR:
                self.add(msgid, msgstr, fuzzy)
                section = None
                fuzzy = 0
            # Record a fuzzy mark
            if l[:2] == '#,' and 'fuzzy' in l:
                fuzzy = 1
            # Skip comments
            if l[0] == '#':
                continue
            # Now we are in a msgid section, output previous section
            if l.startswith('msgid') and not l.startswith('msgid_plural'):
                if section == STR:
                    self.add(msgid, msgstr, fuzzy)
                section = ID
                l = l[5:]
                msgid = msgstr = ''
                is_plural = False
            # This is a message with plural forms
            elif l.startswith('msgid_plural'):
                if section != ID:
                    print >> sys.stderr, 'msgid_plural not preceded by msgid on %s:%d' %\
                        (infile, lno)
                    sys.exit(1)
                l = l[12:]
                msgid += '\0' # separator of singular and plural
                is_plural = True
            # Now we are in a msgstr section
            elif l.startswith('msgstr'):
                section = STR
                if l.startswith('msgstr['):
                    if not is_plural:
                        print >> sys.stderr, 'plural without msgid_plural on %s:%d' %\
                            (infile, lno)
                        sys.exit(1)
                    l = l.split(']', 1)[1]
                    if msgstr:
                        msgstr += '\0' # Separator of the various plural forms
                else:
                    if is_plural:
                        print >> sys.stderr, 'indexed msgstr required for plural on  %s:%d' %\
                            (infile, lno)
                        sys.exit(1)
                    l = l[6:]
            # Skip empty lines
            l = l.strip()
            if not l:
                continue
            l = ast.literal_eval(l)
            if section == ID:
                msgid += l
            elif section == STR:
                msgstr += l
            else:
                print >> sys.stderr, 'Syntax error on %s:%d' % (infile, lno), \
                      'before:'
                print >> sys.stderr, l
                sys.exit(1)
        # Add last entry
        if section == STR:
            self.add(msgid, msgstr, fuzzy)


