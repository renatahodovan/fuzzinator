# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

from .callable_decorator import CallableDecorator


class ExitCodeFilter(CallableDecorator):
    """
    Decorator filter for SUT calls that return issues with 'exit_code' property.

    Mandatory parameter of the decorator:
      - 'exit_codes': if issue['exit_code'] is not in the array of exit_codes,
        the issue is filtered out.

    The issues that are not filtered out are not changed in any way.

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.StdinSubprocessCall
    call.decorate(0)=fuzzinator.call.ExitCodeFilter

    [sut.foo.call]
    command=/home/alice/foo/bin/foo -

    [sut.foo.call.decorate(0)]
    exit_codes=[139]
    """

    def decorator(self, exit_codes, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                return issue if issue is not None and issue['exit_code'] in json.loads(exit_codes) else None

            return filter
        return wrapper
