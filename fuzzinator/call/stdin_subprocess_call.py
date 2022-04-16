# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import subprocess
import time

from ..config import as_bool, as_dict, as_pargs, as_path, decode
from .call import Call
from .non_issue import NonIssue

logger = logging.getLogger(__name__)


class StdinSubprocessCall(Call):
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
      - Otherwise, an issue with ``'exit_code'``, ``'stdout'``, ``'stderr'``
        and ``'time'`` properties is returned.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall

            [sut.foo.call]
            command=./bin/foo -
            cwd=/home/alice/foo
            env={"BAR": "1"}
    """

    def __init__(self, *, command, cwd=None, env=None, no_exit_code=None, timeout=None, encoding=None, **kwargs):
        self.command = command
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.no_exit_code = as_bool(no_exit_code)
        self.timeout = int(timeout) if timeout else None
        self.encoding = encoding

    def __call__(self, *, test, timeout=None, **kwargs):
        issue = {}

        try:
            start_time = time.time()
            result = subprocess.run(as_pargs(self.command),
                                    input=test,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=self.cwd,
                                    env=self.env,
                                    timeout=timeout or self.timeout,
                                    check=False)
            end_time = time.time()
            stdout, stderr = decode(result.stdout, self.encoding), decode(result.stderr, self.encoding)
            logger.debug('%s\n%s', stdout, stderr)

            issue = {
                'exit_code': result.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'time': end_time - start_time,
            }
            if self.no_exit_code or result.returncode != 0:
                return issue
        except subprocess.TimeoutExpired as e:
            logger.debug('StdinSubprocessCall execution timeout (%ds) expired.\n%s\n%s',
                         e.timeout,
                         decode(e.stdout or b'', self.encoding),
                         decode(e.stderr or b'', self.encoding))

        return NonIssue(issue)
