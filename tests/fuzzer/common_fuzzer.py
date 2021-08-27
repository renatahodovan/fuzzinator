# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

import fuzzinator


linesep = os.linesep
blinesep = str.encode(linesep)
resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')


class MockExhaustedFuzzer(fuzzinator.fuzzer.Fuzzer):
    """
    Always return ``None`` signaling an exhausted fuzzer.
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        return None


class MockRepeatingFuzzer(fuzzinator.fuzzer.Fuzzer):
    """
    Return the same ``test`` ``n`` times then return ``None`` that the fuzzer is
    exhausted.
    """

    def __init__(self, test, n):
        self._test = test
        self._n = n
        self._i = 0

    def __call__(self, **kwargs):
        if self._i >= self._n:
            return None

        self._i += 1
        return self._test
