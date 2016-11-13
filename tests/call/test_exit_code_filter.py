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
    ({'init_foo': b'init_bar'}, {'foo': b'bar', 'exit_code': 42})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {'exit_codes': '[]'}, None),
    (mock_always_fail_call, {'exit_codes': '[41,43]'}, None),
    (mock_always_fail_call, {'exit_codes': '[41,42,43]'}, {'foo': b'bar', 'exit_code': 42}),

    (mock_never_fail_call, {'exit_codes': '[41,42,43]'}, None),

    (MockAlwaysFailCall, {'exit_codes': '[]'}, None),
    (MockAlwaysFailCall, {'exit_codes': '[41,43]'}, None),
    (MockAlwaysFailCall, {'exit_codes': '[41,42,43]'}, {'init_foo': b'init_bar', 'foo': b'bar', 'exit_code': 42}),

    (MockNeverFailCall, {'exit_codes': '[41,42,43]'}, None),
])
def test_exit_code_filter(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.ExitCodeFilter(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
