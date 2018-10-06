# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import markdown

from ..call import CallableDecorator


class MarkdownDecorator(CallableDecorator):
    """
    Decorator for formatters that produce their output in Markdown format.

    This decorator converts the ``long`` version of an issue descriptor
    to HTML, while the ``short`` version remains untouched. The reason is
    that ``short`` versions usually serve as a summary in e-mail subjects
    or as a title of bug reports. In these cases having an HTML converted
    summary isn't suitable, while the main content, i.e., the ``long`` format,
    is expected to be in HTML.

    This decorator takes no custom input.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.StringFormatter
            formatter.decorate(0)=fuzzinator.formatter.MarkdownDecorator

            [sut.foo.formatter.init]
            long_file=/path/to/templates/foo.md
    """

    def decorator(self, **kwargs):
        def wrapper(fn):
            def render(issue, format='long', *args, **kwargs):
                formatted = fn(issue, format, *args, **kwargs)
                if format != 'short':
                    formatted = markdown.markdown(formatted, extensions=['extra'])
                return formatted

            return render
        return wrapper
