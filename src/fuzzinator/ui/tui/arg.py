# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse


def add_arguments(parser):
    parser.add_argument('--force-encoding', metavar='NAME', default=None, choices=['utf-8', 'ascii'],
                        help='force text encoding used for TUI widgets (%(choices)s; default: autodetect)')
    parser.add_argument('--utf8', '--utf-8', dest='force_encoding', action='store_const', const='utf-8', default=argparse.SUPPRESS,
                        help='force UTF-8 encoding (alias for --force-encoding=%(const)s)')
    parser.add_argument('--log-file', metavar='FILE',
                        help='redirect stderr (instead of /dev/null; for debugging purposes)')
    parser.add_argument('-s', '--style', metavar='FILE',
                        help='alternative style file for TUI')
