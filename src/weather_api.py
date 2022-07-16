import pandas as pd
from datetime import datetime, timedelta
import os

###############################################################
# Dublin Airport Yesterday Data
# https://data.gov.ie/dataset/yesterdays-weather-dublin-airport
###############################################################

# Download CSV
# URL: https://www.met.ie/latest-reports/observations/download/Dublin-Airport/yesterday

# API (not working) - 504 Gateway Timeout
# URL: https://prodapi.metweb.ie/observations/dublin/yesterday

def format_hour(hour) -> int:
    '''
    Receives a string of the form 'HH:MM' and returns a integer with the hour
    '''
    hour_str = hour.split(':')
    return int(hour_str[0])

today_dt = datetime.now()
yesterday_dt = today_dt - timedelta(days=1)
yesterday_dt_str = yesterday_dt.strftime("%Y-%m-%d")

WEATHER_DATA_URL = 'https://www.met.ie/latest-reports/observations/download/Dublin-Airport/yesterday'
ROOT_DIR_LOCAL = os.path.abspath(os.curdir)

try:
    dubairport_yesterday = pd.read_csv(WEATHER_DATA_URL)
    dubairport_yesterday.columns = ['time', 'report', 'temp', 'wdsp', 'wind_gust', 'wind_direction', 'rain', 'pressure']
    dubairport_yesterday['time'] = dubairport_yesterday['time'].apply(format_hour)
    dubairport_yesterday.drop(['report', 'wind_gust', 'wind_direction', 'pressure'], axis=1, inplace=True)
    csv_filename = f'{ROOT_DIR_LOCAL}/data/external/weather/{yesterday_dt_str}.csv'
    if not os.path.exists(csv_filename):
        dubairport_yesterday.to_csv(csv_filename, index=False)  
except Exception as e:
    txt_filename = f'{ROOT_DIR_LOCAL}/data/external/weather/error_{yesterday_dt_str}.txt'
    with open(txt_filename, 'w') as f:
        f.write(e.__str__())
