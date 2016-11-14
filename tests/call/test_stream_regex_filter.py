# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import pytest

import fuzzinator

from common_call import mock_always_fail_call, mock_never_fail_call, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': b'init_bar'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42'})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {}, None),
    (mock_always_fail_call, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (mock_always_fail_call, {'stdout_patterns': '["(?P<xyz>[A-Z]+)"]'}, None),
    (mock_always_fail_call, {'stderr_patterns': '["(?P<zyx>[a-z]+)"]'}, None),
    (mock_always_fail_call, {'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (mock_always_fail_call, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]', 'stderr_patterns': '["(?P<zyx>[a-z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (mock_always_fail_call, {'stdout_patterns': '["(?P<xyz>[A-Z]+)"]', 'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (mock_always_fail_call, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]', 'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),

    (mock_never_fail_call, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]', 'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, None),

    (MockAlwaysFailCall, {}, None),
    (MockAlwaysFailCall, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (MockAlwaysFailCall, {'stdout_patterns': '["(?P<xyz>[A-Z]+)"]'}, None),
    (MockAlwaysFailCall, {'stderr_patterns': '["(?P<zyx>[a-z]+)"]'}, None),
    (MockAlwaysFailCall, {'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (MockAlwaysFailCall, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]', 'stderr_patterns': '["(?P<zyx>[a-z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (MockAlwaysFailCall, {'stdout_patterns': '["(?P<xyz>[A-Z]+)"]', 'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (MockAlwaysFailCall, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]', 'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),

    (MockNeverFailCall, {'stdout_patterns': '["(?P<xyz>[a-z]+)"]', 'stderr_patterns': '["(?P<zyx>[A-Z]+)"]'}, None),
])
def test_stream_regex_filter(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.StreamRegexFilter(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
