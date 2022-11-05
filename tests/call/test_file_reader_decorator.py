# Copyright (c) 2017-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest
import shutil

import fuzzinator

from common_call import blinesep, resources_dir, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('dec_kwargs', [
    {},
    {'cleanup': False},
    {'cleanup': True},
])
@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_bar'}, {'test': os.path.join(resources_dir, 'mock_tests', 'bar.txt')}),
])
@pytest.mark.parametrize('call_class, exp', [
    (MockAlwaysFailCall, {'init_foo': 'init_bar', 'test': b'bar' + blinesep, 'filename': 'bar.txt'}),
    (MockNeverFailCall, None),
])
def test_file_reader_decorator(call_class, call_init_kwargs, call_kwargs, dec_kwargs, exp, tmpdir):
    call_class = fuzzinator.call.FileReaderDecorator(**dec_kwargs)(call_class)
    call = call_class(**call_init_kwargs)
    test_path = shutil.copy(call_kwargs['test'], str(tmpdir))
    with call:
        assert call(**dict(call_kwargs, test=test_path)) == exp
        assert dec_kwargs.get('cleanup', False) == (not os.path.exists(test_path))
