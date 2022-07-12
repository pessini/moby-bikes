import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn import metrics
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import xgboost as xgb
import pickle
import category_encoders as ce
import requests
from bs4 import BeautifulSoup
import base64
import socket
from PIL import Image

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
elif socket.gethostname() == 'lpessini-mbp': # work mac
    APP_PATH = '/Users/lpessini/TUDublin/moby-bikes/dashboard/'
else: # remote
    APP_PATH = '/app/moby-bikes/dashboard/'

#---------------------------------#
# Page layout
st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
	page_title='Moby Bikes - Demand Forecasting',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=f'{APP_PATH}img/favicon.webp',  # String, anything supported by st.image, or None.
)
#---------------------------------#

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
        # ('scaler', MinMaxScaler())
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
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df, filename=None):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    filename = filename or 'predictions.csv'
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'

st.header('Demand Forecasting')
st.subheader("Predicting bike rentals demand")
# predictors = ['temp','rhum','dayofweek','timesofday','wdsp','rainfall_intensity', 'working_day', 'hour', 'season']

pipe_filename = f"{APP_PATH}xgb_pipeline.pkl"
xgb_pipe = pickle.load(open(pipe_filename, "rb"))

# @st.cache
def predict(df):
    return xgb_pipe.predict(df)

# st.latex(r'''NRMSE = \frac{RSME}{y_{max} - y_{min}}''')

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

#####################################################
##### Trick to hide table and dataframe indexes #####
#####################################################
# CSS to inject contained in a string
hide_dataframe_row_index = """
            <style>
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)

# limiting 15 hours forecast
df_predictions = df_forecast[['date', 'hour', 'temp', 'rhum', 'wdsp', 'rainfall_intensity', 'predicted']][:15].reset_index(drop=True)
df_predictions.columns = ['Date', 'Hour', 'Temperature', 'Relative Humidity', 'Wind Speed', 'Rainfall Intensity', 'Predicted Demand']
st.table(df_predictions)

csv_filename = str(df_predictions['Date'][0]) + '_' + str(df_predictions['Hour'][0]) + 'h_' + \
    str(df_predictions['Date'][len(df_predictions)-1]) + '_' + str(df_predictions['Hour'][len(df_predictions)-1]) + 'h_predictions.csv'
# st.write(csv_filename)
# link to download dataframe as csv
st.markdown(filedownload(df_predictions, filename=csv_filename), unsafe_allow_html=True)