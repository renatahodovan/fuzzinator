/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019-2021 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

(function ($) {
  'use strict';

  const utils = $.fn.bootstrapTable.utils;

  $.BootstrapTable = class extends $.BootstrapTable {
    // Extend init method with initiating a member to keep track of the opened rows.
    init(...args) {
      $.extend(this.options, {
        openRows: [],

        onExpandRow: function (index) {
          if (!this.openRows.includes(index)) {
            this.openRows.push(index);
          }
          return false;
        },

        onCollapseRow: function (index) {
          var inOpenedRowsIndex = this.openRows.indexOf(index);
          if (inOpenedRowsIndex !== -1) {
            this.openRows.splice(inOpenedRowsIndex, 1);
          }
          return false;
        },

        onPageChange: function () {
          this.openRows = [];
          return false;
        }
      });
      super.init(...args);
    }

    // Extend initBody to automatically open the detail view of a rows if it was saved as open.
    initBody (...args) {
      super.initBody(...args);
      var that = this;
      var data = this.getData();

      for (var openIndex of this.options.openRows) {
        var $this = this.$body.find(`> tr[data-index=${openIndex}] > td > .detail-icon`);
        var $tr = $this.parent().parent();
        var index = $tr.data('index');
        var row = data[index];

        $this.find('i').attr('class', `${that.options.iconsPrefix} ${that.options.icons.detailClose}`);
        var colSpan = $tr.find('td').length;
        $tr.after(`<tr class="detail-view"><td colspan="${colSpan}"></td></tr>`);
        var $element = $tr.next().find('td');
        var content = utils.calculateObjectValue(that.options, that.options.detailFormatter, [index, row, $element], '');
        if ($element.length === 1) {
          $element.append(content);
        }
      }
    }
  }
})(jQuery);
