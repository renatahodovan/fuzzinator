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

    # Override the ancestor's constructor to avoid the need for passing an unused config parameter.
    def __init__(self):
        pass

    def new_fuzz_job(self, ident, cost, sut, fuzzer, batch):
        logger.debug('#{ident}: New fuzzer job for {fuzzer} to {sut} ({batch} tests).'.format(ident=ident, sut=sut, fuzzer=fuzzer, batch=batch))

    def new_update_job(self, ident, cost, sut):
        logger.debug('#{ident}: New update job for {sut}.'.format(ident=ident, sut=sut))

    def new_reduce_job(self, ident, cost, sut, issue_id, size):
        logger.debug('#{ident}: New reduce job for {issue!r} in {sut} ({size} bytes).'.format(ident=ident, sut=sut, issue=issue_id, size=size))

    def new_validate_job(self, ident, cost, sut, issue_id):
        logger.debug('#{ident}: New validate job for {issue!r} in {sut}.'.format(ident=ident, sut=sut, issue=issue_id))

    def activate_job(self, ident):
        logger.debug('#{ident}: Activate job.'.format(ident=ident))

    def remove_job(self, ident):
        logger.debug('#{ident}: Remove job.'.format(ident=ident))

    def warning(self, ident, msg):
        if ident is not None:
            logger.warning('#{ident}: {msg}'.format(ident=ident, msg=msg))
        else:
            logger.warning(msg)

    def new_issue(self, ident, issue):
        logger.info('#{ident}: New issue {issue!r} in {sut}.'.format(ident=ident, issue=issue['id'], sut=issue['sut']))

    def update_issue(self, ident, issue):
        logger.info('#{ident}: Updated issue {issue!r} in {sut}.'.format(ident=ident, issue=issue['id'], sut=issue['sut']))

    def invalid_issue(self, ident, issue):
        logger.debug('#{ident}: Invalid issue {issue!r} in {sut}.'.format(ident=ident, issue=issue['id'], sut=issue['sut']))
