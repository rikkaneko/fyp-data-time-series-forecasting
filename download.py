#  This file is part of fyp-data-time-series-forecasting.
#  Copyright (c) 2022 Joe Ma <rikkaneko23@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pathlib import Path
from typing import Any, Callable
from aiocsv import AsyncWriter
from datetime import datetime, timedelta

import asyncio
import aiohttp
import aiofile
import xmltodict
import dateutil.parser


# Define variable
START_TIME = '2021-09-07T09:08'
END_TIME = '2021-09-07T10:00'

# Build data dir for traffic data
data_dir = Path('data/traffic-detectors-speed')
data_dir.mkdir(parents=True, exist_ok=True)


# Generate timestamp in YYYYMMDD-HHMM from start_date to end_data (exclusive)
def make_timestamp(start_date: str, end_data: str):
  start: datetime = dateutil.parser.isoparse(start_date)
  end: datetime = dateutil.parser.isoparse(end_data)
  delta = timedelta(minutes=1)
  while start < end:
    yield start.strftime('%Y%m%d-%H%M')
    start += delta


# Process data to csv list
def process_traffic_detectors_data(content: dict[str, Any]) -> (dict[str, list[list[str]]]):
  date = content['raw_speed_volume_list']['date'].replace('-', '')
  # header
  # detector_id: ID of the detector
  # direction: 8 directions [1, 8]
  # speed: Average traffic speed of lanes (km/h)
  # occupancy: Average Occupancy of lane (%)
  # s.d.: Average standard deviation of lanes
  header = ['detector_id', 'direction', *[f'{k}_speed'
                                          for k in ['fast_lane', 'middle_lane_1', 'middle_lane_2', 'slow_lane']
                                          ]]
  periods = content['raw_speed_volume_list']['periods']['period']
  # Map direction to id
  direct2id: Callable[[str], int] = lambda direction: {
    'North': 1, 'East': 2, 'South': 3, 'West': 4, 'North East': 1,
    'South East': 2, 'North West': 3, 'South West': 4}[direction]
  to_snake: Callable[[str], str] = lambda s: s.replace(' ', '_').lower()

  results: dict[str, list[list[str]]] = {}
  for period in periods:
    speed_data: list[list[str]] = [header]
    title = f'{date}-{period["period_from"].replace(":", "")}_{period["period_to"].replace(":", "")}'
    for detector in period['detectors']['detector']:
      lanes: dict[str, float] = dict([(header[i], 0) for i in range(2, len(header))])
      # Special cases if elements not parsed as list
      if type(detector['lanes']['lane']) is not list:
        lane = detector['lanes']['lane']
        detector['lanes']['lane'] = [lane]
      lane_n = len(detector['lanes']['lane'])
      for lane in detector['lanes']['lane']:
        lane_id = to_snake(lane['lane_id'])
        lanes[f'{lane_id}_speed'] = lane['speed']
      speed_data.append([
        detector['detector_id'], direct2id(detector['direction']), *[lanes[header[k]] for k in range(2, len(header))]
      ])
    results[title] = speed_data
  return results


LIMIT = 16
sem = asyncio.BoundedSemaphore(LIMIT)


# Fetch traffic data
async def fetch_traffic_detectors_data(timestamp: str):
  async with sem, aiohttp.ClientSession() as client:
    async with client.get(url='https://api.data.gov.hk/v1/historical-archive/get-file',
                          params={'url': 'https://resource.data.one.gov.hk/td/traffic-detectors/rawSpeedVol-all.xml',
                                  'time': timestamp}) as res:
      if not res.ok:
        print(f'Unable to fetch traffic detectors data (#timestamp={timestamp})')
        return

      try:
        xml_data = await res.text()
        data: dict[str, Any] = xmltodict.parse(xml_data, xml_attribs=False)
        speed_data = process_traffic_detectors_data(data)
      except:
        print(f'Invalid traffic data (#timestamp={timestamp})')
        return

      for title, content in speed_data.items():
        output_file = Path(data_dir, title + '.csv')
        if output_file.exists():
          print(f'Duplicated file {output_file} (#timestamp={timestamp})')
          continue
        print(f'Download {output_file} (#timestamp={timestamp})')
        async with aiofile.async_open(output_file, 'w') as f:
          writer = AsyncWriter(f)
          await writer.writerows(content)


async def fetch_all():
  tasks = []
  n = 0
  for t in make_timestamp(START_TIME, END_TIME):
    if n >= LIMIT:
      await asyncio.gather(*tasks)
      tasks.clear()
      n = 0
    tasks.append(loop.create_task(fetch_traffic_detectors_data(t)))
    n += 1
  await asyncio.gather(*tasks)


if __name__ == '__main__':
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  try:
    loop.run_until_complete(fetch_all())
  except KeyboardInterrupt:
    print('Interrupted by keyboard')
