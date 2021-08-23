# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Multiton(type):

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._instances = {}

    def __call__(cls, *args, **kwargs):
        key = tuple(args) + tuple(sorted(kwargs.items()))
        instance = cls._instances.get(key, None)
        if instance is None:
            instance = super().__call__(*args, **kwargs)
            cls._instances[key] = instance
        return instance


class BaseTracker(metaclass=Multiton):

    def find_issue(self, query):
        pass

    def report_issue(self, **kwargs):
        pass

    def settings(self):
        return {}


class TrackerError(Exception):
    pass
