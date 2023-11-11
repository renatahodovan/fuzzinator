# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Formatter:
    """
    Abstract base class to represent issue formatters.
    """

    def __call__(self, *, issue):
        """
        Return a string representation of ``issue``, formatted in full.

        Raises :exc:`NotImplementedError` by default.

        :param dict[str, Any] issue: The issue to be formatted.
        :return: The string representation of the issue.
        :rtype: str
        """
        raise NotImplementedError()

    def summary(self, *, issue):
        """
        Return a summary description (preferably a single line of text
        representation) of ``issue``.

        Raises :exc:`NotImplementedError` by default.

        :param dict[str, Any] issue: The issue to be formatted.
        :return: The summarized string representation of the issue.
        :rtype: str
        """
        raise NotImplementedError()
