# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import re

from .callable_decorator import CallableDecorator


class StreamRegexFilter(CallableDecorator):
    """
    Decorator filter for SUT calls that return issues with 'stdout' or 'stderr'
    properties.

    Optional parameters of the decorator:
      - 'stdout_patterns': array of patterns to match against issue['stdout'].
      - 'stderr_patterns': array of patterns to match against issue['stderr'].

    If none of the patterns matches on any of the streams, the issue is filtered
    out. The issues that are not filtered out are extended with keys-values from
    the named groups of the matching regex pattern.

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.StdinSubprocessCall
    call.decorate(0)=fuzzinator.call.StreamRegexFilter

    [sut.foo.call]
    command=/home/alice/foo/bin/foo -

    [sut.foo.call.decorate(0)]
    stderr_patterns=[": (?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)"]
    """

    def decorator(self, stdout_patterns=None, stderr_patterns=None, **kwargs):
        stdout_patterns = [re.compile(pattern.encode('utf-8', errors='ignore')) for pattern in json.loads(stdout_patterns)] if stdout_patterns else []
        stderr_patterns = [re.compile(pattern.encode('utf-8', errors='ignore')) for pattern in json.loads(stderr_patterns)] if stderr_patterns else []

        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                for pattern in stdout_patterns:
                    match = pattern.search(issue['stdout'])
                    if match is not None:
                        issue.update(match.groupdict())
                        return issue

                for pattern in stderr_patterns:
                    match = pattern.search(issue['stderr'])
                    if match is not None:
                        issue.update(match.groupdict())
                        return issue

                return None

            return filter
        return wrapper
