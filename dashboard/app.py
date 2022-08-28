import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import altair as alt
from PIL import Image
import socket
import mysql.connector
from datetime import datetime, timedelta
import xgboost as xgb
import pickle
from sklearn import metrics
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import category_encoders as ce
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import requests
from bs4 import BeautifulSoup

# -------------- SETTINGS --------------
page_title = "Moby Bikes - Analytical Dashboard & Demand Forecasting"
page_subtitle = "Analytical Dashboard & Demand Forecasting"
page_icon = ":bike:"  # emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
layout = "centered" # Can be "centered" or "wide". In the future also "dashboard", etc.

BUSINESS_RULES_SQL = """
-- --------------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS mobybikes.TEMP_completed_rentals;
-- DROP TEMPORARY TABLE IF EXISTS completed_rentals;

-- --------------------------------------------------------------------------------------------------
-- Function to calculate rentals duration
/** 
    Assumption: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new 
    bike rental starts the duration in *minutes* will be calculated by: RentalDuration = LastGPSTime - LastRentalStart
*/
-- --------------------------------------------------------------------------------------------------
USE mobybikes;

DROP FUNCTION IF EXISTS FN_RENTAL_DURATION;
DELIMITER //
CREATE FUNCTION FN_RENTAL_DURATION(LAST_GPSTIME DATETIME, RENTAL_START DATETIME) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE duration BIGINT DEFAULT 0;
    
    SET duration = TIMESTAMPDIFF(MINUTE, RENTAL_START, LAST_GPSTIME);
    
    IF duration < 0 THEN
        SET duration = 0;
    END IF;
    
    RETURN duration;
END //
DELIMITER ;

DROP FUNCTION IF EXISTS FN_TIMESOFDAY;
DELIMITER //
CREATE FUNCTION FN_TIMESOFDAY(rental_date DATETIME) 
RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
    DECLARE timeofday VARCHAR(10);
    DECLARE rental_hour INT;
    
    SET rental_hour := HOUR(rental_date);
    
    IF rental_hour < 7 THEN
        SET timeofday := 'Night';
    ELSEIF rental_hour >= 7 AND rental_hour < 12 THEN
        SET timeofday := 'Morning';
    ELSEIF rental_hour >= 12 AND rental_hour < 18 THEN
        SET timeofday := 'Afternoon';
    ELSEIF rental_hour >= 18 AND rental_hour < 23 THEN
        SET timeofday := 'Evening';
    ELSE 
        SET timeofday := 'Night';
    END IF;

    RETURN timeofday;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_LOG_RENTAL_EVENTS;
DELIMITER //
CREATE PROCEDURE SP_LOG_RENTAL_EVENTS(
    IN rentals_processed INT,
    IN number_errors INT
)
BEGIN

    INSERT INTO mobybikes.Log_Rentals (`Date`, `Processed`, `Errors`)
    VALUES (NOW(), rentals_processed, number_errors);
    
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_GET_TOTAL_RENTALS_TO_PROCESS;
DELIMITER //
CREATE PROCEDURE SP_GET_TOTAL_RENTALS_TO_PROCESS(OUT total_rentals INT)
BEGIN

    SELECT
        COUNT(*) INTO total_rentals
    FROM
    (
        SELECT 
            LastRentalStart,
            BikeID
        FROM
            mobybikes.rawRentals
        GROUP BY
            LastRentalStart, BikeID
    ) AS r;
    
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_GET_TOTAL_OPENED_RENTALS;
DELIMITER //
CREATE PROCEDURE SP_GET_TOTAL_OPENED_RENTALS(OUT opened_rentals INT)
BEGIN
    WITH CTE_OPENED_RENTALS AS (
        SELECT 
            r.LastRentalStart,
            r.BikeID,
            r.rent_rank
        FROM
        (
            SELECT 
                LastRentalStart,
                BikeID,
                RANK() OVER (PARTITION BY BikeID ORDER BY LastRentalStart DESC) rent_rank
            FROM
                mobybikes.rawRentals
            GROUP BY
                LastRentalStart, BikeID
        ) r
        WHERE rent_rank = 1
    )
    -- returning the number of rentals NOT completed
    SELECT COUNT(*) INTO opened_rentals FROM CTE_OPENED_RENTALS;
    
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_COMPLETED_RENTALS;
DELIMITER //
CREATE PROCEDURE SP_COMPLETED_RENTALS(OUT rentals_to_process INT)
BEGIN
    -- The ERROR 1137 is a known issue with MySQL that hasn’t got any fix since 2008.
    -- Not creating a temporary table because of an issue referenced above.

    DROP TABLE IF EXISTS TEMP_completed_rentals;
    
    CREATE TABLE TEMP_completed_rentals
    SELECT 
        r.LastRentalStart,
        r.BikeID,
        r.rent_rank
    FROM
    (
        SELECT 
            LastRentalStart,
            BikeID,
            RANK() OVER (PARTITION BY BikeID ORDER BY LastRentalStart DESC) rent_rank
        FROM
            mobybikes.rawRentals
        GROUP BY
            LastRentalStart, BikeID
    ) r 
    WHERE rent_rank > 1;
    
    -- returning the number of rentals to be processed
    SELECT COUNT(*) INTO rentals_to_process FROM TEMP_completed_rentals;
    
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_CLEASING_PROCESSED_RENTALS;
DELIMITER //
CREATE PROCEDURE SP_CLEASING_PROCESSED_RENTALS()
BEGIN
    SET SQL_SAFE_UPDATES = 0;
    DELETE FROM mobybikes.rawRentals WHERE (LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals);
    DROP TABLE IF EXISTS TEMP_completed_rentals;
    SET SQL_SAFE_UPDATES = 1;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_COORDINATES;
DELIMITER //
CREATE PROCEDURE SP_COORDINATES()
BEGIN

    INSERT INTO mobybikes.Rentals_Coordinates (Date, BikeID, Latitude, Longitude)
    SELECT
        LastRentalStart,
        BikeID,
        Latitude,
        Longitude
    FROM
        mobybikes.rawRentals
    WHERE
        (LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals)
    AND
        (Latitude IS NOT NULL OR Longitude IS NOT NULL)
    AND
        (Latitude <> 0 OR Longitude <> 0);
    
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_RENTALS_PROCESSING;
DELIMITER //
CREATE PROCEDURE SP_RENTALS_PROCESSING()
BEGIN

    DECLARE total_completed_rentals, total_opened_rentals, rentals_to_process, number_errors INT;

    -- creates a temporary table and returns the total of completed rentals
    CALL SP_COMPLETED_RENTALS(total_completed_rentals);

    INSERT INTO mobybikes.Rentals (Date, BikeID, BatteryStart, BatteryEnd, Duration)
    WITH CTE_RENTAL_START_FINISH AS (
        SELECT
            t.LastRentalStart,
            t.BikeID,
            t.Battery,
            t.LastGPSTime,
            CASE 
                WHEN t.RN_RentalStart = 1 THEN 1
                ELSE 0
            END AS RentStarting
        FROM
            (SELECT
                LastRentalStart, BikeID, Battery, LastGPSTime,
                ROW_NUMBER() OVER(PARTITION BY LastRentalStart, BikeID ORDER BY LastGPSTime) AS RN_RentalStart,
                ROW_NUMBER() OVER(PARTITION BY LastRentalStart, BikeID ORDER BY LastGPSTime DESC) AS RN_RentalFinished
            FROM
                mobybikes.rawRentals
            WHERE
                (LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals) -- get only finished rentals from temp table
            ORDER BY
                BikeID,LastRentalStart ASC) t
        WHERE
            t.RN_RentalStart = 1 OR t.RN_RentalFinished = 1
    )
    SELECT
        LastRentalStart,
        BikeID,
        FLOOR (CAST( GROUP_CONCAT( CASE WHEN RentStarting = 1 THEN Battery ELSE NULL END) AS DECIMAL(12,1))) AS BatteryStart,
        FLOOR (CAST( GROUP_CONCAT( CASE WHEN RentStarting = 0 THEN Battery ELSE NULL END) AS DECIMAL(12,1))) AS BatteryEnd,
        -- ORDER BY RentStarting ASC so the first row to calculate would be with RentStarting = 0 (finished rental row)
        -- Not using IF because some rows have only one and then if there is only row with RentStarting=1, it will use that one
        FLOOR (CAST( GROUP_CONCAT( FN_RENTAL_DURATION(LastGPSTime,LastRentalStart) ORDER BY RentStarting ASC ) AS DECIMAL(12,1))) AS duration
    FROM 
        CTE_RENTAL_START_FINISH
    GROUP BY
        LastRentalStart, BikeID
    ORDER BY
        BikeID, LastRentalStart ASC;
        
    CALL SP_COORDINATES();

    -- returns the total of opened rentals (not to be processed yet)
    CALL SP_GET_TOTAL_OPENED_RENTALS(total_opened_rentals);
    CALL SP_CLEASING_PROCESSED_RENTALS();
    
    -- Get rentals that are left to process (it should be only opened rentals)
    CALL SP_GET_TOTAL_RENTALS_TO_PROCESS(rentals_to_process);
    
    -- if = 0 there is no error
    -- if > 0 there are some rentals left which weren't processed
    SET number_errors := rentals_to_process - total_opened_rentals;
    
    -- log the number of processed rentals and the number of errors occurred when processing them
    CALL SP_LOG_RENTAL_EVENTS(total_completed_rentals, number_errors);
        
END //
DELIMITER ;


-- --------------------------------------------------------------------------------------------------
-- WEATHER LOG
-- --------------------------------------------------------------------------------------------------
USE mobybikes;
DROP PROCEDURE IF EXISTS SP_LOG_WEATHER_EVENTS;
DELIMITER //
CREATE PROCEDURE SP_LOG_WEATHER_EVENTS(IN DATE_FILE CHAR(10))
BEGIN
    DECLARE weather_events, number_errors INT;

    SELECT COUNT(*) INTO weather_events FROM mobybikes.Weather WHERE DATE(`Date`) = STR_TO_DATE(DATE_FILE,'%Y-%m-%d');
    
    SET number_errors := 24 - weather_events; -- it should have been recorded 24 hours
    
    INSERT INTO mobybikes.Log_Weather (`Date`, `Processed`, `Errors`)
    VALUES (STR_TO_DATE(DATE_FILE,'%Y-%m-%d'), weather_events, number_errors);
    
END //
DELIMITER ;"""
#---------------------------------#
# Page layout
#---------------------------------#
# Page layout
st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
# 'https://github.com/pessini/moby-bikes/blob/main/dashboard/img/moby-logo.png?raw=true'
st.image('https://www.mobybikes.com/wp-content/uploads/2020/05/logo-1.png', use_column_width='never')
st.header(page_subtitle)
#---------------------------------

# --- HIDE STREAMLIT STYLE ---
hide_st_style = """
            <style>
            /*#MainMenu {visibility: hidden;}*/
            /*footer {visibility: hidden;}*/
            /* header {visibility: hidden;} */
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

#####################################################
##### Trick to hide table and dataframe indexes #####
# .row_heading.level0 {display:none}
# .blank {display:none}

# --- NAVIGATION MENU ---
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Demand Forecasting", "About"],
    icons=["bar-chart-fill", "graph-up-arrow", "journal-text"],  # https://icons.getbootstrap.com/
    orientation="horizontal",  # "horizontal" or "vertical"
)

#---------------------------------#

# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

# Perform query.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def host_is_local(hostname, port=None):
    """returns True if the hostname points to the localhost, otherwise False."""
    if port is None:
        port = 22  # no port specified, lets just use the ssh port
    hostname = socket.getfqdn(hostname)
    if hostname in ("localhost", "0.0.0.0"):
        return True
    localhost = socket.gethostname()
    localaddrs = socket.getaddrinfo(localhost, port)
    targetaddrs = socket.getaddrinfo(hostname, port)
    for (family, socktype, proto, canonname, sockaddr) in localaddrs:
        for (rfamily, rsocktype, rproto, rcanonname, rsockaddr) in targetaddrs:
            if rsockaddr[0] == sockaddr[0]:
                return True
    return False

# Check if it is local or remote
if socket.gethostname() == 'MacBook-Air-de-Leandro.local': # my mac
    APP_PATH = '/Users/pessini/Dropbox/Data-Science/moby-bikes/dashboard/'
else: # remote
    APP_PATH = '/app/moby-bikes/dashboard/'

def format_rental_duration(minutes):
    return timedelta(minutes=float(minutes)).__str__()

conn = init_connection()
#------- Load XGBoost Model ---------#
pipe_filename = f"{APP_PATH}xgb_pipeline.pkl"
xgb_pipe = pickle.load(open(pipe_filename, "rb"))
@st.cache
def predict(df):
    return xgb_pipe.predict(df)


#-------Demand Forecasting --------------------------#

@st.cache
def parse_xml(xml_data):
  # Initializing soup variable
    soup = BeautifulSoup(xml_data, 'lxml')
  # Iterating through time tag and extracting elements
    all_items = soup.find_all('time')
    forecast_df = pd.DataFrame(columns=['temp', 'wdsp', 'rhum', 'rain'])

    for item in all_items:

        datetime_object = pd.to_datetime(item.get('to'))

        if item.location.find('temperature'):
            temp = item.location.temperature.get('value')

        if item.location.find('windspeed'):
            wdsp = item.location.windspeed.get('mps')

        if item.location.find('humidity'):
            humidity = item.location.humidity.get('value')
        
        row = {
            'temp': temp,
            'rhum': humidity,
            'wdsp': wdsp,
        }

        if item.location.find('precipitation'):
            precipitation = item.location.precipitation.get('value')
    
        if datetime_object in forecast_df.index:
            forecast_df.loc[datetime_object]['rain'] = precipitation
        else:
            forecast_df = pd.concat([pd.DataFrame(row, columns=forecast_df.columns, index=[datetime_object]),forecast_df])

    return forecast_df.sort_index()

# Preprocessing
def preprocessor(predictors: list) -> ColumnTransformer:
    # Setting remainder='passthrough' will mean that all columns not specified in the list of “transformers” 
    #   will be passed through without transformation, instead of being dropped

    ##################### Categorical variables #####################
    all_cat_vars = ['timesofday','dayofweek','holiday','peak','hour','working_day','season','month']
    cat_vars = [categorical_var for categorical_var in all_cat_vars if categorical_var in predictors]

    # categorical variables
    cat_pipe = Pipeline([
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse=False))
    ])

    cat_encoder = 'cat', cat_pipe, cat_vars

    ##################### Numerical variables #####################
    all_num_vars = ['rain', 'temp', 'rhum','wdsp','temp_r']
    num_vars = [numerical_var for numerical_var in all_num_vars if numerical_var in predictors]

    num_pipe = Pipeline([
        ('scaler', StandardScaler())
    ])

    num_enconder =  'num', num_pipe, num_vars

    ##################### Ordinal variables #####################
    all_ord_vars = ['wind_speed_group','rainfall_intensity']
    ord_vars = [ordinal_var for ordinal_var in all_ord_vars if ordinal_var in predictors]

    ordinal_cols_mapping = []
    if 'wind_speed_group' in predictors:
        ordinal_cols_mapping.append(
            {"col":"wind_speed_group",    
            "mapping": {
                'Calm / Light Breeze': 0, 
                'Breeze': 1, 
                'Moderate Breeze': 2, 
                'Strong Breeze / Near Gale': 3, 
                'Gale / Storm': 4
            }}
        )

    if 'rainfall_intensity' in predictors:
        ordinal_cols_mapping.append(
            {"col":"rainfall_intensity",    
            "mapping": {
                'no rain': 0, 
                'drizzle': 1, 
                'light rain': 2, 
                'moderate rain': 3, 
                'heavy rain': 4
            }}
        )

    # ordinal variables
    ord_pipe = Pipeline([
        ('ordinal', ce.OrdinalEncoder(mapping=ordinal_cols_mapping))
    ])

    ord_enconder =  'ordinal', ord_pipe, ord_vars
    
    #################################################################################
    
    orig_vars = [var for var in predictors if var not in cat_vars and var not in num_vars and var not in ord_vars]
    orig_enconder = 'pass_vars', 'passthrough', orig_vars
     # ['temp_bin','rhum_bin']
    # ord_pipe = 'passthrough'

    transformers_list = []
    transformers_list.append(cat_encoder) if cat_vars else None
    transformers_list.append(ord_enconder) if ord_vars else None
    transformers_list.append(num_enconder) if num_vars else None
    # transformers_list.append(orig_enconder) if orig_vars else None
    
    return ColumnTransformer(transformers=transformers_list, 
                             remainder='drop')

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
    seasons = [('Winter', (datetime(Y,  1,  1),  datetime(Y,  3, 20))),
            ('Spring', (datetime(Y,  3, 21),  datetime(Y,  6, 20))),
            ('Summer', (datetime(Y,  6, 21),  datetime(Y,  9, 22))),
            ('Autumn', (datetime(Y,  9, 23),  datetime(Y, 12, 20))),
            ('Winter', (datetime(Y, 12, 21),  datetime(Y, 12, 31)))]
    date = date.replace(year=Y)
    return next(season for season, (start, end) in seasons if start <= date <= end)

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
    
    return np.select(conditions, values)

def get_day_of_week_number(date: pd.DatetimeIndex) -> int:
    return date.dayofweek

def get_day_of_week_str(date: pd.DatetimeIndex) -> str:
    return date.day_name()

def isWorkingDay(date: pd.DatetimeIndex) -> bool:
    return (get_day_of_week_number(date) < 5)

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
    
    return np.select(conditions, values,'Night')

def round_up(x):
    '''
    Helper function to round away from zero
    '''
    from math import copysign
    return int(x + copysign(0.5, x))

@st.cache(allow_output_mutation=True)
def generate_features(df):
    
    df['hour'] = df.index.hour
    df['date'] = pd.to_datetime(arg=df.index, utc=True, infer_datetime_format=True).date
    
    # day of the week
    df['dayofweek_n'] = df.index.map(get_day_of_week_number)
    df['dayofweek'] = df.index.map(get_day_of_week_str)

    # working day (Monday=0, Sunday=6)
    # from 0 to 4 or monday to friday and is not holiday
    df['working_day'] = df.index.map(isWorkingDay)
    df['timesofday'] = df['hour'].map(times_of_day)
    df['season'] = pd.to_datetime(df['date']).map(get_season)
    
    df['rainfall_intensity'] = pd.to_numeric(df['rain']).map(rain_intensity_level)

    return df

# Download Predictions dataframe as csv
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

def convert_minutes_to_hours(minutes):
    hour, min = divmod(minutes, 60)
    return f"{round_up(hour)}h {round_up(min)}m"

#---------------------------------#
@st.cache
def get_avg_duration() -> float:
    # CONCAT(FLOOR(AVG(Duration)/60),'h ', ROUND(MOD(AVG(Duration),60),0),'m') as average_duration
    # AVG(Duration) AS average_duration
    sqlquery = run_query("""SELECT 
                                AVG(Duration) AS average_duration
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE();""")
    return sqlquery[0][0]

# Indicator of how the metric changed
@st.cache
def get_avg_duration_delta() -> float:
    sqlquery = run_query("""SELECT 
                                AVG(Duration) AS average_duration
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 6 MONTH) AND DATE_SUB( CURDATE() , INTERVAL 3 MONTH);""")
    return sqlquery[0][0]

@st.cache
def get_total_rentals() -> int:
    sqlquery = run_query("""SELECT 
                                COUNT(*) AS total_rentals 
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE();""")
    return sqlquery[0][0]

# Indicator of how the metric changed
@st.cache
def get_total_rentals_delta() -> float:
    sqlquery = run_query("""SELECT 
                                COUNT(*) AS total_rentals  
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 6 MONTH) AND DATE_SUB( CURDATE() , INTERVAL 3 MONTH);""")
    return sqlquery[0][0]

@st.cache(allow_output_mutation=True)
def get_initial_battery():
    
    sqlquery = run_query("""SELECT
                                BatteryStart
                            FROM 
                                mobybikes.Rentals
                            WHERE
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE()
                            AND
                                (BatteryStart IS NOT NULL OR BatteryStart IS NOT NULL)
                            AND
                                (BatteryStart <> 0 OR BatteryStart <> 0);
                        """)
    return pd.DataFrame(sqlquery, columns=['start_battery'])

def group_battery_status():
    
    df = get_initial_battery()

    bins= [0,30,50,80,100]
    labels = ['< 30%','30% - 50%','50% - 80%','> 80%']
    df['battery_status'] = pd.cut(df['start_battery'], bins=bins, labels=labels, right=False)

    s = df.battery_status
    counts = s.value_counts()
    percent = s.value_counts(normalize=True)
    df_summary = pd.DataFrame({'counts': counts, 'per': percent}, labels)
    df_summary["% of Rentals"] = round((df_summary['per']*100),2).astype(str) + '%'
    df_summary.drop(['counts','per'], axis=1, inplace=True)
    df_summary = df_summary.reset_index().rename(columns={'index': 'Battery Status'})
    
    return df_summary

@st.cache
def get_hourly_total_rentals() -> pd.DataFrame:
    
    # DATE_FORMAT(`Date`, '%Y-%m-%d %H:00:00') AS date_rental,
    # HAVING DATE(date_rental) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE()
    
    sqlquery = run_query("""WITH CTE_HOURLY_TOTAL_RENTALS AS
                            (
                                SELECT 
                                    DATE_FORMAT(`Date`, '%Y-%m-%d %H:00:00') AS date_rental,
                                    COUNT(*) AS total_rentals,
                                    ROUND( AVG(Duration),2 ) AS hourly_avg_duration
                                FROM mobybikes.Rentals
                                GROUP BY date_rental
                            )
                            SELECT 
                                date_rental,
                                FN_TIMESOFDAY(date_rental) AS timeofday, 
                                DAYNAME(date_rental) AS day_of_week, 
                                total_rentals,
                                hourly_avg_duration
                            FROM 
                                CTE_HOURLY_TOTAL_RENTALS;
                        """)
    
    df = pd.DataFrame(sqlquery, columns=['date_rental', 'timeofday', 'day_of_week', 'total_rentals','hourly_avg_duration'])
    df['date'] = pd.to_datetime(arg=df['date_rental'], utc=True, infer_datetime_format=True).dt.date
    df['Season'] = pd.to_datetime(df['date']).map(get_season)
    df.drop(columns=['date'], inplace=True)

    return df
    
def group_hourly_rentals(df, group_by='Day of the Week', type='rentals'):

    if group_by == 'Period of the Day':
        shortgroup_by = ['timeofday']
    elif group_by == 'Day of the Week':
        shortgroup_by = ['day_of_week']
    else:
        shortgroup_by = group_by
        
    if type == 'avg_duration':
        df_grouped = df.groupby(shortgroup_by)['hourly_avg_duration'].mean().reset_index()
        df_grouped = df_grouped.rename(columns={shortgroup_by[0]: group_by})
    else:
 
        df_grouped = df.groupby(shortgroup_by)['total_rentals'].sum().reset_index()
        df_grouped['% of Rentals'] = df_grouped['total_rentals'] / df_grouped['total_rentals'].sum()
        df_grouped.drop(['total_rentals'], axis=1, inplace=True)
        df_grouped = df_grouped.reset_index().rename(columns={shortgroup_by[0]: group_by})
    
    return df_grouped

def plot_percentage_rentals(df, by='Day of the Week'):
    
    grouped_df = group_hourly_rentals(df, group_by=by)

    if by == 'Period of the Day':
        sort = ['Morning', 'Afternoon', 'Evening', 'Night']
        chart_title = 'Number of Rentals by Time of the Day'
    elif by == 'Season':
        sort = ['Autumn', 'Spring', 'Summer', 'Winter']
        chart_title = 'Number of Rentals by Season'
    else:
        sort = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        chart_title = 'Number of Rentals by Day of the Week'
    
    categorical_var = f'{by}:N'

    return alt.Chart(grouped_df)\
        .mark_bar()\
        .encode(x=alt.X('% of Rentals:Q', axis=alt.Axis(format='.0%', title='% of Rentals'), scale=alt.Scale(domain=(0, 1))), 
                y=alt.Y(categorical_var, sort=sort, axis=alt.Axis(title='')), 
                color=alt.Color(categorical_var, legend=None),
                opacity=alt.OpacityValue(0.9),
                tooltip=[categorical_var, alt.Tooltip('% of Rentals:Q', format=".2%")],)\
        .configure_axis(
            grid=True
        ).configure_view(
            strokeWidth=0
        ).properties(title=chart_title, width=600, height=400)
        
def plot_avg_duration_rentals(df, by='Day of the Week'):

    grouped_df = group_hourly_rentals(df, group_by=by, type='avg_duration')

    if by == 'Period of the Day':
        sort = ['Morning', 'Afternoon', 'Evening', 'Night']
        chart_title = 'Average duration (in minutes) of rentals across Times of the Day'
    elif by == 'Season':
        sort = ['Autumn', 'Spring', 'Summer', 'Winter']
        chart_title = 'Average duration (in minutes) of rentals across Seasons'
    else:
        sort = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        chart_title = 'Average duration (in minutes) of rentals across Days of the Week'
    
    categorical_var = f'{by}:N'
    
    return alt.Chart(grouped_df)\
        .mark_bar()\
        .encode(x=alt.X('hourly_avg_duration:Q', axis=alt.Axis(title='Average Duration of Rental (minutes)')), 
                y=alt.Y(categorical_var, sort=sort, axis=alt.Axis(title='')), 
                color=alt.Color(categorical_var, legend=None),
                opacity=alt.OpacityValue(0.9),
                tooltip=[categorical_var, alt.Tooltip('hourly_avg_duration:Q')],)\
        .configure_axis(
            grid=True
        ).configure_view(
            strokeWidth=0
        ).properties(title=chart_title, width=600, height=400)

# --- DASHBOARD ---
if selected == "Dashboard":

    # st.header('Dashboard')
    st.subheader('Dashboard')
    
    # --- METRICS ---
    col_metric_1, padding, col_metric_2 = st.columns((10,2,10))
    
    total_rentals = get_total_rentals()
    try:
        total_rentals_delta = total_rentals - get_total_rentals_delta()
    except Exception:
        total_rentals_delta = None
        
    col_metric_1.metric('Total Rentals (past 3 months)', total_rentals, total_rentals_delta)

    avg_duration = float(get_avg_duration())
    try:
        avg_duration_delta = avg_duration - float(get_avg_duration_delta())
    except Exception:
        avg_duration_delta = None

    col_metric_2.metric('Avg Rental Duration (past 3 months)', 
                        convert_minutes_to_hours(avg_duration), 
                        convert_minutes_to_hours(avg_duration_delta))
    
    st.markdown('---')

    # --- FILTERS ---
    with st.container():
        col_filter1, padding, col_filter2 = st.columns((10,2,10))
        with col_filter1:
            data_type = st.radio("What type of data would you like to show?", ('Number of Rentals', 'Duration of Rentals'))
        with col_filter2:
            groupby = st.selectbox('Group by:', ['Day of the Week', 'Period of the Day', 'Season'])
    
    hourly_rentals = get_hourly_total_rentals()
    st.markdown('---')
    
    # --- CHARTS ---
    if data_type == 'Number of Rentals':  
        st.altair_chart(plot_percentage_rentals(hourly_rentals, by=groupby), use_container_width=True)
    elif data_type == 'Duration of Rentals':
        st.altair_chart(plot_avg_duration_rentals(hourly_rentals, by=groupby), use_container_width=True)

    # --- TABLE with Battery Status ---
    with st.container():
        st.markdown("""##### Battery status when rental started""")
        # col_info_1, col_info_2 = st.columns((5,5))
        # with col_info_1:
        #     st.info('Data from the past three months')
        st.caption('Data from the past three months')
        battery_df = group_battery_status()
        st.table(battery_df.style.highlight_max(subset='% of Rentals', color='#c8fe00'))


def highlight_high_demand(val):
    color = '#c8fe00' if val > 10 else None
    return f'background-color: {color}'

#------- Demand Forecasting --------#
if selected == "Demand Forecasting":

    # st.header('Demand Forecasting')
    st.subheader("Predicting bike rentals demand")

    image = Image.open(f'{APP_PATH}img/met-eireann-long.png')
    st.image(image, use_column_width=False, width=30)

    st.write('''
    This web app shows the predicted bike rentals demand for the next hours based on Weather data.\n

    Weather Forecast API [URL](http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=53.4264;long=-6.2499)

    Source: [Met Éireann - The Irish Meteorological Service](https://www.met.ie/weather/forecast/)
    ''')

    URL_WEATHER_API = "http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=53.4264;long=-6.2499"
    response = requests.get(URL_WEATHER_API).content

    df_xml = parse_xml(response)
    df_forecast = generate_features(df_xml)

    predicted = pd.Series( xgb_pipe.predict(df_forecast), name='predicted') # round up to nearest integer
    predicted = predicted.map(round_up)
    df_forecast['predicted'] = predicted.values

    # limiting 15 hours forecast
    df_predictions = df_forecast[['date', 'hour', 'temp', 'rhum', 'wdsp', 'rainfall_intensity', 'predicted']][:15].reset_index(drop=True)
    df_predictions.columns = ['Date', 'Hour', 'Temperature', 'Relative Humidity', 'Wind Speed', 'Rainfall Intensity', 'Predicted Demand']
    st.caption('Highlighting hours with high demand (> 10)')
    st.table(df_predictions.style.applymap(highlight_high_demand, subset=['Predicted Demand']))

    # DOWNLOAD DATA Button
    csv_filename = str(df_predictions['Date'][0]) + '_' + str(df_predictions['Hour'][0]) + 'h_' + \
        str(df_predictions['Date'][len(df_predictions)-1]) + '_' + str(df_predictions['Hour'][len(df_predictions)-1]) + 'h_predictions.csv'
    # link to download dataframe as csv
    csv = convert_df(df_predictions)

    st.download_button(
        label="Download CSV File",
        data=csv,
        file_name=csv_filename,
        mime='text/csv',
    )

#---------------------------------#

if selected == "About":

    st.header('eBike Operations Optimization')

    st.write("""
            MOBY is an urban mobility company based in Ireland. 
            We deployed a fleet of shared electric bikes in the nation's capital.   

            ### In a nutshell (TL:DR)
            
            - Objectives and Problem Statement
            - Minimum Viable Product (MVP)
            - Research and explorations
            - Milestones and Results

            ### Problem Statement

            As part of Moby Operations, there is a role called "*eBike Operators*" which among its responsibilities are distributing and relocating 
            eBikes throughout the city, while performing safety checks and basic maintenance.

            To optimize operations, we want to predict the demand for the next hours based on weather data in order to decide whether to increase fleet or
            is safe to perform safefy checks and maintenance and even to collect bikes for repair.

            Several studies reported the influence of the weather on usage of bicycle sharing in many cities around the world [(See References)](#references).
            
            ### Data Pipeline

            
             """)

    # ![Data Pipeline](https://github.com/pessini/moby-bikes/blob/73f3d0af24a09b91fb1ca3c3d09edbf66273fdbf/documentation/data-pipeline.png?raw=true)

    moby_data_pipeline = Image.open(f'{APP_PATH}img/data-pipeline.png')
    st.image(moby_data_pipeline, use_column_width='always')

    with open(f'{APP_PATH}docs/Moby-Bikes-Data-Pipeline.pdf', "rb") as file:
        btn = st.download_button(label="Download as PDF",
                                data=file,
                                file_name='data-pipeline.pdf',
                                mime="application/pdf"
                                )

    st.write("""### Notebooks""")

    notebooks = {
        'Data Wrangling': 'https://pessini.me/moby-bikes/notebooks-html/01-data-wrangling.html',
        'Feature Engineering': 'https://pessini.me/moby-bikes/notebooks-html/02-feature-engineering.html',
        'Exploratory Data Analysis': 'https://pessini.me/moby-bikes/notebooks-html/03-exploratory-data-analysis.html',
        'Outlier Analysis': 'https://pessini.me/moby-bikes/notebooks-html/03A-outliers.html',
        'Linear Regression': 'https://pessini.me/moby-bikes/notebooks-html/04A-linear-regression.html',
        'Poisson Regression': 'https://pessini.me/moby-bikes/notebooks-html/04B-poisson.html',
        'Time Series Analysis': 'https://pessini.me/moby-bikes/notebooks-html/04C-time-series.html',
        'Modeling': 'https://pessini.me/moby-bikes/notebooks-html/05-modeling.html',
        'XGBoost': 'https://pessini.me/moby-bikes/notebooks-html/06-xgboost-model.html',
        'Model Evaluation': 'https://pessini.me/moby-bikes/notebooks-html/07-evaluation.html',
    }

    str_list = "".join(f"1. [{notebook}]({value}) \n" for notebook, value in notebooks.items())
    st.markdown(str_list)
    st.markdown("---")

    st.write("""### Database Business Rules""")
    
    db_model = Image.open(f'{APP_PATH}docs/DBDataModel.png')
    st.image(db_model, use_column_width='always')

    with st.expander("SQL code"):
        st.code(BUSINESS_RULES_SQL, language='sql')

    # for notebook in notebooks:
    #     with st.expander(notebook):
    #         components.iframe(notebooks[notebook], scrolling=True, height=600)
    
    st.write("""
            ### Design Docs to Data Science Project
            - Document the customer's business objectives.
            - Define how your data science project will meet their needs.
            - Set a vision for your project or product so that you can steer the team in the right direction.
            - Define clear evaluation metrics so that you can objectively determine whether the project was successful.
            - Conduct a cost-benefit analysis can help determine project go/no-go and prioritization against other potential projects.
            - Document what you are not looking to accomplish (beyond your project scope).
            
            #### How To Build Design Documents
            1. Objectives: Why are you building this?
            1. Minimum Viable Product: What's important for your audience?
            1. Research and explorations: What time and resources are available?
            1. Milestones and Results: What can and has been achieved?
            1. TL:DR (Too Long Didn't Read): What's the summary?""")
    
   
    components.iframe('https://whimsical.com/embed/Y81cDnnBwq5V4CHXjB6NpM@VsSo8s35WwyzAmPQfkttcU', scrolling=True, height=450)
    
    # experiment_tracker_ideas = pd.read_excel(f'{APP_PATH}docs/experiment_tracker.xlsx', sheet_name='Ideas', keep_default_na=False, na_values=['<NA>'])
    # st.table(experiment_tracker_ideas)
    # st.markdown("---")
    
    # experiment_tracker_exp = pd.read_excel(f'{APP_PATH}docs/experiment_tracker.xlsx', sheet_name='Experiments', keep_default_na=False, na_values=['<NA>'])
    # st.table(experiment_tracker_exp)
    # st.markdown("---")
    
    st.markdown("""
            ### References
            [1] Li, L., & McDonald, F. (2013). Automated self-organising vehicles for Barclays Cycle Hire. *Memetic Computing*, *5*(1), 35–48. [https://doi.org/10.1007/s12293-012-0101-3](https://doi.org/10.1007/s12293-012-0101-3)
    
            [2] Gebhart, K., & Noland, R. B. (2014). The impact of weather conditions on bikeshare trips in Washington, DC. *Transportation*, *41*(6), 1205–1225. [https://doi.org/10.1007/s11116-014-9540-7](https://doi.org/10.1007/s11116-014-9540-7)
            
            [3] Hotz, B. N. (2022, August 1). 15 Data Science Documentation Best Practices. Data Science Process Alliance. [https://www.datascience-pm.com/documentation-best-practices/](https://www.datascience-pm.com/documentation-best-practices/)
            
            [4] Tatan, V. (2022, January 1). The Undeniable Importance of Design Docs to Data Scientists. Medium. [https://towardsdatascience.com/the-undeniable-importance-of-design-docs-to-data-scientists-421132561f3c](https://towardsdatascience.com/the-undeniable-importance-of-design-docs-to-data-scientists-421132561f3c)
            """)


footer_github = """<div style='position: absolute; padding-top: 100px; width:100%;'>
<img title="GitHub Mark" src="https://github.com/pessini/avian-flu-wild-birds-ireland/blob/main/img/GitHub-Mark-64px.png?raw=true" 
style="height: 32px; padding-right: 15px" alt="GitHub Mark" align="left"> 
<a href='https://github.com/pessini/moby-bikes' target='_blank'>GitHub Repository</a> <br>Author: Leandro Pessini
</div>"""
st.markdown(footer_github, unsafe_allow_html=True)
