# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

from pathlib import Path

from ..config import as_bool, as_path

logger = logging.getLogger(__name__)


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
            sut=foo
            fuzzer=fuzzinator.fuzzer.ListDirectory
            instances=1
            batch=inf

            [fuzz.foo-with-oldbugs.fuzzer.init]
            pattern=/home/alice/foo-old-bugs/**/*.js
    """
    def __init__(self, pattern, contents=True, **kwargs):
        self.contents = as_bool(contents)
        pattern = as_path(pattern)
        path = Path(pattern)
        anchor, pattern = ('.', pattern) if not path.anchor else (path.anchor, str(path.relative_to(path.anchor)))
        self.tests = [str(fn) for fn in Path(anchor).glob(pattern) if os.path.isfile(str(fn))]
        self.tests.sort(reverse=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __call__(self, index, **kwargs):
        if not self.tests:
            return None

        test = self.tests.pop()
        logger.debug('index=%d, test=%r', index, test)
        if not self.contents:
            return test

        with open(test, 'rb') as f:
            return f.read()
