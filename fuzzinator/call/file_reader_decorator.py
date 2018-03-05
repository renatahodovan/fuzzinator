# Copyright (c) 2017-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from . import CallableDecorator


class FileReaderDecorator(CallableDecorator):
    """
    Decorator for SUTs that take input as a file path: saves the content of
    the failing test case.

    Moreover, the issue (if any) is also extended with the new ``'filename'``
    property containing the name of the test case (as received in the ``test``
    argument).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall
            call.decorate(0)=fuzzinator.call.FileReaderDecorator

            [sut.foo.call]
            # assuming that foo takes one file as input specified on command line
            command=/home/alice/foo/bin/foo {test}
    """

    def decorator(self, **kwargs):
        def wrapper(fn):
            def reader(*args, **kwargs):
                issue = fn(*args, **kwargs)

                if issue is not None:
                    with open(kwargs['test'], 'rb') as f:
                        issue['filename'] = os.path.basename(kwargs['test'])
                        issue['test'] = f.read()

                return issue

            return reader
        return wrapper
