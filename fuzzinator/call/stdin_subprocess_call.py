# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import os
import shlex
import subprocess


def StdinSubprocessCall(command, cwd=None, env=None, test=None, **kwargs):
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

    env = dict(os.environ, **json.loads(env)) if env else None
    with subprocess.Popen(shlex.split(command),
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          cwd=cwd or os.getcwd(),
                          env=env) as proc:
        stdout, stderr = proc.communicate(input=test)
        if proc.returncode != 0:
            return {
                'exit_code': proc.returncode,
                'stdout': stdout,
                'stderr': stderr,
            }
    return None
