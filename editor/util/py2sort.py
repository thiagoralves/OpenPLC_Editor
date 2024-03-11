#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of OpenPLC Editor, an Integrated Development Environment for
# programming OpenPLC Runtime.
#
# Copyright (c) 2021 Thiago Alves (thiagoralves@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This code is made available on the understanding that it will not be
# used in safety-critical situations without a full and competent review.

"""
Since Python 3 list.sort() works a bit differently than Python 2, this function provides a similar functionality
to Python 2 sorting on Python 3.
"""



import itertools

def python2sort(x):
    it = iter(x)
    groups = [[next(it)]]
    for item in it:
        for group in groups:
            try:
                item < group[0]  # exception if not comparable
                group.append(item)
                break
            except TypeError:
                continue
        else:  # did not break, make new group
            groups.append([item])
    print(groups)  # for debugging
    return list(itertools.chain.from_iterable(sorted(group) for group in groups))
