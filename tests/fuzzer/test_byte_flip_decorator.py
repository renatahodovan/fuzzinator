# Copyright (c) 2017-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator

from .common_fuzzer import MockExhaustedFuzzer, MockRepeatingFuzzer


@pytest.mark.parametrize('fuzzer_class, fuzzer_init_kwargs, dec_kwargs, exp_flip_cnt', [
    (MockExhaustedFuzzer, {}, {'frequency': '100'}, None),

    (MockRepeatingFuzzer, {'test': b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F', 'n': 10}, {'frequency': '16'}, 1),
    (MockRepeatingFuzzer, {'test': b'\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F', 'n': 10}, {'frequency': '16'}, 1),
    (MockRepeatingFuzzer, {'test': b'\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F', 'n': 10}, {'frequency': '16'}, 1),

    (MockRepeatingFuzzer, {'test': b'\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F', 'n': 10}, {'frequency': '1'}, 16),
    (MockRepeatingFuzzer, {'test': b'\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F', 'n': 10}, {'frequency': '4'}, 4),
    (MockRepeatingFuzzer, {'test': b'\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F', 'n': 10}, {'frequency': '10'}, 2),
    (MockRepeatingFuzzer, {'test': b'\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F\x7F', 'n': 10}, {'frequency': '100'}, 1),

    (MockRepeatingFuzzer, {'test': b'abc', 'n': 10}, {'frequency': '3', 'max_byte': '95'}, 1),
    (MockRepeatingFuzzer, {'test': b'ABC', 'n': 10}, {'frequency': '3', 'min_byte': '96'}, 1),

    (MockRepeatingFuzzer, {'test': b' ~', 'n': 10}, {'frequency': '1', 'min_byte': '33', 'max_byte': '125'}, 2),
    (MockRepeatingFuzzer, {'test': b'  ', 'n': 10}, {'frequency': '2', 'min_byte': '32', 'max_byte': '32'}, 0),
])
def test_byte_flip_decorator(fuzzer_class, fuzzer_init_kwargs, dec_kwargs, exp_flip_cnt):
    fuzzer_class = fuzzinator.fuzzer.ByteFlipDecorator(**dec_kwargs)(fuzzer_class)
    fuzzer = fuzzer_class(**fuzzer_init_kwargs)

    with fuzzer:
        index = 0
        while True:
            test = fuzzer(index=index)
            if test is None:
                break

            orig_test = fuzzer_init_kwargs['test']
            flips = [i for i in range(min(len(orig_test), len(test))) if orig_test[i] != test[i]]
            assert len(flips) == exp_flip_cnt

            index += 1
