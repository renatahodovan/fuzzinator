# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from jinja2 import Environment

from . import TemplateFormatter


class JinjaFormatter(TemplateFormatter):
    """
    Formatter class using the `Jinja2 <http://jinja.pocoo.org/>`_ template
    engine to render issue dictionaries.

    The formatter renders both the ``short`` and ``long`` versions
    of the issue according to the user-defined templates. If either of
    the templates is missing, then that version will be presented as an
    empty string (default).

    **Optional parameters of the formatter:**

      - ``short``: string template to define the issue summary template
        (default: empty string).

      - ``short_file``: path to a file containing the summary template
        (default: ``None``).

      - ``long``: string template to define the detailed issue template
        (default: empty string).

      - ``long_file``: path to a file containing the detailed issue template
        (default: ``None``).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.JinjaFormatter

            [sut.foo.formatter.init]
            short={{id}}
            long_file=/path/to/templates/foo.md
    """

    def __call__(self, issue, format='long'):
        template = Environment().from_string(self.templates[format])
        return template.render(issue)
