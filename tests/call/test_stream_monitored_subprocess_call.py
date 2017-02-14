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


@pytest.mark.skipif(not hasattr(fuzzinator.call, 'StreamMonitoredSubprocessCall'),
                    reason='platform-dependent component')
@pytest.mark.parametrize('command, cwd, env, end_patterns, test, exp', [
    ('%s %s --print-args 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': b'42' + blinesep + b'foo' + blinesep, 'stderr': b'', 'bar': b'foo'}),
    ('%s %s --print-args --to-stderr 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': b'', 'stderr': b'42' + blinesep + b'foo' + blinesep, 'bar': b'foo'}),
    ('%s %s --print-args --exit-code 1 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': b'42' + blinesep + b'foo' + blinesep, 'stderr': b'', 'bar': b'foo'}),
    ('%s %s --print-args --to-stderr --exit-code 1 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': b'', 'stderr': b'42' + blinesep + b'foo' + blinesep, 'bar': b'foo'}),
    ('%s %s --print-args --print-env FOO --exit-code 1 42 {test}' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, '{"FOO": "baz"}', '["(?P<bar>[a-z]+)"]', '42', {'stdout': b'42' + blinesep + b'42' + blinesep + b'baz' + blinesep, 'stderr': b'', 'bar': b'baz'}),
    ('%s %s --print-args --exit-code 1 42 {test}' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None, '["(?P<bar>[a-z]+)"]', '42', None),
])
def test_stream_monitored_subprocess_call(command, cwd, env, end_patterns, test, exp):
    out = fuzzinator.call.StreamMonitoredSubprocessCall(command, cwd=cwd, env=env, end_patterns=end_patterns)(test=test)

    if out is not None:
        del out['exit_code']

    assert out == exp
