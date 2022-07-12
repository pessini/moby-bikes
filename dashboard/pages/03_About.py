import streamlit as st
import pandas as pd
import numpy as np
# import altair as alt
import matplotlib.pyplot as plt
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
#---------------------------------#
# Page layout
st.set_page_config(  # Alternate names: setup_page, page, layout
	layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
	page_title='Moby Bikes - About',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=f'{APP_PATH}img/favicon.webp',  # String, anything supported by st.image, or None.
)
#---------------------------------
#---------------------------------#

# moby_banner = Image.open(f'{APP_PATH}img/moby_move_home_page_img.webp')
# st.image(moby_banner, width=720)

st.header('About the project')
st.subheader("Predicting bike rentals demand")

st.latex(r'''NRMSE = \frac{RSME}{y_{max} - y_{min}}''')
st.markdown('''This web app is part of a GitHub repository: https://github.com/pessini/moby-bikes''')