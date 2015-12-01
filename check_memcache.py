#!/usr/bin/python2
#  check_memcache.py
#
#  Copyright 2012 Silvio Knizek <sknizek@cyberport.de>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import sys
import time
import argparse
import memcache

def argument_parser():
    parser = argparse.ArgumentParser(description='Check the specified \
        memcached.')
    parser.add_argument('-H',
        help = 'the host to query (Default: localhost)',
        dest = 'host',
        type = str,
        default = 'localhost'
        )
    parser.add_argument('-p',
        help = 'the port at the host (Default: 11211)',
        dest = 'port',
        type = int,
        default = 11211
        )
    parser.add_argument('-w',
        help = 'the time after WARNING is thrown (Default: 1s)',
        dest = 'warning',
        type = int,
        default = 1
        )
    parser.add_argument('-c',
        help = 'the time after CRITICAL is thrown (Default: 3s)',
        dest = 'critical',
        type = int,
        default = 3
        )
    return parser.parse_args()

def main():
    args = argument_parser()
    start_time = time.time()
    mc = memcache.Client([args.host + ":" + str(args.port)])
    try:
        stats = mc.get_stats()[0][1]
    except memcache._ConnectionDeadError:
        sys.stdout.write("Connection died during reading!")
        sys.exit((2))
    except IndexError:
        sys.stdout.write("Couldn't connect to host!")
        sys.exit((2))
    except:
        sys.stdout.write("Unexpected error: " + str(sys.exc_info()[0]))
        sys.exit((2))
    used_time = round(time.time() - start_time, 3)
    total_hits = float(stats['get_hits'])
    total_connections = total_hits + float(stats['get_misses'])
    perf = ""
    for key in stats:
        perf += str(key) + "=" + str(stats[key]) + ", "
    perf = perf[:-2] #remove trailing ", "
    if (total_hits == 0) or (total_connections == 0):
        hitrate = 0
    else:
        hitrate = round(total_hits / total_connections * 100, 2)

    memcache_stat = "Memcached OK"
    exit_value = 0
    if used_time >= args.critical:
        memcache_stat = "Memcached CRITICAL"
        exit_value = 2
    if used_time >= args.warning:
        memcache_stat = "Memcached WARNING"
        exit_value = 1
    sys.stdout.write(memcache_stat + " - " + str(used_time) + "s - Hitrate: " \
        + str(hitrate) + "%" + " | " + perf)
    sys.exit((exit_value))

if __name__ == '__main__':
    main()
    sys.stdout.write("Something really bad happend!")
    sys.exit((3))
