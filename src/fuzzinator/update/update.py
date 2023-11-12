# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Update:
    """
    Abstract base class to represent how a software-under-test (SUT) can be
    updated.
    """

    def __call__(self):
        """
        Update the SUT.

        Raises :exc:`NotImplementedError` by default.
        """
        raise NotImplementedError()
