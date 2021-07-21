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
