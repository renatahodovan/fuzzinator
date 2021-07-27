# Copyright (c) 2017-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import math
import random


class ByteFlipDecorator(object):
    """
    Decorator to add extra random byte flips to fuzzer results.

    **Mandatory parameter of the decorator:**

      - ``frequency``: the length of the test divided by this integer number
        gives the number of bytes flipped.

    **Optional parameters of the decorator:**

      - ``min_byte``: minimum value for the flipped bytes (integer number, 32 by
        default, the smallest ASCII code of the printable characters).
      - ``max_byte``: maximum value for the flipped bytes (integer number, 126
        by default, the largest ASCII code of the printable characters).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-flips]
            sut=foo
            fuzzer=fuzzinator.fuzzer.ListDirectory
            fuzzer.decorate(0)=fuzzinator.fuzzer.ByteFlipDecorator
            batch=inf

            [fuzz.foo-with-flips.fuzzer]
            outdir=/home/alice/foo-old-bugs/

            [fuzz.foo-with-flips.fuzzer.decorate(0)]
            frequency=100
            min_byte=0
            max_byte=255
    """

    def __init__(self, *, frequency, min_byte=32, max_byte=126, **kwargs):
        self.frequency = int(frequency)
        self.min_byte = int(min_byte)
        self.max_byte = int(max_byte)

    def __call__(self, fuzzer_class):
        decorator = self

        class DecoratedFuzzer(fuzzer_class):

            def __call__(self, *, index):
                test = super().__call__(index=index)
                if test is None:
                    return None

                test = bytearray(test)
                for pos in random.sample(range(len(test)), math.ceil(len(test) / decorator.frequency)):
                    test[pos] = random.randint(decorator.min_byte, decorator.max_byte)

                return bytes(test)

        return DecoratedFuzzer
