from sqlalchemy import select
from app.database.connection import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()

for user in users:
    print(
        user.id,
        user.name,
        user.email,
        user.age,
        user.password
    )

db.close()