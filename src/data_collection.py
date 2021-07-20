# %%
import pandas as pd
import numpy as np
import requests
import json
from pandas import json_normalize
import seaborn as sns

# %%
historical_data = pd.read_csv('../data/interim/moby-bikes-historical-data.csv')
historical_data_copy = historical_data.copy()
historical_data_copy = historical_data_copy.drop(['BikeIdentifier', 'BikeTypeName', 'EBikeProfileID', 'IsEBike', 'IsMotor', 'IsSmartLock', 'SpikeID'], axis=1)
historical_data_copy.to_json('../data/interim/moby-bikes-historical-data.json', orient='records')


# %%
parameters = {
    "start": '2020-10-13',
    "end": '2021-6-4',
    "bikeid": 5
}
response = requests.get("https://data.smartdublin.ie/mobybikes-api/last_reading")



# %%
print(response.json())

#########################################
###### API for Weather forecasting ######
#########################################
# https://data.gov.ie/dataset/phoenix-park-hourly-data
# https://data.gov.ie/dataset/phoenixpark-daily-data




#%%
def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

jprint(response.json())
# %%
