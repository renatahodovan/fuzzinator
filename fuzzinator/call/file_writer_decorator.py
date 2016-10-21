# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from .callable_decorator import CallableDecorator


class FileWriterDecorator(CallableDecorator):
    """
    Decorator for SUTs that take input from a file: writes the test input to a
    temporary file and replaces the test input with the name of that file.

    Mandatory parameter of the decorator:
      - 'filename': path pattern for the temporary file, which may contain the
        substring "{uid}" as a placeholder for a unique string (replaced by the
        decorator).

    The issue returned by the decorated SUT (if any) is extended with the new
    'filename' property containing the name of the generated file (although the
    file itself is removed).

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.SubprocessCall
    call.decorator(0)=fuzzionator.call.FileWriterDecorator

    [sut.foo.call]
    # assuming that foo takes one file as input specified on command line
    command=/home/alice/foo/bin/foo {test}

    [sut.foo.call.decorator(0)]
    filename=${fuzzinator:work_dir}/test-{uid}.txt
    """

    def decorator(self, filename, **kwargs):
        def wrapper(fn):
            def writer(*args, **kwargs):
                file_content = kwargs['test']
                file_path = filename.format(uid='{pid}-{id}'.format(pid=os.getpid(), id=id(self))) if 'filename' not in kwargs else kwargs['filename']

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w' if not isinstance(file_content, bytes) else 'wb') as f:
                    f.write(file_content)

                kwargs['test'] = file_path
                issue = fn(*args, **kwargs)
                if issue is not None:
                    issue['filename'] = os.path.basename(file_path)

                os.remove(file_path)
                return issue

            return writer
        return wrapper
