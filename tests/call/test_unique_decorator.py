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
    ({'init_foo': 'init_bar'}, {'test': 'bar', 'baz': 'qux'})
])
@pytest.mark.parametrize('call_class, dec_kwargs, exp', [
    (MockAlwaysFailCall, {'properties': '["init_foo", "baz"]'}, {'init_foo': 'init_bar', 'test': 'bar', 'baz': 'qux', 'id': 'init_bar qux'}),
    (MockNeverFailCall, {'properties': '["init_foo", "baz"]'}, None),
])
def test_unique_decorator(call_class, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call_class = fuzzinator.call.UniqueIdDecorator(**dec_kwargs)(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        assert call(**call_kwargs) == exp
