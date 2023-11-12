# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .arg import add_arguments


def execute(arguments):
    from .wui import execute as _execute
    _execute(arguments)
