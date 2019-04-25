# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
# Copyright (c) 2019 Tamas Keri.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from argparse import ArgumentParser


def execute():
    parser = ArgumentParser(add_help=False)
    ui_group = parser.add_mutually_exclusive_group()
    ui_group.add_argument('--tui', action='store_true', default=False, help='start Fuzzinator with TUI')
    ui_group.add_argument('--wui', action='store_true', default=False, help='start Fuzzinator with WUI')

    args, more_args = parser.parse_known_args()

    if args.tui:
        from .ui import tui
        tui.execute(args=more_args, parser=parser)
    elif args.wui:
        from .ui import wui
        wui.execute(args=more_args, parser=parser)
    else:
        from .ui import cli
        cli.execute(args=more_args, parser=parser)
