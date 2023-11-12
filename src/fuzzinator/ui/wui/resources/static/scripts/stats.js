/*
 * Copyright (c) 2019-2022 Renata Hodovan, Akos Kiss.
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

  // Present fuzzer execution speed in human-readable format: exec/(sec|min|hour).
  function speed(exec, time) {
    var v = exec / time;
    if (v > 1) {
      return `${Math.round(v)}/s`;
    }
    v *= 60;
    if (v > 1) {
      return `${Math.round(v)}/m`;
    }
    v *= 60;
    if (v > 1) {
      return `${Math.round(v)}/h`;
    }
  }

  // Present fuzzer execution time in human-readable format: D(ays)H(ours)?|H(ours)M(ins)?|M(ins)|S(seconds).
  function execTime(time) {
    var seconds = Math.round(time % 60);
    time = Math.floor(time / 60);
    var minutes = Math.round(time % 60);
    time = Math.floor(time / 60);
    var hours = Math.round(time % 24);
    time = Math.floor(time / 24);
    var days = time;
    return `${days > 0 ? days + 'd' : ''}${hours > 0 ? hours + 'h' : ''}${days == 0 && minutes > 0 ? minutes + 'm' : ''}${days > 0 || hours > 0 || minutes > 0 ? '' : seconds + 's'}`;
  }

  function statRowFormatter (value, data) {
    var statRow = document.importNode($('#stat-card-template').prop('content').cloneNode(true), true).children[0];
    $(statRow).find('.fuzzer').text(data.fuzzer);
    $(statRow).find('.exec').text(data.exec);
    $(statRow).find('.issues').text(data.issues);
    $(statRow).find('.unique').text(data.unique);
    $(statRow).find('.time').text(execTime(data.time));
    $(statRow).find('.speed').text(speed(data.exec, data.time));
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
      $(statRowDetail).find('.time').text(execTime(detail.time));
      $(statRowDetail).find('.speed').text(speed(detail.exec, detail.time));
      $(statRowDetail).appendTo($(mainDiv));
    }
    return mainDiv.outerHTML;
  }

  var bst = $('#stats-table').bootstrapTable(fz.utils.bstOptions({
    columnNames: ['fuzzer', 'exec', 'issues', 'unique', 'sut', 'time'],
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
