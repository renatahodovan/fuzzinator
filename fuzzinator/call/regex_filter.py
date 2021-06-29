# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import re

from ..config import as_list
from . import CallableDecorator
from . import NonIssue


class RegexFilter(CallableDecorator):
    """
    Decorator filter for SUT calls to recognise patterns in the returned issue dictionaries.

    **Optional parameters of the decorator:**

      - key: array of patterns to match against ``issue[key]`` (note that 'key'
        can be arbitrary, and multiple different keys can be given to the decorator).

    If none of the patterns matches on any of the fields, the issue is filtered
    out. The issues that are not filtered out are extended with keys-values from
    the named groups of the matching regex pattern.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall
            call.decorate(0)=fuzzinator.call.RegexFilter

            [sut.foo.call]
            command=/home/alice/foo/bin/foo -

            [sut.foo.call.decorate(0)]
            stderr=["(?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)"]
            backtrace=["#[0-9]+ +0x[0-9a-f]+ in (?P<path>[^ ]+) .*? at (?P<file>[^:]+):(?P<line>[0-9]+)"]
    """

    def decorator(self, **kwargs):
        patterns = dict()
        for field, patterns_str in kwargs.items():
            patterns[field] = []
            for pattern in as_list(patterns_str):
                patterns[field].append(re.compile(pattern.encode('utf-8', errors='ignore'), flags=re.MULTILINE | re.DOTALL))

        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return issue

                updated = False
                for field, field_patterns in patterns.items():
                    for pattern in field_patterns:
                        match = pattern.search(issue.get(field, b''))
                        if match is not None:
                            issue.update(match.groupdict())
                            updated = True

                return issue if updated else NonIssue(issue)

            return filter
        return wrapper
