/*
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
  var _initServer = BootstrapTable.prototype.initServer;

  BootstrapTable.prototype.initServer = function () {
    _initServer.apply(this, Array.prototype.slice.apply(arguments));
    var that = this;

    $('.sort-menu .sort-name').each(function () {
      $(this).children('i').first().removeClass('invisible');
      if ($(this).data('value') !== that.options.sortName) {
        $(this).children('i').first().addClass('invisible');
      }
    });

    $('.sort-menu .sort-order').each(function () {
      $(this).children('i').first().removeClass('invisible');
      if ($(this).data('value') !== that.options.sortOrder) {
        $(this).children('i').first().addClass('invisible');
      }
    });
  };

  BootstrapTable.prototype.onSort = function () {
    this.trigger('sort', this.options.sortName, this.options.sortOrder);
    this.initServer(this.options.silentSort);
    $.fn.bootstrapTable.utils.setCookie(this, 'bs.table.sortOrder', this.options.sortOrder);
    $.fn.bootstrapTable.utils.setCookie(this, 'bs.table.sortName', this.options.sortName);
  };

  BootstrapTable.prototype.initSearchText = function () {
    if (this.options.searchText !== '') {
      var $search = $('#table-search');
      $search.val(this.options.searchText);
      this.onSearch({currentTarget: $search, firedByInitSearchText: true});
    }
  };

})(jQuery);


$(document).ready(function () {
  'use strict';

  var bst = $('.bootstrap-table .table').data()['bootstrap.table'];

  $('#table-search').off('keyup drop blur').on('keyup drop blur', function (event) {
    clearTimeout(0);
    setTimeout(function () {
        bst.onSearch(event);
    }, 500);
  });

  $('.sort-menu .sort-name').off('click').on('click', function (event) {
    bst.options.sortName = $(event.currentTarget).data('value');
    bst.onSort();
  });

  $('.sort-menu .sort-order').off('click').on('click', function (event) {
    bst.options.sortOrder = $(event.currentTarget).data('value');
    bst.onSort();
  });
});
