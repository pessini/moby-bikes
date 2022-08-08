# %%
import os
import shutil
from shutil import SameFileError
import glob
import pandas as pd
import pathlib
pathlib.Path().resolve()

#%%

# /Users/lpessini/TUDublin/moby-bikes/data/raw/hist-rentals/
# /Users/lpessini/TUDublin/moby-bikes/data/raw/mysql-data/

src_folder = r'/Users/pessini/Dropbox/Data-Science/moby-bikes/data/raw/hist-rentals/'
dst_folder = r'/Users/pessini/Dropbox/Data-Science/moby-bikes/data/raw/mysql-data/'

all_files = glob.glob(f'{src_folder}moby-bikes*.csv')
print('\n'.join(map(str,list(all_files))))
print(f'\n{len(all_files)} files found')

#%%
# printing the contents of the destination folder
print("Destination folder before copying::", os.listdir(dst_folder))

for f in all_files:
    # file names
    fileName = f.split('/')[-1]
    src_file = src_folder + fileName
    dst_file = dst_folder + fileName
    try:
        # copy file
        shutil.copyfile(src_file, dst_file)
        # destination folder after copying
        print("File copied: ", fileName)
    except SameFileError:
        print("We are trying to copy the same File")
    except IsADirectoryError:
        print("The destination is a directory")

dst_fold_contents = glob.glob(f'{dst_folder}moby-bikes*.csv')
print(f'\n{len(dst_fold_contents)} files copied')
# %%
for f in dst_fold_contents:

    historical_data = pd.read_csv(f)
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

    newfileName = f.split('-')[-1]
    historical_data_copy.to_csv(f'{dst_folder}/{newfileName}', 
                                index=False, na_rep='NULL', 
                                columns=['LastRentalStart','BikeID','Battery','LastGPSTime','Latitude','Longitude'])
    if os.path.isfile(f):
        os.remove(f)
    print(f'{newfileName} done')
