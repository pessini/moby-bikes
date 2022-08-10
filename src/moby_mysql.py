import json
from sys import prefix
from datetime import datetime
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import boto3

s3_client = boto3.client("s3")
S3_BUCKET = "moby-bikes-rentals"

rentals_files_in_bucket = s3_client.list_objects(Bucket=S3_BUCKET, Prefix='moby_')
weather_files_in_bucket = s3_client.list_objects(Bucket=S3_BUCKET, Prefix='weather_')



def parse_files():
    pass

def get_file_tag(fileName):
    # Example of tag 'TagSet': [{'Key': 'rental', 'Value': ''}]
    # If object has not tagging, setting tag = None
    try:
        tag = s3_client.get_object_tagging(Bucket = S3_BUCKET, Key=fileName)['TagSet'][0]['Key']
    except Exception:
        tag = None
        
    return tag

def add_file_tag(fileName, tag):
    try:
        today_dt = datetime.now()
        today_dt_str = today_dt.strftime("%Y-%m-%d")
        new_tag = {'TagSet': [{'Key': tag, 'Value': today_dt_str}]}
        s3_client.put_object_tagging(Bucket = S3_BUCKET, Key=fileName,Tagging=new_tag)
        return True
    except Exception:
        return False

for v in rentals_files_in_bucket['Contents']:
    obj = s3_client.Object(S3_BUCKET, v['Key'])
    
    tag = get_file_tag(v['Key'])
    if not tag:
        add_file_tag(fileName=v['Key'], tag='error')

    data = obj.get()['Body'].read().decode('utf-8')
    json_data = json.loads(data)

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor

def process_weather_data() -> list:
    pass

def process_rentals_data() -> list:
    path = '/Users/lpessini/TUDublin/moby-bikes/data/external/moby/'
    fileName = '2022-07-20.json'

    with open(path+fileName) as json_file:
        parse_json = json.load(json_file)

    return [(i['LastRentalStart'], 
             i['BikeID'], 
             i['Battery'], 
             i['LastGPSTime'], 
             i['Latitude'], 
             i['Longitude']) for i in parse_json]

def lambda_handler(event=None, context=None):
    
    conn, cursor = openDB_connection()
    
    try:
        
        data = process_rentals_data()
        stmt = """INSERT INTO mobybikes.rawRentals (LastRentalStart, BikeID, Battery, LastGPSTime, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.executemany(stmt,data)
        None if conn.autocommit else conn.commit()
        print(cursor.rowcount, "record(s) inserted.")

    except mysql.connector.Error as error:

        print(f"Failed to update record to database rollback: {error}")
        # reverting changes because of exception
        conn.rollback()

    finally:

        cursor.callproc('SP_RENTALS_PROCESSING')
        # cursor.execute('CALL mobybikes.SP_RENTALS_PROCESSING();', multi=True)
        
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("Connection is closed!")


rentals_list = process_rentals_data()
# print(*rentals_list, sep='\n')
print(f'{len(rentals_list)} records in LIST')
lambda_handler()