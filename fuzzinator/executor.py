# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from argparse import ArgumentParser


def execute():
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--tui', action='store_true', default=False, help='start Fuzzinator with TUI')

    args, more_args = parser.parse_known_args()

    if args.tui:
        from .ui.tui import execute
        execute(args=more_args, parser=parser)
    else:
        from .ui.cli import execute
        execute(args=more_args, parser=parser)
