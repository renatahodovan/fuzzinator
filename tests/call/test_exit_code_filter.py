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
    ({'init_foo': 'init_bar'}, {'test': 'bar', 'exit_code': 42})
])
@pytest.mark.parametrize('call_class, dec_kwargs, exp', [
    (MockAlwaysFailCall, {'exit_codes': '[]'}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'exit_codes': '[41,43]'}, fuzzinator.call.NonIssue),
    (MockAlwaysFailCall, {'exit_codes': '[41,42,43]'}, {'init_foo': 'init_bar', 'test': 'bar', 'exit_code': 42}),
    (MockAlwaysFailCall, {'exit_codes': '[]', 'invert': 'true'}, {'init_foo': 'init_bar', 'test': 'bar', 'exit_code': 42}),
    (MockAlwaysFailCall, {'exit_codes': '[41,43]', 'invert': 'true'}, {'init_foo': 'init_bar', 'test': 'bar', 'exit_code': 42}),
    (MockAlwaysFailCall, {'exit_codes': '[41,42,43]', 'invert': 'true'}, fuzzinator.call.NonIssue),

    (MockNeverFailCall, {'exit_codes': '[41,42,43]'}, None),
    (MockNeverFailCall, {'exit_codes': '[41,42,43]', 'invert': 'true'}, None),
])
def test_exit_code_filter(call_class, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call_class = fuzzinator.call.ExitCodeFilter(**dec_kwargs)(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        issue = call(**call_kwargs)

    if exp is None:
        assert issue is None
    elif exp == fuzzinator.call.NonIssue:
        assert not issue
    else:
        assert issue == exp
