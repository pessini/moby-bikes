# Host: localhost
# Port: 3306
# User: root
# SSL: enabled with TLS_AES_256_GCM_SHA384

import mysql.connector
import pandas as pd
import numpy as np

config = {
  'user': 'root',
  'password': 'SanFedele0430@',
  'host': '127.0.0.1',
  'database': 'mobybikes',
  'raise_on_warnings': True
}

cnx = mysql.connector.connect(**config)

cursor = cnx.cursor()

query = ("select LastRentalStart, BikeID, MAX(LastGPSTime) as lastgps "
         "from mobybikes.tmpRentals "
         "group by LastRentalStart, BikeID "
         "having BikeID = 10 order by LastRentalStart asc")

cursor.execute(query)
myresult = cursor.fetchall()
df = pd.DataFrame(myresult, columns=cursor.column_names)

cursor.close()
cnx.close()

print(df.head())

