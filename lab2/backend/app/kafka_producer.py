import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from kafka import KafkaProducer


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    key_serializer=lambda key: key.encode("utf-8") if key else None,
    retries=5,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_event(
    event_type: str,
    actor_id: str,
    entity_type: str,
    entity_id: str,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    trace_id = trace_id or str(uuid.uuid4())
    idempotency_key = idempotency_key or f"{event_type}:{entity_id}:{trace_id}"

    return {
        "event_type": event_type,
        "trace_id": trace_id,
        "timestamp": now_iso(),
        "actor_id": actor_id,
        "entity": {
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
        "payload": payload,
        "idempotency_key": idempotency_key,
    }


def publish_event(topic: str, event: Dict[str, Any]) -> Dict[str, Any]:
    future = producer.send(
        topic,
        key=event.get("idempotency_key"),
        value=event,
    )
    producer.flush(timeout=10)

    metadata = future.get(timeout=10)

    return {
        "topic": metadata.topic,
        "partition": metadata.partition,
        "offset": metadata.offset,
        "trace_id": event.get("trace_id"),
        "idempotency_key": event.get("idempotency_key"),
    }