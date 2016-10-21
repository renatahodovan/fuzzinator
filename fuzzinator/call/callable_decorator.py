# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from inspect import isclass, isroutine


class CallableDecorator(object):

    def __init__(self, *args, **kwargs):
        self.decorator_args = args
        self.decorator_kwargs = kwargs

    # To be overridden by descendants.
    def decorator(self, *args, **kwargs):
        def wrapper(fn):
            return fn
        return wrapper

    def __call__(self, callable):
        if isclass(callable):
            class Inherited(callable):
                @self.decorator(*self.decorator_args, **self.decorator_kwargs)
                def __call__(self, *args, **kwargs):
                    return callable.__call__(self, *args, **kwargs)
            return Inherited

        if isroutine(callable):
            return self.decorator(*self.decorator_args, **self.decorator_kwargs)(callable)
