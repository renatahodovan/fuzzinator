# Copyright (c) 2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from inspect import isclass, isroutine


class FileWriterDecorator(object):
    """
    Decorator for fuzzers that create str or bytes-like output. The decorator writes
    the test input to a temporary file and replaces the output with the name of that file.

    **Mandatory parameter of the decorator:**

      - ``filename``: path pattern for the temporary file, which may contain the
        substring ``{uid}`` as a placeholder for a unique string (replaced by
        the decorator).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*

            [fuzz.foo-with-random]
            sut=sut.foo
            fuzzer=fuzzinator.fuzzer.RandomContent
            fuzzer.decorate(0)=fuzzionator.fuzzer.FileWriterDecorator

            [fuzz.foo-with-random.fuzzer.decorate(0)]
            filename=${fuzzinator:work_dir}/test-{uid}.txt
    """

    def __init__(self, filename):
        self.filename = filename

    def __call__(self, callable):
        ancestor = object if isroutine(callable) else callable

        class Inherited(ancestor):
            decorator = self

            def __init__(self, *args, **kwargs):
                if hasattr(ancestor, '__init__'):
                    super(Inherited, self).__init__(*args, **kwargs)
                self.file_path = self.decorator.filename.format(uid='{pid}-{id}'.format(pid=os.getpid(), id=id(self)))

            def __enter__(self, *args, **kwargs):
                if hasattr(ancestor, '__enter__'):
                    super(Inherited, self).__enter__(*args, **kwargs)
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                return self

            def __exit__(self, *exc):
                if hasattr(ancestor, '__exit__'):
                    super(Inherited, self).__exit__(*exc)

                if os.path.exists(self.file_path):
                    os.remove(self.file_path)

                return None

            def __call__(self, **kwargs):
                call = super(Inherited, self).__call__ if isclass(callable) else callable
                self.test = call(**kwargs)

                if self.test is None:
                    return None

                with open(self.file_path, 'w' if not isinstance(self.test, bytes) else 'wb') as f:
                    f.write(self.test)

                return self.file_path

        return Inherited
