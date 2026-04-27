from fastapi import APIRouter, HTTPException, status, Header
from schemas import UserUpdate, UserResponse, UserPreferenceUpdate
from mongodb import mongo_db
from utils.security import decode_token
from datetime import datetime, timezone
import json
import base64

router = APIRouter(prefix="/api/users", tags=["users"])

def get_current_user_from_header(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = int(payload.get("sub"))
    user = mongo_db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

def encode_profile_photo(photo_binary: bytes | None):
    if not photo_binary:
        return None
    try:
        photo_base64 = base64.b64encode(photo_binary).decode("utf-8")
        return f"data:image/jpeg;base64,{photo_base64}"
    except Exception as e:
        print(f"Error encoding profile photo: {e}")
        return None

def decode_profile_photo(photo_data: str | None):
    if not photo_data or not photo_data.startswith("data:image"):
        return None
    try:
        photo_data_str = photo_data.split(",", 1)[1]
        return base64.b64decode(photo_data_str)
    except Exception as e:
        print(f"Error decoding profile photo: {e}")
        return None

def serialize_user(user: dict):
    role_value = str(user.get("role", "USER")).lower()
    if "." in role_value:
        role_value = role_value.split(".")[-1]

    profile = user.get("profile", {})

    return {
        "id": user.get("_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "about_me": profile.get("about_me"),
        "city": profile.get("city"),
        "country": profile.get("country"),
        "state": profile.get("state"),
        "languages": profile.get("languages"),
        "gender": profile.get("gender"),
        "role": role_value,
        "created_at": user.get("created_at"),
        "profile_photo_data": encode_profile_photo(user.get("profile_picture")),
    }

@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(user_id: int, authorization: str = Header(None)):
    current_user = get_current_user_from_header(authorization)

    if current_user["_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )

    user = mongo_db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return serialize_user(user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user_profile(user_id: int, user_data: UserUpdate, authorization: str = Header(None)):
    current_user = get_current_user_from_header(authorization)

    if current_user["_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    user = mongo_db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with ID: {user_id}"
        )

    update_data = (
        user_data.model_dump(exclude_unset=True)
        if hasattr(user_data, "model_dump")
        else user_data.dict(exclude_unset=True)
    )

    update_doc = {"$set": {"updated_at": datetime.now(timezone.utc)}}
    profile_updates = {}

    if "profile_photo_data" in update_data:
        profile_photo_data = update_data.pop("profile_photo_data")
        profile_photo_binary = decode_profile_photo(profile_photo_data)
        if profile_photo_binary is not None:
            update_doc["$set"]["profile_picture"] = profile_photo_binary
            profile_updates["profile.profile_picture_exists"] = True

    # Map fields to correct MongoDB structure
    root_fields = ["name", "phone"]
    for field, value in update_data.items():
        if field in root_fields:
            update_doc["$set"][field] = value
        else:
            profile_updates[f"profile.{field}"] = value

    if profile_updates:
        update_doc["$set"].update(profile_updates)

    mongo_db.users.update_one({"_id": user_id}, update_doc)
    
    updated_user = mongo_db.users.find_one({"_id": user_id})
    return serialize_user(updated_user)


@router.get("/{user_id}/preferences")
def get_user_preferences(user_id: int):
    preferences = mongo_db.user_preferences.find_one({"user_id": user_id})

    if not preferences or not preferences.get("preferences"):
        return {
            "cuisines": [],
            "price_range": None,
            "preferred_location": None,
            "dietary_restrictions": [],
            "ambiance": [],
            "sort_preference": None,
            "search_radius": 5
        }

    prefs = preferences.get("preferences", {})
    return {
        "id": preferences.get("_id"),
        "user_id": user_id,
        "cuisines": json.loads(prefs.get("cuisines", "[]")) if isinstance(prefs.get("cuisines"), str) else prefs.get("cuisines", []),
        "price_range": prefs.get("price_range"),
        "preferred_location": prefs.get("preferred_location"),
        "dietary_restrictions": json.loads(prefs.get("dietary_restrictions", "[]")) if isinstance(prefs.get("dietary_restrictions"), str) else prefs.get("dietary_restrictions", []),
        "ambiance": json.loads(prefs.get("ambiance", "[]")) if isinstance(prefs.get("ambiance"), str) else prefs.get("ambiance", []),
        "sort_preference": prefs.get("sort_preference"),
        "search_radius": prefs.get("search_radius", 5)
    }


@router.post("/{user_id}/preferences")
def set_user_preferences(user_id: int, prefs: UserPreferenceUpdate):
    user = mongo_db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    preferences_doc = mongo_db.user_preferences.find_one({"user_id": user_id})

    updates = {}
    if prefs.cuisines is not None:
        updates["preferences.cuisines"] = prefs.cuisines
    if prefs.price_range is not None:
        updates["preferences.price_range"] = prefs.price_range
    if prefs.preferred_location is not None:
        updates["preferences.preferred_location"] = prefs.preferred_location
    if prefs.dietary_restrictions is not None:
        updates["preferences.dietary_restrictions"] = prefs.dietary_restrictions
    if prefs.ambiance is not None:
        updates["preferences.ambiance"] = prefs.ambiance
    if prefs.sort_preference is not None:
        updates["preferences.sort_preference"] = prefs.sort_preference
    if prefs.search_radius is not None:
        updates["preferences.search_radius"] = prefs.search_radius

    if not preferences_doc:
        new_doc = {
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "preferences": updates.get("preferences", {})
        }
        for k, v in updates.items():
            key = k.split(".")[1]
            new_doc["preferences"][key] = v
        mongo_db.user_preferences.insert_one(new_doc)
        updated_prefs = new_doc["preferences"]
    else:
        if updates:
            mongo_db.user_preferences.update_one({"user_id": user_id}, {"$set": updates})
        
        doc = mongo_db.user_preferences.find_one({"user_id": user_id})
        updated_prefs = doc.get("preferences", {})

    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "cuisines": updated_prefs.get("cuisines", []),
            "price_range": updated_prefs.get("price_range"),
            "preferred_location": updated_prefs.get("preferred_location"),
            "dietary_restrictions": updated_prefs.get("dietary_restrictions", []),
            "ambiance": updated_prefs.get("ambiance", []),
            "sort_preference": updated_prefs.get("sort_preference"),
            "search_radius": updated_prefs.get("search_radius", 5)
        }
    }