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

const endpoint = 'http://127.0.0.1:8881';
let meta = null;

let tunnel = 'cht';

function show_pop_alert(message, alert_type = 'alert-primary', add_classes = null) {
  remove_pop_alert();
  $('#alert-container').prepend(jQuery.parseHTML(
      `<div class="alert ${alert_type} alert-dismissible position-absolute fade show top-0 start-50 translate-middle-x" 
            style="margin-top: 30px; max-width: 500px; width: 80%" id="pop_alert" role="alert"> \
      <div>${message}</div> \
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button> \
      </div>`,
  ));
  if (add_classes) {
    $('.alert').addClass(add_classes);
  }
  window.scrollTo(0, 0);
}

function remove_pop_alert() {
  const alert = $('#pop_alert');
  if (alert.length)
    alert.remove();
}

$(async function () {
  let plotly_div = $('#plot_div');
  let select_tunnel_btn = $('#select_tunnel_btn');
  let start_time_input = $('#start_time_input');
  let end_time_input = $('#end_time_input');
  let fetch_btn = $('#fetch_button');
  let fetch_btn_icon = $('#fetch_button_icon');

  $(window).on('resize', function () {
    Plotly.relayout(plotly_div[0], {
      autosize: true,
    });
  });

  $('#select_tunnel_menu li').on('click', function () {
    const val = $(this).text();
    tunnel = ['cht', 'eht', 'wht'].at($(this).val());
    select_tunnel_btn.text(val);
    // Plotly.relayout(plotly_div[0], {title: val})
  });

  fetch_btn.on('click', async function () {
    try {
      const start_time = start_time_input.val();
      const end_time = end_time_input.val();
      const res = await fetch(`${endpoint}/fetch?` + new URLSearchParams({
        tunnel,
        start_time,
        end_time,
      }));

      if (!res.ok) {
        alert('Unable to fetch /fetch');
      }
      const data = await res.json();

      // Update plot data
      const data_update = {
        x: [data['timestamp']],
        y: [data['results']],
      };

      const layout_update = {
        title: select_tunnel_btn.text(),
        xaxis: [[]],
        yaxis: [[]]
      }

      Plotly.update(plotly_div[0], data_update, layout_update, [0]);

      // Update button icon state
      fetch_btn_icon.removeClass('bi-chevron-right');
      fetch_btn_icon.addClass('bi-check-lg');
      setTimeout(() => {
        fetch_btn_icon.removeClass('bi-check-lg');
        fetch_btn_icon.addClass('bi-chevron-right');
      }, 3000);

    } catch (err) {
      alert(err.message);
    }
  });

  // Fetch meta
  try {
    const res = await fetch(`${endpoint}/get_meta`);
    if (!res.ok) {
      alert('Unable to fetch /get_meta');
    }
    meta = await res.json();
  } catch (err) {
    alert(err.message);
  }

  start_time_input.prop('min', meta['timstamp_start']);
  start_time_input.prop('max', meta['timestamp_end']);
  start_time_input.val(meta['timestamp_start']);
  end_time_input.prop('min', meta['timestamp_start']);
  end_time_input.prop('max', meta['timestamp_end']);
  end_time_input.val(meta['timestamp_end']);

  // Plot data
  let actuals = {
    x: [],
    y: [],
    mode: 'lines',
    name: 'Actuals',
    line: {
      color: '#636efa'
    },
  };

  let predictions = {
    x: [],
    y: [],
    mode: 'lines',
    name: 'Predictions',
    line: {
      color: '#ef553b'
    },
  };

  let data = [actuals, predictions];

  let layout = {
    autosize: true,
    hovermode: 'closest',
    title: select_tunnel_btn.text(),
    plot_bgcolor: '#e5ecf6',
    xaxis: {
      title: 'Timestamp',
      gridcolor: '#ffffff',
    },
    yaxis: {
      title: 'Jounrey time',
      gridcolor: '#ffffff',
    }
  };

  let config = {
    responsive: true,
    showTips: false
  };

  Plotly.newPlot(plotly_div[0], data, layout, config);
});