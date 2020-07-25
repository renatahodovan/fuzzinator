# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

import chardet
import picire
import picireny

from ..config import as_bool, as_int_or_inf, as_list, as_path
from .picire_tester import PicireTester

logger = logging.getLogger(__name__)


def Picireny(sut_call, sut_call_kwargs, listener, ident, issue, work_dir,
             hddmin=None, parallel=False, combine_loops=False,
             split_method='zeller', subset_first=True, subset_iterator='forward', complement_iterator='forward',
             jobs=os.cpu_count(), max_utilization=100, encoding=None,
             antlr=None, format=None, grammar=None, start=None, replacements=None, lang='python',
             hdd_star=True, flatten_recursion=False, squeeze_tree=True, skip_unremovable=True, skip_whitespace=False,
             build_hidden_tokens=False, granularity=2, cache_class='ContentCache', cleanup=True,
             **kwargs):
    """
    Test case reducer based on the Picireny Hierarchical Delta Debugging
    Framework.

    **Mandatory parameters of the reducer:**

      - Either ``format`` or ``grammar`` and ``start`` must be defined.

    **Optional parameters of the reducer:**

      - ``hddmin``, ``parallel``, ``combine_loops``, ``split_method``, ``subset_first``,
        ``subset_iterator``, ``complement_iterator``, ``jobs``, ``max_utilization``, ``encoding``,
        ``antlr``, ``format``, ``grammar``, ``start``, ``replacements``, ``lang``,
        ``hdd_star``, ``flatten_recursion``, ``squeeze_tree``, ``skip_unremovable``, ``skip_whitespace``,
        ``build_hidden_tokens``, ``granularity``, ``cache_class``, ``cleanup``

    Refer to https://github.com/renatahodovan/picireny for configuring Picireny.

    Note: This reducer is capable of detecting new issues found during the test
    reduction (if any).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            #call=...
            cost=1
            reduce=fuzzinator.reduce.Picireny
            reduce_cost=4

            [sut.foo.reduce]
            hddmin=full
            grammar=["/home/alice/grammars-v4/HTMLParser.g4", "/home/alice/grammars-v4/HTMLLexer.g4"]
            start=htmlDocument
            parallel=True
            jobs=4
            subset_iterator=skip
    """

    logging.getLogger('picireny').setLevel(logger.level)

    antlr = picireny.process_antlr4_path(as_path(antlr) if antlr else None)
    if antlr is None:
        return None, []

    input_format, start = picireny.process_antlr4_format(format=format,
                                                         grammar=[as_path(g) for g in as_list(grammar)] if grammar else None,
                                                         start=start,
                                                         replacements=replacements)

    if not (input_format and start):
        logger.warning('Processing the arguments of picireny failed.')
        return None, []

    src = issue['test']
    file_name = issue.get('filename', 'test')

    hddmin = picireny.cli.args_hdd_choices[hddmin if hddmin else 'full']
    parallel = as_bool(parallel)
    combine_loops = as_bool(combine_loops)
    split_method = getattr(picire.config_splitters, split_method)
    subset_first = as_bool(subset_first)
    subset_iterator = getattr(picire.config_iterators, subset_iterator)
    complement_iterator = getattr(picire.config_iterators, complement_iterator)
    jobs = int(jobs) if parallel else 1
    max_utilization = int(max_utilization)
    encoding = encoding or chardet.detect(src)['encoding'] or 'utf-8'
    hdd_star = as_bool(hdd_star)
    flatten_recursion = as_bool(flatten_recursion)
    squeeze_tree = as_bool(squeeze_tree)
    skip_unremovable = as_bool(skip_unremovable)
    skip_whitespace = as_bool(skip_whitespace)
    build_hidden_tokens = as_bool(build_hidden_tokens)
    granularity = as_int_or_inf(granularity)
    cleanup = as_bool(cleanup)

    cache_class = getattr(picire, cache_class)
    if parallel:
        cache_class = picire.shared_cache_decorator(cache_class)

    # Choose the reducer class that will be used and its configuration.
    reduce_config = {'split': split_method}
    if not parallel:
        reduce_class = picire.LightDD
        reduce_config['subset_iterator'] = subset_iterator
        reduce_config['complement_iterator'] = complement_iterator
        reduce_config['subset_first'] = subset_first
    else:
        reduce_config['proc_num'] = jobs
        reduce_config['max_utilization'] = max_utilization

        if combine_loops:
            reduce_class = picire.CombinedParallelDD
            reduce_config['config_iterator'] = picire.CombinedIterator(subset_first, subset_iterator, complement_iterator)
        else:
            reduce_class = picire.ParallelDD
            reduce_config['subset_iterator'] = subset_iterator
            reduce_config['complement_iterator'] = complement_iterator
            reduce_config['subset_first'] = subset_first

    issues = dict()
    tester_config = dict(
        sut_call=sut_call,
        sut_call_kwargs=sut_call_kwargs,
        enc=encoding,
        expected=issue['id'],
        listener=listener,
        ident=ident,
        issues=issues
    )

    try:
        hdd_tree = picireny.build_with_antlr4(input=file_name,
                                              src=src,
                                              encoding=encoding,
                                              out=work_dir,
                                              input_format=input_format,
                                              start=start,
                                              antlr=antlr,
                                              lang=lang,
                                              build_hidden_tokens=build_hidden_tokens,
                                              cleanup=cleanup)

        reduced_file = picireny.reduce(hdd_tree=hdd_tree,
                                       reduce_class=reduce_class,
                                       reduce_config=reduce_config,
                                       tester_class=PicireTester,
                                       tester_config=tester_config,
                                       input=file_name,
                                       encoding=encoding,
                                       out=work_dir,
                                       hddmin=hddmin,
                                       hdd_star=hdd_star,
                                       flatten_recursion=flatten_recursion,
                                       squeeze_tree=squeeze_tree,
                                       skip_unremovable=skip_unremovable,
                                       skip_whitespace=skip_whitespace,
                                       unparse_with_whitespace=not build_hidden_tokens,
                                       granularity=granularity,
                                       cache_class=cache_class,
                                       cleanup=cleanup)
    except Exception as e:
        logger.warning('Exception in picireny', exc_info=e)
        return None, list(issues.values())

    with open(reduced_file, 'rb') as f:
        src = f.read()

    return src, list(issues.values())
