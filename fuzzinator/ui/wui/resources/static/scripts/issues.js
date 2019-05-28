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

  $('#issues-tab').addClass('active');

  function issueRowFormatter (value, data) {
    var issueRow = document.importNode($('#issue-card-template').prop('content').cloneNode(true), true).children[0];
    $(issueRow).find('.card').id = data.id;
    $(issueRow).find('.card').addClass(typeof data['invalid'] === 'undefined' ? 'bg-warning' : 'bg-secondary');
    $(issueRow).find('.delete-issue').attr('onclick', `fz.api.deleteIssue('${data._id}')`);
    $(issueRow).find('.reduce-issue').attr('onclick', `fz.api.addJob('reduce', '${data._id}')`);
    $(issueRow).find('.validate-issue').attr('onclick', `fz.api.addJob('validate', '${data._id}')`);
    $(issueRow).find('.issue-ref').text(data.id);
    $(issueRow).find('.issue-ref').attr('href', `/issues/${data._id}`);
    $(issueRow).find('.issue-id').attr('title', data.id);
    $(issueRow).find('.sut-id').text(data.sut);
    $(issueRow).find('.fuzzer-id').text(data.fuzzer);
    $(issueRow).find('.date_range').text((new Date(data.first_seen)).toISOString().slice(0, -5) + ' .. ' + (new Date(data.last_seen)).toISOString().slice(0, -5));
    $(issueRow).find('.count').text(data.count);

    if (data.reduced !== null) {
      $(issueRow).find('.reduced').text('crop');
    }
    if (data.reported) {
      $(issueRow).find('.reported').text('link');
    }

    return $(issueRow)[0].outerHTML;
  }

  var options = fz.utils.bstOptions({
    columnNames: ['sut', 'fuzzer', 'id', 'first_seen', 'last_seen', 'count', 'reduced', 'reported'],
    formatter: issueRowFormatter,
    sortName: 'first_seen',
    sortOrder: 'desc',
    cookieIdTable: 'issueTableCookie',
    getRows: fz.api.getIssues,
    showAll: true,
    includeInvalid: false,
  });
  var bst = $('#issue-table').bootstrapTable(options).data()['bootstrap.table'];

  fz.notifications.onmessage['refresh_issues'] = function () {
    bst.refresh({ silent: true });
  };
});
