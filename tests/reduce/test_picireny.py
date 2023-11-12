# Copyright (c) 2018-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import os

from functools import partial

import pytest

import fuzzinator

from .common_reduce import MockFailIfContainsCall, mock_grammars_dir


@pytest.mark.parametrize('format, grammar, start, replacements', [
    (None, json.dumps([os.path.join(mock_grammars_dir, 'MockGrammar.g4')]), 'text', os.path.join(mock_grammars_dir, 'mock_replacements.json')),
    (os.path.join(mock_grammars_dir, 'mock_format.json'), None, None, None),
])
@pytest.mark.parametrize('call, call_init_kwargs, issue, exp_test, exp_issues', [
    (MockFailIfContainsCall, {'strings': [b'bar\n']}, {'id': b'bar\n', 'test': b'foo\nbar\nbaz\n'}, b'bar\n', []),
    (MockFailIfContainsCall, {'strings': [b'bar\n', b'ar\n']}, {'id': b'bar\n', 'test': b'foo\nbar\nbaz\n'}, b'bar\n', [{'id': b'ar\n', 'test': b'ar\n'}]),
])
def test_picireny(call, call_init_kwargs, issue, format, grammar, start, replacements, exp_test, exp_issues, tmpdir):
    reducer = fuzzinator.reduce.Picireny(format=format,
                                         grammar=grammar,
                                         start=start,
                                         replacements=replacements,
                                         work_dir=str(tmpdir))
    reduced_test, new_issues = reducer(sut_call=call(**call_init_kwargs),
                                       issue=issue,
                                       on_job_progressed=partial(fuzzinator.listener.EventListener(None).on_job_progressed, job_id=None))
    assert reduced_test == exp_test
    assert new_issues == exp_issues
