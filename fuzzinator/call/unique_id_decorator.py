# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

from .callable_decorator import CallableDecorator


class UniqueIdDecorator(CallableDecorator):
    """
    Decorator for SUT calls to extend issues with 'id' property.

    Mandatory parameter of the decorator:
      - 'properties': array of issue property names, which are concatenated
        (separated by a space) to form the new 'id' property.

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.StdinSubprocessCall
    call.decorate(0)=fuzzinator.call.StreamRegexFilter
    call.decorate(1)=fuzzinator.call.UniqueIdDecorator

    [sut.foo.call]
    command=/home/alice/foo/bin/foo -

    [sut.foo.call.decorate(0)]
    stderr_patterns=[": (?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)"]

    [sut.foo.call.decorate(1)]
    properties=["msg", "file", "func"]
    """

    def decorator(self, properties, **kwargs):
        properties = json.loads(properties) if properties else None

        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                issue['id'] = b' '.join(issue.get(x, b'') for x in properties)
                return issue

            return filter
        return wrapper
