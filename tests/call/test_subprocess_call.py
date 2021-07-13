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
    ('%s %s --print-args {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, None, 'foo', fuzzinator.call.NonIssue({'stdout': 'foo' + blinesep, 'stderr': '', 'exit_code': 0})),
    ('%s %s --print-args --exit-code 1 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, None, 'foo', {'stdout': 'foo' + blinesep, 'stderr': '', 'exit_code': 1}),
    ('%s %s --print-args --to-stderr --exit-code 1 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, None, 'foo', {'stdout': '', 'stderr': 'foo' + blinesep, 'exit_code': 1}),
    ('%s %s --print-args --exit-code 1 {test}' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, None, None, 'foo', {'stdout': 'foo' + blinesep, 'stderr': '', 'exit_code': 1}),
    ('%s %s --print-env BAR --print-args --exit-code 1 {test}' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, '{"BAR": "baz"}', None, 'foo', {'stdout': 'foo' + blinesep + 'baz' + blinesep, 'stderr': '', 'exit_code': 1}),
    ('%s %s --print-args --exit-code 0 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, 'True', 'foo', {'stdout': 'foo' + blinesep, 'stderr': '', 'exit_code': 0}),
])
def test_subprocess_call(command, cwd, env, no_exit_code, test, exp):
    assert fuzzinator.call.SubprocessCall(command, cwd=cwd, env=env, no_exit_code=no_exit_code, test=test) == exp
