#%%
import pandas as pd
import numpy as np

historical_data = pd.read_csv('../data/raw/historical_data.csv')
historical_data_copy = historical_data.copy()

columns_todrop = ['HarvestTime',
                  'BikeIdentifier', 
                  'BikeTypeName', 
                  'EBikeStateID',
                  'EBikeProfileID', 
                  'IsEBike', 
                  'IsMotor', 
                  'IsSmartLock', 
                  'SpikeID']
historical_data_copy = historical_data_copy[historical_data['BikeTypeName'] == 'DUB-General']
historical_data_copy.drop(columns_todrop, axis=1, inplace=True)
#%%
historical_data.head()

#%%
historical_data_copy.head()
#########################################
###### API for Weather forecasting ######
#########################################
# https://data.gov.ie/dataset/phoenix-park-hourly-data
# https://data.gov.ie/dataset/phoenixpark-daily-data
# %%
