import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# def parse_xml(xml_data):
#   # Initializing soup variable
#     soup = BeautifulSoup(xml_data, 'lxml')
#   # Iterating through time tag and extracting elements
#     all_items = soup.find_all('time')
#     forecast_df = pd.DataFrame(columns=['temp', 'wdsp', 'rhum', 'rain'])

#     for item in all_items:

#         datetime_object = pd.to_datetime(item.get('to'))

#         if item.location.find('temperature'):
#             temp = item.location.temperature.get('value')

#         if item.location.find('windspeed'):
#             wdsp = item.location.windspeed.get('mps')

#         if item.location.find('humidity'):
#             humidity = item.location.humidity.get('value')
        
#         row = {
#             'temp': temp,
#             'rhum': humidity,
#             'wdsp': wdsp,
#         }

#         if item.location.find('precipitation'):
#             precipitation = item.location.precipitation.get('value')
    
#         if datetime_object in forecast_df.index:
#             forecast_df.loc[datetime_object]['rain'] = precipitation
#         else:
#             forecast_df = pd.concat([pd.DataFrame(row, columns=forecast_df.columns, index=[datetime_object]),forecast_df])

#     return forecast_df.sort_index()

today_dt = datetime.now()
today_dt_str = today_dt.strftime("%Y-%m-%d")
yesterday_dt = today_dt - timedelta(days=1)
yesterday_dt_str = yesterday_dt.strftime("%Y-%m-%d")
# http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=<LATITUDE>;long=<LONGI-TUDE>;from=2018-11-10T02:00;to=2018-11-12T12:00
# http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=54.7210798611;long=-8.7237392806
# http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=53.4264;long=-6.2499;from=2022-07-14T00:00;to=2022-07-15T00:00

date_str = f";from={yesterday_dt_str}T00:00;to={today_dt_str}T00:00"
URL_WEATHER_API = "http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=53.4264;long=-6.2499"+date_str
print(URL_WEATHER_API)
api_response = requests.get(URL_WEATHER_API).content
print(api_response)
# parse_json = json.loads(json_str)

# df_xml = parse_xml(response)


###############################################################
# Dublin Airport Yesterday Data
# https://data.gov.ie/dataset/yesterdays-weather-dublin-airport
###############################################################

# Download CSV
# URL: https://www.met.ie/latest-reports/observations/download/Dublin-Airport/yesterday

# API (not working) - 504 Gateway Timeout
# URL: https://prodapi.metweb.ie/observations/dublin/yesterday