# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import as_list
from .call_decorator import CallDecorator


class AnonymizeDecorator(CallDecorator):
    """
    Decorator for SUT calls to anonymize issue properties.

    **Mandatory parameter of the decorator:**

      - ``old_text``: text to replace in issue properties.

    **Optional parameters of the decorator:**

      - ``new_text``: text to replace 'old_text' with (empty string by default).
      - ``properties``: array of properties to anonymize (anonymize all
        properties by default).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall
            call.decorate(0)=fuzzinator.call.AnonymizeDecorator

            [sut.foo.call]
            command=/home/alice/foo/bin/foo -

            [sut.foo.call.decorate(0)]
            old_text=/home/alice/foo
            new_text=FOO_ROOT
            properties=["stdout", "stderr"]
    """

    def __init__(self, *, old_text, new_text=None, properties=None, **kwargs):
        self.old_text = old_text
        self.new_text = new_text or ''
        self.properties = as_list(properties) if properties else None

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            issue = call(obj, test=test, **kwargs)
            if not issue:
                return issue

            keys = self.properties or list(issue.keys())
            for key in keys:
                issue[key] = issue.get(key, '').replace(self.old_text, self.new_text)

            return issue

        return decorated_call
