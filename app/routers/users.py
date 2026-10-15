from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserCreateResponse,
    UserUpdate,
    UserLogin,
    Token
)
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.services.password import hash_password, verify_password
from app.services.auth import (
    create_access_token,
    get_current_user,
    require_role
)




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
    hashed_password = hash_password(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        age=user.age,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "message" : "User created successfully",
        "user" : db_user
    }

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    if not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Unathorized"
        )
    
    access_token = create_access_token({
        "sub" : user.email
    })
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@router.get("/users", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    print("Authenticated user:", current_user.email)
    print("User role:", current_user.role)
    users = db.query(User).all()
    return users

@router.get("/admin/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_role("admin"))
):
    return {
        "message": f"Welcome, {current_user.name}!",
        "role": current_user.role
    }

@router.get("/users/{id}", response_model=UserResponse)
def get_user_by_id(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        raise HTTPException(
            status_code = 404,
            detail = "User not found"
        )

    if current_user.id != user.id and current_user.role != "admin":
        raise HTTPException(
            status_code = 403,
            detail = "Insufficient permissions"
        )
    return user

@router.patch("/users/{id}", response_model=UserResponse)
def update_user (
    id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    user = db.query(User).filter(User.id == id).first()

    if user is None:
        raise HTTPException(
            status_code = 404,
            detail = "User not found"
        )

    if current_user.id != user.id and current_user.role != "admin":
        raise HTTPException (
            status_code = 403,
            detail = "Insufficient permissions"
        )

    update_data = user_data.model_dump(exclude_unset = True)

    if "email" in update_data and update_data["email"] is not None:
        existing_user = (
            db.query(User)
            .filter(
                User.email == update_data["email"],
                User.id != user.id
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code = 409,
                detail = "Email already registered"
            )

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
    ):
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