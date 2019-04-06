# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging

from ...listener import EventListener

logger = logging.getLogger(__name__)


class CliListener(EventListener):

    def __init__(self):
        super().__init__(None)

    def new_fuzz_job(self, ident, cost, sut, fuzzer, batch):
        logger.debug('#%s: New fuzzer job for %s to %s (%s tests).', ident, fuzzer, sut, batch)

    def new_update_job(self, ident, cost, sut):
        logger.debug('#%s: New update job for %s.', ident, sut)

    def new_reduce_job(self, ident, cost, sut, issue_id, size):
        logger.debug('#%s: New reduce job for %r in %s (%s bytes).', ident, issue_id, sut, size)

    def new_validate_job(self, ident, cost, sut, issue_id):
        logger.debug('#%s: New validate job for %r in %s.', ident, issue_id, sut)

    def activate_job(self, ident):
        logger.debug('#%s: Activate job.', ident)

    def remove_job(self, ident):
        logger.debug('#%s: Remove job.', ident)

    def warning(self, ident, msg):
        if ident is not None:
            logger.warning('#%s: %s', ident, msg)
        else:
            logger.warning(msg)

    def new_issue(self, ident, issue):
        logger.info('#%s: New issue %r in %s.', ident, issue['id'], issue['sut'])

    def update_issue(self, ident, issue):
        logger.info('#%s: Updated issue %r in %s.', ident, issue['id'], issue['sut'])

    def invalid_issue(self, ident, issue):
        logger.debug('#%s: Invalid issue %r in %s.', ident, issue['id'], issue['sut'])
