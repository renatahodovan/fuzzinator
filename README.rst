==========
Fuzzinator
==========
*Random Testing Framework*

.. image:: https://badge.fury.io/py/fuzzinator.svg
   :target: https://badge.fury.io/py/fuzzinator
.. image:: https://travis-ci.org/renatahodovan/fuzzinator.svg?branch=master
   :target: https://travis-ci.org/renatahodovan/fuzzinator
.. image:: https://ci.appveyor.com/api/projects/status/mhdvgk65p0r7fkxr/branch/master?svg=true
   :target: https://ci.appveyor.com/project/renatahodovan/fuzzinator/branch/master
.. image:: https://readthedocs.org/projects/fuzzinator/badge/?version=latest
   :target: http://fuzzinator.readthedocs.io/en/latest/

.. start included documentation

*Fuzzinator* is a fuzzing framework that helps you to automate tasks usually
needed during a fuzz session:

* run your favorite test generator and feed the test cases to the
  system-under-test,
* catch and save the unique issues,
* reduce the failing test cases,
* ease the reporting of issues in bug trackers (e.g., Bugzilla or GitHub),
* regularly update SUTs if needed, and
* schedule multiple SUTs and generators without overloading your workstation.

All the above features are fully customizable either by writing a simple config
file or by implementing Python snippets to cover special needs. Check out some
slides_ about *Fuzzinator* for a general overview, or see the
`Tutorial <docs/tutorial.rst>`_ for a detailed walk-through on the config files.

To help tracking the progress of the fuzzing, *Fuzzinator* provides two
interfaces:

* an interactive TUI (supported on Linux and Mac OS X) that gives a continuously
  updated overview about the currently running tasks, statistics about the
  efficacy of the test generators, and the found issues (and also supports
  reporting them); and
* a dump-mode (supported on every platform) that displays the news on line-based
  consoles.

Although *Fuzzinator* itself doesn't come with test generators (except for an
example random character sequence generator), you can find a list of useful
generators in the wiki_.

.. _Tutorial: docs/tutorial.rst
.. _slides: http://www.slideshare.net/hodovanrenata/fuzzinator-in-bug-we-trust
.. _wiki: https://github.com/renatahodovan/fuzzinator/wiki


Requirements
============

* Python_ >= 3.4
* pip_ and setuptools Python packages (the latter is automatically installed by
  pip)
* MongoDB_ (either local installation or access to remote database)

.. _Python: https://www.python.org
.. _pip: https://pip.pypa.io
.. _MongoDB: https://www.mongodb.com


Install
=======

The quick way::

    pip install fuzzinator

Alternatively, by cloning the project and running setuptools::

    python setup.py install


Usage
=====

A common form of *Fuzzinator*'s usage::

    fuzzinator --tui -U <path/to/the/config.ini>


Compatibility
=============

*Fuzzinator* was tested on:

* Linux (Ubuntu 14.04 / 15.10 / 16.04)
* Mac OS X (OS X El Capitan - 10.11).


Acknowledgements
================

The authors are immensely grateful to Dr. Heinz Doofenshmirtz for the continuous
inspiration.

.. end included documentation


Copyright and Licensing
=======================

Licensed under the BSD 3-Clause License_.

.. _License: LICENSE.rst
