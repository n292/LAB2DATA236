import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

from kafka import KafkaConsumer, KafkaProducer

try:
    from app.mongodb import mongo_db
except ImportError:
    from mongodb import mongo_db


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
RESTAURANT_TOPICS = ["restaurant.created"]
STATUS_TOPIC = "booking.status"


status_producer = None

def get_producer():
    global status_producer
    if status_producer is None:
        try:
            status_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                key_serializer=lambda key: key.encode("utf-8") if key else None,
                retries=5,
            )
        except Exception as e:
            print(f"Error creating producer: {e}")
            return None
    return status_producer


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_status(original_event: Dict[str, Any], status: str, message: str) -> None:
    status_event = {
        "event_type": "booking.status",
        "trace_id": original_event.get("trace_id"),
        "timestamp": now_iso(),
        "actor_id": original_event.get("actor_id"),
        "entity": original_event.get("entity"),
        "payload": {
            "status": status,
            "message": message,
            "source_event_type": original_event.get("event_type"),
        },
        "idempotency_key": f"status:{original_event.get('idempotency_key')}",
    }

    producer = get_producer()
    if not producer:
        print("Cannot publish status: Producer not available")
        return

    producer.send(
        STATUS_TOPIC,
        key=status_event["idempotency_key"],
        value=status_event,
    )
    producer.flush(timeout=10)


def ensure_worker_tables() -> None:
    mongo_db.processed_kafka_events.create_index("idempotency_key", unique=True)


def already_processed(idempotency_key: str) -> bool:
    return mongo_db.processed_kafka_events.find_one({"idempotency_key": idempotency_key}) is not None


def mark_processed(event: Dict[str, Any]) -> None:
    mongo_db.processed_kafka_events.insert_one({
        "idempotency_key": event["idempotency_key"],
        "event_type": event["event_type"],
        "trace_id": event.get("trace_id"),
        "processed_at": datetime.now(timezone.utc)
    })


def handle_restaurant_created(event: Dict[str, Any]) -> None:
    payload = event["payload"]

    last_rest = mongo_db.restaurants.find_one({}, sort=[("_id", -1)])
    new_id = (last_rest["_id"] + 1) if last_rest else 1

    new_restaurant = {
        "_id": new_id,
        "mysql_id": new_id,
        "name": payload.get("name"),
        "cuisine_type": payload.get("cuisine_type"),
        "description": payload.get("description"),
        "location": {
            "address": payload.get("address"),
            "city": payload.get("city"),
            "zip_code": payload.get("zip_code"),
        },
        "contact": {
            "phone": payload.get("phone"),
            "email": payload.get("email"),
        },
        "pricing_tier": payload.get("pricing_tier"),
        "owner_id": payload.get("owner_id"),
        "average_rating": 0,
        "review_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    print(f"Worker received restaurant creation for: {payload.get('name')}")
    # mongo_db.restaurants.insert_one(new_restaurant) # Removed to avoid duplication


def process_event(event: Dict[str, Any]) -> None:
    try:
        ensure_worker_tables()

        idempotency_key = event.get("idempotency_key")
        if not idempotency_key:
            raise ValueError("Missing idempotency_key")

        if already_processed(idempotency_key):
            print(f"Skipping duplicate event: {idempotency_key}")
            publish_status(event, "duplicate_skipped", "Duplicate event skipped by restaurant worker")
            return

        event_type = event.get("event_type")

        if event_type == "restaurant.created":
            handle_restaurant_created(event)
        else:
            raise ValueError(f"Unsupported event_type: {event_type}")

        mark_processed(event)

        print(f"Processed {event_type} trace_id={event.get('trace_id')}")
        publish_status(event, "processed", f"{event_type} processed successfully")

    except Exception as exc:
        print(f"Failed to process event: {exc}")
        try:
            publish_status(event, "failed", str(exc))
        except Exception as status_exc:
            print(f"Failed to publish status event: {status_exc}")
        raise


def main() -> None:
    print("Starting Restaurant Worker Service...", flush=True)
    print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}", flush=True)
    print(f"Subscribing to topics: {RESTAURANT_TOPICS}", flush=True)

    while True:
        try:
            consumer = KafkaConsumer(
                *RESTAURANT_TOPICS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id="restaurant-worker-group",
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                key_deserializer=lambda key: key.decode("utf-8") if key else None,
            )

            for message in consumer:
                event = message.value
                print(f"Received event from topic={message.topic}: {event}", flush=True)

                try:
                    process_event(event)
                    consumer.commit()
                except Exception:
                    print("Event failed. Offset not committed.")

        except Exception as exc:
            print(f"Kafka consumer error: {exc}", flush=True)
            print("Retrying in 5 seconds...", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()