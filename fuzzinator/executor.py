# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
# Copyright (c) 2019 Tamas Keri.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import configparser
import logging
import os
import re
import sys

import inators

from .pkgdata import __version__

root_logger = logging.getLogger()


def process_args(args):
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation(),
                                       strict=False,
                                       allow_no_value=True)

    config.read_dict({
        'fuzzinator': {
            'work_dir': os.path.join('~', '.fuzzinator', '{uid}'),
            'cost_budget': str(os.cpu_count()),
            'validate_after_update': 'False',
            'db_uri': 'mongodb://localhost/fuzzinator',
            'db_server_selection_timeout': '30000',
        }
    })

    parsed_fn = config.read(args.config)
    if len(parsed_fn) != len(args.config):
        return f'Config file(s) do(es) not exist: {", ".join(fn for fn in args.config if fn not in parsed_fn)}'

    for define in args.defines:
        parts = re.fullmatch('([^:=]*):([^:=]*)=(.*)', define)
        if not parts:
            return f'Config option definition not in SECT:OPT=VAL format: {define}'

        section, option, value = parts.group(1, 2, 3)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, value)

    for undef in args.undefs:
        parts = re.fullmatch('([^:=]*)(:([^:=]*))?', undef)
        if not parts:
            return f'Config section/option undefinition not in SECT[:OPT] format: {undef}'

        section, option = parts.group(1, 3)
        if option is None:
            config.remove_section(section)
        elif config.has_section(section):
            config.remove_option(section, option)

    if args.show_config:
        config.write(sys.stdout)

    args.config = config

    inators.arg.process_log_level_argument(args, root_logger)
    # Force chatty third-party libraries to report at least on INFO level.
    log_level_chatty = max(inators.log.levels[args.log_level], inators.log.INFO)
    for logger_name in ('asyncio', 'chardet.charsetprober', 'keyring.backend'):
        logging.getLogger(logger_name).setLevel(log_level_chatty)
    inators.arg.process_sys_recursion_limit_argument(args)

    return None


def execute():
    pre_parser = argparse.ArgumentParser(add_help=False)
    ui_group = pre_parser.add_mutually_exclusive_group()
    ui_group.add_argument('--tui', action='store_true', default=False, help='start Fuzzinator with TUI')
    ui_group.add_argument('--wui', action='store_true', default=False, help='start Fuzzinator with WUI')
    pre_args, more_args = pre_parser.parse_known_args()

    if pre_args.tui:
        from .ui import tui as ui
    elif pre_args.wui:
        from .ui import wui as ui
    else:
        from .ui import cli as ui

    parser = argparse.ArgumentParser(description='Fuzzinator Random Testing Framework', fromfile_prefix_chars='@', parents=[pre_parser])
    parser.add_argument('config', default=[], nargs='*',
                        help='config files describing the fuzz jobs to run (if no config is provided and TUI is enabled, then the framework starts in issue viewer mode)')
    parser.add_argument('-D', metavar='SECT:OPT=VAL', dest='defines', default=[], action='append',
                        help='define additional config options')
    parser.add_argument('-U', metavar='SECT[:OPT]', dest='undefs', default=[], action='append',
                        help='undefine config sections or options')
    parser.add_argument('--max-cycles', metavar='N', default=None, type=int,
                        help='limit number of fuzz job cycles to %(metavar)s (default: no limit)')
    parser.add_argument('--validate', metavar='NAME',
                        help='validate issues of SUT before running any fuzz jobs')
    parser.add_argument('--validate-all', dest='validate', action='store_const', const='', default=argparse.SUPPRESS,
                        help='validate issues of all SUTs before running any fuzz jobs (alias for --validate=%(const)r)')
    parser.add_argument('--reduce', metavar='NAME',
                        help='reduce issues of SUT before running any fuzz jobs')
    parser.add_argument('--reduce-all', dest='reduce', action='store_const', const='', default=argparse.SUPPRESS,
                        help='reduce issues of all SUTs before running any fuzz jobs (alias for --reduce=%(const)r)')
    parser.add_argument('--show-config', action='store_true',
                        help='show complete config')
    inators.arg.add_log_level_argument(parser)
    inators.arg.add_sys_recursion_limit_argument(parser)
    inators.arg.add_version_argument(parser, version=__version__)
    ui.add_arguments(parser)
    args = parser.parse_args(more_args)

    error_msg = process_args(args)
    if error_msg:
        parser.error(error_msg)

    ui.execute(args)
