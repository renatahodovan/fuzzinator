# Copyright (c) 2018-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from copy import deepcopy

from .formatter_decorator import FormatterDecorator


class DecoderDecorator(FormatterDecorator):
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

            [sut.foo.formatter]
            long_file=/path/to/templates/foo.md

            [sut.foo.formatter.decorate(0)]
            encoding=utf-8
    """

    def __init__(self, *, encoding='utf-8', **kwargs):
        self.encoding = encoding

    def decode(self, value):
        if isinstance(value, dict):
            for k, v in value.items():
                value[k] = self.decode(v)

        elif isinstance(value, list):
            for i, v in enumerate(value):
                value[i] = self.decode(v)

        elif isinstance(value, bytes):
            value = value.decode(self.encoding, 'ignore')

        return value

    def call(self, cls, obj, *, issue, format='long'):
        return super(cls, obj).__call__(issue=self.decode(deepcopy(issue)), format=format)
