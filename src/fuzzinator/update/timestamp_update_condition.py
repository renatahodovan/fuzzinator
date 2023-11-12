# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import datetime
import os
import time

from ..config import as_path
from .update_condition import UpdateCondition


class TimestampUpdateCondition(UpdateCondition):
    """
    File timestamp-based SUT update condition.

    **Mandatory parameters of the SUT update condition:**

      - ``path``: path to a file or directory to check for its last modification
        time.
      - ``age``: maximum allowed age of ``path`` given in
        [days:][hours:][minutes:]seconds format.

    **Result of the SUT update condition:**

      - Returns ``True`` if ``path`` does not exist or is older than ``age``.

    Example configuration snippet:

        .. code-block:: ini

            [sut.foo]
            update_condition=fuzzinator.update.TimestampUpdateCondition
            #update=... will be triggered if file timestamp is too old

            [sut.foo.update_condition]
            path=/home/alice/foo/bin/foo
            age=7:00:00:00
    """

    def __init__(self, *, path, age, **kwargs):
        self.path = path
        self.age = age

    def __call__(self):
        path = as_path(self.path)
        if not os.path.exists(path):
            return True

        parts = reversed(list(map(float, self.age.split(':'))))
        keys = ['seconds', 'minutes', 'hours', 'days']
        age = datetime.timedelta(**dict(zip(keys, parts))).total_seconds()
        return (time.time() - os.stat(path).st_mtime) > age
