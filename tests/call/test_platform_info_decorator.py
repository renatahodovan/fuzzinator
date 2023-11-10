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
    ({'init_foo': 'init_bar'}, {'test': 'bar'})
])
@pytest.mark.parametrize('call_class, exp', [
    (MockAlwaysFailCall, {'init_foo': 'init_bar', 'test': 'bar'}),
    (MockNeverFailCall,  None),
])
def test_platform_info_decorator(call_class, call_init_kwargs, call_kwargs, exp):
    call_class = fuzzinator.call.PlatformInfoDecorator()(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        out = call(**call_kwargs)

    if out is not None:
        assert out['platform'] is not None
        del out['platform']

        assert out['node'] is not None
        del out['node']

    assert out == exp
