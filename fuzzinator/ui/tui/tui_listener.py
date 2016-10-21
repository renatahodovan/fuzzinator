# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import os

from fuzzinator.listener import EventListener


class TuiListener(EventListener):

    def __init__(self, pipe, events, lock):
        for fn, _ in inspect.getmembers(EventListener, predicate=inspect.isfunction):
            setattr(self, fn, self.Trampoline(name=fn, pipe=pipe, events=events, lock=lock))

    class Trampoline(object):
        def __init__(self, name, pipe, events, lock):
            self.name = name
            self.pipe = pipe
            self.events = events
            self.lock = lock

        def __call__(self, **kwargs):
            with self.lock:
                self.events.put({'fn': self.name, 'kwargs': kwargs})
                os.write(self.pipe, b'x')
