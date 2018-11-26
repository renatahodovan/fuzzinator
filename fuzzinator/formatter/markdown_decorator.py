# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import markdown

from ..call import CallableDecorator


class MarkdownDecorator(CallableDecorator):
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

            [sut.foo.formatter.init]
            long_file=/path/to/templates/foo.md

            [sut.foo.formatter.decorate(0)]
            extensions=["extra", "codehilite"]
    """

    def decorator(self, extensions=None, **kwargs):
        extensions = ['extra'] if extensions is None else json.loads(extensions) if isinstance(extensions, str) else extensions
        def wrapper(fn):
            def render(*args, **kwargs):
                formatted = fn(*args, **kwargs)
                if kwargs.get('format', 'long') != 'short':
                    formatted = markdown.markdown(formatted, extensions=extensions)
                return formatted

            return render
        return wrapper
