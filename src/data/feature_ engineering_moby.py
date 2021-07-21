# %%
import pandas as pd
import numpy as np
import json
from pandas import json_normalize

# %%
historical_data = pd.read_csv('../../data/interim/moby-bikes-historical-data.csv')
historical_data_copy = historical_data.copy()

columns_todrop = ['BikeIdentifier', 
                  'BikeTypeName', 
                  'EBikeProfileID', 
                  'IsEBike', 
                  'IsMotor', 
                  'IsSmartLock', 
                  'SpikeID']
historical_data_copy = historical_data_copy.drop(columns_todrop, axis=1)


# %%
from datetime import datetime
# 



#########################################
###### API for Weather forecasting ######
#########################################
# https://data.gov.ie/dataset/phoenix-park-hourly-data
# https://data.gov.ie/dataset/phoenixpark-daily-data


# %%
from urllib.request import urlopen
  
# import json
import requests
# store the URL in url as 
# parameter for urlopen
url = "https://calendarific.com/api/v2/holidays/"
  
# store the response of URL
#response = urlopen(url)

parameters = {
    "api_key": '45f3218e321b77bf8ae47b5680283784344b5d4f',
    "country": 'ie',
    "year": '2020'
}
response = requests.get(url, params=parameters)

#%%
def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

jprint(response.json())
# %%
