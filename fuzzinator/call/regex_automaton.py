# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import re


class RegexAutomaton(object):
    """
    Auxiliary class to recognize patterns in textual data and process them with
    user-defined automaton-like instructions.

    Two kinds of instructions can be assigned to every pattern which are
    encoded as a prefix to the regex pattern in the form of:
    ``m<inst1><inst2> /<pattern>/``.
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
    interpreted as an ``msc /<pattern>/``.
    """
    regex_pattern = re.compile(r'm(?P<field_op>.)(?P<next_line_op>.) */(?P<regex>.*)/')

    def __init__(self, instructions, existing_fields=None):
        self.instructions = instructions
        self.existing_fields = existing_fields or []

    @classmethod
    def split_pattern(cls, pattern):
        match = cls.regex_pattern.fullmatch(pattern)
        if match:
            return re.compile(match.group('regex')), match.group('field_op')[0], match.group('next_line_op')[0]
        return re.compile(pattern), 's', 'c'

    def process_line(self, line, issue):
        updated = False
        for pattern, field_op, next_line_op in self.instructions:
            match = pattern.search(line)
            if not match:
                continue

            match_items = [(k, v) for k, v in match.groupdict().items() if v is not None]
            updated = updated or len(match_items) > 0
            # Set every dictionary field from match groups.
            if field_op == 's':
                issue.update(match_items)
            # Add new dictionary fields from match groups.
            elif field_op == 'a':
                issue.update((k, v) for k, v in match_items if k not in issue and k not in self.existing_fields)
            # Clear all dictionary fields.
            elif field_op == 'c':
                issue.clear()
            # Do not add any groups to the issue dictionary.
            elif field_op == 'n':
                pass
            else:
                raise ValueError(f'Unknown instruction for operation on fields: {field_op}.')

            # Terminate pattern matching and return with the current result.
            if next_line_op == 't':
                return True, updated
            # Stop the processing of the current line and continue with the next line.
            if next_line_op == 's':
                break
            # Continue the processing of the current line with the next pattern.
            if next_line_op == 'c':
                pass
            else:
                raise ValueError(f'Unknown instruction for input processing: {next_line_op}.')

        return False, updated

    def process(self, lines, issue):
        updated = False
        for line in lines:
            terminate, line_updated = self.process_line(line, issue)
            updated = updated or line_updated
            if terminate:
                return True, updated
        return False, updated
