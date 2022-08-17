#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz
# Copyright (C) 2021: Edouard TISSERANT
#
# See COPYING file for copyrights details.

# Based on Eelco Hoogendoorn stackoverflow answer about RingBuffer with numpy

import numpy as np


class RingBuffer(object):
    def __init__(self, width=None, size=131072, padding=None):
        self.size = size
        self.padding = size if padding is None else padding
        shape = (self.size+self.padding,)
        if width :
            shape += (width,)
        self.buffer = np.zeros(shape)
        self.cursor = 0

    def append(self, data):
        """this is an O(n) operation"""
        data = data[-self.size:]
        n = len(data)
        if self.size + self.padding - self.cursor < n:
            self.compact()
        self.buffer[self.cursor:][:n] = data
        self.cursor += n

    @property
    def count(self):
        return min(self.size, self.cursor)

    @property
    def view(self):
        """this is always an O(1) operation"""
        return self.buffer[max(0, self.cursor - self.size):][:self.count]

    def compact(self):
        """
        note: only when this function is called, is an O(size) performance hit incurred,
        and this cost is amortized over the whole padding space
        """
        print 'compacting'
        self.buffer[:self.count] = self.view
        self.cursor -= self.size

