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
    ({'init_foo': b'init_bar'}, {'foo': b'bar'})
])
@pytest.mark.parametrize('call, exp', [
    (mock_always_fail_call, {'foo': b'bar'}),
    (mock_never_fail_call, None),
    (MockAlwaysFailCall, {'init_foo': b'init_bar', 'foo': b'bar'}),
    (MockNeverFailCall,  None),
])
def test_platform_info_decorator(call, call_init_kwargs, call_kwargs, exp):
    call = fuzzinator.call.PlatformInfoDecorator()(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    out = call(**call_kwargs)

    if out is not None:
        assert out['platform'] is not None
        del out['platform']

    assert out == exp
