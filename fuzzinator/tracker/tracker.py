# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class Multiton(type):

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._instances = {}

    def __call__(cls, *args, **kwargs):
        key = tuple(args) + tuple(sorted(kwargs.items()))
        instance = cls._instances.get(key, None)
        if instance is None:
            instance = super().__call__(*args, **kwargs)
            cls._instances[key] = instance
        return instance


class Tracker(metaclass=Multiton):
    """
    An abstract base class for issue trackers where issues can be reported to.
    """

    ui_extension = {}
    """
    A dictionary to reference UI extensions for the tracker (if it needs any).

    If it contains the key ``'tui'``, then the associated value must be the
    fully qualified name of a sub-class of
    :class:`fuzzinator.ui.tui.ReportDialog`. That specialized dialog will be
    used by the text-based UI to prepare the report of an issue with this
    tracker.

    If it contains the key ``'wui'``, then the associated value must either be
    an absolute file path (formatted as ``/path/to/file``) or a reference to a
    resource in a package (formatted as ``//package.module/path/to/file``),
    naming a child template of :ref:`template-report.html`. That specialized
    template page will be used by the web UI to prepare the report of an issue
    with this tracker.

    See :ref:`ui-extensions`.
    """

    def find_duplicates(self, *, title):
        """
        Query for potential duplicates of an issue in the tracker based on the
        similarity of titles.

        Return an empty list by default.

        :param str title: A string to query the tracker for. The short string
            representation of the issue as returned by its
            :class:`~fuzzinator.formatter.Formatter`.
        :return: A list of tuples, where each tuple contains the URL and a short
            description (title) of the potential duplicate in the tracker.
        :rtype: list[tuple[str, str]]
        :raises TrackerError: If the query cannot be performed.
        """
        return []

    def report_issue(self, *, title, body):
        """
        Report an issue to the tracker.

        Raises :exc:`NotImplementedError` by default.

        :param str title: The short description to use when reporting the issue
            to the tracker. Potentially the short string representation of the
            issue as returned by its :class:`~fuzzinator.formatter.Formatter`,
            but may have been edited by the user.
        :param str body: The full issue report to send to the tracker.
            Potentially the long string representation of the issue as returned
            by its :class:`~fuzzinator.formatter.Formatter`, but may have been
            edited by the user.
        :return: The URL of the reported issue.
        :rtype: str
        :raises TrackerError: If the issue cannot be reported.

        Sub-classes may extend the signature of this method in overridden
        versions. In that case, they should also define UI extensions that
        collect input from the user that will be passed to the extra arguments
        (see: :attr:`ui_extension`, and
        :meth:`fuzzinator.ui.tui.ReportDialog.data` or
        :ref:`template-report.html`).
        """
        raise NotImplementedError()

    def settings(self):
        """
        Return tracker-specific information. This method is to be used by
        trackers that need UI extensions to collect extra input from the user
        when reporting an issue and need some tracker-specific information to
        build the UI extension (see :attr:`ui_extension`, and
        :meth:`fuzzinator.ui.tui.ReportDialog.init`
        or :ref:`template-report.html`).

        Return ``None`` by default.

        :return: Tracker-specific information.
        :rtype: Any
        """
        return None


class TrackerError(Exception):
    """
    Raised when a :class:`Tracker` operation cannot be performed.
    """
    pass
