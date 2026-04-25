from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from app.kafka_producer import build_event, publish_event
except ImportError:
    from kafka_producer import build_event, publish_event


router = APIRouter(prefix="/api/reviews/kafka", tags=["Kafka Review Flow"])


class ReviewCreateRequest(BaseModel):
    user_id: int
    restaurant_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewUpdateRequest(BaseModel):
    user_id: int
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class ReviewDeleteRequest(BaseModel):
    user_id: int


@router.post("/create")
def create_review_event(request: ReviewCreateRequest):
    try:
        event = build_event(
            event_type="review.created",
            actor_id=str(request.user_id),
            entity_type="review",
            entity_id=f"pending-{request.user_id}-{request.restaurant_id}",
            payload={
                "user_id": request.user_id,
                "restaurant_id": request.restaurant_id,
                "rating": request.rating,
                "comment": request.comment,
            },
        )

        metadata = publish_event("review.created", event)

        return {
            "message": "Review creation event published to Kafka",
            "status": "accepted",
            "kafka": metadata,
            "event": event,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to publish review.created event: {str(exc)}")


@router.put("/update/{review_id}")
def update_review_event(review_id: int, request: ReviewUpdateRequest):
    try:
        event = build_event(
            event_type="review.updated",
            actor_id=str(request.user_id),
            entity_type="review",
            entity_id=str(review_id),
            payload={
                "review_id": review_id,
                "user_id": request.user_id,
                "rating": request.rating,
                "comment": request.comment,
            },
        )

        metadata = publish_event("review.updated", event)

        return {
            "message": "Review update event published to Kafka",
            "status": "accepted",
            "kafka": metadata,
            "event": event,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to publish review.updated event: {str(exc)}")


@router.delete("/delete/{review_id}")
def delete_review_event(review_id: int, request: ReviewDeleteRequest):
    try:
        event = build_event(
            event_type="review.deleted",
            actor_id=str(request.user_id),
            entity_type="review",
            entity_id=str(review_id),
            payload={
                "review_id": review_id,
                "user_id": request.user_id,
            },
        )

        metadata = publish_event("review.deleted", event)

        return {
            "message": "Review delete event published to Kafka",
            "status": "accepted",
            "kafka": metadata,
            "event": event,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to publish review.deleted event: {str(exc)}")