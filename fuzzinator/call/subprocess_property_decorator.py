# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import subprocess

from ..config import as_dict, as_pargs, as_path
from .. import Controller
from . import CallableDecorator

logger = logging.getLogger(__name__)


class SubprocessPropertyDecorator(CallableDecorator):
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

    def decorator(self, property, command, cwd=None, env=None, timeout=None, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return issue

                try:
                    proc = subprocess.Popen(as_pargs(command),
                                            cwd=as_path(cwd) if cwd else os.getcwd(),
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            env=dict(os.environ, **as_dict(env or '{}')))
                    stdout, stderr = proc.communicate(timeout=timeout)
                    if proc.returncode == 0:
                        issue[property] = stdout
                    else:
                        logger.debug('SubprocessPropertyDecorator exited with nonzero exit code while setting the \'%s\' property.\n%s\n%s',
                                     property,
                                     stdout.decode('utf-8', errors='ignore'),
                                     stderr.decode('utf-8', errors='ignore'))
                except subprocess.TimeoutExpired:
                    logger.debug('Timeout expired in the SubprocessPropertyDecorator while setting the \'%s\' property.', property)
                    Controller.kill_process_tree(proc.pid)

                return issue

            return filter
        return wrapper
