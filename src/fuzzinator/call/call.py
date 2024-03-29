# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Call:
    """
    Abstract base class to represent how a software-under-test (SUT) can be
    called/executed.
    """

    def __enter__(self):
        """
        Set up steps before calling the SUT potentially multiple times.

        No-op by default.
        """
        return self

    def __exit__(self, *exc):
        """
        Tear down steps after calling the SUT.

        No-op by default.
        """
        return False

    def __call__(self, *, test, **kwargs):
        """
        Call SUT with ``test`` as input. Return a dictionary object if the input
        triggered an issue in the SUT, or a value considered false otherwise.
        (``NonIssue``, a dictionary that always evaluates to false, can be
        returned to communicate details about an input that did not trigger an
        issue.) The returned issue dictionary (if any) *should* contain an
        ``'id'`` key that equals for issues that are not considered unique.

        Raises :exc:`NotImplementedError` by default.

        :param Any test: Input or test case, usually generated by a fuzzer. It
            is the responsibility of the configuration to ensure that the SUT
            can be called with the test case generated by the fuzzer.
        :return: The result of the SUT call.
        :rtype: dict[str, Any] or NonIssue or None
        """
        raise NotImplementedError()
