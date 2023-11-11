# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Reducer:
    """
    Abstract base class to represent test case reducers.
    """

    def __call__(self, *, sut_call, issue, on_job_progressed):
        """
        Reduce the test case of ``issue`` while ensuring that the reduced test
        case still triggers the original issue. Return a tuple consisting of a
        reduced test case for the issue (or ``None`` if the issue's current test
        case could not be reduced) and a (potentially empty) list of new issues
        that were discovered during test case reduction (if any).

        Raises :exc:`NotImplementedError` by default.

        :param Call sut_call: The SUT call that reported the original issue.
        :param dict[str, Any] issue: The original issue, the test case of which
            should be reduced.
        :param on_job_progressed: A bound
            :meth:`~fuzzinator.listener.EventListener.on_job_progressed` method
            with frozen ``job_id`` argument that may be notified about the
            progress of the reduction.
        :return: The reduced test case (if reduction was successful) and the
            list of new issues detected during reduction (if any).
        :rtype: tuple[Any or None, list[dict[str, Any]]]
        """
        raise NotImplementedError()
