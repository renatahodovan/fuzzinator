/*
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global fuzzinator */

(function (fz, $) {
  'use strict';

  var api = {};

  var getCollection = function (url, pagination, success, error) {
    $.ajax({
      url: url,
      data: $.extend(pagination, { detailed: false }),
      converters: fz.bson.converters,
      cache: false,
      success: success,
      error: error,
    });
  };

  api.getStats = function (pagination, success, error) {
    getCollection('/api/stats', pagination, success, error);
  };

  api.getIssues = function (pagination, success, error) {
    getCollection('/api/issues', pagination, success, error);
  };

  api.deleteIssue = function (issueId, success, error) {
    $.ajax({
      method: 'DELETE',
      url: `/api/issues/${issueId}`,
      success: success,
      error: error,
    });
  };

  api.addJob = function (type, issueId, success, error) {
    $.ajax({
      method: 'POST',
      url: '/api/jobs',
      contentType: 'application/json',
      data: JSON.stringify({ type: type, _id: issueId }),
      success: success,
      error: error,
    });
  };

  api.cancelJob = function (jobId, success, error) {
    $.ajax({
      method: 'DELETE',
      url: `/api/jobs/${jobId}`,
      success: success,
      error: error,
    });
  };

  api.getJobs = function (success, error) {
    $.ajax({
      url: '/api/jobs',
      converters: fz.bson.converters,
      cache: false,
      success: success,
      error: error,
    });
  };

  fz.api = api;

  return api;
})(fuzzinator, jQuery);
