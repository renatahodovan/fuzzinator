# Copyright (c) 2017-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from ..config import as_bool
from .call_decorator import CallDecorator


class FileReaderDecorator(CallDecorator):
    """
    Decorator for SUTs that take input as a file path: saves the content of
    the failing test case and optionally removes the file.

    Moreover, the issue (if any) is also extended with the new ``'filename'``
    property containing the name of the test case (as received in the ``test``
    argument).

    **Optional parameter of the decorator:**

      - ``cleanup``: Boolean to enable the removal of the loaded file
        (default: False).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall
            call.decorate(0)=fuzzinator.call.FileReaderDecorator

            [sut.foo.call]
            # assuming that foo takes one file as input specified on command line
            command=/home/alice/foo/bin/foo {test}

            [sut.foo.decorate(0)]
            cleanup=True
    """

    def __init__(self, *, cleanup=False, **kwargs):
        self.cleanup = as_bool(cleanup)

    def call(self, cls, obj, *, test, **kwargs):
        issue = super(cls, obj).__call__(test=test, **kwargs)

        if issue:
            with open(test, 'rb') as f:
                issue['test'] = f.read()
            issue['filename'] = os.path.basename(test)

        if self.cleanup:
            os.remove(test)

        return issue
