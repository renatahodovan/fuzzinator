# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os.path import dirname, join
from setuptools import setup, find_packages

with open(join(dirname(__file__), 'fuzzinator/VERSION'), 'rb') as f:
    version = f.read().decode('ascii').strip()

setup(
    name='fuzzinator',
    version=version,
    packages=find_packages(),
    url='https://github.com/renatahodovan/fuzzinator',
    license='BSD',
    author='Renata Hodovan, Akos Kiss',
    author_email='hodovan@inf.u-szeged.hu, akiss@inf.u-szeged.hu',
    description='Fuzzinator Random Testing Framework',
    long_description=open('README.rst').read(),
    zip_safe=False,
    include_package_data=True,
    install_requires=['chardet', 'keyring', 'keyrings.alt', 'pexpect', 'picire==18.1', 'picireny==18.2', 'psutil',
                      'PyGithub', 'pymongo', 'pyperclip', 'python-bugzilla', 'google-api-python-client',
                      'rainbow_logging_handler', 'sphinx', 'sphinx_rtd_theme',
                      'tornado', 'urwid'],
    entry_points={
        'console_scripts': ['fuzzinator = fuzzinator.executor:execute']
    }
)
