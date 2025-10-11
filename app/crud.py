import sqlite3

conn = sqlite3.connect("../data/app.db") ## to update this value into a db path

print("db init")

conn.close()