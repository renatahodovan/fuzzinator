# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from inspect import signature
from math import ceil, sqrt
from multiprocessing import Value


class AdaptiveTimeoutDecorator:
    """
    Decorator for SUT calls used in validate or reduce jobs. It helps
    dynamically optimizing the timeout of SUT calls. It works with SUTs
    that receive and respect a ``timeout`` kwarg both in their ``__init__``
    and ``__call__`` methods. Further requirement is that the issue dict
    provided by the decorated SUT call must contain ``time`` and ``id`` fields.
    Having these requirements fulfilled, the decorator adapts the timeout of
    the next call by taking the geometric mean of the previous two execution
    times that reproduced the expected issue.

    The decorator takes no parameter.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.SubprocessCall
            reduce_call=${call}
            reduce_call.decorate(0)=fuzzinator.call.AdaptiveTimeoutDecorator

            [sut.foo.call]
            command=./bin/foo {test}
            cwd=/home/alice/foo
            timeout=3
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, call_class):

        class DecoratedCall(call_class):

            def __init__(self, **kwargs):
                signature(self.__init__).bind(**kwargs)
                super().__init__(**kwargs)
                if 'timeout' in kwargs:
                    self.__initial_timeout = int(kwargs['timeout'])
                    # NOTE: not checking for parallelism, we simply prepare for it
                    self.__adapted_timeout = Value('i', -1, lock=False)
                else:
                    self.__initial_timeout = None
                    self.__adapted_timeout = None
            __init__.__signature__ = signature(call_class.__init__)

            def __call__(self, *, test, **kwargs):
                if self.__adapted_timeout:
                    adapted_timeout = self.__adapted_timeout.value
                    if adapted_timeout == -1:
                        if 'time' in kwargs:
                            # NOTE: geometric mean, rounded up, clamped to [1, __initial_timeout]
                            adapted_timeout = min(max(ceil(sqrt(kwargs['time'] * self.__initial_timeout)), 1), self.__initial_timeout)
                        else:
                            adapted_timeout = self.__initial_timeout
                        self.__adapted_timeout.value = adapted_timeout
                    kwargs['timeout'] = adapted_timeout

                issue = super().__call__(test=test, **kwargs)

                # NOTE: because of this check, decorator has to be in the stack when 'id' is already known
                if issue and 'id' in issue and 'id' in kwargs and issue['id'] == kwargs['id'] and 'time' in issue and self.__adapted_timeout:
                    # NOTE: geometric mean, rounded up, clamped to [1, __initial_timeout]
                    self.__adapted_timeout.value = min(max(ceil(sqrt(issue['time'] * self.__adapted_timeout.value)), 1), self.__initial_timeout)
                return issue

        return DecoratedCall
