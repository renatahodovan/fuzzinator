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
    long_description=open('README.md').read(),
    zip_safe=False,
    include_package_data=True,
    install_requires=['chardet', 'picire', 'pexpect', 'psutil',
                      'PyGithub', 'pymongo', 'pyperclip', 'python-bugzilla',
                      'rainbow_logging_handler', 'tornado', 'urwid'],
    entry_points={
        'console_scripts': ['fuzzinator = fuzzinator.executor:execute']
    }
)
