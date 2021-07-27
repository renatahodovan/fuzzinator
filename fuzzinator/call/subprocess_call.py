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
from ..controller import Controller
from .call import Call
from .non_issue import NonIssue

logger = logging.getLogger(__name__)


class SubprocessCall(Call):
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
      - ``encoding``: stdout and stderr encoding (default: autodetect).

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

    def __init__(self, *, command, cwd=None, env=None, no_exit_code=None, timeout=None, encoding=None, **kwargs):
        self.command = command
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.no_exit_code = as_bool(no_exit_code)
        self.timeout = int(timeout) if timeout else None
        self.encoding = encoding

    def __call__(self, *, test, **kwargs):
        issue = {}

        try:
            proc = subprocess.Popen(as_pargs(self.command.format(test=test)),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=self.cwd,
                                    env=self.env)
            stdout, stderr = proc.communicate(timeout=self.timeout)
            stdout, stderr = decode(stdout, self.encoding), decode(stderr, self.encoding)
            logger.debug('%s\n%s', stdout, stderr)

            issue = {
                'exit_code': proc.returncode,
                'stdout': stdout,
                'stderr': stderr,
            }
            if self.no_exit_code or proc.returncode != 0:
                return issue
        except subprocess.TimeoutExpired as e:
            logger.debug('SubprocessCall execution timeout (%ds) expired.', e.timeout)
            Controller.kill_process_tree(proc.pid)

        return NonIssue(issue) if issue else None
