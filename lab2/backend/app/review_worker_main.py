import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

from kafka import KafkaConsumer, KafkaProducer
from sqlalchemy import text

try:
    from app.database import SessionLocal
except ImportError:
    from database import SessionLocal


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")
REVIEW_TOPICS = ["review.created", "review.updated", "review.deleted"]
STATUS_TOPIC = "booking.status"


status_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    key_serializer=lambda key: key.encode("utf-8") if key else None,
    retries=5,
)


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

    status_producer.send(
        STATUS_TOPIC,
        key=status_event["idempotency_key"],
        value=status_event,
    )
    status_producer.flush(timeout=10)


def ensure_worker_tables(db) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS processed_kafka_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                idempotency_key VARCHAR(255) NOT NULL UNIQUE,
                event_type VARCHAR(100) NOT NULL,
                trace_id VARCHAR(100),
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.commit()


def already_processed(db, idempotency_key: str) -> bool:
    result = db.execute(
        text("SELECT id FROM processed_kafka_events WHERE idempotency_key = :key"),
        {"key": idempotency_key},
    ).fetchone()

    return result is not None


def mark_processed(db, event: Dict[str, Any]) -> None:
    db.execute(
        text(
            """
            INSERT INTO processed_kafka_events
            (idempotency_key, event_type, trace_id)
            VALUES (:idempotency_key, :event_type, :trace_id)
            """
        ),
        {
            "idempotency_key": event["idempotency_key"],
            "event_type": event["event_type"],
            "trace_id": event.get("trace_id"),
        },
    )


def handle_review_created(db, event: Dict[str, Any]) -> None:
    payload = event["payload"]

    db.execute(
        text(
            """
            INSERT INTO reviews (user_id, restaurant_id, rating, comment, created_at, updated_at)
            VALUES (:user_id, :restaurant_id, :rating, :comment, NOW(), NOW())
            """
        ),
        {
            "user_id": payload["user_id"],
            "restaurant_id": payload["restaurant_id"],
            "rating": payload["rating"],
            "comment": payload.get("comment"),
        },
    )


def handle_review_updated(db, event: Dict[str, Any]) -> None:
    payload = event["payload"]

    fields = []
    params = {
        "review_id": payload["review_id"],
    }

    if payload.get("rating") is not None:
        fields.append("rating = :rating")
        params["rating"] = payload["rating"]

    if payload.get("comment") is not None:
        fields.append("comment = :comment")
        params["comment"] = payload["comment"]

    if not fields:
        return

    fields.append("updated_at = NOW()")

    query = f"""
        UPDATE reviews
        SET {", ".join(fields)}
        WHERE id = :review_id
    """

    db.execute(text(query), params)


def handle_review_deleted(db, event: Dict[str, Any]) -> None:
    payload = event["payload"]

    db.execute(
        text("DELETE FROM reviews WHERE id = :review_id"),
        {"review_id": payload["review_id"]},
    )


def process_event(event: Dict[str, Any]) -> None:
    db = SessionLocal()

    try:
        ensure_worker_tables(db)

        idempotency_key = event.get("idempotency_key")
        if not idempotency_key:
            raise ValueError("Missing idempotency_key")

        if already_processed(db, idempotency_key):
            print(f"Skipping duplicate event: {idempotency_key}")
            publish_status(event, "duplicate_skipped", "Duplicate event skipped by worker")
            return

        event_type = event.get("event_type")

        if event_type == "review.created":
            handle_review_created(db, event)
        elif event_type == "review.updated":
            handle_review_updated(db, event)
        elif event_type == "review.deleted":
            handle_review_deleted(db, event)
        else:
            raise ValueError(f"Unsupported event_type: {event_type}")

        mark_processed(db, event)
        db.commit()

        print(f"Processed {event_type} trace_id={event.get('trace_id')}")
        publish_status(event, "processed", f"{event_type} processed successfully")

    except Exception as exc:
        db.rollback()
        print(f"Failed to process event: {exc}")
        try:
            publish_status(event, "failed", str(exc))
        except Exception as status_exc:
            print(f"Failed to publish status event: {status_exc}")
        raise

    finally:
        db.close()


def main() -> None:
    print("Starting Review Worker Service...")
    print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Subscribing to topics: {REVIEW_TOPICS}")

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
                print(f"Received event from topic={message.topic}: {event}")

                try:
                    process_event(event)
                    consumer.commit()
                except Exception:
                    print("Event failed. Offset not committed.")

        except Exception as exc:
            print(f"Kafka consumer error: {exc}")
            print("Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()