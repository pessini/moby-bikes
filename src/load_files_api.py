import pandas as pd
from datetime import datetime, timedelta
import os
import requests
import json

today_dt = datetime.now()
today_dt_str = today_dt.strftime("%Y-%m-%d")
yesterday_dt = today_dt - timedelta(days=1)
yesterday_dt_str = yesterday_dt.strftime("%Y-%m-%d")

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

headers={'content-type': 'application/json', 'accept': 'application/json'}

WEATHER_DATA_API_URL = "https://prodapi.metweb.ie/observations/dublin/yesterday"
WEATHER_DATA_CSV_URL = 'https://www.met.ie/latest-reports/observations/download/Dublin-Airport/yesterday'
ROOT_DIR_LOCAL = os.path.abspath(os.curdir)

try:
    
    api_response = requests.get(WEATHER_DATA_API_URL, headers=headers)
    json_str = api_response.text
    parse_json = json.loads(json_str)

    if api_response:
        json_filename = f'{ROOT_DIR_LOCAL}/data/external/weather/{yesterday_dt_str}.json'
    else:
        json_filename = f'{ROOT_DIR_LOCAL}/data/external/weather/{yesterday_dt_str}_error.json'

    if not os.path.exists(json_filename):
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(parse_json, f, ensure_ascii=False, indent=4)
            
except Exception:
    
    try:
        
        dubairport_yesterday = pd.read_csv(WEATHER_DATA_CSV_URL)
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

###############################################################
# Moby Bikes Data
# https://data.gov.ie/dataset/moby-bikes
###############################################################

# Moby API
# URL: https://data.smartdublin.ie/mobybikes-api/

#parameters = None
parameters = {
    "start": yesterday_dt_str,
    "end": today_dt_str
}

baseurl = "https://data.smartdublin.ie/mobybikes-api/"
# last_reading_url = f'{baseurl}last_reading/'

historical_url = f'{baseurl}historical/'
api_response_moby = requests.get(historical_url, headers=headers, params=parameters)
moby_json_str = api_response_moby.text
moby_parse_json = json.loads(moby_json_str)

if api_response_moby:
    moby_json_filename = f'{ROOT_DIR_LOCAL}/data/external/moby/{yesterday_dt_str}.json'
else:
    moby_json_filename = f'{ROOT_DIR_LOCAL}/data/external/moby/{yesterday_dt_str}_error.json'

if not os.path.exists(moby_json_filename):
    with open(moby_json_filename, 'w', encoding='utf-8') as f:
        json.dump(moby_parse_json, f, ensure_ascii=False, indent=4)
