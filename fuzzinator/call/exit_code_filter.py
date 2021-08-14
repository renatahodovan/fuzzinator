# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import as_bool, as_list
from .call_decorator import CallDecorator
from .non_issue import NonIssue


class ExitCodeFilter(CallDecorator):
    """
    Decorator filter for SUT calls that return issues with ``'exit_code'``
    property.

    **Mandatory parameter of the decorator:**

      - ``exit_codes``: if ``issue['exit_code']`` is not in the array of
        ``exit_codes``, the issue is filtered out; this behavior can be
        inverted by setting the ``'invert'`` property to True, thus
        keeping issues with exit code not listed in the array.

    **Optional parameter of the decorator:**

      - ``invert``: if it's true then exit code filtering mechanism is
        inverted (boolean value, False by default).

    The issues that are not filtered out are not changed in any way.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall
            call.decorate(0)=fuzzinator.call.ExitCodeFilter

            [sut.foo.call]
            command=/home/alice/foo/bin/foo -

            [sut.foo.call.decorate(0)]
            exit_codes=[139]
            invert=false
    """

    def __init__(self, *, exit_codes, invert=False, **kwargs):
        self.exit_codes = as_list(exit_codes)
        self.invert = as_bool(invert)

    def call(self, cls, obj, *, test, **kwargs):
        issue = super(cls, obj).__call__(test=test, **kwargs)
        if not issue:
            return issue

        if not self.invert:
            if issue['exit_code'] in self.exit_codes:
                return issue
        elif issue['exit_code'] not in self.exit_codes:
            return issue
        return NonIssue(issue)
