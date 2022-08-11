import json
from sys import prefix
from datetime import datetime
from typing import List
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import boto3
import numpy as np

s3_client = boto3.client("s3")
S3_BUCKET = "moby-bikes-rentals"

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor

def get_file_tag(fileName):
    # Example of tag 'TagSet': [{'Key': 'rental', 'Value': ''}]
    # If object has not tagging, setting tag = None
    try:
        tag = s3_client.get_object_tagging(Bucket=S3_BUCKET, Key=fileName)['TagSet'][0]['Key']
    except Exception:
        tag = None
        
    return tag

def remove_file_tag(fileName):
    s3_client.delete_object_tagging(Bucket=S3_BUCKET,Key=fileName)

def add_file_tag(fileName, tag):
    try:
        today_dt = datetime.now()
        today_dt_str = today_dt.strftime("%Y-%m-%d")
        new_tag = {'TagSet': [{'Key': tag, 'Value': today_dt_str}]}
        s3_client.put_object_tagging(Bucket=S3_BUCKET, Key=fileName, Tagging=new_tag)
        return True
    except Exception:
        return False
    
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
        
    files_in_bucket = s3_client.list_objects(Bucket=S3_BUCKET, Prefix=filePrefix)
    
    all_data=[]
    if 'Contents' in files_in_bucket:
        count_er = 0
        
        for v in files_in_bucket['Contents']:
            
            tag = get_file_tag(v['Key'])
            
            print(v['Key'])
            # if not tag: # if object is not tagged, needs to be processed
                
            obj = s3_client.get_object(Bucket=S3_BUCKET, Key=v['Key'])
            json_data = json.loads(obj['Body'].read().decode('utf-8'))

            print(count_er)
            count_er += 1

            if fileType == 'rentals':
                
                print('Rental IF')
                
                list_rdata = [(i['LastRentalStart'], 
                                i['BikeID'], 
                                i['Battery'], 
                                i['LastGPSTime'], 
                                i['Latitude'], 
                                i['Longitude']) for i in json_data]
                all_data.extend(list_rdata)
                
            elif fileType == 'weather':
                
                print('Weather IF')
                
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

    print('Test----Test')
    print(all_data)
    return all_data
    

def lambda_handler(event, context):  # sourcery skip: use-named-expression

    # conn, cursor = openDB_connection()
    
    rentals_data = process_files_data(fileType='rentals')
    weather_data = process_files_data(fileType='weather')

    # try:

    #     rentals_data = process_files_data(fileType='rentals')
    #     if rentals_data:
    #         print(rentals_data)        
    #         # stmt = """INSERT INTO mobybikes.rawRentals (LastRentalStart, BikeID, Battery, LastGPSTime, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s)"""
    #         # cursor.executemany(stmt,rentals_data)
    #         # None if conn.autocommit else conn.commit()
    #         # print(cursor.rowcount, "record(s) inserted.")
    #     else:
    #         print('No Rental files were found to be processed!')

    # except mysql.connector.Error as error:

    #     print(f"Failed to update record to database rollback: {error}")
    #     # reverting changes because of exception
    #     # conn.rollback()

    # finally:
        
    #     # cursor.callproc('SP_RENTALS_PROCESSING')
        
    #     try:

    #         # weather_data = process_files_data(fileType='weather')
        
    #         if weather_data:
    #             print(weather_data)
    #             print('Weather files to be processed!')
    #             # stmt = """INSERT INTO mobybikes.Weather (Date, Hour, TimeOfDay, Temperature, WindSpeed, Humidity, Rain, RainLevel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    #             # cursor.executemany(stmt,rentals_data)
    #             # None if conn.autocommit else conn.commit()
    #         else:
    #             print('No Weather files were found to be processed!')

    #     except mysql.connector.Error as error:

    #         print(f"Failed to update record to database rollback: {error}")
    #         # reverting changes because of exception
    #         # conn.rollback()

    # closing database connection.
    # cursor.close()
    # conn.close()
