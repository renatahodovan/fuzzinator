# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os

import fuzzinator

from common_fuzzer import resources_dir


@pytest.mark.parametrize('outdir, exp', [
    (os.path.join(resources_dir, 'mock_tests'), {b'foo\n', b'bar\n', b'baz\n'})
])
def test_list_directory(outdir, exp):
    fuzzer = fuzzinator.fuzzer.ListDirectory(outdir=outdir)
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
