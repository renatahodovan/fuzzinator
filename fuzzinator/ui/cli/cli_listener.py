# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging

from ...listener import EventListener

logger = logging.getLogger(__name__)


class CliListener(EventListener):

    # Override the ancestor's constructor to avoid the need for passing an unused config parameter.
    def __init__(self):
        pass

    def new_fuzz_job(self, ident, fuzzer, sut, cost, batch):
        logger.debug('New fuzzer job #{ident} for {fuzzer} to {sut} ({batch} tests).'.format(ident=ident, sut=sut, fuzzer=fuzzer, batch=batch))

    def new_update_job(self, ident, sut):
        logger.debug('New update job #{ident} for {sut}.'.format(ident=ident, sut=sut))

    def new_reduce_job(self, ident, sut, cost, issue_id, size):
        logger.debug('New reduce job #{ident} for {issue!r} in {sut} ({size} bytes).'.format(ident=ident, sut=sut, issue=issue_id, size=size))

    def new_validate_job(self, ident, sut, issue_id):
        logger.debug('New validate job #{ident} for {issue!r} in {sut}.'.format(ident=ident, sut=sut, issue=issue_id))

    def activate_job(self, ident):
        logger.debug('Activate job #{ident}.'.format(ident=ident))

    def remove_job(self, ident):
        logger.debug('Remove job #{ident}.'.format(ident=ident))

    def warning(self, msg):
        logger.warning(msg)

    def new_issue(self, issue):
        logger.info('New issue {issue!r} in {sut}.'.format(issue=issue['id'], sut=issue['sut']))

    def update_issue(self, issue):
        logger.info('Updated issue {issue!r} in {sut}.'.format(issue=issue['id'], sut=issue['sut']))

    def invalid_issue(self, issue):
        logger.debug('Invalid issue {issue!r} in {sut}.'.format(issue=issue['id'], sut=issue['sut']))
