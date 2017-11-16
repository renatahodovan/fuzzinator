# Copyright (c) 2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import pytest
import os

import fuzzinator

from common_call import resources_dir, mock_always_fail_call, mock_never_fail_call, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': b'init_bar'}, {'test': os.path.join(resources_dir, 'mock_tests', 'bar.txt')})
])
@pytest.mark.parametrize('call, exp', [
    (mock_always_fail_call, {'test': b'bar\n', 'filename': 'bar.txt'}),
    (mock_never_fail_call, None),

    (MockAlwaysFailCall, {'init_foo': b'init_bar', 'test': b'bar\n', 'filename': 'bar.txt'}),
    (MockNeverFailCall, None),
])
def test_file_reader_decorator(call, call_init_kwargs, call_kwargs, exp, tmpdir):
    call = fuzzinator.call.FileReaderDecorator()(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
