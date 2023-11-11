# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import as_list
from .call_decorator import CallDecorator


class UniqueIdDecorator(CallDecorator):
    """
    Decorator for SUT calls to extend issues with ``'id'`` property.

    **Mandatory parameter of the decorator:**

      - ``properties``: array of issue property names, which are concatenated
        (separated by a space) to form the new ``'id'`` property.

    **Example configuration snippet:**

        .. code-block:: ini

           [sut.foo]
           call=fuzzinator.call.StdinSubprocessCall
           call.decorate(0)=fuzzinator.call.RegexFilter
           call.decorate(1)=fuzzinator.call.UniqueIdDecorator

           [sut.foo.call]
           command=/home/alice/foo/bin/foo -

           [sut.foo.call.decorate(0)]
           stderr=[": (?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)"]

           [sut.foo.call.decorate(1)]
           properties=["msg", "file", "func"]
    """

    def __init__(self, *, properties, **kwargs):
        self.properties = as_list(properties) if properties else None

    def call(self, cls, obj, *, test, **kwargs):
        issue = super(cls, obj).__call__(test=test, **kwargs)
        if not issue:
            return issue

        prop_lst = [issue.get(prop, '') for prop in self.properties]
        issue['id'] = ' '.join(prop.decode('utf-8', errors='ignore') if isinstance(prop, bytes) else prop for prop in prop_lst)
        return issue
