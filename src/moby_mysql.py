import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials

conn = mysql.connector.connect(**mysqlcredentials.config)
cursor = conn.cursor()

try:
    data = [
        ('2022-08-08 18:28:35','777','0'),
        ('2022-08-08 18:33:49','2677','0'),
        ('2022-08-08 18:38:48','04030','0'),
    ]
    stmt = """INSERT IGNORE INTO mobybikes.Log_Weather (Date, Processed, Errors) VALUES (%s, %s, %s)"""

    cursor.executemany(stmt,data)
    None if conn.autocommit else conn.commit()
    print(cursor.rowcount, "record(s) inserted.")

except mysql.connector.Error as error:

    print(f"Failed to update record to database rollback: {error}")
    # reverting changes because of exception
    conn.rollback()

finally:
    
    # cursor.callproc('mobybikes.SP_RENTALS_PROCESSING')

    # closing database connection.
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("Connection is closed!")
