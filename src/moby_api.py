import os
import requests
import json
import pandas as pd

ROOT_DIR_LOCAL = os.path.abspath(os.curdir)
LOCAL_FILE_SYS = ROOT_DIR_LOCAL + '/data/raw/hist-rentals-2/'

def get_rentals_data(start_date, end_date):
    ###############################################################
    # Moby Bikes Data
    # https://data.gov.ie/dataset/moby-bikes
    ###############################################################

    # Moby API
    # URL: https://data.smartdublin.ie/mobybikes-api/

    #parameters = None
    parameters = {
        "start": start_date,
        "end": end_date
    }

    headers={'content-type': 'application/json', 'accept': 'application/json'}
    baseurl = "https://data.smartdublin.ie/mobybikes-api/"

    historical_url = f'{baseurl}historical/'
    api_response_moby = requests.get(historical_url, headers=headers, params=parameters)
    moby_json_str = api_response_moby.text
    return json.loads(moby_json_str)

start_date = '2022-08-12'
end_date = '2022-08-13'
rentals = get_rentals_data(start_date, end_date)
rentals_df = pd.DataFrame(rentals)
fileName = f'moby-bikes-{start_date}-{end_date}.csv'
rentals_df.to_csv(LOCAL_FILE_SYS + fileName, index=False)
print(f'{start_date} - {end_date} | {rentals_df.shape}')
