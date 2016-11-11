# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


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
