/*
 * Copyright (c) 2019-2021 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global fz */

$(document).ready(function () {
  'use strict';

   var jobAdded = function (data) {
    var job = $(`#${data.type}-job-template`).prop('content').cloneNode(true);
    $(job).find('.card').attr('id', `job-${data.job_id}`);
    $(job).find('.card').addClass(data.status === 'active' ? 'bg-success' : 'bg-secondary');
    $(job).find('.close').attr('onclick', `fz.api.cancelJob('${data.job_id}')`);
    $(job).find('.job-id').text(data.job_id);
    if ('fuzzer' in data) {
      $(job).find('.job-fuzzer').text(data.fuzzer);
    }
    if ('sut' in data) {
      $(job).find('.job-sut').text(data.sut);
    }
    if ('issue_id' in data) {
      $(job).find('.job-issue').text(data.issue_id);
    }
    if ('issue_oid' in data) {
      $(job).find('.job-issue').attr('href', `/issues/${data.issue_oid}`);
    }
    var maxValue = data.batch || data.size || 0;
    var progress = $(job).find('.progress-bar');
    progress.attr('data-maxvalue', maxValue);

    if (maxValue == Infinity) {
      $(job).find('.progress-text').text('0');
    }
    $('#jobs').append(document.importNode(job, true));

    if ('progress' in data) {
      jobProgressed(data);
    }
  };

  fz.notifications.onmessage['job_added'] = jobAdded;

  var jobProgressed = function (data) {
    var jobCard = $(`#job-${data.job_id}`);
    if (jobCard.length !== 0) {
      var progress = jobCard.find('.progress-bar');
      if ($(progress).data('maxvalue') < Infinity) {
        var percent = Math.round(data.progress / $(progress).data('maxvalue') * 100);
        progress.css('width', `${percent}%`);
        progress.attr('aria-valuenow', percent);
        jobCard.find('.progress-text').text(`${percent}%`);
      } else {
        jobCard.find('.progress-text').text(new Intl.NumberFormat({ notation: "scientific" }).format(data.progress));
        if (!progress.hasClass('progress-bar-striped')) {
          progress.attr('style', 'width: 100%');
          progress.addClass('progress-bar-striped');
        }
      }
    }
  };

  fz.notifications.onmessage['job_progressed'] = jobProgressed;

  fz.notifications.onmessage['job_activated'] = function (data) {
    var jobCard = $(`#job-${data.job_id}`);
    if (jobCard.length !== 0 && jobCard.hasClass('bg-secondary')) {
      jobCard.removeClass('bg-secondary').addClass('bg-success');
    }
    if ($(jobCard).data('job-type') == 'fuzz') {
      var progress = $(jobCard).find('.progress-bar');
      if ($(progress).data('maxvalue') == Infinity) {
        progress.attr('style', 'width: 100%');
        progress.addClass('progress-bar-striped');
      }
    }
  };

  fz.notifications.onmessage['job_removed'] = function (data) {
    $(`#job-${data.job_id}`).remove();
  };

  fz.api.getJobs(function (data) {
    for (var job of data) {
      jobAdded(job);
    }
  });
});
