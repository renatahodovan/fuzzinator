# Copyright (c) 2020 Tamas Keri
# Copyright (c) 2020-2021 Renata Hodovan, Akos Kiss.
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
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_container_overflow.txt')}, {'error_type': 'container-overflow', 'function': 'container_overflow()', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_container_overflow_debug.txt')}, {'error_type': 'container-overflow', 'function': 'container_overflow()', 'file': 'crashme.cpp', 'line': '51', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_double_free.txt')}, {'error_type': 'double-free', 'function': 'double_free()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_double_free_debug.txt')}, {'error_type': 'double-free', 'function': 'double_free()', 'file': 'crashme.cpp', 'line': '29', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_buffer_overflow.txt')}, {'error_type': 'heap-buffer-overflow', 'function': 'heap_buffer_overflow(int)', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_buffer_overflow_debug.txt')}, {'error_type': 'heap-buffer-overflow', 'function': 'heap_buffer_overflow(int)', 'file': 'crashme.cpp', 'line': '38', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_use_after_free.txt')}, {'error_type': 'heap-use-after-free', 'function': 'heap_use_after_free()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_heap_use_after_free_debug.txt')}, {'error_type': 'heap-use-after-free', 'function': 'heap_use_after_free()', 'file': 'crashme.cpp', 'line': '61', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_null_pointer_dereference.txt')}, {'error_type': 'null-dereference', 'function': 'null_point_deref()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_null_pointer_dereference_debug.txt')}, {'error_type': 'null-dereference', 'function': 'null_point_deref()', 'file': 'crashme.cpp', 'line': '68', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_overflow.txt')}, {'error_type': 'stack-overflow', 'function': 'stack_overflow()', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_overflow_debug.txt')}, {'error_type': 'stack-overflow', 'function': 'stack_overflow()', 'file': 'crashme.cpp', 'line': '78', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_use_after_scope.txt')}, {'error_type': 'stack-use-after-scope', 'function': 'stack_use_after_scope()', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'asan_stack_use_after_scope_debug.txt')}, {'error_type': 'stack-use-after-scope', 'function': 'stack_use_after_scope()', 'file': 'crashme.cpp', 'line': '86', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_division_by_zero.txt')}, {'error_type': 'divide-by-zero', 'function': 'division_by_zero(int)', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_division_by_zero_debug.txt')}, {'error_type': 'divide-by-zero', 'function': 'division_by_zero(int)', 'file': 'crashme.cpp', 'line': '100', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_global_buffer_overflow.txt')}, {'error_type': 'index-out-of-bounds', 'function': 'global_buffer_overflow(int)', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_global_buffer_overflow_debug.txt')}, {'error_type': 'index-out-of-bounds', 'function': 'global_buffer_overflow(int)', 'file': 'crashme.cpp', 'line': '33', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_read.txt')}, {'error_type': 'null-dereference READ', 'function': 'null_deref_read()', 'line': '105', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_read_debug.txt')}, {'error_type': 'null-dereference READ', 'function': 'null_deref_read()', 'file': 'crashme.cpp', 'line': '105', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_write.txt')}, {'error_type': 'null-dereference WRITE', 'function': 'null_deref_write()', 'line': '110', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_null_deref_write_debug.txt')}, {'error_type': 'null-dereference WRITE', 'function': 'null_deref_write()', 'file': 'crashme.cpp', 'line': '110', 'security': 'High'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_stack_buffer_overflow.txt')}, {'error_type': 'index-out-of-bounds', 'function': 'stack_buffer_overflow(int)', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_asan_stack_buffer_overflow_debug.txt')}, {'error_type': 'index-out-of-bounds', 'function': 'stack_buffer_overflow(int)', 'file': 'crashme.cpp', 'line': '74', 'security': 'Medium'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_shifts.txt')}, {'error_type': 'undefined-shift', 'file': 'crashme.cpp', 'line': '91', 'char': '7', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_shifts_debug.txt')}, {'error_type': 'undefined-shift', 'file': 'crashme.cpp', 'line': '91', 'char': '7', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_signed_integer_overflow.txt')}, {'error_type': 'signed-integer-overflow', 'file': 'crashme.cpp', 'line': '96', 'char': '7', 'security': 'None'}),
    (mock_always_fail_call, {'test': os.path.join(resources_dir, 'sanitizer_data', 'ubsan_signed_integer_overflow_debug.txt')}, {'error_type': 'signed-integer-overflow', 'file': 'crashme.cpp', 'line': '96', 'char': '7', 'security': 'None'}),
])
def test_sanitizer_analyzer_decorator(call, call_kwargs, exp):
    call = fuzzinator.call.SanitizerAnalyzerDecorator()(fuzzinator.call.SanitizerAutomatonFilter()(call))
    call_kwargs = dict(call_kwargs, test=call_kwargs['test'])

    with open(call_kwargs['test'], 'r') as f:
        call_kwargs['stderr'] = f.read()

    result = call(**call_kwargs)
    for k, v in exp.items():
        assert result[k] == v, result[k] + ' != ' + v
