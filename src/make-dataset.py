# %%
import os
import glob
import pandas as pd
import pathlib
pathlib.Path().resolve()
# %%
path = r'../data/raw/hist-rentals-2'
all_files = sorted(glob.glob(f'{path}/moby-bikes*.csv'))
print(all_files)

# %%
#combine all files in the list
combined_csv = pd.concat([pd.read_csv(f) for f in all_files ])

#export to csv
combined_csv.to_csv( '../data/raw/hist-rentals-2/moby-bikes-historical-data-082022-12-8.csv', index=False)

# %%
moby_all = pd.read_csv('../data/raw/historical_data.csv')

# %%
moby_all.shape

# %%
moby_all.isnull().sum()
# %%
