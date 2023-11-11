# Copyright (c) 2018-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import logging

from .event_listener import EventListener

logger = logging.getLogger(__name__)


class Trampoline:

    def __init__(self, manager, name):
        self.manager = manager
        self.name = name

    def __call__(self, **kwargs):
        for listener in self.manager.listeners:
            try:
                getattr(listener, self.name)(**kwargs)
            except Exception as e:
                logger.warning('Unhandled exception in listener %r.', self.name, exc_info=e)


class ListenerManager:
    """
    Class that registers listeners to various events and executes all of them
    when the event has triggered.
    """

    def __init__(self, listeners=None):
        """
        :param listeners: List of listener objects.
        """
        self.listeners = listeners or []

        for fn, _ in inspect.getmembers(EventListener, predicate=inspect.isfunction):
            setattr(self, fn, Trampoline(self, fn))

    def __iadd__(self, listener):
        """
        Register a new listener in the manager (trampoline to :meth:`add`).

        :param listener: The new listener to register.
        """
        self.add(listener)
        return self

    def add(self, listener):
        """
        Register a new listener in the manager.

        :param listener: The new listener to register.
        """
        self.listeners.append(listener)
