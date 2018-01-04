#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4:shiftwidth=4:smarttab:expandtab:softtabstop=4:autoindent

from Config import Config
from parse_args import parse_args
from ParseStats import ParseStats
from tc import TerminalController

import os
import sys
import time
import datetime as dt
import threading
import Queue
import signal
import math

import termios
TERMIOS = termios

term = TerminalController()

debug = False
if debug:
    logfile = open("/tmp/nasdk.py.log", "w")

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

    getkey_thread = threading.Thread(
        group=None,
        target=getkey,
        name="keythread"
    )
    getkey_thread.start()

    while True:
        queue = Queue.Queue()
        thread_ = threading.Thread(
            group=None,
            target=process,
            name="Thread1",
            args=(stats_before.columns, queue)
        )

        thread_.start()

        time.sleep(Config.timewait)
        stats_before.columns = queue.get()


def getkey():
    global Config
    while 1:
        c = _getkey()
        try:
            if c == "0":
                Config.sort = 0
            if c == "1":
                Config.sort = 1
            if c == "2":
                Config.sort = 2
            if c == "3":
                Config.sort = 3
            if c == "4":
                Config.sort = 4
            if c == "5":
                Config.sort = 5
        except Exception:
            import traceback
            mesg = "Generic Exception: {}".format(traceback.format_exc())
            print(mesg)
            os._exit(0)


def _getkey():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~TERMIOS.ICANON & ~TERMIOS.ECHO
    new[6][TERMIOS.VMIN] = 1
    new[6][TERMIOS.VTIME] = 0
    termios.tcsetattr(fd, TERMIOS.TCSANOW, new)
    c = None
    try:
        c = os.read(fd, 1)
    finally:
        termios.tcsetattr(fd, TERMIOS.TCSAFLUSH, old)
    return c


def process(previous_stats, queue):
    try:
        _process(previous_stats, queue)
    except Exception:
        import traceback
        mesg = "Generic Exception: {}".format(traceback.format_exc())
        print(mesg)
        os._exit(0)


def _process(previous_stats, queue):
    display_header()
    stats_current = ParseStats()
    stats_current.read_file()
    stats_current.parse()

    stats = compare_stats(previous_stats, stats_current.columns)
    stats = sort_stats(stats)
    display_stats(stats)

    text = place_text(term.LINES, 2, "Time: {0} / Sort Columns: {1}".format(dt.datetime.now(), Config.sort))
    sys.stdout.write(text)
    sys.stdout.flush()

    queue.put(stats_current.columns)


def sort_stats(stats):
    if Config.sort is 0:
        return stats
    else:
        return sorted(stats, key=lambda e: e[Config.sort], reverse=True)


def display_header():
    text = "{0:>{firstcol}}  {1:>{col1}}  {2:>{col2}}  {3:>{col3}}  {4:>{col4}}  {5:>{col5}}".format(
        "Name",
        "Cnt",
        "//",
        "Errs",
        "Latms",
        "bytes_sz",
        firstcol=Config.col_size[0],
        col1=Config.col_size[1],
        col2=Config.col_size[2],
        col3=Config.col_size[3],
        col4=Config.col_size[4],
        col5=Config.col_size[5]
    )

    # separator
    delimf = "{0}".format("#" * Config.col_size[0])
    delimg = "{0}".format("#" * Config.col)
    delim = "{0:{1}}  {2:>{3}}  {2:>{4}}  {2:>{5}}  {2:>{6}}  {2:>{7}}".format(
        delimf,
        Config.col_size[0],
        delimg,
        Config.col_size[1],
        Config.col_size[2],
        Config.col_size[3],
        Config.col_size[4],
        Config.col_size[5]
    )

    log("line 1 : header")
    headnames = place_text(1, 0, text)
    sys.stdout.write(headnames)

    log("line 2 : separator")
    separ = place_text(2, 0, "{0}".format(delim))
    sys.stdout.write(separ)

    sys.stdout.flush()


def display_bw(s):
    wps = (s[2] / 1e6)
    rps = (s[1] / 1e6)
    text = "READ: {reads:.{prec}f} MiB/s - WRITE: {writes:.{prec}f} MiB/s".format(writes=wps, reads=rps, prec=2)
    text = "{0:{align}{width}}".format(text, align='', width=term.COLS)
    text = place_text(3, 0, text)
    sys.stdout.write(text)
    sys.stdout.flush()


def display_stats(stats):
    # Let space for header + footer
    head_size = 4
    foot_size = 1

    place_cursor(head_size, 0)
    clear_seq = '{0}{0}'.format(term.CLEAR_EOL, term.CLEAR_BOL)

    sys.stdout.write(term.NORMAL)
    content_size = (term.LINES - (head_size + foot_size))
    log(stats)
    for i, v in enumerate(stats):
        if v[0] is "totalrw":
            display_bw(stats[i])
            continue

        # stop writing when screen is filled (header + footer)
        # Not a break because we still want to display the bandwidth
        if i >= content_size:
            continue

        sys.stdout.write(term.DOWN)
        log("line {0} : stats".format(head_size))
        text = ""

        for idx, val in enumerate(stats[i]):
            if idx == 0:
                text = "{0:>{col}}".format(
                    val,
                    col=Config.col_size[0]
                )
            else:
                if len(str(val))+1 > Config.col_size[idx]:
                    Config.col_size[idx] = len(str(val))+1
                text += "| {0:_>{col}}".format(
                    val,
                    col=Config.col_size[idx]
                )
        sys.stdout.write(clear_seq)
        sys.stdout.write(text)
    sys.stdout.flush()


def place_cursor(x, y):
    sys.stdout.write("\x1b7\x1b[{0:d};{1:d}H".format(x, y))


def place_text(x, y, text):
    # http://ascii-table.com/ansi-escape-sequences.php
    return("\x1b7\x1b[{0:d};{1:d}H{2}{3}{4}\x1b8".format(x, y, term.CLEAR_EOL, term.CLEAR_BOL, text[:term.COLS]))


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
            log("{0}".format(metricname))
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
    if signum in [1, 2, 3, 15]:
        place_cursor(term.LINES, 0)
        sys.stdout.write(term.SHOW_CURSOR)
        print('Caught signal %s, exiting.' % (str(signum)))
        os.system('stty sane')
        if debug:
            logfile.close()
        os._exit(0)
    else:
        print('Caught signal %s, ignoring.' % (str(signum)))


def log(text):
    if debug:
        logfile.write("{0}\n".format(text))


# Run the program
if __name__ == '__main__':
    signal.signal(signal.SIGINT, receive_signal)

    # run the main program
    Main(sys.argv[1:])
