# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Exporter:
    """
    Abstract base class to represent issue exporters.
    """

    def __call__(self, *, issue):
        """
        Return a representation of ``issue`` that can be written to a file.
        The export format does not necessarily have to contain all elements of
        the issue dictionary.

        Raises :exc:`NotImplementedError` by default.

        :param dict[str, Any] issue: The issue to be exported.
        :return: A serializable representation of the issue, or parts of the
            issue.
        :rtype: str or bytes
        """
        raise NotImplementedError()
