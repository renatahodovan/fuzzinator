/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
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

  fz.notifications.onmessage['new_issue'] = function () {
    $('.badge').text(Number($('.badge').text()) + 1);
    fireworks();
  };

  fz.notifications.start();

  $('.fz-motto').click(function () {
    fz.notifications.toggle();
  });
});
