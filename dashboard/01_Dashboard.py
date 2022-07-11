from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

#---------------------------------#
# Page layout
## Page expands to full width
st.set_page_config(layout="wide")
#---------------------------------#

st.header('Dashboard')
st.subheader("Predicting bike rentals demand")


st.write('''
         #### Normalized Root Mean Square Error (NRMSE)
         ''')
st.latex(r'''NRMSE = \frac{RSME}{y_{max} - y_{min}}''')