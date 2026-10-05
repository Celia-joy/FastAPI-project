from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserCreateResponse,
    UserUpdate
)
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User


router = APIRouter()

"""
@router.get("/users")
def get_users():
    return {
        "users" : ["Celia", "Alice", "Bob"]
    }
"""

@router.post("/users", response_model=UserCreateResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existingUser = db.query(User).filter(User.email == user.email).first()
    if existingUser:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )
    db_user = User(
        name=user.name,
        email=user.email,
        age=user.age,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "message" : "User created successfully",
        "user" : db_user
    }

@router.get("/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{id}", response_model=UserResponse)
def get_user_by_id(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    return user

@router.patch("/users/{id}", response_model=UserResponse)
def update_user (
    id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    update_data = user_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

@router.delete("/users/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    db.delete(user)
    db.commit()
    return {
        "message": "User deleted successfully"
    }