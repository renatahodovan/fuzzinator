# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from urwid import *
from os import get_terminal_size

from fuzzinator.tracker import BugzillaReport, GithubReport
from fuzzinator.tracker.base import init_tracker
from .reporter_dialogs import BugzillaReportDialog, GithubReportDialog
from .button import FormattedButton
from .dialogs import EditIssueDialog, FormattedIssueDialog


class FullScreenPopupLauncher(PopUpLauncher):

    def get_pop_up_parameters(self):
        cols, rows = get_terminal_size()
        return {'left': cols // 2, 'top': rows // 2, 'overlay_width': cols, 'overlay_height': rows}


class ViewButton(FullScreenPopupLauncher):
    signals = ['click']

    def __init__(self, label, issues_table, config, trackers):
        super(ViewButton, self).__init__(FormattedButton(label))
        self.issues_table = issues_table
        self.config = config
        self.trackers = trackers
        self.pop_up_params = {'left': -40, 'top': -100, 'overlay_width': 200, 'overlay_height': 60}
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        sut = focus.data['sut']
        sut_section = 'sut.' + sut
        if sut not in self.trackers:
            self.trackers[sut] = init_tracker(self.config, sut_section, self.issues_table.db)
        pop_up = FormattedIssueDialog(issue=self.issues_table.db.find_issue_by_id(focus.data['_id']),
                                      tracker=self.trackers[sut])

        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up


class EditButton(FullScreenPopupLauncher):
    signals = ['click']

    def __init__(self, label, issues_table):
        super(EditButton, self).__init__(FormattedButton(label))
        self.issues_table = issues_table
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        pop_up = EditIssueDialog(issue=self.issues_table.db.find_issue_by_id(focus.data['_id']),
                                 db=self.issues_table.db)
        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up


class ReportButton(FullScreenPopupLauncher):
    signals = ['click']

    def __init__(self, label, issues_table, config, trackers):
        super(ReportButton, self).__init__(FormattedButton(label))
        self.issues_table = issues_table
        self.config = config
        self.trackers = trackers

        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        sut = focus.data['sut']
        sut_section = 'sut.' + sut
        if sut not in self.trackers:
            self.trackers[sut] = init_tracker(self.config, sut_section, self.issues_table.db)

        self.get_pop_up_parameters = super(ReportButton, self).get_pop_up_parameters
        issue_details = self.issues_table.db.find_issue_by_id(focus.data['_id'])
        if isinstance(self.trackers[sut], BugzillaReport):
            popup_cls = BugzillaReportDialog
        elif isinstance(self.trackers[sut], GithubReport):
            popup_cls = GithubReportDialog
        else:
            # If there is no reporter interface for the given tracker
            # then we only display the formatted issue.
            popup_cls = FormattedIssueDialog

        pop_up = popup_cls(issue=issue_details, tracker=self.trackers[sut])
        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up
