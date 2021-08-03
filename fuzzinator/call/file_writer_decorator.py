# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

from .call_decorator import CallDecorator

logger = logging.getLogger(__name__)


class FileWriterDecorator(CallDecorator):
    """
    Decorator for SUTs that take input from a file: writes the test input to a
    temporary file (relative to an implicit temporary working directory) and
    replaces the test input with the name of that file.

    **Mandatory parameter of the decorator:**

      - ``filename``: name pattern for the temporary file, which may contain the
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
            filename=test-{uid}.txt
    """

    def __init__(self, *, filename, work_dir, **kwargs):
        if os.path.basename(filename) != filename:
            logger.warning('specifying directories in filename parameter of fuzzinator.call.FileWriterDecorator is deprecated (%s) (explicit use of ${fuzzinator:work_dir}?)', filename)
            filename = os.path.basename(filename)

        self.filename = filename

        self.work_dir = work_dir
        self.uid = 0

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            if 'filename' in kwargs:
                # Ensure that the test case will be saved to the directory defined by the
                # config file and its name will be what is expected by the kwargs.
                filename = kwargs['filename']
            else:
                filename = self.filename.format(uid=self.uid)
                self.uid += 1
            file_path = os.path.join(self.work_dir, filename)

            os.makedirs(self.work_dir, exist_ok=True)
            with open(file_path, 'w' if not isinstance(test, bytes) else 'wb') as f:
                f.write(test)

            issue = call(obj, test=file_path, **kwargs)
            if issue:
                issue['filename'] = filename

            os.remove(file_path)
            return issue

        return decorated_call
