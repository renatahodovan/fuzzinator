# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

try:
    # FIXME: very nasty, but a recent PyGithub version began to depend on
    # pycrypto transitively, which is a PITA on Windows (can easily fail with an
    # ``ImportError: No module named 'winrandom'``) -- so, we just don't care
    # for now if we cannot load the github module at all. This workaround just
    # postpones the error to the point when ``GithubTracker`` is actually used,
    # so be warned, don't do that on Windows!
    from github import Github, GithubException
except ImportError:
    pass

from .tracker import Tracker, TrackerError


class GithubTracker(Tracker):
    """
    GitHub_ issue tracker.

    .. _GitHub: https://github.com/

    **Mandatory parameter of the issue tracker:**

      - ``repository``: repository name in user/repo format.

    **Optional parameter of the issue tracker:**

      - ``token``: a personal access token for authenticating.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            tracker=fuzzinator.tracker.GithubTracker

            [sut.foo.tracker]
            repository=alice/foo
            token=1234567890123456789012345678901234567890
    """

    def __init__(self, *, repository, token=None):
        self.repository = repository
        self.ghapi = Github(login_or_token=token)
        self.project = self.ghapi.get_repo(repository)

    def find_duplicates(self, *, title):
        try:
            issues = list(self.ghapi.search_issues('repo:{repository} is:issue is:open {title}'.format(repository=self.repository, title=title)))
            return [(issue.html_url, issue.title) for issue in issues]
        except GithubException as e:
            raise TrackerError('Finding possible duplicates failed') from e

    def report_issue(self, *, title, body):
        try:
            new_issue = self.project.create_issue(title=title, body=body)
            return new_issue.html_url
        except GithubException as e:
            raise TrackerError('Issue reporting failed') from e
