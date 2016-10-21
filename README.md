# Fuzzinator
_Random Testing Framework_


## Requirements

* Python >= 3.4
* pip and setuptools Python packages (the latter is automatically installed by
  pip)
* MongoDB (either local installation or access to remote database)
* Picireny (see its [documentation](https://github.com/renatahodovan/picireny)
  why manual installation is required)


## Install

The quick way:

    pip install fuzzinator

Alternatively, by cloning the project and running setuptools:

    python setup.py install


## Usage

A common form of *Fuzzinator*'s usage:

    fuzzinator --tui --force-encoding=utf-8 <path/to/the/config.ini>


## Compatibility

*Fuzzinator* was tested on:

* Linux (Ubuntu 14.04 / 15.10)
* Mac OS X (OS X El Capitan - 10.11).


## Acknowledgements

The authors are immensely grateful to Dr. Heinz Doofenshmirtz for the continuous
inspiration.


## Copyright and Licensing

See [LICENSE](LICENSE.md).
