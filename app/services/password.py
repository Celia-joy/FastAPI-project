import bcrypt
def hash_password(password: str):
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")

def verify_password(password: str, hashed_password: str):
    password_bytes = password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


hashed = hash_password("secret123")

print("Hashed:", hashed)

print("Correct password:", verify_password("secret123", hashed))

print("Wrong password:", verify_password("wrongpassword", hashed))