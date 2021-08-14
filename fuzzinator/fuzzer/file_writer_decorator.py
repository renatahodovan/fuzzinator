# Copyright (c) 2017-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import shutil

from .fuzzer_decorator import FuzzerDecorator

logger = logging.getLogger(__name__)


class FileWriterDecorator(FuzzerDecorator):
    """
    Decorator for fuzzers that create str or bytes-like output. The decorator
    writes the test input to a temporary file (relative to an implicit temporary
    working directory) and replaces the output with the name of that file.

    **Mandatory parameter of the decorator:**

      - ``filename``: name pattern for the temporary file, which may contain the
        substring ``{uid}`` as a placeholder for a unique string (replaced by
        the decorator).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-random]
            sut=foo
            fuzzer=fuzzinator.fuzzer.RandomContent
            fuzzer.decorate(0)=fuzzinator.fuzzer.FileWriterDecorator

            [fuzz.foo-with-random.fuzzer.decorate(0)]
            filename=test-{uid}.txt
    """

    def __init__(self, *, filename, work_dir, **kwargs):
        if os.path.basename(filename) != filename:
            logger.warning('specifying directories in filename parameter of fuzzinator.fuzzer.FileWriterDecorator is deprecated (%s) (explicit use of ${fuzzinator:work_dir}?)', filename)
            filename = os.path.basename(filename)

        self.filename = filename

        self.work_dir = work_dir
        self.uid = 0

    def init(self, cls, obj, **kwargs):
        super(cls, obj).__init__(**kwargs)
        obj.test = None

    def enter(self, cls, obj):
        super(cls, obj).__enter__()
        os.makedirs(self.work_dir, exist_ok=True)
        return self

    def exit(self, cls, obj, *exc):
        suppress = super(cls, obj).__exit__(*exc)
        shutil.rmtree(self.work_dir, ignore_errors=True)
        return suppress

    def call(self, cls, obj, *, index):
        obj.test = super(cls, obj).__call__(index=index)
        if obj.test is None:
            return None

        file_path = os.path.join(self.work_dir, self.filename.format(uid=self.uid))
        self.uid += 1

        with open(file_path, 'w' if not isinstance(obj.test, bytes) else 'wb') as f:
            f.write(obj.test if isinstance(obj.test, (str, bytes)) else str(obj.test))

        return file_path
