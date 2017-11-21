#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4:shiftwidth=4:smarttab:expandtab:softtabstop=4:autoindent

import getopt
import sys
import os
from Config import Config


def parse_args(*argv):
    shrt_args = "hf:c:"
    long_args = ["help", "file=", "column="]

    try:
        opts, args = getopt.getopt(sys.argv[1:], shrt_args, long_args)
    except getopt.GetoptError:
        return False

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-f", "--file"):
            Config.stats_file = arg
        elif opt in ("-c", "--column"):
            try:
                arg = int(arg)
            except:
                print "need integer in column argument"
                usage()
                os._exit(0)

            if arg >= 0 and arg < 6:
                Config.sort = int(arg)
            else:
                usage()

def usage():
    message = """
Usage: {progname} [options]

    \t-h, --help: __________________ Displays the usage.
    \t-f, --file: __________________ stats file or http.
    \t-c, --column: ________________ sort on this column number - from 0 to 5.


    \t"--column 0" means no sort at all

    \tif no file is provided, the default will be:
    \t\t/run/scality/connectors/sfused/misc/stats_sfused

    Usage examples::
    {progname} -f 'http://127.0.0.1:35951/store/bizobj/DATA/0?ctl=bizobj_advanced_stats'
    {progname} -f /run/scality/connectors/sfused/misc/stats_sfused
    {progname} -c 2

""".format(progname=sys.argv[0])

    print message

    os._exit(0)



    print "{} [-h|--help] ".format(progname)

