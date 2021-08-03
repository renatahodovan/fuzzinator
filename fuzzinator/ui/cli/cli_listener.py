# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
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

    def on_fuzz_job_added(self, job_id, cost, sut, fuzzer, batch):
        logger.debug('#%s: New fuzzer job for %s to %s (%s tests).', job_id, fuzzer, sut, batch)

    def on_update_job_added(self, job_id, cost, sut):
        logger.debug('#%s: New update job for %s.', job_id, sut)

    def on_reduce_job_added(self, job_id, cost, sut, issue_oid, issue_id, size):
        logger.debug('#%s: New reduce job for %r in %s (%s bytes).', job_id, issue_id, sut, size)

    def on_validate_job_added(self, job_id, cost, sut, issue_oid, issue_id):
        logger.debug('#%s: New validate job for %r in %s.', job_id, issue_id, sut)

    def on_job_activated(self, job_id):
        logger.debug('#%s: Activate job.', job_id)

    def on_job_removed(self, job_id):
        logger.debug('#%s: Remove job.', job_id)

    def warning(self, job_id, msg):
        if job_id is not None:
            logger.warning('#%s: %s', job_id, msg)
        else:
            logger.warning(msg)

    def on_issue_added(self, job_id, issue):
        logger.info('#%s: New issue %r in %s.', job_id, issue['id'], issue['sut'])

    def on_issue_updated(self, job_id, issue):
        logger.info('#%s: Updated issue %r in %s.', job_id, issue['id'], issue['sut'])

    def on_issue_invalidated(self, job_id, issue):
        logger.debug('#%s: Invalid issue %r in %s.', job_id, issue['id'], issue['sut'])

    def on_issue_reduced(self, job_id, issue):
        logger.debug('#%s: Reduced issue %r in %s.', job_id, issue['id'], issue['sut'])
