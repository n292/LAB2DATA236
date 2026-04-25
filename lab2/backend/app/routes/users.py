from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from models import User, UserPreference
from schemas import UserUpdate, UserResponse, UserPreferenceUpdate
from database import get_db
from utils.security import decode_token
import json
import base64

router = APIRouter(prefix="/api/users", tags=["users"])


def get_current_user_from_header(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
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
    user = db.query(User).filter(User.id == user_id).first()

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


def serialize_user(user: User):
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)

    if "." in role_value:
        role_value = role_value.split(".")[-1]

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "about_me": user.about_me,
        "city": user.city,
        "country": user.country,
        "state": user.state,
        "languages": user.languages,
        "gender": user.gender,
        "role": role_value.lower(),
        "created_at": user.created_at,
        "profile_photo_data": encode_profile_photo(user.profile_picture),
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(
    user_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return serialize_user(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user_profile(
    user_id: int,
    user_data: UserUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    user = db.query(User).filter(User.id == user_id).first()

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

    if "profile_photo_data" in update_data:
        profile_photo_data = update_data.pop("profile_photo_data")
        profile_photo_binary = decode_profile_photo(profile_photo_data)
        if profile_photo_binary is not None:
            user.profile_picture = profile_photo_binary

    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return serialize_user(user)


@router.get("/{user_id}/preferences")
def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()

    if not preferences:
        return {
            "cuisines": [],
            "price_range": None,
            "preferred_location": None,
            "dietary_restrictions": [],
            "ambiance": [],
            "sort_preference": None,
            "search_radius": 5
        }

    return {
        "id": preferences.id,
        "user_id": preferences.user_id,
        "cuisines": json.loads(preferences.cuisines) if preferences.cuisines else [],
        "price_range": preferences.price_range,
        "preferred_location": preferences.preferred_location,
        "dietary_restrictions": json.loads(preferences.dietary_restrictions) if preferences.dietary_restrictions else [],
        "ambiance": json.loads(preferences.ambiance) if preferences.ambiance else [],
        "sort_preference": preferences.sort_preference,
        "search_radius": preferences.search_radius
    }


@router.post("/{user_id}/preferences")
def set_user_preferences(
    user_id: int,
    prefs: UserPreferenceUpdate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()

    if not preferences:
        preferences = UserPreference(user_id=user_id)
        db.add(preferences)

    if prefs.cuisines:
        preferences.cuisines = json.dumps(prefs.cuisines)
    if prefs.price_range:
        preferences.price_range = prefs.price_range
    if prefs.preferred_location:
        preferences.preferred_location = prefs.preferred_location
    if prefs.dietary_restrictions:
        preferences.dietary_restrictions = json.dumps(prefs.dietary_restrictions)
    if prefs.ambiance:
        preferences.ambiance = json.dumps(prefs.ambiance)
    if prefs.sort_preference:
        preferences.sort_preference = prefs.sort_preference
    if prefs.search_radius:
        preferences.search_radius = prefs.search_radius

    db.commit()
    db.refresh(preferences)

    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "cuisines": json.loads(preferences.cuisines) if preferences.cuisines else [],
            "price_range": preferences.price_range,
            "preferred_location": preferences.preferred_location,
            "dietary_restrictions": json.loads(preferences.dietary_restrictions) if preferences.dietary_restrictions else [],
            "ambiance": json.loads(preferences.ambiance) if preferences.ambiance else [],
            "sort_preference": preferences.sort_preference,
            "search_radius": preferences.search_radius
        }
    }