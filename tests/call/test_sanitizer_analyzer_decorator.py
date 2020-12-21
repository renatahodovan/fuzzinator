# Copyright (c) 2020 Tamas Keri
# Copyright (c) 2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest

import fuzzinator

from common_call import resources_dir, mock_always_fail_call


@pytest.mark.parametrize('call, call_kwargs, exp', [
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_container_overflow.txt')}, {'error_type': b'container-overflow', 'function': b'container_overflow()', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_container_overflow_debug.txt')}, {'error_type': b'container-overflow', 'function': b'container_overflow()', 'file': b'crashme.cpp', 'line': b'51', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_double_free.txt')}, {'error_type': b'double-free', 'function': b'double_free()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_double_free_debug.txt')}, {'error_type': b'double-free', 'function': b'double_free()', 'file': b'crashme.cpp', 'line': b'29', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_buffer_overflow.txt')}, {'error_type': b'heap-buffer-overflow', 'function': b'heap_buffer_overflow(int)', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_buffer_overflow_debug.txt')}, {'error_type': b'heap-buffer-overflow', 'function': b'heap_buffer_overflow(int)', 'file': b'crashme.cpp', 'line': b'38', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_use_after_free.txt')}, {'error_type': b'heap-use-after-free', 'function': b'heap_use_after_free()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_use_after_free_debug.txt')}, {'error_type': b'heap-use-after-free', 'function': b'heap_use_after_free()', 'file': b'crashme.cpp', 'line': b'61', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_null_pointer_dereference.txt')}, {'error_type': b'null-dereference', 'function': b'null_point_deref()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_null_pointer_dereference_debug.txt')}, {'error_type': b'null-dereference', 'function': b'null_point_deref()', 'file': b'crashme.cpp', 'line': b'68', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_overflow.txt')}, {'error_type': b'stack-overflow', 'function': b'stack_overflow()', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_overflow_debug.txt')}, {'error_type': b'stack-overflow', 'function': b'stack_overflow()', 'file': b'crashme.cpp', 'line': b'78', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_use_after_scope.txt')}, {'error_type': b'stack-use-after-scope', 'function': b'stack_use_after_scope()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_use_after_scope_debug.txt')}, {'error_type': b'stack-use-after-scope', 'function': b'stack_use_after_scope()', 'file': b'crashme.cpp', 'line': b'86', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_division_by_zero.txt')}, {'error_type': b'divide-by-zero', 'function': b'division_by_zero(int)', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_division_by_zero_debug.txt')}, {'error_type': b'divide-by-zero', 'function': b'division_by_zero(int)', 'file': b'crashme.cpp', 'line': b'100', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_global_buffer_overflow.txt')}, {'error_type': b'index-out-of-bounds', 'function': b'global_buffer_overflow(int)', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_global_buffer_overflow_debug.txt')}, {'error_type': b'index-out-of-bounds', 'function': b'global_buffer_overflow(int)', 'file': b'crashme.cpp', 'line': b'33', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_read.txt')}, {'error_type': b'null-dereference READ', 'function': b'null_deref_read()', 'line': b'105', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_read_debug.txt')}, {'error_type': b'null-dereference READ', 'function': b'null_deref_read()', 'file': b'crashme.cpp', 'line': b'105', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_write.txt')}, {'error_type': b'null-dereference WRITE', 'function': b'null_deref_write()', 'line': b'110', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_write_debug.txt')}, {'error_type': b'null-dereference WRITE', 'function': b'null_deref_write()', 'file': b'crashme.cpp', 'line': b'110', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_stack_buffer_overflow.txt')}, {'error_type': b'index-out-of-bounds', 'function': b'stack_buffer_overflow(int)', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_stack_buffer_overflow_debug.txt')}, {'error_type': b'index-out-of-bounds', 'function': b'stack_buffer_overflow(int)', 'file': b'crashme.cpp', 'line': b'74', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_shifts.txt')}, {'error_type': b'undefined-shift', 'file': b'crashme.cpp', 'line': b'91', 'char': b'7', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_shifts_debug.txt')}, {'error_type': b'undefined-shift', 'file': b'crashme.cpp', 'line': b'91', 'char': b'7', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_signed_integer_overflow.txt')}, {'error_type': b'signed-integer-overflow', 'file': b'crashme.cpp', 'line': b'96', 'char': b'7', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_signed_integer_overflow_debug.txt')}, {'error_type': b'signed-integer-overflow', 'file': b'crashme.cpp', 'line': b'96', 'char': b'7', 'security': 'None'}),
])
def test_sanitizer_analyzer_decorator(call, call_kwargs, exp):
    call = fuzzinator.call.SanitizerAnalyzerDecorator()(fuzzinator.call.SanitizerAutomatonFilter()(call))
    call_kwargs = dict(call_kwargs, test=call_kwargs['test'])

    with open(call_kwargs['test'], 'rb') as f:
        call_kwargs['stderr'] = f.read()

    result = call(**call_kwargs)
    for k, v in exp.items():
        assert result[k] == v, result[k] + b' != ' + v
