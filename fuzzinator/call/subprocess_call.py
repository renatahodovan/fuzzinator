# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import os
import subprocess


def SubprocessCall(command, cwd=None, env=None, test=None, **kwargs):
    """
    Subprocess invocation-based call of a SUT that takes test input on its
    command line. (See FileWriterDecorator for SUTs that take input from a
    file.)

    Mandatory parameter of the SUT call:
      - 'command': string to pass to the child shell as a command to run (all
        occurrences of "{test}" in the string are replaced by the actual test
        input).
    Optional parameters of the SUT call:
      - 'cwd': if not None, change working directory before the command
        invocation.
      - 'env': if not None, a dictionary of variable names-values to update the
        environment with.

    Result of the SUT call:
      - If the child process exits with 0 exit code, no issue is returned.
      - Otherwise, an issue with 'exit_code', 'stdout', 'stderr' properties is
        returned.

    Example configuration snippet:
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
    with subprocess.Popen(command.format(test=test),
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          close_fds=True,
                          cwd=cwd or os.getcwd(),
                          env=env) as proc:
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            return {
                'exit_code': proc.returncode,
                'stdout': stdout,
                'stderr': stderr,
            }
    return None
