/*
 * Copyright (c) 2019-2021 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global fz */

(function ($) {
  'use strict';

  $.merge($.fn.bootstrapTable.defaults.cookiesEnabled, ['bs.table.includeInvalid', 'bs.table.showAll']);
  const utils = $.fn.bootstrapTable.utils;

  $.BootstrapTable = class extends $.BootstrapTable {
    initCookie (...args) {
      super.initCookie(...args);

      if ('includeInvalid' in this.options) {
          var includeInvalidCookie = utils.getCookie(this, this.options.cookieIdTable, 'bs.table.includeInvalid');
          this.options.includeInvalid = includeInvalidCookie !== null ? includeInvalidCookie == 'true' : this.options.includeInvalid;
      }

      var showAllCookie = utils.getCookie(this, this.options.cookieIdTable, 'bs.table.showAll');
      this.options.showAll = showAllCookie !== null ? showAllCookie == 'true' : this.options.showAll;
    }

    init (...args) {
      super.init(...args);

      if ('includeInvalid' in this.options && !this.options.includeInvalid) {
        $('.include-invalid i').first().removeClass('invisible');
      }

      if (!this.options.showAll) {
        $('.show-all i').first().removeClass('invisible');
      }
    }

    initServer (...args) {
      super.initServer(...args);
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
    }

    onSort () {
      this.trigger('sort', this.options.sortName, this.options.sortOrder);
      this.initServer(this.options.silentSort);
      utils.setCookie(this, 'bs.table.sortOrder', this.options.sortOrder);
      utils.setCookie(this, 'bs.table.sortName', this.options.sortName);
    }

    onSearch (...args) {
      super.onSearch(...args);
      // This cookie saving must be done here, since the 'search' option of our bstables are not
      // set, hence it wouldn't be saved otherwise.
      utils.setCookie(this, 'bs.table.searchText', this.options.searchText);
    }

    initSearchText () {
      // Calling super wouldn't have any effect since it's bound to the 'search' option
      // which isn't set for Fuzzinator.
      if (this.options.searchText !== '') {
        var $search = $('#table-search');
        $search.val(this.options.searchText);
        this.onSearch({currentTarget: $search, firedByInitSearchText: true});
      }
    }
  }
})(jQuery);


$(document).ready(function () {
  'use strict';

  var bst = $('#issues-table, #stats-table').data()['bootstrap.table'];

  $('#table-search').off('keyup drop blur').on('keyup drop blur', function (event) {
    clearTimeout(0);
    setTimeout(function () {
        bst.onSearch({currentTarget: event.currentTarget});
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

  $('#import-form').submit(function () {
    fz.api.addIssues($('#import-form').prop('files'));
  });

  $('.export .dropdown-item').on('click', function (event) {
    var target = $(event.currentTarget).data('target');
    var format = $(event.currentTarget).data('format');
    var ext = $(event.currentTarget).data('ext');
    var collectionName = $('.bootstrap-table table.table').attr('id').replace('-table', '');
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
    $(event.currentTarget).attr('download', `${collectionName}-${target}.${ext ? ext : format}`);
    return true;
  });
});
