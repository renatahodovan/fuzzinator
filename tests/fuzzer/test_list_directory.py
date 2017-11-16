# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os

import fuzzinator

from common_fuzzer import resources_dir


@pytest.mark.parametrize('pattern, subdirs, exp', [
    (os.path.join(resources_dir, 'mock_tests', '*'), False, {b'foo\n', b'bar\n', b'baz\n'}),
    (os.path.join(resources_dir, 'mock_tests', '**', '*'), True, {b'foo\n', b'bar\n', b'baz\n', b'qux\n'}),
])
def test_list_directory(pattern, subdirs, exp):
    fuzzer = fuzzinator.fuzzer.ListDirectory(pattern=pattern, subdirs=subdirs)
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
