# Copyright (c) 2018-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator

from .common_formatter import MockFixedFormatter, MockIdFormatter


@pytest.mark.parametrize('issue, formatter_class, formatter_init_kwargs, exp_short, exp_long', [
    ({'id': 'foo'},
     MockIdFormatter,
     {},
     'foo',
     '<p>foo</p>'),
    ({'id': 'foo'},
     MockFixedFormatter,
     {'short': 'bar', 'long': '# baz\n\n- qux: 42'},
     'bar',
     '<h1>baz</h1>\n<ul>\n<li>qux: 42</li>\n</ul>'),
])
def test_markdown_decorator(issue, formatter_class, formatter_init_kwargs, exp_short, exp_long):
    formatter_class = fuzzinator.formatter.MarkdownDecorator()(formatter_class)
    formatter = formatter_class(**formatter_init_kwargs)
    assert exp_long == formatter(issue=issue)
    assert exp_short == formatter.summary(issue=issue)
