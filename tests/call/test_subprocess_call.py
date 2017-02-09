# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os

import fuzzinator

from common_call import blinesep, resources_dir


@pytest.mark.parametrize('command, cwd, env, no_exit_code, test, exp', [
    ('%s --print-args {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, None, 'foo', None),
    ('%s --print-args --exit-code 1 {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, None, 'foo', {'stdout': b'foo' + blinesep, 'stderr': b'', 'exit_code': 1}),
    ('%s --print-args --to-stderr --exit-code 1 {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, None, 'foo', {'stdout': b'', 'stderr': b'foo' + blinesep, 'exit_code': 1}),
    ('%s --print-args --exit-code 1 {test}' % os.path.join('.', 'mock_tool.py'), resources_dir, None, None, 'foo', {'stdout': b'foo' + blinesep, 'stderr': b'', 'exit_code': 1}),
    ('%s --print-env BAR --print-args --exit-code 1 {test}' % os.path.join('.', 'mock_tool.py'), resources_dir, '{"BAR": "baz"}', None, 'foo', {'stdout': b'foo' + blinesep + b'baz' + blinesep, 'stderr': b'', 'exit_code': 1}),
    ('%s --print-args --exit-code 0 {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, 'True', 'foo', {'stdout': b'foo' + blinesep, 'stderr': b'', 'exit_code': 0}),
])
def test_subprocess_call(command, cwd, env, no_exit_code, test, exp):
    assert fuzzinator.call.SubprocessCall(command, cwd=cwd, env=env, no_exit_code=no_exit_code, test=test) == exp
