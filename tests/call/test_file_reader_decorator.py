# Copyright (c) 2017-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest

import fuzzinator

from common_call import blinesep, resources_dir, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_bar'}, {'test': os.path.join(resources_dir, 'mock_tests', 'bar.txt')})
])
@pytest.mark.parametrize('call_class, exp', [
    (MockAlwaysFailCall, {'init_foo': 'init_bar', 'test': b'bar' + blinesep, 'filename': 'bar.txt'}),
    (MockNeverFailCall, None),
])
def test_file_reader_decorator(call_class, call_init_kwargs, call_kwargs, exp):
    call_class = fuzzinator.call.FileReaderDecorator()(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        assert call(**call_kwargs) == exp
