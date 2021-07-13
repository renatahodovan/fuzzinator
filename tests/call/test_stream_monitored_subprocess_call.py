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


@pytest.mark.skipif(not hasattr(fuzzinator.call, 'StreamMonitoredSubprocessCall'),
                    reason='platform-dependent component')
@pytest.mark.parametrize('command, cwd, env, end_patterns, test, exp', [
    ('%s %s --print-args 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': '42' + blinesep + 'foo' + blinesep, 'stderr': '', 'bar': 'foo'}),
    ('%s %s --print-args --to-stderr 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': '', 'stderr': '42' + blinesep + 'foo' + blinesep, 'bar': 'foo'}),
    ('%s %s --print-args --exit-code 1 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': '42' + blinesep + 'foo' + blinesep, 'stderr': '', 'bar': 'foo'}),
    ('%s %s --print-args --to-stderr --exit-code 1 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': '', 'stderr': '42' + blinesep + 'foo' + blinesep, 'bar': 'foo'}),
    ('%s %s --print-args --print-env FOO --exit-code 1 42 {test}' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, '{"FOO": "baz"}', '["(?P<bar>[a-z]+)"]', '42', {'stdout': '42' + blinesep + '42' + blinesep + 'baz' + blinesep, 'stderr': '', 'bar': 'baz'}),
    ('%s %s --print-args --exit-code 1 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', '42', None),
])
def test_stream_monitored_subprocess_call(command, cwd, env, end_patterns, test, exp):
    out = fuzzinator.call.StreamMonitoredSubprocessCall(command, cwd=cwd, env=env, end_patterns=end_patterns)(test=test)

    if out is not None:
        del out['exit_code']

    assert out == exp
