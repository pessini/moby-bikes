
#%%
import mysql.connector
import pandas as pd
import numpy as np
from mysql_conn import mysqldb as mysqlconn

#%%
cnx = mysql.connector.connect(**mysqlconn.config)

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
