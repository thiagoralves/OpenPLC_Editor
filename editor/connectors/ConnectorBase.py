#!/usr/bin/env python
# -*- coding: utf-8 -*-

# See COPYING file for copyrights details.

from __future__ import absolute_import
import hashlib


class ConnectorBase(object):

    chuncksize = 1024*1024

    def BlobFromFile(self, filepath, seed):
        s = hashlib.new('md5')
        s.update(seed)
        blobID = self.SeedBlob(seed)
        with open(filepath, "rb") as f:
            while blobID == s.digest():
                chunk = f.read(self.chuncksize)
                if len(chunk) == 0:
                    return blobID
                blobID = self.AppendChunkToBlob(chunk, blobID)
                s.update(chunk)
