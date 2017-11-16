# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from pathlib import Path


class ListDirectory(object):
    """
    A simple test generator to iterate through existing files in a directory and
    return their contents one by one. Useful for re-testing previously
    discovered issues.

    Since the fuzzer starts iterating from the beginning of the directory in
    every fuzz job, there is no gain in running multiple instances of this
    fuzzer in parallel. Because of the same reason, the fuzzer should be left
    running in the same fuzz job batch until all the files of the directory are
    processed.

    **Mandatory parameter of the fuzzer:**

      - ``pattern``: shell-like pattern to the test files.

    **Optional parameter of the fuzzer:**

      - ``contents``: if it's true then the content of the files will be returned
         instead of their path (boolean value, True by default).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-oldbugs]
            sut=sut.foo
            fuzzer=fuzzinator.fuzzer.ListDirectory
            instances=1
            batch=inf

            [fuzz.foo-with-oldbugs.fuzzer.init]
            pattern=/home/alice/foo-old-bugs/**/*.js
    """
    def __init__(self, pattern, contents='True', **kwargs):
        self.contents = contents in [1, '1', True, 'True', 'true']
        path = Path(pattern)
        anchor, pattern = ('.', pattern) if not path.anchor else (path.anchor, str(path.relative_to(path.anchor)))
        self.tests = [str(fn) for fn in Path(anchor).glob(pattern) if os.path.isfile(str(fn))]
        self.tests.sort(reverse=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, **kwargs):
        if not self.tests:
            return None

        test = self.tests.pop()
        if not self.contents:
            return test

        with open(test, 'rb') as f:
            return f.read()
