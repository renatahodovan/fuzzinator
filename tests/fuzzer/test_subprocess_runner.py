# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import sys

from os.path import join

import fuzzinator

from common_fuzzer import blinesep, resources_dir


@pytest.mark.parametrize('command, cwd, env, contents, exp', [
    ('%s %s -i %s -o {work_dir}' % (sys.executable, join(resources_dir, 'mock_fuzzer.py'), join(resources_dir, 'mock_tests')), None, None, True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    ('%s %s -i %s -o .' % (sys.executable, join(resources_dir, 'mock_fuzzer.py'), join(resources_dir, 'mock_tests')), '{work_dir}', None, True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    ('%s %s -i %s -o {work_dir}' % (sys.executable, join('.', 'mock_fuzzer.py'), 'mock_tests'), resources_dir, None, True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    ('%s %s -i %s' % (sys.executable, join('.', 'mock_fuzzer.py'), 'mock_tests'), resources_dir, '{"ODIR": "{work_dir}"}', True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    ('%s %s -o {work_dir}' % (sys.executable, join('.', 'mock_fuzzer.py')), resources_dir, '{"IDIR": "mock_tests"}', True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    ('%s %s -i %s -o {work_dir}' % (sys.executable, join('.', 'mock_fuzzer.py'), 'mock_tests'), resources_dir, None, False, {join('{tmpdir}', 'foo.txt'), join('{tmpdir}', 'bar.txt'), join('{tmpdir}', 'baz.txt')}),
])
def test_subprocess_runner(command, cwd, env, contents, exp, tmpdir):
    fuzzer = fuzzinator.fuzzer.SubprocessRunner(command=command, cwd=cwd, env=env, contents=contents, work_dir=str(tmpdir))
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
        exp = {e.format(tmpdir=tmpdir) for e in exp}

    assert tests == exp
