# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class NonIssue(dict):
    """
    Wrapper class for issue dictionaries to mark them as non-issue.

    The ``NonIssue`` class is a custom dictionary with a truth value forced to
    ``False``. With this change, it's capable to express that an issue
    dictionary doesn't encode a failure, without emptying it or converting to
    ``None``. The content of a ``NonIssue`` can be taken as a SUT response to a
    given test case and can be useful in feedback-driven fuzzing scenarios.
    """

    def __bool__(self):
        return False
