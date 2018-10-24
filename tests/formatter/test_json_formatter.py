# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator


@pytest.mark.parametrize('formatter_kwargs, exp_key', [
    ({'format': 'short'}, 'short'),
    ({'format': 'long'}, 'long'),
    ({}, 'long'),
])
@pytest.mark.parametrize('issue, exp_dict', [
    ({'id': 'foo', 'bar': 'baz'},
     {'short': '"foo"', 'long': '{\n    "bar": "baz",\n    "id": "foo"\n}'}),
])
def test_json_formatter(issue, formatter_kwargs, exp_dict, exp_key):
    assert exp_dict[exp_key] == fuzzinator.formatter.JsonFormatter(issue=issue, **formatter_kwargs)
