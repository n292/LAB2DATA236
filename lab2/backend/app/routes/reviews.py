from fastapi import APIRouter, HTTPException, status, Query, Header
from schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from mongodb import mongo_db
from utils.security import decode_token
from datetime import datetime, timezone
import os
import json
import uuid
from kafka import KafkaProducer

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

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

def recalculate_restaurant_stats(restaurant_id: int):
    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    if not restaurant:
        return

    pipeline = [
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "avg": {"$avg": "$rating"}}}
    ]
    stats = list(mongo_db.reviews.aggregate(pipeline))
    
    if stats:
        review_count = stats[0]["count"]
        average_rating = stats[0]["avg"]
    else:
        review_count = 0
        average_rating = 0.0

    mongo_db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"review_count": review_count, "average_rating": float(round(average_rating, 2))}}
    )

def serialize_review(review: dict):
    if not review:
        return None
    author = mongo_db.users.find_one({"_id": review["user_id"]})
    return {
        "id": review["_id"],
        "user_id": review["user_id"],
        "restaurant_id": review["restaurant_id"],
        "rating": review["rating"],
        "comment": review.get("comment"),
        "created_at": review.get("created_at"),
        "author": {
            "id": author["_id"],
            "name": author.get("name"),
            "email": author.get("email"),
            "role": author.get("role"),
            "created_at": author.get("created_at")
        } if author else None
    }

@router.get("/restaurant/{restaurant_id}", response_model=list[ReviewResponse])
def get_restaurant_reviews(restaurant_id: int, skip: int = Query(0), limit: int = Query(10)):
    reviews = list(mongo_db.reviews.find({"restaurant_id": restaurant_id}).sort("created_at", -1).skip(skip).limit(limit))
    return [serialize_review(r) for r in reviews]

@router.get("/user/{user_id}", response_model=list[ReviewResponse])
def get_user_reviews(user_id: int, skip: int = Query(0), limit: int = Query(10)):
    reviews = list(mongo_db.reviews.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit))
    return [serialize_review(r) for r in reviews]

@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int):
    review = mongo_db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    return serialize_review(review)

@router.post("/restaurant/{restaurant_id}", response_model=ReviewResponse)
def create_review(
    restaurant_id: int,
    review_data: ReviewCreate,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)

    restaurant = mongo_db.restaurants.find_one({"_id": restaurant_id})
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    existing_review = mongo_db.reviews.find_one({
        "restaurant_id": restaurant_id,
        "user_id": current_user["_id"]
    })

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this restaurant"
        )

    # Use atomic counter to prevent race conditions during high concurrency
    counter = mongo_db.counters.find_one_and_update(
        {"_id": "review_id"},
        {"$inc": {"seq": 1}},
        return_document=True,
        upsert=True
    )
    new_id = counter["seq"]

    new_review = {
        "_id": new_id,
        "mysql_id": new_id,
        "user_id": current_user["_id"],
        "restaurant_id": restaurant_id,
        "rating": review_data.rating,
        "comment": review_data.comment.strip() if review_data.comment else None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    mongo_db.reviews.insert_one(new_review)
    recalculate_restaurant_stats(restaurant_id)

    # Send Kafka event for Lab 2 Async requirements
    kp = get_producer()
    if kp:
        event = {
            "event_type": "review.created",
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": current_user["_id"],
            "entity": "review",
            "payload": {
                "review_id": new_id,
                "user_id": current_user["_id"],
                "restaurant_id": restaurant_id,
                "rating": review_data.rating,
                "comment": review_data.comment
            },
            "idempotency_key": f"rev:create:{new_id}"
        }
        kp.send("review.created", value=event)
        kp.flush()

    return serialize_review(new_review)

@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)

    review = mongo_db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if review["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own review"
        )

    if review_data.rating is not None and (review_data.rating < 1 or review_data.rating > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    update_data = review_data.model_dump(exclude_unset=True) if hasattr(review_data, "model_dump") else review_data.dict(exclude_unset=True)
    update_doc = {"$set": {"updated_at": datetime.now(timezone.utc)}}

    if "comment" in update_data:
        update_doc["$set"]["comment"] = update_data["comment"].strip() if update_data["comment"] else None
    if "rating" in update_data:
        update_doc["$set"]["rating"] = update_data["rating"]

    mongo_db.reviews.update_one({"_id": review_id}, update_doc)
    recalculate_restaurant_stats(review["restaurant_id"])

    # Send Kafka event for Lab 2 Async requirements
    kp = get_producer()
    if kp:
        event = {
            "event_type": "review.updated",
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": current_user["_id"],
            "entity": "review",
            "payload": {
                "review_id": review_id,
                "user_id": current_user["_id"],
                "restaurant_id": review["restaurant_id"],
                "rating": review_data.rating,
                "comment": review_data.comment
            },
            "idempotency_key": f"rev:update:{review_id}:{int(datetime.now().timestamp())}"
        }
        kp.send("review.updated", value=event)
        kp.flush()

    updated_review = mongo_db.reviews.find_one({"_id": review_id})
    return serialize_review(updated_review)

@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    authorization: str = Header(None)
):
    current_user = get_current_user_from_header(authorization)

    review = mongo_db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if review["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own review"
        )

    restaurant_id = review["restaurant_id"]
    mongo_db.reviews.delete_one({"_id": review_id})
    recalculate_restaurant_stats(restaurant_id)

    # Send Kafka event for Lab 2 Async requirements
    kp = get_producer()
    if kp:
        event = {
            "event_type": "review.deleted",
            "trace_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": current_user["_id"],
            "entity": "review",
            "payload": {
                "review_id": review_id,
                "restaurant_id": restaurant_id
            },
            "idempotency_key": f"rev:delete:{review_id}"
        }
        kp.send("review.deleted", value=event)
        kp.flush()

    return {"message": "Review deleted successfully"}