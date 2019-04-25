/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

(function ($) {
  'use strict';

  var BootstrapTable = $.fn.bootstrapTable.Constructor;
  var _initToolbar = BootstrapTable.prototype.initToolbar;

  // Extend initToolbar to override the icon of refresh to a material icon-
  // based option and to add a dropdown button to the toolbar which are able
  // to trigger sorting on the columns.
  BootstrapTable.prototype.initToolbar = function () {
    _initToolbar.apply(this, Array.prototype.slice.apply(arguments));
    var that = this;

    if (this.options.showRefresh) {
      $("[aria-label='refresh']").removeClass('btn-sm');
      var refresh = $("[aria-label='refresh']>i");
      refresh.attr('class', 'material-icons align-text-top');
      refresh.html('cached');
    }

    // Add drop-down sort button to the toolbar.
    var btnGroup = that.$toolbar.find('>.btn-group');
    var button = btnGroup.find('button[name=sort]');
    if (!button.length) {
      var btn = `<button class="btn btn-${that.options.buttonsClass} aria-label="sort type" title="Sort" data-toggle="dropdown" type="button">` +
                `  <i class='material-icons'>unfold_more</i>` +
                `</button>`;

      var dropBtnGroup = $(`<div class='sort btn-group'>` +
                           `  ${btn}` +
                           `  <div class='dropdown-menu'></div>` +
                           `</div>`).appendTo(btnGroup);

      for (var col of that.options.columns[0]) {
        var htmlItem = `<button class='dropdown-item'>` +
                       `  <i class='material-icons align-text-top'></i>` +
                       `  ${col.field}` +
                       `</button>`;

        $(htmlItem).appendTo($(dropBtnGroup).find('.dropdown-menu')).click(col, function (event) {
          var sorter = that.$el.find(`[data-field=${event.data.field}]`).find('.sortable');
          $(sorter).trigger('click', { 'type': 'keypress' });
          // Reset all class set to the items.
          $.each($(event.target).closest('.dropdown-menu').children(), function (i, item) {
            $(item).attr('class', 'dropdown-item');
          });
          $(event.target).addClass($(sorter).hasClass('desc') ? 'desc' : 'asc');
        });
      }
    }
  };
})(jQuery);
