import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
import xgboost as xgb
import pickle
from sklearn import metrics
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import category_encoders as ce
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import boto3
import json

s3_client = boto3.client("s3")
S3_BUCKET = "moby-bikes-rentals"
MODEL_FOLDER = 'prod-model/'

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor


#------- Load XGBoost Model ---------#
pipe_filename = f"{MODEL_FOLDER}xgb_pipeline.pkl"
xgb_pipe = pickle.load(open(pipe_filename, "rb"))
def predict(df):
    return xgb_pipe.predict(df)

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


def main():
    
    conn, cursor = openDB_connection()
    
    df_forecast = pd.DataFrame()
    predicted = pd.Series( xgb_pipe.predict(df_forecast), name='predicted') # round up to nearest integer
    predicted = predicted.map(round_up)
    df_forecast['predicted'] = predicted.values

if __name__ == '__main__':
    main()  