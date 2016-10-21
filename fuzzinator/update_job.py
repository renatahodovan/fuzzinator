# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .config import config_get_callable


class UpdateJob(object):
    """
    Class for running SUT update jobs.
    """

    def __init__(self, config, sut_section):
        self.config = config
        self.sut_section = sut_section

    def run(self):
        update, update_kwargs = config_get_callable(self.config, self.sut_section, 'update')
        with update:
            update(**update_kwargs)
