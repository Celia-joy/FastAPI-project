import jwt
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserCreateResponse,
    UserUpdate,
    UserLogin,
    Token,
    RefreshTokenRequest,
    PasswordChange,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from sqlalchemy.orm import Session

from app.database.connection import get_db

from datetime import datetime, timezone

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken

from app.services.password import hash_password, verify_password
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    get_current_user,
    require_role,
    SECRET_KEY,
    ALGORITHM
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
    refresh_token, jti, expires_at = create_refresh_token({
        "sub" : user.email
    })

    db_refresh_token = RefreshToken(
        jti=jti,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_access_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate" : "Bearer"}
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate" : "Bearer"}
        )
    
    email = payload.get("sub")
    token_type = payload.get("type")
    jti = payload.get("jti")

    if not email or token_type != "refresh" or not jti:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise HTTPException(
            status_code = 401,
            detail="User not found",
            headers={"WWW-Authenticate" : "Bearer"}
        )

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.jti == jti
    ).first()

    if (
        stored_token is None
        or stored_token.user_id != user.id
        or stored_token.revoked
        or stored_token.expires_at <= int(
            datetime.now(timezone.utc).timestamp()
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid or has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )

    stored_token.revoked = True   

    new_access_token = create_access_token({"sub": user.email})
    new_refresh_token, new_jti, new_expires_at = create_refresh_token({"sub": user.email})

    db_new_token = RefreshToken(
        jti=new_jti,
        user_id=user.id,
        expires_at=new_expires_at
    )

    db.add(db_new_token)

    try: 
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if not user:
        return {
            "message": "If the account exists, a password reset request has been created."
        }

    token, jti, expires_at = create_password_reset_token({
        "sub": user.email
    })

    reset_record = PasswordResetToken(
        jti=jti,
        user_id=user.id,
        expires_at=expires_at
    )

    db.add(reset_record)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message" : "If the account exists, a password reset request has been created.",
        "development_reset_token" : token
    }

@router.post("/logout")
def logout(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token_data.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    email = payload.get("sub")
    token_type = payload.get("type")
    jti = payload.get("jti")

    if not email or token_type != "refresh" or not jti:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.jti == jti
    ).first()

    if (
        stored_token is None
        or stored_token.user_id != user.id
        or stored_token.revoked
        or stored_token.expires_at <= int(
            datetime.now(timezone.utc).timestamp()
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid or has been revoked"
        )

    stored_token.revoked = True
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Successfully logged out"
    }

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if not verify_password(
        password_data.current_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    if verify_password(
        password_data.new_password,
        current_user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different"
        )

    current_user.password = hash_password(
        password_data.new_password
    )

    active_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False
    ).all()

    for token in active_tokens:
        token.revoked = True

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message" : "Password changed successfully. Please log in again."
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