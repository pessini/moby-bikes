import requests
import json
from datetime import datetime, timedelta
import os

today_dt = datetime.now()
today_dt_str = today_dt.strftime("%Y-%m-%d")
yesterday_dt = today_dt - timedelta(days=1)
yesterday_dt_str = yesterday_dt.strftime("%Y-%m-%d")

#parameters = None
parameters = {
    "start": yesterday_dt_str,
    "end": today_dt_str
}

headers={'content-type': 'application/json', 'accept': 'application/json'}
baseurl = "https://data.smartdublin.ie/mobybikes-api/"
# last_reading_url = f'{baseurl}last_reading/'

historical_url = f'{baseurl}historical/'

r = requests.get(historical_url, headers=headers, params=parameters)
json_str = r.text
parse_json = json.loads(json_str)

ROOT_DIR = os.path.abspath(os.curdir)
json_filename = f'{ROOT_DIR}/data/raw/moby/{yesterday_dt_str}.json'
with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump(parse_json, f, ensure_ascii=False, indent=4)