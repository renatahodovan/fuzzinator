.. image:: docs/img/fuzzinator-black-on-trans-289x49.png

*Fuzzinator: Random Testing Framework*

.. image:: https://img.shields.io/pypi/v/fuzzinator?logo=python&logoColor=white
   :target: https://pypi.org/project/fuzzinator/
.. image:: https://img.shields.io/pypi/l/fuzzinator?logo=open-source-initiative&logoColor=white
   :target: https://pypi.org/project/fuzzinator/
.. image:: https://img.shields.io/github/actions/workflow/status/renatahodovan/fuzzinator/main.yml?branch=master&logo=github&logoColor=white
   :target: https://github.com/renatahodovan/fuzzinator/actions
.. image:: https://img.shields.io/readthedocs/fuzzinator?logo=read-the-docs&logoColor=white
   :target: http://fuzzinator.readthedocs.io/en/latest/
.. image:: https://img.shields.io/gitter/room/inbugwetrust/fuzzinator?color=blueviolet&logo=gitter&logoColor=white
   :target: https://gitter.im/inbugwetrust/fuzzinator

.. start included documentation

*Fuzzinator* is a fuzzing framework that helps you to automate tasks usually
needed during a fuzz session:

* run your favorite `test generator`_ and feed the test cases to the
  software-under-test,
* catch and save the unique issues,
* reduce_ the failing test cases,
* ease the reporting of issues in bug trackers (e.g., Bugzilla or GitHub),
* regularly update SUTs if needed, and
* schedule multiple SUTs and generators without overloading your workstation.

All the above features are fully customizable either by writing a simple config
file or by implementing Python snippets to cover special needs. Check out some
slides_ about *Fuzzinator* for a general overview, or see the Tutorial_ for a
detailed walk-through. There is also a repository collecting configurations_ for
various real-life SUTs and fuzzers.

To help tracking the progress of the fuzzing, *Fuzzinator* provides three
interfaces:

* an interactive Web UI (WUI) (supported on all platforms) that gives a
  continuously updated overview about the currently running tasks, statistics
  about the efficacy of the test generators, and the found issues (and also
  supports reporting them);
* an interactive Text UI (TUI) (supported on Linux and Mac OS X only) that
  supports the same functionality as the WUI, but as a retro-style console
  interface; and
* a dump-mode (supported on every platform) that displays the news on line-based
  consoles.


.. _`test generator`: https://github.com/renatahodovan/fuzzinator/wiki#list-of-fuzzers-test-generators
.. _reduce: https://github.com/renatahodovan/fuzzinator/wiki#list-of-test-case-reducers
.. _slides: http://www.slideshare.net/hodovanrenata/fuzzinator-in-bug-we-trust
.. _Tutorial: docs/tutorial.rst
.. _configurations: https://github.com/renatahodovan/fuzzinator-configs


Requirements
============

* Python_ >= 3.6
* MongoDB_ >= 3.6 (either local installation or access to remote database)
* Java_ SE >= 7 JRE or JDK (optional, required if the *Picireny* test case
  reducer is used)

.. _Python: https://www.python.org
.. _MongoDB: https://www.mongodb.com
.. _Java: https://www.oracle.com/java/


Install
=======

To install the latest release of *Fuzzinator* from PyPI_, use pip_::

    pip install fuzzinator

Alternatively, for the development version, clone the project and perform a
local install::

    pip install .

.. _PyPI: https://pypi.org/
.. _pip: https://pip.pypa.io


Usage
=====

A common form of *Fuzzinator*'s usage::

    fuzzinator --wui <path/to/the/config.ini>


Compatibility
=============

*Fuzzinator* was tested on:

* Linux (Ubuntu 14.04 / 16.04 / 18.04 / 20.04)
* OS X / macOS (10.11 / 10.12 / 10.13 / 10.14 / 10.15 / 11)
* Windows (Server 2012 R2 / Server version 1809 / Windows 10)


Acknowledgement and Citations
=============================

The authors are immensely grateful to Dr. Heinz Doofenshmirtz for the continuous
inspiration.

Background on *Fuzzinator* is published in:

* Renata Hodovan and Akos Kiss. Fuzzinator: An Open-Source Modular Random
  Testing Framework.
  In Proceedings of the 11th IEEE International Conference on Software Testing,
  Verification and Validation (ICST 2018), pages 416-421, Vasteras, Sweden,
  April 2018. IEEE.
  https://doi.org/10.1109/ICST.2018.00050

.. end included documentation


Copyright and Licensing
=======================

Licensed under the BSD 3-Clause License_.

.. _License: LICENSE.rst
