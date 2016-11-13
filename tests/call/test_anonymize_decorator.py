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
    ({'init_foo': b'init_baz', 'init_bar': b'init_baz'}, {'foo': b'baz', 'bar': b'baz'})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {'old_text': 'baz'}, {'foo': b'', 'bar': b''}),
    (mock_always_fail_call, {'old_text': 'baz', 'new_text': 'qux'}, {'foo': b'qux', 'bar': b'qux'}),
    (mock_always_fail_call, {'old_text': 'baz', 'properties': '["foo"]'}, {'foo': b'', 'bar': b'baz'}),
    (mock_always_fail_call, {'old_text': 'baz', 'new_text': 'qux', 'properties': '["foo"]'}, {'foo': b'qux', 'bar': b'baz'}),

    (mock_never_fail_call, {'old_text': 'baz'}, None),

    (MockAlwaysFailCall, {'old_text': 'baz'}, {'foo': b'', 'bar': b'', 'init_foo': b'init_', 'init_bar': b'init_'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'new_text': 'qux'}, {'foo': b'qux', 'bar': b'qux', 'init_foo': b'init_qux', 'init_bar': b'init_qux'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'properties': '["foo"]'}, {'foo': b'', 'bar': b'baz', 'init_foo': b'init_baz', 'init_bar': b'init_baz'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'new_text': 'qux', 'properties': '["foo"]'}, {'foo': b'qux', 'bar': b'baz', 'init_foo': b'init_baz', 'init_bar': b'init_baz'}),

    (MockNeverFailCall, {'old_text': 'baz'}, None),
])
def test_anonymize_decorator(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.AnonymizeDecorator(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
