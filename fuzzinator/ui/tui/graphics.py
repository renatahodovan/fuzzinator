# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

"""
Graphical components of the TUI, prepared for UTF-8 and non-UTF-8 terminals
"""

from urwid import util

from fuzzinator import __version__


def fz_logo_4lines():
    padding = ''.join([' '] * (len(__version__) + 2)) + '\n'
    if util.get_encoding_mode() == 'utf8':
        return [
            ('green', u' ▄▄▄▄ ▄▄ ▄▄ ▄▄▄▄▄ ▄▄▄▄▄ ▄▄ ▄▄▄▄   ▄▄▄  █▄     ▄▄▄  ▄▄▄▄  '), ('yellow', u'[{version}]\n'.format(version=__version__)),
            ('green', u'██ ▀▀ ██ ██   ▄█▀   ▄█▀ ▄▄ ██ ██ ▀▀ ██ ██▀   ██ ██ ██ ██ '), ('yellow', padding),
            ('green', u'██▀   ██ ██ ▄█▀   ▄█▀   ██ ██ ██ ▄█▀██ ██ ██ ██ ██ ██▀█▄ '), ('yellow', padding),
            ('green', u'█▀     ▀▀▀  ▀▀▀▀▀ ▀▀▀▀▀ ▀▀ ▀▀ ▀▀ ▀▀▀▀▀  ▀▀▀▀  ▀▀▀  ▀▀ ▀█ '), ('yellow', padding),
            ('motto', u'In Bug We Trust.')]
    return [
        u' #### ## ## ##### ##### ## ####  ####  ##     ###  ####  ', ('yellow', '[{version}]\n'.format(version=__version__)),
        u'##    ## ##   ###   ###    ## ##   ### ###   ## ## ## ## ', ('yellow', padding),
        u'###   ## ## ###   ###   ## ## ## ## ## ##    ## ## ####  ', ('yellow', padding),
        u'##     ###  ##### ##### ## ## ## #####  ####  ###  ## ## ', ('yellow', padding)]


def fz_box_pattern():
    if util.get_encoding_mode() == 'utf8':
        return {
            'tlcorner': u'▗',
            'tline': u'─╍┄┉═┅╌┈━',
            'trcorner': u'▖',
            'blcorner': u'▝',
            'bline': u'┅╌┈━─╍┄┉═',
            'brcorner': u'▘',
            'lline': u'│╏┆┋║┇╎┊┃',
            'rline': u'┇╎┊┃│╏┆┋║',
        }
    return {
        'tlcorner': '/',
        'tline': '==--=-',
        'trcorner': '\\',
        'blcorner': '\\',
        'bline': '-=-==-',
        'brcorner': '/',
        'lline': "||:|.|'",
        'rline': "|.|'||:",
    }
