# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import random

from .fuzzer import Fuzzer


class RandomInteger(Fuzzer):
    """
    A simple test generator to produce a single random integer number from
    a predefined interval.

    **Mandatory parameters of the fuzzer:**

        - ``min_value``: lower boundary of the interval to generate the
          number from.
        - ``max_value``: upper boundary of the interval to generate the
          number from.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-randint]
            sut=foo
            fuzzer=fuzzinator.fuzzer.RandomNumber
            batch=100

            [fuzz.foo-with-randint.fuzzer]
            min_value=0
            max_value=1000
    """

    def __init__(self, *, min_value, max_value, **kwargs):
        self.min_value = int(min_value)
        self.max_value = int(max_value)

    def __call__(self, *, index):
        return random.randint(self.min_value, self.max_value)
