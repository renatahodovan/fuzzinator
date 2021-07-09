# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator


@pytest.mark.parametrize('fuzzer_kwargs, exp_min_value, exp_max_value', [
    ({'min_value': '10', 'max_value': '100'}, 10, 100),
])
def test_random_integer(fuzzer_kwargs, exp_min_value, exp_max_value):
    fuzzer = fuzzinator.fuzzer.RandomInteger(**fuzzer_kwargs)
    for index in range(100):
        out = fuzzer(index=index)
        assert exp_min_value <= out <= exp_max_value
