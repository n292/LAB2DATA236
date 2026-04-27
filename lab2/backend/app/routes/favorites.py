from fastapi import APIRouter, HTTPException, status, Query
from schemas import FavoriteCreate, FavoriteResponse
from mongodb import mongo_db
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/favorites", tags=["favorites"])

def serialize_restaurant(restaurant: dict):
    if not restaurant:
        return None

    return {
        "id": restaurant.get("_id"),
        "name": restaurant.get("name"),
        "cuisine_type": restaurant.get("cuisine_type"),
        "description": restaurant.get("description"),
        "address": restaurant.get("location", {}).get("address"),
        "city": restaurant.get("location", {}).get("city"),
        "zip_code": restaurant.get("location", {}).get("zip_code"),
        "phone": restaurant.get("contact", {}).get("phone"),
        "email": restaurant.get("contact", {}).get("email"),
        "hours_of_operation": json.loads(restaurant.get("hours_of_operation", "null")) if isinstance(restaurant.get("hours_of_operation"), str) else restaurant.get("hours_of_operation"),
        "amenities": json.loads(restaurant.get("amenities", "null")) if isinstance(restaurant.get("amenities"), str) else restaurant.get("amenities"),
        "pricing_tier": restaurant.get("pricing_tier"),
        "average_rating": restaurant.get("average_rating", 0),
        "review_count": restaurant.get("review_count", 0),
        "created_at": restaurant.get("created_at"),
    }


def serialize_favorite(favorite: dict, restaurant: dict = None):
    return {
        "id": favorite.get("_id"),
        "restaurant_id": favorite.get("restaurant_id"),
        "created_at": favorite.get("created_at"),
        "restaurant": serialize_restaurant(restaurant)
    }


@router.get("/user/{user_id}", response_model=list[FavoriteResponse])
def get_user_favorites(
    user_id: int,
    skip: int = Query(0),
    limit: int = Query(10)
):
    favorites_cursor = mongo_db.favourites.find({"user_id": user_id}).skip(skip).limit(limit)
    favorites = list(favorites_cursor)

    result = []
    for f in favorites:
        restaurant = mongo_db.restaurants.find_one({"_id": f["restaurant_id"]})
        result.append(serialize_favorite(f, restaurant))

    return result


@router.post("/", response_model=FavoriteResponse)
def add_favorite(
    favorite_data: FavoriteCreate,
    user_id: int
):
    restaurant = mongo_db.restaurants.find_one({"_id": favorite_data.restaurant_id})

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    existing = mongo_db.favourites.find_one({
        "user_id": user_id,
        "restaurant_id": favorite_data.restaurant_id
    })

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant already in favorites"
        )

    last_fav = mongo_db.favourites.find_one({}, sort=[("_id", -1)])
    new_id = (last_fav["_id"] + 1) if last_fav else 1

    new_favorite = {
        "_id": new_id,
        "mysql_id": new_id,
        "user_id": user_id,
        "restaurant_id": favorite_data.restaurant_id,
        "created_at": datetime.now(timezone.utc)
    }

    mongo_db.favourites.insert_one(new_favorite)

    return serialize_favorite(new_favorite, restaurant)


@router.delete("/{favorite_id}")
def remove_favorite(favorite_id: int):
    favorite = mongo_db.favourites.find_one({"_id": favorite_id})

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    mongo_db.favourites.delete_one({"_id": favorite_id})

    return {"message": "Removed from favorites"}


@router.get("/check/{user_id}/{restaurant_id}")
def check_favorite(user_id: int, restaurant_id: int):
    favorite = mongo_db.favourites.find_one({
        "user_id": user_id,
        "restaurant_id": restaurant_id
    })

    return {
        "is_favorite": favorite is not None,
        "favorite_id": favorite.get("_id") if favorite else None
    }