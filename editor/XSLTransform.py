#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Beremiz.
# See COPYING file for copyrights details.


from lxml import etree

class XSLTransform(object):
    """ a class to handle XSLT queries on project and libs """
    def __init__(self, xsltpath, xsltext):

        # parse and compile. "beremiz" arbitrary namespace for extensions
        self.xslt = etree.XSLT(
            etree.parse(
                xsltpath,
                etree.XMLParser()),
            extensions={("beremiz", name): call for name, call in xsltext})

    def transform(self, root, profile_run=False, **kwargs):
        res = self.xslt(root, profile_run=profile_run, **{k: etree.XSLT.strparam(v) for k, v in kwargs.items()})
        # print(self.xslt.error_log)
        return res

    def get_error_log(self):
        return self.xslt.error_log


