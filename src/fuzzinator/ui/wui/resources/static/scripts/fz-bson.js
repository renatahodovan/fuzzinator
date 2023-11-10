/*
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

  var bson = {};

  // Handle 'bson.dumps()' canonical extended JSON format properties.
  var reviver = function (key, value) {
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
  };

  bson.reviver = reviver;

  bson.converters = {
    'text json': function (data) {
      return JSON.parse(data, reviver);
    }
  };

  fz.bson = bson;

  return bson;
})(fuzzinator);
