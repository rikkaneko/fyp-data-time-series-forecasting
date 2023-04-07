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
import io
import os

import uvicorn
from typing import Annotated, Literal
from fastapi import FastAPI, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import requests
import zipfile
from pathlib import Path
from zstandard import ZstdDecompressor
from datetime import datetime, timedelta
from keras.models import load_model

BASE_DATA_DIR = 'data'
# Environment variable
WORKER_N = int(os.getenv('WORKER_N', 1))
USE_HTTPS = int(os.getenv('USE_HTTPS', 0))

DATESET_FILES = {
  'cht': {'path': f'{BASE_DATA_DIR}/journal_time_data_cht.csv',
          'download_url': 'https://files.nekoul.com/pub/journal_time_data_cht.csv.zst'},
  'eht': {'path': f'{BASE_DATA_DIR}/journal_time_data_eht.csv',
          'download_url': 'https://files.nekoul.com/pub/journal_time_data_eht.csv.zst'},
  'wht': {'path': f'{BASE_DATA_DIR}/journal_time_data_wht.csv',
          'download_url': 'https://files.nekoul.com/pub/journal_time_data_wht.csv.zst'}
}

for tunnel in DATESET_FILES:
  if not Path(DATESET_FILES[tunnel]['path']).exists():
    print(f'Downloading {DATESET_FILES[tunnel]["path"]}')
    r = requests.get(DATESET_FILES[tunnel]["download_url"])
    if not r.ok:
      print('Unable to download the datasets')
      exit(128)

    with open(DATESET_FILES[tunnel]['path'], 'wb+') as f:
      print(f'Decompressing {DATESET_FILES[tunnel]["path"]}')
      dctx = ZstdDecompressor()
      decompressor = dctx.stream_writer(f)
      decompressor.write(r.content)
      print(f'Decompression done')

MODEL_DIR = f'{BASE_DATA_DIR}/model'
MODEL_ARCHIEVE = 'fyp_forecasting_best_models.zip'
# Download all model versions if not exist
if not Path(MODEL_DIR).exists():
  print(f'Downloading {MODEL_ARCHIEVE}')
  r = requests.get(f'https://files.nekoul.com/pub/{MODEL_ARCHIEVE}', stream=True)
  if not r.ok:
    print('Unable to download the archieve')
    exit(128)

  with zipfile.ZipFile(io.BytesIO(r.content)) as zipfile:
    zipfile.extractall(BASE_DATA_DIR)

  print(f'Extracted all models')

# K02-CH (Cross-Harbour Tunnel)
cht = pd.read_csv(DATESET_FILES['cht']['path'])
cht.index = pd.to_datetime(cht['timestamp'])
cht.drop('timestamp', axis=1, inplace=True)
cht_model = load_model(f'{MODEL_DIR}/v19')
print('Loaded CHT (dataset, model)')

# K02-EH (Eastern Harbour Crossing)
eht = pd.read_csv(DATESET_FILES['eht']['path'])
eht.index = pd.to_datetime(eht['timestamp'])
eht.drop('timestamp', axis=1, inplace=True)
eht_model = load_model(f'{MODEL_DIR}/v25')
print('Loaded EHT (dataset, model)')

# K03-WH (Eastern Harbour Crossing)
wht = pd.read_csv(DATESET_FILES['wht']['path'])
wht.index = pd.to_datetime(wht['timestamp'])
wht.drop('timestamp', axis=1, inplace=True)
wht_model = load_model(f'{MODEL_DIR}/v25')
print('Loaded WHT (dataset, model)')

# Prediction horizon
# Use the past n_steps  data points to predict the next n_horizon data points
n_steps = 12 * 6
n_horizon = 12 * 3


def round_dt(dt, delta=timedelta(minutes=5)) -> datetime:
  dt1 = dt.replace(microsecond=0)
  dt1 = dt + (datetime.min - dt) % delta
  # Round down the timestamp
  return dt1 if dt1 <= dt else dt1 - delta


app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["GET"],
)


@app.get("/")
async def root():
  return {"status": "online"}


@app.get("/predict")
async def predict(tunnel: Literal["cht", "eht", "wht"],
                  time: Annotated[datetime | None, Query()],
                  response: Response,
                  include_timestamp: Annotated[bool | None, Query()] = True,
                  include_input: Annotated[bool | None, Query()] = True):
  if time is None:
    time = datetime.now() - timedelta(minutes=5)

  # Model input is [time1,time] inclusively
  time = round_dt(time) - timedelta(minutes=5)
  time1 = time - timedelta(minutes=(n_steps - 1) * 5)

  # Select dataset
  data = cht if tunnel == "cht" \
    else eht if tunnel == "eht" \
    else wht if tunnel == "wht" \
    else None

  # Select model
  model = cht_model if tunnel == "cht" \
    else eht_model if tunnel == "eht" \
    else wht_model if tunnel == "wht" \
    else None

  if time1 < data.index[0]:
    response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    eariler_time = data.index[0].to_pydatetime() + timedelta(minutes=n_steps * 5)
    return {
      "error": f"Index out of range, the earlist available time is {eariler_time}"
    }

  # Use existing dataset
  model_input = None
  if time <= data.index[-1]:
    model_input = data.loc[time1:time]
  else:
    # TODO Fetch from upstream
    # When time is None, attempt to fetch the previous n_steps journey data from upstream API
    pass

  if model_input is None:
    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return {
      "error": "Unable to fetch data from upstream or the dataset"
    }

  # Predict the next n_horizon data point
  result = model.predict(np.expand_dims(model_input.to_numpy(), axis=0))
  result = result.flatten()
  predict_start = time + timedelta(minutes=5)
  predict_end = time + timedelta(minutes=n_horizon * 5)
  next_iter = predict_end + timedelta(minutes=5)
  if next_iter > data.index[-1]:
    next_iter = None

  res = {"time": predict_start, "predict": result.tolist(), "next": next_iter}

  if include_timestamp:
    timestamp = pd.date_range(start=predict_start, end=predict_end, freq='5min')
    res["timestamp"] = timestamp.tolist()

  if include_input:
    input_data = {
      "timestamp": model_input.index.tolist(),
      "data": model_input.iloc[:, 0].tolist(),
    }
    res["input_data"] = input_data

  return res


@app.get("/fetch")
async def fetch(tunnel: Literal["cht", "eht", "wht"],
                start_time: Annotated[datetime, Query()],
                end_time: Annotated[datetime, Query()],
                response: Response,
                include_timestamp: Annotated[bool | None, Query()] = True):
  start_time = round_dt(start_time)
  end_time = round_dt(end_time)

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
               data.index[0].to_pydatetime() + " to " +
               data.index[-1].to_pydatetime()
    }

  result = data.loc[start_time:end_time, data.columns[0]]
  res = {
    "start_time": start_time,
    "end_time": end_time,
    "results": result.to_list()
  }

  if include_timestamp:
    timestamp = result.index
    res["timestamp"] = timestamp.tolist()

  return res


@app.get("/get_meta")
def fetch_meta():
  return {
    "n_steps": n_steps,
    "n_horizon": n_horizon,
    "earliest_predict_start": cht.index[0].to_pydatetime() + timedelta(minutes=n_steps * 5),
    "timestamp_start": cht.index[0].to_pydatetime(),
    "timestamp_end": cht.index[-1].to_pydatetime(),
  }


if __name__ == "__main__":
  if USE_HTTPS == 1:
    uvicorn.run(app, host="0.0.0.0", port=8881, workers=WORKER_N,
                ssl_keyfile="privkey.pem", ssl_certfile="fullchain.pem")
  else:
    uvicorn.run(app, host="0.0.0.0", port=8881, workers=WORKER_N)
