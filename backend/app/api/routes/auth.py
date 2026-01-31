from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime

from app.models.user import UserCreate, UserLogin, UserResponse, Token
from app.db.mongodb import get_collection
from app.api.middleware.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from app.api.middleware.rate_limiter import strict_rate_limit

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, _: bool = Depends(strict_rate_limit)):
    users_collection = get_collection("users")
    
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_doc = {
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": get_password_hash(user_data.password),
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            created_at=user_doc["created_at"]
        )
    )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, _: bool = Depends(strict_rate_limit)):
    users_collection = get_collection("users")
    
    user = await users_collection.find_one({"email": user_data.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    user_id = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id, "email": user["email"]}
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"]
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    users_collection = get_collection("users")
    from bson import ObjectId
    
    user = await users_collection.find_one({"_id": ObjectId(current_user["id"])})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"]
    )
