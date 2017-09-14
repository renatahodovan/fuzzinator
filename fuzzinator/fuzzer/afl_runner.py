# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import logging
import os
import pexpect

logger = logging.getLogger(__name__)


class AFLRunner(object):
    """
    Wrapper around AFL to be executed continuously in a subprocess. The findings
    of AFL are periodically checked and any new test cases are returned as test
    inputs to the SUT. (Thus, all AFL findings are processed, extended, and
    filtered by any and all SUT decorators, uniqueness is determined, etc.)

    For AFL, it is best not to run multiple instances in parallel.

    **Mandatory parameters of the fuzzer:**

      - ``afl_fuzz``: path to the AFL fuzzer tool.
      - ``sut_command``: the string to append to the command string used to
        invoke AFL, probably the same string that is used for
        :func:`fuzzinator.call.SubprocessCall`'s command parameter (the
        ``{test}`` substring is automatically replaced with the ``@@`` input
        file placeholder used by AFL).
      - ``input``: the directory of initial test cases for AFL.
      - ``output``: the directory that will store the findings of AFL (all
        occurrences of ``{uid}`` in the string are replaced by an identifier
        unique to this fuzz job).

    **Optional parameters of the fuzzer:**

      - ``cwd``: if not ``None``, change working directory before invoking AFL.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with (``AFL_NO_UI=1`` will be added automatically
        to suppress AFL's own UI).
      - ``timeout``: if not ``None``, pass its value as the ``-t`` timeout
        parameter to AFL.
      - ``dictionary``: if not ``None``, pass its value as the ``-x`` dictionary
        parameter to AFL.
      - ``master_name``: the name of the master fuzzer instance which will perform
        deterministic checks.
      - ``slave_name``: the name of a slave fuzzer instance which will proceed to
        random tweaks.
        For further details check:
        https://github.com/mirrorer/afl/blob/master/docs/parallel_fuzzing.txt

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall

            [sut.foo.call]
            command=./bin/foo {test}
            cwd=/home/alice/foo
            env={"BAR": "1"}

            [fuzz.foo-with-afl]
            sut=sut.foo
            fuzzer=fuzzinator.fuzzer.AFLRunner
            batch=inf
            instances=1

            [fuzz.foo-with-afl.fuzzer.init]
            afl_fuzz=/home/alice/afl/afl-fuzz
            sut_command=${sut.foo.call:command}
            cwd=${sut.foo.call:cwd}
            env=${sut.foo.call:env}
            input=/home/alice/foo-inputs
            output=${fuzzinator:work_dir}/afl-output/{uid}
    """

    def __init__(self, afl_fuzz, input, output, sut_command, cwd=None, env=None, timeout=None, dictionary=None,
                 master_name=None, slave_name=None, **kwargs):
        self.afl_fuzz = afl_fuzz
        self.input = input
        self.output = output.format(uid=str(id(self)))
        self.sut_command = sut_command
        self.cwd = cwd
        self.env = json.loads(env) if env else dict()
        self.env.update({'AFL_NO_UI': '1'})
        self.timeout = timeout
        self.dictionary = dictionary
        self.master_name = master_name
        self.slave_name = slave_name

        self.iteration = 1
        self.checked = set()
        self.tests = list()

    def __enter__(self):
        os.makedirs(self.output, exist_ok=True)
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, **kwargs):
        crash_dir = os.path.join(self.output, '{name}'.format(name=self.master_name or self.slave_name or ''), 'crashes')

        while True:
            if self.tests:
                test = self.tests.pop()
                self.checked.add(os.path.basename(test))
                with open(test, 'rb') as f:
                    return f.read()

            command = '{afl} {input} {output} {timeout} {dictionary} {master_name} {slave_name} {sut_command}'.format(
                afl=self.afl_fuzz,
                input='-i {i}'.format(i=self.input) if self.iteration == 1 else '-i-',
                output='-o {o}'.format(o=self.output),
                timeout='-t {t}'.format(t=self.timeout) if self.timeout else '',
                dictionary='-x {x}'.format(x=self.dictionary) if self.dictionary else '',
                master_name='-M {n}'.format(n=self.master_name) if self.master_name else '',
                slave_name='-S {n}'.format(n=self.slave_name) if self.slave_name else '',
                sut_command=self.sut_command.format(test='@@'))

            child = pexpect.spawn(command, cwd=self.cwd, env=self.env)
            child.expect(['Fuzzing test case [#]{next_it}.*'.format(next_it=self.iteration), pexpect.EOF], timeout=None)
            child.terminate(force=True)

            self.tests = [os.path.join(crash_dir, test) for test in os.listdir(crash_dir) if test.startswith('id') and test not in self.checked]
            self.iteration += 1
