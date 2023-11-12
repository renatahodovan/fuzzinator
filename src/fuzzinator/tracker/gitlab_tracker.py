# Copyright (c) 2019-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from gitlab import exceptions, Gitlab

from .tracker import Tracker, TrackerError


class GitlabTracker(Tracker):
    """
    GitLab_ issue tracker.

    .. _GitLab: https://about.gitlab.com/

    **Mandatory parameters of the issue tracker:**

      - ``url``: URL of the GitLab installation.
      - ``project``: repository name in user/repo format.

    **Optional parameter of the issue tracker:**

      - ``private_token``: a personal access token for authenticating.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            tracker=fuzzinator.tracker.GitlabTracker

            [sut.foo.tracker]
            url=https://gitlab.example.org
            project=alice/foo
            private_token=12345678901234567890
    """

    def __init__(self, *, url, project, private_token=None):
        gl = Gitlab(url, private_token=private_token)
        gl.auth()
        self.project = gl.projects.get(gl.search('projects', project)[0]['id'])

    def find_duplicates(self, *, title):
        try:
            issues = [issue for issue in self.project.search('issues', title) if issue['state'] == 'opened']
            return [(issue['web_url'], issue['title']) for issue in issues]
        except (exceptions.GitlabAuthenticationError, exceptions.GitlabSearchError) as e:
            raise TrackerError('Finding possible duplicates failed') from e

    def report_issue(self, *, title, body):
        try:
            new_issue = self.project.issues.create({'title': title, 'description': body})
            return new_issue.attributes['web_url']
        except (exceptions.GitlabAuthenticationError, exceptions.GitlabCreateError) as e:
            raise TrackerError('Issue reporting failed') from e
