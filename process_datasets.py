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
import csv
import os
import re
import tarfile
import dateutil.parser

from multiprocessing import Process
from pathlib import Path
from zstandard import ZstdDecompressor
from datetime import datetime

# Define variables
BASE_DIR = Path('data')
JOURNEY_DATA_TIMESTAMP_PAT = re.compile(r'.*(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})\d{2}.csv')


# Extract zstd stream and pipe to fifo
def do_zstd_extract(output_name: Path):
  print(f'Started proccess do_zstd_extract() (PID=#{os.getpid()})')
  ifh = open(Path(BASE_DIR, 'journey-data.tar.zstd'), 'rb')
  ofh = open(output_name, 'wb')
  dec = ZstdDecompressor()
  dec.copy_stream(ifh, ofh, read_size=8192, write_size=8192)
  print('Decompression completed.')


def extract_timestamp(file_title: str) -> datetime:
  mat = JOURNEY_DATA_TIMESTAMP_PAT.match(file_title)
  return dateutil.parser.isoparse(f'{mat.group(1)}-{mat.group(2)}-{mat.group(3)}'
                                  f'T{mat.group(4)}:{mat.group(5)}')


def process_journey_data():
  header = ['timestamp', 'journey_time']
  journey_time_data: dict[str, list[list[int | str]]] = {}
  fifo_path = Path(BASE_DIR, '.fifo')
  if not fifo_path.exists():
    os.mkfifo(fifo_path)
  p = Process(target=do_zstd_extract, args=(fifo_path,))
  p.start()
  with tarfile.open(fifo_path, mode='r|') as tar:
    ent = tar.next()
    while ent is not None:
      if not ent.isfile():
        ent = tar.next()
        continue
      f = tar.extractfile(ent)
      timestamp = extract_timestamp(ent.name)
      content = f.read().decode('utf-8')
      reader = csv.reader(content.split('\n'))
      next(reader)
      for row in reader:
        if not row:
          break
        road = f'{row[0]}-{row[1]}'
        if road not in journey_time_data:
          journey_time_data[road] = [header]
        journey_time_data[road].append([timestamp.isoformat(), row[2]])

      ent = tar.next()

  p.join()
  print(f'Proccess do_zstd_extract() ended')

  for name, record in journey_time_data.items():
    record[1:] = sorted(record[1:], key=lambda e: e[0])
    print(f'Writing to {name}.csv')
    with open(Path(BASE_DIR / 'road', f'{name}.csv'), mode='w+') as f:
      writer = csv.writer(f)
      writer.writerows(record)


if __name__ == '__main__':
  process_journey_data()
