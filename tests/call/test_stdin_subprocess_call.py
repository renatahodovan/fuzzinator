# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest
import sys

import fuzzinator

from common_call import linesep, resources_dir


@pytest.mark.parametrize('command, cwd, env, no_exit_code, test, exp', [
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --echo-stdin', None, None, None, b'foo', fuzzinator.call.NonIssue({'stdout': 'foo', 'stderr': '', 'exit_code': 0})),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --echo-stdin --exit-code 1', None, None, None, b'foo', {'stdout': 'foo', 'stderr': '', 'exit_code': 1}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --echo-stdin --to-stderr --exit-code 1', None, None, None, b'foo', {'stdout': '', 'stderr': 'foo', 'exit_code': 1}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --echo-stdin --exit-code 1', resources_dir, None, None, b'foo', {'stdout': 'foo', 'stderr': '', 'exit_code': 1}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-env BAR --echo-stdin --exit-code 1', resources_dir, '{"BAR": "baz"}', None, b'foo', {'stdout': f'baz{linesep}foo', 'stderr': '', 'exit_code': 1}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --echo-stdin --exit-code 0', None, None, 'True', b'foo', {'stdout': 'foo', 'stderr': '', 'exit_code': 0}),
    ])
def test_stdin_subprocess_call(command, cwd, env, no_exit_code, test, exp):
    call = fuzzinator.call.StdinSubprocessCall(command=command, cwd=cwd, env=env, no_exit_code=no_exit_code)
    with call:
        out = call(test=test)
        assert out.pop('time')
        assert out == exp
