# Copyright (c) 2020-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import as_list
from .call_decorator import CallDecorator
from .non_issue import NonIssue
from .regex_automaton import RegexAutomaton


class RegexAutomatonFilter(CallDecorator):
    """
    Decorator filter for SUT calls to recognise patterns in the returned issue
    dictionaries and process them according to user-defined automaton-like
    instructions.

    **Optional parameters of the decorator:**

      - key: array of patterns to match against the lines of ``issue[key]``
        (note that 'key' can be arbitrary, and multiple different keys can
        be given to the decorator). The patterns and instructions are
        interpreted as defined in :class:`fuzzinator.call.RegexAutomaton`.


    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall
            call.decorate(0)=fuzzinator.call.RegexAutomatonFilter

            [sut.foo.call]
            command=/home/alice/foo/bin/foo -

            [sut.foo.call.decorate(0)]
            stderr=["mss /(?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)/"]
            backtrace=["mas /#[0-9]+ +0x[0-9a-f]+ in (?P<path>[^ ]+) .*? at (?P<file>[^:]+):(?P<line>[0-9]+)/"]
    """

    def __init__(self, **kwargs):
        self.patterns = {}
        for stream, desc in kwargs.items():
            self.patterns[stream] = [RegexAutomaton.split_pattern(p) for p in as_list(desc)]

    def call(self, cls, obj, *, test, **kwargs):
        issue = super(cls, obj).__call__(test=test, **kwargs)
        if not issue:
            return issue

        issue_details = {}
        for field, instructions in self.patterns.items():
            # Process the field content line-by-line.
            regex_automaton = RegexAutomaton(instructions, existing_fields=set(issue.keys()))
            terminate, _ = regex_automaton.process(issue.get(field, '').splitlines(), issue_details)
            if terminate:
                if not issue_details:
                    return NonIssue(issue)
                issue.update(issue_details)
                return issue

        if not issue_details:
            return NonIssue(issue)

        issue.update(issue_details)
        return issue
