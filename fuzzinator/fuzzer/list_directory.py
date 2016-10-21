# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os


class ListDirectory(object):
    """
    A simple fuzzer to iterate through the files in a directory and return their
    contents one by one. Useful for re-testing previously discovered issues.

    Since the fuzzer starts iterating from the beginning of the directory in
    every fuzz job, there is no gain in running multiple instances of this
    fuzzer in parallel. Because of the same reason, the fuzzer should be left
    running in the same fuzz job batch until all the files of the directory are
    processed.

    Mandatory parameter of the fuzzer:
      - 'outdir': path to the directory containing the files that act as test
        inputs.

    Example configuration snippet:
    [sut.foo]
    # see fuzzinator.call.*

    [fuzz.foo-with-oldbugs]
    sut=sut.foo
    fuzzer=fuzzinator.fuzzer.ListDirectory
    instances=1
    batch=inf

    [fuzz.foo-with-oldbugs.fuzzer.init]
    outdir=/home/alice/foo-old-bugs/
    """

    def __init__(self, outdir, **kwargs):
        self.tests = [os.path.join(outdir, test) for test in os.listdir(outdir)]
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
