import json
from sys import prefix
from datetime import datetime
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import boto3

s3_client = boto3.client("s3")
S3_BUCKET = "moby-bikes-rentals"

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor

def get_file_tag(fileName):
    # Example of tag 'TagSet': [{'Key': 'rental', 'Value': ''}]
    # If object has not tagging, setting tag = None
    try:
        tag = s3_client.get_object_tagging(Bucket=S3_BUCKET, Key=fileName)['TagSet'][0]['Key']
    except Exception:
        tag = None
        
    return tag

def remove_file_tag(fileName):
    s3_client.delete_object_tagging(Bucket=S3_BUCKET,Key=fileName)

def add_file_tag(fileName, tag):
    try:
        today_dt = datetime.now()
        today_dt_str = today_dt.strftime("%Y-%m-%d")
        new_tag = {'TagSet': [{'Key': tag, 'Value': today_dt_str}]}
        s3_client.put_object_tagging(Bucket=S3_BUCKET, Key=fileName, Tagging=new_tag)
        return True
    except Exception:
        return False

def process_files_data(type='rentals') -> list:
    
    if type == 'rentals':
        filePrefix = 'moby_'
    elif type == 'weather':
        filePrefix = 'weather_'
        
    files_in_bucket = s3_client.list_objects(Bucket=S3_BUCKET, Prefix=filePrefix)
    
    all_data=[]
    if 'Contents' in files_in_bucket:
        for v in files_in_bucket['Contents']:
            
            tag = get_file_tag(v['Key'])
            
            if not tag: # if object is not tagged, needs to be processed
                
                obj = s3_client.get_object(Bucket=S3_BUCKET, Key=v['Key'])
                json_data = json.loads(obj['Body'].read().decode('utf-8'))
                
                if type == 'rentals':
                    list_data = [(i['LastRentalStart'], 
                                    i['BikeID'], 
                                    i['Battery'], 
                                    i['LastGPSTime'], 
                                    i['Latitude'], 
                                    i['Longitude']) for i in json_data]
                    
                elif type == 'weather':
                    list_data = [(i['date'], 
                                    i['reportTime'], 
                                    i['temperature'], 
                                    i['windSpeed'], 
                                    i['humidity'], 
                                    i['rainfall']) for i in json_data]

                all_data.extend(list_data)

    return all_data
    

def lambda_handler(event, context):
    
    conn, cursor = openDB_connection()
    
    try:
        
        data = process_files_data() # rentals
        print(data)
        
        # stmt = """INSERT INTO mobybikes.rawRentals (LastRentalStart, BikeID, Battery, LastGPSTime, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s)"""
        # cursor.executemany(stmt,data)
        # None if conn.autocommit else conn.commit()
        # print(cursor.rowcount, "record(s) inserted.")

    except mysql.connector.Error as error:

        print(f"Failed to update record to database rollback: {error}")
        # reverting changes because of exception
        conn.rollback()

    finally:

        # cursor.callproc('SP_RENTALS_PROCESSING')
        
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("Connection is closed!")
            
