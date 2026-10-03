from fastapi import APIRouter
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

"""
@router.get("/users")
def get_users():
    return {
        "users" : ["Celia", "Alice", "Bob"]
    }
"""

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    return {
        "message" : "User created successfully",
        "user" : user
    }