# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .arg import add_arguments
from .reporter_dialogs import BugzillaReportDialog, ReportDialog


def execute(arguments):
    from .tui import execute as _execute
    _execute(arguments)
