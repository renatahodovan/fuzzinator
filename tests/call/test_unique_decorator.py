# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
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
    ({'init_foo': 'init_bar'}, {'foo': 'bar', 'baz': 'qux'})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {'properties': '["foo", "baz"]'}, {'foo': 'bar', 'baz': 'qux', 'id': 'bar qux'}),
    (mock_never_fail_call, {'properties': '["foo", "baz"]'}, None),
    (MockAlwaysFailCall, {'properties': '["init_foo", "baz"]'}, {'init_foo': 'init_bar', 'foo': 'bar', 'baz': 'qux', 'id': 'init_bar qux'}),
    (MockNeverFailCall, {'properties': '["init_foo", "baz"]'}, None),
])
def test_unique_decorator(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.UniqueIdDecorator(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
