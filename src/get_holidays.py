import json
import requests
from urllib.parse import quote_plus
import mysql.connector
import datetime
from mysql_conn import mysqldb as mysqlcredentials
import pandas as pd
import numpy as np

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor

def get_season(date: pd.DatetimeIndex) -> str:
    '''
        Receives a date and returns the corresponded season
        0 - Spring | 1 - Summer | 2 - Autumn | 3 - Winter
        Vernal equinox(about March 21): day and night of equal length, marking the start of spring
        Summer solstice (June 20 or 21): longest day of the year, marking the start of summer
        Autumnal equinox(about September 23): day and night of equal length, marking the start of autumn
        Winter solstice (December 21 or 22): shortest day of the year, marking the start of winter
    '''
    Y = 2000 # dummy leap year to allow input X-02-29 (leap day)
    seasons = [('Winter', (datetime.datetime(Y,  1,  1),  datetime.datetime(Y,  3, 20))),
            ('Spring', (datetime.datetime(Y,  3, 21),  datetime.datetime(Y,  6, 20))),
            ('Summer', (datetime.datetime(Y,  6, 21),  datetime.datetime(Y,  9, 22))),
            ('Autumn', (datetime.datetime(Y,  9, 23),  datetime.datetime(Y, 12, 20))),
            ('Winter', (datetime.datetime(Y, 12, 21),  datetime.datetime(Y, 12, 31)))]
    date = date.replace(year=Y)
    return next(season for season, (start, end) in seasons if start <= date <= end)

def get_holiday_data(year: str) -> pd.DataFrame:
    url = "https://calendarific.com/api/v2/holidays/"
    parameters = {"api_key": '45f3218e321b77bf8ae47b5680283784344b5d4f', "country": 'ie', "year": year}

    response = requests.get(url, params=parameters)
    irishcalendar = response.json()
    holidays = []
    for irishday in irishcalendar.get('response').get('holidays'):
        item = {'date': irishday['date']['iso'], 'country': irishday['country']['name'], 'name': irishday['name'], 'type': irishday['type'][0]}

        holidays.append(item)
    df_holidays = pd.DataFrame(holidays)
    return df_holidays[df_holidays['type'] == 'National holiday']

def get_day_of_week_number(date: pd.DatetimeIndex) -> int:
    return date.dayofweek

def get_day_of_week_str(date: pd.DatetimeIndex) -> str:
    return date.day_name()

# working day (Monday=0, Sunday=6)
# from 0 to 4 or monday to friday and is not holiday
def isWorkingDay(date: pd.DatetimeIndex) -> bool:
    return (get_day_of_week_number(date) < 5)

def isHoliday(dt_tocheck: pd.DatetimeIndex, df_holidays: pd.DataFrame) -> bool:
    return df_holidays['date'].isin([dt_tocheck.strftime("%Y-%m-%d")]).any()

def generate_date_info(df_holidays: pd.DataFrame, start_date: datetime.datetime , end_date: datetime.datetime) -> list:
    '''
        Receives a start and end date and returns a list of dictionaries with the following structure:
         (Date, DayofWeek, Holiday, WorkingDay, Season)
    '''

    dt = start_date
    step = datetime.timedelta(days=1)
    result = []

    while dt < end_date:
        dt_pandas = pd.to_datetime(dt)
        holiday = isHoliday(dt_pandas, df_holidays)
        working_day = False if holiday else isWorkingDay(dt_pandas)
        row = (dt.strftime('%Y-%m-%d'), get_day_of_week_number(dt_pandas), int(holiday), int(working_day), get_season(dt_pandas))
        result.append(row)
        dt += step

    return result

conn, cursor = openDB_connection()

holiday_2020 = get_holiday_data(year='2020')
holiday_2021 = get_holiday_data(year='2021')
holiday_2022 = get_holiday_data(year='2022')
holiday_2023 = get_holiday_data(year='2023')
holidays = pd.concat([holiday_2020, holiday_2021, holiday_2022, holiday_2023])

try:

    data_generated = generate_date_info(holidays, datetime.datetime(2020, 9, 18), datetime.datetime(2022, 12, 31))
    stmt = """INSERT INTO mobybikes.Day_Info (Date, DayofWeek, Holiday, WorkingDay, Season) VALUES (%s, %s, %s, %s, %s)"""
    cursor.executemany(stmt,data_generated)
        
    None if conn.autocommit else conn.commit()
    print(cursor.rowcount, "record(s) inserted.")

except mysql.connector.Error as error:
    
    print(f"Failed to update record to database rollback: {error}")
    conn.rollback()
    
cursor.close()
conn.close()