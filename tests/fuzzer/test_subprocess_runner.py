# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import sys

from os.path import join

import pytest

import fuzzinator

from .common_fuzzer import blinesep, resources_dir


@pytest.mark.parametrize('command, cwd, env, contents, exp', [
    (f'{sys.executable} {join(resources_dir, "mock_fuzzer.py")} -i {join(resources_dir, "mock_tests")} -o {{work_dir}}', None, None, True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    (f'{sys.executable} {join(resources_dir, "mock_fuzzer.py")} -i {join(resources_dir, "mock_tests")} -o .', '{work_dir}', None, True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    (f'{sys.executable} {join(resources_dir, "mock_fuzzer.py")} -i {join(resources_dir, "mock_tests")} -o {{work_dir}}', resources_dir, None, True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    (f'{sys.executable} {join(resources_dir, "mock_fuzzer.py")} -i mock_tests', resources_dir, '{"ODIR": "{work_dir}"}', True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    (f'{sys.executable} {join(resources_dir, "mock_fuzzer.py")} -o {{work_dir}}', resources_dir, '{"IDIR": "mock_tests"}', True, {b'foo' + blinesep, b'bar' + blinesep, b'baz' + blinesep}),
    (f'{sys.executable} {join(resources_dir, "mock_fuzzer.py")} -i mock_tests -o {{work_dir}}', resources_dir, None, False, {join('{tmpdir}', 'foo.txt'), join('{tmpdir}', 'bar.txt'), join('{tmpdir}', 'baz.txt')}),
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
