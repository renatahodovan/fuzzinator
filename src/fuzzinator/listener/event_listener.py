# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class EventListener:
    """
    A no-op base class for listeners that can get notified by
    :class:`fuzzinator.Controller` on various events of a fuzz sessions.

    .. note::

        Subclasses should be aware that some notification methods may be called
        from subprocesses.
    """

    def __init__(self, config):
        """
        :param configparser.ConfigParser config: Fuzzinator settings.
        """
        self.config = config

    def on_load_updated(self, load):
        """
        Invoked when the framework's load changes.

        :param int load: number between 0 and controller's capacity.
        """

    def on_fuzz_job_added(self, job_id, cost, sut, fuzzer, batch):
        """
        Invoked when a new (still inactive) fuzz job is instantiated.

        :param int job_id: a unique identifier of the new fuzz job.
        :param int cost: cost associated with the new fuzz job.
        :param str sut: short name of the SUT of the new fuzz job (name of the
            corresponding config section without the "sut." prefix).
        :param str fuzzer: short name of the new fuzz job (name of the
            corresponding config section without the "fuzz." prefix).
        :param batch: batch size of the new fuzz job, i.e., number of test cases
            requested from the fuzzer (may be ``inf``).
        :type batch: int, float
        """

    def on_reduce_job_added(self, job_id, cost, sut, issue_oid, issue_id, size):
        """
        Invoked when a new (still inactive) reduce job is instantiated.

        :param int job_id: a unique identifier of the new reduce job.
        :param int cost: cost associated with the new reduce job.
        :param str sut: short name of the SUT used in the new reduce job (name
            of the corresponding config section without the "sut." prefix).
        :param str issue_oid: ``'_id'`` property of the issue to be reduced.
        :param Any issue_id: ``'id'`` property of the issue to be reduced.
        :param int size: size of the test case associated with the issue to be
            reduced.
        """

    def on_update_job_added(self, job_id, cost, sut):
        """
        Invoked when a new (still inactive) update job is instantiated.

        :param int job_id: a unique identifier of the new update job.
        :param int cost: cost associated with the new update job.
        :param str sut: short name of the SUT to be updated (name of the
            corresponding config section without the "sut." prefix).
        """

    def on_validate_job_added(self, job_id, cost, sut, issue_oid, issue_id):
        """
        Invoked when a new (still inactive) validate job is instantiated.

        :param int job_id: a unique identifier of the new validate job.
        :param int cost: cost associated with the new validate job.
        :param str sut: short name of the SUT used in the new validate job (name
            of the corresponding config section without the "sut." prefix).
        :param str issue_oid: ``'_id'`` property of the issue to be validated.
        :param Any issue_id: ``'id'`` property of the issue to be validated.
        """

    def on_job_activated(self, job_id):
        """
        Invoked when a previously instantiated job is activated (started).

        :param int job_id: unique identifier of the activated job.
        """

    def on_job_progressed(self, job_id, progress):
        """
        Invoked when an activated job makes progress.

        :param int job_id: unique identifier of the progressing job.
        :param int progress: for fuzz jobs, this is the number of already
            generated tests (number between 0 and the job's batch size); for
            reduce jobs, this is the current size of the test case being reduced
            (number between the original test size and 0).
        """

    def on_job_removed(self, job_id):
        """
        Invoked when an active job has finished.

        :param int job_id: unique identifier of the finished job.
        """

    def on_issue_added(self, job_id, issue):
        """
        Invoked when a new issue is found.

        :param int job_id: identifier of the job that has found the issue.
        :param dict issue: the issue that was found (all relevant information -
            e.g., the SUT that reported the issue, the test case that triggered
            the issue, the fuzzer that generated the test case, the ID of the
            issue - is stored in appropriate properties of the issue).
        """

    def on_issue_invalidated(self, job_id, issue):
        """
        Invoked when an issue seems invalid.

        :param int job_id: identifier of the job that has invalidated the issue.
        :param dict issue: the issue object that did not pass re-validation
            (listener is free to decide how to react, an option is to remove the
            issue from the database).
        """

    def on_issue_updated(self, job_id, issue):
        """
        Invoked when the status of an issue changed.

        :param int job_id: identifier of the job that has updated the issue.
        :param dict issue: the issue object that has changed.
        """

    def on_issue_reduced(self, job_id, issue):
        """
        Invoked when an issue got reduced.

        :param int job_id: identifier of the job that has reduced the issue.
        :param dict issue: the issue object that got reduced.
        """

    def warning(self, job_id, msg):
        """
        Invoked on unexpected events.

        :param int job_id: identifier of the job that has signalled the warning
            (may be ``None`` if the warning was not signalled by a job but by
            the core).
        :param str msg: description of the problem.
        """

    def on_stats_updated(self):
        """
        Invoked when statistics about fuzzers, SUTs, and issues (e.g., execution
        counts, issue counts, unique issue counts) are updated in the
        framework's database.
        """
