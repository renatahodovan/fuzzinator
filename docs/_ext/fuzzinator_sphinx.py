# Copyright (c) 2020-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from docutils import nodes
from docutils.transforms import Transform
from sphinx import addnodes


# Useful for README.rst that is also included by docs/introduction.rst but
# is linking to docs/tutorial.rst. (From within docs/introduction.rst, the
# proper way of linking would be :doc:`tutorial`, but that cannot be used
# in the standalone README.rst.)
class FixOuterDocLinks(Transform):
    default_priority = 900
    def apply(self):
        # reference nodes represent embedded uris
        for refnode in self.document.traverse(nodes.reference):
            refuri = refnode['refuri']
            # only interested in local references to files docs/FILENAME.rst
            if not refuri.startswith('docs/') or not refuri.endswith('.rst'):
                continue

            # replace them with :doc:`FILENAME` to turn them into
            # sphinx-specific direct document links
            _ = ''
            xrefnode = addnodes.pending_xref(_, nodes.inline(_, *tuple(refnode.children), classes=['xref', 'std', 'std-doc']),
                                             refdoc='.'.join(self.document['source'].rpartition('docs/')[2].rsplit('.', maxsplit=1)[:-1]),
                                             refdomain='std',
                                             refexplicit=False,
                                             reftarget=refuri[len('docs/'):-len('.rst')],
                                             reftype='doc',
                                             refwarn=True)
            refnode.replace_self(xrefnode)


def setup(app):
    app.add_transform(FixOuterDocLinks)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
