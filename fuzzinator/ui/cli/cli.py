# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import configparser
import logging
import sys

from rainbow_logging_handler import RainbowLoggingHandler

from fuzzinator import Controller
from fuzzinator.ui import build_parser
from .cli_listener import CliListener


def execute(args=None, parser=None):
    parser = build_parser(parent=parser)
    arguments = parser.parse_args(args)

    logger = logging.getLogger('fuzzinator')
    logger.addHandler(RainbowLoggingHandler(sys.stdout))
    logger.setLevel(arguments.log_level)

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(arguments.config)

    controller = Controller(config=config)
    controller.listener = CliListener()

    try:
        controller.run()
    except KeyboardInterrupt:
        pass
