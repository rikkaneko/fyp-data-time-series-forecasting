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
import pandas as pd
import requests
from plotly.subplots import make_subplots
import plotly.graph_objs as go

from pathlib import Path

from zstandard import ZstdDecompressor

DATASET_FILE_PATH = 'data/hk_opendata_journey_data.csv'

if not Path('data/hk_opendata_journey_data.csv').exists():
  print(f'Downloading hk_opendata_journey_data.csv.zst')
  r = requests.get('https://files.nekoul.com/pub/hk_opendata_journey_data.csv.zst')
  if not r.ok:
    print('Unable to download the datasets')
    exit(128)

  with open(DATASET_FILE_PATH, 'wb+') as f:
    dctx = ZstdDecompressor()
    decompressor = dctx.stream_writer(f)
    decompressor.write(r.content)

df = pd.read_csv(DATASET_FILE_PATH, parse_dates=['timestamp'])
feature_keys = [
  'H1-CH', 'H1-EH', 'H11-CH', 'H11-EH', 'H2-CH', 'H2-EH', 'H2-WH', 'H3-CH', 'H3-WH', 'H4-CH', 'H4-EH', 'H4-WH',
  'H5-CH', 'H5-EH', 'H5-WH', 'K01-CH', 'K01-WH', 'K02-CH', 'K02-EH', 'K03-CH', 'K03-EH', 'K03-WH', 'K04-CH', 'K04-WH',
  'K05-CH', 'K05-EH', 'K06-CH', 'K06-WH'
]


def plot(data: list[pd.Series], title: str = '', *,
         xaxis_title='Time', yaxis_title='Journey time', rows=1, cols=1,
         subplot_titles: list[str] = None, subplot_pos: list[int] = None):
  fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles)
  for idx, s in enumerate(data):
    pos = subplot_pos[idx] if subplot_pos is not None else idx
    fig.add_trace(
      go.Scatter(x=s.index, y=s),
      row=pos // rows + 1,
      col=pos % cols + 1,
    )

  fig.update_layout(
    title={
      'text': title,
      'x': 0.5,
    },
    xaxis_title=xaxis_title,
    yaxis_title=yaxis_title,
  )
  fig.show()


print(f'dataset shape={df.shape}')
cht = df['K02-CH']
cht.index = df['timestamp']
# Filter invalid time
cht = cht[cht != -1].iloc[5:]
print(f'K02-CH shape={cht.shape}')
print(cht.head(10))
# Resample the datasets to 5 Min
cht_5m: pd.Series = cht.resample('5Min').interpolate(method='time')
print(f'K02-CH (5 Min) shape={cht_5m.shape}')
plot([
  cht,
  cht_5m,
  cht.resample('10Min').interpolate(method='time'),
  cht.resample('30Min').interpolate(method='time'),
], 'K02-CH', rows=2, cols=2, subplot_titles=['1s', '5 Min', '10 Min', '30 Min'])


def splint_and_normalize_dataset(data: pd.Series, *,
                                 train_ratio=0.7, val_ratio=0.2) -> (pd.Series, pd.Series, pd.Series):
  data_n = data.shape[0]
  train_n = int(data_n * train_ratio)
  val_n = int(data_n * val_ratio)

  train_data: pd.Series = data.iloc[:train_n]
  # Normalize data
  mean = train_data.mean()
  std = train_data.std()
  train_data = (train_data - mean) / std
  val_data = (data.iloc[train_n:train_n + val_n] - mean) / std
  test_data = (data.iloc[train_n + val_n:] - mean) / std
  return train_data, val_data, test_data


print(cht_5m.head(10))
train, val, test = splint_and_normalize_dataset(cht_5m)
print(f'Train data shape={train.shape}')
print(f'Validation data shape={val.shape}')
print(f'Test data shape={test.shape}')
plot([train, val, test], 'K02-CH', rows=1, cols=1,
     subplot_titles=['Train', 'Validation', 'Test'], subplot_pos=[0, 0, 0])

# Tensor input=[[1], [2], [3], [4], [5]] output=[6]

if __name__ == '__main__':
  pass
