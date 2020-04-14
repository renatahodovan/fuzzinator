# Copyright (c) 2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest

import fuzzinator


@pytest.mark.parametrize('issue, exp_test', [
    ({'test': 'foo bar'}, 'foo bar'),
    ({'test': 'foo bar', 'reduced': 'oo'}, 'oo'),
    ({'test': b'baz qux'}, b'baz qux'),
    ({'test': b'baz qux', 'reduced': b'qu'}, b'qu'),
])
@pytest.mark.parametrize('exporter_init_kwargs, exp_ext, exp_type', [
    ({}, None, None),
    ({'extension': '.foo', 'type': 'application/example'}, '.foo', 'application/example'),
])
def test_test_exporter(issue, exporter_init_kwargs, exp_test, exp_ext, exp_type):
    exporter = fuzzinator.exporter.TestExporter(**exporter_init_kwargs)
    assert exp_test == exporter(issue=issue)
    assert exp_ext == exporter.extension
    assert exp_type == exporter.type
