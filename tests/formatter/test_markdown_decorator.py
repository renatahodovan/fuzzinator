# Copyright (c) 2018-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator

from common_formatter import MockFixedFormatter, MockIdFormatter


@pytest.mark.parametrize('formatter_kwargs, exp_key', [
    ({'format': 'short'}, 'short'),
    ({'format': 'long'}, 'long'),
    ({}, 'long'),
])
@pytest.mark.parametrize('issue, formatter_class, formatter_init_kwargs, exp_dict', [
    ({'id': 'foo'},
     MockIdFormatter,
     {},
     {'short': 'foo', 'long': '<p>foo</p>'}),
    ({'id': 'foo'},
     MockFixedFormatter,
     {'short': 'bar', 'long': '# baz\n\n- qux: 42'},
     {'short': 'bar', 'long': '<h1>baz</h1>\n<ul>\n<li>qux: 42</li>\n</ul>'}),
])
def test_markdown_decorator(issue, formatter_class, formatter_init_kwargs, formatter_kwargs, exp_dict, exp_key):
    formatter_class = fuzzinator.formatter.MarkdownDecorator()(formatter_class)
    formatter = formatter_class(**formatter_init_kwargs)
    assert exp_dict[exp_key] == formatter(issue=issue, **formatter_kwargs)
