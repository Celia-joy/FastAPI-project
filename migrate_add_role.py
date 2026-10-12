import sqlite3

connection = sqlite3.connect("app.db")

try:
    cursor = connection.cursor()
    column = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    ]

    if "role" not in column:
        cursor.execute(
            """
            ALTER TABLE users
            ADD COLUMN role VARCHAR(20)
            NOT NULL DEFAULT 'student'
            """
        )
        connection.commit()
        print("Role column added successfully")

    else:
        print("Role column already exists.")
    
finally:
    connection.close()