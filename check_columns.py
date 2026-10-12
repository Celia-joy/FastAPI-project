import sqlite3

connection = sqlite3.connect("app.db")
cursor = connection.cursor()
columns = cursor.execute(
    "PRAGMA table_info(users)"
).fetchall()

for column in columns: 
    print(f"Column: {column[1]}")

connection.close()