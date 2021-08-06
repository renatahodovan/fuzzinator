# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

from argparse import Namespace
from shutil import rmtree

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

      - ``split_class``, ``granularity``, ``subset_first``, ``subset_iterator``,
        ``complement_iterator``, ``parallel``, ``combine_loops``, ``jobs``,
        ``max_utilization``, ``format``, ``grammar``, ``start``,
        ``replacements``, ``antlr``, ``lang``, ``build_hidden_tokens``,
        ``hddmin``, ``hdd_phases``, ``hdd_star``, ``flatten_recursion``,
        ``squeeze_tree``, ``skip_unremovable``, ``skip_whitespace``,
        ``encoding``, ``cache_class``

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

    def __init__(self, *,
                 split_class='zeller', granularity=2, subset_first=True, subset_iterator='forward', complement_iterator='forward',
                 parallel=False, combine_loops=False, jobs=os.cpu_count(), max_utilization=100,
                 format=None, grammar=None, start=None, replacements=None, antlr=None, lang='python', build_hidden_tokens=False,
                 hddmin='hdd', hdd_phases='["prune"]', hdd_star=True,
                 flatten_recursion=False, squeeze_tree=True, skip_unremovable=True, skip_whitespace=False,
                 encoding=None, cache_class='ContentCache',
                 work_dir, **kwargs):

        super().__init__(split_class=split_class, granularity=granularity, subset_first=subset_first, subset_iterator=subset_iterator, complement_iterator=complement_iterator,
                         parallel=parallel, combine_loops=combine_loops, jobs=jobs, max_utilization=max_utilization,
                         encoding=encoding, cache_class=cache_class)

        args = Namespace(format=format,
                         grammar=[as_path(g) for g in as_list(grammar)] if grammar else None,
                         start=start,
                         replacements=replacements,
                         antlr=as_path(antlr) if antlr else None)
        picireny.cli.process_antlr4_args(args)
        self.input_format = args.input_format
        self.start = args.start
        self.antlr = args.antlr

        self.lang = lang
        self.build_hidden_tokens = as_bool(build_hidden_tokens)
        self.hddmin = picireny.cli.args_hdd_choices[hddmin]
        self.hdd_phase_configs = [picireny.cli.args_phase_choices[phase] for phase in as_list(hdd_phases)]
        self.hdd_star = as_bool(hdd_star)
        self.flatten_recursion = as_bool(flatten_recursion)
        self.squeeze_tree = as_bool(squeeze_tree)
        self.skip_unremovable = as_bool(skip_unremovable)
        self.skip_whitespace = as_bool(skip_whitespace)

        self.work_dir = work_dir

    def __call__(self, *, sut_call, issue, on_job_progressed):
        logging.getLogger('picire').setLevel(logger.level)
        logging.getLogger('picireny').setLevel(logger.level)

        try:
            test, tester = self._prepare_call(sut_call=sut_call,
                                              issue=issue,
                                              on_job_progressed=on_job_progressed)

            hdd_tree = picireny.build_with_antlr4(test.src,
                                                  input_format=self.input_format, start=self.start,
                                                  antlr=self.antlr, lang=self.lang,
                                                  build_hidden_tokens=self.build_hidden_tokens,
                                                  work_dir=self.work_dir)
            rmtree(self.work_dir)

            hdd_tree = picireny.reduce(hdd_tree,
                                       hddmin=self.hddmin,
                                       reduce_class=self.reduce_class, reduce_config=self.reduce_config,
                                       tester_class=tester.tester_class, tester_config=tester.tester_config,
                                       cache_class=self.cache_class, unparse_with_whitespace=not self.build_hidden_tokens,
                                       hdd_phase_configs=self.hdd_phase_configs, hdd_star=self.hdd_star,
                                       flatten_recursion=self.flatten_recursion,
                                       squeeze_tree=self.squeeze_tree,
                                       skip_unremovable=self.skip_unremovable,
                                       skip_whitespace=self.skip_whitespace)

            out_src = hdd_tree.unparse(with_whitespace=not self.build_hidden_tokens)
            out_src = out_src.encode(test.encoding, errors='ignore')
            return out_src, list(tester.new_issues.values())
        except Exception as e:
            logger.warning('Exception in picireny', exc_info=e)
            return None, list(tester.new_issues.values())
