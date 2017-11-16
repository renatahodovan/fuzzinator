# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import glob
import os


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

      - ``subdirs``: if it's true, the '**' characters in ``pattern`` will match
         any files and zero or more subdirectories (boolean value, False by default).

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
            subdirs=True
    """

    def __init__(self, pattern, subdirs='False', **kwargs):
        subdirs = subdirs in [1, '1', True, 'True', 'true']
        self.tests = [fn for fn in glob.glob(pattern, recursive=subdirs) if os.path.isfile(fn)]
        self.tests.sort(reverse=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, **kwargs):
        if not self.tests:
            return None

        test = self.tests.pop()
        with open(test, 'rb') as f:
            return f.read()
