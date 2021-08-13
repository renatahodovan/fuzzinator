# Copyright (c) 2017-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import shutil

from inspect import signature

logger = logging.getLogger(__name__)


class FileWriterDecorator(object):
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

    def __call__(self, fuzzer_class):
        decorator = self

        class DecoratedFuzzer(fuzzer_class):

            def __init__(self, **kwargs):
                signature(self.__init__).bind(**kwargs)
                super().__init__(**kwargs)
                self.test = None
            __init__.__signature__ = signature(fuzzer_class.__init__)

            def __enter__(self):
                super().__enter__()
                os.makedirs(decorator.work_dir, exist_ok=True)
                return self

            def __exit__(self, *exc):
                suppress = super().__exit__(*exc)
                shutil.rmtree(decorator.work_dir, ignore_errors=True)
                return suppress

            def __call__(self, *, index):
                self.test = super().__call__(index=index)

                if self.test is None:
                    return None

                file_path = os.path.join(decorator.work_dir, decorator.filename.format(uid=decorator.uid))
                decorator.uid += 1

                with open(file_path, 'w' if not isinstance(self.test, bytes) else 'wb') as f:
                    f.write(self.test if isinstance(self.test, (str, bytes)) else str(self.test))

                return file_path

        return DecoratedFuzzer
