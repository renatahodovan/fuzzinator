# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
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
from .cli_listener import CliListener

root_logger = logging.getLogger()


def execute(arguments):
    if not root_logger.hasHandlers():
        root_logger.addHandler(RainbowLoggingHandler(sys.stdout))

    controller = Controller(config=arguments.config)
    controller.listener += CliListener()

    try:
        controller.run(max_cycles=arguments.max_cycles, validate=arguments.validate, reduce=arguments.reduce)
    except KeyboardInterrupt:
        Controller.kill_process_tree(os.getpid(), kill_root=False)
