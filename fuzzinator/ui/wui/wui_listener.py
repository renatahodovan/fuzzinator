# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect

from ...listener import EventListener


class Trampoline(object):

    def __init__(self, name, events, lock):
        self.name = name
        self.events = events
        self.lock = lock

    def __call__(self, **kwargs):
        with self.lock:
            try:
                self.events.put_nowait({'fn': self.name, 'kwargs': kwargs})
            except Exception:
                pass


class WuiListener(object):

    def __init__(self, events, lock):
        for fn, _ in inspect.getmembers(EventListener, predicate=inspect.isfunction):
            setattr(self, fn, Trampoline(name=fn, events=events, lock=lock))
