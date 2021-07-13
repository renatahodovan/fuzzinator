# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import os
import pytest
import sys

import fuzzinator

from common_call import blinesep, resources_dir, mock_always_fail_call, mock_never_fail_call, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_bar'}, {'foo': 'bar'})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {'property': 'baz', 'command': '%s %s --print-args qux' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py'))}, {'foo': 'bar', 'baz': 'qux' + blinesep}),
    (mock_always_fail_call, {'property': 'baz', 'command': '%s %s --print-args qux' % (sys.executable, os.path.join('.', 'mock_tool.py')), 'cwd': resources_dir}, {'foo': 'bar', 'baz': 'qux' + blinesep}),
    (mock_always_fail_call, {'property': 'baz', 'command': '%s %s --print-env QUX' % (sys.executable, os.path.join('.', 'mock_tool.py')), 'cwd': resources_dir, 'env': '{"QUX": "qux"}'}, {'foo': 'bar', 'baz': 'qux' + blinesep}),

    (mock_never_fail_call, {'property': 'baz', 'command': '%s %s --print-env QUX' % (sys.executable, os.path.join('.', 'mock_tool.py')), 'cwd': resources_dir, 'env': '{"QUX": "qux"}'}, None),

    (MockAlwaysFailCall, {'property': 'baz', 'command': '%s %s --print-args qux' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py'))}, {'init_foo': 'init_bar', 'foo': 'bar', 'baz': 'qux' + blinesep}),
    (MockAlwaysFailCall, {'property': 'baz', 'command': '%s %s --print-args qux' % (sys.executable, os.path.join('.', 'mock_tool.py')), 'cwd': resources_dir}, {'init_foo': 'init_bar', 'foo': 'bar', 'baz': 'qux' + blinesep}),
    (MockAlwaysFailCall, {'property': 'baz', 'command': '%s %s --print-env QUX' % (sys.executable, os.path.join('.', 'mock_tool.py')), 'cwd': resources_dir, 'env': '{"QUX": "qux"}'}, {'init_foo': 'init_bar', 'foo': 'bar', 'baz': 'qux' + blinesep}),

    (MockNeverFailCall, {'property': 'baz', 'command': '%s %s --print-env QUX' % (sys.executable, os.path.join('.', 'mock_tool.py')), 'cwd': resources_dir, 'env': '{"QUX": "qux"}'}, None),
])
def test_subprocess_property_decorator(call, call_init_kwargs, call_kwargs, dec_kwargs, exp):
    call = fuzzinator.call.SubprocessPropertyDecorator(**dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    assert call(**call_kwargs) == exp
