from getpass import getpass

from app.database.connection import SessionLocal
from app.models.user import User
from app.services.password import hash_password

email = "jwt-test@example.com"
db = SessionLocal()

try:
    user = db.query(User).filter(User.email == email).first()

    if user is None :
        print("Admin account not found.")
    elif user.role != "admin":
        print("Account is not an admin. No changes made")
    else:
        password = getpass("Enter a new test admin password: ")
        confirmation = getpass("Confirm the password: ")

        if password != confirmation:
            print("Passwords do not match. No changes made.")
        elif len(password) < 8:
            print("Use at least 8 characters. No changes made.")
        else:
            user.password = hash_password(password)
            db.commit()
            print("Test admin password updated successfully.")

finally:
    db.close()