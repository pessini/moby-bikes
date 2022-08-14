import json
from datetime import datetime
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import numpy as np
import os
import pandas as pd

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

def feat_eng_weather(data: pd.DataFrame) -> list:
    '''
    Receives a DataFrame with weather data
    and returns a new DF with feature engineered data
        0 - ['datetime'],
        1 - ['rain'], 
        2 - ['temp'], 
        3 - ['rhum'],
        4 - ['wdsp']
    Returns:
        (Date, Hour, TimeOfDay, Temperature, WindSpeed, Humidity, Rain, RainLevel)
    '''
    
    data['dt'] = pd.to_datetime(data['date'].dt.date).dt.strftime('%Y-%m-%d')
    data['hour'] = data['date'].dt.hour
    data.drop(columns='date', axis=1, inplace=True)
    data.rename(columns={'dt':'date'},inplace=True)

    data['timesofday'] = data['hour'].map(times_of_day)
    data['rainfall_intensity'] = data['rain'].map(rain_intensity_level)
    
    data = data[['date', 'hour', 'timesofday', 'temp', 'wdsp', 'rhum', 'rain', 'rainfall_intensity']]

    return list(data.itertuples(index=False, name=None))

def force_integer(input_number):
    try:
        tmp = int(input_number)
    except Exception:
        tmp = 0
    return tmp

    
conn, cursor = openDB_connection()

start_date, end_date = '2020-09-18', '2022-07-31'
# start_date, end_date = '2022-07-29', '2022-07-31'

dublin_airport_weather_hourly = pd.read_csv(f'{ROOT_DIR_LOCAL}/src/lambda_data/processed/hly532.csv', low_memory=False, parse_dates=['date'])
recent_dubairport_data = dublin_airport_weather_hourly.copy()
columns_to_drop = ['ind','ind.1','ind.2','ind.3','vappr','msl','ind.4','wddir','ww','w','sun','vis','clht','clamt','wetb','dewpt']
weather_data = recent_dubairport_data.drop(columns=columns_to_drop)
mask = (weather_data['date'] >= start_date) & (weather_data['date'] <= end_date)
weather_data = weather_data.loc[mask]

# print(weather_data.info())
# print(weather_data.head())
# print(weather_data.tail())

weatherDB_data = feat_eng_weather(weather_data)
# print(weatherDB_data)

try:

    if weatherDB_data:

        stmt = """INSERT INTO mobybikes.Weather (Date, Hour, TimeOfDay, Temperature, WindSpeed, Humidity, Rain, RainLevel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.executemany(stmt,weatherDB_data)

        None if conn.autocommit else conn.commit()
        print(len(weatherDB_data), "record(s) inserted.")

    else:
        print('No Weather files were found to be processed!')

except mysql.connector.Error as error:

    print(f"Failed to update record to database rollback: {error}")
    # reverting changes because of exception
    conn.rollback()

# closing database connection.
cursor.close()
conn.close()