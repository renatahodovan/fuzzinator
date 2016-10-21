# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import importlib

from inspect import isclass


def import_entity(name):
    steps = name.split('.')
    module_name = '.'.join(steps[0:-1])
    entity_name = steps[-1]
    module = importlib.import_module(module_name)
    return eval('module.' + entity_name)


def config_get_kwargs(config, section):
    return dict(config.items(section)) if config.has_section(section) else dict()


class CallableContextManager(object):
    def __init__(self, callable):
        self._callable = callable

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, *args, **kwargs):
        return self._callable(*args, **kwargs)


def config_get_callable(config, section, option):
    """
    Return an object that can both act as a context manager and as a callable,
    as well as a dictionary with key-value pairs to be used when calling the
    object.
    """
    # get the python entity (function or callable context manager class) named
    # in $(section:option) and its call arguments given in $(section.option:*)
    entity = import_entity(config.get(section, option))
    entity_kwargs = config_get_kwargs(config, section + '.' + option)

    # find decorator classes named in $(section:option.decorate(*)) and apply
    # them with their arguments given in $(section.option.decorate(*):*)
    opt_prefix = option + '.decorate('
    opt_suffix = ')'
    decorator_options = [opt for opt in config.options(section)
                         if opt.startswith(opt_prefix) and
                         opt.endswith(opt_suffix)]
    decorator_options.sort(key=lambda opt: int(opt[len(opt_prefix):-len(opt_suffix)]))
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

    # return the callable context manager and its call arguments
    return callable_ctx, entity_kwargs


def config_get_name_from_section(section_name):
    return section_name.split('.', maxsplit=1)[1]


def config_get_with_writeback(config, section, option, fallback):
    if not config.has_section(section):
        config.add_section(section)

    if not config.has_option(section, option):
        config.set(section, option, fallback)

    return config.get(section, option)
