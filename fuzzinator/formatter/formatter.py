# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Formatter(object):
    """
    Abstract base class to represent issue formatters.
    """

    def __call__(self, *, issue, format='long'):
        """
        Return a string representation of ``issue``. If ``format`` is ``'long'``
        or not specified, the issue should be formatted in full, while if
        ``'short'`` is given, a summary description (preferably a single line of
        text) should be returned.

        Raises :exc:`NotImplementedError` by default.

        :param dict[str, Any] issue: The issue to be formatted.
        :param str format: The formatting instruction (``'long'`` or
            ``'short'``).
        :return: The full or summarized string representation of the issue.
        :rtype: str
        """
        raise NotImplementedError()
