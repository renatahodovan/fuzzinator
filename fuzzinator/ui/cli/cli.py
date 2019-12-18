# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import sys

from rainbow_logging_handler import RainbowLoggingHandler

from ... import Controller
from .. import build_parser, process_args
from .cli_listener import CliListener

root_logger = logging.getLogger()


def execute(args=None, parser=None):
    parser = build_parser(parent=parser)
    arguments = parser.parse_args(args)
    error_msg = process_args(arguments)
    if error_msg:
        parser.error(error_msg)

    if not root_logger.hasHandlers():
        root_logger.addHandler(RainbowLoggingHandler(sys.stdout))

    controller = Controller(config=arguments.config)
    controller.listener += CliListener()

    try:
        controller.run(max_cycles=arguments.max_cycles)
    except KeyboardInterrupt:
        Controller.kill_process_tree(os.getpid(), kill_root=False)
