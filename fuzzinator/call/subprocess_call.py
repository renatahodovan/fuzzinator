# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import subprocess

from ..config import as_bool, as_dict, as_pargs, as_path
from .. import Controller
from . import NonIssue

logger = logging.getLogger(__name__)


def SubprocessCall(command, cwd=None, env=None, no_exit_code=None, test=None,
                   timeout=None, **kwargs):
    """
    Subprocess invocation-based call of a SUT that takes test input on its
    command line. (See :class:`fuzzinator.call.FileWriterDecorator` for SUTs
    that take input from a file.)

    **Mandatory parameter of the SUT call:**

      - ``command``: string to pass to the child shell as a command to run (all
        occurrences of ``{test}`` in the string are replaced by the actual test
        input).

    **Optional parameters of the SUT call:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``no_exit_code``: makes possible to force issue creation regardless of
        the exit code.
      - ``timeout``: run subprocess with timeout.

    **Result of the SUT call:**

      - If the child process exits with 0 exit code, no issue is returned.
      - Otherwise, an issue with ``'exit_code'``, ``'stdout'``, and ``'stderr'``
        properties is returned.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall

            [sut.foo.call]
            # assuming that {test} is something that can be interpreted by foo as
            # command line argument
            command=./bin/foo {test}
            cwd=/home/alice/foo
            env={"BAR": "1"}
    """
    env = dict(os.environ, **as_dict(env)) if env else None
    no_exit_code = as_bool(no_exit_code)
    timeout = int(timeout) if timeout else None
    issue = {}

    try:
        proc = subprocess.Popen(as_pargs(command.format(test=test)),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=as_path(cwd) if cwd else os.getcwd(),
                                env=env)
        stdout, stderr = proc.communicate(timeout=timeout)
        logger.debug('%s\n%s', stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore'))

        issue = {
            'exit_code': proc.returncode,
            'stdout': stdout,
            'stderr': stderr,
        }
        if no_exit_code or proc.returncode != 0:
            return issue
    except subprocess.TimeoutExpired:
        logger.debug('Timeout expired in the SUT\'s subprocess runner.')
        proc.kill()
        proc.communicate()

    return NonIssue(issue) if issue else None
