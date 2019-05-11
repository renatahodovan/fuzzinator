/*
 * Copyright (c) 2019 Tamas Keri.
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

  var notifications = {};

  notifications.onopen = null;
  notifications.onclose = null;
  notifications.onmessage = {};

  var ws = null;

  notifications.start = function () {
    ws = new WebSocket(`ws://${window.location.host}/notifications`);

    ws.onopen = function (evt) {
      if (notifications.onopen !== null) {
        notifications.onopen(evt);
      }
    };

    ws.onclose = function (evt) {
      if (notifications.onclose !== null) {
        notifications.onclose(evt)
      }
    };

    ws.onmessage = function (evt) {
      var msg = JSON.parse(evt.data, fz.bson.reviver);

      if (msg.action in notifications.onmessage) {
        notifications.onmessage[msg.action](msg.data);
      }
    };
  };

  notifications.toggle = function () {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    } else {
      notifications.start();
    }
  };

  fz.notifications = notifications;

  return notifications;
})(fuzzinator);
