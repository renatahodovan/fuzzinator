# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import subprocess

from ..config import as_bool, as_dict, as_pargs, as_path, decode
from .. import Controller
from . import NonIssue

logger = logging.getLogger(__name__)


def StdinSubprocessCall(command, cwd=None, env=None, no_exit_code=None, test=None, timeout=None, encoding=None, **kwargs):
    """
    Subprocess invocation-based call of a SUT that takes a test input on its
    stdin stream.

    **Mandatory parameter of the SUT call:**

      - ``command``: string to pass to the child shell as a command to run.

    **Optional parameters of the SUT call:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``no_exit_code``: makes possible to force issue creation regardless of
        the exit code.
      - ``timeout``: run subprocess with timeout.
      - ``encoding``: stdout and stderr encoding (default: autodetect).

    **Result of the SUT call:**

      - If the child process exits with 0 exit code, no issue is returned.
      - Otherwise, an issue with ``'exit_code'``, ``'stdout'``, and ``'stderr'``
        properties is returned.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall

            [sut.foo.call]
            command=./bin/foo -
            cwd=/home/alice/foo
            env={"BAR": "1"}
    """
    env = dict(os.environ, **as_dict(env)) if env else None
    no_exit_code = as_bool(no_exit_code)
    timeout = int(timeout) if timeout else None
    issue = {}

    try:
        proc = subprocess.Popen(as_pargs(command),
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=as_path(cwd) if cwd else os.getcwd(),
                                env=env)
        stdout, stderr = proc.communicate(input=test, timeout=timeout)
        stdout, stderr = decode(stdout, encoding), decode(stderr, encoding)
        logger.debug('%s\n%s', stdout, stderr)

        issue = {
            'exit_code': proc.returncode,
            'stdout': stdout,
            'stderr': stderr,
        }
        if no_exit_code or proc.returncode != 0:
            return issue
    except subprocess.TimeoutExpired as e:
        logger.debug('StdinSubprocessCall execution timeout (%ds) expired.', e.timeout)
        Controller.kill_process_tree(proc.pid)

    return NonIssue(issue) if issue else None
