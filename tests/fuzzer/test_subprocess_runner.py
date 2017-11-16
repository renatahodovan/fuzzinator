# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import sys

import fuzzinator

from os.path import join

from common_fuzzer import resources_dir


@pytest.mark.parametrize('outdir', [join('{tmpdir}', 'tests-{{uid}}')])
@pytest.mark.parametrize('command, cwd, env, contents, exp', [
    ('%s %s -i %s -o %s' % (sys.executable, join(resources_dir, 'mock_fuzzer.py'), join(resources_dir, 'mock_tests'), join('{tmpdir}', 'tests-{{uid}}')), None, None, True, {b'foo\n', b'bar\n', b'baz\n'}),
    ('%s %s -i %s -o %s' % (sys.executable, join('.', 'mock_fuzzer.py'), 'mock_tests', join('{tmpdir}', 'tests-{{uid}}')), resources_dir, None, True, {b'foo\n', b'bar\n', b'baz\n'}),
    ('%s %s -o %s' % (sys.executable, join('.', 'mock_fuzzer.py'), join('{tmpdir}', 'tests-{{uid}}')), resources_dir, '{"IDIR": "mock_tests"}', True, {b'foo\n', b'bar\n', b'baz\n'}),
    ('%s %s -i %s -o %s' % (sys.executable, join('.', 'mock_fuzzer.py'), 'mock_tests', join('{tmpdir}', 'tests-{{uid}}')), resources_dir, None, False, {join('{tmpdir}', 'tests-{uid}', 'foo.txt'), join('{tmpdir}', 'tests-{uid}', 'bar.txt'), join('{tmpdir}', 'tests-{uid}', 'baz.txt')}),
])
def test_subprocess_runner(outdir, command, cwd, env, contents, exp, tmpdir):
    fuzzer = fuzzinator.fuzzer.SubprocessRunner(outdir=outdir.format(tmpdir=tmpdir), command=command.format(tmpdir=tmpdir), cwd=cwd, env=env, contents=contents)
    with fuzzer:
        tests = set()
        index = 0
        while True:
            test = fuzzer(index=index)
            if test is None:
                break

            tests.add(test)
            index += 1

    if not contents:
        exp = {e.format(tmpdir=tmpdir, uid=fuzzer.uid) for e in exp}

    assert tests == exp
