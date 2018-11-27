# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import config_get_callable


class UpdateJob(object):
    """
    Class for running SUT update jobs.
    """
    def __init__(self, id, config, sut_name, db, listener):
        self.id = id
        self.config = config
        self.sut_name = sut_name
        self.cost = int(self.config.get('sut.' + self.sut_name, 'update_cost', fallback=self.config.get('fuzzinator', 'cost_budget')))

    def run(self):
        update, update_kwargs = config_get_callable(self.config, 'sut.' + self.sut_name, 'update')
        with update:
            update(**update_kwargs)
        return []
