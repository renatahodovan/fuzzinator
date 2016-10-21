# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging

from fuzzinator import EventListener

logger = logging.getLogger(__name__)


class CliListener(EventListener):

    def new_fuzz_job(self, ident, fuzzer, sut, cost, batch):
        logger.debug('[{sut}] New fuzzer jobb added: {fuzzer} [{batch}]'.format(sut=sut, fuzzer=fuzzer, batch=batch))

    def new_update_job(self, ident, sut):
        logger.debug('[{sut}] New update job added.'.format(sut=sut))

    def new_reduce_job(self, ident, sut, cost, issue_id, size):
        logger.debug('[{sut}] New reduce job added: {issue} [{size} bytes].'.format(sut=sut, issue=issue_id, size=size))

    def remove_job(self, ident):
        logger.debug('[{ident}] Remove job.'.format(ident=ident))

    def warning(self, msg):
        logger.warn(msg)

    def new_issue(self, issue):
        logger.info('New issue: {msg}'.format(msg=issue['id']))

    def activate_job(self, ident):
        logger.debug('Activate job: {ident}'.format(ident=ident))
