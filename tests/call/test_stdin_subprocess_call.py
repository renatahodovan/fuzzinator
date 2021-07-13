# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest
import sys

import fuzzinator

from common_call import blinesep, resources_dir


@pytest.mark.parametrize('command, cwd, env, no_exit_code, test, exp', [
    ('%s %s --echo-stdin' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, None, b'foo', fuzzinator.call.NonIssue({'stdout': 'foo', 'stderr': '', 'exit_code': 0})),
    ('%s %s --echo-stdin --exit-code 1' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, None, b'foo', {'stdout': 'foo', 'stderr': '', 'exit_code': 1}),
    ('%s %s --echo-stdin --to-stderr --exit-code 1' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, None, b'foo', {'stdout': '', 'stderr': 'foo', 'exit_code': 1}),
    ('%s %s --echo-stdin --exit-code 1' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, None, None, b'foo', {'stdout': 'foo', 'stderr': '', 'exit_code': 1}),
    ('%s %s --print-env BAR --echo-stdin --exit-code 1' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, '{"BAR": "baz"}', None, b'foo', {'stdout': 'baz' + blinesep + 'foo', 'stderr': '', 'exit_code': 1}),
    ('%s %s --echo-stdin --exit-code 0' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, 'True', b'foo', {'stdout': 'foo', 'stderr': '', 'exit_code': 0}),
    ])
def test_stdin_subprocess_call(command, cwd, env, no_exit_code, test, exp):
    assert fuzzinator.call.StdinSubprocessCall(command, cwd=cwd, env=env, no_exit_code=no_exit_code, test=test) == exp
