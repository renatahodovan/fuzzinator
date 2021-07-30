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
from .update import Update

logger = logging.getLogger(__name__)


class SubprocessUpdate(Update):
    """
    Subprocess invocation-based SUT update.

    **Mandatory parameter of the SUT update:**

      - ``command``: string to pass to the child shell as a command to run.

    **Optional parameters of the SUT update:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``timeout``: run subprocess with timeout.
      - ``encoding``: stdout and stderr encoding (default: autodetect).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            update=fuzzinator.update.SubprocessUpdate
            #update_condition=... is needed to trigger the update

            [sut.foo.update]
            command=git pull && make
            cwd=/home/alice/foo
            env={"BAR": "1"}
    """

    def __init__(self, *, command, cwd=None, env=None, timeout=None, encoding=None, **kwargs):
        self.command = command
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.timeout = int(timeout) if timeout else None
        self.encoding = encoding

    def __call__(self):
        try:
            result = subprocess.run(as_pargs(self.command),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    cwd=self.cwd,
                                    env=self.env,
                                    timeout=self.timeout,
                                    check=True)
            logger.info('Update succeeded.\n%s', decode(result.stdout, self.encoding))
        except subprocess.TimeoutExpired as e:
            logger.warning('SUT update execution timeout (%ds) expired.', e.timeout)
        except subprocess.CalledProcessError as e:
            logger.warning('SUT update command returned with nonzero exit code (%d).\n%s\n%s',
                           e.returncode,
                           decode(e.stdout, self.encoding),
                           decode(e.stderr, self.encoding))
