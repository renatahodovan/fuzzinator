# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import logging

logger = logging.getLogger(__name__)


class EventListener(object):
    """
    A no-op base class for listeners that can get notified by
    :class:`fuzzinator.Controller` on various events of a fuzz sessions.

    .. note::

        Subclasses should be aware that some notification methods may be called
        from subprocesses.
    """

    def update_load(self, load):
        """
        Invoked when the framework's load changes.

        :param int load: number between 0 and controller's capacity.
        """
        pass

    def new_fuzz_job(self, ident, fuzzer, sut, cost, batch):
        """
        Invoked when a new (still inactive) fuzz job is instantiated.

        :param int ident: a unique identifier of the new fuzz job.
        :param str fuzzer: short name of the new fuzz job (name of the
            corresponding config section without the "fuzz." prefix).
        :param str sut: short name of the SUT of the new fuzz job (name of the
            corresponding config section without the "sut." prefix).
        :param int cost: cost associated with the new fuzz job.
        :param batch: batch size of the new fuzz job, i.e., number of test cases
            requested from the fuzzer (may be ``inf``).
        :type batch: int, float
        """
        pass

    def new_reduce_job(self, ident, sut, cost, issue_id, size):
        """
        Invoked when a new (still inactive) reduce job is instantiated.

        :param int ident: a unique identifier of the new reduce job.
        :param str sut: short name of the SUT used in the new reduce job (name
            of the corresponding config section without the "sut." prefix).
        :param int cost: cost associated with the new reduce job.
        :param Any issue_id: ``'id'`` property of the issue to be reduced.
        :param int size: size of the test case associated with the issue to be
            reduced.
        """
        pass

    def new_update_job(self, ident, sut):
        """
        Invoked when a new (still inactive) update job is instantiated.

        :param int ident: a unique identifier of the new update job.
        :param str sut: short name of the SUT to be updated (name of the
            corresponding config section without the "sut." prefix).
        """
        pass

    def activate_job(self, ident):
        """
        Invoked when a previously instantiated job is activated (started).

        :param int ident: unique identifier of the activated job.
        """
        pass

    def job_progress(self, ident, progress):
        """
        Invoked when an activated job makes progress.

        :param int ident: unique identifier of the progressing job.
        :param int progress: for fuzz jobs, this is the number of already
            generated tests (number between 0 and the job's batch size); for
            reduce jobs, this is the current size of the test case being reduced
            (number between the original test size and 0).
        """
        pass

    def remove_job(self, ident):
        """
        Invoked when an active job has finished.

        :param int ident: unique identifier of the finished job.
        """
        pass

    def new_issue(self, issue):
        """
        Invoked when a new issue is found.

        :param dict issue: the issue that was found (all relevant information -
            e.g., the SUT that reported the issue, the test case that triggered
            the issue, the fuzzer that generated the test case, the ID of the
            issue - is stored in appropriate properties of the issue).
        """
        pass

    def invalid_issue(self, issue):
        """
        Invoked when an issue seems invalid.

        :param dict issue: the issue object that did not pass re-validation
            (listener is free to decide how to react, an option is to remove the
            issue from the database).
        """
        pass

    def update_issue(self, issue):
        """
        Invoked when the status of an issue changed.

        :param dict issue: the issue object that has changed.
        """
        pass

    def warning(self, msg):
        """
        Invoked on unexpected events.

        :param str msg: a string representation of the problem.
        """
        pass

    def update_fuzz_stat(self):
        """
        Invoked when statistics about fuzzers, SUTs, and issues (e.g., execution
        counts, crash counts, unique issue counts) are updated in the
        framework's database.
        """
        pass


class ListenerManager(object):
    """
    Class that registers listeners to various events and executes all of them
    when the event has triggered.
    """

    def __init__(self, listeners=None):
        """
        :param listeners: List of listener objects.
        """
        self.listeners = listeners or []

        class Trampoline(object):

            def __init__(self, manager, name):
                self.manager = manager
                self.name = name

            def __call__(self, **kwargs):
                for listener in self.manager.listeners:
                    try:
                        getattr(listener, self.name)(**kwargs)
                    except Exception as e:
                        logger.warning(e)

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
