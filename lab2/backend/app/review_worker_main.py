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
REVIEW_TOPICS = ["review.created", "review.updated", "review.deleted"]
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


def handle_review_created(event: Dict[str, Any]) -> None:
    payload = event["payload"]

    last_rev = mongo_db.reviews.find_one({}, sort=[("_id", -1)])
    new_id = (last_rev["_id"] + 1) if last_rev else 1

    new_review = {
        "_id": new_id,
        "mysql_id": new_id,
        "user_id": payload.get("user_id"),
        "restaurant_id": payload.get("restaurant_id"),
        "rating": payload.get("rating"),
        "comment": payload.get("comment"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    print(f"Worker received review creation for restaurant_id: {payload.get('restaurant_id')}")
    # mongo_db.reviews.insert_one(new_review) # Removed to avoid duplication


def handle_review_updated(event: Dict[str, Any]) -> None:
    payload = event["payload"]

    updates = {}
    if "rating" in payload:
        updates["rating"] = payload["rating"]
    if "comment" in payload:
        updates["comment"] = payload["comment"]

    if not updates:
        return

    updates["updated_at"] = datetime.now(timezone.utc)

    mongo_db.reviews.update_one(
        {"_id": payload["review_id"]},
        {"$set": updates}
    )


def handle_review_deleted(event: Dict[str, Any]) -> None:
    payload = event["payload"]
    mongo_db.reviews.delete_one({"_id": payload["review_id"]})


def process_event(event: Dict[str, Any]) -> None:
    try:
        ensure_worker_tables()

        idempotency_key = event.get("idempotency_key")
        if not idempotency_key:
            raise ValueError("Missing idempotency_key")

        if already_processed(idempotency_key):
            print(f"Skipping duplicate event: {idempotency_key}")
            publish_status(event, "duplicate_skipped", "Duplicate event skipped by worker")
            return

        event_type = event.get("event_type")

        if event_type == "review.created":
            handle_review_created(event)
        elif event_type == "review.updated":
            handle_review_updated(event)
        elif event_type == "review.deleted":
            handle_review_deleted(event)
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
    print("Starting Review Worker Service...", flush=True)
    print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}", flush=True)
    print(f"Subscribing to topics: {REVIEW_TOPICS}", flush=True)

    while True:
        try:
            consumer = KafkaConsumer(
                *REVIEW_TOPICS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id="review-worker-group",
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