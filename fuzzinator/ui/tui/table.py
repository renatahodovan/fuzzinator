# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from collections.abc import MutableMapping
from functools import cmp_to_key
from urwid import *

from .graphics import fz_box_pattern
from .decor_widgets import PatternBox


def cmp(a, b):
    return (a > b) - (a < b)


def sort_natural_none_last(a, b):
    if a is None:
        return 1
    if b is None:
        return -1
    return cmp(a, b)


def sort_reverse_none_last(a, b):
    if a is None:
        return 1
    if b is None:
        return -1
    return cmp(b, a)


sort_key_natural_none_last = cmp_to_key(sort_natural_none_last)
sort_key_reverse_none_last = cmp_to_key(sort_reverse_none_last)


class TableRowsListWalker(listbox.ListWalker):
    def __init__(self, table, sort=None):
        self.focus = 0
        self.rows = list()
        self.sort = sort
        self.table = table
        super(TableRowsListWalker, self).__init__()

    def __getitem__(self, position):
        if position < 0 or position >= len(self.rows):
            raise IndexError

        try:
            row = self.rows[position]
        except:
            raise
        return row

    def __delitem__(self, index):
        if -1 < index < len(self.rows):
            del self.rows[index]
            self._modified()

    def __len__(self):
        return len(self.rows)

    def add(self, item):
        self.rows.append(item)
        self._modified()

    def insert(self, *args):
        self.rows.insert(*args)
        self._modified()

    def replace(self, data, idx):
        self.rows[idx] = data

    def clear(self):
        self.focus = 0
        del self.rows[:]

    def remove(self, value):
        self.rows.remove(value)

    def next_position(self, position):
        index = position + 1
        if position >= len(self.rows):
            raise IndexError
        return index

    def prev_position(self, position):
        index = position - 1
        if position < 0:
            raise IndexError
        return index

    def set_focus(self, position):
        self.focus = position

    def set_sort_column(self, column, **kwargs):
        self._modified()


# It contains two columns: the content of the rows and the scrollbar (at least the original version).
class ScrollingListBox(WidgetWrap):
    signals = ["select", "load_more"]

    def __init__(self, body, infinite=False, row_count_fn=None):
        self.infinite = infinite
        self.row_count_fn = row_count_fn

        self.requery = False
        self.height = 0

        self.listbox = ListBox(body)
        self.columns = Columns([('weight', 1, AttrMap(self.listbox, 'table_row'))])

        self.body = self.listbox.body
        self.contents = self.columns.contents
        self.ends_visible = self.listbox.ends_visible

        super(ScrollingListBox, self).__init__(self.columns)

    def keypress(self, size, key):
        if len(self.body):
            if key == 'home':
                self.focus_position = 0
                self.listbox._invalidate()
                return key
            elif key == 'end':
                self.focus_position = len(self.body) - 1
                self._invalidate()
                return key
            elif (self.infinite
                  and key in ['page down', "down"]
                  and len(self.body)
                  and self.focus_position == len(self.body) - 1):
                self.requery = True
                self._invalidate()
            elif key == "enter":
                emit_signal(self, "select", self, self.selection)
            else:
                return super(ScrollingListBox, self).keypress(size, key)
        return super(ScrollingListBox, self).keypress(size, key)

    def render(self, size, focus=False):
        maxcol, maxrow = size
        if self.requery and "bottom" in self.ends_visible((maxcol, maxrow)):
            self.requery = False
            emit_signal(self, "load_more", len(self.body))

        self.height = maxrow
        return super(ScrollingListBox, self).render((maxcol, maxrow), focus)

    @property
    def focus(self):
        return self.listbox.focus

    @property
    def focus_position(self):
        if len(self.listbox.body) > 0:
            return self.listbox.focus_position
        return 0

    @focus_position.setter
    def focus_position(self, value):
        self.listbox.focus_position = value
        self.listbox._invalidate()

    @property
    def row_count(self):
        if self.row_count_fn:
            return self.row_count_fn()
        return len(self.listbox.body)

    @property
    def selection(self):
        if len(self.body):
            return self.body[self.focus_position]


class TableColumn(object):
    def __init__(self, name, label=None, width=('weight', 1),
                 align="left", wrap="space", padding=None,
                 format_fn=None, attr=None,
                 sort_key=None, sort_fn=None, sort_reverse=False,
                 attr_map=None, focus_map=None):

        self.name = name
        self.label = label if label else name
        self.align = align
        self.wrap = wrap
        self.padding = padding
        self.format_fn = format_fn
        self.attr = attr
        self.sort_key = sort_key
        self.sort_fn = sort_fn
        self.sort_reverse = sort_reverse
        self.attr_map = attr_map if attr_map else {}
        self.focus_map = focus_map if focus_map else {}

        if isinstance(width, tuple):
            if width[0] != "weight":
                raise Exception("Column width %s not supported" % self.width[0])
            self.sizing, self.width = width
        else:
            self.width = width
            self.sizing = "given"

    def _format(self, v):
        if isinstance(v, str):
            return Text(v, align=self.align, wrap=self.wrap)
        # First, call the format function for the column, if there is one
        if self.format_fn:
            try:
                v = self.format_fn(v)
            except TypeError:
                return Text("", align=self.align, wrap=self.wrap)
            except:
                raise
        return self.format(v)

    def format(self, v):
        # Do our best to make the value into something presentable
        if v is None:
            v = ""
        elif isinstance(v, int):
            v = "%d" % v
        elif isinstance(v, float):
            v = "%.03f" % v

        # If v doesn't match any of the previous options than it might be a Widget.
        if not isinstance(v, Widget):
            return Text(v, align=self.align, wrap=self.wrap)
        return v


class TableCell(WidgetWrap):
    signals = ["click", "select"]

    def __init__(self, table, column, row, value, attr_map=None, focus_map=None):

        self.table = table
        self.column = column
        self.row = row
        self.value = value
        self.contents = self.column._format(self.value)

        self.attr_map = {}
        self.focus_map = {}

        if column.attr_map:
            self.attr_map.update(column.attr_map)
        if row.attr_map:
            self.attr_map.update(row.attr_map)
        if column.attr and isinstance(row.data, MutableMapping):
            a = row.data.get(column.attr, {})
            if isinstance(a, str):
                a = {None: a}
            self.attr_map.update(a)

        if attr_map:
            self.attr_map.update(attr_map)

        if column.focus_map:
            self.focus_map.update(column.focus_map)
        if row.focus_map:
            self.focus_map.update(row.focus_map)
        if focus_map:
            self.focus_map.update(focus_map)

        padding = self.column.padding or self.table.padding
        self.padding = Padding(self.contents, left=padding, right=padding)

        self.attr = AttrMap(self.padding,
                            attr_map=self.attr_map,
                            focus_map=self.focus_map)

        self.orig_attr_map = self.attr.get_attr_map()
        self.orig_focus_map = self.attr.get_focus_map()

        self.highlight_attr_map = self.attr.get_attr_map()
        for k in self.highlight_attr_map.keys():
            self.highlight_attr_map[k] += " column_focused"

        self.highlight_focus_map = self.attr.get_attr_map()
        for k in self.highlight_focus_map.keys():
            self.highlight_focus_map[k] += " column_focused focused"

        super(TableCell, self).__init__(self.attr)

    def selectable(self):
        return isinstance(self.value, str)

    def highlight(self):
        self.attr.set_attr_map(self.highlight_attr_map)
        self.attr.set_focus_map(self.highlight_focus_map)

    def unhighlight(self):
        self.attr.set_attr_map(self.orig_attr_map)
        self.attr.set_focus_map(self.orig_focus_map)

    def set_attr_map(self, attr_map):
        self.attr.set_attr_map(attr_map)

    def set_focus_map(self, focus_map):
        self.attr.set_focus_map(focus_map)

    def keypress(self, _, key):
        if key != "enter":
            return key
        emit_signal(self, "select")

    # Override the mouse_event method (param list is fixed).
    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            emit_signal(self, "click")


class HeaderColumns(Columns):
    def __init__(self, contents):
        self.selected_column = None
        super(HeaderColumns, self).__init__(contents)

    def __setitem__(self, i, v):
        self.contents[i * 2] = (v, self.contents[i * 2][1])


class BodyColumns(Columns):
    def __init__(self, contents, header=None):
        self.header = header
        super(BodyColumns, self).__init__(contents)

    @property
    def selected_column(self):
        return self.header.selected_column

    @selected_column.setter
    def selected_column(self, value):
        self.header.selected_column = value


class TableRow(WidgetWrap):
    attr_map = {}
    border_char = ' '
    focus_map = {}
    decorate = True
    _selectable = True

    def __init__(self, table, data,
                 header=None,
                 cell_click=None, cell_select=None,
                 border_attr_map=None, border_focus_map=None,
                 attr_map=None, focus_map=None):

        self.table = table
        if isinstance(data, (list, tuple)):
            self.data = dict(zip([c.name for c in self.table.columns], data))
        elif isinstance(data, MutableMapping):
            self.data = data
        else:
            self.data = {}

        self.header = header
        self.cell_click = cell_click
        self.cell_select = cell_select
        self.contents = []
        self._values = dict()

        if self.decorate:
            if attr_map:
                self.attr_map = attr_map
            elif table.attr_map:
                self.attr_map.update(table.attr_map)
            if focus_map:
                self.focus_map = focus_map
            elif table.focus_map:
                self.focus_map.update(table.focus_map)

        if border_attr_map:
            self.border_attr_map = border_attr_map
        else:
            self.border_attr_map = self.attr_map

        if border_focus_map:
            self.border_focus_map = border_focus_map
        else:
            self.border_focus_map = self.focus_map

        # Create tuples to describe the sizing of the column.
        for i, col in enumerate(self.table.columns):
            l = list()
            if col.sizing == "weight":
                l += [col.sizing, col.width]
            else:
                l.append(col.width)

            if hasattr(self.data, col.name):
                val = getattr(self.data, col.name, None)
            else:
                val = self.data.get(col.name, None)

            cell = TableCell(self.table, col, self, val)
            if self.cell_click:
                connect_signal(cell, 'click', self.cell_click, i * 2)
            if self.cell_select:
                connect_signal(cell, 'select', self.cell_select, i * 2)

            l.append(cell)
            self.contents.append(tuple(l))

        if isinstance(table.border, tuple):
            if len(table.border) == 3:
                border_width, border_char, border_attr = table.border
            elif len(table.border) == 2:
                border_width, border_char = table.border
            else:
                border_width = table.border
        elif isinstance(table.border, int):
            border_width = table.border
        else:
            raise Exception("Invalid border specification: %s" % table.border)

        if self.header:
            self.row = self.column_class(self.contents, header=self.header)
        else:
            self.row = self.column_class(self.contents)
        self.row.selected_column = None

        # content sep content sep ...
        self.row.contents = sum([[x, (Divider(self.border_char), ('given', border_width, False))] for x in self.row.contents], [])
        self.attr = AttrMap(self.row,
                            attr_map=self.attr_map,
                            focus_map=self.focus_map)

        super(TableRow, self).__init__(self.attr)

    def __len__(self):
        return len(self.contents)

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __hash__(self):
        return hash(self._key())

    def __iter__(self):
        return iter(self.data)

    def __setitem__(self, i, v):
        self.row.contents[i * 2] = (v, self.row.options(self.table.columns[i].sizing,
                                                        self.table.columns[i].width))

    @property
    def focus(self):
        return self.row.focus

    @property
    def focus_position(self):
        return self.row.focus_position

    @focus_position.setter
    def focus_position(self, value):
        self.row.focus_position = value

    @property
    def selected_column(self):
        return self.row.selected_column

    @selected_column.setter
    def selected_column(self, value):
        self.row.selected_column = value

    def set_attr_map(self, attr_map):
        self.attr.set_attr_map(attr_map)

    def set_focus_map(self, focus_map):
        self.attr.set_focus_map(focus_map)

    def get(self, key, default):
        if key in self:
            return self[key]
        return default

    def _key(self):
        return frozenset([self.get(c, None) for c in self.table.key_columns])

    def cell(self, i):
        return self.row[i * 2]

    def highlight_column(self, index):
        if self.selected_column is not None:
            self.row[self.selected_column].unhighlight()
        self.row[index].highlight()
        self.selected_column = index


class TableBodyRow(TableRow):
    column_class = BodyColumns

    attr_map = {None: "table_row"}
    focus_map = {
        None: "table_row focused",
        "table_row": "table_row focused"}


class TableHeaderRow(TableRow):
    signals = ['column_click']

    column_class = HeaderColumns
    decorate = False

    border_attr_map = {None: "table_border"}
    border_focus_map = {None: "table_border focused"}

    def __init__(self, table,  *args, **kwargs):
        self.row = None

        self.attr_map = {None: "table_header"}
        self.focus_map = {None: "table_header focused"}

        self.table = table
        self.contents = [str(x.label) for x in self.table.columns]

        super(TableHeaderRow, self).__init__(
            self.table,
            self.contents,
            border_attr_map=self.border_attr_map,
            border_focus_map=self.border_focus_map,
            cell_click=self.header_clicked,
            cell_select=self.header_clicked,
            *args, **kwargs)

    def header_clicked(self, index):
        emit_signal(self, "column_click", index)


class Table(WidgetWrap):
    signals = ["select", "refresh", "focus"]

    attr_map = {}
    columns = []
    focus_map = {}
    key_columns = None
    sort_field = None
    _selectable = True

    def __init__(self, border=None, padding=None,
                 initial_sort=None,
                 limit=None):

        self.focus_map = dict()
        self.border = border or (1, ' ', 'table_border')
        self.padding = padding or 1
        self.initial_sort = initial_sort
        self.limit = limit

        if not self.key_columns:
            self.key_columns = self.columns

        self.walker = TableRowsListWalker(self, sort=self.initial_sort)
        self.listbox = ScrollingListBox(self.walker, infinite=self.limit, row_count_fn=None)

        self.selected_column = None
        self.sort_reverse = False

        # Forward 'select' signal to the caller of table.
        connect_signal(
            self.listbox, "select",
            lambda source, selection: emit_signal(self, "select", self, selection))

        if self.limit:
            connect_signal(self.listbox, "load_more", self.load_more)
            self.offset = 0

        self.header = TableHeaderRow(self)
        self.pile = Pile([('pack', self.header),
                          ('weight', 1, self.listbox)])

        self.pattern_box = PatternBox(self.pile, title=['[', ('yellow', ' {title} (0) '.format(title=self.title)), ']'], **fz_box_pattern())
        self.attr = AttrMap(self.pattern_box, attr_map=self.attr_map)
        super(Table, self).__init__(self.attr)

        connect_signal(self.header, "column_click", lambda index: self.sort_by_column(index, toggle=True))

        if self.initial_sort and self.initial_sort in [c.name for c in self.columns]:
            self.sort_by_column(self.initial_sort, toggle=False)
        else:
            self.requery(self.query_data)

    def update_header(self):
        self.pattern_box.set_title(['[', ('yellow', ' {title} ({cnt}) '.format(title=self.title, cnt=len(self.walker))), ']'])

    def __contains__(self, value):
        return any([all([value.get(c, None) == x.data.get(c, None) for c in self.key_columns]) for x in self.body])

    def __delitem__(self, i):
        del self.body[i]

    def __iter__(self):
        return iter(self.body)

    def __len__(self):
        return len(self.body)

    def __getitem__(self, i):
        return self.body[i]

    def __setitem__(self, i, v):
        self.body[i] = v

    def insert(self, i, v):
        self.body.insert(i, v)

    @property
    def body(self):
        return self.listbox.body

    @property
    def contents(self):
        return self.listbox.contents

    @property
    def focus(self):
        return self.listbox.focus

    @property
    def height(self):
        return self.body.row_count + 1

    @property
    def focus_position(self):
        return self.listbox.focus_position

    @focus_position.setter
    def focus_position(self, value):
        self.listbox.focus_position = value

    @property
    def selection(self):
        if len(self.body):
            return self.body[self.focus_position]

    def add_row(self, data, position=None, attr_map=None, focus_map=None):
        row = TableBodyRow(self, data, header=self.header.row, attr_map=attr_map, focus_map=focus_map)
        if not position:
            self.walker.add(row)
        else:
            self.walker.insert(position, row)
        self.update_header()

    def update_ui(self):
        self._invalidate()
        self.listbox._invalidate()
        emit_signal(self, "refresh", self)

    def clear(self):
        self.listbox.body.clear()

    def highlight_column(self, index):
        self.header.highlight_column(index)
        for row in self.listbox.body:
            row.highlight_column(index)

    def load_more(self, offset):
        self.requery(offset)
        self._invalidate()
        self.listbox._invalidate()

    # These two methods will might be overridden in subclasses.
    def query(self, data, sort=(None, None), offset=None):
        sort_field, sort_reverse = sort
        if sort_field:
            kwargs = {}
            if not sort_reverse:
                sort_fn = sort_key_natural_none_last
            else:
                sort_fn = sort_key_reverse_none_last
            kwargs['key'] = lambda x: sort_fn(x[sort_field])
            data.sort(**kwargs)
        if offset is not None:
            start = offset
            end = offset + self.limit
            r = data[start:end]
        else:
            r = data

        for d in r:
            yield d

    def requery(self, data, offset=0):
        kwargs = {"sort": (self.sort_field, self.sort_reverse)}
        if self.limit:
            kwargs["offset"] = offset

        if not offset:
            self.clear()

        if self.selected_column is not None:
            self.highlight_column(self.selected_column)

        for r in self.query(data, **kwargs):
            if isinstance(r, (tuple, list)):
                r = dict(zip([c.name for c in self.columns], r))
            self.add_row(r)
        self.update_header()

    def sort_by_column(self, index=None, reverse=None, toggle=False):
        if index is None:
            if self.sort_field is None:
                return
            index = self.sort_field

        if isinstance(index, str):
            sort_field = index
            for i, col in enumerate(self.columns):
                if col.name == sort_field:
                    index = i * 2
                    break
        else:
            sort_field = self.columns[index // 2].name

        if not isinstance(index, int):
            raise Exception("invalid column index: %s" % index)

        if reverse is not None:
            self.sort_reverse = reverse ^ self.columns[index // 2].sort_reverse
        elif not toggle or sort_field != self.sort_field:
            self.sort_reverse = self.columns[index // 2].sort_reverse
        else:
            self.sort_reverse = not self.sort_reverse

        self.sort_field = sort_field
        self.selected_column = index
        self.walker.set_sort_column(self.columns[index // 2], reverse=self.sort_reverse)
        self.requery(self.query_data)
