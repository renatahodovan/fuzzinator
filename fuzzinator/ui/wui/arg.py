# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse


def add_arguments(parser):
    parser.add_argument('--bind-ip', metavar='NAME/IP', default='localhost',
                        help='hostname or IP address to start the service on (default: %(default)s)')
    parser.add_argument('--bind-ip-all', dest='bind_ip', action='store_const', const='', default=argparse.SUPPRESS,
                        help='bind service to all available addresses (alias for --bind-ip=%(const)r)')
    parser.add_argument('--port', metavar='NUM', default=8080, type=int,
                        help='port to start the service on (default: %(default)d)')
    parser.add_argument('--develop', action='store_true',
                        help='run the service in development mode')
