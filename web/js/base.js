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
            style="margin-top: 30px; max-width: 500px; width: 80%; z-index: 10;" id="pop_alert" role="alert"> \
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

function get_local_isotime(time) {
  const tzoffset = time.getTimezoneOffset() * 60000;
  return (new Date(time.getTime() - tzoffset)).toISOString().slice(0, 16);
}

function get_random_date(start, end) {
  const start_time = new Date(start);
  const end_time = new Date(end);
  const time = new Date(start_time.getTime() + Math.random() * (end_time.getTime() - start_time.getTime()))
  return get_local_isotime(time);
}

$(async function () {
  let plotly_div = $('#plot_div');
  let select_tunnel_btn = $('#select_tunnel_btn');
  let start_time_input = $('#start_time_input');
  let end_time_input = $('#end_time_input');
  let fetch_btn = $('#fetch_button');
  let fetch_btn_icon = $('#fetch_button_icon');
  let predict_time_input = $('#predict_time_input');
  let predict_button = $('#predict_button');
  let predict_btn_icon = $('#predict_button_icon');
  let show_actual_checkbox = $('#show_actual_checkbox');
  let next_day_btn = $('#next_day_button');
  let predict_all_btn = $('#predict_all_button');
  let predict_all_btn_icon = $('#predict_all_button_icon');
  let predict_all_btn_text = $('#predict_all_button_text');
  let shuffle_button = $('#shuffle_button');

  let predict_all_started = false;
  const layout_update = {
    title: select_tunnel_btn.text(),
    xaxis: {},
    yaxis: {}
  }

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
        fetch_btn_icon.addClass('bi-x');
        console.log('error', 'Unable to fetch data');
        show_pop_alert('Unable to fetch data', 'alert-danger');
        return;
      }
      const data = await res.json();

      // Update plot data
      const data_update = {
        x: [data["timestamp"], []],
        y: [data["results"], []],
        name: ["Actuals"],
      };

      Plotly.update(plotly_div[0], data_update, layout_update, [0, 1]);

      // Update button icon state
      fetch_btn_icon.removeClass();
      fetch_btn_icon.addClass('bi bi-check-lg');
      setTimeout(() => {
        fetch_btn_icon.removeClass();
        fetch_btn_icon.addClass('bi bi-chevron-right');
      }, 3000);

    } catch (err) {
      console.log('error', err);
      show_pop_alert(err.message, 'alert-danger');
    }
  });

  predict_button.on('click', async function () {
    try {
      const time = predict_time_input.val();
      const res = await fetch(`${endpoint}/predict?` + new URLSearchParams({
        tunnel,
        time,
      }));

      if (!res.ok) {
        console.log('error', 'Unable to fetch prediction result');
        show_pop_alert('Unable to fetch prediction result', 'alert-danger');
        return;
      }
      const data = await res.json();

      // Update plot data
      const data_update = {
        x: [data['input_data']['timestamp'], data['timestamp']],
        y: [data['input_data']['data'], data['predict']],
      };

      if (!!data['next'] && show_actual_checkbox.prop('checked')) {
        const res = await fetch(`${endpoint}/fetch?` + new URLSearchParams({
          tunnel,
          start_time: data['timestamp'][0],
          end_time: data['timestamp'][data['timestamp'].length - 1],
        }));

        const data1 = await res.json();

        data_update.x[0] = data_update.x[0].concat(data1['timestamp']);
        data_update.y[0] = data_update.y[0].concat(data1['results']);
      }

      Plotly.update(plotly_div[0], data_update, layout_update, [0, 1]);

      // Update button icon state
      predict_btn_icon.removeClass();
      predict_btn_icon.addClass('bi bi-check-lg');
      setTimeout(() => {
        predict_btn_icon.removeClass();
        predict_btn_icon.addClass('bi bi-chevron-right');
      }, 3000);

    } catch (err) {
      console.log('error', err);
      show_pop_alert(err.message, 'alert-danger');
    }
  });

  next_day_btn.on('click', function () {
    const date = new Date(predict_time_input.val());
    const max_date = new Date(meta['timestamp_end']);
    date.setDate(date.getDate() + 1);
    if (date <= max_date) {
      predict_time_input.val(get_local_isotime(date));
    }
  });

  predict_all_btn.on('click', async function () {
    // TODO Predict All
    // Already running, revert state
    if (predict_all_started) {
      predict_all_started = false;
      predict_all_btn_text.text('Predict All');
      predict_all_btn_icon.removeClass();
      predict_all_btn_icon.addClass('bi bi-check-lg');
      return;
    }

    // Clear plot
    const data_update = {
      x: [[]],
      y: [[]],
    };

    Plotly.update(plotly_div[0], data_update, layout_update, [0, 1]);

    // Extend plot
    let time = start_time_input.val();
    let end_time = new Date(end_time_input.val());
    let is_first_time = true;

    if (new Date(time) < new Date(meta['earliest_predict_start'])) {
      time = meta['earliest_predict_start'];
    }

    try {
      // Start predict_all_started state
      predict_all_btn_text.text('Pasue');
      predict_all_btn_icon.removeClass();
      predict_all_btn_icon.addClass('bi bi-pause');
      predict_all_started = true;

      while (predict_all_started && !!time && new Date(time) < end_time) {
        const res = await fetch(`${endpoint}/predict?` + new URLSearchParams({
          tunnel,
          time,
        }));

        if (!res.ok) {
          console.log('error', 'Unable to fetch prediction result');
          show_pop_alert('Unable to fetch prediction result', 'alert-danger');
          return;
        }
        const data = await res.json();

        const data_extend = {
          x: [data['input_data']['timestamp'], data['timestamp']],
          y: [data['input_data']['data'], data['predict']],
        };

        // Remove unneeded time period
        if (!is_first_time) {
          data_extend.x[0] = data_extend.x[0].slice(meta['n_steps'] - meta['n_horizon']);
          data_extend.y[0] = data_extend.y[0].slice(meta['n_steps'] - meta['n_horizon']);
        } else {
          is_first_time = false;
        }

        Plotly.extendTraces(plotly_div[0], data_extend, [0, 1]);

        time = data['next'];
        // Add delay
        await new Promise(r => setTimeout(r, 250));
      }

      predict_all_btn_text.text('Predict All');
      // Update button icon state
      predict_all_btn_icon.removeClass();
      predict_all_btn_icon.addClass('bi bi-check-lg');
      setTimeout(() => {
        predict_all_btn_icon.removeClass();
        predict_all_btn_icon.addClass('bi bi-chevron-right');
      }, 3000);

    } catch(err) {
      predict_all_btn_text.text('Predict All');
      predict_all_btn_icon.removeClass();
      predict_all_btn_icon.addClass('bi bi-x');
      console.log('error', err);
      show_pop_alert(err.message, 'alert-danger');
    }
  });

  shuffle_button.on('click', function () {
    predict_time_input.val(get_random_date(meta['timestamp_start'], meta['timestamp_end']));
  });

  // Enable bootstrap tooltips
  const tooltip_trigger_list = [].slice.call($('[data-bs-toggle="tooltip"]'));
  const tooltip_list = tooltip_trigger_list.map(function (e) {
    return new bootstrap.Tooltip(e);
  });

  $('input[type=datetime-local]').on('input', function () {
    const time_input = $(this);
    const time = new Date(time_input.val());
    if (time < new Date(time_input.prop('min'))) {
      time_input.val(time_input.prop('min'));
    } else if (time > new Date(time_input.prop('max'))) {
      time_input.val(time_input.prop('max'));
    }
  });

  // Fetch meta
  try {
    const res = await fetch(`${endpoint}/get_meta`);
    if (!res.ok) {
      console.log('error', 'Unable to fetch metadata');
      show_pop_alert('Unable to fetch metadata', 'alert-danger');
    }
    meta = await res.json();
  } catch (err) {
    console.log('error', err);
    show_pop_alert(err.message, 'alert-danger');
  }

  start_time_input.prop('min', meta['timstamp_start']);
  start_time_input.prop('max', meta['timestamp_end']);
  start_time_input.val(meta['timestamp_start']);
  end_time_input.prop('min', meta['timestamp_start']);
  end_time_input.prop('max', meta['timestamp_end']);
  end_time_input.val(meta['timestamp_end']);
  predict_time_input.prop('min', meta['earliest_predict_start']);
  predict_time_input.prop('max', meta['timestamp_end']);
  predict_time_input.val(get_random_date(meta['timestamp_start'], meta['timestamp_end']));

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
      range: [4, 35],
    }
  };

  let config = {
    responsive: true,
    showTips: false
  };

  Plotly.newPlot(plotly_div[0], data, layout, config);
});