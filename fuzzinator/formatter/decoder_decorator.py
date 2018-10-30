# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from copy import deepcopy

from ..call import CallableDecorator


class DecoderDecorator(CallableDecorator):
    """
    Decorator for formatters to stringify the issue dictionary values.

    This decorator decodes all the byte values of an issue dictionary
    to string *before* calling the formatter (i.e., it modifies its
    input rather than its output).

    **Optional parameters of the decorator:**

      - ``encoding``: encoding to use to decode byte values (``'utf-8'``
        by default).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.StringFormatter
            formatter.decorate(0)=fuzzinator.formatter.DecoderDecorator

            [sut.foo.formatter.init]
            long_file=/path/to/templates/foo.md

            [sut.foo.formatter.decorate(0)]
            encoding=utf-8
    """

    def decorator(self, encoding='utf-8', **kwargs):
        def wrapper(fn):
            def decoder(*args, **kwargs):
                def decode(value):
                    if isinstance(value, dict):
                        for k, v in value.items():
                            value[k] = decode(v)

                    elif isinstance(value, list):
                        for i, v in enumerate(value):
                            value[i] = decode(v)

                    elif isinstance(value, bytes):
                        value = value.decode(encoding, 'ignore')

                    return value

                kwargs['issue'] = decode(deepcopy(kwargs['issue']))
                return fn(*args, **kwargs)

            return decoder
        return wrapper
