#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4:shiftwidth=4:smarttab:expandtab:softtabstop=4:autoindent

import string
import re
import pprint
import sys
import os
import urllib2
from Config import Config


class ParseStats(object):
    def __init__(self):
        self.columns = []
    	self.discard_lines = ["timestamp:", "total", "for", "operation"]
        self.stats = []

    def parse(self):
        subsection = 0
        for line in self.stats:
            if line == "":
                continue

            spline = re.split('\s+', line.strip())

            if spline[0] in "timestamp:":
                subsection += 1
            if subsection < Config.subsection:
                continue

            if spline[0] in self.discard_lines:
                continue

            if spline[1] == "<" or spline[1] == ">=":
                continue

            if spline[0] in "Total":
                # need to keep the same number of column because i'm lazy
                self.columns.append(["totalrw", int(spline[2]), int(spline[4]), 0, 0, 0, 0, 0, 0, 0])
                continue

            mydict = []
            for key, val in enumerate(spline):
                if key == 0:
                    d = val
                else:
                    try:
                        d = int(val)
                    except:
                        d = 0

                mydict.append(d)
            while len(mydict) < 9:
                mydict.append(0)

            self.columns.append(mydict)


    def read_file(self):
        if Config.stats_file.startswith('http'):
            try:
                request_headers = {"Accept" : "text/plain"}
                request = urllib2.Request(Config.stats_file, headers=request_headers)
                file = urllib2.urlopen(request)
                for line in file:
                    self.stats.append(line.strip("\n"))
                file.close()
            except urllib2.HTTPError as err:
                print err
                os._exit(1)
            except urllib2.URLError as err:
                print err
                os._exit(1)
            except Exception:
                import traceback
                print 'generic exception: ' + traceback.format_exc()
                os._exit(1)
        else:
            try:
                file = open(Config.stats_file, "r")
                for line in file:
                    self.stats.append(line.strip("\n"))
                file.close()
            except IOError as err:
                print "Error: Unable to open {} - {}.".format(Config.stats_file, err)
                os._exit(1)


    def get_max_size(self):
        for i, v in enumerate(self.columns):
            if len(v[0]) > Config.col_size[0]:
                Config.col_size[0] = len(v[0])

