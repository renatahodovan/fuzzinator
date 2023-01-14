# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import hashlib
import json
import logging
import os
import shlex
import sys

from collections import OrderedDict
from configparser import ConfigParser
from io import StringIO
from inspect import signature
from math import inf
from uuid import uuid4

import chardet

from inators.imp import import_object

logger = logging.getLogger(__name__)


def config_get_kwargs(config, section):
    return dict(config.items(section)) if config.has_section(section) else {}


def config_init_object(config, cls, kwargs):
    if any(param == 'work_dir' for param in signature(cls.__init__).parameters):
        kwargs['work_dir'] = os.path.join(as_path(config.get('fuzzinator', 'work_dir')), f'{os.getpid()}-{cls.__name__}-{uuid4().hex}')
    return cls(**kwargs)


def config_get_object(config, section, options, *, init_kwargs=None):
    """
    Create an object as defined by ``$(section:option)`` in the configuration.

    1. Load the "base" class given with fully qualified name in
        ``$(section:option)`` (for the first ``option`` that exists in
        ``options``).
    2. For all decorators in ``$(section:option.decorate(*))``:
        a. Load the "decorator" class given with fully qualified name in
            ``$(section:option.decorate(n))``.
        b. Instantiate the "decorator" class with keyword arguments given in
            ``$(section.option.decorate(n):*)``.
        c. Call the "decorator" object with the "base" class and replace the
            "base" class with the result.
    3. Instantiate the "base" class with keyword arguments given in
        ``$(section.option:*)`` and in ``init_kwargs``, and return the object.

    :param configparser.ConfigParser config: the configuration options of the
        fuzz session.
    :param str section: section name.
    :param options: list of option names that can define the object.
    :type options: str or list[str]
    :param init_kwargs: extra keyword arguments to use when instantiating the
        object.
    :return: an object defined by the first option that exists in the section,
        or None if section contains none of the options.
    """
    options = options if isinstance(options, list) else [options]

    obj = None
    for option in options:
        if not config.has_option(section, option):
            continue

        # 1) get the class named in $(section:option)
        obj_class = import_object(config.get(section, option))

        # 2) find decorator classes named in $(section:option.decorate(*)) and apply
        # them with their arguments given in $(section.option.decorate(*):*)
        opt_prefix = f'{option}.decorate('
        opt_suffix = ')'
        decorator_options = [opt for opt in config.options(section)
                             if opt.startswith(opt_prefix) and opt.endswith(opt_suffix)]
        decorator_options.sort(key=lambda opt, pre=opt_prefix, suf=opt_suffix: int(opt[len(pre):-len(suf)]))
        for decopt in decorator_options:
            decorator_class = import_object(config.get(section, decopt))
            decorator_kwargs = config_get_kwargs(config, f'{section}.{decopt}')
            decorator = config_init_object(config, decorator_class, decorator_kwargs)
            obj_class = decorator(obj_class)

        # 3) compute class instantiation arguments
        obj_kwargs = {}

        # 3.a) get old-style arguments from $(section.option.init:*)
        init_section = f'{section}.{option}.init'
        if config.has_section(init_section):
            logger.warning('.init sections are deprecated (%s)', init_section)
            obj_kwargs.update(config_get_kwargs(config, init_section))

        # 3.b) get arguments from $(section.option:*)
        obj_kwargs.update(config_get_kwargs(config, f'{section}.{option}'))

        # 3.c) get arguments from init_kwargs
        if init_kwargs:
            obj_kwargs.update(init_kwargs)

        # 3.d) instantiate class
        obj = config_init_object(config, obj_class, obj_kwargs)

        # break the loop after finding the first matching option.
        break

    # return the object
    return obj


def config_get_fuzzers(config):

    def filter_available_sections(section_name):
        if not config.has_section(section_name):
            return

        if not sub_parser.has_section(section_name):
            sub_parser.add_section(section_name)

        for option in config.options(section_name):
            sub_parser[section_name][option] = config.get(section_name, option).replace(work_dir, '')

            for subsection_name in (f'{section_name}.{option}', f'{section_name}.{option}.init'):
                filter_available_sections(subsection_name)

            opt_prefix = f'{option}.decorate('
            opt_suffix = ')'
            decorator_options = [opt for opt in config.options(section_name) if
                                 opt.startswith(opt_prefix) and opt.endswith(opt_suffix)]
            decorator_options.sort(key=lambda opt, pre=opt_prefix, suf=opt_suffix: int(opt[len(pre):-len(suf)]))
            for decopt in decorator_options:
                for subsection_name in (f'{section_name}.{decopt}', f'{section_name}.{decopt}.init'):
                    filter_available_sections(subsection_name)

    work_dir = config.get('fuzzinator', 'work_dir')
    # Extract fuzzer names from sections describing fuzzing jobs.
    fuzzer_names = [section.split('.', maxsplit=1)[1] for section in config.sections() if section.startswith('fuzz.') and section.count('.') == 1]
    fuzzers = OrderedDict()

    for fuzzer in fuzzer_names:
        sut = config.get(f'fuzz.{fuzzer}', 'sut')
        sub_parser = ConfigParser(interpolation=None, strict=False, allow_no_value=True)
        filter_available_sections(f'sut.{sut}')
        filter_available_sections(f'fuzz.{fuzzer}')

        config_str = StringIO()
        sub_parser.write(config_str, space_around_delimiters=False)
        src = config_str.getvalue()
        fuzzers[fuzzer] = dict(sut=sut, subconfig=hashlib.md5(src.encode('utf-8', errors='ignore')).hexdigest()[:9], src=src)

    return fuzzers


def as_list(s):
    if isinstance(s, list):
        return s
    return json.loads(s)


def as_dict(s):
    if isinstance(s, dict):
        return s
    return json.loads(s)


def as_bool(s):
    if isinstance(s, bool):
        return s
    return s in [1, '1', 'True', 'true']


def as_int_or_inf(s):
    if isinstance(s, int) or s == inf:
        return s
    return inf if s == 'inf' else int(s)


def as_path(s):
    return os.path.expanduser(os.path.expandvars(s))


def as_pargs(s):
    return [as_path(e) for e in shlex.split(s, posix=sys.platform != 'win32')]


def decode(b, encoding=None):
    encoding = encoding or chardet.detect(b)['encoding'] or 'latin-1'
    return b.decode(encoding, errors='ignore')
