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

import pandas as pd
from pathlib import Path

BASE_DIR = Path('data')

df_1 = pd.read_csv(Path(BASE_DIR, 'journal_time_data-1.csv'))
df_2 = pd.read_csv(Path(BASE_DIR, 'journal_time_data-2.csv'))
df = pd.concat([df_1, df_2], axis=0)
df: pd.DataFrame = df.filter(regex=r'(-(CH|WH|EH)$)|timestamp')
df.index = pd.to_datetime(df['timestamp'])
df.drop('timestamp', axis=1, inplace=True)
# Filter invalid time
skip_date = pd.to_datetime("2022-03-11")
df = df[df.index > skip_date]
df.to_csv(Path(BASE_DIR, 'journal_time_data_hk.csv'))

# Splint dataset related to individual tunnel
# Filter invalid time
skip_date = pd.to_datetime("2022-07-11")
util_date = pd.to_datetime("2023-11-10")
df = df[(df.index > skip_date) & (df.index <= util_date)]

df = df.resample('5Min').interpolate(method='time').iloc[1:]
df['week_day'] = df.index.dayofweek.values
df['hour'] = df.index.hour.values
df['minute'] = df.index.minute.values

# K02-CH (Cross-Harbour Tunnel)
cht = df[['K02-CH', 'week_day', 'hour', 'minute']]
cht_mean = cht.loc[:, 'K02-CH'].mean()
cht['K02-CH'].replace(-1, cht_mean, inplace=True)
# Smooth traffic data by move average
cht['K02-CH'] = cht['K02-CH'].rolling(6).mean().shift(periods=-2).fillna(cht_mean)
cht.to_csv(f'{BASE_DIR}/journal_time_data_cht.csv', encoding='utf-8')

# K02-EH (Eastern Harbour Crossing)
eht = df[['K02-EH', 'week_day', 'hour', 'minute']]
# Replace the invalid data with the average value instead of removing it
eht_mean = eht.loc[:, 'K02-EH'].mean()
eht['K02-EH'].replace(-1, eht_mean, inplace=True)
# Smooth traffic data by move average
eht['K02-EH'] = eht['K02-EH'].rolling(6).mean().shift(periods=-2).fillna(eht_mean)
eht.to_csv(f'{BASE_DIR}/journal_time_data_eht.csv', encoding='utf-8')

# K03-WH (Western Harbour Crossing)
wht = df[['K03-WH', 'week_day', 'hour', 'minute']]
# cht = cht[cht['K02-CH'] != -1]
# Replace the invalid data with the average value instead of removing it
wht_mean = wht.loc[:, 'K03-WH'].mean()
wht['K03-WH'].replace(-1, wht_mean, inplace=True)

# Smooth traffic data by move average
wht['K03-WH'] = wht['K03-WH'].rolling(6).mean().shift(periods=-2).fillna(wht_mean)
wht.to_csv(f'{BASE_DIR}/journal_time_data_wht.csv', encoding='utf-8')
