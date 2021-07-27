# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator

from common_call import MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_baz', 'init_bar': 'init_baz'}, {'test': 'baz', 'id': 'baz'})
])
@pytest.mark.parametrize('call_class, dec_kwargs, exp', [
    (MockAlwaysFailCall, {'old_text': 'baz'}, {'init_foo': 'init_', 'init_bar': 'init_', 'test': '', 'id': ''}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'new_text': 'qux'}, {'init_foo': 'init_qux', 'init_bar': 'init_qux', 'test': 'qux', 'id': 'qux'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'properties': '["test"]'}, {'init_foo': 'init_baz', 'init_bar': 'init_baz', 'test': '', 'id': 'baz'}),
    (MockAlwaysFailCall, {'old_text': 'baz', 'new_text': 'qux', 'properties': '["test"]'}, {'init_foo': 'init_baz', 'init_bar': 'init_baz', 'test': 'qux', 'id': 'baz'}),

    (MockNeverFailCall, {'old_text': 'baz'}, None),
])
def test_anonymize_decorator(call_class, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call_class = fuzzinator.call.AnonymizeDecorator(**dec_kwargs)(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        assert call(**call_kwargs) == exp
