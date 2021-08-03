# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

import picireny

from ..config import as_bool, as_list, as_path
from .picire_common import PicireReducer

logger = logging.getLogger(__name__)


class Picireny(PicireReducer):
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

        super().__init__(parallel=parallel, combine_loops=combine_loops,
                         split_method=split_method, subset_first=subset_first, subset_iterator=subset_iterator, complement_iterator=complement_iterator,
                         jobs=jobs, max_utilization=max_utilization,
                         encoding=encoding, granularity=granularity, cache_class=cache_class, cleanup=cleanup,
                         work_dir=work_dir)

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

    def __call__(self, *, sut_call, issue, on_job_progressed):
        logging.getLogger('picireny').setLevel(logger.level)

        if self.antlr is None:
            logger.warning('Processing the arguments of picireny failed (no antlr).')
            return None, []

        if not (self.input_format and self.start):
            logger.warning('Processing the arguments of picireny failed (no input format or start rule).')
            return None, []

        test, tester = self._prepare_call(sut_call=sut_call,
                                          issue=issue,
                                          on_job_progressed=on_job_progressed)

        try:
            hdd_tree = picireny.build_with_antlr4(input=test.file_name,
                                                  src=test.src,
                                                  encoding=test.encoding,
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
                                           tester_class=tester.tester_class,
                                           tester_config=tester.tester_config,
                                           input=test.file_name,
                                           encoding=test.encoding,
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
            return None, list(tester.new_issues.values())

        with open(reduced_file, 'rb') as f:
            src = f.read()

        return src, list(tester.new_issues.values())
