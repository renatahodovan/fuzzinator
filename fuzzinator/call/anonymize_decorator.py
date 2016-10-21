# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

from .callable_decorator import CallableDecorator


class AnonymizeDecorator(CallableDecorator):
    """
    Decorator for SUT calls to anonymize issue properties.

    Mandatory parameter of the decorator:
      - 'old_text': text to replace in issue properties.
    Optional parameters of the decorator:
      - 'new_text': text to replace 'old_text' with (empty string by default).
      - 'properties': array of properties to anonymize (anonymize all properties
        by default).

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.StdinSubprocessCall
    call.decorate(0)=fuzzinator.call.AnonymizeDecorator

    [sut.foo.call]
    command=/home/alice/foo/bin/foo -

    [sut.foo.call.decorate(0)]
    old_text=/home/alice/foo
    new_text=FOO_ROOT
    properties=["stdout", "stderr"]
    """

    def decorator(self, old_text, new_text=None, properties=None, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                if properties:
                    ks = json.loads(properties)
                else:
                    ks = list(issue.keys())

                for key in ks:
                    issue[key] = issue[key].replace(bytes(old_text, 'utf-8'), bytes(new_text or '', 'utf-8'))

                return issue

            return filter
        return wrapper
