# Copyright (c) 2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import re

from ..config import as_list
from . import CallableDecorator
from . import NonIssue


class RegexAutomatonFilter(CallableDecorator):
    """
    Decorator filter for SUT calls to recognise patterns in the returned issue
    dictionaries and process them according to user-defined automata-like
    instructions.

    **Optional parameters of the decorator:**

      - key: array of patterns to match against the lines of ``issue[key]``
        (note that 'key' can be arbitrary, and multiple different keys can
        be given to the decorator).
        Two kinds of instructions can be assigned to every pattern which are
        encoded as a prefix to the regex pattern in the form of:
        `m<inst1><inst2> /<pattern>/`.
        The first instruction defines what to do with the groups of a matching
        pattern:
          - s: Save every group into the issue dictionary even if it exists.
          - a: Add only new fields to the issue dictionary.
          - c: Clear the whole issue dictionary.
          - n: Do not add any groups to the issue dictionary.
        The second instruction defines how to continue the processing of the
        input after a match:
          - c: Continue the processing of the current line with the next
            pattern.
          - s: Stop the processing of the current line and continue with the
            next line.
          - t: Terminate the processing of the whole input and return with the
            current version of the issue dictionary.
        If a pattern lacks the instructions and the slashes then it is
        interpreted as an `msc /<pattern>/`.

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
    regex_pattern = re.compile(b'm(?P<field_op>.)(?P<next_line_op>.) */(?P<regex>.*)/')

    @classmethod
    def split_pattern(cls, pattern):
        match = cls.regex_pattern.fullmatch(pattern)
        if match:
            return re.compile(match.group('regex')), chr(match.group('field_op')[0]), chr(match.group('next_line_op')[0])
        return re.compile(pattern), 's', 'c'

    def decorator(self, **kwargs):
        patterns = dict()
        for stream, desc in kwargs.items():
            if stream not in patterns:
                patterns[stream] = []
            patterns[stream].extend(self.split_pattern(p.encode('utf-8', errors='ignore')) for p in as_list(desc))

        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return issue

                issue_details = dict()
                for field, instructions in patterns.items():
                    # Process the field content line-by-line.
                    for line in issue.get(field, b'').splitlines():
                        for pattern, field_op, next_line_op in instructions:
                            match = pattern.search(line)
                            if not match:
                                continue

                            match_items = match.groupdict().items()
                            # Set every dictionary field from match groups.
                            if field_op == 's':
                                issue_details.update(match_items)
                            # Add new dictionary fields from match groups.
                            elif field_op == 'a':
                                issue_details.update((k, v) for k, v in match_items if k not in issue_details and k not in issue)
                            # Clear all dictionary fields.
                            elif field_op == 'c':
                                issue_details.clear()
                            # Do not add any groups to the issue dictionary.
                            elif field_op == 'n':
                                pass
                            else:
                                assert False, 'Unknown instruction for operation on fields: %s.' % field_op

                            # Terminate pattern matching and return with the current result.
                            if next_line_op == 't':
                                if not issue_details:
                                    return NonIssue(issue)
                                issue.update(issue_details)
                                return issue
                            # Stop the processing of the current line and continue with the next line.
                            if next_line_op == 's':
                                break
                            # Continue the processing of the current line with the next pattern.
                            if next_line_op == 'c':
                                pass
                            else:
                                assert False, 'Unknown instruction for input processing: %s.' % next_line_op

                if not issue_details:
                    return NonIssue(issue)

                issue.update(issue_details)
                return issue

            return filter
        return wrapper
