import streamlit as st
import pandas as pd
import numpy as np
from sklearn import metrics
from sklearn import pipeline
import xgboost as xgb
import pickle

st.write(
    """
# Dashboard
    """
)

xgb_pipe = pickle.load(open("xgb_pipeline.pkl", "rb"))
@st.cache
def predict(df):
    return xgb_pipe.predict(df)

@st.cache
def load_data():
    return pd.read_csv("df_test.csv")

df = load_data()
st.dataframe(df)

