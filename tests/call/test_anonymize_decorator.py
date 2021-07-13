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
    ({'init_foo': 'init_baz', 'init_bar': 'init_baz'}, {'foo': 'baz', 'bar': 'baz'})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {'old_text': 'baz'}, {'foo': '', 'bar': ''}),
    (mock_always_fail_call, {'old_text': 'baz', 'new_text': 'qux'}, {'foo': 'qux', 'bar': 'qux'}),
    (mock_always_fail_call, {'old_text': 'baz', 'properties': '["foo"]'}, {'foo': '', 'bar': 'baz'}),
    (mock_always_fail_call, {'old_text': 'baz', 'new_text': 'qux', 'properties': '["foo"]'}, {'foo': 'qux', 'bar': 'baz'}),

    (mock_never_fail_call, {'old_text': 'baz'}, None),

    (MockAlwaysFailCall, {'old_text': 'baz'}, {'foo': '', 'bar': '', 'init_foo': 'init_', 'init_bar': 'init_'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'new_text': 'qux'}, {'foo': 'qux', 'bar': 'qux', 'init_foo': 'init_qux', 'init_bar': 'init_qux'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'properties': '["foo"]'}, {'foo': '', 'bar': 'baz', 'init_foo': 'init_baz', 'init_bar': 'init_baz'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'new_text': 'qux', 'properties': '["foo"]'}, {'foo': 'qux', 'bar': 'baz', 'init_foo': 'init_baz', 'init_bar': 'init_baz'}),

    (MockNeverFailCall, {'old_text': 'baz'}, None),
])
def test_anonymize_decorator(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.AnonymizeDecorator(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
