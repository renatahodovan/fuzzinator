# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import random
import string


def RandomContent(*, min_length='1', max_length='1', **kwargs):
    """
    Example fuzzer to generate strings of random length from random ASCII
    uppercase letters and decimal digits.

    Optional parameters of the fuzzer:
      - 'min_length': minimum length of the string to generate (integer number,
        1 by default)
      - 'max_length': maximum length of the string to generate (integer number,
        1 by default)

    Example configuration snippet:
    [sut.foo]
    # see fuzzinator.call.*

    [fuzz.foo-with-random]
    sut=sut.foo
    fuzzer=fuzzinator.fuzzer.RandomContent
    batch=100

    [fuzz.foo-with-random.fuzzer]
    min_length=100
    max_length=1000
    """

    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                   for _ in range(random.randint(int(min_length), int(max_length)))).encode('utf-8', errors='ignore')
