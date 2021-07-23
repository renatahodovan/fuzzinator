# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import os
import pytest
import re

import fuzzinator

from common_call import mock_always_fail_call, mock_never_fail_call, MockAlwaysFailCall, MockNeverFailCall


@pytest.mark.parametrize('call_init_kwargs, call_kwargs', [
    ({'init_foo': 'init_bar'}, {'foo': 'bar', 'test': b'baz'})
])
@pytest.mark.parametrize('call, dec_kwargs, exp', [
    (mock_always_fail_call, {'filename': 'baz.txt'}, {'foo': 'bar'}),
    (mock_always_fail_call, {'filename': 'baz{uid}.txt'}, {'foo': 'bar'}),

    (mock_never_fail_call, {'filename': 'baz{uid}.txt'}, None),

    (MockAlwaysFailCall, {'filename': 'baz.txt'}, {'init_foo': 'init_bar', 'foo': 'bar'}),
    (MockAlwaysFailCall, {'filename': 'baz{uid}.txt'}, {'init_foo': 'init_bar', 'foo': 'bar'}),

    (MockNeverFailCall, {'filename': 'baz{uid}.txt'}, None),
])
def test_file_writer_decorator(call, call_init_kwargs, call_kwargs, dec_kwargs, exp, tmpdir):
    tmp_dec_kwargs = dict(dec_kwargs)
    tmp_dec_kwargs['filename'] = os.path.join(str(tmpdir), dec_kwargs['filename'])

    call = fuzzinator.call.FileWriterDecorator(**tmp_dec_kwargs)(call)
    if inspect.isclass(call):
        call = call(**call_init_kwargs)

    out = call(**call_kwargs)

    if out is not None:
        assert re.fullmatch(pattern=dec_kwargs['filename'].format(uid='.*'), string=out['filename']) is not None
        assert out['test'] == os.path.join(str(tmpdir), out['filename'])
        assert not os.path.exists(out['test'])

        del out['filename']
        del out['test']

    assert out == exp
