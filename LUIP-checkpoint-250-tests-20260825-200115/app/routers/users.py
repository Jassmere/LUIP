from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/")
def list_users():
    return {
        "message": "User endpoint working"
    }


@router.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not existing_user:
        print("======================================")
        print("User not found")
        print(f"Email entered: {form_data.username}")
        print("======================================")

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    print("======================================")
    print(f"User found: {existing_user.email}")
    print(f"Password entered: {form_data.password}")
    print(f"Stored password hash: {existing_user.password_hash}")

    password_ok = verify_password(
        form_data.password,
        existing_user.password_hash
    )

    print(f"Password verification result: {password_ok}")
    print("======================================")

    if not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": existing_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/reset-admin-password")
def reset_admin_password(
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == "admin@luip.com"
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Administrator not found"
        )

    user.password_hash = hash_password("Admin@123")

    db.commit()
    db.refresh(user)

    print("======================================")
    print("Administrator password has been reset")
    print(f"Email: {user.email}")
    print("Password: Admin@123")
    print("======================================")

    return {
        "message": "Administrator password reset successfully",
        "email": user.email,
        "password": "Admin@123"
    }


@router.get("/me")
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }