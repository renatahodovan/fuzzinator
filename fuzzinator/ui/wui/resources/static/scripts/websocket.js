/*
 * Copyright (c) 2019 Tamas Keri.
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

var WUIWebSocket = function () {
  this.ws = null;
  this.onopen = null;
  this.onclose = null;
  this.onmessage = [];
}

WUIWebSocket.prototype.start = function ()  {
  var wuiws = this;
  var ws = new WebSocket(`ws://${window.location.host}/wui`);

  ws.onopen = wuiws.onopen;
  ws.onclose = wuiws.onclose;

  ws.onmessage = function (evt) {
    // Handle 'bson.dumps()' canonical extended JSON format properties.
    var msg = JSON.parse(evt.data, function (key, value) {
      if (typeof value === 'object' && value !== null && Object.keys(value).length === 1 && Object.keys(value)[0].startsWith('$')) {
        var k = Object.keys(value)[0];
        switch (k) {
          case '$date':
            return new Date(value[k]);
          case '$numberDouble':
          case '$numberDecimal':
            return new Number(value[k]);
          default:
            return value[k];
        }
      }
      return value;
    });

    if (msg.action in wuiws.onmessage) {
      wuiws.onmessage[msg.action](msg.data);
    }
  };
  this.ws = ws;
}

WUIWebSocket.prototype.wait = function (onconnect) {
  var wuiws = this;
  setTimeout(function () {
    if (wuiws.ws.readyState === WebSocket.OPEN) {
      onconnect();
    } else {
      wuiws.wait(onconnect);
    }
  }, 5);
};

WUIWebSocket.prototype.toggle = function () {
  if (this.ws.readyState === WebSocket.OPEN) {
    this.ws.close();
  } else {
    this.start();
  }
};

WUIWebSocket.prototype.send = function (data) {
  this.ws.send(data);
};
