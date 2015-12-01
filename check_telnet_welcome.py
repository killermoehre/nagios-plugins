#!/usr/bin/python2
# -*- coding: utf-8 -*-
#~ Author: Silvio Knizek
#~ License: GPLv2
#~ Version: 1.0

import sys
import time
import argparse
from telnetlib import Telnet
import socket

def connection_telnet(hostname, port, sstring, timeout):
    """
    Connects to a socket, checks for the WELCOME-MSG and closes the
    connection.
    Returns nothing.
    
    """
    connection = Telnet()
    connection.open(hostname, port)
    connection.read_until(sstring, timeout)
    connection.close()


def main():
    """
    Parses the time it needs to got the WELCOME-MSG and returns:
    0:  all got well
    1:  connection is slow
    2:  no connection at all (or really slow)
    3:  something really bad happend
    
    """
    parser = argparse.ArgumentParser(description = "Check for returned \
        string")
    parser.add_argument("-H",
        required = True,
        help = "the HOST to check",
        dest = "hostname",
        metavar = "<IP or URI>")
    parser.add_argument("-P",
        type = int,
        choices = xrange(0, 65535),
        required = True,
        help = "the PORT to check",
        dest = "port",
        metavar = "<0 - 65535>")
    parser.add_argument("-s",
        required = True,
        help = "the STRING which has to be in the telnet output",
        dest = "sstring",
        metavar = "<search string>")
    parser.add_argument("-w",
        type = float,
        default = 1.0,
        help = "the WARNING time (Default: 1s)",
        dest = "warning",
        metavar = "<sec>")
    parser.add_argument("-c",
        type = float,
        default = 2.0,
        help = "the CRITICAL time (Default: 2s)",
        dest = "critical",
        metavar = "<sec>")
    args = parser.parse_args()

    start = time.time()
    try:
        connection_telnet(args.hostname, args.port, args.sstring,
            args.critical)
    except socket.error, (value, message):
        sys.stdout.write("Could not open socket: " + message + " " + 
        "(" + str(value) + ")")
        sys.exit((2))
    end = time.time()
    time_delta = end - start

    if time_delta >= args.critical:
        sys.stdout.write("Timed out or string not found!")
        sys.exit((2))
    elif time_delta >= args.warning:
        sys.stdout.write("Host responded on port " + str(args.port) +
            " after " + str(round(time_delta, int((2)))) + " seconds.")
        sys.exit((1))
    else:
        sys.stdout.write("Host responded on port " + str(args.port) +
            " after " + str(round(time_delta, int((2)))) + " seconds.")
        sys.exit((0))

    sys.stdout.write("Something got terrible wrong!")
    sys.exit((3))

if __name__ == '__main__':
    main()
