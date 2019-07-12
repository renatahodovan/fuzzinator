# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import platform

from . import CallableDecorator


class PlatformInfoDecorator(CallableDecorator):
    """
    Decorator for SUT calls to extend issues with ``'platform'`` and ``'node'``
    properties.

    The new ``'platform'`` issue property will contain the result of Python's
    :func:`platform.platform` and the ``'node'`` property will contain the
    result of :func:`platform.node`.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            #call=...
            call.decorate(0)=fuzzinator.call.PlatformInfoDecorator
    """

    def decorator(self, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return issue

                issue['platform'] = platform.platform()
                issue['node'] = platform.node()
                return issue

            return filter
        return wrapper
