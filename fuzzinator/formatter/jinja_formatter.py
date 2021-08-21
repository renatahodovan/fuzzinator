# Copyright (c) 2018-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from jinja2 import Environment

from .template_formatter import TemplateFormatter


class JinjaFormatter(TemplateFormatter):
    """
    Formatter class using the Jinja_ template engine to render issue
    dictionaries.

    .. _Jinja: https://jinja.palletsprojects.com/

    The formatter renders both the short and long versions of the issue
    according to the user-defined templates. If either of the templates is
    missing, then that version will be presented as an empty string (default).

    **Optional parameters of the formatter:**

      - ``short``: the issue summary template string (default: empty string).
      - ``short_file``: path to a file containing the issue summary template
        (default: ``None``).
      - ``long``: the detailed issue template string (default: empty string).
      - ``long_file``: path to a file containing the detailed issue template
        (default: ``None``).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.JinjaFormatter

            [sut.foo.formatter]
            short={{id}}
            long_file=/path/to/templates/foo.md
    """

    def render(self, *, issue, template):
        return Environment().from_string(template).render(issue)
