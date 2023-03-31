/*
 * This file is part of fyp-data-time-series-forecasting.
 * Copyright (c) 2023 Joe Ma <rikkaneko23@gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

let tunnel = 'cht';

$(function () {
  let plotly_div = $('#plot_div');

  $('#select_tunnel_menu li').on('click', function () {
    const val = $(this).text();
    tunnel = ['cht', 'eht', 'wht'].at($(this).val());
    $('#select_tunnel_btn').text(val);
  });

  // Example plot
  let trace1 = {
    x: [1, 2, 3, 4],
    y: [10, 15, 13, 17],
    mode: 'markers',
    name: 'Scatter'
  };

  let trace2 = {
    x: [2, 3, 4, 5],
    y: [16, 5, 11, 9],
    mode: 'lines',
    name: 'Lines'
  };

  let trace3 = {
    x: [1, 2, 3, 4],
    y: [12, 9, 15, 12],
    mode: 'lines+markers',
    name: 'Scatter and Lines'
  };

  let data = [trace1, trace2, trace3];

  let layout = {
    title: 'Title of the Graph',
    xaxis: {
      title: 'x-axis title'
    },
    yaxis: {
      title: 'y-axis title'
    }
  };

  Plotly.plot(plotly_div[0], data, layout);
});