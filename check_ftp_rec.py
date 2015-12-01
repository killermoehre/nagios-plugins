#!/usr/bin/python2
# -*- coding: utf-8 -*-
#~ Author: Silvio Knizek
#~ License: GPLv2
#~ Version: 1.0

import sys
import os.path
import argparse
import getpass
import socket
import ftplib

def dirlist_split(dir_list):
    filename = dir_list[0].split(None, 1)[1]
    dir_list = dir_list[0].split(None, 1)[0]    #~ remove filename
    dir_list = dir_list[:-1]                    #~ remove ';'
    dir_list = dict(part.split('=') for part in dir_list.split(';'))
    filetype = dir_list['type']
    try:
        filesize = dir_list['size']
    except KeyError:
        filesize = 0
    return filetype, filesize, filename

def humanize(data_size):
    if data_size >= 1099511627776:
        terabytes = data_size / 1099511627776.0
        data_size = "%.2fT" % terabytes
    elif data_size >= 1073741824:
        gigabytes = data_size / 1073741824.0
        data_size = "%.2fG" % gigabytes
    elif data_size >= 1048576:
        megabytes = data_size / 1048576.0
        data_size = "%.2fM" % megabytes
    elif data_size >= 1024:
        kilobytes = data_size / 1024.0
        data_size = "%.2fK" % kilobytes
    else:
        data_size = "%.2f" % data_size
    return data_size

def dehumanize(data_size):
    suffix = data_size[-1]
    size_string = ""
    try:
        float(suffix)
        for value in data_size:
            size_string += value
        return size_string
    except ValueError:
        pass
    data_size = data_size[:-1]
    for value in data_size:
        size_string += value
    data_size = float(size_string)
    if suffix == 'T':
        data_size *= 1099511627776.0
    elif suffix == 'G':
        data_size *= 1073741824.0
    elif suffix == 'M':
        data_size *= 1048576.0
    elif suffix == 'k':
        data_size *= 1024.0
    else:
        raise AttributeError('Not recognized suffix!')
    return data_size

def rec_search(dir_list, dir_name, dir_struct, data_size, data_count, connection):
    if dir_struct[-1] == 0:
        del dir_struct[-1]
        if not dir_struct:
            return({'size': data_size, 'count': data_count})
        else:
            connection.cwd("../")
            del dir_list
            dir_list = []
            connection.retrlines('MLSD', dir_list.append)
            del dir_list[0:int(len(dir_list) - int(dir_struct[-1]))]
    else:
        filetype = dirlist_split(dir_list)[0]
        if filetype == "cdir":
            del dir_list[0]
            dir_struct[-1] -= 1
        elif filetype == "pdir":
            del dir_list[0]
            dir_struct[-1] -= 1
        elif filetype == "file":
            data_size += int(dirlist_split(dir_list)[1])
            data_count += 1
            del dir_list[0]
            dir_struct[-1] -= 1
        elif filetype == "dir":
            dir_name = dirlist_split(dir_list)[2] #~ directory name
            connection.cwd(dir_name)
            dir_struct[-1] -= 1
            del dir_list
            dir_list = []
            connection.retrlines('MLSD', dir_list.append)
            dir_struct.append(len(dir_list))
    return rec_search(dir_list, dir_name, dir_struct, data_size, data_count, connection)

def main():
    sys.setrecursionlimit((10000))
    
    parser = argparse.ArgumentParser(description = "Check number and\
        size of a ftp directory recursivly.",
        epilog = "-w and -c accepts two numbers, the first is the file\
            size (maybe with suffix) and second is the file count.")
    parser.add_argument("-H",
        required = True,
        help = "the HOST to check",
        dest = "hostname",
        metavar = "<IP or URI>")
    parser.add_argument("-P",
        type = int,
        default = "21",
        help = "the PORT to connect (Default: 21)",
        dest = "port",
        metavar = "<port>")
    parser.add_argument("-u",
        default = "anonymous",
        help = "the USER to connect (Default: anonymous)",
        dest = "user_name",
        metavar = "<user name>")
    parser.add_argument("-p",
        default = "anonymous@",
        help = "the password to connect (Default: anonymous@)",
        dest = "password",
        metavar = "<password>")
    parser.add_argument("-r",
        default = "/",
        help = "the root directory (Default: /)",
        dest = "startdir",
        metavar = "<rootdir>")
    parser.add_argument("-s",
        default = False,
        action = "store_true",
        help = "should SSL be used?",
        dest = "ssl_enable")
    parser.add_argument("-w",
        required = True,
        nargs = 2,
        help = "the WARNING data size and data count (Default: 2G, 1024)",
        dest = "warning",
        metavar = "<number>")
    parser.add_argument("-c",
        required = True,
        nargs = 2,
        help = "the CRITICAL data size and data count (Default: 4G, 2048)",
        dest = "critical",
        metavar = "<number>")
    args = parser.parse_args()

    if args.ssl_enable:
        connection = ftplib.FTP_TLS()
    else:
        connection = ftplib.FTP()
    try:
        connection.connect(args.hostname, args.port)
    except socket.error, msg:
        sys.stdout.write(str(msg))
        sys.exit((3))
    try:
        connection.login(args.user_name, args.password)
    except ftplib.error_perm, msg:
        sys.stdout.write(str(msg))
        sys.exit((3))
    try:
        connection.cwd(args.startdir)
    except ftplib.error_perm, msg:
        sys.stdout.write(str(msg))
        sys.exit((3))

    data_size = 0.0
    data_count = 0
    dir_name = ""
    dir_struct = []
    dir_list = []
    connection.retrlines('MLSD', dir_list.append)
    connection.cwd(args.startdir)
    dir_struct.append(len(dir_list))
    try:
        data = rec_search(dir_list, args.startdir, dir_struct, float(data_size), int(data_count), connection)
    finally:
        try:
            connection.quit()
        finally:
            connection.close()

    try:
        warning_size = dehumanize(args.warning[0])
        critical_size = dehumanize(args.critical[0])
        warning_count = dehumanize(args.warning[1])
        critical_count = dehumanize(args.critical[1])
    except AttributeError, msg:
        sys.stdout.write(str(msg))
        sys.exit((3))
    if data['size'] >= critical_size or data['count'] >= int(critical_count):
        sys.stdout.write("Read " + str(humanize(data['size'])) + "b in " + str(data['count']) + " Files.")
        sys.exit((2))
    elif data['size'] >= warning_size or data['count'] >= int(warning_count):
        sys.stdout.write("Read " + str(humanize(data['size'])) + "b in " + str(data['count']) + " Files.")
        sys.exit((1))
    else:
        sys.stdout.write("Read " + str(humanize(data['size'])) + "b in " + str(data['count']) + " Files.")
        sys.exit((0))
    sys.stdout.write("Something really bad happend!")
    sys.exit((3))

if __name__ == '__main__':
    main()
