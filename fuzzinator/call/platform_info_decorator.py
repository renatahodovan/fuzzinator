# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import platform

from .callable_decorator import CallableDecorator


class PlatformInfoDecorator(CallableDecorator):
    """
    Decorator for SUT calls to extend issues with 'platform' property.

    The new 'platform' issue property will contain the result of Python's
    platform.platform().

    Example configuration snippet:
    [sut.foo]
    #call=...
    call.decorate(0)=fuzzinator.call.PlatformInfoDecorator
    """

    def decorator(self, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                issue['platform'] = platform.platform()
                return issue

            return filter
        return wrapper
