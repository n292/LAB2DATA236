from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from app.kafka_producer import build_event, publish_event
except ImportError:
    from kafka_producer import build_event, publish_event


router = APIRouter(prefix="/api/restaurants/kafka", tags=["Kafka Restaurant Flow"])


class RestaurantCreateRequest(BaseModel):
    name: str
    cuisine_type: str
    description: Optional[str] = None
    address: str
    city: str
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    pricing_tier: Optional[str] = None
    owner_id: Optional[int] = None


@router.post("/create")
def create_restaurant_event(request: RestaurantCreateRequest):
    try:
        event = build_event(
            event_type="restaurant.created",
            actor_id=str(request.owner_id or "system"),
            entity_type="restaurant",
            entity_id=f"pending-{request.name.replace(' ', '-').lower()}",
            payload=request.model_dump(),
        )

        metadata = publish_event("restaurant.created", event)

        return {
            "message": "Restaurant creation event published to Kafka",
            "status": "accepted",
            "kafka": metadata,
            "event": event,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish restaurant.created event: {str(exc)}",
        )