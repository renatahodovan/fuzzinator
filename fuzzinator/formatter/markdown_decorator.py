# Copyright (c) 2018-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import markdown

from ..config import as_list
from .formatter_decorator import FormatterDecorator


class MarkdownDecorator(FormatterDecorator):
    """
    Decorator for formatters that produce their output in
    `Markdown <https://github.com/Python-Markdown/markdown>`_ format.

    This decorator converts the ``long`` version of an issue descriptor
    to HTML, while the ``short`` version remains untouched. The reason is
    that ``short`` versions usually serve as a summary in e-mail subjects
    or as a title of bug reports. In these cases having an HTML-converted
    summary isn't suitable, while the main content, i.e., the ``long`` format,
    is expected to be in HTML.

    **Optional parameters of the decorator:**

      - ``extensions``: array of markdown extensions to enable (enable
        ``extra`` by default).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.StringFormatter
            formatter.decorate(0)=fuzzinator.formatter.MarkdownDecorator

            [sut.foo.formatter]
            long_file=/path/to/templates/foo.md

            [sut.foo.formatter.decorate(0)]
            extensions=["extra", "codehilite"]
    """

    def __init__(self, *, extensions=None, **kwargs):
        self.extensions = as_list(extensions) if extensions else ['extra']

    def call(self, cls, obj, *, issue, format='long'):
        formatted = super(cls, obj).__call__(issue=issue, format=format)
        if format != 'short':
            formatted = markdown.markdown(formatted, extensions=self.extensions)
        return formatted
