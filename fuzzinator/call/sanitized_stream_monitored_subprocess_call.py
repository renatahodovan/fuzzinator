# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .regex_automaton_filter import RegexAutomaton
from .sanitizer_automaton_filter import SanitizerAutomatonFilter
from .stream_monitored_subprocess_call import StreamMonitoredSubprocessCall


class SanitizedStreamMonitoredSubprocessCall(StreamMonitoredSubprocessCall):
    """
    SanitizedStreamMonitoredSubprocessCall is a specialized
    :class:`fuzzinator.call.StreamMonitoredSubprocessCall` that contains
    hard-wired regexes for ASAN and UBSAN error messages. Otherwise, it accepts
    parameters the same way as :class:`fuzzinator.call.StreamMonitoredSubprocessCall`.
    If custom end_patterns are specified, they take precedence over the predefined patterns.

    .. note::

       Not available on platforms without fcntl support (e.g., Windows).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.end_patterns.extend(RegexAutomaton.split_pattern(p) for p in SanitizerAutomatonFilter.STDERR_PATTERNS)
