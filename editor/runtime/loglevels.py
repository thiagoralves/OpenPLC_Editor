#!/usr/bin/env python
# -*- coding: utf-8 -*-

# See COPYING.Runtime file for copyrights details.

LogLevels = ["CRITICAL", "WARNING", "INFO", "DEBUG"]
LogLevelsCount = len(LogLevels)
LogLevelsDict = dict(zip(LogLevels, range(LogLevelsCount)))
LogLevelsDefault = LogLevelsDict["DEBUG"]
