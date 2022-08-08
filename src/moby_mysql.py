import mysql.connector
from mysql_conn import mysqldb as mysqlcredentials

try:
    conn = mysql.connector.connect(**mysqlcredentials.config)
    conn.autocommit = False
    cursor = conn.cursor()

    data = [
        ('2022-08-08 18:28:35',865,0),
        ('2022-08-08 18:33:49',3183,0),
        ('2022-08-08 18:38:48',3133,0),
    ]
    stmt = """INSERT IGNORE INTO mobybikes.Log_Rentals (Date, Processed, Errors) VALUES (%s, %s, %s)"""

    query = ('''INSERT INTO Log_Rentals (Date,Processed,Errors) VALUES ('2022-08-08 18:28:35',865,0), 
            ('2022-08-08 18:33:49',3183,0), ('2022-08-08 18:38:48',3133,0);''')

    cursor.executemany(stmt,data)
    conn.commit()
    print(cursor.rowcount, "record(s) inserted.")

except mysql.connector.Error as error:
    print(f"Failed to update record to database rollback: {error}")
    # reverting changes because of exception
    conn.rollback()
finally:
    # closing database connection.
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("connection is closed")

# myresult = cursor.fetchall()
# df = pd.DataFrame(myresult, columns=cursor.column_names)

# cursor.execute("SELECT * FROM Log_Rentals")

# for v in cursor:
#     print(v)
