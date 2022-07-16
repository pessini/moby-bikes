import streamlit as st
import pandas as pd
import numpy as np
import pymongo
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


client = pymongo.MongoClient(**st.secrets["mongo"])

#@st.cache
def get_data():
    db = client.mobybikes
    items = db['moby-historical'].find().limit(1000)
    return pd.DataFrame(items)
items = get_data()

text_to_display = '''
## This is the document title

This is some _markdown_.
'''
st.markdown(text_to_display)
st.dataframe(items)
