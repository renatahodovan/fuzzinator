# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os
import sys

import fuzzinator

from common_fuzzer import resources_dir


@pytest.mark.parametrize('outdir, exp', [
    ('{tmpdir}/tests-{{uid}}', {b'foo\n', b'bar\n', b'baz\n'})
])
@pytest.mark.parametrize('command, cwd, env', [
    ('%s %s -i %s -o {tmpdir}/tests-{{uid}}' % (sys.executable, os.path.join(resources_dir, 'mock_fuzzer.py'), os.path.join(resources_dir, 'mock_tests')), None, None),
    ('%s %s -i %s -o {tmpdir}/tests-{{uid}}' % (sys.executable, os.path.join('.', 'mock_fuzzer.py'), 'mock_tests'), resources_dir, None),
    ('%s %s -o {tmpdir}/tests-{{uid}}' % (sys.executable, os.path.join('.', 'mock_fuzzer.py')), resources_dir, '{"IDIR": "mock_tests"}'),
])
def test_subprocess_runner(outdir, command, cwd, env, exp, tmpdir):
    fuzzer = fuzzinator.fuzzer.SubprocessRunner(outdir=outdir.format(tmpdir=tmpdir), command=command.format(tmpdir=tmpdir), cwd=cwd, env=env)
    with fuzzer:
        tests = set()
        index = 0
        while True:
            test = fuzzer(index=index)
            if test is None:
                break

            tests.add(test)
            index += 1

    assert tests == exp
