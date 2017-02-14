# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os
import sys

import fuzzinator

from common_call import blinesep, resources_dir


@pytest.mark.parametrize('command, cwd, env, test, exp', [
    ('%s %s --echo-stdin' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, b'foo', None),
    ('%s %s --echo-stdin --exit-code 1' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, b'foo', {'stdout': b'foo', 'stderr': b'', 'exit_code': 1}),
    ('%s %s --echo-stdin --to-stderr --exit-code 1' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, b'foo', {'stdout': b'', 'stderr': b'foo', 'exit_code': 1}),
    ('%s %s --echo-stdin --exit-code 1' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, None, b'foo', {'stdout': b'foo', 'stderr': b'', 'exit_code': 1}),
    ('%s %s --print-env BAR --echo-stdin --exit-code 1' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, '{"BAR": "baz"}', b'foo', {'stdout': b'baz' + blinesep + b'foo', 'stderr': b'', 'exit_code': 1}),
])
def test_stdin_subprocess_call(command, cwd, env, test, exp):
    assert fuzzinator.call.StdinSubprocessCall(command, cwd=cwd, env=env, test=test) == exp
