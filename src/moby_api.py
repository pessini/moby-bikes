# sourcery skip: use-named-expression
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

ROOT_DIR_LOCAL = os.path.abspath(os.curdir)

api_response = requests.get(historical_url, headers=headers, params=parameters)
json_str = api_response.text
parse_json = json.loads(json_str)

if api_response:
    json_filename = f'{ROOT_DIR_LOCAL}/data/external/moby/{yesterday_dt_str}.json'
else:
    json_filename = f'{ROOT_DIR_LOCAL}/data/external/moby/{yesterday_dt_str}_error.json'
    
if not os.path.exists(json_filename):
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(parse_json, f, ensure_ascii=False, indent=4)
