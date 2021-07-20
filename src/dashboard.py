import streamlit as st
import pandas as pd
import numpy as np
import pymongo
import json
from math import ceil

st.set_page_config(
     page_title="Ex-stream-ly Cool App",
     page_icon="🚲",
     layout="wide",
     initial_sidebar_state="expanded",
)

st.title('Moby Bikes - Dashboard')
st.subheader('Creating a dashboard for your benefit :)')

DATE_COLUMN = 'date/time'
DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
            'streamlit-demo-data/uber-raw-data-sep14.csv.gz')

@st.cache
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

data_load_state = st.text('Loading data...')
data = load_data(10000)
data_load_state.text("Done! (using st.cache)")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

st.subheader('Number of pickups by hour')
hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0,24))[0]
st.bar_chart(hist_values)

CONN_URI = "mongodb://test-user:test1234@localhost:27017/?authSource=test&authMechanism=SCRAM-SHA-256&readPreference=primary&appname=MongoDB%20Compass&ssl=false"
page_size = 1000

def provide_db_connection(func):
    #@wraps(func)
    def wrapper(*args, **kwargs):
        conn = pymongo.MongoClient(CONN_URI)
        result =  func(conn=conn, *args, **kwargs)
        conn.close()
        return result
    return wrapper

@st.cache
@provide_db_connection
def load_mongo_data(conn, db_name, coll_name, page):
    data = list(conn[db_name][coll_name].find().skip((page-1)*page_size).limit(page_size))
    return data


# coll_name = st.sidebar.selectbox ("Select collection: ",db.list_collection_names())

# document_count = db[coll_name].count_documents()
# page_number = st.number_input(
#     label="Page Number",
#     min_value=1,
#     max_value=ceil(document_count /page_size),
#     step=1,
# )
# st.write(load_mongo_data(coll_name, page_number))