# Host: localhost
# Port: 3306
# User: root
# SSL: enabled with TLS_AES_256_GCM_SHA384

#%%
import mysql.connector
import pandas as pd
import numpy as np

cnx = mysql.connector.connect(**config)

cursor = cnx.cursor()

query = ("select * from mobybikes.tmpRentals order by LastRentalStart asc")

cursor.execute(query)
myresult = cursor.fetchall()
df = pd.DataFrame(myresult, columns=cursor.column_names)

cursor.close()
cnx.close()

#%%
df.head()


# %%
df_grouped = df.groupby(['LastRentalStart', 'BikeID'])
df_grouped.head()
# %%
