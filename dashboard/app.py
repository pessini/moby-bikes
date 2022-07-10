from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
from sklearn import metrics
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import xgboost as xgb
import pickle
import category_encoders as ce
import requests
from bs4 import BeautifulSoup

def parse_xml(xml_data):
  # Initializing soup variable
    soup = BeautifulSoup(xml_data, 'lxml')
  # Iterating through time tag and extracting elements
    all_items = soup.find_all('time')
    forecast_df = pd.DataFrame(columns=['temp', 'wdsp', 'rhum', 'rainfall_intensity'])

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
            forecast_df.loc[datetime_object]['rainfall_intensity'] = precipitation
        else:
            forecast_df = pd.concat([pd.DataFrame(row, columns=forecast_df.columns, index=[datetime_object]),forecast_df])
        
    # df = pd.DataFrame.from_records(forecast, index=datetime_object)
    st.write(forecast_df.sort_index())

    return 'df'

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


st.header('Dashboard')
st.subheader("Predicting bike rentals demand")
# predictors = ['temp','rhum','dayofweek','timesofday','wdsp','rainfall_intensity', 'working_day', 'hour', 'season']

xgb_pipe = pickle.load(open("../models/xgb_pipeline.pkl", "rb"))

@st.cache
def predict(df):
    return xgb_pipe.predict(df)

@st.cache
def load_data():
    df = pd.read_csv("df_test.csv")
    X = df.drop(['count'], axis=1)
    y = df.pop('count')
    return X,y

st.write('''
         #### Normalized Root Mean Square Error (NRMSE)
         ''')
st.latex(r'''NRMSE = \frac{RSME}{y_{max} - y_{min}}''')

X,y = load_data()
predicted = pd.Series(xgb_pipe.predict(X))

st.dataframe(predicted)


st.write('''
**GPS coordinates of Dublin Airport in Ireland** \n
Latitude: 53.4264 - Longitude: -6.2499 \n
**Weather Forescat API URL**: http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=53.4264;long=-6.2499
''')

URL_WEATHER_API = "http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=53.4264;long=-6.2499"
response = requests.get(URL_WEATHER_API).content

# st.write(soup.prettify())

df_forecast = parse_xml(response)

