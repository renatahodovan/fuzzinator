# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator

from .common_call import MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_bar'}, {'test': 'bar', 'stdout': '42baz42', 'stderr': '42QUX42'})
])
@pytest.mark.parametrize('call_class, dec_kwargs, exp', [
    (MockAlwaysFailCall, {}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]'}, {'init_foo': 'init_bar', 'test': 'bar', 'stdout': '42baz42', 'stderr': '42QUX42', 'xyz': 'baz'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[A-Z]+)"]'}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'stderr': '["(?P<zyx>[a-z]+)"]'}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': 'init_bar', 'test': 'bar', 'stdout': '42baz42', 'stderr': '42QUX42', 'zyx': 'QUX'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[a-z]+)"]'}, {'init_foo': 'init_bar', 'test': 'bar', 'stdout': '42baz42', 'stderr': '42QUX42', 'xyz': 'baz'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[A-Z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': 'init_bar', 'test': 'bar', 'stdout': '42baz42', 'stderr': '42QUX42', 'zyx': 'QUX'}),
    (MockAlwaysFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, {'init_foo': 'init_bar', 'test': 'bar', 'stdout': '42baz42', 'stderr': '42QUX42', 'xyz': 'baz', 'zyx': 'QUX'}),

    (MockNeverFailCall, {'stdout': '["(?P<xyz>[a-z]+)"]', 'stderr': '["(?P<zyx>[A-Z]+)"]'}, None),
])
def test_regex_filter(call_class, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call_class = fuzzinator.call.RegexFilter(**dec_kwargs)(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        issue = call(**call_kwargs)

    if exp is None:
        assert issue is None
    elif exp == fuzzinator.call.NonIssue:
        assert not issue
    else:
        assert issue == exp
