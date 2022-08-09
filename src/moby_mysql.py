import json
from sys import prefix
import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import boto3

s3_client = boto3.client("s3")
S3_BUCKET = "moby-bikes-rentals"

rentals_files_in_bucket = s3_client.list_objects(Bucket=S3_BUCKET, Prefix='moby_')
weather_files_in_bucket = s3_client.list_objects(Bucket=S3_BUCKET, Prefix='weather_')

def parse_files():
    pass

for v in rentals_files_in_bucket['Contents']:
    obj = s3_client.Object(S3_BUCKET, v['Key'])
    data = obj.get()['Body'].read().decode('utf-8')
    json_data = json.loads(data)
    
{'ResponseMetadata': {'RequestId': 'EMT49ZDYQF7MYCGM', 
                      'HostId': '1zrX1ogYgqHOfGECth0PIDEhIuqDuYMkXnTAVsz0zS0af6YR0ZQe7rDKZhBM/6SBm9ZDc1GbY0k=', 
                      'HTTPStatusCode': 200, 
                      'HTTPHeaders': {'x-amz-id-2': 
                          '1zrX1ogYgqHOfGECth0PIDEhIuqDuYMkXnTAVsz0zS0af6YR0ZQe7rDKZhBM/6SBm9ZDc1GbY0k=', 
                          'x-amz-request-id': 'EMT49ZDYQF7MYCGM', 'date': 'Tue, 09 Aug 2022 22:40:30 GMT', 
                          'transfer-encoding': 'chunked', 'server': 'AmazonS3'}, 'RetryAttempts': 0}, 
 'TagSet': [{'Key': 'rental', 'Value': ''}]}

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