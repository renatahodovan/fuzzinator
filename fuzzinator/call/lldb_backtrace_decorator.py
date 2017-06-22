# Copyright (c) 2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import os
import pexpect

from . import CallableDecorator


class LldbBacktraceDecorator(CallableDecorator):
    """
    Decorator for subprocess-based SUT calls with file input to extend issues
    with ``'backtrace'`` property.

    **Mandatory parameter of the decorator:**

      - ``command``: string to pass to Lldb as a command to run (all occurrences
        of ``{test}`` in the string are replaced by the actual name of the test
        file).

    **Optional parameters of the decorator:**

      - ``cwd``: if not ``None``, change working directory before Lldb/command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``timeout``: timeout (in seconds) to wait between two lldb commands
        (integer number, 1 by default).

    The new ``'backtrace'`` issue property will contain the result of Lldb's
    ``bt`` command after the halt of the SUT.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall
            call.decorate(0)=fuzzinator.call.LldbBacktraceDecorator

            [sut.foo.call]
            # assuming that {test} is something that can be interpreted by foo as
            # command line argument
            command=./bin/foo {test}
            cwd=/home/alice/foo
            env={"BAR": "1"}

            [sut.foo.call.decorate(0)]
            command=${sut.foo.call:command}
            cwd=${sut.foo.call:cwd}
            env={"BAR": "1", "BAZ": "1"}
    """

    def decorator(self, command, cwd=None, env=None, timeout=None, **kwargs):
        timeout = int(timeout) if timeout is not None else 1

        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                try:
                    expect_patterns = ['\(lldb\) ', pexpect.EOF, pexpect.TIMEOUT]
                    child = pexpect.spawn('lldb -X -- {cmd}'.format(
                        cmd=command.format(test=kwargs['test'])),
                        cwd=cwd or os.getcwd(),
                        env=dict(os.environ, **json.loads(env or '{}')))
                    while child.expect(expect_patterns, timeout=timeout) == 0:
                        pass
                    child.sendline('run')
                    while child.expect(expect_patterns, timeout=timeout) == 0:
                        pass
                    child.sendline('bt')

                    backtrace = b''
                    while child.expect(expect_patterns, timeout=timeout) == 0:
                        backtrace += child.before

                    child.sendline('quit')
                    issue['backtrace'] = backtrace
                except:
                    pass

                return issue

            return filter
        return wrapper
