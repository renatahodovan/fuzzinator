# Copyright (c) 2018-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator


@pytest.mark.parametrize('issue, formatter_class, formatter_init_kwargs, exp_short, exp_long', [
    ({'id': b'foo', 'foo': [b'bar'], 'xyz': {'foo': b'bar'}},
     fuzzinator.formatter.JsonFormatter,
     {},
     'foo',
     '{\n    "foo": [\n        "bar"\n    ],\n    "id": "foo",\n    "xyz": {\n        "foo": "bar"\n    }\n}'),
])
def test_decoder_decorator(issue, formatter_class, formatter_init_kwargs, exp_short, exp_long):
    formatter_class = fuzzinator.formatter.DecoderDecorator()(formatter_class)
    formatter = formatter_class(**formatter_init_kwargs)
    assert exp_long == formatter(issue=issue)
    assert exp_short == formatter.summary(issue=issue)
