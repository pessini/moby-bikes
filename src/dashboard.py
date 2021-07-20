import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient, collection
import json
from urllib.parse import quote_plus

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

CONN_URI = quote_plus("mongodb://superuser:anq2677@@localhost:27017/?authSource=test&authMechanism=SCRAM-SHA-256&readPreference=primary&appname=MongoDB%20Compass&ssl=false")
#cache the function and map the type to the hash function
@st.cache(hash_funcs={MongoClient: id})
def mongo_connect(url):
    return MongoClient(url)

client = mongo_connect(CONN_URI)
# db = client.mobybikes


# @st.cache(ttl=600)
def get_data():
    db = client.mobybikes
    items = db['moby-historical'].find(limit=5)
    # items = list(items)  # make hashable for st.cache
    st.write(items)
    return items
items = get_data()

# Print results.
for item in items:
    st.write(f"{item['HarvestTime']} has a :{item['LastRentalStart']}:")