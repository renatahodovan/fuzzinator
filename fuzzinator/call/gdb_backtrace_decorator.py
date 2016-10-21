# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import os
import pexpect

from .callable_decorator import CallableDecorator


class GdbBacktraceDecorator(CallableDecorator):
    """
    Decorator for subprocess-based SUT calls with file input to extend issues
    with 'backtrace' property.

    Mandatory parameter of the decorator:
      - 'command': string to pass to GDB as a command to run (all occurrences of
        "{test}" in the string are replaced by the actual name of the test
        file).
    Optional parameters of the decorator:
      - 'cwd': if not None, change working directory before GDB/command
        invocation.
      - 'env': if not None, a dictionary of variable names-values to update the
        environment with.

    The new 'backtrace' issue property will contain the result of GDB's bt
    command after the halt of the SUT.

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.SubprocessCall
    call.decorator(0)=fuzzinator.call.GdbBacktraceDecorator

    [sut.foo.call]
    # assuming that {test} is something that can be interpreted by foo as
    # command line argument
    command=./bin/foo {test}
    cwd=/home/alice/foo
    env={"BAR": "1"}

    [sut.foo.call.decorator(0)]
    command=${sut.foo.call:command}
    cwd=${sut.foo.call:cwd}
    env={"BAR": "1", "BAZ": "1"}
    """

    def decorator(self, command, cwd=None, env=None, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                child = pexpect.spawn('gdb -ex "set width unlimited" -ex "set pagination off" --args {cmd}'.format(
                    cmd=command.format(test=issue['test'])),
                    cwd=cwd or os.getcwd(),
                    env=dict(os.environ, **json.loads(env or '{}')))
                child.expect_exact('(gdb) ')
                child.sendline('run')
                child.expect_exact('(gdb) ')
                child.sendline('bt')
                child.expect_exact('(gdb) ')
                backtrace = child.before
                child.terminate(force=True)
                issue['backtrace'] = backtrace
                return issue

            return filter
        return wrapper
