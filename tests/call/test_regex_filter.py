# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
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
    (mock_always_fail_call, {}, fuzzinator.call.NonIssue),
    (mock_always_fail_call, {'stdout': '["(?P<xyz>[a-z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (mock_always_fail_call, {'stdout': '["(?P<xyz>[A-Z]+)"]'}, fuzzinator.call.NonIssue),
    (mock_always_fail_call, {'stderr': '["(?P<zyx>[a-z]+)"]'}, fuzzinator.call.NonIssue),
    (mock_always_fail_call, {'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (mock_always_fail_call, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[a-z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (mock_always_fail_call, {'stdout': '["(?P<xyz>[A-Z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (mock_always_fail_call, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz', 'zyx': b'QUX'}),

    (mock_never_fail_call, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, None),

    (MockAlwaysFailCall, {}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[A-Z]+)"]'}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'stderr': '["(?P<zyx>[a-z]+)"]'}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[a-z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[A-Z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'zyx': b'QUX'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'stdout': b'42baz42', 'stderr': b'42QUX42', 'xyz': b'baz', 'zyx': b'QUX'}),

    (MockNeverFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, None),
])
def test_regex_filter(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.RegexFilter(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)
    issue = call(**call_kwargs)

    if exp is None:
        assert issue is None
    elif exp == fuzzinator.call.NonIssue:
        assert not issue
    else:
        assert issue == exp
