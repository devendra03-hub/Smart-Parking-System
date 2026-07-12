import os
import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="smartparking-mysql-36d13ba7-smartparkingdev.l.aivencloud.com",
        user="avnadmin",
        password=os.environ.get("DB_PASSWORD"),
        database="defaultdb",
        port=17094,
        ssl_disabled=False
    )
    return connection