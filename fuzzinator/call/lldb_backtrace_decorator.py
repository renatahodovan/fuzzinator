# Copyright (c) 2017-2021 Renata Hodovan, Akos Kiss.
# Copyright (c) 2021 Paulo Matos, Igalia S.L.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import pexpect

from ..config import as_dict, as_pargs, as_path, decode
from .call_decorator import CallDecorator

logger = logging.getLogger(__name__)


class LldbBacktraceDecorator(CallDecorator):
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
      - ``encoding``: stdout and stderr encoding (default: autodetect).

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

    def __init__(self, *, command, cwd=None, env=None, timeout=None, encoding=None, **kwargs):
        self.command = command
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.timeout = int(timeout) if timeout is not None else 1
        self.encoding = encoding

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            issue = call(obj, test=test, **kwargs)
            if not issue:
                return issue

            try:
                expect_patterns = [r'\(lldb\) ', pexpect.EOF, pexpect.TIMEOUT]
                child = pexpect.spawn('lldb', ['-X', '--'] + as_pargs(self.command.format(test=test)),
                                      cwd=self.cwd,
                                      env=self.env)
                while child.expect(expect_patterns, timeout=self.timeout) == 0:
                    pass
                child.sendline('run')
                while child.expect(expect_patterns, timeout=self.timeout) == 0:
                    pass
                child.sendline('bt')

                backtrace = b''
                while child.expect(expect_patterns, timeout=self.timeout) == 0:
                    backtrace += child.before

                child.sendline('quit')
                issue['backtrace'] = decode(backtrace, self.encoding)
            except Exception as e:
                logger.warning('Failed to obtain lldb backtrace', exc_info=e)

            return issue

        return decorated_call
