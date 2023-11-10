# Copyright (c) 2020-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .exporter import Exporter


class TestExporter(Exporter):
    """
    A simple exporter that extracts the test input (or the reduced test input,
    if it exists) from the issue.

    Note: This exporter expects the test input to be a :class:`str` or a
    :class:`bytes` instance.

    **Optional parameters of the exporter:**

      - ``extension``: the filename extension (including the leading period) to
        use when writing exported test inputs to file (default: no extension).

      - ``type``: the MIME (or content) type of the exported test inputs
        (default: no MIME type).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # see fuzzinator.call.*
            exporter=fuzzinator.exporter.TestExporter

            [sut.foo.exporter]
            extension=.txt
            type=text/plain
    """

    def __init__(self, *, extension=None, type=None, **kwargs):
        self.extension = extension
        self.type = type

    def __call__(self, *, issue):
        return issue.get('reduced') or issue['test']
