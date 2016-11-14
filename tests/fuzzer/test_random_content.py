# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator


@pytest.mark.parametrize('fuzzer_kwargs, exp_min_len, exp_max_len', [
    ({}, 1, 1),
    ({'max_length': '100'}, 1, 100),
    ({'min_length': '10', 'max_length': '100'}, 10, 100),
])
def test_random_content(fuzzer_kwargs, exp_min_len, exp_max_len):
    for index in range(100):
        out = fuzzinator.fuzzer.RandomContent(index=index, **fuzzer_kwargs)
        out_len = len(out)
        assert out_len >= exp_min_len and out_len <= exp_max_len
