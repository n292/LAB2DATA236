from fastapi import APIRouter, HTTPException, status, Query, Header
from schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from mongodb import mongo_db
from utils.security import decode_token
from datetime import datetime, timezone
import os
import json
import base64
import re

import uuid
from kafka import KafkaProducer

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
producer = None

def get_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            print(f"Kafka Producer error: {e}")
    return producer

def normalize_role(role):
    if role is None:
        return "user"
    if hasattr(role, "value"):
        return str(role.value).strip().lower()
    role_str = str(role).strip()
    if "." in role_str:
        role_str = role_str.split(".")[-1]
    return role_str.lower()

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

def get_owner_name(restaurant: dict):
    owner_id = restaurant.get("owner_id")
    if owner_id:
        owner = mongo_db.users.find_one({"_id": owner_id})
        if owner:
            return owner.get("name")
    return None

def serialize_restaurant(restaurant: dict):
    photo_data = None
    photos = restaurant.get("photos", {})
    if isinstance(photos, bytes):
        try:
            photo_base64 = base64.b64encode(photos).decode("utf-8")
            photo_data = f"data:image/jpeg;base64,{photo_base64}"
        except Exception as e:
            print(f"Error encoding photo: {e}")
            photo_data = None

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
        "owner_id": restaurant.get("owner_id"),
        "owner_name": get_owner_name(restaurant),
        "average_rating": restaurant.get("average_rating", 0),
        "review_count": restaurant.get("review_count", 0),
        "created_at": restaurant.get("created_at"),
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
    limit: int = Query(50)
):
    query = {}
    if name:
        query["name"] = {"$regex": re.compile(name, re.IGNORECASE)}
    if cuisine:
        query["cuisine_type"] = {"$regex": re.compile(cuisine, re.IGNORECASE)}
    if city:
        query["location.city"] = {"$regex": re.compile(city, re.IGNORECASE)}
    if keywords:
        kw_regex = re.compile(keywords, re.IGNORECASE)
        query["$or"] = [
            {"description": {"$regex": kw_regex}},
            {"amenities": {"$regex": kw_regex}}
        ]

    restaurants = list(mongo_db.restaurants.find(query).skip(skip).limit(limit))
    return [serialize_restaurant(r) for r in restaurants]

@router.get("/user/{user_id}", response_model=list[RestaurantResponse])
def get_user_restaurants(user_id: int, skip: int = Query(0), limit: int = Query(10)):
    restaurants = list(mongo_db.restaurants.find({"owner_id": user_id}).skip(skip).limit(limit))
    return [serialize_restaurant(r) for r in restaurants]

@router.get("/owner/list", response_model=list[RestaurantResponse])
def get_owner_restaurants(
    authorization: str = Header(None),
    skip: int = Query(0),
    limit: int = Query(10)
):
    current_user = get_current_user_from_header(authorization)
    restaurants = list(mongo_db.restaurants.find({"owner_id": current_user["_id"]}).skip(skip).limit(limit))
    return [serialize_restaurant(r) for r in restaurants]

@router.get("/owner/dashboard", response_model=dict)
def get_owner_dashboard(authorization: str = Header(None)):
    current_user = get_current_user_from_header(authorization)
    restaurants = list(mongo_db.restaurants.find({"owner_id": current_user["_id"]}))

    if not restaurants:
        return {
            "total_restaurants": 0,
            "total_favorites": 0,
            "average_rating": 0,
            "total_reviews": 0,
            "recent_reviews": [],
            "restaurants": []
        }

    restaurant_ids = [r["_id"] for r in restaurants]

    total_favorites = mongo_db.favourites.count_documents({"restaurant_id": {"$in": restaurant_ids}})
    total_reviews = mongo_db.reviews.count_documents({"restaurant_id": {"$in": restaurant_ids}})
    
    pipeline = [
        {"$match": {"_id": {"$in": restaurant_ids}}},
        {"$group": {"_id": None, "avg": {"$avg": "$average_rating"}}}
    ]
    avg_res = list(mongo_db.restaurants.aggregate(pipeline))
    avg_rating = avg_res[0]["avg"] if avg_res else 0

    recent_reviews = list(mongo_db.reviews.find({"restaurant_id": {"$in": restaurant_ids}}).sort("created_at", -1).limit(5))

    return {
        "total_restaurants": len(restaurants),
        "total_favorites": total_favorites,
        "average_rating": float(round(avg_rating, 2)),
        "total_reviews": total_reviews,
        "recent_reviews": [
            {
                "id": r["_id"],
                "restaurant_id": r["restaurant_id"],
                "rating": r["rating"],
                "comment": r.get("comment"),
                "created_at": r.get("created_at")
            }
            for r in recent_reviews
        ],
        "restaurants": [serialize_restaurant(r) for r in restaurants]
    }

@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(restaurant_id: int):
    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    return serialize_restaurant(restaurant)

@router.post("/", response_model=RestaurantResponse)
def create_restaurant(
    restaurant_data: RestaurantCreate,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)
    current_user_role = normalize_role(current_user.get("role"))
    photo_binary = decode_photo_data(restaurant_data.photo_data)

    last_rest = mongo_db.restaurants.find_one({}, sort=[("_id", -1)])
    new_id = (last_rest["_id"] + 1) if last_rest else 1

    new_restaurant = {
        "_id": new_id,
        "mysql_id": new_id,
        "name": restaurant_data.name,
        "cuisine_type": restaurant_data.cuisine_type,
        "description": restaurant_data.description,
        "location": {
            "address": restaurant_data.address,
            "city": restaurant_data.city,
            "zip_code": restaurant_data.zip_code,
        },
        "contact": {
            "phone": restaurant_data.phone,
            "email": restaurant_data.email,
        },
        "hours_of_operation": restaurant_data.hours_of_operation,
        "amenities": restaurant_data.amenities,
        "pricing_tier": restaurant_data.pricing_tier,
        "photos": photo_binary,
        "owner_id": current_user["_id"] if current_user_role == "owner" else None,
        "average_rating": 0,
        "review_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    mongo_db.restaurants.insert_one(new_restaurant)
    
    # Send Kafka event for Lab 2 Async requirements
    kp = get_producer()
    if kp:
        event = {
            "event_type": "restaurant.created",
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": current_user["_id"],
            "entity": "restaurant",
            "payload": {
                "restaurant_id": new_id,
                "name": restaurant_data.name,
                "cuisine_type": restaurant_data.cuisine_type,
                "address": restaurant_data.address,
                "city": restaurant_data.city,
                "owner_id": current_user["_id"] if current_user_role == "owner" else None
            },
            "idempotency_key": f"rest:create:{new_id}"
        }
        kp.send("restaurant.created", value=event)
        kp.flush()

    return serialize_restaurant(new_restaurant)

@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)
    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.get("owner_id") and restaurant["owner_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this restaurant"
        )

    update_data = restaurant_data.model_dump(exclude_unset=True) if hasattr(restaurant_data, "model_dump") else restaurant_data.dict(exclude_unset=True)

    if "photo_data" in update_data:
        photo_data = update_data.pop("photo_data")
        photo_binary = decode_photo_data(photo_data)
        if photo_binary is not None:
            update_data["photos"] = photo_binary

    update_doc = {"$set": {"updated_at": datetime.now(timezone.utc)}}
    for field, value in update_data.items():
        if field in ["address", "city", "zip_code"]:
            update_doc["$set"][f"location.{field}"] = value
        elif field in ["phone", "email"]:
            update_doc["$set"][f"contact.{field}"] = value
        else:
            update_doc["$set"][field] = value

    mongo_db.restaurants.update_one({"_id": restaurant_id}, update_doc)
    updated_restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    return serialize_restaurant(updated_restaurant)

@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: int,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)
    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.get("owner_id") != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this restaurant"
        )

    mongo_db.restaurants.delete_one({"_id": restaurant_id})
    return {"message": "Restaurant deleted successfully"}

@router.get("/{restaurant_id}/favorites")
def get_restaurant_favorites_count(restaurant_id: int):
    count = mongo_db.favourites.count_documents({"restaurant_id": restaurant_id})
    return {"restaurant_id": restaurant_id, "favorite_count": count}

@router.post("/{restaurant_id}/claim")
def claim_restaurant(
    restaurant_id: int,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)
    current_user_role = normalize_role(current_user.get("role"))

    if current_user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only restaurant owners can claim restaurants"
        )

    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if restaurant.get("owner_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This restaurant is already claimed by another owner"
        )

    mongo_db.restaurants.update_one({"_id": restaurant_id}, {"$set": {"owner_id": current_user["_id"]}})
    updated_restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    return {
        "message": "Restaurant claimed successfully",
        "restaurant": serialize_restaurant(updated_restaurant)
    }

@router.post("/{restaurant_id}/unclaim")
def unclaim_restaurant(
    restaurant_id: int,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)
    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if not restaurant.get("owner_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This restaurant is not currently claimed"
        )

    if restaurant["owner_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unclaim restaurants you own"
        )

    mongo_db.restaurants.update_one({"_id": restaurant_id}, {"$set": {"owner_id": None}})
    updated_restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    return {
        "message": "Restaurant unclaimed successfully",
        "restaurant": serialize_restaurant(updated_restaurant)
    }