# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def SubprocessUpdate(command, cwd=None, env=None):
    """
    Subprocess invocation-based SUT update.

    Mandatory parameter of the SUT update:
      - 'command': string to pass to the child shell as a command to run.
    Optional parameters of the SUT update:
      - 'cwd': if not None, change working directory before the command
        invocation.
      - 'env': if not None, a dictionary of variable names-values to update the
        environment with.

    Example configuration snippet:
    [sut.foo]
    update=fuzzinator.update.SubprocessUpdate
    #update_condition=... is needed to trigger the update

    [sut.foo.update]
    command=git pull && make
    cwd=/home/alice/foo
    env={"BAR": "1"}
    """

    with subprocess.Popen(command,
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd=cwd or os.getcwd(),
                          env=dict(os.environ, **json.loads(env or '{}'))) as proc:
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logger.warn(stderr)
        else:
            logger.info(stdout)
