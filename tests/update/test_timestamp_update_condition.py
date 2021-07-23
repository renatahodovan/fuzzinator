# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest

import fuzzinator


@pytest.mark.parametrize('touch, age, exp', [
    (None, '0:0:1', True),
    (-60*60*24*31, '0:0:10', True),
    (-60*60*24*31, '0:10:0', True),
    (-60*60*24*31, '10:0:0', True),
    (-60*60*24*31, '1:0:0:0', True),
    (0, '0:0:10', False),
    (0, '0:10:0', False),
    (0, '10:0:0', False),
    (0, '1:0:0:0', False),
])
def test_timestamp_update_condition(touch, age, exp, tmpdir):
    path = os.path.join(str(tmpdir), 'foo.txt')

    if touch is not None:
        with open(path, 'w') as f:
            print('bar', file=f)
        statinfo = os.stat(path)
        os.utime(path, times=(statinfo.st_mtime + touch, statinfo.st_mtime + touch))

    assert fuzzinator.update.TimestampUpdateCondition(path, age) == exp

    if touch is not None:
        os.remove(path)
