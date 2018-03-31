==========================
*Fuzzinator* Release Notes
==========================

.. start included documentation

18.3.1
======

Summary of changes:

* Fixed the way package metadata is accessed to ensure wheel compatibility.


18.3
====

Summary of changes:

* New features in the framework:

  * Support for issue (re-)validation with a new job type (validate).
  * Support for user-defined event listeners.

* Numerous new building blocks in the framework:

  * ``fuzzinator.EmailListener``: support for sending emails about events, e.g.,
    new issues.
  * ``fuzzinator.tracker.MonorailReport``: support for the Monorail issue
    tracking system.
  * ``fuzzinator.call.LldbBacktraceDecorator``: support for backtrace info via
    LLDB.
  * ``fuzzinator.fuzzer.ByteFlipDecorator``: support for adding extra random
    byte flips to fuzzer results.
  * ``fuzzinator.fuzzer.FileWriterDecorator``: support for writing fuzzer
    results to files.
  * ``fuzzinator.call.FileReaderDecorator``: support for extracting fuzzer
    results from files.

* Building blocks with extended or changed functionality:

  * ``fuzzinator.call.SubprocessCall`` and ``.StdinSubprocessCall`` can accept 0
    exit code as an issue.
  * ``fuzzinator.call.StreamRegexFilter`` has been renamed to ``.RegexFilter``
    to enable arbitrary filtering of issues, and can match multiple patterns.
  * ``fuzzinator.call.StreamMonitoredSubprocessCall`` regex patterns are
    multiline.
  * ``fuzzinator.fuzzer.AFLRunner`` supports AFL's master and slave concepts.
  * ``fuzzinator.fuzzer.ListDirectory`` works with a glob pattern instead of a
    simple directory name to collect test cases.
  * ``fuzzinator.fuzzer.SubprocessRunner`` and ``.ListDirectory`` can work both
    as file content generators and as file path generators.
  * ``fuzzinator.update.TimestampUpdateCondition`` supports time intervals
    longer than 24 hours.
  * All Popen-based subprocess-executing building blocks
    (``fuzzinator.call.StdinSubprocessCall``,
    ``.StreamMonitoredSubprocessCall``, ``.SubprocessCall``,
    ``.SubprocessPropertyDecorator``, ``.TestRunnerSubprocessCall``,
    ``fuzzinator.fuzzer.SubprocessRunner``, and
    ``fuzzinator.update.SubprocessUpdate``) have timeout support and avoid shell
    invocation.
  * ``fuzzinator.reduce.Picire`` has been updated to use *Picire* 18.1.
  * ``fuzzinator.reduce.Picireny`` has been updated to use *Picireny* 18.2.
  * All reporters (``fuzzinator.tracker.MonorailReport``, ``.BugzillaReport``,
    ``.GithubReport``) have been changed to use format string syntax ({key})
    instead of template syntax ($key) in their report templates, and all handle
    missing keys gracefully.

* TUI improvements:

  * Support for simpler custom color schemes.
  * More convenient bug report editor.
  * Support for both text and binary copying of test cases to the clipboard.
  * Support for declaring bug duplicates manually.
  * New and improved dialogs (about dialog, closing of dialogs).
  * Improved event handling (responsivity, updated issues, invalid issues).

* General usability improvements:

  * More flexible configuration format enabling config sections to be split
    across multiple files, and keys to have no value.
  * Support for command line arguments specified in list files to help with
    config file fragments.
  * Useful command line argument aliases and new arguments (appearance,
    verbosity, Python interpreter limits, fuzz session length).

* Under-the-hood improvements:

  * Improved logging.
  * Added testing infrastructure: unit testing of SUT calls, fuzzers, and SUT
    updaters via tox; continuous testing via Travis and AppVeyor CI services.
  * Added documentation: out-of-sources tutorial and auto-generated API docs via
    Sphinx; online documentation hosting on Read-the-Docs.
  * Various bug fixes and refactorings (in core components, in building blocks,
    and in user interfaces).


16.10
=====

First public release of the *Fuzzinator* Random Testing Framework.

Summary of main features:

* Core scheduler/controller of fuzzing-related jobs (update, fuzz, reduce).
* MongoDB-based issue repository.
* Extensible framework with predefined building blocks for invoking SUTs,
  detecting issues, and determining uniqueness; for generating test cases and
  transporting them to SUTs; for minimizing issue-triggering tests; and for
  keeping SUTs under development up-to-date.
* Configurability via INI files.
* CLI and Urwid-based TUI.
