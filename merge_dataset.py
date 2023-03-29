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
# df = df.resample('5Min').interpolate(method='time').iloc[1:]
# df['week_day'] = df.index.dayofweek.values
# df['hour'] = df.index.hour.values
# df['minute'] = df.index.minute.values
df.to_csv(Path(BASE_DIR, 'journal_time_data_hk.csv'))

