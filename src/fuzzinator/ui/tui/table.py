# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from functools import cmp_to_key

from urwid import (
    AttrMap, Columns, connect_signal, Divider, emit_signal, ListBox, ListWalker,
    Padding, Pile, Text, Widget, WidgetWrap
)

from .decor_widgets import PatternBox
from .graphics import fz_box_pattern


class TableRowsListWalker(ListWalker):
    def __init__(self, table, sort=None):
        self.table = table
        self.sort = sort
        self.focus = 0
        self.rows = []
        super().__init__()

    def __getitem__(self, position):
        if position < 0 or position >= len(self.rows):
            raise IndexError

        return self.rows[position]

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
        self.rows[self.focus].unhighlight()
        self.focus = position
        self.rows[self.focus].highlight()

    def set_sort_column(self, column, **kwargs):
        self._modified()


# It contains two columns: the content of the rows and the scrollbar (at least the original version).
class ScrollingListBox(WidgetWrap):
    signals = ['select', 'load_more']

    def __init__(self, body, infinite=False):
        self.infinite = infinite

        self.requery = False
        self.height = 0

        self.listbox = ListBox(body)
        self.body = self.listbox.body
        self.ends_visible = self.listbox.ends_visible

        super().__init__(self.listbox)

    def keypress(self, size, key):
        if key == 'home':
            if self.body:   # len(self.body) != 0
                self.focus_position = 0
                self._invalidate()
            return key
        if key == 'end':
            if self.body:   # len(self.body) != 0
                self.focus_position = len(self.body) - 1
                self._invalidate()
            return key
        if key in ['page down', 'down'] and self.infinite and self.focus_position == len(self.body) - 1:
            self.requery = True
            self._invalidate()
            return None
        if key == 'enter':
            if self.body:   # len(self.body) != 0
                emit_signal(self, 'select', self, self.selection)
            return None
        if key == 'left':
            return None
        return super().keypress(size, key)

    def render(self, size, focus=False):
        maxcol, maxrow = size
        if self.requery and 'bottom' in self.ends_visible((maxcol, maxrow)):
            self.requery = False
            emit_signal(self, 'load_more', len(self.body))

        self.height = maxrow
        return super().render((maxcol, maxrow), focus)

    @property
    def focus(self):
        return self.listbox.focus

    @property
    def focus_position(self):
        if self.listbox.body:   # len(self.listbox.body) != 0
            return self.listbox.focus_position
        return 0

    @focus_position.setter
    def focus_position(self, value):
        self.listbox.focus_position = value
        self.listbox._invalidate()

    @property
    def row_count(self):
        return len(self.listbox.body)

    @property
    def selection(self):
        if self.body:   # len(self.body) != 0
            return self.body[self.focus_position]
        return None


class TableColumn:
    align = 'left'
    wrap = 'space'
    padding = None

    def __init__(self, name, label=None, width=('weight', 1),
                 format_fn=None,
                 sort_key=None, sort_fn=None, sort_reverse=False):

        self.name = name
        self.label = label if label else name
        self.format_fn = format_fn
        self.sort_key = sort_key
        self.sort_fn = sort_fn
        self.sort_reverse = sort_reverse
        self.sizing, self.width = width

    def _format(self, v):
        if isinstance(v, str):
            return Text(v, align=self.align, wrap=self.wrap)
        # First, call the format function for the column, if there is one
        if self.format_fn:
            try:
                v = self.format_fn(v)
            except TypeError:
                return Text('', align=self.align, wrap=self.wrap)
        return self.format(v)

    def format(self, v):
        # Do our best to make the value into something presentable
        if v is None:
            v = ''
        elif isinstance(v, int):
            v = str(v)
        elif isinstance(v, float):
            v = f'{v:.03f}'

        # If v doesn't match any of the previous options than it might be a Widget.
        if not isinstance(v, Widget):
            return Text(v, align=self.align, wrap=self.wrap)
        return v


class HeaderColumns(Columns):
    def __init__(self, contents):
        self.selected_column = None
        super().__init__(contents)

    def __setitem__(self, i, v):
        self.contents[i * 2] = (v, self.contents[i * 2][1])


class BodyColumns(Columns):
    def __init__(self, contents, header=None):
        self.header = header
        super().__init__(contents)

    @property
    def selected_column(self):
        return self.header.selected_column

    @selected_column.setter
    def selected_column(self, value):
        self.header.selected_column = value


class TableCell(WidgetWrap):
    signals = ['click', 'select']

    def __init__(self, table, column, row, value):
        self.table = table
        self.column = column
        self.row = row
        self.value = value
        self.contents = self.column._format(self.value)

        padding = self.column.padding or self.table.padding
        self.padding = Padding(self.contents, left=padding, right=padding)
        self.attr = AttrMap(self.padding, attr_map=row.attr_map, focus_map=row.focus_map)
        super().__init__(self.attr)

    def selectable(self):
        return isinstance(self.row, TableBodyRow)

    def highlight(self):
        self.attr.set_attr_map(self.row.focus_map)

    def unhighlight(self):
        self.attr.set_attr_map(self.row.attr_map)

    def set_attr_map(self, attr_map):
        self.attr.set_attr_map(attr_map)

    def set_focus_map(self, focus_map):
        self.attr.set_focus_map(focus_map)

    def keypress(self, size, key):
        if key == 'enter':
            emit_signal(self, 'select')
        return key

    # Override the mouse_event method (param list is fixed).
    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            emit_signal(self, 'click')


class TableRow(WidgetWrap):
    attr_map = {}
    focus_map = {}

    border_char = ' '
    column_class = Columns  # To be redefined by subclasses.
    decorate = True
    _selectable = True

    def __init__(self, table, data,
                 header=None,
                 cell_click=None, cell_select=None,
                 attr_map=None, focus_map=None):

        self.table = table

        if isinstance(data, (list, tuple)):
            self.data = dict(zip([c.name for c in self.table.columns], data))
        elif isinstance(data, dict):
            self.data = data

        self.header = header
        self.cell_click = cell_click
        self.cell_select = cell_select
        self.contents = []

        if self.decorate:
            if attr_map:
                self.attr_map = attr_map
            elif table.attr_map:
                self.attr_map.update(table.attr_map)
            if focus_map:
                self.focus_map = focus_map
            elif table.focus_map:
                self.focus_map.update(table.focus_map)

        # Create tuples to describe the sizing of the column.
        for i, col in enumerate(self.table.columns):
            lst = []
            if col.sizing == 'weight':
                lst.extend([col.sizing, col.width])
            else:
                lst.append(col.width)

            cell = TableCell(self.table, col, self, self.data.get(col.name, None))
            if self.cell_click:
                connect_signal(cell, 'click', self.cell_click, i * 2)
            if self.cell_select:
                connect_signal(cell, 'select', self.cell_select, i * 2)

            lst.append(cell)
            self.contents.append(tuple(lst))

        if isinstance(table.border, tuple):
            border_width = table.border[0]
        elif isinstance(table.border, int):
            border_width = table.border
        else:
            raise ValueError(f'Invalid border specification: {table.border}')

        self.row = self.column_class(self.contents)
        if self.header:
            self.row.header = self.header
        self.row.selected_column = None

        # content sep content sep ...
        self.row.contents = sum(([x, (Divider(self.border_char), ('given', border_width, False))] for x in self.row.contents), [])
        self.attr = AttrMap(self.row, attr_map=self.attr_map, focus_map=self.focus_map)

        super().__init__(self.attr)

    def __len__(self):
        return len(self.contents)

    def __getitem__(self, key):
        return self.data.get(key, None)

    def __iter__(self):
        return iter(self.data)

    def __setitem__(self, i, v):
        self.row.contents[i * 2] = (v, self.row.options(self.table.columns[i].sizing,
                                                        self.table.columns[i].width))

    @property
    def focus(self):
        return self.row.focus

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

    def highlight(self):
        for x in self.contents:
            x[-1].highlight()

    def unhighlight(self):
        for x in self.contents:
            x[-1].unhighlight()


class TableBodyRow(TableRow):
    column_class = BodyColumns

    attr_map = {None: 'default'}
    focus_map = {None: 'selected'}


class TableHeaderRow(TableRow):
    signals = ['column_click']

    column_class = HeaderColumns
    decorate = False

    def __init__(self, table, *args, **kwargs):
        self.row = None

        self.attr_map = {None: 'table_head'}
        self.focus_map = {None: 'table_head'}

        self.table = table
        self.contents = [str(x.label) for x in self.table.columns]

        super().__init__(
            self.table,
            self.contents,
            cell_click=self.header_clicked,
            cell_select=self.header_clicked,
            *args, **kwargs)

    @property
    def selected_column(self):
        return self.row.selected_column

    @selected_column.setter
    def selected_column(self, value):
        self.row.selected_column = value

    def header_clicked(self, index):
        emit_signal(self, 'column_click', index)

    def highlight_column(self, index):
        if self.selected_column is not None:
            self.row[self.selected_column].unhighlight()
        self.row[index].highlight()
        self.selected_column = index


class Table(WidgetWrap):
    signals = ['select', 'refresh', 'focus', 'delete']

    attr_map = {}
    focus_map = {}
    row_dict = {}

    title = ''
    columns = []
    query_data = []
    key_columns = None
    sort_field = None
    _selectable = True

    def __init__(self, initial_sort=None, limit=None):
        self.border = (1, ' ', 'table_border')
        self.padding = 1
        self.initial_sort = initial_sort
        self.limit = limit

        if not self.key_columns:
            self.key_columns = self.columns

        self.walker = TableRowsListWalker(self, sort=self.initial_sort)
        self.listbox = ScrollingListBox(self.walker, infinite=self.limit)

        self.selected_column = None
        self.sort_reverse = False

        # Forward 'select' signal to the caller of table.
        connect_signal(self.listbox, 'select',
                       lambda source, selection: emit_signal(self, 'select', self, selection))

        if self.limit:
            connect_signal(self.listbox, 'load_more', self.load_more)
            self.offset = 0

        self.header = TableHeaderRow(self)
        self.pile = Pile([('pack', self.header),
                          ('weight', 1, self.listbox)])

        self.pattern_box = PatternBox(self.pile, title=['[', ('border_title', f' {self.title} (0) '), ']'], **fz_box_pattern())
        self.attr = AttrMap(self.pattern_box, attr_map=self.attr_map)
        super().__init__(self.attr)

        connect_signal(self.header, 'column_click', lambda index: self.sort_by_column(index, toggle=True))

        if self.initial_sort and self.initial_sort in [c.name for c in self.columns]:
            self.sort_by_column(self.initial_sort, toggle=False)
        else:
            self.requery(self.query_data)

    def update_header(self):
        self.pattern_box.set_title(['[', ('border_title', f' {self.title} ({len(self.walker)}) '), ']'])

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
        return self.listbox.listbox.contents

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
        if self.body:   # len(self.body) != 0
            return self.body[self.focus_position]
        return None

    def add_row(self, data, position=None, attr_map=None, focus_map=None):
        row = TableBodyRow(self, data, header=self.header.row, attr_map=attr_map, focus_map=focus_map)
        if '_id' in data:
            self.row_dict[data['_id']] = row
        if not position:
            self.walker.add(row)
        else:
            self.walker.insert(position, row)
        self.update_header()

    def update_row_style(self, row_id, attr_map, focus_map):
        if not self.attr_map:
            self.row_dict[row_id].attr_map = attr_map
        else:
            self.row_dict[row_id].attr_map = self.attr_map
            self.row_dict[row_id].attr_map.update(attr_map)

        if not self.focus_map:
            self.row_dict[row_id].focus_map = focus_map
        else:
            self.row_dict[row_id].focus_map = self.focus_map
            self.row_dict[row_id].focus_map.update(self.focus_map)

        self.row_dict[row_id]._wrapped_widget.set_attr_map(self.row_dict[row_id].attr_map)
        self.row_dict[row_id]._wrapped_widget.set_focus_map(self.row_dict[row_id].focus_map)

    def clear(self):
        self.listbox.body.clear()

    def highlight_column(self, index):
        self.header.highlight_column(index)

    def load_more(self, offset):
        self.requery(offset)
        self._invalidate()
        self.listbox._invalidate()

    # These two methods will might be overridden in subclasses.
    def query(self, data, sort=(None, None), offset=None):
        sort_field, sort_reverse = sort
        if sort_field:
            def sort_natural_none_last(a, b):
                if a is None:
                    return 1
                if b is None:
                    return -1
                return (a > b) - (a < b)

            def sort_reverse_none_last(a, b):
                if a is None:
                    return 1
                if b is None:
                    return -1
                return (a > b) - (a < b)

            if not sort_reverse:
                sort_fn = cmp_to_key(sort_natural_none_last)
            else:
                sort_fn = cmp_to_key(sort_reverse_none_last)

            data.sort(key=lambda x: sort_fn(x[sort_field]))
        if offset is not None:
            r = data[offset:offset + self.limit]
        else:
            r = data

        for d in r:
            yield d

    def requery(self, data, offset=0):
        kwargs = {'sort': (self.sort_field, self.sort_reverse)}
        if self.limit:
            kwargs['offset'] = offset

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
            raise ValueError(f'invalid column index: {index}')

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
