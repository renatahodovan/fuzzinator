# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest

import fuzzinator

from common_formatter import mock_issue, mock_templates_dir


@pytest.mark.parametrize('formatter_kwargs, exp_key', [
    ({'format': 'short'}, 'short'),
    ({'format': 'long'}, 'long'),
    ({}, 'long'),
])
@pytest.mark.parametrize('issue, formatter_init_kwargs, exp_dict', [
    (mock_issue,
     {'short': '{{id}}', 'long': 'id: {{id}}, bar: {{bar}}, baz: {{baz}}, qux.xyz: {{qux.xyz}}'},
     {'short': 'foo', 'long': 'id: foo, bar: True, baz: False, qux.xyz: 42'}),
    (mock_issue,
     {'short_file': os.path.join(mock_templates_dir, 'doublecurly_short.txt'), 'long_file': os.path.join(mock_templates_dir, 'doublecurly_long.md')},
     {'short': 'issue: foo\n', 'long': '# Issue: foo\n\n- bar: True\n- baz: False\n- qux.xyz: 42\n'}),
    (mock_issue,
     {},
     {'short': '', 'long': ''}),
])
def test_chevron_formatter(issue, formatter_init_kwargs, formatter_kwargs, exp_dict, exp_key):
    assert exp_dict[exp_key] == fuzzinator.formatter.ChevronFormatter(**formatter_init_kwargs)(issue=issue, **formatter_kwargs)
