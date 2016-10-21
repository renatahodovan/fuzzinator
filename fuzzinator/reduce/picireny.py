# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import chardet
import json
import logging
import os
import picire
import picireny

from .picire_tester import PicireTester

logger = logging.getLogger(__name__)


def Picireny(sut_call, sut_call_kwargs, listener, ident, issue, work_dir,
             grammar, start_rule, replacements=None, islands=None,
             parallel=False, combine_loops=False,
             split_method='zeller', subset_first=True, subset_iterator='forward', complement_iterator='forward',
             jobs=os.cpu_count(), max_utilization=100, encoding=None, disable_cache=False, cleanup=True,
             **kwargs):
    """
    Test case reducer based on the Picireny Hierarchical Delta Debugging
    Framework.

    Mandatory parameters of the reducer:
      - 'grammar', 'start_rule'
    Optional parameters of the reducer:
      - 'replacements', 'islands', 'parallel', 'combine_loops', 'split_method',
        'subset_first', 'subset_iterator', 'complement_iterator', 'jobs',
        'max_utilization', 'encoding', 'disable_cache', 'cleanup'
    Refer to https://github.com/renatahodovan/picireny for configuring Picireny.

    Note: This reducer is capable of detecting new issues found during the test
    reduction (if any).

    Example configuration snippet:
    [sut.foo]
    #call=...
    cost=1
    reduce=fuzzinator.reduce.Picireny
    reduce_cost=4

    [sut.foo.reduce]
    grammar=/home/alice/grammars-v4/HTMLParser.g4 /home/alice/grammars-v4/HTMLLexer.g4
    start_rule=htmlDocument
    parallel=True
    jobs=4
    subset_iterator=skip
    """

    def eval_arg(arg):
        return eval(arg) if isinstance(arg, str) else arg

    logging.getLogger('picireny').setLevel(logger.level)

    src = issue['test']
    file_name = issue.get('filename', 'test')

    parallel = eval_arg(parallel)
    jobs = 1 if not parallel else eval_arg(jobs)
    disable_cache = eval_arg(disable_cache)
    encoding = encoding or chardet.detect(src)['encoding']
    cleanup = eval_arg(cleanup)

    combine_loops = eval_arg(combine_loops)
    subset_first = eval_arg(subset_first)
    max_utilization = eval_arg(max_utilization)

    split_method = getattr(picire.config_splitters, split_method)
    subset_iterator = getattr(picire.config_iterators, subset_iterator)
    complement_iterator = getattr(picire.config_iterators, complement_iterator)

    if islands:
        with open(islands, 'rb') as f:
            islands_src = f.read()
        try:
            islands = eval(islands_src)
        except Exception as err:
            listener.warning(msg='Exception in island descriptor: ' % err)

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

    replacements = replacements or dict()

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

    call_config = dict(reduce_class=reduce_class,
                       reduce_config=reduce_config,
                       tester_class=PicireTester,
                       tester_config=tester_config,
                       input=file_name,
                       src=src,
                       encoding=encoding,
                       out=work_dir,
                       antlr=os.path.join(os.path.expanduser('~'), '.picireny', 'antlr.jar'),
                       grammar=json.loads(grammar),
                       islands=islands,
                       start_rule=start_rule,
                       replacements=replacements,
                       parallel=parallel,
                       disable_cache=disable_cache,
                       cleanup=cleanup)

    try:
        reduced_file = picireny.call(**call_config)
    except:
        return None, list(issues.values())

    with open(reduced_file, 'rb') as f:
        src = f.read()

    return src, list(issues.values())
