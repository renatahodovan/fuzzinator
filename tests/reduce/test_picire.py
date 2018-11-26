# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator

from common_reduce import MockFailIfContainsCall


@pytest.mark.parametrize('call, call_init_kwargs, issue, exp_test, exp_issues', [
    (MockFailIfContainsCall, {'strings': [b'bar\n']}, {'id': b'bar\n', 'test': b'foo\nbar\nbaz\n'}, b'bar\n', []),
    (MockFailIfContainsCall, {'strings': [b'bar\n', b'ar\n']}, {'id': b'bar\n', 'test': b'foo\nbar\nbaz\n'}, b'bar\n', [{'id': b'ar\n', 'test': b'ar\n'}]),
])
def test_picire(call, call_init_kwargs, issue, exp_test, exp_issues, tmpdir):
    reduced_test, new_issues = fuzzinator.reduce.Picire(sut_call=call(**call_init_kwargs),
                                                        sut_call_kwargs={},
                                                        listener=fuzzinator.listener.EventListener(None),
                                                        ident=None,
                                                        issue=issue,
                                                        work_dir=str(tmpdir))
    assert reduced_test == exp_test
    assert new_issues == exp_issues
