# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import logging

from fuzzinator import __version__


def build_parser(parent=None):
    parser = argparse.ArgumentParser(description='Fuzzinator Random Testing Framework', parents=[parent])
    parser.add_argument('config', default=list(), nargs='*', help='config files describing the fuzz jobs to run (if no config is provided and TUI is enabled, then the framework starts in issue viewer mode)')
    parser.add_argument('-l', '--log-level', metavar='LEVEL', default=logging.INFO, help='set log level')
    parser.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    return parser
