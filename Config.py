#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4:shiftwidth=4:smarttab:expandtab:softtabstop=4:autoindent


class _Config(object):
    def __init__(self):
        self.stats_file = "/run/scality/connectors/sfused/misc/stats_sfused"
        self.subsection = 1

        self.sort = 1  # column number
        self.col = 4
        self.cols = 60
        self.rows = 130
        self.bwread = 0
        self.bwwrit = 0
        self.timewait = 1
        self.col_size = [10, 5, 5, 5, 5, 5]  # default size of the columns, in order

Config = _Config()
