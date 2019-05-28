/*
 * Copyright (c) 2019 Renata Hodovan, Akos Kiss.
 *
 * Licensed under the BSD 3-Clause License
 * <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
 * This file may not be copied, modified, or distributed except
 * according to those terms.
 */

$(document).ready(function () {
  'use strict';

  var bst = $('.bootstrap-table .table').data()['bootstrap.table'];

  function onSort () {
    bst.trigger('sort', bst.options.sortName, bst.options.sortOrder);
    bst.refresh({'silent': true});

    $('.sort-menu .sort-name').each(function () {
      $(this).children('i').first().removeClass('invisible');
      if ($(this).data('value') !== bst.options.sortName) {
        $(this).children('i').first().addClass('invisible');
      }
    });

    $('.sort-menu .sort-order').each(function () {
      $(this).children('i').first().removeClass('invisible');
      if ($(this).data('value') !== bst.options.sortOrder) {
        $(this).children('i').first().addClass('invisible');
      }
    });
  }
  onSort(bst);

  $('#table-search').off('keyup drop blur').on('keyup drop blur', function (event) {
    clearTimeout(0);
    setTimeout(function () {
        bst.onSearch(event);
    }, 500);
  });

  $('.sort-menu .sort-name').off('click').on('click', function (event) {
    bst.options.sortName = $(event.currentTarget).data('value');
    onSort(bst);
  });

  $('.sort-menu .sort-order').off('click').on('click', function (event) {
    bst.options.sortOrder = $(event.currentTarget).data('value');
    onSort(bst);
  });
});
