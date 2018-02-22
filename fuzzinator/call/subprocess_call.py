# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import logging
import os
import shlex
import subprocess
import sys

from fuzzinator import Controller

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
    env = dict(os.environ, **json.loads(env)) if env else None
    no_exit_code = eval(no_exit_code) if no_exit_code else False
    timeout = int(timeout) if timeout else None

    try:
        proc = subprocess.Popen(shlex.split(command.format(test=test), posix=sys.platform != 'win32'),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=cwd or os.getcwd(),
                                env=env)
        stdout, stderr = proc.communicate(timeout=timeout)
        logger.debug('{stdout}\n{stderr}'.format(stdout=stdout.decode('utf-8', errors='ignore'),
                                                 stderr=stderr.decode('utf-8', errors='ignore')))
        if no_exit_code or proc.returncode != 0:
            return {
                'exit_code': proc.returncode,
                'stdout': stdout,
                'stderr': stderr,
            }
    except subprocess.TimeoutExpired:
        logger.debug('Timeout expired in the SUT\'s subprocess runner.')
        Controller.kill_process_tree(proc.pid)

    return None
