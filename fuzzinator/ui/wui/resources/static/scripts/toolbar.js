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
  var _initCookie = BootstrapTable.prototype.initCookie;
  var _init = BootstrapTable.prototype.init;

  $.merge($.fn.bootstrapTable.defaults.cookiesEnabled, ['bs.table.includeInvalid', 'bs.table.showAll']);

  BootstrapTable.prototype.initCookie = function () {
    _initCookie.apply(this, Array.prototype.slice.apply(arguments));

    if ('includeInvalid' in this.options) {
        var includeInvalidCookie = $.fn.bootstrapTable.utils.getCookie(this, this.options.cookieIdTable, 'bs.table.includeInvalid');
        this.options.includeInvalid = includeInvalidCookie !== null ? includeInvalidCookie == 'true' : this.options.includeInvalid;
    }

    var showAllCookie = $.fn.bootstrapTable.utils.getCookie(this, this.options.cookieIdTable, 'bs.table.showAll');
    this.options.showAll = showAllCookie !== null ? showAllCookie == 'true' : this.options.showAll;
  };

  BootstrapTable.prototype.init = function () {
    _init.apply(this, Array.prototype.slice.apply(arguments));

    if ('includeInvalid' in this.options && !this.options.includeInvalid) {
      $('.include-invalid i').first().removeClass('invisible');
    }

    if (!this.options.showAll) {
      $('.show-all i').first().removeClass('invisible');
    }
  };

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

  $('.show-all').off('click').on('click', function (event) {
    bst.options.showAll = !bst.options.showAll;
    $.fn.bootstrapTable.utils.setCookie(bst, 'bs.table.showAll', bst.options.showAll);
    bst.refresh({ silent: true });
    if (!bst.options.showAll) {
      $(event.currentTarget).children('i').first().removeClass('invisible');
    } else {
      $(event.currentTarget).children('i').first().addClass('invisible');
    }
  });

  $('.include-invalid').off('click').on('click', function (event) {
    bst.options.includeInvalid = !bst.options.includeInvalid;
    $.fn.bootstrapTable.utils.setCookie(bst, 'bs.table.includeInvalid', bst.options.includeInvalid);
    bst.refresh({ silent: true });
    if (!bst.options.includeInvalid) {
      $(event.currentTarget).children('i').first().removeClass('invisible');
    } else {
      $(event.currentTarget).children('i').first().addClass('invisible');
    }
  });

  $('.export .dropdown-item').on('click', function (event) {
    var target = $(event.currentTarget).data('target');
    var format = $(event.currentTarget).data('format');
    var collectionName = $('.bootstrap-table .table').attr('id').replace('-table', '');
    var href = `/api/${collectionName}?format=${format}`;

    if (target == 'all') {
      href += '&showAll=true&includeInvalid=true'
    } else if (['filtered', 'page'].includes(target)) {
      href += `&search=${bst.options.searchText}&showAll=${bst.options.showAll}`;
      if ('includeInvalid' in bst.options) {
        href += `&includeInvalid=${bst.options.includeInvalid}`;
      }
      if (target === 'page') {
        var offset = (bst.options.pageNumber - 1) * bst.options.pageSize;
        href += `&order=${bst.options.sortOrder}&sort=${bst.options.sortName}&offset=${offset}&limit=${bst.options.pageSize}`;
      }
    }
    $(event.currentTarget).attr('href', href);
    $(event.currentTarget).attr('download', `${collectionName}-${target}.${format}`);
    return true;
  });
});
