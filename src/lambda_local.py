import json
from sys import prefix
from datetime import datetime
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import numpy as np
import os
import shutil

ROOT_DIR_LOCAL = os.path.abspath(os.curdir)

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor

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
    return [(convert_date(str.strip(i[4])),
             str.strip(i[5].split(':')[0]), 
             times_of_day(int( str.strip(i[5].split(':')[0]) )),
             force_integer( str.strip(i[0]) ), 
             force_integer( str.strip(i[1]) ), 
             force_integer( str.strip(i[2]) ), 
             str.strip(i[3]), 
             rain_intensity_level(float( str.strip(i[3]) ))) for i in data]

def convert_date(date_weather: str) -> str:
    '''
    Receives a date 'dd-mm-yyyy' and returns a date like 'yyyy-mm-dd'
    '''
    return datetime.strptime(date_weather, "%d-%m-%Y").strftime("%Y-%m-%d")

def get_date_from_filename(filename: str) -> str:
    '''
    Receives a filename and returns the date from the filename
    '''
    filename = filename.split('.')[0]
    return filename.split('_')[1]

def force_integer(input_number):
    try:
        tmp = int(input_number)
    except Exception:
        tmp = 0
    return tmp
    
def process_files_data(fileType='rentals') -> list:
    
    if fileType == 'rentals':
        filePrefix = 'moby_'
    elif fileType == 'weather':
        filePrefix = 'weather_'
        
    files_in_bucket = f'{ROOT_DIR_LOCAL}/src/lambda_data/'
    
    all_data = []
    files_queued = []
    
    for filename in os.listdir(files_in_bucket):
        f = os.path.join(files_in_bucket, filename)
        
        if os.path.isfile(f) and filename.startswith(filePrefix):
            
            files_queued.append(filename)

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
            
            f.close()
            
    return all_data, files_queued
    

conn, cursor = openDB_connection()

try:

    rentals_data, rfiles_queued = process_files_data(fileType='rentals')

    if rentals_data:

        stmt = """INSERT INTO mobybikes.rawRentals (LastRentalStart, BikeID, Battery, LastGPSTime, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.executemany(stmt,rentals_data)

        if rfiles_queued:
            for fileName in rfiles_queued:
                shutil.move(f'{ROOT_DIR_LOCAL}/src/lambda_data/{fileName}', f'{ROOT_DIR_LOCAL}/src/lambda_data/processed/{fileName}')
                
        None if conn.autocommit else conn.commit()
        print(cursor.rowcount, "record(s) inserted.")

    else:
        print('No Rental files were found to be processed!')

except mysql.connector.Error as error:
    
    print(f"Failed to update record to database rollback: {error}")
    conn.rollback()
    
finally:
    
    cursor.callproc('SP_RENTALS_PROCESSING')
    None if conn.autocommit else conn.commit()

    try:

        weather_data, wfiles_queued = process_files_data(fileType='weather')

        if weather_data:

            stmt = """INSERT INTO mobybikes.Weather (Date, Hour, TimeOfDay, Temperature, WindSpeed, Humidity, Rain, RainLevel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.executemany(stmt,weather_data)

            if wfiles_queued:
                for fileName in wfiles_queued:
                    args = (get_date_from_filename(fileName),)
                    cursor.callproc('SP_LOG_WEATHER_EVENTS', args)
                    shutil.move(f'{ROOT_DIR_LOCAL}/src/lambda_data/{fileName}', f'{ROOT_DIR_LOCAL}/src/lambda_data/processed/{fileName}')

            None if conn.autocommit else conn.commit()

        else:
            print('No Weather files were found to be processed!')

    except mysql.connector.Error as error:

        print(f"Failed to update record to database rollback: {error}")
        # reverting changes because of exception
        conn.rollback()

    # closing database connection.
    cursor.close()
    conn.close()
