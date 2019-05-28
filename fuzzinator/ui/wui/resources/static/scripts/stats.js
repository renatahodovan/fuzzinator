/*
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global fz */

$(document).ready(function () {
  'use strict';

  $('#stats-tab').addClass('active');

  function statRowFormatter (value, data) {
    var statRow = document.importNode($('#stat-card-template').prop('content').cloneNode(true), true).children[0];
    $(statRow).find('.fuzzer').text(data.fuzzer);
    $(statRow).find('.exec').text(data.exec);
    $(statRow).find('.issues').text(data.issues);
    $(statRow).find('.unique').text(data.unique);
    return $(statRow)[0].outerHTML;
  }

  function statRowDetailFormatter (index, row) {
    var mainDiv = document.createElement('div');
    for (var detail of row.subconfigs) {
      var statRowDetail = document.importNode($('#stat-row-template').prop('content').cloneNode(true), true).children[0];
      if (detail.subconfig !== null) {
          $(statRowDetail).find('.config-ref').attr('href', `/configs/${detail.subconfig}`);
      }
      $(statRowDetail).find('.config-ref').text(detail.subconfig === null ? 'N/A' : `${detail.subconfig}`);
      $(statRowDetail).find('.sut').text(row.sut);
      $(statRowDetail).find('.exec').text(detail.exec);
      $(statRowDetail).find('.issues').text(detail.issues);
      $(statRowDetail).find('.unique').text(detail.unique);
      $(statRowDetail).appendTo($(mainDiv));
    }
    return mainDiv.outerHTML;
  }


  var bst = $('#stat-table').bootstrapTable(fz.utils.bstOptions({
    columnNames: ['fuzzer', 'exec', 'issues', 'unique', 'sut'],
    formatter: statRowFormatter,
    detailFormatter: statRowDetailFormatter,
    sortName: 'exec',
    sortOrder: 'desc',
    cookieIdTable: 'statTableCookie',
    getRows: fz.api.getStats,
    showAll: true,
  })).data()['bootstrap.table'];

  fz.notifications.onmessage['refresh_stats'] = function () {
    bst.refresh({ silent: true });
  };
});
