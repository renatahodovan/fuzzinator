# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import re

from ..config import as_list
from .call_decorator import CallDecorator
from .non_issue import NonIssue


class RegexFilter(CallDecorator):
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

    def __init__(self, **kwargs):
        self.patterns = dict()
        for field, patterns_str in kwargs.items():
            self.patterns[field] = [re.compile(pattern, flags=re.MULTILINE | re.DOTALL) for pattern in as_list(patterns_str)]

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            issue = call(obj, test=test, **kwargs)
            if not issue:
                return issue

            updated = False
            for field, field_patterns in self.patterns.items():
                for pattern in field_patterns:
                    match = pattern.search(issue.get(field, ''))
                    if match is not None:
                        issue.update(match.groupdict())
                        updated = True

            return issue if updated else NonIssue(issue)

        return decorated_call
