# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import configparser
import logging
import re
import sys

from ..pkgdata import __version__


def build_parser(parent=None):
    parser = argparse.ArgumentParser(description='Fuzzinator Random Testing Framework', fromfile_prefix_chars='@', parents=[parent])
    parser.add_argument('config', default=list(), nargs='*',
                        help='config files describing the fuzz jobs to run (if no config is provided and TUI is enabled, then the framework starts in issue viewer mode)')
    parser.add_argument('-D', metavar='SECT:OPT=VAL', dest='defines', default=list(), action='append',
                        help='define additional config options')
    parser.add_argument('-U', metavar='SECT[:OPT]', dest='undefs', default=list(), action='append',
                        help='undefine config sections or options')
    parser.add_argument('--show-config', action='store_true',
                        help='show complete config')
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

    parsed_fn = config.read(args.config)
    if len(parsed_fn) != len(args.config):
        return 'Config file(s) do(es) not exist: {fn}'.format(fn=', '.join(fn for fn in args.config if fn not in parsed_fn))

    for define in args.defines:
        parts = re.fullmatch('([^:=]*):([^:=]*)=(.*)', define)
        if not parts:
            return 'Config option definition not in SECT:OPT=VAL format: {d}'.format(d=define)

        section, option, value = parts.group(1, 2, 3)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, value)

    for undef in args.undefs:
        parts = re.fullmatch('([^:=]*)(:([^:=]*))?', undef)
        if not parts:
            return 'Config section/option undefinition not in SECT[:OPT] format: {u}'.format(u=undef)

        section, option = parts.group(1, 3)
        if option is None:
            config.remove_section(section)
        elif config.has_section(section):
            config.remove_option(section, option)

    if args.show_config:
        config.write(sys.stdout)

    args.config = config

    logger = logging.getLogger()
    logger.setLevel(args.log_level)

    sys.setrecursionlimit(args.sys_recursion_limit)
