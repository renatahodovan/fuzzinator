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

    def on_fuzz_job_added(self, ident, cost, sut, fuzzer, batch):
        logger.debug('#%s: New fuzzer job for %s to %s (%s tests).', ident, fuzzer, sut, batch)

    def on_update_job_added(self, ident, cost, sut):
        logger.debug('#%s: New update job for %s.', ident, sut)

    def on_reduce_job_added(self, ident, cost, sut, issue_id, size):
        logger.debug('#%s: New reduce job for %r in %s (%s bytes).', ident, issue_id, sut, size)

    def on_validate_job_added(self, ident, cost, sut, issue_id):
        logger.debug('#%s: New validate job for %r in %s.', ident, issue_id, sut)

    def on_job_activated(self, ident):
        logger.debug('#%s: Activate job.', ident)

    def on_job_removed(self, ident):
        logger.debug('#%s: Remove job.', ident)

    def warning(self, ident, msg):
        if ident is not None:
            logger.warning('#%s: %s', ident, msg)
        else:
            logger.warning(msg)

    def on_issue_added(self, ident, issue):
        logger.info('#%s: New issue %r in %s.', ident, issue['id'], issue['sut'])

    def on_issue_updated(self, ident, issue):
        logger.info('#%s: Updated issue %r in %s.', ident, issue['id'], issue['sut'])

    def on_issue_invalidated(self, ident, issue):
        logger.debug('#%s: Invalid issue %r in %s.', ident, issue['id'], issue['sut'])

    def on_issue_reduced(self, ident, issue):
        logger.debug('#%s: Reduced issue %r in %s.', ident, issue['id'], issue['sut'])
