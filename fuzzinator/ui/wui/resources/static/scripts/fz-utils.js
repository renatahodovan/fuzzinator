/*
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global fuzzinator */

(function (fz) {
  'use strict';

  var utils = {};

  utils.bstOptions = function (options) {
    var columns = [];
    for (var colName of options.columnNames) {
      columns.push({ field: colName, title: colName, visible: true, sortable: true });
    }
    columns[0].formatter = options.formatter;

    return {
      columns: columns,
      pagination: true,
      sidePagination: 'server',
      undefinedText: 'N/A',
      showHeader: false,
      filterControl: true,
      rememberOrder: true,
      sortName: options.sortName,
      sortOrder: options.sortOrder,
      buttonsClass: 'outline-secondary',

      detailView: options.detailFormatter !== null,
      detailViewIcon: false,
      detailFormatter: options.detailFormatter,

      cookie: true,
      cookieStorage: 'localStorage',
      cookieExpire: '1d',
      cookieIdTable: options.cookieIdTable,

      showAll: options.showAll,
      includeInvalid: options.includeInvalid,

      queryParams: function (params) {
        if ('includeInvalid' in this) {
            params.includeInvalid = this.includeInvalid;
        }
        params.showAll = this.showAll;
        return params;
      },

      ajax: function (params) {
        options.getRows(
          params.data,
          function (data, status, xhr) {
            params.success({ rows: data, total: Number(xhr.getResponseHeader('X-Total')) }, status, xhr);
          },
          params.error
        );
      }
    };
  };

  fz.utils = utils;

  return utils;
})(fuzzinator);
