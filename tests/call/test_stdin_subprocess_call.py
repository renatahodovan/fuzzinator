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
    ('%s --echo-stdin' % os.path.join(resources_dir, 'mock_tool.py'), None, None, b'foo', None),
    ('%s --echo-stdin --exit-code 1' % os.path.join(resources_dir, 'mock_tool.py'), None, None, b'foo', {'stdout': b'foo', 'stderr': b'', 'exit_code': 1}),
    ('%s --echo-stdin --to-stderr --exit-code 1' % os.path.join(resources_dir, 'mock_tool.py'), None, None, b'foo', {'stdout': b'', 'stderr': b'foo', 'exit_code': 1}),
    ('%s --echo-stdin --exit-code 1' % os.path.join('.', 'mock_tool.py'), resources_dir, None, b'foo', {'stdout': b'foo', 'stderr': b'', 'exit_code': 1}),
    ('%s --print-env BAR --echo-stdin --exit-code 1' % os.path.join('.', 'mock_tool.py'), resources_dir, '{"BAR": "baz"}', b'foo', {'stdout': b'baz\nfoo', 'stderr': b'', 'exit_code': 1}),
])
def test_stdin_subprocess_call(command, cwd, env, test, exp):
    assert fuzzinator.call.StdinSubprocessCall(command, cwd=cwd, env=env, test=test) == exp
