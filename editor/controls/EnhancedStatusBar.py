# --------------------------------------------------------------------------- #
# ENHANCEDSTATUSBAR wxPython IMPLEMENTATION
# Python Code By:
#
# Andrea Gavana, @ 31 May 2005
# Nitro, @ 21 September 2005
# Latest Revision: 21 September 2005, 19.57.20 GMT+2
# Latest Revision before Latest Revision: 21 September 2005, 18.29.35 GMT+2
# Latest Revision before Latest Revision before Latest Revision: 31 May 2005, 23.17 CET
#
#
# TODO List/Caveats
#
# 1. Some Requests/Features To Add?
#
#
# For All Kind Of Problems, Requests Of Enhancements And Bug Reports, Please
# Write To Me At:
#
#
# andrea.gavana@agip.it
# andrea_gavan@tin.it
#
# Or, Obviously, To The wxPython Mailing List!!!
#
#
# licensed under wxWidgets License (GPL compatible)
# End Of Comments
# --------------------------------------------------------------------------- #

""" Description:

EnhancedStatusBar Is A Slight Modification (Actually A Subclassing) Of wx.StatusBar.
It Allows You To Add Almost Any Widget You Like To The wx.StatusBar Of Your Main
Frame Application And Also To Layout Them Properly.


What It Can Do:

1) Almost All The Functionalities Of wx.StatusBar Are Still Present;
2) You Can Add Different Kind Of Widgets Into Every Field Of The EnhancedStatusBar;
3) The AddWidget() Methods Accepts 2 Layout Inputs:
   - horizontalalignment: This Specify The Horizontal Alignment For Your Widget,
     And Can Be ESB_EXACT_FIT, ESB_ALIGN_CENTER_HORIZONTAL, ESB_ALIGN_LEFT And
     ESB_ALIGN_RIGHT;
   - varticalalignment: This Specify The Vertical Alignment For Your Widget,
     And Can Be ESB_EXACT_FIT, ESB_ALIGN_CENTER_VERTICAL, ESB_ALIGN_BOTTOM And
     ESB_ALIGN_LEFT;

EnhancedStatusBar Is Freeware And Distributed Under The wxPython License.

Latest Revision: 21 September 2005, 19.57.20 GMT+2
Latest Revision before Latest Revision: 21 September 2005, 18.29.35 GMT+2
Latest Revision before Latest Revision before Latest Revision: 31 May 2005, 23.17 CET

"""

from __future__ import absolute_import
from __future__ import division
import wx

# Horizontal Alignment Constants
ESB_ALIGN_CENTER_VERTICAL = 1
ESB_ALIGN_TOP = 2
ESB_ALIGN_BOTTOM = 3

# Vertical Alignment Constants
ESB_ALIGN_CENTER_HORIZONTAL = 11
ESB_ALIGN_LEFT = 12
ESB_ALIGN_RIGHT = 13

# Exact Fit (Either Horizontal Or Vertical Or Both) Constant
ESB_EXACT_FIT = 20


# ---------------------------------------------------------------
# Class EnhancedStatusBar
# ---------------------------------------------------------------
# This Is The Main Class Implementation. See The Demo For Details
# ---------------------------------------------------------------
class EnhancedStatusBarItem(object):
    def __init__(self, widget, pos, horizontalalignment=ESB_ALIGN_CENTER_HORIZONTAL, verticalalignment=ESB_ALIGN_CENTER_VERTICAL):
        self.__dict__.update(locals())


class EnhancedStatusBar(wx.StatusBar):

    def __init__(self, parent, id=wx.ID_ANY, style=wx.ST_SIZEGRIP,
                 name="EnhancedStatusBar"):
        """Default Class Constructor.

        EnhancedStatusBar.__init__(self, parent, id=wx.ID_ANY,
                                   style=wx.ST_SIZEGRIP,
                                   name="EnhancedStatusBar")
        """

        wx.StatusBar.__init__(self, parent, id, style, name)

        self._items = {}
        self._curPos = 0
        self._parent = parent

        wx.EVT_SIZE(self, self.OnSize)
        wx.CallAfter(self.OnSize, None)

    def OnSize(self, event):
        """Handles The wx.EVT_SIZE Events For The StatusBar.

        Actually, All The Calculations Linked To HorizontalAlignment And
        VerticalAlignment Are Done In This Function."""

        for pos, item in self._items.items():
            widget, horizontalalignment, verticalalignment = item.widget, item.horizontalalignment, item.verticalalignment

            rect = self.GetFieldRect(pos)
            widgetsize = widget.GetSize()

            rect = self.GetFieldRect(pos)

            if horizontalalignment == ESB_EXACT_FIT:

                if verticalalignment == ESB_EXACT_FIT:
                    # 1 September 2015 Fix fit align
                    widget.SetSize((rect.width-4, rect.height-4))
                    widget.SetPosition((rect.x+2, rect.y+2))
                elif verticalalignment == ESB_ALIGN_CENTER_VERTICAL:
                    if widgetsize[1] < rect.width - 1:
                        diffs = (rect.height - widgetsize[1])/2
                        widget.SetSize((rect.width-2, widgetsize[1]))
                        widget.SetPosition((rect.x-1, rect.y+diffs))
                    else:
                        widget.SetSize((rect.width-2, widgetsize[1]))
                        widget.SetPosition((rect.x-1, rect.y-1))
                elif verticalalignment == ESB_ALIGN_TOP:
                    widget.SetSize((rect.width-2, widgetsize[1]))
                    widget.SetPosition((rect.x-1, rect.y))
                elif verticalalignment == ESB_ALIGN_BOTTOM:
                    widget.SetSize((rect.width-2, widgetsize[1]))
                    widget.SetPosition((rect.x-1, rect.height-widgetsize[1]))

            elif horizontalalignment == ESB_ALIGN_LEFT:

                xpos = rect.x - 1
                if verticalalignment == ESB_EXACT_FIT:
                    widget.SetSize((widgetsize[0], rect.height-2))
                    widget.SetPosition((xpos, rect.y-1))
                elif verticalalignment == ESB_ALIGN_CENTER_VERTICAL:
                    if widgetsize[1] < rect.height - 1:
                        diffs = (rect.height - widgetsize[1]) // 2
                        widget.SetPosition((xpos, rect.y+diffs))
                    else:
                        widget.SetSize((widgetsize[0], rect.height-2))
                        widget.SetPosition((xpos, rect.y-1))
                elif verticalalignment == ESB_ALIGN_TOP:
                    widget.SetPosition((xpos, rect.y))
                elif verticalalignment == ESB_ALIGN_BOTTOM:
                    widget.SetPosition((xpos, rect.height-widgetsize[1]))

            elif horizontalalignment == ESB_ALIGN_RIGHT:

                xpos = rect.x + rect.width - widgetsize[0] - 1
                if verticalalignment == ESB_EXACT_FIT:
                    widget.SetSize((widgetsize[0], rect.height-2))
                    widget.SetPosition((xpos, rect.y-1))
                elif verticalalignment == ESB_ALIGN_CENTER_VERTICAL:
                    if widgetsize[1] < rect.height - 1:
                        diffs = (rect.height - widgetsize[1]) // 2
                        widget.SetPosition((xpos, rect.y+diffs))
                    else:
                        widget.SetSize((widgetsize[0], rect.height-2))
                        widget.SetPosition((xpos, rect.y-1))
                elif verticalalignment == ESB_ALIGN_TOP:
                    widget.SetPosition((xpos, rect.y))
                elif verticalalignment == ESB_ALIGN_BOTTOM:
                    widget.SetPosition((xpos, rect.height-widgetsize[1]))

            elif horizontalalignment == ESB_ALIGN_CENTER_HORIZONTAL:

                xpos = rect.x + (rect.width - widgetsize[0]) // 2 - 1
                if verticalalignment == ESB_EXACT_FIT:
                    widget.SetSize((widgetsize[0], rect.height))
                    widget.SetPosition((xpos, rect.y))
                elif verticalalignment == ESB_ALIGN_CENTER_VERTICAL:
                    if widgetsize[1] < rect.height - 1:
                        diffs = (rect.height - widgetsize[1]) // 2
                        widget.SetPosition((xpos, rect.y+diffs))
                    else:
                        widget.SetSize((widgetsize[0], rect.height-1))
                        widget.SetPosition((xpos, rect.y+1))
                elif verticalalignment == ESB_ALIGN_TOP:
                    widget.SetPosition((xpos, rect.y))
                elif verticalalignment == ESB_ALIGN_BOTTOM:
                    widget.SetPosition((xpos, rect.height-widgetsize[1]))

        if event is not None:
            event.Skip()

    def AddWidget(self, widget, horizontalalignment=ESB_ALIGN_CENTER_HORIZONTAL,
                  verticalalignment=ESB_ALIGN_CENTER_VERTICAL, pos=-1):
        """Add A Widget To The EnhancedStatusBar.

        Parameters:

        - horizontalalignment: This Can Be One Of:
          a) ESB_EXACT_FIT: The Widget Will Fit Horizontally The StatusBar Field Width;
          b) ESB_ALIGN_CENTER_HORIZONTAL: The Widget Will Be Centered Horizontally In
             The StatusBar Field;
          c) ESB_ALIGN_LEFT: The Widget Will Be Left Aligned In The StatusBar Field;
          d) ESB_ALIGN_RIGHT: The Widget Will Be Right Aligned In The StatusBar Field;

        - verticalalignment:
          a) ESB_EXACT_FIT: The Widget Will Fit Vertically The StatusBar Field Height;
          b) ESB_ALIGN_CENTER_VERTICAL: The Widget Will Be Centered Vertically In
             The StatusBar Field;
          c) ESB_ALIGN_BOTTOM: The Widget Will Be Bottom Aligned In The StatusBar Field;
          d) ESB_ALIGN_TOP: The Widget Will Be TOP Aligned In The StatusBar Field;

        """

        if pos == -1:
            pos = self._curPos
            self._curPos += 1

        if self.GetFieldsCount() <= pos:
            raise ValueError("\nERROR: EnhancedStatusBar has a max of %d items, you tried to set item #%d" %
                             (self.GetFieldsCount(), pos))

        if horizontalalignment not in [ESB_ALIGN_CENTER_HORIZONTAL, ESB_EXACT_FIT,
                                       ESB_ALIGN_LEFT, ESB_ALIGN_RIGHT]:
            raise ValueError('\nERROR: Parameter "horizontalalignment" Should Be One Of '
                             '"ESB_ALIGN_CENTER_HORIZONTAL", "ESB_ALIGN_LEFT", "ESB_ALIGN_RIGHT"'
                             '"ESB_EXACT_FIT"')

        if verticalalignment not in [ESB_ALIGN_CENTER_VERTICAL, ESB_EXACT_FIT,
                                     ESB_ALIGN_TOP, ESB_ALIGN_BOTTOM]:
            raise ValueError('\nERROR: Parameter "verticalalignment" Should Be One Of '
                             '"ESB_ALIGN_CENTER_VERTICAL", "ESB_ALIGN_TOP", "ESB_ALIGN_BOTTOM"'
                             '"ESB_EXACT_FIT"')

        try:
            self.RemoveChild(self._items[pos].widget)
            self._items[pos].widget.Destroy()
        except KeyError:
            pass

        self._items[pos] = EnhancedStatusBarItem(widget, pos, horizontalalignment, verticalalignment)

        wx.CallAfter(self.OnSize, None)
