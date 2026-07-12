import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="parking@123",
        database="smart_parking"
    )
    return connection