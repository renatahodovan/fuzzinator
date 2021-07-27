# Copyright (c) 2018-2021 Renata Hodovan, Akos Kiss.
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
@pytest.mark.parametrize('issue, formatter_class, exp_dict', [
    ({'id': b'foo', 'foo': [b'bar'], 'xyz': {'foo': b'bar'}},
     fuzzinator.formatter.JsonFormatter,
     {'short': '"foo"', 'long': '{\n    "foo": [\n        "bar"\n    ],\n    "id": "foo",\n    "xyz": {\n        "foo": "bar"\n    }\n}'}),
])
def test_decoder_decorator(issue, formatter_class, formatter_kwargs, exp_dict, exp_key):
    formatter_class = fuzzinator.formatter.DecoderDecorator()(formatter_class)
    formatter = formatter_class()
    assert exp_dict[exp_key] == formatter(issue=issue, **formatter_kwargs)
