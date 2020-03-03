# Copyright (c) 2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from docutils import nodes
from docutils.transforms import Transform
from sphinx import addnodes


# Add section header above all top-level classes and functions in
# autodoc-generated documentation to make them appear in TOC.
class AddApiToToc(Transform):
    default_priority = 50
    def apply(self):
        # desc nodes of sphinx represent domain-specific entities,
        # their first children, desc_signature nodes, are their "heads"
        for signode in self.document.traverse(addnodes.desc_signature):
            descnode = signode.parent
            domain = descnode['domain']
            objtype = descnode['objtype']
            # only interested in py:class and py:function entities
            if domain != 'py' or objtype not in ['class', 'function']:
                continue

            # wrap the desc node in a section node, which will appear in TOC
            name = signode['fullname']
            secname = objtype + ' ' + name
            _ = ''
            secnode = nodes.section(_, nodes.title(_, objtype + ' ', nodes.literal(_, name)),
                                    ids=[nodes.make_id(secname)],
                                    names=[nodes.fully_normalize_name(secname)])
            descnode.replace_self(secnode)
            secnode += descnode


# Useful for README.rst that is also included by docs/introduction.rst but
# is linking to docs/tutorial.rst. (From within docs/introduction.rst, the
# proper way of linking would be :docs:`tutorial`, but that cannot be used
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

            # replace them with :doc:`/FILENAME` to turn them into
            # sphinx-specific direct document links
            _ = ''
            xrefnode = addnodes.pending_xref(_, nodes.inline(_, *tuple(refnode.children), classes=['xref', 'doc']),
                                             refdoc='.'.join(self.document['source'].rpartition('docs/')[2].rsplit('.', maxsplit=1)[:-1]),
                                             refdomain='',
                                             refexplicit=True,
                                             reftarget=refuri[len('docs'):-len('.rst')],
                                             reftype='doc',
                                             refwarn=True)
            refnode.replace_self(xrefnode)


def setup(app):
    app.add_transform(AddApiToToc)
    app.add_transform(FixOuterDocLinks)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
