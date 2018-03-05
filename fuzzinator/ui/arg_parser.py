# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import configparser
import logging
import sys

from fuzzinator import __version__


def build_parser(parent=None):
    parser = argparse.ArgumentParser(description='Fuzzinator Random Testing Framework', fromfile_prefix_chars='@', parents=[parent])
    parser.add_argument('config', default=list(), nargs='*',
                        help='config files describing the fuzz jobs to run (if no config is provided and TUI is enabled, then the framework starts in issue viewer mode)')
    parser.add_argument('-l', '--log-level', metavar='LEVEL', default=logging.INFO,
                        help='set log level')
    parser.add_argument('-v', dest='log_level', action='store_const', const='DEBUG', default=argparse.SUPPRESS,
                        help='verbose mode (alias for -l %(const)s)')
    parser.add_argument('--sys-recursion-limit', metavar='NUM', type=int, default=sys.getrecursionlimit(),
                        help='override maximum depth of the Python interpreter stack (default: %(default)d)')
    parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    return parser


def process_args(args):
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation(),
                                       strict=False,
                                       allow_no_value=True)
    config.read(args.config)
    args.config = config

    logger = logging.getLogger('fuzzinator')
    logger.setLevel(args.log_level)

    sys.setrecursionlimit(args.sys_recursion_limit)
