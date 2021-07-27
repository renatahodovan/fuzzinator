# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Fuzzer(object):
    """
    Abstract base class to represent a (random) test case generator, a.k.a.
    fuzzer.
    """

    def __enter__(self):
        """
        Set up steps before requesting test cases from the fuzzer.

        No-op by default.
        """
        return self

    def __exit__(self, *exc):
        """
        Tear down steps after test case generation.

        No-op by default.
        """
        return False

    def __call__(self, *, index):
        """
        Request a test case from the fuzzer. Return the test case (or ``None``
        to signal that the fuzzer is exhausted and cannot generate more test
        cases).

        Raises :exc:`NotImplementedError` by default.

        :param int index: A running counter distinguishing test case requests
            in a fuzz job.
        :return: The generated test case, or ``None`` if the fuzzer is
            exhausted. The semantics of the generated test case is not
            restricted by the framework. It is the responsibility of the
            configuration to ensure that the SUT targeted by the fuzzer can be
            called with the tests case.
        :rtype: Any or None
        """
        raise NotImplementedError()
