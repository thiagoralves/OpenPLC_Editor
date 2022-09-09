#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
# This file is based on code written for Whyteboard project.
#
# Copyright (c) 2009, 2010 by Steven Sproat
# Copyright (c) 2016 by Andrey Skvortsov <andrej.skvortzov@gmail.com>
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


"""
This module contains classes extended from wx.Dialog used by the GUI.
"""


from __future__ import absolute_import
import os
import wx
from wx.lib.agw.hyperlink import HyperLinkCtrl
import util.paths as paths

current_dir = paths.AbsDir(__file__)

class AboutDialog(wx.Dialog):
    """
    A replacement About Dialog for Windows, as it uses a generic frame that
    well...sucks.
    """
    def __init__(self, parent, info):
        title = _("About") + " " + info.Name
        wx.Dialog.__init__(self, parent, title=title)
        self.info = info

        if parent and parent.GetIcon():
            self.SetIcon(parent.GetIcon())

        image = None
        if self.info.Icon:
            bitmap = wx.BitmapFromIcon(self.info.Icon)
            image = wx.StaticBitmap(self, bitmap=bitmap)

        name = wx.StaticText(self, label="%s %s" % (info.Name, info.Version))
        description = wx.StaticText(self, label=info.Description)
        description.Wrap(400)
        copyright = wx.StaticText(self, label=info.Copyright)
        url = HyperLinkCtrl(self, label=info.WebSite[0], URL=info.WebSite[1])

        font = name.GetClassDefaultAttributes().font
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(18)
        name.SetFont(font)
        
        if os.name == 'nt':
            credits = wx.Button(self, id=wx.ID_ABOUT, label=_("C&redits"))
            license = wx.Button(self, label=_("&License"))
            sponsors = wx.Button(self, label=("&Sponsors"))
            close = wx.Button(self, id=wx.ID_CANCEL, label=_("&Close"))
        else:
            #Linux buttons must be a little bit bigger
            credits = wx.Button(self, id=wx.ID_ABOUT, label=_("C&redits"), size = wx.Size( -1,50 ))
            license = wx.Button(self, label=_("&License"), size = wx.Size( -1,50 ))
            sponsors = wx.Button(self, label=("&Sponsors"), size = wx.Size( -1,50 ))
            close = wx.Button(self, id=wx.ID_CANCEL, label=_("&Close"), size = wx.Size( -1,50 ))
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(credits, flag=wx.CENTER | wx.LEFT | wx.RIGHT, border=5)
        btnSizer.Add(license, flag=wx.CENTER | wx.RIGHT, border=5)
        btnSizer.Add(sponsors, flag=wx.CENTER | wx.RIGHT, border=5)
        btnSizer.Add(close, flag=wx.CENTER | wx.RIGHT, border=5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        if image:
            sizer.Add(image, flag=wx.CENTER | wx.TOP | wx.BOTTOM, border=5)
        sizer.Add(name, flag=wx.CENTER | wx.BOTTOM, border=10)
        sizer.Add(description, flag=wx.CENTER | wx.BOTTOM, border=10)
        sizer.Add(copyright, flag=wx.CENTER | wx.BOTTOM, border=10)
        sizer.Add(url, flag=wx.CENTER | wx.BOTTOM, border=15)
        sizer.Add(btnSizer, flag=wx.CENTER | wx.BOTTOM, border=5)

        container = wx.BoxSizer(wx.VERTICAL)
        container.Add(sizer, flag=wx.ALL, border=10)
        self.SetSizer(container)
        self.Layout()
        self.Fit()
        self.Centre()
        self.Show(True)
        self.SetEscapeId(close.GetId())

        credits.Bind(wx.EVT_BUTTON, self.on_credits)
        license.Bind(wx.EVT_BUTTON, self.on_license)
        sponsors.Bind(wx.EVT_BUTTON, self.on_sponsors)
        close.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())

    def on_license(self, event):
        LicenseDialog(self, self.info)

    def on_credits(self, event):
        CreditsDialog(self, self.info)
    
    def on_sponsors(self, event):
        SponsorsDialog(self)


class CreditsDialog(wx.Dialog):
    def __init__(self, parent, info):
        wx.Dialog.__init__(self, parent, title=_("Credits"), size=(475, 320),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        if parent and parent.GetIcon():
            self.SetIcon(parent.GetIcon())

        self.SetMinSize((300, 200))
        notebook = wx.Notebook(self)
        close = wx.Button(self, id=wx.ID_CLOSE, label=_("&Close"))
        close.SetDefault()

        developer = wx.TextCtrl(notebook, style=wx.TE_READONLY | wx.TE_MULTILINE)
        translators = wx.TextCtrl(notebook, style=wx.TE_READONLY | wx.TE_MULTILINE)

        developer.SetValue(u'\n'.join(info.Developers))
        translators.SetValue(u'\n'.join(info.Translators))

        notebook.AddPage(developer, text=_("Written by"))
        notebook.AddPage(translators, text=_("Translated by"))

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(close)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(btnSizer, flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
        self.SetEscapeId(close.GetId())

        close.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())


class LicenseDialog(wx.Dialog):
    def __init__(self, parent, info):
        wx.Dialog.__init__(self, parent, title=_("License"), size=(500, 400),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        if parent and parent.GetIcon():
            self.SetIcon(parent.GetIcon())

        self.SetMinSize((400, 300))
        close = wx.Button(self, id=wx.ID_CLOSE, label=_("&Close"))

        ctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)
        ctrl.SetValue(info.License)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(close)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ctrl, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(btnSizer, flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
        self.SetEscapeId(close.GetId())

        close.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())

class SponsorsDialog(wx.Dialog):
    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,440 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )

        bSizer3 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"OpenPLC Gold Sponsors", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTRE )
        self.m_staticText2.Wrap( -1 )
        self.m_staticText2.SetFont( wx.Font( 20, 74, 90, 92, False, "Arial Black" ) )

        bSizer3.Add( self.m_staticText2, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"You can enjoy a free and open source IEC 61131-3 programming environment thanks to the help and support of the following GOLD sponsors:", wx.DefaultPosition, wx.Size( 450,40 ), 0 )
        self.m_staticText3.Wrap( -1 )
        self.m_staticText3.SetFont( wx.Font( 10, 74, 90, 90, False, "Arial" ) )

        bSizer3.Add( self.m_staticText3, 0, wx.LEFT|wx.RIGHT, 20 )

        gSizer1 = wx.GridSizer( 0, 2, 0, 0 )

        self.m_bitmap1 = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap(os.path.join(current_dir, "..", "images", "sponsor_logos", "facts.png"), wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer1.Add( self.m_bitmap1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.m_bitmap2 = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap(os.path.join(current_dir, "..", "images", "sponsor_logos", "freewave.png"), wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer1.Add( self.m_bitmap2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.m_staticText4 = HyperLinkCtrl(self, label=u"https://facts-eng.com", URL="https://facts-eng.com")
        gSizer1.Add( self.m_staticText4, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_staticText5 = HyperLinkCtrl(self, label=u"https://www.freewave.com", URL="https://www.freewave.com")
        gSizer1.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        bSizer3.Add( gSizer1, 0, wx.EXPAND, 5 )

        self.m_staticText51 = wx.StaticText( self, wx.ID_ANY, u"If you are interested in becoming an official OpenPLC Sponsor, check out our Patreon page:", wx.DefaultPosition, wx.Size( 450,40 ), 0 )
        self.m_staticText51.Wrap( -1 )
        self.m_staticText51.SetFont( wx.Font( 10, 74, 90, 90, False, "Arial" ) )

        bSizer3.Add( self.m_staticText51, 0, wx.LEFT|wx.RIGHT, 20 )

        self.m_staticText6 = HyperLinkCtrl(self, label=u"https://www.patreon.com/openplc", URL="https://www.patreon.com/openplc")
        bSizer3.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.close_button = wx.Button( self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.close_button, 0, wx.ALIGN_RIGHT|wx.ALL, 10 )

        self.SetSizer( bSizer3 )
        self.Layout()
        self.Centre( wx.BOTH )
        self.Fit()
        self.Show()
        self.close_button.Bind(wx.EVT_BUTTON, lambda evt: self.Destroy())


def ShowAboutDialog(parent, info):
    #if os.name == "nt":
    AboutDialog(parent, info)
    #else:
    #    wx.AboutBox(info)
