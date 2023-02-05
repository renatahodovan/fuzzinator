==============================================
Issue Trackers: package ``fuzzinator.tracker``
==============================================

.. automodule:: fuzzinator.tracker
   :members:
   :imported-members:


.. _ui-extensions:

UI Extensions
=============

.. autoclass:: fuzzinator.ui.tui.ReportDialog
   :members:

.. _template-report:

.. describe:: template report.html

    Parent template of pages that allow preparing an issue report on the
    Tornado_-based web UI. To be extended using ``{% extends "report.html" %}``.

    .. _Tornado: https://www.tornadoweb.org/

    Child templates can extend ``report.html`` at two points:

    {% block report_head %}
        A replaceable block in the ``<head>`` element where child templates can
        put ``<script>`` elements and extra logic (empty by default).

    {% block settings %}
        A replaceable block in the report form of the issue report page where
        child templates can put extra UI/form elements (empty by default).

        When reporting the issue, the form data is automatically collected and
        posted via the web API to
        :meth:`fuzzinator.tracker.Tracker.report_issue`. (The ``name``
        attributes of the form elements become the names of the keyword
        arguments of :meth:`~fuzzinator.tracker.Tracker.report_issue`.) The
        report form already contains elements with ``name="title"`` and
        ``name="body"`` (outside the ``settings`` block).

    Some information is available to the templates as variables in their
    namespace:

    settings
        The tracker-specific information returned by
        :meth:`fuzzinator.tracker.Tracker.settings`.
