# %%
import pandas as pd
import numpy as np

lastreading = pd.read_csv("../data/lastreading.csv")

# %%
lastreading.head()
# %%
lastreading_clean = lastreading.drop(columns=['BikeTypeName',
                                        'EBikeProfileID',
                                        'EBikeStateID',
                                        'BikeIdentifier',
                                        'IsEBike',
                                        'IsMotor',
                                        'IsSmartLock',
                                        'Latitude',
                                        'Longitude',
                                        'SpikeID'])
# %%
lastreading_clean.head(30)
# %%
lastreading_clean[lastreading_clean.BikeID == 5]
# %%
import requests
import json
from pandas import json_normalize
from datetime import date, datetime

# %%
# parameters = {
#     "start": '2020-10-13',
#     "end": '2021-6-4',
#     "bikeid": 5
# }
#parameters = None
parameters = {
    "start": '2022-03-03',
    "end": '2022-03-04'
}

headers={'content-type': 'application/json', 'accept': 'application/json'}
baseurl = "https://data.smartdublin.ie/mobybikes-api/"
last_reading_url = f'{baseurl}last_reading/'

historical_url = f'{baseurl}historical/'

r = requests.get(historical_url, headers=headers, params=parameters)
data = r.text
parse_json = json.loads(data)
#print(parse_json)

now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
json_filename = f'../data/{dt_string}.json'
json_filename_yesterday = '../data/yesterday2.json'
with open(json_filename_yesterday, 'w', encoding='utf-8') as f:
    json.dump(parse_json, f, ensure_ascii=False, indent=4)
    

# %%
from datetime import date, datetime
now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
print(dt_string)
# %%