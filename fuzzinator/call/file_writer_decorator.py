# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from ..config import as_path
from .call_decorator import CallDecorator


class FileWriterDecorator(CallDecorator):
    """
    Decorator for SUTs that take input from a file: writes the test input to a
    temporary file and replaces the test input with the name of that file.

    **Mandatory parameter of the decorator:**

      - ``filename``: path pattern for the temporary file, which may contain the
        substring ``{uid}`` as a placeholder for a unique string (replaced by
        the decorator).

    The issue returned by the decorated SUT (if any) is extended with the new
    ``'filename'`` property containing the name of the generated file (although
    the file itself is removed).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall
            call.decorate(0)=fuzzinator.call.FileWriterDecorator

            [sut.foo.call]
            # assuming that foo takes one file as input specified on command line
            command=/home/alice/foo/bin/foo {test}

            [sut.foo.call.decorate(0)]
            filename=${fuzzinator:work_dir}/test-{uid}.txt
    """

    def __init__(self, *, filename, **kwargs):
        self.filename = filename

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            file_path = as_path(self.filename.format(uid='{pid}-{id}'.format(pid=os.getpid(), id=id(self))))
            if 'filename' in kwargs:
                # Ensure that the test case will be saved to the directory defined by the
                # config file and its name will be what is expected by the kwargs.
                file_path = os.path.join(os.path.dirname(file_path), kwargs['filename'])

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w' if not isinstance(test, bytes) else 'wb') as f:
                f.write(test)

            issue = call(obj, test=file_path, **kwargs)
            if issue:
                issue['filename'] = os.path.basename(file_path)

            os.remove(file_path)
            return issue

        return decorated_call
