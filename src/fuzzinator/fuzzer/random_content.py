# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import random
import string

from .fuzzer import Fuzzer


class RandomContent(Fuzzer):
    """
    Example fuzzer to generate strings of random length from random ASCII
    uppercase letters and decimal digits.

    **Optional parameters of the fuzzer:**

      - ``min_length``: minimum length of the string to generate (integer
        number, 1 by default)
      - ``max_length``: maximum length of the string to generate (integer
        number, 1 by default)

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-random]
            sut=foo
            fuzzer=fuzzinator.fuzzer.RandomContent
            batch=100

            [fuzz.foo-with-random.fuzzer]
            min_length=100
            max_length=1000
    """

    def __init__(self, *, min_length=1, max_length=1, **kwargs):
        self.min_length = int(min_length)
        self.max_length = int(max_length)

    def __call__(self, *, index):
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                       for _ in range(random.randint(self.min_length, self.max_length))).encode('utf-8', errors='ignore')
