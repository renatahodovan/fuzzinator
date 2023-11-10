# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import sys

import pytest

import fuzzinator

from .common_call import linesep, resources_dir, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_bar'}, {'test': 'bar'})
])
@pytest.mark.parametrize('call_class, dec_kwargs, exp', [
    (MockAlwaysFailCall, {'property': 'baz', 'command': f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args qux'}, {'init_foo': 'init_bar', 'test': 'bar', 'baz': f'qux{linesep}'}),
    (MockAlwaysFailCall, {'property': 'baz', 'command': f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args qux', 'cwd': resources_dir}, {'init_foo': 'init_bar', 'test': 'bar', 'baz': f'qux{linesep}'}),
    (MockAlwaysFailCall, {'property': 'baz', 'command': f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-env QUX', 'cwd': resources_dir, 'env': '{"QUX": "qux"}'}, {'init_foo': 'init_bar', 'test': 'bar', 'baz': f'qux{linesep}'}),

    (MockNeverFailCall, {'property': 'baz', 'command': f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-env QUX', 'cwd': resources_dir, 'env': '{"QUX": "qux"}'}, None),
])
def test_subprocess_property_decorator(call_class, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call_class = fuzzinator.call.SubprocessPropertyDecorator(**dec_kwargs)(call_class)
    call = call_class(**call_init_kwargs)

    with call:
        assert call(**call_kwargs) == exp
