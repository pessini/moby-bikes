# %%
import pandas as pd
import numpy as np
import requests
import json
from pandas import json_normalize

# Database
# create a folder called conn/ and a python file called mongodb with variables for connection
from mongodb_conn import mongodb
import importlib
from pymongo import MongoClient
from urllib.parse import quote_plus
importlib.reload(mongodb)

# parameters = {
#     "start": '2020-10-13',
#     "end": '2021-6-4',
#     "bikeid": 5
# }
parameters = None

headers={'content-type': 'application/json', 'accept': 'application/json'}
baseurl = "https://data.smartdublin.ie/mobybikes-api/"

last_reading_url = f'{baseurl}last_reading/'

# r = requests.get(last_reading_url, headers=headers, params=parameters)
# data = r.text
# parse_json = json.loads(data)


# def jprint(obj):
#     # create a formatted string of the Python JSON object
#     text = json.dumps(obj, sort_keys=True, indent=4)
#     print(text)

# jprint(r.json())

def _connect_mongo(host, port, username, password, db_name):
    """ A util for making a connection to mongo """

    if username and password:
        try:
            mongo_uri = f'mongodb://{username}:{quote_plus(password)}@{host}:{port}/{db_name}'
            conn = MongoClient(mongo_uri)
        except Exception:
            print('Could not connect to MongoDB')
    else:
        conn = MongoClient(host, port)

    return conn

def read_mongo(query=None, collection='', no_id=True):
    """ Read from Mongo and Store into a DataFrame """
    if query is None:
        query = {}
    df = None
    try:
        # Connect to MongoDB
        conn = _connect_mongo(host=mongodb.host, port=mongodb.port, username=mongodb.user_name, password=mongodb.pass_word, db_name=mongodb.db_name)
        db = conn.moby # switch to the database

        if collection in db.list_collection_names(): 
            # Make a query to the specific DB and Collection 
            # and store into a Dataframe
            data = db[collection].find(query)
            df =  pd.DataFrame(list(data))
            # Delete the _id
            if no_id:
                del df['_id']
        else:
            print(f'Collection {collection} was not found!')
        # close mongodb connection
        conn.close()
    except Exception:
        print('Could not query MongoDB')

    return df

def insert_mongo(data=None, collection='', no_id=True):
    """ Insert data in MongoDB """
    if data is not None:
        try:
            # Connect to MongoDB
            conn = _connect_mongo(host=mongodb.host, port=mongodb.port, username=mongodb.user_name, password=mongodb.pass_word, db_name=mongodb.db_name)
            db = conn.mobybikes # switch to the database

            if collection in db.list_collection_names(): 
                # Insert values from a list to MongoDB Collection
                data = db[collection].insert_many(data)
                print(data.inserted_ids)
            else:
                print(f'Collection {collection} was not found!')
            # close mongodb connection
            conn.close()
        except Exception:
            print('Could not insert data in MongoDB')
    else:
        print('No data to insert in MongoDB')


historical_data = read_mongo(collection='historical')
irish_calendar = read_mongo(collection='irishcalendar')

historical_data.head()

# insert_mongo(data=parse_json, collection='lastreading')