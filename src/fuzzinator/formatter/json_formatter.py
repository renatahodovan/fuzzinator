# Copyright (c) 2018-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

from .formatter import Formatter


class JsonFormatter(Formatter):
    """
    A simple JSON-based issue formatter.

    This formatter does not take any custom instructions regarding the format,
    beyond that it's processed with JSON. The summary description of an issue is
    its ``id`` field, while the full representation is a sorted and 4-space
    indented JSON dump of the issue.

    Because of these defaults, there is no need to define templates for the two
    versions (i.e., neither ``short`` nor ``long`` definitions are required).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.JsonFormatter
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, *, issue):
        return json.dumps(issue, indent=4, default=str, sort_keys=True)

    def summary(self, *, issue):
        return str(issue.get('id', ''))
