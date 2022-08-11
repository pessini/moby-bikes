import json
from sys import prefix
from datetime import datetime
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import numpy as np
import os

ROOT_DIR_LOCAL = os.path.abspath(os.curdir)

def times_of_day(hour: int) -> str:
    '''
    Receives an hour and returns the time of day
    Morning: 7:00 - 11:59
    Afternoon: 12:01 - 17:59
    Evening: 18:00 - 22:59
    Night: 23:00 - 06:59
    '''

    conditions = [
        (hour < 7), # night 23:00 - 06:59
        (hour >= 7) & (hour < 12), # morning 7:00 - 11:59
        (hour >= 12) & (hour < 18), # afternoon 12:01 - 17:59
        (hour >= 18) & (hour < 23) # evening 18:00 - 22:59
    ]
    values = ['Night', 'Morning', 'Afternoon', 'Evening']
    
    return str(np.select(conditions, values,'Night'))

def rain_intensity_level(rain: float) -> str:
    '''
    Receives a rain intensity (in mm) and returns the rain intensity level
    '''

    conditions = [
        (rain == 0.0), # no rain
        (rain <= 0.3), # drizzle
        (rain > 0.3) & (rain <= 0.5), # light rain
        (rain > 0.5) & (rain <= 4), # moderate rain
        (rain > 4) # heavy rain
        ]
    values = ['no rain', 'drizzle', 'light rain', 'moderate rain','heavy rain']
    
    return str(np.select(conditions, values))

def feat_eng_weather(data: list) -> list:
    '''
    Receives a List with tuples weather data from JSON file 
    and returns a new list with feature engineered data
        0 - ['temperature'],
        1 - ['windSpeed'], 
        2 - ['humidity'], 
        3 - ['rainfall'],
        4 - ['date'], 
        5 - ['reportTime']
    Returns:
        (Date, Hour, TimeOfDay, Temperature, WindSpeed, Humidity, Rain, RainLevel)
    '''
    return [(str.strip(i[4]),
             str.strip(i[5].split(':')[0]), 
             times_of_day(int( str.strip(i[5].split(':')[0]) )),
             str.strip(i[0]), 
             str.strip(i[1]), 
             str.strip(i[2]), 
             str.strip(i[3]), 
             rain_intensity_level(np.float( str.strip(i[3]) ))) for i in data]
    
def process_files_data(fileType='rentals') -> list:
    
    if fileType == 'rentals':
        filePrefix = 'moby_'
    elif fileType == 'weather':
        filePrefix = 'weather_'
        
    files_in_bucket = f'{ROOT_DIR_LOCAL}/src/lambda_data/'
    
    
    all_data=[]
    
    for filename in os.listdir(files_in_bucket):
        f = os.path.join(files_in_bucket, filename)
        if os.path.isfile(f):
            f = open (f, "r")

            json_data = json.loads(f.read())
            if fileType == 'rentals':

                list_rdata = [(i['LastRentalStart'], 
                                i['BikeID'], 
                                i['Battery'], 
                                i['LastGPSTime'], 
                                i['Latitude'], 
                                i['Longitude']) for i in json_data]
                all_data.extend(list_rdata)
                
            elif fileType == 'weather':
                
                list_wdata = [(i['temperature'],
                                i['windSpeed'], 
                                i['humidity'], 
                                i['rainfall'],
                                i['date'], 
                                i['reportTime']) for i in json_data]
                
                list_wdata = feat_eng_weather(list_wdata)
                all_data.extend(list_wdata)
                
            else:
                print('Else')
            
            f.close()

    return all_data
    

# rentals_data = process_files_data(fileType='rentals')
weather_data = process_files_data(fileType='weather')
