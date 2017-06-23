# Copyright (c) 2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import inspect
import pytest
import os
import re

import fuzzinator

from common_fuzzer import mock_exhausted_fuzzer, MockRepeatingFuzzer


@pytest.mark.parametrize('fuzzer, fuzzer_init_kwargs, dec_kwargs, exp', [
    (mock_exhausted_fuzzer, {}, {'filename': 'baz.txt'}, None),
    (mock_exhausted_fuzzer, {}, {'filename': 'baz{uid}.txt'}, None),

    (MockRepeatingFuzzer, {'test': b'init_bar', 'n': 1}, {'filename': 'baz.txt'}, b'init_bar'),
    (MockRepeatingFuzzer, {'test': b'init_bar', 'n': 1}, {'filename': 'baz{uid}.txt'}, b'init_bar'),
])
def test_file_writer_decorator(fuzzer, fuzzer_init_kwargs, dec_kwargs, exp, tmpdir):
    tmp_dec_kwargs = dict(dec_kwargs)
    tmp_dec_kwargs['filename'] = os.path.join('%s' % tmpdir, dec_kwargs['filename'])

    fuzzer = fuzzinator.fuzzer.FileWriterDecorator(**tmp_dec_kwargs)(fuzzer)
    if inspect.isclass(fuzzer):
        fuzzer = fuzzer(**fuzzer_init_kwargs)

    with fuzzer:
        out = fuzzer(index=0)
        if out is not None:
            assert os.path.exists(out)
            with open(out, 'rb') as f:
                assert f.read() == exp

    if exp is None:
        assert out is None
    else:
        assert re.search(pattern=dec_kwargs['filename'].format(uid='.*') + '$', string=out) is not None
        assert not os.path.exists(out)
