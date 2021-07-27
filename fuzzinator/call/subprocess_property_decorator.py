# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import subprocess

from ..config import as_dict, as_pargs, as_path, decode
from ..controller import Controller
from .call_decorator import CallDecorator

logger = logging.getLogger(__name__)


class SubprocessPropertyDecorator(CallDecorator):
    """
    Decorator for SUT calls to extend issues with an arbitrary property where
    the value is the output of a shell subprocess.

    **Mandatory parameters of the decorator:**

      - ``property``: name of the property to extend the issue with.
      - ``command``: string to pass to the child shell as a command to run.

    **Optional parameters of the decorator:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``timeout``: run subprocess with timeout.
      - ``encoding``: stdout and stderr encoding (default: autodetect).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall
            call.decorate(0)=fuzzinator.call.SubprocessPropertyDecorator

            [sut.foo.call]
            command=./bin/foo -
            cwd=/home/alice/foo

            [sut.foo.call.decorate(0)]
            property=version
            command=git rev-parse --short HEAD
            cwd=${sut.foo.call:cwd}
            env={"GIT_FLUSH": "1"}
    """

    def __init__(self, *, property, command, cwd=None, env=None, timeout=None, encoding=None, **kwargs):
        self.property = property
        self.command = command
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.timeout = int(timeout) if timeout else None
        self.encoding = encoding

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            issue = call(obj, test=test, **kwargs)
            if not issue:
                return issue

            try:
                proc = subprocess.Popen(as_pargs(self.command),
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        cwd=self.cwd,
                                        env=self.env)
                stdout, stderr = proc.communicate(timeout=self.timeout)
                stdout, stderr = decode(stdout, self.encoding), decode(stderr, self.encoding)
                if proc.returncode == 0:
                    issue[self.property] = stdout
                else:
                    logger.debug('SubprocessPropertyDecorator exited with nonzero exit code while setting the \'%s\' property.\n%s\n%s',
                                 self.property,
                                 stdout,
                                 stderr)
            except subprocess.TimeoutExpired as e:
                logger.debug('SubprocessPropertyDecorator execution timeout (%ds) expired while setting the \'%s\' property.', e.timeout, self.property)
                Controller.kill_process_tree(proc.pid)

            return issue

        return decorated_call
