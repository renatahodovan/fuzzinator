# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import hashlib
import importlib

from collections import OrderedDict
from configparser import ConfigParser, ExtendedInterpolation
from inspect import isclass
from io import StringIO


def import_entity(name):
    steps = name.split('.')
    return getattr(importlib.import_module('.'.join(steps[0:-1])), steps[-1])


def config_get_kwargs(config, section):
    return dict(config.items(section)) if config.has_section(section) else dict()


class CallableContextManager(object):
    def __init__(self, callable):
        self._callable = callable

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __call__(self, *args, **kwargs):
        return self._callable(*args, **kwargs)


def config_get_callable(config, section, options):
    """
    Return an object that can both act as a context manager and as a callable,
    as well as a dictionary with key-value pairs to be used when calling the
    object.
    """
    options = options if isinstance(options, list) else [options]

    callable_ctx, entity_kwargs = None, None
    for option in options:
        if not config.has_option(section, option):
            continue

        # get the python entity (function or callable context manager class) named
        # in $(section:option) and its call arguments given in $(section.option:*)
        entity = import_entity(config.get(section, option))
        entity_kwargs = config_get_kwargs(config, section + '.' + option)

        # find decorator classes named in $(section:option.decorate(*)) and apply
        # them with their arguments given in $(section.option.decorate(*):*)
        opt_prefix = option + '.decorate('
        opt_suffix = ')'
        decorator_options = [opt for opt in config.options(section)
                             if opt.startswith(opt_prefix) and opt.endswith(opt_suffix)]
        decorator_options.sort(key=lambda opt, pre=opt_prefix, suf=opt_suffix: int(opt[len(pre):-len(suf)]))
        for decopt in decorator_options:
            decorator_class = import_entity(config.get(section, decopt))
            decorator_kwargs = config_get_kwargs(config, section + '.' + decopt)
            decorator = decorator_class(**decorator_kwargs)
            entity = decorator(entity)

        # if entity is a callable context manager class, instantiate it with
        # arguments given in $(section.option.init:*)
        if isclass(entity):
            init_kwargs = {}
            if config.has_section(section + '.' + option + '.init'):
                init_kwargs = config_get_kwargs(config, section + '.' + option + '.init')
            callable_ctx = entity(**init_kwargs)
        # if entity is a function, wrap it into a default callable context manager
        # object
        else:
            callable_ctx = CallableContextManager(entity)

        # break the loop after finding the first matching option.
        break

    # return the callable context manager and its call arguments
    return callable_ctx, entity_kwargs


def config_get_with_writeback(config, section, option, fallback):
    if not config.has_section(section):
        config.add_section(section)

    if not config.has_option(section, option) or not config.get(section, option):
        config.set(section, option, fallback)

    return config.get(section, option)


def config_get_fuzzers(config):

    def filter_available_sections(section_name):
        if not config.has_section(section_name):
            return

        if not sub_parser.has_section(section_name):
            sub_parser.add_section(section_name)

        for option in config.options(section_name):
            sub_parser[section_name][option] = config.get(section_name, option).replace(work_dir, '')

            for subsection_name in (section_name + '.' + option, section_name + '.' + option + '.init'):
                filter_available_sections(subsection_name)

            opt_prefix = option + '.decorate('
            opt_suffix = ')'
            decorator_options = [opt for opt in config.options(section_name) if
                                 opt.startswith(opt_prefix) and opt.endswith(opt_suffix)]
            decorator_options.sort(key=lambda opt, pre=opt_prefix, suf=opt_suffix: int(opt[len(pre):-len(suf)]))
            for decopt in decorator_options:
                for subsection_name in (section_name + '.' + decopt, section_name + '.' + decopt + '.init'):
                    filter_available_sections(subsection_name)

    work_dir = config.get('fuzzinator', 'work_dir')
    # Extract fuzzer names from sections describing fuzzing jobs.
    fuzzer_names = [section.split('.', maxsplit=1)[1] for section in config.sections() if section.startswith('fuzz.') and section.count('.') == 1]
    fuzzers = OrderedDict()

    for fuzzer in fuzzer_names:
        sut = config.get('fuzz.' + fuzzer, 'sut')
        sub_parser = ConfigParser(interpolation=ExtendedInterpolation(),
                                  strict=False,
                                  allow_no_value=True)
        filter_available_sections('sut.' + sut)
        filter_available_sections('fuzz.' + fuzzer)

        config_str = StringIO()
        sub_parser.write(config_str, space_around_delimiters=False)
        src = config_str.getvalue()
        fuzzers[fuzzer] = dict(sut=sut, subconfig=hashlib.md5(src.encode('utf-8', errors='ignore')).hexdigest()[:9], src=src)

    return fuzzers
