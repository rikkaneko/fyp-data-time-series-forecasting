#  This file is part of fyp-data-time-series-forecasting.
#  Copyright (c) 2023 Joe Ma <rikkaneko23@gmail.com>
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

import uvicorn
from typing import Annotated, Literal
from fastapi import FastAPI, Query, Response, status
from datetime import datetime
import pandas as pd
import numpy as np
import os
import requests
from pathlib import Path
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from zstandard import ZstdCompressionWriter, ZstdDecompressor
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from numpy import array2string
from datetime import datetime

DATASET_FILE_PATH = 'journal_time_data_hk.csv'
if not Path(DATASET_FILE_PATH).exists():
  print(f'Downloading journal_time_data_hk.csv.zst')
  r = requests.get('https://files.nekoul.com/pub/journal_time_data_hk.csv.zst')
  if not r.ok:
    print('Unable to download the datasets')
    exit(128)

  with open(DATASET_FILE_PATH, 'wb+') as f:
    print(f'Decompressing {DATASET_FILE_PATH}')
    dctx = ZstdDecompressor()
    decompressor = dctx.stream_writer(f)
    decompressor.write(r.content)
    print(f'Decompression done')

df = pd.read_csv(DATASET_FILE_PATH)
df.index = pd.to_datetime(df['timestamp'])
df.drop('timestamp', axis=1, inplace=True)

# Filter invalid time
skip_date = pd.to_datetime("2022-07-11")
util_date = pd.to_datetime("2023-11-10")
df = df[(df.index > skip_date) & (df.index <= util_date)]

df = df.resample('5Min').interpolate(method='time').iloc[1:]
df['week_day'] = df.index.dayofweek.values
df['hour'] = df.index.hour.values
df['minute'] = df.index.minute.values

# TODO Use the pre-processed dataset
# K02-CH (Cross-Harbour Tunnel)
cht = df[['K02-CH', 'week_day', 'hour', 'minute']]
cht_mean = cht.loc[:, 'K02-CH'].mean()
cht.loc[:, 'K02-CH'].replace(-1, cht_mean, inplace=True)
# Smooth traffic data by move average
cht['K02-CH'] = cht['K02-CH'].rolling(6).mean().shift(periods=-2).fillna(cht_mean)

# K02-EH (Eastern Harbour Crossing)
eht = df[['K02-EH', 'week_day', 'hour', 'minute']]
# Replace the invalid data with the average value instead of removing it
eht_mean = eht.loc[:, 'K02-EH'].mean()
eht.loc[:, 'K02-EH'].replace(-1, eht_mean, inplace=True)
# Smooth traffic data by move average
eht['K02-EH'] = eht['K02-EH'].rolling(6).mean().shift(periods=-2).fillna(eht_mean)

# ??? (Western Harbour Crossing)
# TODO Find the suitable data columns
wht = pd.DataFrame()

# Prediction horizon
# Use the past n_steps  data points to predict the next n_horizon data points
n_steps = 12 * 6
n_horizon = 12 * 3

app = FastAPI()


@app.get("/")
async def root():
  return {"status": "online"}


@app.get("/predict")
async def predict(time: Annotated[datetime | None, Query()] = datetime.now()):
  time = time.replace(second=0, microsecond=0)
  # TODO Return the predict journey data after `time`
  # When time is None, attempt to fetch the previous n_steps journey data from upstream API
  return {"time": time.isoformat(), predict: []}


@app.get("/fetch")
async def fetch(tunnel: Literal["cht", "eht", "wht"],
                start_time: Annotated[datetime, Query()],
                end_time: Annotated[datetime, Query()],
                response: Response):
  start_time = start_time.replace(second=0, microsecond=0)
  end_time = end_time.replace(second=0, microsecond=0)

  data = cht if tunnel == "cht" \
    else eht if tunnel == "eht" \
    else wht if tunnel == "wht" \
    else None

  if data is None:
    return {}

  if start_time < data.index[0] or end_time > data.index[-1]:
    response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return {
      "error": "Index out of range, the available time range is " +
               data.index[0].to_pydatetime().isoformat() + " to " +
               data.index[-1].to_pydatetime().isoformat()
    }

  return {
    "start_time": start_time.isoformat(),
    "end_time": end_time.isoformat(),
    "results": eht.loc[start_time:end_time, 'K02-EH'].to_list()
  }


if __name__ == "__main__":
  uvicorn.run(app, host="127.0.0.1", port=8881)
