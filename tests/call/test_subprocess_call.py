# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os

import fuzzinator

from common_call import resources_dir


@pytest.mark.parametrize('command, cwd, env, test, exp', [
    ('%s --print-args {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, 'foo', None),
    ('%s --print-args --exit-code 1 {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, 'foo', {'stdout': b'foo\n', 'stderr': b'', 'exit_code': 1}),
    ('%s --print-args --to-stderr --exit-code 1 {test}' % os.path.join(resources_dir, 'mock_tool.py'), None, None, 'foo', {'stdout': b'', 'stderr': b'foo\n', 'exit_code': 1}),
    ('%s --print-args --exit-code 1 {test}' % os.path.join('.', 'mock_tool.py'), resources_dir, None, 'foo', {'stdout': b'foo\n', 'stderr': b'', 'exit_code': 1}),
    ('%s --print-env BAR --print-args --exit-code 1 {test}' % os.path.join('.', 'mock_tool.py'), resources_dir, '{"BAR": "baz"}', 'foo', {'stdout': b'foo\nbaz\n', 'stderr': b'', 'exit_code': 1}),
])
def test_subprocess_call(command, cwd, env, test, exp):
    assert fuzzinator.call.SubprocessCall(command, cwd=cwd, env=env, test=test) == exp
