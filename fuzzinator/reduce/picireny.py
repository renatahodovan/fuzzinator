# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
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
from .reducer import Reducer

logger = logging.getLogger(__name__)


class Picireny(Reducer):
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

    def __init__(self, *, parallel=False, combine_loops=False,
                 split_method='zeller', subset_first=True, subset_iterator='forward', complement_iterator='forward',
                 jobs=os.cpu_count(), max_utilization=100,
                 hddmin=None, antlr=None, format=None, grammar=None, start=None, replacements=None, lang='python',
                 hdd_star=True, flatten_recursion=False, squeeze_tree=True, skip_unremovable=True, skip_whitespace=False, build_hidden_tokens=False,
                 encoding=None, granularity=2, cache_class='ContentCache', cleanup=True,
                 work_dir, **kwargs):
        parallel = as_bool(parallel)
        combine_loops = as_bool(combine_loops)
        split_method = getattr(picire.config_splitters, split_method)
        subset_first = as_bool(subset_first)
        subset_iterator = getattr(picire.config_iterators, subset_iterator)
        complement_iterator = getattr(picire.config_iterators, complement_iterator)
        jobs = int(jobs) if parallel else 1
        max_utilization = int(max_utilization)

        self.hddmin = picireny.cli.args_hdd_choices[hddmin if hddmin else 'full']
        self.lang = lang
        self.hdd_star = as_bool(hdd_star)
        self.flatten_recursion = as_bool(flatten_recursion)
        self.squeeze_tree = as_bool(squeeze_tree)
        self.skip_unremovable = as_bool(skip_unremovable)
        self.skip_whitespace = as_bool(skip_whitespace)
        self.build_hidden_tokens = as_bool(build_hidden_tokens)

        self.antlr = picireny.process_antlr4_path(as_path(antlr) if antlr else None)
        self.input_format, self.start = picireny.process_antlr4_format(format=format,
                                                                       grammar=[as_path(g) for g in as_list(grammar)] if grammar else None,
                                                                       start=start,
                                                                       replacements=replacements)

        self.encoding = encoding
        self.granularity = as_int_or_inf(granularity)
        self.cache_class = getattr(picire, cache_class)
        if parallel:
            self.cache_class = picire.shared_cache_decorator(self.cache_class)
        self.cleanup = as_bool(cleanup)

        # Choose the reducer class that will be used and its configuration.
        self.reduce_config = {'split': split_method}
        if not parallel:
            self.reduce_class = picire.LightDD
            self.reduce_config['subset_iterator'] = subset_iterator
            self.reduce_config['complement_iterator'] = complement_iterator
            self.reduce_config['subset_first'] = subset_first
        else:
            self.reduce_config['proc_num'] = jobs
            self.reduce_config['max_utilization'] = max_utilization

            if combine_loops:
                self.reduce_class = picire.CombinedParallelDD
                self.reduce_config['config_iterator'] = picire.CombinedIterator(subset_first, subset_iterator, complement_iterator)
            else:
                self.reduce_class = picire.ParallelDD
                self.reduce_config['subset_iterator'] = subset_iterator
                self.reduce_config['complement_iterator'] = complement_iterator
                self.reduce_config['subset_first'] = subset_first

        self.work_dir = work_dir

    def __call__(self, *, sut_call, issue, listener, ident):
        logging.getLogger('picireny').setLevel(logger.level)

        if self.antlr is None:
            logger.warning('Processing the arguments of picireny failed (no antlr).')
            return None, []

        if not (self.input_format and self.start):
            logger.warning('Processing the arguments of picireny failed (no input format or start rule).')
            return None, []

        src = issue['test']
        if isinstance(src, bytes):
            encoding = self.encoding or chardet.detect(src)['encoding'] or 'latin-1'
        else:
            encoding = self.encoding or 'latin-1'
            src = src.encode(encoding, errors='ignore')

        file_name = issue.get('filename', 'test')

        new_issues = dict()
        tester_config = dict(
            sut_call=sut_call,
            issue=issue,
            listener=listener,
            ident=ident,
            encoding=encoding,
            new_issues=new_issues,
        )

        try:
            hdd_tree = picireny.build_with_antlr4(input=file_name,
                                                  src=src,
                                                  encoding=encoding,
                                                  out=self.work_dir,
                                                  input_format=self.input_format,
                                                  start=self.start,
                                                  antlr=self.antlr,
                                                  lang=self.lang,
                                                  build_hidden_tokens=self.build_hidden_tokens,
                                                  cleanup=self.cleanup)

            reduced_file = picireny.reduce(hdd_tree=hdd_tree,
                                           reduce_class=self.reduce_class,
                                           reduce_config=self.reduce_config,
                                           tester_class=PicireTester,
                                           tester_config=tester_config,
                                           input=file_name,
                                           encoding=encoding,
                                           out=self.work_dir,
                                           hddmin=self.hddmin,
                                           hdd_star=self.hdd_star,
                                           flatten_recursion=self.flatten_recursion,
                                           squeeze_tree=self.squeeze_tree,
                                           skip_unremovable=self.skip_unremovable,
                                           skip_whitespace=self.skip_whitespace,
                                           unparse_with_whitespace=not self.build_hidden_tokens,
                                           granularity=self.granularity,
                                           cache_class=self.cache_class,
                                           cleanup=self.cleanup)
        except Exception as e:
            logger.warning('Exception in picireny', exc_info=e)
            return None, list(new_issues.values())

        with open(reduced_file, 'rb') as f:
            src = f.read()

        return src, list(new_issues.values())
