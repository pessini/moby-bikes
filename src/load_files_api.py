import pandas as pd
from datetime import datetime, timedelta
import os
import requests
import json
import boto3

s3_client = boto3.client("s3")
LOCAL_FILE_SYS = "/tmp"
S3_BUCKET = "moby-bikes-rentals"

today_dt = datetime.now()
today_dt_str = today_dt.strftime("%Y-%m-%d")
yesterday_dt = today_dt - timedelta(days=1)
yesterday_dt_str = yesterday_dt.strftime("%Y-%m-%d")

###############################################################
# Dublin Airport Yesterday Data
# https://data.gov.ie/dataset/yesterdays-weather-dublin-airport
###############################################################

# Download CSV
# URL: https://www.met.ie/latest-reports/observations/download/Dublin-Airport/yesterday

# API (sometimes is not working) - 504 Gateway Timeout 
# Checking alternative with CSV file
# URL: https://prodapi.metweb.ie/observations/dublin/yesterday

def format_hour(hour) -> int:
    '''
    Receives a string of the form 'HH:MM' and returns a integer with the hour
    '''
    hour_str = hour.split(':')
    return int(hour_str[0])

def key_exists(mykey, mybucket):
    if result := s3_client.list_objects_v2(Bucket=mybucket, Prefix=mykey):
        return 'Contents' in result

headers={'content-type': 'application/json', 'accept': 'application/json'}

WEATHER_DATA_API_URL = "https://prodapi.metweb.ie/observations/dublin/yesterday"
WEATHER_DATA_CSV_URL = 'https://www.met.ie/latest-reports/observations/download/Dublin-Airport/yesterday'
# ROOT_DIR_LOCAL = os.path.abspath(os.curdir)

def get_weather_data():
     
    try:
        
        api_response = requests.get(WEATHER_DATA_API_URL, headers=headers)
        json_str = api_response.text
        parse_json = json.loads(json_str)

        if api_response:
            weather_filename = f'{yesterday_dt_str}.json'
        else:
            weather_filename = f'{yesterday_dt_str}_error.json'

        with open(LOCAL_FILE_SYS + "/" + weather_filename, 'w', encoding='utf-8') as f:
            json.dump(parse_json, f, ensure_ascii=False, indent=4)
                
    except Exception:
        
        try:
            
            dubairport_yesterday = pd.read_csv(WEATHER_DATA_CSV_URL)
            dubairport_yesterday.columns = ['time', 'report', 'temp', 'wdsp', 'wind_gust', 'wind_direction', 'rain', 'pressure']
            dubairport_yesterday['time'] = dubairport_yesterday['time'].apply(format_hour)
            dubairport_yesterday.drop(['report', 'wind_gust', 'wind_direction', 'pressure'], axis=1, inplace=True)
            weather_filename = f'{yesterday_dt_str}.csv'
            dubairport_yesterday.to_csv(LOCAL_FILE_SYS + "/" + weather_filename, index=False)
                
        except Exception as e:
            
            weather_filename = f'{yesterday_dt_str}_error.txt'
            with open(LOCAL_FILE_SYS + "/" + weather_filename, 'w') as f:
                f.write(e.__str__())
        
    finally:
        
        if key_exists("weather_" + weather_filename, S3_BUCKET):
            print("Weather data file already in S3 bucket!")
        else:
            s3_client.upload_file(LOCAL_FILE_SYS + "/" + weather_filename, S3_BUCKET, "weather_" + weather_filename)
    
def get_rentals_data():
    ###############################################################
    # Moby Bikes Data
    # https://data.gov.ie/dataset/moby-bikes
    ###############################################################

    # Moby API
    # URL: https://data.smartdublin.ie/mobybikes-api/

    #parameters = None
    parameters = {
        "start": yesterday_dt_str,
        "end": today_dt_str
    }

    baseurl = "https://data.smartdublin.ie/mobybikes-api/"
    # last_reading_url = f'{baseurl}last_reading/'

    historical_url = f'{baseurl}historical/'
    api_response_moby = requests.get(historical_url, headers=headers, params=parameters)
    moby_json_str = api_response_moby.text
    moby_parse_json = json.loads(moby_json_str)

    if api_response_moby:
        moby_json_filename = f'{yesterday_dt_str}.json'
    else:
        moby_json_filename = f'{yesterday_dt_str}_error.json'

    with open(LOCAL_FILE_SYS + "/" + moby_json_filename, 'w', encoding='utf-8') as f:
        json.dump(moby_parse_json, f, ensure_ascii=False, indent=4)
    
    if key_exists("moby_" + moby_json_filename, S3_BUCKET):
        print("Moby rentals data file already in S3 bucket!")
    else:
        s3_client.upload_file(LOCAL_FILE_SYS + "/" + moby_json_filename, S3_BUCKET, "moby_" + moby_json_filename)
        
        
def lambda_handler(event, context):
    '''
    Loads the weather data from the API and saves it to S3
    '''
    get_weather_data()
    get_rentals_data()