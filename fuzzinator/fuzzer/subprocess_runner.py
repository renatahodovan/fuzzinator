# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import shutil
import subprocess

from ..config import as_bool, as_dict, as_pargs, as_path, decode
from .fuzzer import Fuzzer

logger = logging.getLogger(__name__)


class SubprocessRunner(Fuzzer):
    """
    Wrapper around a fuzzer that is available as an executable and can generate
    its test cases as file(s) in a directory. First, the external executable is
    invoked as a subprocess, and once it has finished, the contents of the
    generated files are returned one by one.

    **Mandatory parameters of the fuzzer:**

      - ``command``: string to pass to the child shell as a command to run,
        which must generate its test cases in the temporary working directory
        unique to this fuzzer instance (all occurrences of ``{work_dir}`` in the
        string are replaced by the path to this directory).

    **Optional parameters of the fuzzer:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation (all occurrences of ``{work_dir}`` in the string are replaced
        by the path to the temporary working directory unique to this fuzzer
        instance).
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with (all occurrences of ``{work_dir}`` in the
        values are replaced by the path to the temporary working directory
        unique to this fuzzer instance)..
      - ``timeout``: run subprocess with timeout.
      - ``contents``: if it's true then the content of the files will be
        returned instead of their path (boolean value, True by default).
      - ``encoding``: stdout and stderr encoding (default: autodetect).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-bar]
            sut=foo
            fuzzer=fuzzinator.fuzzer.SubprocessRunner
            batch=50

            [fuzz.foo-with-bar.fuzzer]
            command=barfuzzer -n ${fuzz.foo-with-bar:batch} -o {work_dir}
    """

    def __init__(self, *, command, cwd=None, env=None, timeout=None, contents=True, encoding=None, work_dir, **kwargs):
        if 'outdir' in kwargs:
            logger.warning('outdir parameter of fuzzinator.fuzzer.SubprocessRunner is deprecated')

        self.command = as_pargs(command.format(work_dir=work_dir))
        self.cwd = as_path(cwd.format(work_dir=work_dir)) if cwd else os.getcwd()
        self.env = dict(os.environ, **{k: v.format(work_dir=work_dir) for k, v in as_dict(env).items()}) if env else None
        self.timeout = int(timeout) if timeout else None
        self.contents = as_bool(contents)
        self.encoding = encoding

        self.work_dir = work_dir
        self.tests = []

    def __enter__(self):
        os.makedirs(self.work_dir, exist_ok=True)
        try:
            subprocess.run(self.command,
                           cwd=self.cwd,
                           env=self.env,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           timeout=self.timeout,
                           check=True)
        except subprocess.TimeoutExpired as e:
            logger.warning('Fuzzer execution timeout (%ds) expired.', e.timeout)
        except subprocess.CalledProcessError as e:
            logger.warning('Fuzzer command returned with nonzero exit code (%d).\n%s\n%s', e.returncode,
                           decode(e.stdout, self.encoding),
                           decode(e.stderr, self.encoding))
        self.tests = [os.path.join(self.work_dir, test) for test in os.listdir(self.work_dir)]
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.work_dir, ignore_errors=True)
        return False

    def __call__(self, *, index):
        if not self.tests:
            return None

        test = self.tests.pop()
        if not self.contents:
            return test

        with open(test, 'rb') as f:
            return f.read()
