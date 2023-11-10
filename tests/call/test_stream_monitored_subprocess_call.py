# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import sys

import pytest

import fuzzinator

from .common_call import linesep, resources_dir


@pytest.mark.skipif(not hasattr(fuzzinator.call, 'StreamMonitoredSubprocessCall'),
                    reason='platform-dependent component')
@pytest.mark.parametrize('command, cwd, env, end_patterns, test, exp', [
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args 42 {{test}}', None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': f'42{linesep}foo{linesep}', 'stderr': '', 'bar': 'foo'}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args --to-stderr 42 {{test}}', None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': '', 'stderr': f'42{linesep}foo{linesep}', 'bar': 'foo'}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args --exit-code 1 42 {{test}}', None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': f'42{linesep}foo{linesep}', 'stderr': '', 'bar': 'foo'}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args --to-stderr --exit-code 1 42 {{test}}', None, None, '["(?P<bar>[a-z]+)"]', 'foo', {'stdout': '', 'stderr': f'42{linesep}foo{linesep}', 'bar': 'foo'}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args --print-env FOO --exit-code 1 42 {{test}}', resources_dir, '{"FOO": "baz"}', '["(?P<bar>[a-z]+)"]', '42', {'stdout': f'42{linesep}42{linesep}baz{linesep}', 'stderr': '', 'bar': 'baz'}),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args --exit-code 1 42 {{test}}', None, None, '["(?P<bar>[a-z]+)"]', '42', fuzzinator.call.NonIssue({'stderr': '', 'stdout': f'42{linesep}42{linesep}'})),
])
def test_stream_monitored_subprocess_call(command, cwd, env, end_patterns, test, exp):
    call = fuzzinator.call.StreamMonitoredSubprocessCall(command=command, cwd=cwd, env=env, end_patterns=end_patterns)
    with call:
        out = call(test=test)

    if out is not None:
        del out['exit_code']
        assert out.pop('time')
    assert out == exp
