"""Authentication routes for User Signup and Login."""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from app.core.mongodb import get_database
from app.models.user import (
    UserCreate, 
    UserLogin, 
    UserResponse, 
    Token, 
    hash_password, 
    verify_password, 
    create_access_token
)
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db=Depends(get_database)):
    """Create a new user in MongoDB."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable. Please try again later."
        )

    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Prepare user data
    user_data = user_in.model_dump()
    password = user_data.pop("password")
    user_data["hashed_password"] = hash_password(password)
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    
    # Insert into MongoDB
    result = await db.users.insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)
    
    # Generate token
    user_resp = UserResponse(**user_data)
    access_token = create_access_token(data={"sub": user_resp.email, "user_id": user_resp.id})
    
    return Token(access_token=access_token, user=user_resp)

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db=Depends(get_database)):
    """Log in an existing user."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable. Please try again later."
        )

    # Find user by email
    user_data = await db.users.find_one({"email": user_in.email})
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Verify password
    if not verify_password(user_in.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Convert ObjectId to string for response
    user_data["_id"] = str(user_data["_id"])
    user_resp = UserResponse(**user_data)
    
    # Generate token
    access_token = create_access_token(data={"sub": user_resp.email, "user_id": user_resp.id})
    
    return Token(access_token=access_token, user=user_resp)
