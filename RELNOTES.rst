==========================
*Fuzzinator* Release Notes
==========================

.. start included documentation

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
