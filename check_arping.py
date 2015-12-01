#!/usr/bin/python2
# -*- coding: utf-8 -*-
#~ Author: Silvio Knizek
#~ License: GPLv2
#~ Version: 1.0

import sys
import os
import argparse
from subprocess import Popen, PIPE


def main():
    """
    arpings a host:
    0:  all got well
    1:  connection is slow
    2:  no connection at all (or really slow)
    3:  something really bad happend
    
    """
    parser = argparse.ArgumentParser(description = "Check with arping\
        if HOST is alive.")
    parser.add_argument("-H",
        required = True,
        help = "the HOST to check",
        dest = "hostname",
        metavar = "<IP or URI>")
    parser.add_argument("-I",
        default = "eth0",
        help = "the interface to use (Default: eth0)",
        dest = "interface",
        metavar = "<interface>")
    parser.add_argument("-w",
        type = float,
        default = "2.0",
        help = "the WARNING time (Default: 2ms)",
        dest = "warning",
        metavar = "<msec>")
    parser.add_argument("-c",
        type = float,
        default = "5.0",
        help = "the CRITICAL time (Default: 5ms)",
        dest = "critical",
        metavar = "<msec>")
    args = parser.parse_args()

    try:
        arping = Popen(["arping", "-f", "-I", args.interface,
            "-w", str(args.critical), "-c", "1", args.hostname],
            stdout = PIPE, stderr = PIPE)
    except OSError:
        sys.stdout.write("arping not found!")
        sys.exit((3))

    exit_code = os.waitpid(arping.pid, 0)
    output = arping.communicate()
    
    if output[1]:
        sys.stdout.write(str(output[1]))
        sys.exit((3))

    try:
        time = str(output[0]).splitlines()
        time = time[1].split("  ", 1)[1]
        time = time.translate(None, 'ms')
    except IndexError:
        pass
    
    if exit_code[1] == 0:
        sys.stdout.write(str(output[0]))
        if float(time) >= float(args.warning):
            sys.exit((1))
        sys.exit((0))
    if exit_code[1] == 256:
        sys.stdout.write(str(output[0]))
        sys.exit((2))
    sys.stdout.write("Something got terrible wrong!")
    sys.exit((3))

if __name__ == '__main__':
    main()
