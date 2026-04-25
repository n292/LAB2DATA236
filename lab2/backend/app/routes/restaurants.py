from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models import Restaurant, Favorite, Review, User
from schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from database import get_db
from utils.security import decode_token
import json
import base64

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


def normalize_role(role):
    if role is None:
        return "user"

    if hasattr(role, "value"):
        return str(role.value).strip().lower()

    role_str = str(role).strip()

    if "." in role_str:
        role_str = role_str.split(".")[-1]

    return role_str.lower()


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


def get_owner_name(restaurant: Restaurant, db: Session):
    owner_relation = getattr(restaurant, "owner", None)
    if owner_relation and getattr(owner_relation, "name", None):
        return owner_relation.name

    if restaurant.owner_id:
        owner = db.query(User).filter(User.id == restaurant.owner_id).first()
        if owner:
            return owner.name

    return None


def serialize_restaurant(restaurant: Restaurant, db: Session):
    photo_data = None

    if restaurant.photos:
        try:
            photo_base64 = base64.b64encode(restaurant.photos).decode("utf-8")
            photo_data = f"data:image/jpeg;base64,{photo_base64}"
        except Exception as e:
            print(f"Error encoding photo: {e}")
            photo_data = None

    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "cuisine_type": restaurant.cuisine_type,
        "description": restaurant.description,
        "address": restaurant.address,
        "city": restaurant.city,
        "zip_code": restaurant.zip_code,
        "phone": restaurant.phone,
        "email": restaurant.email,
        "hours_of_operation": json.loads(restaurant.hours_of_operation)
        if restaurant.hours_of_operation else None,
        "amenities": json.loads(restaurant.amenities)
        if restaurant.amenities else None,
        "pricing_tier": restaurant.pricing_tier,
        "owner_id": restaurant.owner_id,
        "owner_name": get_owner_name(restaurant, db),
        "average_rating": restaurant.average_rating,
        "review_count": restaurant.review_count,
        "created_at": restaurant.created_at,
        "photo_data": photo_data,
    }


def decode_photo_data(photo_data: str | None):
    if not photo_data or not photo_data.startswith("data:image"):
        return None

    try:
        photo_data_str = photo_data.split(",", 1)[1]
        return base64.b64decode(photo_data_str)
    except Exception as e:
        print(f"Error processing photo data: {e}")
        return None


@router.get("/", response_model=list[RestaurantResponse])
def search_restaurants(
    name: str = Query(None),
    cuisine: str = Query(None),
    city: str = Query(None),
    keywords: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    query = db.query(Restaurant)

    if name:
        query = query.filter(Restaurant.name.ilike(f"%{name}%"))

    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))

    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))

    if keywords:
        query = query.filter(
            or_(
                Restaurant.description.ilike(f"%{keywords}%"),
                Restaurant.amenities.ilike(f"%{keywords}%")
            )
        )

    restaurants = query.offset(skip).limit(limit).all()
    return [serialize_restaurant(r, db) for r in restaurants]


@router.get("/user/{user_id}", response_model=list[RestaurantResponse])
def get_user_restaurants(
    user_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [serialize_restaurant(r, db) for r in restaurants]


@router.get("/owner/list", response_model=list[RestaurantResponse])
def get_owner_restaurants(
    authorization: str = Header(None),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [serialize_restaurant(r, db) for r in restaurants]


@router.get("/owner/dashboard", response_model=dict)
def get_owner_dashboard(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    restaurants = db.query(Restaurant).filter(
        Restaurant.owner_id == current_user.id
    ).all()

    if not restaurants:
        return {
            "total_restaurants": 0,
            "total_favorites": 0,
            "average_rating": 0,
            "total_reviews": 0,
            "recent_reviews": [],
            "restaurants": []
        }

    restaurant_ids = [r.id for r in restaurants]

    total_favorites = db.query(func.count(Favorite.id)).filter(
        Favorite.restaurant_id.in_(restaurant_ids)
    ).scalar() or 0

    total_reviews = db.query(func.count(Review.id)).filter(
        Review.restaurant_id.in_(restaurant_ids)
    ).scalar() or 0

    avg_rating = db.query(func.avg(Restaurant.average_rating)).filter(
        Restaurant.id.in_(restaurant_ids)
    ).scalar() or 0

    recent_reviews = db.query(Review).filter(
        Review.restaurant_id.in_(restaurant_ids)
    ).order_by(Review.created_at.desc()).limit(5).all()

    return {
        "total_restaurants": len(restaurants),
        "total_favorites": total_favorites,
        "average_rating": float(round(avg_rating, 2)),
        "total_reviews": total_reviews,
        "recent_reviews": [
            {
                "id": r.id,
                "restaurant_id": r.restaurant_id,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at
            }
            for r in recent_reviews
        ],
        "restaurants": [serialize_restaurant(r, db) for r in restaurants]
    }


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    return serialize_restaurant(restaurant, db)


@router.post("/", response_model=RestaurantResponse)
def create_restaurant(
    restaurant_data: RestaurantCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)
    current_user_role = normalize_role(current_user.role)
    photo_binary = decode_photo_data(restaurant_data.photo_data)

    new_restaurant = Restaurant(
        name=restaurant_data.name,
        cuisine_type=restaurant_data.cuisine_type,
        description=restaurant_data.description,
        address=restaurant_data.address,
        city=restaurant_data.city,
        zip_code=restaurant_data.zip_code,
        phone=restaurant_data.phone,
        email=restaurant_data.email,
        hours_of_operation=json.dumps(restaurant_data.hours_of_operation)
        if restaurant_data.hours_of_operation is not None else None,
        amenities=json.dumps(restaurant_data.amenities)
        if restaurant_data.amenities is not None else None,
        pricing_tier=restaurant_data.pricing_tier,
        photos=photo_binary,
        owner_id=current_user.id if current_user_role == "owner" else None
    )

    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)

    return serialize_restaurant(new_restaurant, db)


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.owner_id and restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this restaurant"
        )

    update_data = restaurant_data.model_dump(exclude_unset=True)

    if "hours_of_operation" in update_data:
        update_data["hours_of_operation"] = (
            json.dumps(update_data["hours_of_operation"])
            if update_data["hours_of_operation"] is not None else None
        )

    if "amenities" in update_data:
        update_data["amenities"] = (
            json.dumps(update_data["amenities"])
            if update_data["amenities"] is not None else None
        )

    if "photo_data" in update_data:
        photo_data = update_data.pop("photo_data")
        photo_binary = decode_photo_data(photo_data)
        if photo_binary is not None:
            update_data["photos"] = photo_binary

    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    return serialize_restaurant(restaurant, db)


@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this restaurant"
        )

    db.delete(restaurant)
    db.commit()

    return {"message": "Restaurant deleted successfully"}


@router.get("/{restaurant_id}/favorites")
def get_restaurant_favorites_count(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    count = db.query(Favorite).filter(
        Favorite.restaurant_id == restaurant_id
    ).count()

    return {"restaurant_id": restaurant_id, "favorite_count": count}


@router.post("/{restaurant_id}/claim")
def claim_restaurant(
    restaurant_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)
    current_user_role = normalize_role(current_user.role)

    if current_user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only restaurant owners can claim restaurants"
        )

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This restaurant is already claimed by another owner"
        )

    restaurant.owner_id = current_user.id
    db.commit()
    db.refresh(restaurant)

    return {
        "message": "Restaurant claimed successfully",
        "restaurant": serialize_restaurant(restaurant, db)
    }


@router.post("/{restaurant_id}/unclaim")
def unclaim_restaurant(
    restaurant_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_header(authorization, db)

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if not restaurant.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This restaurant is not currently claimed"
        )

    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unclaim restaurants you own"
        )

    restaurant.owner_id = None
    db.commit()
    db.refresh(restaurant)

    return {
        "message": "Restaurant unclaimed successfully",
        "restaurant": serialize_restaurant(restaurant, db)
    }