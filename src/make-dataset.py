# %%
import pandas as pd
import numpy as np
import requests
import json
from pandas import json_normalize


# %%
#moby_jan[(moby_jan['BikeID'] == 5) &(moby_jan['LastRentalStart'] == '2020-12-31 17:35:09')]


# %%
parameters = {
    "start": '2020-10-13',
    "end": '2021-6-4',
    "bikeid": 5
}


# %%
response = requests.get("https://data.smartdublin.ie/mobybikes-api/historical", params=parameters)


# %%
print(response.json())


# %%
def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

jprint(response.json())


# %%
dictr = response.json()
df = json_normalize(dictr)


# %%
df.shape


# %%
df.head()


# %%
df.groupby('LastRentalStart').size().sort_values(ascending=False)


# %%
import os
import glob
import pandas as pd
import pathlib
pathlib.Path().resolve()


# %%
path = r'../data/raw/hist-rentals'
all_files = glob.glob(path + '/moby-bikes*.csv')
print(all_files)


# %%
#combine all files in the list
combined_csv = pd.concat([pd.read_csv(f) for f in all_files ])

#export to csv
combined_csv.to_csv( '../data/raw/historical_data.csv', index=False, encoding='utf-8-sig')


# %%
moby_all = pd.read_csv('../data/raw/historical_data.csv')


# %%
moby_all.shape


# %%
moby_all.head()


# %%
moby_all.isnull().sum()


# %% [markdown]
# >https://data.gov.ie/dataset/phoenix-park-hourly-data
# 
# >https://data.gov.ie/dataset/phoenixpark-daily-data