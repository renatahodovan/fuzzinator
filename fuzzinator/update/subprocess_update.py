# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import subprocess

from ..config import as_dict, as_pargs, as_path
from .. import Controller

logger = logging.getLogger(__name__)


def SubprocessUpdate(command, cwd=None, env=None, timeout=None):
    """
    Subprocess invocation-based SUT update.

    **Mandatory parameter of the SUT update:**

      - ``command``: string to pass to the child shell as a command to run.

    **Optional parameters of the SUT update:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``timeout``: run subprocess with timeout.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            update=fuzzinator.update.SubprocessUpdate
            #update_condition=... is needed to trigger the update

            [sut.foo.update]
            command=git pull && make
            cwd=/home/alice/foo
            env={"BAR": "1"}
    """

    timeout = int(timeout) if timeout else None
    try:
        proc = subprocess.Popen(as_pargs(command),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=as_path(cwd) if cwd else os.getcwd(),
                                env=dict(os.environ, **as_dict(env or '{}')))
        stdout, stderr = proc.communicate(timeout=timeout)
        stdout_str = stdout.decode('utf-8', errors='ignore')
        if proc.returncode != 0:
            logger.warning('Update command returned with nonzero exit code (%d).\n%s\n%s',
                           proc.returncode,
                           stdout_str,
                           stderr.decode('utf-8', errors='ignore'))
        else:
            logger.info('Update succeeded.\n%s', stdout_str)
    except subprocess.TimeoutExpired:
        logger.debug('Timeout expired in the subprocess update.')
        Controller.kill_process_tree(proc.pid)
