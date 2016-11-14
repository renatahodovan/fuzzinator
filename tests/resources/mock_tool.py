#!/usr/bin/env python3

# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import os
import signal
import sys


def main():
    parser = argparse.ArgumentParser(description='Mock tool with control over its output & termination.')
    parser.add_argument('--print-args', action='store_true', default=False,
                        help='print the (non-option) arguments')
    parser.add_argument('--print-env', metavar='VAR', type=str, default=None,
                        help='print an environment variable')
    parser.add_argument('--echo-stdin', action='store_true', default=False,
                        help='echo the standard input')
    parser.add_argument('--to-stderr', action='store_true', default=False,
                        help='write to standard error instead of standard output')
    parser.add_argument('--crash', action='store_true', default=False,
                        help='crash process after output')
    parser.add_argument('--exit-code', metavar='N', type=int, default=0,
                        help='terminate process with given exit code (default: %(default)s)')
    parser.add_argument('args', nargs='*',
                        help='arbitrary command line arguments')
    args = parser.parse_args()

    out = sys.stderr if args.to_stderr else sys.stdout

    if args.print_args:
        for arg in args.args:
            print(arg, file=out, flush=True)

    if args.print_env is not None:
        print(os.getenv(args.print_env, ''), file=out, flush=True)

    if args.echo_stdin:
        for line in sys.stdin:
            print(line, file=out, end='', flush=True)

    if args.crash:
        os.kill(os.getpid(), signal.SIGSEGV)

    sys.exit(args.exit_code)


if __name__ == '__main__':
    main()
