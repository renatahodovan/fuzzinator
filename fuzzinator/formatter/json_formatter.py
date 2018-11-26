# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json


def JsonFormatter(issue, format='long'):
    """
    A simple JSON-based issue formatter.

    This formatter does not take any custom instructions regarding the
    format, beyond that it's processed with JSON.
    The ``short`` version returns the ``id`` field of the input issue
    dictionary, while the ``long`` version returns a sorted and 4-space
    indented JSON dump of the issue. Because of these defaults, there
    is no need to define templates for the two versions (i.e., neither
    ``short`` nor ``long`` definitions are required).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            formatter=fuzzinator.formatter.JsonFormatter
    """

    if format == 'short':
        issue = issue.get('id', '')

    return json.dumps(issue, indent=4, default=str, sort_keys=True)
