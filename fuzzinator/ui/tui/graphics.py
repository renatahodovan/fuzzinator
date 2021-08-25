# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

"""
Graphical components of the TUI, prepared for UTF-8 and non-UTF-8 terminals
"""

from urwid import util

from ...pkgdata import __version__


def fz_logo_4lines():
    version_parts = __version__.split('+')
    if len(version_parts) > 1:
        version_parts[1:] = [version_parts[1].split('.')[0]]
    short_version = '+'.join(version_parts)
    padding = ''.join([' '] * (len(short_version) + 2)) + '\n'
    if util.get_encoding_mode() == 'utf8':
        return [
            ('logo', ' ▄▄▄▄ ▄▄ ▄▄ ▄▄▄▄▄ ▄▄▄▄▄ ▄▄ ▄▄▄▄   ▄▄▄  █▄     ▄▄▄  ▄▄▄▄  '), ('logo_secondary', '[{version}]\n'.format(version=short_version)),
            ('logo', '██ ▀▀ ██ ██   ▄█▀   ▄█▀ ▄▄ ██ ██ ▀▀ ██ ██▀   ██ ██ ██ ██ '), ('logo_secondary', padding),
            ('logo', '██▀   ██ ██ ▄█▀   ▄█▀   ██ ██ ██ ▄█▀██ ██ ██ ██ ██ ██▀█▄ '), ('logo_secondary', padding),
            ('logo', '█▀     ▀▀▀  ▀▀▀▀▀ ▀▀▀▀▀ ▀▀ ▀▀ ▀▀ ▀▀▀▀▀  ▀▀▀▀  ▀▀▀  ▀▀ ▀█ '), ('logo_secondary', padding),
            ('logo_secondary', 'In Bug We Trust.')]
    return [
        ('logo', ' #### ## ## ##### ##### ## ####  ####  ##     ###  ####  '), ('logo_secondary', '[{version}]\n'.format(version=short_version)),
        ('logo', '##    ## ##   ###   ###    ## ##   ### ###   ## ## ## ## '), ('logo_secondary', padding),
        ('logo', '###   ## ## ###   ###   ## ## ## ## ## ##    ## ## ####  '), ('logo_secondary', padding),
        ('logo', '##     ###  ##### ##### ## ## ## #####  ####  ###  ## ## '), ('logo_secondary', padding),
        ('logo_secondary', 'In Bug We Trust.')]


def fz_box_pattern():
    if util.get_encoding_mode() == 'utf8':
        return {
            'tlcorner': '▗',
            'tline': '─╍┄┉═┅╌┈━',
            'trcorner': '▖',
            'blcorner': '▝',
            'bline': '┅╌┈━─╍┄┉═',
            'brcorner': '▘',
            'lline': '│╏┆┋║┇╎┊┃',
            'rline': '┇╎┊┃│╏┆┋║',
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
