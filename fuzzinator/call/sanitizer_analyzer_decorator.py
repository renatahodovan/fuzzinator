# Copyright (c) 2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from collections import OrderedDict

from . import CallableDecorator


class SanitizerAnalyzerDecorator(CallableDecorator):
    """
    Decorator for SUT calls to beautify the sanitizer-specific error messages and
    extend issues with the ``'security'`` property which describes the severity
    of the issue. This decorator has to be used with
    :class:`fuzzinator.call.SanitizerAutomatonFilter`.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            #call=...
            call.decorate(0)=fuzzinator.call.SanitizerAutomataFilter
            call.decorate(1)=fuzzinator.call.SanitizerAnalyzerDecorator
    """
    NONE = 'None'
    LOW = 'Low'  # pylint: disable=unused-variable
    MEDIUM = 'Medium'
    HIGH = 'High'

    san_error_types = {
        b'AddressSanitizer': OrderedDict([
            (b'attempting free on address which was not malloc()-ed', b'invalid-free'),
            (b'attempting double-free', b'double-free'),
            (b'double-free on ', b'double-free'),
            (b'FPE', b'floating-point-exception'),
        ]),

        b'UndefinedBehaviorSanitizer': OrderedDict([
            (b'member access within', b'bad-cast'),
            (b'member call on', b'bad-cast'),
            (b'downcast of', b'bad-cast'),
            (b'control flow integrity check', b'bad-cast'),
            (b'control flow integrity violation', b'bad-cast'),
            (b'division by zero', b'divide-by-zero'),
            (b'outside the range of representable values', b'float-cast-overflow'),
            (b'through pointer to incorrect function type', b'incorrect-function-pointer-type'),
            (b'out of bounds for type', b'index-out-of-bounds'),
            (b'not a valid value for type bool', b'invalid-bool-value'),
            (b'which is not a valid argument', b'invalid-builtin-use'),
            (b'misaligned address', b'misaligned-address'),
            (b'reached the end of a value-returning function', b'no-return-value'),
            (b'which is declared to never be null', b'invalid-null-argument'),
            (b'load of null pointer', b'null-dereference READ'),
            (b'binding to null pointer', b'null-dereference'),
            (b'access within null pointer', b'null-dereference'),
            (b'call on null pointer', b'null-dereference'),
            (b'store to null pointer', b'null-dereference WRITE'),
            (b'with insufficient space for an object of type', b'object-size'),
            (b'addition of unsigned offset', b'pointer-overflow'),
            (b'subtraction of unsigned offset', b'pointer-overflow'),
            (b'pointer index expression with base ', b'pointer-overflow'),
            (b'applying non-zero offset', b'pointer-overflow'),
            (b'applying zero offset to null pointer', b'pointer-overflow'),

            (b'null pointer returned from function declared to never return null', b'invalid-null-return'),
            (b'shift', b'undefined-shift'),
            (b'execution reached an unreachable program point', b'unreachable code'),
            (b'signed integer overflow', b'signed-integer-overflow'),
            (b'unsigned integer overflow', b'unsigned-integer-overflow'),
            (b'variable length array bound evaluates to non-positive value', b'non-positive-vla-bound-value'),

            # The following types are supersets of other types, and should be placed
            # at the end to avoid subsuming crashes from the more specialized types.
            (b'not a valid value for type', b'invalid-enum-value'),
            (b'integer overflow', b'integer-overflow'),
            (b'cannot be represented in type', b'integer-overflow'),
        ]),
    }

    severity = {
        MEDIUM: [
            b'container-overflow',
            b'global-buffer-overflow',
            b'heap-buffer-overflow',
            b'incorrect-function-pointer-type',
            b'index-out-of-bounds',
            b'memcpy-param-overlap',
            b'non-positive-vla-bound-value',
            b'object-size',
            b'stack-buffer-overflow',
            b'use-of-uninitialized-value',
            b'unknown-crash',
        ],
        HIGH: [
            b'bad-cast',
            b'heap-double-free',
            b'double-free',
            b'invalid-free',
            b'heap-use-after-free',
            b'use-after-poison',
        ],
    }

    def decorator(self, **kwargs):

        def is_null_dereference(address):
            try:
                return int(address, 16) < 0x1000
            except ValueError:
                return True

        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return issue

                if not issue.get('error_type'):
                    return issue

                sanitizer = b'UndefinedBehaviorSanitizer' if issue.get('ubsan') else issue.get('sanitizer')

                for pattern, name in self.san_error_types.get(sanitizer, {}).items():
                    if pattern in issue['error_type']:
                        issue['error_type'] = name
                        break

                if issue['error_type'] in [b'SEGV', b'access-violation']:
                    if is_null_dereference(issue['address'].decode('utf-8', errors='ignore')):
                        issue['error_type'] = b'null-dereference'
                    else:
                        issue['error_type'] = b'unknown-crash'

                for severity, error_types in self.severity.items():
                    if issue['error_type'] in error_types:
                        issue['security'] = severity
                        break
                else:
                    issue['security'] = self.NONE

                if b'WRITE' in issue.get('mem_access', b''):
                    issue['security'] = self.HIGH

                return issue
            return filter
        return wrapper
