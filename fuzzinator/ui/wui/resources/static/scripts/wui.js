/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global WUIWebSocket, activePage */
/* exported cancelJob deleteIssue, reduceIssue, validateIssue */

var ws = new WUIWebSocket();
var successQueue = [];

ws.onopen = function () {
  $('.fz-motto').attr('title', 'online').removeClass('websocket-error');
};

ws.onclose = function () {
  $('.fz-motto').attr('title', 'offline').addClass('websocket-error');
};

ws.onmessage['new_fuzz_job'] = function (data) {
  var job = $('#fuzz-job-template').prop('content').cloneNode(true);
  $(job).find('.card').attr('id', `job-${data.ident}`);
  $(job).find('.card').addClass(data.status === 'active' ? 'bg-success' : 'bg-secondary');
  $(job).find('.close').attr('onclick', `cancelJob('${data.ident}')`);
  $(job).find('.fuzz-job-id').text(data.ident);
  $(job).find('.fuzz-job-fuzzer').text(data.fuzzer);
  $(job).find('.fuzz-job-sut').text(data.sut);
  $(job).find('.progress-bar').attr('data-maxvalue', data.batch);
  $('#jobs').append(document.importNode(job, true));
};

ws.onmessage['new_reduce_job'] = function (data) {
  var job = $('#reduce-job-template').prop('content').cloneNode(true);
  $(job).find('.card').attr('id', `job-${data.ident}`);
  $(job).find('.card').addClass(data.status === 'active' ? 'bg-success' : 'bg-secondary');
  $(job).find('.close').attr('onclick', `cancelJob('${data.ident}')`);
  $(job).find('.reduce-job-id').text(data.ident);
  $(job).find('.reduce-job-sut').text(data.sut);
  $(job).find('.reduce-job-issue').text(data.issue_id);
  $(job).find('.progress-bar').attr('data-maxvalue', data.size);
  $('#jobs').append(document.importNode(job, true));
};

ws.onmessage['new_update_job'] = function (data) {
  var job = $('#update-job-template').prop('content').cloneNode(true);
  $(job).find('.card').attr('id', `job-${data.ident}`);
  $(job).find('.card').addClass(data.status === 'active' ? 'bg-success' : 'bg-secondary');
  $(job).find('.close').attr('onclick', `cancelJob('${data.ident}')`);
  $(job).find('.update-job-id').text(data.ident);
  $(job).find('.update-job-sut').text(data.sut);
  $('#jobs').append(document.importNode(job, true));
};

ws.onmessage['new_validate_job'] = function (data) {
  var job = $('#validate-job-template').prop('content').cloneNode(true);
  $(job).find('.card').attr('id', `job-${data.ident}`);
  $(job).find('.card').addClass(data.status === 'active' ? 'bg-success' : 'bg-secondary');
  $(job).find('.close').attr('onclick', `cancelJob('${data.ident}')`);
  $(job).find('.validate-job-id').text(data.ident);
  $(job).find('.validate-job-sut').text(data.sut);
  $(job).find('.validate-job-issue').text(data.issue_id);
  $('#jobs').append(document.importNode(job, true));
};

ws.onmessage['job_progress'] = function (data) {
  var jobCard = $(`#job-${data.ident}`);
  if (jobCard.length !== 0) {
    var progress = jobCard.find('.progress-bar');
    var percent = Math.round(data.progress / progress.attr('data-maxvalue') * 100);
    progress.css('width', `${percent}%`);
    progress.attr('aria-valuenow', percent);
    jobCard.find('.progress-text').text(`${percent}%`);
  }
};

ws.onmessage['activate_job'] = function (data) {
  var jobCard = $(`#job-${data.ident}`);
  if (jobCard.length !== 0 && jobCard.hasClass('bg-secondary')) {
    jobCard.removeClass('bg-secondary').addClass('bg-success');
  }
};

ws.onmessage['remove_job'] = function (data) {
  $(`#job-${data.ident}`).remove();
};

ws.onmessage['new_issue'] = function () {
  $('.badge').text(Number($('.badge').text()) + 1);
  $('#issue-table').bootstrapTable('refresh', { silent: true });
  fireworks();
};

ws.onmessage['update_fuzz_stat'] = function () {
  if (activePage === 'stats') {
    $('#stat-table').bootstrapTable('refresh', { silent: true });
  }
};

ws.onmessage['update_issue'] =
ws.onmessage['delete_issue'] =
ws.onmessage['invalid_issue'] = function () {
  $('#issue-table').bootstrapTable('refresh', { silent: true });
};

ws.onmessage['get_issues'] =
ws.onmessage['get_stats'] = function (data) {
  successQueue.shift()(data);
};

function createBootstrapTable (table, sortName, sortOrder, columnNames, formatter, detailFormatter, cookie, action) {
  var columns = [];
  for (var colName of columnNames) {
    columns.push({field: colName, title: colName, visible: true, sortable: true});
  }
  columns[0].formatter = formatter;

  table.bootstrapTable({
    columns: columns,
    search: true,
    pagination: true,
    sidePagination: 'server',
    undefinedText: 'N/A',
    showRefresh: true,
    showHeader: false,
    filterControl: true,
    rememberOrder: true,
    sortName: sortName,
    sortOrder: sortOrder,
    buttonsClass: 'outline-secondary',

    detailView: detailFormatter !== null,
    detailViewIcon: false,
    detailFormatter: detailFormatter,

    cookie: true,
    cookieStorage: 'localStorage',
    cookieExpire: '1d',
    cookieIdTable: cookie,

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
    },

    ajax: function (params) {
      ws.send(JSON.stringify({
        'action': action,
        'data': params.data
      }));
      successQueue.push(params.success);
    }
  });
}

function issueRowFormatter (value, data) {
  var issueRow = document.importNode($('#issue-card-template').prop('content').cloneNode(true), true).children[0];
  $(issueRow).find('.card').id = data.id;
  $(issueRow).find('.card').addClass(typeof data['invalid'] === 'undefined' ? 'bg-warning' : 'bg-secondary');
  $(issueRow).find('.delete-issue').attr('onclick', `deleteIssue('${data._id}')`);
  $(issueRow).find('.reduce-issue').attr('onclick', `reduceIssue('${data._id}')`);
  $(issueRow).find('.validate-issue').attr('onclick', `validateIssue('${data._id}')`);
  $(issueRow).find('.issue-ref').text(data.id);
  $(issueRow).find('.issue-ref').attr('href', `/issue/${data._id}`);
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
  for (var detail of row.configs) {
    var statRowDetail = document.importNode($('#stat-row-template').prop('content').cloneNode(true), true).children[0];
    if (detail.subconfig !== null) {
        $(statRowDetail).find('.config-ref').attr('href', `/config/${detail.subconfig}/stat`);
    }
    $(statRowDetail).find('.config-ref').text(detail.subconfig === null ? 'N/A' : `${detail.subconfig}`);
    $(statRowDetail).find('.sut').text(row.sut);
    $(statRowDetail).find('.exec').text(detail.exec);
    $(statRowDetail).find('.issues').text(detail.crashes);
    $(statRowDetail).find('.unique').text(detail.unique);
    $(statRowDetail).appendTo($(mainDiv));
  }
  return mainDiv.outerHTML;
}

function createIssueTable () {
  return createBootstrapTable($('#issue-table'), 'first_seen', 'desc',
                              ['sut', 'fuzzer', 'id', 'first_seen', 'last_seen', 'count', 'reduced', 'reported'],
                              issueRowFormatter, null, 'issueTableCookie', 'get_issues');
}

function createStatTable () {
  return createBootstrapTable($('#stat-table'), 'exec', 'desc',
                              ['fuzzer', 'exec', 'crashes', 'unique', 'sut'],
                              statRowFormatter, statRowDetailFormatter, 'statTableCookie', 'get_stats');
}

function fireworks () {
  $('.fz-logo').addClass('fz-logo-fireworks');
  $('.fz-logo').one('animationend', function () {
    $(this).removeClass('fz-logo-fireworks');
  });
}

function deleteIssue (issueId) {
  ws.send(JSON.stringify({
    'action': 'delete_issue',
    '_id': issueId,
  }));
}

function reduceIssue (issueId) {
  ws.send(JSON.stringify({
    'action': 'reduce_issue',
    '_id': issueId,
  }));
}

function validateIssue (issueId) {
  ws.send(JSON.stringify({
    'action': 'validate_issue',
    '_id': issueId,
  }));
}

function cancelJob (jobId) {
  ws.send(JSON.stringify({
    'action': 'cancel_job',
    'ident': jobId,
  }));
}

$(document).ready(function () {
  ws.start();
  ws.wait(function () {
    ws.send(JSON.stringify({ 'action': 'get_jobs' }));
      switch (activePage) {
        case 'stats': createStatTable(); break;
        case 'issues': createIssueTable(); break;
      }
  });

  $('.fz-motto').click(function () {
    ws.toggle();
  });

  $('.fz-logo').click(function () {
    fireworks();
  });
});
