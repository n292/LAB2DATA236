from fastapi import APIRouter, HTTPException, status
from schemas import UserSignup, UserLogin, Token, UserResponse
from mongodb import mongo_db
from utils.security import hash_password, verify_password, create_access_token
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])

def normalize_role(role):
    if role is None:
        return "user"
    if hasattr(role, "value"):
        return str(role.value).strip().lower()
    role_str = str(role).strip()
    if "." in role_str:
        role_str = role_str.split(".")[-1]
    return role_str.lower()

@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserSignup):
    existing_user = mongo_db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = hash_password(user_data.password)
    
    # Auto-incrementing ID to match legacy MySQL integer IDs
    last_user = mongo_db.users.find_one({}, sort=[("_id", -1)])
    new_id = (last_user["_id"] + 1) if last_user else 1
    
    now = datetime.now(timezone.utc)
    new_user = {
        "_id": new_id,
        "mysql_id": new_id,
        "name": user_data.name,
        "email": user_data.email,
        "password_hash": hashed_password,
        "role": user_data.role,
        "created_at": now,
        "updated_at": now,
        "profile": {
            "profile_picture_exists": False
        }
    }

    mongo_db.users.insert_one(new_user)
    
    # Return data in the format UserResponse expects
    new_user["id"] = new_user["_id"]
    return new_user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin):
    user = mongo_db.users.find_one({"email": user_data.email})

    if not user or not verify_password(user_data.password, user.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    normalized_role = normalize_role(user.get("role", "USER"))

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": normalized_role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["_id"],
        "role": normalized_role
    }