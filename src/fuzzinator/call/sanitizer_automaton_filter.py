# Copyright (c) 2020-2021 Renata Hodovan, Akos Kiss.
# Copyright (c) 2020 Tamas Keri.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import as_list
from .regex_automaton import RegexAutomaton
from .regex_automaton_filter import RegexAutomatonFilter


class SanitizerAutomatonFilter(RegexAutomatonFilter):
    """
    SanitizerAutomatonFilter is a specialized :class:`fuzzinator.call.RegexAutomatonFilter`
    that contains hard-wired regexes for ASAN and UBSAN error messages. The streams where
    these regexes are looked for can be defined with the ``sanitized_properties`` parameter.
    Otherwise, it accepts optional parameters the same way as
    :class:`fuzzinator.call.RegexAutomatonFilter`. If they are specified, they take precedence
    over the predefined patterns. If an ASAN or UBSAN specific pattern is recognized, then
    issue dictionary will be extended with the ``error_type`` field.

    **Optional parameter of the decorator:**

      - ``sanitized_properties``: array of field names in the issue dictionary where the
        patterns are looked for (default: ``["stderr"]``).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StdinSubprocessCall
            call.decorate(0)=fuzzinator.call.SanitizerAutomatonFilter

            [sut.foo.call]
            command=/home/alice/foo/bin/foo -

            [sut.foo.call.decorate(0)]
            stdout=["mss /(?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)/"]
            backtrace=["mas /#[0-9]+ +0x[0-9a-f]+ in (?P<path>[^ ]+) .*? at (?P<file>[^:]+):(?P<line>[0-9]+)/"]
            sanitized_properties=["stdout"]
    """

    STACK_PREFIX = r'#(?P<frame_id>\d+)\s+(?P<address>[xX\da-fA-F]+)\s+'
    STACK_FUNCTION_OFFSET = r'in\s+(?P<function>.+?)\s*(\+(?P<offset>[xX\da-fA-F]+))?\s+'
    STACK_FILE_LINE_CHAR = r'(?P<file>[^()]+?):(?P<line>\d+)(?::(?P<char>\d+))?'
    STACK_MODULE_OFFSET = r'\((?P<module>[^+]+)(\+(?P<module_offset>[xX\da-fA-F]+))?\)'
    STACK_FUNCTION_MODULE_OFFSET = r'in\s*(?P<function>.+?)\s+\((?P<module>.+?)\+(?P<module_offset>[xX\da-fA-F]+)\)'

    SANITIZER_PATTERNS = [
        r'mns /libsystem_platform|libclang_rt|libdyld|libc.so|glibc|libasan.so/',
        r'mac /The signal is caused by a (?P<mem_access>[A-Z]+) memory access/',  # ASAN_READ_OR_WRITE_REGEX1
        r'mac /(?P<mem_access>[A-Z]+ of size \d+)/',  # ASAN_READ_OR_WRITE_REGEX2
        r'mas /\s+(?P<sanitizer>.+?Sanitizer)\s*:\s+(?P<error_type>.+?) on (?P<address_type>unknown address|address|)\s*(?P<address>[xX0-9a-fA-F]+)/',
        # SAN_ADDR_REGEX
        r'mas /^((?P<file>[^: ]+):(?P<line>\d+)(?::(?P<char>\d+))?:\s+)?(?P<ubsan>runtime error): (?P<error_type>.*)/',  # UBSAN_RUNTIME_ERROR_REGEX

        r'mac /(?P<error_type>Received signal 11 SEGV_[A-Z]+) ([0-9a-f]*)/',  # GENERIC_SEGV_HANDLER_REGEX
        # STACK_FRAME_REGEXES:
        r'mat /' + STACK_PREFIX + STACK_FUNCTION_OFFSET + STACK_FILE_LINE_CHAR + r'/',
        r'mat /' + STACK_PREFIX + STACK_FUNCTION_OFFSET + STACK_MODULE_OFFSET + r'/',
        r'mat /' + STACK_PREFIX + STACK_FUNCTION_MODULE_OFFSET + r'/',
        r'mat /' + STACK_PREFIX + STACK_FUNCTION_OFFSET + r'/',
        r'mas /' + STACK_PREFIX + STACK_MODULE_OFFSET + r'/',
        r'mac /pc (?P<pc_zero>\(nil\)|0x00000000|0x000000000000)/',  # STACK_FRAME_ZERO
    ]

    def __init__(self, sanitized_properties=None, **kwargs):
        super().__init__(**kwargs)
        sanitized_properties = as_list(sanitized_properties) if sanitized_properties else ['stderr']

        for prop in sanitized_properties:
            if prop not in self.patterns:
                self.patterns[prop] = []
            self.patterns[prop].extend(RegexAutomaton.split_pattern(p) for p in self.SANITIZER_PATTERNS)
