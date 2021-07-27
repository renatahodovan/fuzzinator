# Copyright (c) 2020-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from collections import OrderedDict

from .call_decorator import CallDecorator


class SanitizerAnalyzerDecorator(CallDecorator):
    """
    Decorator for SUT calls to beautify the sanitizer-specific error messages and
    extend issues with the ``'security'`` property which describes the severity
    of the issue. This decorator has to be used with
    :class:`fuzzinator.call.SanitizerAutomatonFilter`.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            #call=...
            call.decorate(0)=fuzzinator.call.SanitizerAutomatonFilter
            call.decorate(1)=fuzzinator.call.SanitizerAnalyzerDecorator
    """
    NONE = 'None'
    LOW = 'Low'  # pylint: disable=unused-variable
    MEDIUM = 'Medium'
    HIGH = 'High'

    san_error_types = {
        'AddressSanitizer': OrderedDict([
            ('attempting free on address which was not malloc()-ed', 'invalid-free'),
            ('attempting double-free', 'double-free'),
            ('double-free on ', 'double-free'),
            ('FPE', 'floating-point-exception'),
        ]),

        'UndefinedBehaviorSanitizer': OrderedDict([
            ('member access within', 'bad-cast'),
            ('member call on', 'bad-cast'),
            ('downcast of', 'bad-cast'),
            ('control flow integrity check', 'bad-cast'),
            ('control flow integrity violation', 'bad-cast'),
            ('division by zero', 'divide-by-zero'),
            ('outside the range of representable values', 'float-cast-overflow'),
            ('through pointer to incorrect function type', 'incorrect-function-pointer-type'),
            ('out of bounds for type', 'index-out-of-bounds'),
            ('not a valid value for type bool', 'invalid-bool-value'),
            ('which is not a valid argument', 'invalid-builtin-use'),
            ('misaligned address', 'misaligned-address'),
            ('reached the end of a value-returning function', 'no-return-value'),
            ('which is declared to never be null', 'invalid-null-argument'),
            ('load of null pointer', 'null-dereference READ'),
            ('binding to null pointer', 'null-dereference'),
            ('access within null pointer', 'null-dereference'),
            ('call on null pointer', 'null-dereference'),
            ('store to null pointer', 'null-dereference WRITE'),
            ('with insufficient space for an object of type', 'object-size'),
            ('addition of unsigned offset', 'pointer-overflow'),
            ('subtraction of unsigned offset', 'pointer-overflow'),
            ('pointer index expression with base ', 'pointer-overflow'),
            ('applying non-zero offset', 'pointer-overflow'),
            ('applying zero offset to null pointer', 'pointer-overflow'),

            ('null pointer returned from function declared to never return null', 'invalid-null-return'),
            ('shift', 'undefined-shift'),
            ('execution reached an unreachable program point', 'unreachable code'),
            ('unsigned integer overflow', 'unsigned-integer-overflow'),
            ('signed integer overflow', 'signed-integer-overflow'),
            ('variable length array bound evaluates to non-positive value', 'non-positive-vla-bound-value'),

            # The following types are supersets of other types, and should be placed
            # at the end to avoid subsuming crashes from the more specialized types.
            ('not a valid value for type', 'invalid-enum-value'),
            ('integer overflow', 'integer-overflow'),
            ('cannot be represented in type', 'integer-overflow'),
        ]),
    }

    severity = {
        MEDIUM: [
            'container-overflow',
            'global-buffer-overflow',
            'heap-buffer-overflow',
            'incorrect-function-pointer-type',
            'index-out-of-bounds',
            'memcpy-param-overlap',
            'non-positive-vla-bound-value',
            'object-size',
            'stack-buffer-overflow',
            'use-of-uninitialized-value',
            'unknown-crash',
        ],
        HIGH: [
            'bad-cast',
            'heap-double-free',
            'double-free',
            'invalid-free',
            'heap-use-after-free',
            'use-after-poison',
        ],
    }

    def __init__(self, **kwargs):
        pass

    @staticmethod
    def is_null_dereference(address):
        try:
            return int(address, 16) < 0x1000
        except ValueError:
            return True

    def decorate(self, call):
        def decorated_call(obj, *, test, **kwargs):
            issue = call(obj, test=test, **kwargs)
            if not issue:
                return issue

            if not issue.get('error_type'):
                return issue

            sanitizer = 'UndefinedBehaviorSanitizer' if issue.get('ubsan') else issue.get('sanitizer')

            for pattern, name in self.san_error_types.get(sanitizer, {}).items():
                if pattern in issue['error_type']:
                    issue['error_type'] = name
                    break

            if issue['error_type'] in ['SEGV', 'access-violation']:
                if self.is_null_dereference(issue['address']):
                    issue['error_type'] = 'null-dereference'
                else:
                    issue['error_type'] = 'unknown-crash'

            for severity, error_types in self.severity.items():
                if issue['error_type'] in error_types:
                    issue['security'] = severity
                    break
            else:
                issue['security'] = self.NONE

            if 'WRITE' in issue.get('mem_access', ''):
                issue['security'] = self.HIGH

            return issue

        return decorated_call
