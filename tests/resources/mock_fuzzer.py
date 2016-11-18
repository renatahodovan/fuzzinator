#!/usr/bin/env python3

# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import os
import shutil


def main():
    parser = argparse.ArgumentParser(description='Mock fuzzer that copies directory contents.')
    parser.add_argument('-i', metavar='DIR', default=os.getenv('IDIR'), help='source directory (default: IDIR environment variable)')
    parser.add_argument('-o', metavar='DIR', default=os.getenv('ODIR'), help='destination directory (default: ODIR environment variable)')
    args = parser.parse_args()

    if args.i is None or args.o is None:
        parser.error('both source and destination directories have to be specified, either with command line argments or through environment variables')

    os.makedirs(args.o, exist_ok=True)

    for root, dirs, files in os.walk(args.i):
        for f in files:
            shutil.copy(os.path.join(root, f), args.o)
        dirs[:] = []


if __name__ == '__main__':
    main()
