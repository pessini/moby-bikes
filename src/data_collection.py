# %%
import pandas as pd
import numpy as np
import requests
import json
from pandas import json_normalize
import seaborn as sns

# %%
historical_data = pd.read_csv('../data/raw/moby-bikes-historical-data-012021.csv')

historical_data.head()


# %%
parameters = {
    "start": '2020-10-13',
    "end": '2021-6-4',
    "bikeid": 5
}
response = requests.get("https://data.smartdublin.ie/mobybikes-api/historical", params=parameters)



# %%

#########################################
###### API for Weather forecasting ######
#########################################
# https://data.gov.ie/dataset/phoenix-park-hourly-data
#https://data.gov.ie/dataset/phoenixpark-daily-data

