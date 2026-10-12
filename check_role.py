import sqlite3

connection = sqlite3.connect("app.db")

try:
    cursor = connection.cursor()
    result = cursor.execute(
        """
        SELECT name, email, role
        FROM users
        WHERE email = ?
        """,
        ("student.test@example.com",)
    ).fetchone()
    print(result)

finally:
    connection.close()