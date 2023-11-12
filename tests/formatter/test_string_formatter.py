# Copyright (c) 2018-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

import pytest

import fuzzinator

from .common_formatter import mock_issue, mock_templates_dir


@pytest.mark.parametrize('issue, formatter_init_kwargs, exp_short, exp_long', [
    (mock_issue,
     {'short': '{id}', 'long': 'id: {id}, bar: {bar}, baz: {baz}, qux: {qux}'},
     'foo',
     'id: foo, bar: True, baz: False, qux: {\'xyz\': 42}'),
    (mock_issue,
     {'short_file': os.path.join(mock_templates_dir, 'singlecurly_short.txt'), 'long_file': os.path.join(mock_templates_dir, 'singlecurly_long.md')},
     'issue: foo\n',
     '# Issue: foo\n\n- bar: True\n- baz: False\n- qux: {\'xyz\': 42}\n'),
    (mock_issue,
     {},
     '',
     ''),
])
def test_string_formatter(issue, formatter_init_kwargs, exp_short, exp_long):
    formatter = fuzzinator.formatter.StringFormatter(**formatter_init_kwargs)
    assert exp_long == formatter(issue=issue)
    assert exp_short == formatter.summary(issue=issue)
