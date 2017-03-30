# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os


resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')


def mock_exhausted_fuzzer(**kwargs):
    """
    Always return ``None`` signaling an exhausted fuzzer.
    """
    return None


class MockRepeatingFuzzer(object):
    """
    Return the same ``test`` ``n`` times then return ``None`` that the fuzzer is
    exhausted.
    """

    def __init__(self, test, n):
        self.test = test
        self.n = n
        self.i = 0

    def __call__(self, **kwargs):
        if self.i >= self.n:
            return None

        self.i += 1
        return self.test
