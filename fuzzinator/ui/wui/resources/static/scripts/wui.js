/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019-2021 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global fz */

$(document).ready(function () {
  function fireworks () {
    $('.fz-logo').addClass('fz-logo-fireworks');
    $('.fz-logo').one('animationend', function () {
      $(this).removeClass('fz-logo-fireworks');
    });
  }

  $('.fz-logo').click(function () {
    fireworks();
  });

  fz.notifications.onopen = function () {
    $('.fz-motto').attr('title', 'online').removeClass('websocket-error');
  };

  fz.notifications.onclose = function () {
    $('.fz-motto').attr('title', 'offline').addClass('websocket-error');
  };

  fz.notifications.onmessage['issue_added'] = function () {
    $('.badge').text(Number($('.badge').text()) + 1);
    fireworks();
  };

  fz.notifications.onmessage['error'] = function (data) {
    var toast = document.importNode($('#notification-toast-template').prop('content').cloneNode(true), true).children[0];
    $(toast).find('.toast-title').text(data.title);
    var body = data.body;
    if (data.exc_info) {
      body += data.exc_info;
    }
    $(toast).find('.toast-body').text(body);
    $('#toast-container').append(toast);
    $(toast).toast({'autohide': false})
    $(toast).on('click', function() { $(toast).toast('dispose'); $(toast).remove(); });
    $(toast).toast('show');
  };

  fz.notifications.start();

  $('.fz-motto').click(function () {
    fz.notifications.toggle();
  });
});
