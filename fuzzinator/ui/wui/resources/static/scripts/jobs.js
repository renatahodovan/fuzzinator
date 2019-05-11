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

   var newJob = function (data) {
    var job = $(`#${data.type}-job-template`).prop('content').cloneNode(true);
    $(job).find('.card').attr('id', `job-${data.ident}`);
    $(job).find('.card').addClass(data.status === 'active' ? 'bg-success' : 'bg-secondary');
    $(job).find('.close').attr('onclick', `fz.api.cancelJob('${data.ident}')`);
    $(job).find('.job-id').text(data.ident);
    if ('fuzzer' in data) {
      $(job).find('.job-fuzzer').text(data.fuzzer);
    }
    if ('sut' in data) {
      $(job).find('.job-sut').text(data.sut);
    }
    if ('issue_id' in data) {
      $(job).find('.job-issue').text(data.issue_id);
    }
    if ('batch' in data || 'size' in data) {
      $(job).find('.progress-bar').attr('data-maxvalue', Math.max(data.batch || 0, data.size || 0));
    }
    $('#jobs').append(document.importNode(job, true));
  };

  fz.notifications.onmessage['new_job'] = newJob;

  fz.notifications.onmessage['job_progress'] = function (data) {
    var jobCard = $(`#job-${data.ident}`);
    if (jobCard.length !== 0) {
      var progress = jobCard.find('.progress-bar');
      var percent = Math.round(data.progress / progress.attr('data-maxvalue') * 100);
      progress.css('width', `${percent}%`);
      progress.attr('aria-valuenow', percent);
      jobCard.find('.progress-text').text(`${percent}%`);
    }
  };

  fz.notifications.onmessage['activate_job'] = function (data) {
    var jobCard = $(`#job-${data.ident}`);
    if (jobCard.length !== 0 && jobCard.hasClass('bg-secondary')) {
      jobCard.removeClass('bg-secondary').addClass('bg-success');
    }
  };

  fz.notifications.onmessage['remove_job'] = function (data) {
    $(`#job-${data.ident}`).remove();
  };

  fz.api.getJobs(function (data) {
    for (var job of data) {
      newJob(job);
    }
  });
});
