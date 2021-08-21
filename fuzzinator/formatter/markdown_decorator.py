# Copyright (c) 2018-2022 Renata Hodovan, Akos Kiss.
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
    Decorator for formatters that produce their output in Markdown_ format.

    .. _Markdown: https://github.com/Python-Markdown/markdown

    This decorator converts the full string representation of an issue to HTML,
    while the summary remains untouched. The reason is that the summary usually
    serves as a subject in e-mails or as a title of bug reports. In these cases
    having an HTML-converted summary isn't suitable, while the main content,
    i.e., the ``long`` format, is expected to be in HTML.

    **Optional parameter of the decorator:**

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

    def call(self, cls, obj, *, issue):
        return markdown.markdown(super(cls, obj).__call__(issue=issue), extensions=self.extensions)
