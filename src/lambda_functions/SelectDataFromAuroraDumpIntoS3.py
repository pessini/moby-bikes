import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials
import boto3
import json

s3_client = boto3.client("s3")
S3_BUCKET = "moby-bikes-rentals"

def openDB_connection():
    conn = mysql.connector.connect(**mysqlcredentials.config)
    cursor = conn.cursor()
    return conn, cursor

conn, cursor = openDB_connection()

def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def get_metrics():
    return {
        "average_duration": float(get_avg_duration()),
        "average_duration_delta": float(get_avg_duration_delta()),
        "total_rentals": get_total_rentals(),
        "total_rentals_delta": get_total_rentals_delta()
    }

def get_avg_duration() -> float:
    # CONCAT(FLOOR(AVG(Duration)/60),'h ', ROUND(MOD(AVG(Duration),60),0),'m') as average_duration
    # AVG(Duration) AS average_duration
    sqlquery = run_query("""SELECT 
                                AVG(Duration) AS average_duration
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE();""")
    return sqlquery[0][0]

# Indicator of how the metric changed
def get_avg_duration_delta() -> float:
    sqlquery = run_query("""SELECT 
                                AVG(Duration) AS average_duration
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 6 MONTH) AND DATE_SUB( CURDATE() , INTERVAL 3 MONTH);""")
    return sqlquery[0][0]

def get_total_rentals() -> int:
    sqlquery = run_query("""SELECT 
                                COUNT(*) AS total_rentals 
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE();""")
    return sqlquery[0][0]

# Indicator of how the metric changed
def get_total_rentals_delta() -> int:
    sqlquery = run_query("""SELECT 
                                COUNT(*) AS total_rentals  
                            FROM 
                                mobybikes.Rentals
                            WHERE 
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 6 MONTH) AND DATE_SUB( CURDATE() , INTERVAL 3 MONTH);""")
    return sqlquery[0][0]

def get_hourly_total_rentals() -> dict:
    
    # DATE_FORMAT(`Date`, '%Y-%m-%d %H:00:00') AS date_rental,
    # HAVING DATE(date_rental) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE()
    
    sqlquery = run_query("""WITH CTE_HOURLY_TOTAL_RENTALS AS
                            (
                                SELECT 
                                    DATE_FORMAT(`Date`, '%Y-%m-%d %H:00:00') AS date_rental,
                                    COUNT(*) AS total_rentals,
                                    ROUND( AVG(Duration),2 ) AS hourly_avg_duration
                                FROM mobybikes.Rentals
                                GROUP BY date_rental
                            )
                            SELECT 
                                date_rental,
                                FN_TIMESOFDAY(date_rental) AS timeofday, 
                                DAYNAME(date_rental) AS day_of_week, 
                                total_rentals,
                                CAST(hourly_avg_duration AS FLOAT) AS hourly_avg_duration
                            FROM 
                                CTE_HOURLY_TOTAL_RENTALS;
                        """)

    return sqlquery

def get_initial_battery():
    
    sqlquery = run_query("""SELECT
                                BatteryStart
                            FROM 
                                mobybikes.Rentals
                            WHERE
                                DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE()
                            AND
                                (BatteryStart IS NOT NULL OR BatteryStart IS NOT NULL)
                            AND
                                (BatteryStart <> 0 OR BatteryStart <> 0);
                        """)
    return sqlquery
    
def lambda_handler(event, context):

    metrics = get_metrics()
    metrics_json = json.dumps(metrics, indent = 4)
    s3_client.put_object(
        Body=metrics_json,
        Bucket=S3_BUCKET,
        Key='dashboard/metrics.json'
    )
    
    rentals = get_hourly_total_rentals()
    rentals_json = json.dumps(rentals, indent = 4)
    s3_client.put_object(
        Body=rentals_json,
        Bucket=S3_BUCKET,
        Key='dashboard/rentals.json'
    )
    
    battery = get_initial_battery()
    battery_json = json.dumps(battery, indent = 4)
    s3_client.put_object(
        Body=battery_json,
        Bucket=S3_BUCKET,
        Key='dashboard/battery.json'
    )