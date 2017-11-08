#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4:shiftwidth=4:smarttab:expandtab:softtabstop=4:autoindent

import os
import sys
import time
import datetime as dt
import os
import pprint
import threading
import Queue
import signal

from Config import Config
from parse_args import parse_args
from ParseStats import ParseStats
from tc import TerminalController

term = TerminalController()

def Main(*argv):

    parse_args(*argv)

    stats_before = ParseStats()
    stats_before.read_file()
    stats_before.parse()
    stats_before.get_max_size()

    sys.stdout.write(term.CLEAR_SCREEN)
    for i in range(term.LINES):
        sys.stdout.write(term.DOWN)
    sys.stdout.write(term.HIDE_CURSOR)
    sys.stdout.flush()

    while True:
        queue = Queue.Queue()
        thread_ = threading.Thread(
            group=None,
            target=process,
            name="Thread1",
            args=(stats_before.columns, queue),
        )

        thread_.start()
        time.sleep(1)
        stats_before.columns = queue.get()
        

def process(previous_stats, queue):
    try:
        _process(previous_stats, queue)
    except Exception:
        import traceback
        print 'generic exception: ' + traceback.format_exc()
        os._exit(0)

def _process(previous_stats, queue):
    display_header()
    stats_current = ParseStats()
    stats_current.read_file()
    stats_current.parse()

    stats = compare_stats(previous_stats, stats_current.columns)
    stats = sort_stats(stats)
    display_stats(stats)

    text = place_text(term.LINES, 2, "Time: {}".format(dt.datetime.now()))
    sys.stdout.write(text)
    sys.stdout.flush()

    queue.put(stats_current.columns)


def sort_stats(stats):
    return sorted(stats, key=lambda e: e[Config.sort], reverse=True)


def display_header():
    text = "{:{firstcol}} {:>{col}} {:>{col}} {:>{col}} {:>{col}} {:>{col}}".format(
        "metric",
        "Count",
        "Parallel",
        "Errors",
        "Latency(ms)",
        "Size(bytes)",
        firstcol=Config.operation_size,
        col=Config.col
    )

    # separator
    delim = "{}".format("#" * Config.operation_size)
    delim = "{0:{1}} {0:.{2}} {0:.{2}} {0:.{2}} {0:.{2}} {0:.{2}}".format(
        delim,
        Config.operation_size,
        Config.col
    )


    headnames = place_text(1, 0, text)
    sys.stdout.write(headnames)

    separ = place_text(2, 0, "{}".format(delim))
    sys.stdout.write(separ)

    sys.stdout.flush()


def display_bw(s):
    wps = (s[2] / 1e6)
    rps = (s[1] / 1e6)
    text = "READ: {reads:.{prec}f} MiB/s - WRITE: {writes:.{prec}f} MiB/s".format(writes=wps, reads=rps, prec=2)
    text = "{:{align}{width}}".format(text, align='^', width=term.COLS)
    text = place_text(3, 2, text)
    sys.stdout.write(text)
    sys.stdout.flush()


def display_stats(stats):
    # Let space for header + footer
    head_size = 4
    foot_size = 1

    place_cursor(head_size, 0)
    clear_seq = '{}{}'.format(term.CLEAR_EOL, term.CLEAR_BOL)

    for i, v in enumerate(stats):
        # stop writing when screen is filled (header + footer)
        if i >= (term.LINES - (head_size + foot_size)):
           return True
        
        if v[0] is "totalrw":
            display_bw(stats[i])
            continue

        sys.stdout.write(term.DOWN)
        text = ""
        for idx, val in enumerate(stats[i]):
            if idx == 0:
                text = "{:{col}}".format(val, col=Config.operation_size)
            else:
                text += " {:>{col}}".format(val, col=Config.col)
        # text = place_text( (i + head_size), 0, text)
        sys.stdout.write(clear_seq)
        sys.stdout.write(text)
    sys.stdout.flush()


def place_cursor(x, y):
    sys.stdout.write("\x1b7\x1b[{:d};{:d}H".format(x, y))


def place_text(x, y, text):
    # http://ascii-table.com/ansi-escape-sequences.php
    return("\x1b7\x1b[{:d};{:d}H{}{}{}\x1b8".format(x, y, term.CLEAR_EOL, term.CLEAR_BOL, text[:term.COLS]))


def compare_stats(da, db):
    dc = []
    for elem, val in enumerate(da):
        mydict = []
        # columns are in order (except for total_rw):
        # 0. metricname
        # 1. count
        # 2. //
        # 3. max//
        # 4. errors
        # 5. avg(ms)
        # 6. slowest
        # 7. total_ms
        # 8. total_bytes
        # 9. total_sq_ms

        # we output with:
        # 0. metricname
        # 1. count
        # 2. parall
        # 3. errors
        # 4. latency
        # 5. size

        metricname = db[elem][0]
        if metricname is "totalrw":
            mydict = [
                metricname,
                (db[elem][1] - da[elem][1]),
                (db[elem][2] - da[elem][2]),
                0,
                0,
                0
            ]
            dc.append(mydict)
            continue

        count = (db[elem][1] - da[elem][1])
        parall = db[elem][2]
        errors = (db[elem][4] - da[elem][4])
        tm = (db[elem][7] - da[elem][7])
        vol = (db[elem][8] - da[elem][8])
        latency = (tm / count) if count > 0 else 0
        size = (vol / count) if count > 0 else 0

        mydict = [
            metricname,
            count,
            parall,
            errors,
            latency,
            size
        ]
        dc.append(mydict)
    return dc


def receive_signal(signum, stack):
    if signum in [1,2,3,15]:
        place_cursor(term.LINES, 0)
        sys.stdout.write(term.SHOW_CURSOR)
        print 'Caught signal %s, exiting.' %(str(signum))
        os._exit(0)
    else:
        print 'Caught signal %s, ignoring.' %(str(signum))

 
# Run the program
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)

    # run the main program
    Main(sys.argv[1:])

