# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import config_get_object


class UpdateJob(object):
    """
    Class for running SUT update jobs.
    """
    def __init__(self, id, config, sut_name, db, listener):
        self.id = id
        self.config = config
        self.sut_name = sut_name
        capacity = int(config.get('fuzzinator', 'cost_budget'))
        self.cost = min(int(config.get(f'sut.{sut_name}', 'update_cost', fallback=config.get('fuzzinator', 'cost_budget'))), capacity)

    def run(self):
        update = config_get_object(self.config, f'sut.{self.sut_name}', 'update')
        update()
        return []
