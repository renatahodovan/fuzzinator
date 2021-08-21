# Copyright (c) 2018-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator


@pytest.mark.parametrize('issue, exp_short, exp_long', [
    ({'id': 'foo', 'bar': 'baz'},
     'foo',
     '{\n    "bar": "baz",\n    "id": "foo"\n}'),
])
def test_json_formatter(issue, exp_short, exp_long):
    formatter = fuzzinator.formatter.JsonFormatter()
    assert exp_long == formatter(issue=issue)
    assert exp_short == formatter.summary(issue=issue)
