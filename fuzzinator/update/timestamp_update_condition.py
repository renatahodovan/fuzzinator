# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import datetime
import os
import time


def TimestampUpdateCondition(path, age):
    """
    File timestamp-based SUT update condition.

    Mandatory parameters of the SUT update condition:
      - 'path': path to a file or directory to check for its last modification
        time.
      - 'age': maximum allowed age of 'path' given in HH:MM:SS format.

    Result of the SUT update condition:
      - Returns True if 'path' does not exist or is older than 'age'.

    Example configuration snippet:
    [sut.foo]
    should_update=fuzzinator.update.TimestampUpdateCondition
    #update=... will be triggered if file timestamp is too old

    [sut.foo.update_condition]
    path=/home/alice/foo/bin/foo
    age=24:00:00
    """

    if not os.path.exists(path):
        return True
    x = time.strptime(age, '%H:%M:%S')
    age = datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()
    return (time.time() - os.stat(path).st_mtime) > age
