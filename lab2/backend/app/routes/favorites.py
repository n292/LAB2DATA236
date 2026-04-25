from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models import Favorite, Restaurant
from schemas import FavoriteCreate, FavoriteResponse
from database import get_db
import json

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


def serialize_restaurant(restaurant: Restaurant):
    if not restaurant:
        return None

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
        "average_rating": restaurant.average_rating,
        "review_count": restaurant.review_count,
        "created_at": restaurant.created_at,
    }


def serialize_favorite(favorite: Favorite):
    return {
        "id": favorite.id,
        "restaurant_id": favorite.restaurant_id,
        "created_at": favorite.created_at,
        "restaurant": serialize_restaurant(favorite.restaurant)
    }


@router.get("/user/{user_id}", response_model=list[FavoriteResponse])
def get_user_favorites(
    user_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    favorites = db.query(Favorite).filter(
        Favorite.user_id == user_id
    ).offset(skip).limit(limit).all()

    return [serialize_favorite(f) for f in favorites]


@router.post("/", response_model=FavoriteResponse)
def add_favorite(
    favorite_data: FavoriteCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == favorite_data.restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.restaurant_id == favorite_data.restaurant_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant already in favorites"
        )

    new_favorite = Favorite(
        user_id=user_id,
        restaurant_id=favorite_data.restaurant_id
    )

    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    # make sure relationship is available
    new_favorite = db.query(Favorite).filter(Favorite.id == new_favorite.id).first()

    return serialize_favorite(new_favorite)


@router.delete("/{favorite_id}")
def remove_favorite(favorite_id: int, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter(Favorite.id == favorite_id).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )

    db.delete(favorite)
    db.commit()

    return {"message": "Removed from favorites"}


@router.get("/check/{user_id}/{restaurant_id}")
def check_favorite(user_id: int, restaurant_id: int, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.restaurant_id == restaurant_id
    ).first()

    return {
    "is_favorite": favorite is not None,
    "favorite_id": favorite.id if favorite else None
}