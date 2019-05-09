/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

/* global bsonReviver */
/* exported WUIWebSocket */

var WUIWebSocket = function () {
  this.ws = null;
  this.onopen = null;
  this.onclose = null;
  this.onmessage = [];
}

WUIWebSocket.prototype.start = function ()  {
  var wuiws = this;
  var ws = new WebSocket(`ws://${window.location.host}/notifications`);

  ws.onopen = wuiws.onopen;
  ws.onclose = wuiws.onclose;

  ws.onmessage = function (evt) {
    var msg = JSON.parse(evt.data, bsonReviver);

    if (msg.action in wuiws.onmessage) {
      wuiws.onmessage[msg.action](msg.data);
    }
  };
  this.ws = ws;
}

WUIWebSocket.prototype.toggle = function () {
  if (this.ws.readyState === WebSocket.OPEN) {
    this.ws.close();
  } else {
    this.start();
  }
};
